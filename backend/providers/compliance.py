from __future__ import annotations
from abc import ABC, abstractmethod

import httpx
from pydantic import BaseModel, Field

from shared.multilingual.language_detector import LanguageDetector
from shared.multilingual.translator import Translator
from shared.schemas import ComplianceStatus, EvidenceItem, FeedbackExample
from backend.utils.config import get_settings


class ComplianceDecisionPayload(BaseModel):
    status: ComplianceStatus = Field(description="Compliance decision")
    reasoning: str = Field(description="Why this decision was made")
    confidence: float = Field(description="Decision confidence from 0 to 1")
    recommended_action: str = Field(description="Next action for the bid team")
    review_required: bool = Field(description="Whether a human should review this decision")
    audit_notes: list[str] = Field(description="Short audit trail bullets")


class ComplianceReasoningProvider(ABC):
    @abstractmethod
    def assess(
        self,
        requirement_text: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample],
    ) -> ComplianceDecisionPayload:
        raise NotImplementedError


class HeuristicComplianceReasoningProvider(ComplianceReasoningProvider):
    def __init__(self) -> None:
        self.settings = get_settings()

    def assess(
        self,
        requirement_text: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample],
    ) -> ComplianceDecisionPayload:
        best_score = evidence[0].score if evidence else 0.0
        if feedback_examples and feedback_examples[0].similarity >= 0.8:
            status = feedback_examples[0].corrected_status
        elif best_score >= 0.6 and evidence:
            status = "full"
        elif best_score >= 0.3 and evidence:
            status = "partial"
        else:
            status = "missing"

        confidence = 0.35 + (best_score * 0.5) + min(len(evidence), 3) * 0.05 + min(len(feedback_examples), 2) * 0.05
        return ComplianceDecisionPayload(
            status=status,
            reasoning="",
            confidence=round(min(confidence, 0.96), 3),
            recommended_action="",
            review_required=round(min(confidence, 0.96), 3) < self.settings.confidence_threshold or status != "full",
            audit_notes=[
                f"Requirement category: {category_label}.",
                f"Retrieved {len(evidence)} evidence snippets.",
            ],
        )


import logging
logger = logging.getLogger(__name__)

class BaseComplianceReasoningProvider(ComplianceReasoningProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.language_detector = LanguageDetector()
        self.translator = Translator()

    def _build_prompt(
        self,
        requirement_text: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample],
    ) -> str:
        evidence_lines = "\n".join(
            f"- Source: {item.source} | Score: {item.score} | Backend: {item.retrieval_backend}\n  Snippet: {item.snippet}"
            for item in evidence
        )
        feedback_lines = "\n".join(
            f"- corrected_status={item.corrected_status}, similarity={item.similarity}, comments={item.comments}"
            for item in feedback_examples
        )
        return (
            "Assess whether the company satisfies this tender requirement.\n"
            f"Output language: {output_language}\n"
            "Use only these statuses: full, partial, missing.\n"
            "Decision rules:\n"
            "- full: evidence clearly supports the requirement.\n"
            "- partial: evidence is relevant but incomplete, ambiguous, or indirect.\n"
            "- missing: no convincing support is present.\n"
            "Keep reasoning concise and auditable. Confidence must be between 0 and 1.\n\n"
            f"Requirement category: {category_label}\n"
            f"Requirement text: {requirement_text}\n\n"
            f"Retrieved evidence:\n{evidence_lines or '- No evidence retrieved.'}\n\n"
            f"Reviewer feedback examples:\n{feedback_lines or '- No similar reviewer feedback.'}"
        )

    def _enforce_language(self, decision: ComplianceDecisionPayload, output_language: str) -> ComplianceDecisionPayload:
        if output_language in {"en", "unknown", "hi"}:
            return decision

        combined = f"{decision.reasoning} {decision.recommended_action}"
        detected = self.language_detector.detect(combined)
        if detected == output_language:
            return decision

        translated_reasoning = self.translator.translate_from_english(decision.reasoning, output_language).translated_text
        translated_action = self.translator.translate_from_english(decision.recommended_action, output_language).translated_text
        translated_notes = [
            self.translator.translate_from_english(item, output_language).translated_text for item in decision.audit_notes
        ]
        return decision.model_copy(
            update={
                "reasoning": translated_reasoning,
                "recommended_action": translated_action,
                "audit_notes": translated_notes,
            }
        )


