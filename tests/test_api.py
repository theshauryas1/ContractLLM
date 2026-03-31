from pathlib import Path

from backend.utils.config import get_settings


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_trace_ingest_and_reports_flow(client, sample_trace) -> None:
    ingest_response = client.post(
        "/api/trace",
        json={"trace": sample_trace, "contract_path": "contracts/default.yaml"},
    )
    assert ingest_response.status_code == 200
    body = ingest_response.json()
    assert body["trace_id"] == sample_trace["trace_id"]
    assert len(body["results"]["results"]) == 4

    runs_response = client.get("/api/reports/runs")
    assert runs_response.status_code == 200
    assert len(runs_response.json()["runs"]) == 1

    overview_response = client.get("/api/reports/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["total_runs"] == 1
    assert "v2" in overview["tracked_prompt_versions"]

    regressions_response = client.get("/api/reports/regressions")
    assert regressions_response.status_code == 200
    regression = regressions_response.json()
    assert regression["total_runs"] == 1
    assert len(regression["points"]) == 1


def test_contract_routes_support_listing_and_creation(client, tmp_path) -> None:
    contract_file = tmp_path / "contracts.yaml"
    contract_file.write_text("contracts: []\n", encoding="utf-8")

    create_response = client.post(
        "/api/contracts",
        json={
            "contract_path": str(contract_file),
            "contract": {
                "id": "must_be_json",
                "type": "structural",
                "description": "Return JSON output",
                "config": {"format": "json"},
            },
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["contract_id"] == "must_be_json"

    list_response = client.get("/api/contracts", params={"contract_path": str(contract_file)})
    assert list_response.status_code == 200
    contracts = list_response.json()["contracts"]
    assert len(contracts) == 1
    assert contracts[0]["id"] == "must_be_json"


def test_contract_creation_404s_for_missing_file(client, tmp_path) -> None:
    missing_path = tmp_path / "missing.yaml"
    response = client.post(
        "/api/contracts",
        json={
            "contract_path": str(missing_path),
            "contract": {
                "id": "example",
                "type": "semantic",
                "description": "example",
                "config": {},
            },
        },
    )
    assert response.status_code == 404


def test_default_contract_file_exists() -> None:
    assert Path("contracts/default.yaml").exists()


def test_auth_is_enforced_when_enabled(client, sample_trace) -> None:
    settings = get_settings()
    settings.require_auth = True
    settings.api_key = "secret-key"

    unauthorized = client.post(
        "/api/trace",
        json={"trace": sample_trace, "contract_path": "contracts/default.yaml"},
    )
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/trace",
        json={"trace": sample_trace, "contract_path": "contracts/default.yaml"},
        headers={"x-api-key": "secret-key"},
    )
    assert authorized.status_code == 200
