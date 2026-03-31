from __future__ import annotations

from pathlib import Path

from backend.rag.embedder import Embedder
from backend.utils.config import get_settings


class Retriever:
    def __init__(self, kb_path: str | None = None) -> None:
        settings = get_settings()
        self.kb_path = Path(kb_path or settings.knowledge_base_path)
        self.embedder = Embedder()

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        if not self.kb_path.exists():
            return []
        query_vector = self.embedder.encode([query])[0]
        ranked: list[tuple[float, str]] = []
        for file_path in self.kb_path.glob("*.txt"):
            content = file_path.read_text(encoding="utf-8")
            document_vector = self.embedder.encode([content])[0]
            score = self._similarity(query_vector, document_vector, query, content)
            ranked.append((score, file_path.name))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [name for score, name in ranked[:top_k] if score > 0]

    def _similarity(self, query_vector: list[float], document_vector: list[float], query: str, content: str) -> float:
        lexical_overlap = sum(1 for token in query.lower().split() if token in content.lower())
        vector_signal = min(sum(query_vector), sum(document_vector)) / max(sum(query_vector), sum(document_vector), 1.0)
        return float(lexical_overlap) + vector_signal
