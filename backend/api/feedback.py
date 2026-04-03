from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.crud import create_feedback_entry, list_feedback_entries
from backend.db.models import get_db
from backend.schemas import FeedbackListResponse, FeedbackRecord, FeedbackRequest
from backend.utils.security import require_api_key


router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackRecord)
def create_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> FeedbackRecord:
    return create_feedback_entry(db, payload)


@router.get("/feedback", response_model=FeedbackListResponse)
def get_feedback(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> FeedbackListResponse:
    return list_feedback_entries(db)
