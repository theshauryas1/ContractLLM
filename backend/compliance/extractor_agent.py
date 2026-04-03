from __future__ import annotations

import re

from backend.compliance.classifier_agent import ClassifierAgent
from backend.compliance.localization import localize_category
from backend.multilingual.translator import Translator
from backend.schemas import ExtractedRequirement


class ExtractorAgent:
    REQUIREMENT_HINTS = (
        "must",
        "shall",
        "required",
        "need",
        "provide",
        "submit",
        "maintain",
        "deliver",
        "certification",
        "insurance",
        "turnover",
        "gdpr",
        "registration",
        "experience",
        "support",
    )

    def __init__(self) -> None:
        self.classifier = ClassifierAgent()
        self.translator = Translator()

    def extract(self, text: str, source_language: str, output_language: str) -> tuple[list[ExtractedRequirement], dict[str, str]]:
        segments = self._split_into_segments(text)
        requirements: list[ExtractedRequirement] = []
        normalized_text_by_id: dict[str, str] = {}

        for index, segment in enumerate(segments, start=1):
            normalized = self._normalize_for_matching(segment, source_language)
            if not self._looks_like_requirement(normalized):
                continue
            category, mandatory = self.classifier.classify(normalized)
            requirement_id = f"REQ-{index:03d}"
            requirements.append(
                ExtractedRequirement(
                    id=requirement_id,
                    text=segment,
                    category=category,
                    category_label=localize_category(category, output_language),
                    mandatory=mandatory,
                    evaluation_weight=1.15 if mandatory else 0.9,
                )
            )
            normalized_text_by_id[requirement_id] = normalized

        if requirements:
            return requirements, normalized_text_by_id

        fallbacks = [segment for segment in segments if len(segment) > 30][:5]
        for index, segment in enumerate(fallbacks, start=1):
            normalized = self._normalize_for_matching(segment, source_language)
            category, mandatory = self.classifier.classify(normalized)
            requirement_id = f"REQ-{index:03d}"
            requirements.append(
                ExtractedRequirement(
                    id=requirement_id,
                    text=segment,
                    category=category,
                    category_label=localize_category(category, output_language),
                    mandatory=mandatory,
                    evaluation_weight=1.0,
                )
            )
            normalized_text_by_id[requirement_id] = normalized

        return requirements, normalized_text_by_id

    def _split_into_segments(self, text: str) -> list[str]:
        normalized = text.replace("\r", "\n")
        bullets = re.sub(r"\n[•*-]\s*", "\n", normalized)
        segments = re.split(r"\n+|(?<=[.!?])\s+", bullets)
        return [segment.strip(" -\t") for segment in segments if segment.strip()]

    def _normalize_for_matching(self, text: str, source_language: str) -> str:
        if source_language and source_language != "en":
            return self.translator.translate_to_english(text, source_language).translated_text.lower()
        return text.lower()

    def _looks_like_requirement(self, normalized_text: str) -> bool:
        return any(hint in normalized_text for hint in self.REQUIREMENT_HINTS)
