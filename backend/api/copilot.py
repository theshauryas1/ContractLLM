from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.gemini import generate_with_gemini

router = APIRouter(tags=["AI Legal Copilot"])

class ChatRequest(BaseModel):
    message: str
    context: str = ""

class DraftRequest(BaseModel):
    template_name: str
    party_details: str
    custom_terms: str = ""

class CitationSearchRequest(BaseModel):
    keywords: str

@router.post("/copilot/chat")
def copilot_chat(request: ChatRequest) -> dict[str, str]:
    system_instruction = (
        "You are the AI Legal Copilot, a helpful, precise legal assistant trained to assist with contracts, "
        "compliance, legal research, and business governance. Keep formatting clean and professional."
    )
    prompt = request.message
    if request.context:
        prompt = f"Context:\n{request.context}\n\nUser Query:\n{request.message}"
        
    reply = generate_with_gemini(prompt, system_instruction=system_instruction)
    return {"reply": reply}

@router.post("/copilot/draft")
def copilot_draft(request: DraftRequest) -> dict[str, str]:
    system_instruction = (
        "You are an expert contract draftsman. Draft a comprehensive, professional, and legally sound agreement "
        "based on the user's template type, party details, and custom terms. Ensure the output is ready to print "
        "and properly structured."
    )
    prompt = (
        f"Template Type: {request.template_name}\n"
        f"Party Details:\n{request.party_details}\n"
        f"Custom Terms/Parameters:\n{request.custom_terms or 'None provided.'}"
    )
    draft = generate_with_gemini(prompt, system_instruction=system_instruction)
    return {"draft": draft}

@router.post("/copilot/search-citations")
def copilot_search_citations(request: CitationSearchRequest) -> dict[str, str]:
    system_instruction = (
        "You are an expert case law citation researcher. Search and list highly relevant legal precedents, "
        "court case summaries, and citations matching the user's keywords. Organize the citations clearly "
        "with summary facts, rulings, and citation numbers."
    )
    prompt = f"Search Query: {request.keywords}"
    results = generate_with_gemini(prompt, system_instruction=system_instruction)
    return {"results": results}
