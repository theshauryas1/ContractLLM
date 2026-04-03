import httpx

from backend.db.models import KnowledgeChunk, SessionLocal
from backend.utils.config import get_settings


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tender_analysis_flow_returns_compliance_matrix(client) -> None:
    payload = {
        "tender_title": "Municipal Maintenance Framework",
        "tender_text": (
            "The bidder must provide ISO 9001 certification. "
            "The bidder shall demonstrate annual turnover above EUR 2 million. "
            "The bidder must comply with GDPR."
        ),
        "company_profile_text": (
            "Our company holds ISO 9001 certification, maintains GDPR controls, "
            "and reported annual turnover of EUR 2.4 million last year."
        ),
        "kb_documents": [
            {
                "title": "Public References",
                "content": "We delivered municipal transport and housing support projects."
            }
        ],
        "target_language": "auto"
    }

    analyze_response = client.post("/api/analyze", json=payload)
    assert analyze_response.status_code == 200
    body = analyze_response.json()
    assert body["tender_title"] == "Municipal Maintenance Framework"
    assert body["tender_language"] == "en"
    assert len(body["requirements"]) >= 3
    assert body["matrix"]["summary"]["full_count"] >= 2

    list_response = client.get("/api/analyses")
    assert list_response.status_code == 200
    assert len(list_response.json()["analyses"]) == 1

    detail_response = client.get(f"/api/analyses/{body['analysis_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["analysis_id"] == body["analysis_id"]

    overview_response = client.get("/api/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["total_analyses"] == 1
    assert overview["total_requirements"] >= 3


def test_multilingual_analysis_preserves_tender_language_by_default(client) -> None:
    payload = {
        "tender_title": "Appel d'offres services publics",
        "tender_text": (
            "Certification ISO 9001 obligatoire. "
            "Enregistrement obligatoire. "
            "Conformite GDPR obligatoire."
        ),
        "company_profile_text": (
            "Our company holds ISO 9001 certification, maintains GDPR controls, "
            "and keeps all required registrations active."
        ),
        "target_language": "auto"
    }

    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["tender_language"] == "fr"
    assert body["output_language"] == "fr"
    assert body["requirements"][0]["category_label"]
    assert body["matrix"]["rows"][0]["status_label"] in {"Complet", "Partiel", "Manquant"}


def test_feedback_endpoint_records_feedback_and_updates_overview(client) -> None:
    payload = {
        "tender_title": "Eligibility Check",
        "tender_text": "The bidder must provide evidence of experience.",
        "company_profile_text": "The company profile does not mention public references.",
        "target_language": "auto"
    }

    analysis = client.post("/api/analyze", json=payload).json()
    row = analysis["matrix"]["rows"][0]

    feedback_response = client.post(
        "/api/feedback",
        json={
            "analysis_id": analysis["analysis_id"],
            "requirement_id": row["requirement_id"],
            "requirement_text": row["requirement_text"],
            "original_status": row["status"],
            "corrected_status": "partial",
            "comments": "Reference was found in annex."
        },
    )
    assert feedback_response.status_code == 200
    assert feedback_response.json()["corrected_status"] == "partial"

    feedback_list = client.get("/api/feedback")
    assert feedback_list.status_code == 200
    assert len(feedback_list.json()["items"]) == 1

    overview = client.get("/api/overview").json()
    assert overview["feedback_items"] == 1


def test_analysis_persists_knowledge_chunks_without_duplicate_scope_rows(client) -> None:
    payload = {
        "tender_title": "Knowledge Persistence",
        "tender_text": "The bidder must provide ISO 9001 certification.",
        "company_profile_text": "Our company holds ISO 9001 certification and public-sector references.",
        "kb_documents": [{"title": "Annex", "content": "ISO 9001 certificate attached."}],
    }

    first = client.post("/api/analyze", json=payload)
    assert first.status_code == 200
    second = client.post("/api/analyze", json=payload)
    assert second.status_code == 200

    db = SessionLocal()
    try:
        chunk_count = db.query(KnowledgeChunk).count()
    finally:
        db.close()

    assert chunk_count > 0
    assert second.json()["retrieval_backend"] in {"database-fallback", "pgvector"}


def test_xai_reasoning_provider_returns_structured_decision(monkeypatch, client) -> None:
    settings = get_settings()
    settings.llm_provider = "xai"
    settings.xai_api_key = "test-key"

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": (
                                    '{"status":"full","reasoning":"Evidence fully supports this requirement.",'
                                    '"confidence":0.91,"recommended_action":"Reference the certificate directly.",'
                                    '"review_required":false,"audit_notes":["xAI reviewed evidence.","Structured output returned."]}'
                                ),
                            }
                        ],
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        assert args[0].endswith("/responses")
        return MockResponse()

    monkeypatch.setattr(httpx, "post", fake_post)

    response = client.post(
        "/api/analyze",
        json={
            "tender_title": "xAI Reasoning",
            "tender_text": "The bidder must provide ISO 9001 certification.",
            "company_profile_text": "Our company holds ISO 9001 certification.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reasoning_backend"] == "xai"
    assert body["provider"].startswith("xai+")
    assert body["matrix"]["rows"][0]["reasoning"] == "Evidence fully supports this requirement."


def test_auth_is_enforced_when_enabled(client) -> None:
    settings = get_settings()
    settings.require_auth = True
    settings.api_key = "secret-key"

    unauthorized = client.post(
        "/api/analyze",
        json={
            "tender_title": "Secured Request",
            "tender_text": "The bidder must provide ISO 9001 certification.",
            "company_profile_text": "ISO 9001 certification is held.",
        },
    )
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/analyze",
        json={
            "tender_title": "Secured Request",
            "tender_text": "The bidder must provide ISO 9001 certification.",
            "company_profile_text": "ISO 9001 certification is held.",
        },
        headers={"x-api-key": "secret-key"},
    )
    assert authorized.status_code == 200
