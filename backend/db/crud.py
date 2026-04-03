from __future__ import annotations

import re

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.db.models import AnalysisRun, FeedbackEntry
from backend.schemas import (
    AnalysisListResponse,
    AnalysisSummary,
    DashboardOverview,
    FeedbackExample,
    FeedbackListResponse,
    FeedbackRecord,
    FeedbackRequest,
    TenderAnalysisResponse,
)
from backend.utils.config import get_settings


def create_analysis_run(db: Session, payload: dict, result: TenderAnalysisResponse) -> TenderAnalysisResponse:
    row = AnalysisRun(
        analysis_id=result.analysis_id,
        tender_title=result.tender_title,
        tender_language=result.tender_language,
        output_language=result.output_language,
        input_payload=payload,
        output_payload=result.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    stored = result.model_copy(update={"created_at": row.created_at})
    row.output_payload = stored.model_dump(mode="json")
    db.commit()
    return stored


def list_analysis_runs(db: Session) -> AnalysisListResponse:
    rows = db.query(AnalysisRun).order_by(desc(AnalysisRun.id)).all()
    analyses = [
        AnalysisSummary(
            analysis_id=row.analysis_id,
            tender_title=row.tender_title,
            tender_language=row.tender_language,
            output_language=row.output_language,
            overall_risk=row.output_payload["matrix"]["summary"]["overall_risk"],
            missing_count=row.output_payload["matrix"]["summary"]["missing_count"],
            created_at=row.created_at,
        )
        for row in rows
    ]
    return AnalysisListResponse(analyses=analyses)


def get_analysis_run(db: Session, analysis_id: str) -> TenderAnalysisResponse | None:
    row = db.query(AnalysisRun).filter(AnalysisRun.analysis_id == analysis_id).one_or_none()
    if row is None:
        return None
    return TenderAnalysisResponse.model_validate(row.output_payload)


def create_feedback_entry(db: Session, payload: FeedbackRequest) -> FeedbackRecord:
    row = FeedbackEntry(
        analysis_id=payload.analysis_id,
        requirement_id=payload.requirement_id,
        requirement_text=payload.requirement_text,
        original_status=payload.original_status,
        corrected_status=payload.corrected_status,
        comments=payload.comments,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return FeedbackRecord(
        id=row.id,
        analysis_id=row.analysis_id,
        requirement_id=row.requirement_id,
        requirement_text=row.requirement_text,
        original_status=row.original_status,
        corrected_status=row.corrected_status,
        comments=row.comments,
        created_at=row.created_at,
    )


def list_feedback_entries(db: Session) -> FeedbackListResponse:
    rows = db.query(FeedbackEntry).order_by(desc(FeedbackEntry.id)).all()
    return FeedbackListResponse(
        items=[
            FeedbackRecord(
                id=row.id,
                analysis_id=row.analysis_id,
                requirement_id=row.requirement_id,
                requirement_text=row.requirement_text,
                original_status=row.original_status,
                corrected_status=row.corrected_status,
                comments=row.comments,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


def find_feedback_examples(db: Session | None, requirement_text: str) -> list[FeedbackExample]:
    settings = get_settings()
    if db is None or not settings.enable_feedback_loop:
        return []

    rows = db.query(FeedbackEntry).order_by(desc(FeedbackEntry.id)).limit(25).all()
    ranked: list[tuple[float, FeedbackExample]] = []
    for row in rows:
        similarity = _text_similarity(requirement_text, row.requirement_text)
        if similarity < 0.3:
            continue
        ranked.append(
            (
                similarity,
                FeedbackExample(
                    corrected_status=row.corrected_status,
                    comments=row.comments,
                    similarity=round(similarity, 3),
                ),
            )
        )
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [example for _, example in ranked[:3]]


def build_dashboard_overview(db: Session) -> DashboardOverview:
    analysis_rows = db.query(AnalysisRun).order_by(desc(AnalysisRun.id)).all()
    feedback_rows = db.query(FeedbackEntry).order_by(desc(FeedbackEntry.id)).all()

    total_analyses = len(analysis_rows)
    total_requirements = sum(len(row.output_payload["matrix"]["rows"]) for row in analysis_rows)
    high_risk_analyses = sum(
        1 for row in analysis_rows if row.output_payload["matrix"]["summary"]["overall_risk"] in {"high", "critical"}
    )
    confidence_values = [
        decision["confidence"]
        for row in analysis_rows
        for decision in row.output_payload["matrix"]["rows"]
    ]
    languages = sorted({row.tender_language for row in analysis_rows})

    recent_analyses = [
        AnalysisSummary(
            analysis_id=row.analysis_id,
            tender_title=row.tender_title,
            tender_language=row.tender_language,
            output_language=row.output_language,
            overall_risk=row.output_payload["matrix"]["summary"]["overall_risk"],
            missing_count=row.output_payload["matrix"]["summary"]["missing_count"],
            created_at=row.created_at,
        )
        for row in analysis_rows[:6]
    ]

    return DashboardOverview(
        total_analyses=total_analyses,
        total_requirements=total_requirements,
        high_risk_analyses=high_risk_analyses,
        feedback_items=len(feedback_rows),
        average_confidence=round(sum(confidence_values) / max(len(confidence_values), 1), 3),
        languages=languages,
        recent_analyses=recent_analyses,
    )


def _text_similarity(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"\w+", left.lower()))
    right_tokens = set(re.findall(r"\w+", right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