class XAIComplianceReasoningProvider(BaseComplianceReasoningProvider):
    def assess(
        self,
        requirement_text: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample],
    ) -> ComplianceDecisionPayload:
        prompt = self._build_prompt(requirement_text, category_label, evidence, output_language, feedback_examples)
        response = httpx.post(
            f"{self.base_url}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "store": False,
                "input": [
                    {
                        "role": "system",
                        "content": "You are a procurement compliance reasoning engine. Always follow the schema exactly.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "compliance_decision",
                        "schema": ComplianceDecisionPayload.model_json_schema(),
                        "strict": True,
                    }
                },
            },
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
        raw_text = self._extract_output_text(payload)
        decision = ComplianceDecisionPayload.model_validate_json(raw_text)
        return self._enforce_language(decision, output_language)

    def _extract_output_text(self, payload: dict) -> str:
        output = payload.get("output", [])
        for item in output:
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
        raise ValueError("xAI response did not include structured output text")


class GeminiComplianceReasoningProvider(BaseComplianceReasoningProvider):
    def assess(
        self,
        requirement_text: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample],
    ) -> ComplianceDecisionPayload:
        prompt = self._build_prompt(requirement_text, category_label, evidence, output_language, feedback_examples)
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        response = httpx.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": "You are a procurement compliance reasoning engine. Always analyze compliance details and return a structured JSON object matching the requested schema.\n\n" + prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "OBJECT",
                        "properties": {
                            "status": {"type": "STRING", "enum": ["full", "partial", "missing"]},
                            "reasoning": {"type": "STRING"},
                            "confidence": {"type": "NUMBER"},
                            "recommended_action": {"type": "STRING"},
                            "review_required": {"type": "BOOLEAN"},
                            "audit_notes": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["status", "reasoning", "confidence", "recommended_action", "review_required", "audit_notes"]
                    }
                }
            },
            timeout=60.0
        )
        response.raise_for_status()
        res_json = response.json()
        
        try:
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error(f"Gemini API returned unexpected payload format: {res_json}")
            raise ValueError("Gemini response did not include generated text") from e
            
        decision = ComplianceDecisionPayload.model_validate_json(raw_text)
        return self._enforce_language(decision, output_language)


class NvidiaComplianceReasoningProvider(BaseComplianceReasoningProvider):
    def assess(
        self,
        requirement_text: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample],
    ) -> ComplianceDecisionPayload:
        prompt = self._build_prompt(requirement_text, category_label, evidence, output_language, feedback_examples)
        
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a procurement compliance reasoning engine. Output your decision as a valid JSON object matching the schema exactly with keys: status, reasoning, confidence, recommended_action, review_required, audit_notes."
                    },
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            },
            timeout=60.0
        )
        response.raise_for_status()
        res_json = response.json()
        
        try:
            raw_text = res_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"NVIDIA NIM returned unexpected response structure: {res_json}")
            raise ValueError("NVIDIA NIM response did not include completions text") from e
            
        decision = ComplianceDecisionPayload.model_validate_json(raw_text)
        return self._enforce_language(decision, output_language)


class FallbackComplianceReasoningProvider(ComplianceReasoningProvider):
    def __init__(self, providers: list[ComplianceReasoningProvider]) -> None:
        self.providers = providers

    def assess(
        self,
        requirement_text: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample],
    ) -> ComplianceDecisionPayload:
        errors = []
        for provider in self.providers:
            try:
                return provider.assess(
                    requirement_text=requirement_text,
                    category_label=category_label,
                    evidence=evidence,
                    output_language=output_language,
                    feedback_examples=feedback_examples,
                )
            except Exception as e:
                logger.warning(f"Compliance provider {provider.__class__.__name__} failed: {e}. Trying next fallback...")
                errors.append(f"{provider.__class__.__name__}: {str(e)}")
        
        # If all fail, use the heuristic provider as a final safety net
        logger.error(f"All LLM providers failed: {errors}. Falling back to Heuristic compliance provider.")
        return HeuristicComplianceReasoningProvider().assess(
            requirement_text=requirement_text,
            category_label=category_label,
            evidence=evidence,
            output_language=output_language,
            feedback_examples=feedback_examples,
        )


def build_compliance_reasoning_provider() -> ComplianceReasoningProvider:
    settings = get_settings()
    providers = []
    
    # 1. Google Gemini
    if settings.gemini_api_key:
        providers.append(
            GeminiComplianceReasoningProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                base_url=settings.gemini_base_url,
            )
        )
        
    # 2. NVIDIA NIM
    if settings.nvidia_api_key:
        providers.append(
            NvidiaComplianceReasoningProvider(
                api_key=settings.nvidia_api_key,
                model=settings.nvidia_model,
                base_url=settings.nvidia_base_url,
            )
        )
        
    # 3. xAI Grok
    if settings.xai_api_key:
        # Use grok-beta/grok-2 as default if llm_model is configured with invalid name
        model_name = settings.llm_model if "grok" in settings.llm_model.lower() else "grok-beta"
        providers.append(
            XAIComplianceReasoningProvider(
                api_key=settings.xai_api_key,
                model=model_name,
                base_url=settings.xai_base_url,
            )
        )
        
    if providers:
        return FallbackComplianceReasoningProvider(providers)
        
    return HeuristicComplianceReasoningProvider()
