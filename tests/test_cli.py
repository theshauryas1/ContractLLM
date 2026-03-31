import json

from typer.testing import CliRunner

from cli.llmtest import app


runner = CliRunner()


def test_cli_run_outputs_bundle() -> None:
    result = runner.invoke(app, ["run", "tests/sample_traces.json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["trace_id"] == "trace-001"
    assert len(payload["results"]) == 4
