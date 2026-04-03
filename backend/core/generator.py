from __future__ import annotations

from backend.multilingual.language_detector import LanguageDetector
from backend.providers.generation import build_generation_provider, detect_output_language
from backend.schemas import GenerateRequest, GenerateResponse
from backend.utils.config import get_settings


class LanguagePreservingGenerator:
    SUPPORTED_LANGUAGES = {"auto", "en", "fr", "de", "es", "nl", "hi"}

    def __init__(self) -> None:
        self.settings = get_settings()
        self.language_detector = LanguageDetector()
        self.provider = build_generation_provider()

    def generate(self, payload: GenerateRequest) -> GenerateResponse:
        input_language = self.language_detector.detect(payload.text)
        target_language = self._resolve_target_language(payload.target_language, input_language)

        retries = 0
        result = self.provider.generate_structured(payload.text, payload.context, target_language)
        output = result["output"]
        output_language = detect_output_language(output)

        while (
            self.settings.strict_language_match
            and output_language != target_language
            and retries < self.settings.language_retry_limit
        ):
            retries += 1
            result = self.provider.generate_structured(payload.text, payload.context, target_language)
            output = result["output"]
            output_language = detect_output_language(output)

        return GenerateResponse(
            input_language=input_language,
            target_language=target_language,
            output_language=output_language,
            output=output,
            provider=result["provider"],
            retries=retries,
        )

    def _resolve_target_language(self, requested_language: str, input_language: str) -> str:
        if requested_language not in self.SUPPORTED_LANGUAGES:
            requested_language = "auto"

        if requested_language != "auto" and self.settings.allow_language_override:
            return requested_language

        if self.settings.language_mode == "fixed":
            return self.settings.default_output_language

        return input_language if input_language != "unknown" else self.settings.default_output_language
