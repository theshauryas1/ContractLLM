from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.crud import build_dashboard_overview, list_trace_runs, summarize_regressions
from backend.db.models import get_db
from backend.schemas import DashboardOverview, RegressionSummary, TraceRunListResponse
from backend.utils.security import require_api_key


router = APIRouter(tags=["reports"])


@router.get("/reports/runs", response_model=TraceRunListResponse)
def get_runs(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> TraceRunListResponse:
    runs = list_trace_runs(db)
    return TraceRunListResponse(runs=runs)


@router.get("/reports/regressions", response_model=RegressionSummary)
def get_regressions(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> RegressionSummary:
    return summarize_regressions(db)


@router.get("/reports/overview", response_model=DashboardOverview)
def get_overview(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> DashboardOverview:
    return build_dashboard_overview(db)
