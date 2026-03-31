from pathlib import Path

from backend.core.contract_engine import ContractEngine
from backend.db.crud import build_dashboard_overview, create_trace_run, list_trace_runs, summarize_regressions
from backend.db.models import SessionLocal
from backend.schemas import ContractDefinition


def test_contract_engine_appends_and_loads_contracts(tmp_path) -> None:
    contract_path = tmp_path / "contracts.yaml"
    contract_path.write_text("contracts: []\n", encoding="utf-8")
    engine = ContractEngine()
    contract = ContractDefinition(
        id="no_pii",
        type="pattern",
        description="No PII allowed",
        config={"pattern": "\\d+"},
    )

    engine.append_contract(contract_path, contract)
    contracts = engine.load_contracts(contract_path)

    assert len(contracts) == 1
    assert contracts[0].id == "no_pii"


def test_crud_regression_and_overview_summaries() -> None:
    db = SessionLocal()
    try:
        create_trace_run(
            db,
            trace_id="trace-1",
            prompt_version="v1",
            input_payload={"metadata": {"model": "model-a"}},
            results={"pass_rate": 0.75, "results": [], "failures": []},
        )
        create_trace_run(
            db,
            trace_id="trace-2",
            prompt_version="v2",
            input_payload={"metadata": {"model": "model-b"}},
            results={
                "pass_rate": 0.5,
                "results": [
                    {
                        "contract": "context_faithfulness",
                        "failure": {
                            "failure_type": "hallucination",
                            "severity": "high",
                            "rationale": "Unsupported claim detected",
                        },
                    }
                ],
                "failures": [{"failure_type": "hallucination"}],
            },
        )

        runs = list_trace_runs(db)
        regression = summarize_regressions(db)
        overview = build_dashboard_overview(db)
    finally:
        db.close()

    assert len(runs) == 2
    assert regression.total_runs == 2
    assert regression.delta == -0.25
    assert overview.total_runs == 2
    assert overview.failing_runs == 1
    assert overview.recent_failures[0].failure_type == "hallucination"
    assert sorted(overview.tracked_prompt_versions) == ["v1", "v2"]
