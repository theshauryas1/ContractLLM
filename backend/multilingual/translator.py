from backend.schemas import TranslationBundle


class Translator:
    def translate_to_english(self, text: str, language: str) -> TranslationBundle:
        return TranslationBundle(source_language=language, translated_text=text)

    def translate_from_english(self, text: str, target_language: str) -> TranslationBundle:
        return TranslationBundle(source_language="en", translated_text=text, target_language=target_language)
