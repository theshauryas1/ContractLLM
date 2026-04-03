import hashlib

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from backend.compliance.parser_agent import ParserAgent
from backend.db.crud import create_document_asset, get_document_asset, list_document_assets
from backend.db.models import get_db
from backend.schemas import DocumentKind, DocumentListResponse, DocumentUploadResponse
from backend.utils.security import require_api_key


router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    kind: DocumentKind = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> DocumentUploadResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    parser = ParserAgent()
    parsed = parser.parse_bytes(data, file.filename or "upload.bin", file.content_type)
    return create_document_asset(
        db,
        kind=kind,
        filename=file.filename or "upload.bin",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        content_hash=hashlib.sha256(data).hexdigest(),
        file_bytes=data,
        extracted_text=parsed.text,
        source_language=parsed.language,
    )


@router.get("/documents", response_model=DocumentListResponse)
def get_documents(db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> DocumentListResponse:
    return list_document_assets(db)


@router.get("/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)) -> Response:
    document = get_document_asset(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return Response(
        content=document.file_bytes,
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{document.filename}"'},
    )
