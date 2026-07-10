import jwt
import pytest
from fastapi.testclient import TestClient

from backend.utils.config import get_settings
from shared.db.models import User, SessionLocal


def test_get_profile_require_auth_false(client: TestClient) -> None:
    """
    Test that when auth is disabled, /api/users/me returns the default guest/test user.
    """
    settings = get_settings()
    original_require_auth = settings.require_auth
    settings.require_auth = False

    try:
        response = client.get("/api/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "usr_test_default"
        assert data["email"] == "guest@legalaip.com"
        assert data["full_name"] == "Guest User"
    finally:
        settings.require_auth = original_require_auth


def test_get_profile_mock_jwt_decoding_and_provisioning(client: TestClient) -> None:
    """
    Test that when auth is enabled, sending a valid JWT parses claims
    and creates a new user profile row in the database.
    """
    settings = get_settings()
    original_require_auth = settings.require_auth
    settings.require_auth = True

    # Build a mock JWT payload
    payload = {
        "sub": "user_clerk_98765",
        "email": "tester@example.com",
        "name": "Alex Tester",
        "lang": "fr",
        "country": "France",
        "tz": "Europe/Paris"
    }
    
    # Encode token with a mock secret
    token = jwt.encode(payload, "secret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Request should succeed, decodes claims, and register user in DB
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_clerk_98765"
        assert data["email"] == "tester@example.com"
        assert data["full_name"] == "Alex Tester"
        assert data["preferred_language"] == "fr"
        assert data["country"] == "France"
        assert data["timezone"] == "Europe/Paris"
        
        # Verify user exists in the local database session
        db = SessionLocal()
        user_in_db = db.query(User).filter(User.user_id == "user_clerk_98765").first()
        assert user_in_db is not None
        assert user_in_db.email == "tester@example.com"
        db.close()
    finally:
        settings.require_auth = original_require_auth


def test_update_profile_preferences(client: TestClient) -> None:
    """
    Test updating profile preferences and making sure they are saved.
    """
    settings = get_settings()
    original_require_auth = settings.require_auth
    settings.require_auth = True

    payload = {
        "sub": "user_clerk_11111",
        "email": "editor@example.com",
        "name": "Original Name"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "full_name": "Updated Name",
        "preferred_language": "de",
        "country": "Germany",
        "timezone": "Europe/Berlin",
        "legal_profession": "Corporate Lawyer",
        "industry": "Finance",
        "default_jurisdiction": "DE-BY",
        "preferred_ai_model": "grok-4"
    }

    try:
        # First retrieve the initial profile to register it
        client.get("/api/users/me", headers=headers)
        
        # Send update request
        response = client.put("/api/users/me", headers=headers, json=update_payload)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response attributes match update payload
        assert data["full_name"] == "Updated Name"
        assert data["preferred_language"] == "de"
        assert data["country"] == "Germany"
        assert data["timezone"] == "Europe/Berlin"
        assert data["legal_profession"] == "Corporate Lawyer"
        assert data["industry"] == "Finance"
        assert data["default_jurisdiction"] == "DE-BY"
        assert data["preferred_ai_model"] == "grok-4"

        # Verify database session state matches updates
        db = SessionLocal()
        user = db.query(User).filter(User.user_id == "user_clerk_11111").first()
        assert user.full_name == "Updated Name"
        assert user.preferred_language == "de"
        assert user.default_jurisdiction == "DE-BY"
        db.close()
    finally:
        settings.require_auth = original_require_auth
