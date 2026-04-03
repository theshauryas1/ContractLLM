from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.compliance import TenderComplianceOrchestrator
from backend.db.crud import (
    create_analysis_run,
    get_analysis_run,
    get_document_asset,
    get_stored_knowledge_documents,
    list_analysis_runs,
)
from backend.db.models import get_db
from backend.schemas import AnalysisListResponse, KnowledgeDocument, TenderAnalysisRequest, TenderAnalysisResponse
from backend.utils.security import require_api_key


router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=TenderAnalysisResponse)
def analyze_tender(
    payload: TenderAnalysisRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> TenderAnalysisResponse:
    orchestrator = TenderComplianceOrchestrator()
    hydrated_payload = _hydrate_payload_from_documents(payload, db)
    result = orchestrator.analyze(hydrated_payload, db)
    return create_analysis_run(db, hydrated_payload.model_dump(mode="json"), result)


@router.get("/analyses", response_model=AnalysisListResponse)
def get_analyses(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> AnalysisListResponse:
    return list_analysis_runs(db)


@router.get("/analyses/{analysis_id}", response_model=TenderAnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> TenderAnalysisResponse:
    analysis = get_analysis_run(db, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


def _hydrate_payload_from_documents(payload: TenderAnalysisRequest, db: Session) -> TenderAnalysisRequest:
    updates: dict = {}

    if payload.tender_document_id is not None:
        tender_document = get_document_asset(db, payload.tender_document_id)
        if tender_document is None:
            raise HTTPException(status_code=404, detail="Tender document not found")
        updates["tender_text"] = tender_document.extracted_text
        updates["tender_document_base64"] = None

    if payload.company_document_id is not None:
        company_document = get_document_asset(db, payload.company_document_id)
        if company_document is None:
            raise HTTPException(status_code=404, detail="Company document not found")
        updates["company_profile_text"] = company_document.extracted_text
        updates["company_document_base64"] = None

    if payload.knowledge_document_ids:
        stored_documents = get_stored_knowledge_documents(db, payload.knowledge_document_ids)
        updates["kb_documents"] = [
            *payload.kb_documents,
            *[KnowledgeDocument(title=item.title, content=item.content) for item in stored_documents],
        ]

    return payload.model_copy(update=updates)
