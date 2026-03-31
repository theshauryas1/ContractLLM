from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.evaluator import EvaluationOrchestrator
from backend.db.crud import create_trace_run
from backend.db.models import get_db
from backend.schemas import TraceIngestRequest, TraceRunResponse
from backend.utils.security import require_api_key


router = APIRouter(tags=["ingest"])


@router.post("/trace", response_model=TraceRunResponse)
def ingest_trace(
    payload: TraceIngestRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> TraceRunResponse:
    orchestrator = EvaluationOrchestrator()
    evaluation = orchestrator.evaluate_trace(payload.trace, payload.contract_path)
    run = create_trace_run(
        db=db,
        trace_id=payload.trace.trace_id,
        prompt_version=payload.trace.prompt_version,
        input_payload=payload.trace.model_dump(mode="json"),
        results=evaluation.model_dump(mode="json"),
    )
    return TraceRunResponse(run_id=run.id, trace_id=run.trace_id, results=evaluation)
