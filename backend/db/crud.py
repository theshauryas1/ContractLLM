from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.db.models import TraceRun
from backend.schemas import DashboardFailure, DashboardOverview, RegressionPoint, RegressionSummary, StoredTraceRun


def create_trace_run(
    db: Session,
    trace_id: str,
    prompt_version: str,
    input_payload: dict,
    results: dict,
) -> TraceRun:
    run = TraceRun(
        trace_id=trace_id,
        prompt_version=prompt_version,
        input_payload=input_payload,
        results=results,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_trace_runs(db: Session) -> list[StoredTraceRun]:
    rows = db.query(TraceRun).order_by(desc(TraceRun.id)).all()
    return [
        StoredTraceRun(
            id=row.id,
            trace_id=row.trace_id,
            prompt_version=row.prompt_version,
            input_payload=row.input_payload,
            results=row.results,
            created_at=row.created_at,
        )
        for row in rows
    ]


def summarize_regressions(db: Session) -> RegressionSummary:
    rows = db.query(TraceRun).order_by(TraceRun.created_at.asc()).all()
    points = [
        RegressionPoint(
            run_id=row.id,
            trace_id=row.trace_id,
            pass_rate=row.results.get("pass_rate", 0.0),
        )
        for row in rows
    ]
    latest = points[-1].pass_rate if points else 0.0
    previous = points[-2].pass_rate if len(points) > 1 else latest
    delta = round(latest - previous, 3)
    return RegressionSummary(total_runs=len(points), delta=delta, points=points)


def build_dashboard_overview(db: Session) -> DashboardOverview:
    rows = db.query(TraceRun).order_by(desc(TraceRun.id)).all()
    total_runs = len(rows)
    pass_rates = [row.results.get("pass_rate", 0.0) for row in rows]
    average_pass_rate = round(sum(pass_rates) / max(total_runs, 1), 3)
    latest_pass_rate = pass_rates[0] if pass_rates else 0.0
    failing_runs = sum(1 for row in rows if row.results.get("failures"))
    tracked_prompt_versions = sorted({row.prompt_version for row in rows})

    recent_failures: list[DashboardFailure] = []
    for row in rows:
        for result in row.results.get("results", []):
            failure = result.get("failure")
            if not failure:
                continue
            recent_failures.append(
                DashboardFailure(
                    trace_id=row.trace_id,
                    contract=result["contract"],
                    failure_type=failure["failure_type"],
                    severity=failure["severity"],
                    rationale=failure["rationale"],
                )
            )
            if len(recent_failures) >= 8:
                break
        if len(recent_failures) >= 8:
            break

    return DashboardOverview(
        total_runs=total_runs,
        average_pass_rate=average_pass_rate,
        latest_pass_rate=latest_pass_rate,
        failing_runs=failing_runs,
        tracked_prompt_versions=tracked_prompt_versions,
        recent_failures=recent_failures,
    )
