from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared.db.crud import build_dashboard_overview
from shared.db.models import get_db
from shared.schemas import DashboardOverview
from backend.utils.security import require_api_key


router = APIRouter(tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def get_overview(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> DashboardOverview:
    return build_dashboard_overview(db)
