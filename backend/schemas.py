from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RequirementCategory = Literal["eligibility", "technical", "financial", "legal", "operational"]
ComplianceStatus = Literal["full", "partial", "missing"]
RiskSeverity = Literal["low", "medium", "high", "critical"]


class TranslationBundle(BaseModel):
    source_language: str
    translated_text: str
    target_language: str = "en"


class KnowledgeDocument(BaseModel):
    title: str
    content: str


class TenderAnalysisRequest(BaseModel):
    tender_title: str = "Untitled Tender"
    tender_text: str = ""
    tender_document_base64: str | None = None
    company_profile_text: str = ""
    company_document_base64: str | None = None
    kb_documents: list[KnowledgeDocument] = Field(default_factory=list)
    target_language: str = "auto"
    top_k: int = 3


class ParsedDocument(BaseModel):
    text: str
    source_type: Literal["text", "pdf", "empty"]
    language: str = "en"


class ExtractedRequirement(BaseModel):
    id: str
    text: str
    category: RequirementCategory
    category_label: str
    mandatory: bool = True
    evaluation_weight: float = 1.0


class EvidenceItem(BaseModel):
    source: str
    snippet: str
    score: float
    retrieval_backend: str = "hybrid"


class FeedbackExample(BaseModel):
    corrected_status: ComplianceStatus
    comments: str = ""
    similarity: float = 0.0


class ComplianceMatrixRow(BaseModel):
    requirement_id: str
    requirement_text: str
    category: RequirementCategory
    category_label: str
    status: ComplianceStatus
    status_label: str
    reasoning: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float
    recommended_action: str
    review_required: bool = False
    feedback_examples: list[FeedbackExample] = Field(default_factory=list)
    audit_trail: list[str] = Field(default_factory=list)


class RiskFlag(BaseModel):
    requirement_id: str
    severity: RiskSeverity
    title: str
    rationale: str
    mitigation: str


class ComplianceSummary(BaseModel):
    full_count: int
    partial_count: int
    missing_count: int
    review_required_count: int
    overall_risk: RiskSeverity


class ComplianceMatrix(BaseModel):
    rows: list[ComplianceMatrixRow]
    risks: list[RiskFlag]
    summary: ComplianceSummary
    executive_summary: str
    retrieved_sources: list[str] = Field(default_factory=list)


class TenderAnalysisResponse(BaseModel):
    analysis_id: str
    tender_title: str
    tender_language: str
    output_language: str
    parser_source: Literal["text", "pdf", "empty"]
    requirements: list[ExtractedRequirement]
    matrix: ComplianceMatrix
    provider: str
    retrieval_backend: str = "in-memory"
    reasoning_backend: str = "heuristic"
    created_at: datetime | None = None


class AnalysisSummary(BaseModel):
    analysis_id: str
    tender_title: str
    tender_language: str
    output_language: str
    overall_risk: RiskSeverity
    missing_count: int
    created_at: datetime


class AnalysisListResponse(BaseModel):
    analyses: list[AnalysisSummary]


class DashboardOverview(BaseModel):
    total_analyses: int
    total_requirements: int
    high_risk_analyses: int
    feedback_items: int
    average_confidence: float
    languages: list[str]
    recent_analyses: list[AnalysisSummary]


class FeedbackRequest(BaseModel):
    analysis_id: str
    requirement_id: str
    requirement_text: str
    original_status: ComplianceStatus
    corrected_status: ComplianceStatus
    comments: str = ""


class FeedbackRecord(BaseModel):
    id: int
    analysis_id: str
    requirement_id: str
    requirement_text: str
    original_status: ComplianceStatus
    corrected_status: ComplianceStatus
    comments: str
    created_at: datetime


class FeedbackListResponse(BaseModel):
    items: list[FeedbackRecord]
