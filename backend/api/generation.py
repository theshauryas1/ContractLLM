from fastapi import APIRouter, Depends

from backend.core.generator import LanguagePreservingGenerator
from backend.schemas import GenerateRequest, GenerateResponse
from backend.utils.security import require_api_key


router = APIRouter(tags=["generation"])


@router.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest, _: None = Depends(require_api_key)) -> GenerateResponse:
    generator = LanguagePreservingGenerator()
    return generator.generate(payload)
