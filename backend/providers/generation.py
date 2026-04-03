from __future__ import annotations

import json
from abc import ABC, abstractmethod

import httpx

from backend.multilingual.language_detector import LanguageDetector
from backend.multilingual.translator import Translator
from backend.utils.config import get_settings


class GenerationProvider(ABC):
    @abstractmethod
    def generate_structured(self, text: str, context: str, target_language: str) -> dict:
        raise NotImplementedError


class HeuristicGenerationProvider(GenerationProvider):
    def __init__(self) -> None:
        self.translator = Translator()

    def generate_structured(self, text: str, context: str, target_language: str) -> dict:
        summary = text.strip()
        if context.strip():
            summary = f"{summary}. {context.strip()}"

        detector = LanguageDetector()
        source_language = detector.detect(summary)
        if source_language != target_language and target_language != "unknown":
            if target_language == "en":
                summary = self.translator.translate_to_english(summary, source_language).translated_text
            else:
                english_summary = summary
                if source_language != "en":
                    english_summary = self.translator.translate_to_english(summary, source_language).translated_text
                summary = self.translator.translate_from_english(english_summary, target_language).translated_text
        return {
            "output": {
                "summary": summary[:280],
                "language": target_language,
            },
            "provider": "heuristic",
        }


class XAIGenerationProvider(GenerationProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate_structured(self, text: str, context: str, target_language: str) -> dict:
        prompt = (
            "Generate a concise structured JSON response with keys: summary, language.\n"
            f"Target language: {target_language}\n"
            "STRICT RULES:\n"
            "- Output valid JSON only.\n"
            "- The summary must be written entirely in the target language.\n"
            "- Preserve domain meaning and terminology.\n"
            "- Do not translate into English unless the target language is English.\n"
            f"Input:\n{text}\n\n"
            f"Context:\n{context}"
        )
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a precise multilingual structured generation engine."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return {"output": json.loads(content), "provider": "xai"}


def build_generation_provider() -> GenerationProvider:
    settings = get_settings()
    if settings.llm_provider == "xai" and settings.xai_api_key:
        return XAIGenerationProvider(
            api_key=settings.xai_api_key,
            model=settings.llm_model,
            base_url=settings.xai_base_url,
        )
    return HeuristicGenerationProvider()


def extract_language_text(payload: object) -> str:
    if isinstance(payload, dict):
        return " ".join(extract_language_text(value) for value in payload.values()).strip()
    if isinstance(payload, list):
        return " ".join(extract_language_text(value) for value in payload).strip()
    if isinstance(payload, str):
        return payload
    return ""


def detect_output_language(payload: dict[str, object]) -> str:
    detector = LanguageDetector()
    return detector.detect(extract_language_text(payload))
