from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.evaluator import EvaluationOrchestrator
from backend.schemas import TracePayload


app = typer.Typer(help="CLI for contract-driven LLM trace evaluation.")


@app.callback()
def main() -> None:
    """Expose a command group so `run` behaves as an explicit subcommand."""


@app.command()
def run(trace_file: str, contract_path: str = "contracts/default.yaml") -> None:
    raw = json.loads(Path(trace_file).read_text(encoding="utf-8"))
    trace = TracePayload(**raw)
    bundle = EvaluationOrchestrator().evaluate_trace(trace, contract_path)
    typer.echo(bundle.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
