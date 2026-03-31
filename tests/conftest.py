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
    settings.require_auth = False
    settings.api_key = "local-dev-key"
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


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def sample_trace() -> dict:
    return json.loads(Path("tests/sample_traces.json").read_text(encoding="utf-8"))
