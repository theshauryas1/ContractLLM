class LanguageDetector:
    def detect(self, text: str) -> str:
        normalized = f" {text.lower()} "
        language_markers = {
            "fr": [" le ", " la ", " les ", " des ", " une ", " résumez ", " politique ", " remboursement "],
            "de": [" der ", " die ", " und ", " sie ", " zusammenfassen ", " richtlinie ", " rückerstattung "],
            "es": [" el ", " la ", " los ", " las ", " una ", " resume ", " politica ", " reembolso "],
            "nl": [" de ", " het ", " een ", " samenvatten ", " beleid ", " terugbetaling "],
        }
        for language, markers in language_markers.items():
            if any(marker in normalized for marker in markers):
                return language

        ascii_ratio = sum(1 for char in text if ord(char) < 128) / max(len(text), 1)
        return "en" if ascii_ratio > 0.9 else "unknown"
