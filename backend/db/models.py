from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import JSON, Column, DateTime, Integer, String, UniqueConstraint, create_engine, event, func, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.utils.config import get_settings


settings = get_settings()
engine_kwargs = {"future": True, "pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

try:
    from pgvector.psycopg import register_vector
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    register_vector = None
    Vector = None
    PGVECTOR_AVAILABLE = False


def is_postgres() -> bool:
    return settings.database_url.startswith("postgresql")


def can_use_pgvector() -> bool:
    return is_postgres() and settings.vector_db == "pgvector" and PGVECTOR_AVAILABLE


if can_use_pgvector():
    @event.listens_for(engine, "connect")
    def register_pgvector(dbapi_connection, _) -> None:
        register_vector(dbapi_connection)


EmbeddingVectorType = Vector(settings.embedding_dimensions) if can_use_pgvector() else JSON


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, index=True, unique=True, nullable=False)
    tender_title = Column(String, nullable=False)
    tender_language = Column(String, nullable=False)
    output_language = Column(String, nullable=False)
    input_payload = Column(JSON, nullable=False)
    output_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, index=True, nullable=False)
    requirement_id = Column(String, index=True, nullable=False)
    requirement_text = Column(String, nullable=False)
    original_status = Column(String, nullable=False)
    corrected_status = Column(String, nullable=False)
    comments = Column(String, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("scope", "content_hash", name="uq_knowledge_chunks_scope_hash"),)

    id = Column(Integer, primary_key=True, index=True)
    content_hash = Column(String, index=True, nullable=False)
    scope = Column(String, index=True, nullable=False, default="global")
    source = Column(String, index=True, nullable=False)
    language = Column(String, nullable=False, default="en")
    content = Column(String, nullable=False)
    normalized_content = Column(String, nullable=False)
    embedding = Column(EmbeddingVectorType, nullable=False)
    chunk_metadata = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def init_db() -> None:
    if can_use_pgvector():
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    _ensure_pgvector_index()


def _ensure_pgvector_index() -> None:
    if not can_use_pgvector():
        return
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_hnsw_idx "
                "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
            )
        )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
