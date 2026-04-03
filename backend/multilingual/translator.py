from __future__ import annotations

import json
import re

import httpx

from backend.schemas import TranslationBundle
from backend.utils.config import get_settings


class Translator:
    SUPPORTED_LANGUAGES = {"fr", "de", "es", "nl", "en"}
    PHRASE_MAP = {
        "fr": [
            ("certification iso 9001", "iso 9001 certification"),
            ("certification requise", "certification required"),
            ("politique de remboursement", "refund policy"),
            ("chiffre d'affaires", "turnover"),
            ("assurance responsabilite", "liability insurance"),
            ("preuve d'experience", "evidence of experience"),
            ("enregistrement", "registration"),
            ("obligatoire", "mandatory"),
            ("soumettre", "submit"),
            ("conformite", "compliance"),
            ("resume", "summary"),
        ],
        "de": [
            ("iso 9001 zertifizierung", "iso 9001 certification"),
            ("zertifizierung erforderlich", "certification required"),
            ("jahresumsatz", "turnover"),
            ("haftpflichtversicherung", "liability insurance"),
            ("erfahrungsnachweis", "evidence of experience"),
            ("registrierung", "registration"),
            ("verpflichtend", "mandatory"),
            ("einreichen", "submit"),
            ("compliance", "compliance"),
            ("zusammenfassung", "summary"),
        ],
        "es": [
            ("certificacion iso 9001", "iso 9001 certification"),
            ("certificacion requerida", "certification required"),
            ("facturacion anual", "turnover"),
            ("seguro de responsabilidad", "liability insurance"),
            ("prueba de experiencia", "evidence of experience"),
            ("registro", "registration"),
            ("obligatorio", "mandatory"),
            ("presentar", "submit"),
            ("cumplimiento", "compliance"),
            ("resumen", "summary"),
        ],
        "nl": [
            ("iso 9001 certificering", "iso 9001 certification"),
            ("certificering vereist", "certification required"),
            ("jaaromzet", "turnover"),
            ("aansprakelijkheidsverzekering", "liability insurance"),
            ("bewijs van ervaring", "evidence of experience"),
            ("registratie", "registration"),
            ("verplicht", "mandatory"),
            ("indienen", "submit"),
            ("naleving", "compliance"),
            ("samenvatting", "summary"),
        ],
    }

    REVERSE_PHRASE_MAP = {
        language: sorted(((target, source) for source, target in pairs), key=lambda item: len(item[0]), reverse=True)
        for language, pairs in PHRASE_MAP.items()
    }

    def __init__(self) -> None:
        self.settings = get_settings()

    def translate_to_english(self, text: str, language: str) -> TranslationBundle:
        if not text or language == "en":
            return TranslationBundle(source_language=language, translated_text=text)
        if language not in self.SUPPORTED_LANGUAGES:
            return TranslationBundle(source_language=language, translated_text=text)
        translated = self._translate(text=text, source_language=language, target_language="en")
        return TranslationBundle(source_language=language, translated_text=translated, target_language="en")

    def translate_from_english(self, text: str, target_language: str) -> TranslationBundle:
        if not text or target_language == "en":
            return TranslationBundle(source_language="en", translated_text=text, target_language=target_language)
        if target_language not in self.SUPPORTED_LANGUAGES:
            return TranslationBundle(source_language="en", translated_text=text, target_language=target_language)
        translated = self._translate(text=text, source_language="en", target_language=target_language)
        return TranslationBundle(source_language="en", translated_text=translated, target_language=target_language)

    def _translate(self, text: str, source_language: str, target_language: str) -> str:
        if self.settings.translation_provider == "xai" and self.settings.xai_api_key:
            return self._translate_with_xai(text, source_language, target_language)
        return self._translate_with_rules(text, source_language, target_language)

    def _translate_with_xai(self, text: str, source_language: str, target_language: str) -> str:
        prompt = (
            "Translate the text precisely while preserving structure, numbers, and factual meaning. "
            "Return only the translated text.\n"
            f"Source language: {source_language}\n"
            f"Target language: {target_language}\n"
            f"Text:\n{text}"
        )
        response = httpx.post(
            f"{self.settings.xai_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.xai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.settings.translation_model,
                "messages": [
                    {"role": "system", "content": "You are a precise multilingual translation engine."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()

    def _translate_with_rules(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text

        if self._looks_like_json(text):
            data = json.loads(text)
            translated_data = self._translate_json(data, source_language, target_language)
            return json.dumps(translated_data, ensure_ascii=False)

        return self._replace_phrases(text, source_language, target_language)

    def _translate_json(self, value: object, source_language: str, target_language: str) -> object:
        if isinstance(value, dict):
            return {
                self._replace_phrases(key, source_language, target_language): self._translate_json(
                    item, source_language, target_language
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._translate_json(item, source_language, target_language) for item in value]
        if isinstance(value, str):
            return self._replace_phrases(value, source_language, target_language)
        return value

    def _replace_phrases(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == "en":
            replacements = self.REVERSE_PHRASE_MAP.get(target_language, [])
        elif target_language == "en":
            replacements = sorted(self.PHRASE_MAP.get(source_language, []), key=lambda item: len(item[0]), reverse=True)
        else:
            to_english = self._replace_phrases(text, source_language, "en")
            return self._replace_phrases(to_english, "en", target_language)

        translated = text
        for source, target in replacements:
            translated = re.sub(re.escape(source), target, translated, flags=re.IGNORECASE)
        return translated

    def _looks_like_json(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped or stripped[0] not in "[{":
            return False
        try:
            json.loads(stripped)
        except json.JSONDecodeError:
            return False
        return True
