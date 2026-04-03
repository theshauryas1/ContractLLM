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
            return self.parse_bytes(base64.b64decode(document_base64), "upload.pdf", "application/pdf")

        normalized = self._normalize_text(text)
        if not normalized:
            return ParsedDocument(text="", source_type="empty", language="unknown")
        return ParsedDocument(text=normalized, source_type="text", language=self.language_detector.detect(normalized))

    def parse_bytes(self, data: bytes, filename: str, content_type: str | None = None) -> ParsedDocument:
        source_type = "pdf" if filename.lower().endswith(".pdf") or content_type == "application/pdf" else "text"
        extracted = self._parse_file_bytes(data, source_type)
        language = self.language_detector.detect(extracted) if extracted else "unknown"
        return ParsedDocument(text=extracted, source_type=source_type if extracted else "empty", language=language)

    def _parse_file_bytes(self, data: bytes, source_type: str) -> str:
        if source_type == "pdf":
            parsed_pdf = self._parse_pdf_bytes(data)
            if parsed_pdf:
                return parsed_pdf
        return self._parse_text_bytes(data)

    def _parse_pdf_bytes(self, data: bytes) -> str:
        try:
            import fitz  # type: ignore

            with fitz.open(stream=data, filetype="pdf") as doc:
                content = "\n".join(page.get_text("text") for page in doc)
                return self._normalize_text(content)
        except Exception:
            return ""

    def _parse_text_bytes(self, data: bytes) -> str:
        try:
            return self._normalize_text(io.BytesIO(data).read().decode("utf-8"))
        except UnicodeDecodeError:
            return ""

    def _normalize_text(self, text: str) -> str:
        compact = text.replace("\r", "\n")
        compact = re.sub(r"[ \t]+", " ", compact)
        compact = re.sub(r"\n{3,}", "\n\n", compact)
        return compact.strip()
