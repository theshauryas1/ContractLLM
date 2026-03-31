class LanguageDetector:
    def detect(self, text: str) -> str:
        ascii_ratio = sum(1 for char in text if ord(char) < 128) / max(len(text), 1)
        return "en" if ascii_ratio > 0.9 else "unknown"
