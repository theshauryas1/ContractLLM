import pytest
from fastapi.testclient import TestClient

from backend.db.models import AnalysisRun, FeedbackEntry, KnowledgeChunk, SessionLocal, init_db
from backend.main import app
from backend.utils.config import get_settings


@pytest.fixture(autouse=True)
def clean_db() -> None:
    settings = get_settings()
    original_require_auth = settings.require_auth
    original_api_key = settings.api_key
    original_llm_provider = settings.llm_provider
    original_xai_api_key = settings.xai_api_key
    original_embedding_provider = settings.embedding_provider
    original_translation_provider = settings.translation_provider
    original_language_mode = settings.language_mode
    original_allow_language_override = settings.allow_language_override
    original_enable_feedback_loop = settings.enable_feedback_loop

    settings.require_auth = False
    settings.api_key = "local-dev-key"
    settings.llm_provider = "heuristic"
    settings.xai_api_key = ""
    settings.embedding_provider = "multilingual_vector"
    settings.translation_provider = "heuristic"
    settings.language_mode = "auto"
    settings.allow_language_override = True
    settings.enable_feedback_loop = True

    init_db()
    db = SessionLocal()
    try:
        db.query(KnowledgeChunk).delete()
        db.query(FeedbackEntry).delete()
        db.query(AnalysisRun).delete()
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(KnowledgeChunk).delete()
        db.query(FeedbackEntry).delete()
        db.query(AnalysisRun).delete()
        db.commit()
    finally:
        db.close()

    settings.require_auth = original_require_auth
    settings.api_key = original_api_key
    settings.llm_provider = original_llm_provider
    settings.xai_api_key = original_xai_api_key
    settings.embedding_provider = original_embedding_provider
    settings.translation_provider = original_translation_provider
    settings.language_mode = original_language_mode
    settings.allow_language_override = original_allow_language_override
    settings.enable_feedback_loop = original_enable_feedback_loop


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
