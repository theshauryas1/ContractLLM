from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.compliance import TenderComplianceOrchestrator
from backend.db.crud import create_analysis_run, get_analysis_run, list_analysis_runs
from backend.db.models import get_db
from backend.schemas import AnalysisListResponse, TenderAnalysisRequest, TenderAnalysisResponse
from backend.utils.security import require_api_key


router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=TenderAnalysisResponse)
def analyze_tender(
    payload: TenderAnalysisRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> TenderAnalysisResponse:
    orchestrator = TenderComplianceOrchestrator()
    result = orchestrator.analyze(payload, db)
    return create_analysis_run(db, payload.model_dump(mode="json"), result)


@router.get("/analyses", response_model=AnalysisListResponse)
def get_analyses(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> AnalysisListResponse:
    return list_analysis_runs(db)


@router.get("/analyses/{analysis_id}", response_model=TenderAnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> TenderAnalysisResponse:
    analysis = get_analysis_run(db, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis
