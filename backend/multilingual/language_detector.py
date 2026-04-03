class LanguageDetector:
    def detect(self, text: str) -> str:
        if any("\u0900" <= char <= "\u097F" for char in text):
            return "hi"

        normalized = f" {text.lower()} "
        language_markers = {
            "fr": [" le ", " la ", " les ", " des ", " une ", " politique ", " remboursement ", " conformite "],
            "de": [" der ", " die ", " und ", " sie ", " richtlinie ", " zertifizierung ", " angebot "],
            "es": [" el ", " la ", " los ", " las ", " una ", " politica ", " reembolso ", " cumplimiento "],
            "nl": [" de ", " het ", " een ", " beleid ", " terugbetaling ", " inschrijving "],
        }
        for language, markers in language_markers.items():
            if any(marker in normalized for marker in markers):
                return language

        ascii_ratio = sum(1 for char in text if ord(char) < 128) / max(len(text), 1)
        return "en" if ascii_ratio > 0.9 else "unknown"
