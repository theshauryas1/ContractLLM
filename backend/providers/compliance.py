from __future__ import annotations
from abc import ABC, abstractmethod

import httpx
from pydantic import BaseModel, Field

from backend.multilingual.language_detector import LanguageDetector
from backend.multilingual.translator import Translator
from backend.schemas import ComplianceStatus, EvidenceItem, FeedbackExample
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


class XAIComplianceReasoningProvider(ComplianceReasoningProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.language_detector = LanguageDetector()
        self.translator = Translator()

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

    def _extract_output_text(self, payload: dict) -> str:
        output = payload.get("output", [])
        for item in output:
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
        raise ValueError("xAI response did not include structured output text")

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


def build_compliance_reasoning_provider() -> ComplianceReasoningProvider:
    settings = get_settings()
    if settings.llm_provider == "xai" and settings.xai_api_key:
        return XAIComplianceReasoningProvider(
            api_key=settings.xai_api_key,
            model=settings.llm_model,
            base_url=settings.xai_base_url,
        )
    return HeuristicComplianceReasoningProvider()
