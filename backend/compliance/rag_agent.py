from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import KnowledgeChunk, can_use_pgvector
from backend.multilingual.language_detector import LanguageDetector
from backend.multilingual.translator import Translator
from backend.providers.embeddings import build_embedding_provider
from backend.schemas import EvidenceItem, KnowledgeDocument
from backend.utils.config import get_settings


class RAGAgent:
    GLOBAL_SCOPE = "global-default-kb"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedder = build_embedding_provider()
        self.language_detector = LanguageDetector()
        self.translator = Translator()

    def prepare_scope(
        self,
        company_profile_text: str,
        kb_documents: list[KnowledgeDocument],
        db: Session | None = None,
    ) -> tuple[list[str], str]:
        request_scope = self._build_scope_key(company_profile_text, kb_documents)
        if db is None:
            return [request_scope, self.GLOBAL_SCOPE], "in-memory"

        request_chunks = self._build_request_chunks(company_profile_text, kb_documents)
        global_chunks = self._build_global_chunks()

        self._sync_chunks(db, request_chunks, request_scope)
        self._sync_chunks(db, global_chunks, self.GLOBAL_SCOPE)

        backend = "pgvector" if can_use_pgvector() else "database-fallback"
        return [request_scope, self.GLOBAL_SCOPE], backend

    def retrieve(
        self,
        requirement_text: str,
        company_profile_text: str,
        kb_documents: list[KnowledgeDocument],
        top_k: int = 3,
        db: Session | None = None,
        scopes: list[str] | None = None,
    ) -> list[EvidenceItem]:
        scopes = scopes or self.prepare_scope(company_profile_text, kb_documents, db)[0]
        query = self._normalize_for_matching(requirement_text)
        query_vector = self.embedder.embed(query)

        if db is not None:
            if can_use_pgvector():
                return self._retrieve_from_pgvector(db, scopes, query, query_vector, top_k)
            return self._retrieve_from_rows(db, scopes, query, query_vector, top_k)

        local_chunks = self._build_request_chunks(company_profile_text, kb_documents) + self._build_global_chunks()
        return self._rank_local_chunks(local_chunks, query, query_vector, top_k, "in-memory")

    def _retrieve_from_pgvector(
        self,
        db: Session,
        scopes: list[str],
        query: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[EvidenceItem]:
        distance = KnowledgeChunk.embedding.cosine_distance(query_vector)
        rows = (
            db.execute(
                select(KnowledgeChunk)
                .where(KnowledgeChunk.scope.in_(scopes))
                .order_by(distance)
                .limit(max(top_k * 6, 12))
            )
            .scalars()
            .all()
        )

        ranked: list[tuple[float, EvidenceItem]] = []
        for row in rows:
            score = self._hybrid_score(query, row.normalized_content, query_vector, row.embedding)
            ranked.append(
                (
                    score,
                    EvidenceItem(
                        source=row.source,
                        snippet=row.content[:280],
                        score=round(score, 3),
                        retrieval_backend="pgvector",
                    ),
                )
            )

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in ranked[:top_k]]

    def _retrieve_from_rows(
        self,
        db: Session,
        scopes: list[str],
        query: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[EvidenceItem]:
        rows = (
            db.execute(select(KnowledgeChunk).where(KnowledgeChunk.scope.in_(scopes)))
            .scalars()
            .all()
        )

        ranked: list[tuple[float, EvidenceItem]] = []
        for row in rows:
            score = self._hybrid_score(query, row.normalized_content, query_vector, row.embedding)
            ranked.append(
                (
                    score,
                    EvidenceItem(
                        source=row.source,
                        snippet=row.content[:280],
                        score=round(score, 3),
                        retrieval_backend="database-fallback",
                    ),
                )
            )

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in ranked[:top_k] if item.score > 0]

    def _rank_local_chunks(
        self,
        chunks: list[dict[str, str]],
        query: str,
        query_vector: list[float],
        top_k: int,
        backend: str,
    ) -> list[EvidenceItem]:
        ranked: list[tuple[float, EvidenceItem]] = []
        for chunk in chunks:
            normalized_chunk = chunk["normalized_content"]
            score = self._hybrid_score(query, normalized_chunk, query_vector, self.embedder.embed(normalized_chunk))
            if score <= 0:
                continue
            ranked.append(
                (
                    score,
                    EvidenceItem(
                        source=chunk["source"],
                        snippet=chunk["content"][:280],
                        score=round(score, 3),
                        retrieval_backend=backend,
                    ),
                )
            )
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in ranked[:top_k]]

    def _build_scope_key(self, company_profile_text: str, kb_documents: list[KnowledgeDocument]) -> str:
        digest = hashlib.sha256()
        digest.update(company_profile_text.encode("utf-8"))
        for document in kb_documents:
            digest.update(document.title.encode("utf-8"))
            digest.update(document.content.encode("utf-8"))
        return f"request-{digest.hexdigest()[:24]}"

    def _build_request_chunks(self, company_profile_text: str, kb_documents: list[KnowledgeDocument]) -> list[dict[str, str]]:
        chunks: list[dict[str, str]] = []
        for index, chunk in enumerate(self._chunk_text(company_profile_text), start=1):
            chunks.append(self._build_chunk_record(f"company-profile-{index}", chunk, "company_profile"))

        for document in kb_documents:
            for index, chunk in enumerate(self._chunk_text(document.content), start=1):
                chunks.append(self._build_chunk_record(f"{document.title}-{index}", chunk, "request_kb"))

        return chunks

    def _build_global_chunks(self) -> list[dict[str, str]]:
        chunks: list[dict[str, str]] = []
        kb_path = Path(self.settings.knowledge_base_path)
        if not kb_path.exists():
            return chunks

        for file_path in kb_path.glob("*.txt"):
            content = file_path.read_text(encoding="utf-8")
            for index, chunk in enumerate(self._chunk_text(content), start=1):
                chunks.append(self._build_chunk_record(f"{file_path.stem}-{index}", chunk, "global_kb"))
        return chunks

    def _build_chunk_record(self, source: str, content: str, source_kind: str) -> dict[str, str]:
        language = self.language_detector.detect(content)
        normalized = self._normalize_for_matching(content)
        return {
            "source": source,
            "content": content,
            "normalized_content": normalized,
            "language": language,
            "source_kind": source_kind,
        }

    def _sync_chunks(self, db: Session, chunks: list[dict[str, str]], scope: str) -> None:
        if not chunks:
            return

        for chunk in chunks:
            content_hash = hashlib.sha256(chunk["content"].encode("utf-8")).hexdigest()
            existing = (
                db.execute(
                    select(KnowledgeChunk).where(
                        KnowledgeChunk.scope == scope,
                        KnowledgeChunk.content_hash == content_hash,
                    )
                )
                .scalar_one_or_none()
            )
            if existing is not None:
                continue

            embedding = self.embedder.embed(chunk["normalized_content"])
            db.add(
                KnowledgeChunk(
                    scope=scope,
                    content_hash=content_hash,
                    source=chunk["source"],
                    language=chunk["language"],
                    content=chunk["content"],
                    normalized_content=chunk["normalized_content"],
                    embedding=embedding,
                    chunk_metadata={"source_kind": chunk["source_kind"]},
                )
            )
        db.commit()

    def _chunk_text(self, text: str) -> list[str]:
        paragraphs = [item.strip() for item in re.split(r"\n+|(?<=[.!?])\s+", text) if item.strip()]
        return [paragraph for paragraph in paragraphs if len(paragraph) > 20]

    def _normalize_for_matching(self, text: str) -> str:
        language = self.language_detector.detect(text)
        if language != "en":
            return self.translator.translate_to_english(text, language).translated_text.lower()
        return text.lower()

    def _hybrid_score(
        self,
        query_text: str,
        chunk_text: str,
        query_vector: list[float],
        chunk_vector: list[float],
    ) -> float:
        query_tokens = set(re.findall(r"\w+", query_text.lower()))
        chunk_tokens = set(re.findall(r"\w+", chunk_text.lower()))
        lexical = len(query_tokens & chunk_tokens) / max(len(query_tokens), 1)
        similarity = self._cosine_similarity(query_vector, chunk_vector)
        return round((0.4 * lexical) + (0.6 * similarity), 4)

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(item * item for item in left))
        right_norm = math.sqrt(sum(item * item for item in right))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)
