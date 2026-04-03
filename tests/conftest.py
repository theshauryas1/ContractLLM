import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.db.models import SessionLocal, TraceRun, init_db
from backend.main import app
from backend.utils.config import get_settings


@pytest.fixture(autouse=True)
def clean_db() -> None:
    settings = get_settings()
    original_require_auth = settings.require_auth
    original_api_key = settings.api_key
    original_llm_provider = settings.llm_provider
    original_language_mode = settings.language_mode
    original_default_output_language = settings.default_output_language
    original_strict_language_match = settings.strict_language_match
    original_allow_language_override = settings.allow_language_override
    original_language_retry_limit = settings.language_retry_limit
    settings.require_auth = False
    settings.api_key = "local-dev-key"
    settings.llm_provider = "heuristic"
    settings.language_mode = "auto"
    settings.default_output_language = "en"
    settings.strict_language_match = True
    settings.allow_language_override = True
    settings.language_retry_limit = 2
    init_db()
    db = SessionLocal()
    try:
        db.query(TraceRun).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(TraceRun).delete()
        db.commit()
    finally:
        db.close()
    settings.require_auth = original_require_auth
    settings.api_key = original_api_key
    settings.llm_provider = original_llm_provider
    settings.language_mode = original_language_mode
    settings.default_output_language = original_default_output_language
    settings.strict_language_match = original_strict_language_match
    settings.allow_language_override = original_allow_language_override
    settings.language_retry_limit = original_language_retry_limit


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def sample_trace() -> dict:
    return json.loads(Path("tests/sample_traces.json").read_text(encoding="utf-8"))
