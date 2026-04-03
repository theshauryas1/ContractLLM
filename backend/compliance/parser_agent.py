from __future__ import annotations

import base64
import io
import re

from backend.multilingual.language_detector import LanguageDetector
from backend.schemas import ParsedDocument


class ParserAgent:
    def __init__(self) -> None:
        self.language_detector = LanguageDetector()

    def parse(self, text: str = "", document_base64: str | None = None) -> ParsedDocument:
        if document_base64:
            extracted = self._parse_pdf(document_base64)
            return ParsedDocument(
                text=extracted,
                source_type="pdf",
                language=self.language_detector.detect(extracted),
            )

        normalized = self._normalize_text(text)
        if not normalized:
            return ParsedDocument(text="", source_type="empty", language="unknown")
        return ParsedDocument(text=normalized, source_type="text", language=self.language_detector.detect(normalized))

    def _parse_pdf(self, document_base64: str) -> str:
        data = base64.b64decode(document_base64)
        try:
            import fitz  # type: ignore

            with fitz.open(stream=data, filetype="pdf") as doc:
                content = "\n".join(page.get_text("text") for page in doc)
                return self._normalize_text(content)
        except Exception:
            try:
                return self._normalize_text(io.BytesIO(data).read().decode("utf-8"))
            except UnicodeDecodeError:
                return ""

    def _normalize_text(self, text: str) -> str:
        compact = text.replace("\r", "\n")
        compact = re.sub(r"[ \t]+", " ", compact)
        compact = re.sub(r"\n{3,}", "\n\n", compact)
        return compact.strip()
