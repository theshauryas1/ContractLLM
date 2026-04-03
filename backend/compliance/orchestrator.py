from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from backend.compliance.compliance_agent import ComplianceAgent
from backend.compliance.extractor_agent import ExtractorAgent
from backend.compliance.localization import localize_summary
from backend.compliance.parser_agent import ParserAgent
from backend.compliance.rag_agent import RAGAgent
from backend.compliance.risk_agent import RiskAgent
from backend.db.crud import find_feedback_examples
from backend.schemas import ComplianceMatrix, ComplianceSummary, TenderAnalysisRequest, TenderAnalysisResponse
from backend.utils.config import get_settings


class TenderComplianceOrchestrator:
    SUPPORTED_OUTPUT_LANGUAGES = {"auto", "en", "fr", "de", "es", "nl", "hi"}

    def __init__(self) -> None:
        self.settings = get_settings()
        self.parser_agent = ParserAgent()
        self.extractor_agent = ExtractorAgent()
        self.rag_agent = RAGAgent()
        self.compliance_agent = ComplianceAgent()
        self.risk_agent = RiskAgent()

    def analyze(self, payload: TenderAnalysisRequest, db: Session | None = None) -> TenderAnalysisResponse:
        tender = self.parser_agent.parse(payload.tender_text, payload.tender_document_base64)
        company = self.parser_agent.parse(payload.company_profile_text, payload.company_document_base64)
        output_language = self._resolve_output_language(payload.target_language, tender.language)
        requirements, normalized_text = self.extractor_agent.extract(tender.text, tender.language, output_language)
        scopes, retrieval_backend = self.rag_agent.prepare_scope(company.text, payload.kb_documents, db)

        rows = []
        for requirement in requirements:
            evidence = self.rag_agent.retrieve(
                requirement_text=normalized_text.get(requirement.id, requirement.text),
                company_profile_text=company.text,
                kb_documents=payload.kb_documents,
                top_k=payload.top_k,
                db=db,
                scopes=scopes,
            )
            feedback_examples = find_feedback_examples(db, normalized_text.get(requirement.id, requirement.text)) if db else []
            rows.append(
                self.compliance_agent.assess(
                    requirement_id=requirement.id,
                    requirement_text=requirement.text,
                    category=requirement.category,
                    category_label=requirement.category_label,
                    evidence=evidence,
                    output_language=output_language,
                    feedback_examples=feedback_examples,
                )
            )

        risks, overall_risk = self.risk_agent.analyze(rows, output_language)
        full_count = sum(1 for row in rows if row.status == "full")
        partial_count = sum(1 for row in rows if row.status == "partial")
        missing_count = sum(1 for row in rows if row.status == "missing")
        review_required_count = sum(1 for row in rows if row.review_required)
        retrieved_sources = sorted({item.source for row in rows for item in row.evidence})
        reasoning_backend = "xai" if self.settings.llm_provider == "xai" and self.settings.xai_api_key else "heuristic"
        provider = f"{reasoning_backend}+{retrieval_backend}"

        return TenderAnalysisResponse(
            analysis_id=f"analysis-{uuid4().hex[:12]}",
            tender_title=payload.tender_title,
            tender_language=tender.language,
            output_language=output_language,
            parser_source=tender.source_type,
            requirements=requirements,
            matrix=ComplianceMatrix(
                rows=rows,
                risks=risks,
                summary=ComplianceSummary(
                    full_count=full_count,
                    partial_count=partial_count,
                    missing_count=missing_count,
                    review_required_count=review_required_count,
                    overall_risk=overall_risk,
                ),
                executive_summary=localize_summary(
                    full_count=full_count,
                    partial_count=partial_count,
                    missing_count=missing_count,
                    overall_risk=overall_risk,
                    language=output_language,
                ),
                retrieved_sources=retrieved_sources,
            ),
            provider=provider,
            retrieval_backend=retrieval_backend,
            reasoning_backend=reasoning_backend,
        )

    def _resolve_output_language(self, requested_language: str, tender_language: str) -> str:
        requested = requested_language if requested_language in self.SUPPORTED_OUTPUT_LANGUAGES else "auto"
        if requested != "auto" and self.settings.allow_language_override:
            return requested
        if self.settings.language_mode == "fixed":
            return self.settings.default_output_language
        return tender_language if tender_language != "unknown" else self.settings.default_output_language
