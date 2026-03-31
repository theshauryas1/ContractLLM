from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ContractType = Literal["semantic", "pattern", "structural", "rag_grounding"]


class TracePayload(BaseModel):
    trace_id: str
    prompt_version: str = "v1"
    input_text: str
    output: str
    context: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceIngestRequest(BaseModel):
    trace: TracePayload
    contract_path: str = "contracts/default.yaml"


class ContractDefinition(BaseModel):
    id: str
    type: ContractType
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


class FailureClassification(BaseModel):
    failure_type: Literal["hallucination", "format_violation", "inconsistency", "instruction_drift"]
    severity: Literal["low", "medium", "high"]
    rationale: str


class EvaluationResult(BaseModel):
    contract: str
    status: Literal["pass", "fail"]
    confidence: float
    reasoning_trace: str = ""
    evidence_pointers: list[str] = Field(default_factory=list)
    failure: FailureClassification | None = None


class RepairSuggestion(BaseModel):
    contract: str
    strategy: Literal["inject_constraints", "add_context", "adjust_system_prompt"]
    prompt_patch: str


class EvaluationBundle(BaseModel):
    trace_id: str
    source_language: str = "en"
    pass_rate: float
    results: list[EvaluationResult]
    failures: list[FailureClassification]
    suggested_repairs: list[RepairSuggestion]


class TraceRunResponse(BaseModel):
    run_id: int
    trace_id: str
    results: EvaluationBundle


class ContractCreateRequest(BaseModel):
    contract_path: str = "contracts/default.yaml"
    contract: ContractDefinition


class ContractListResponse(BaseModel):
    contracts: list[ContractDefinition]


class StoredTraceRun(BaseModel):
    id: int
    trace_id: str
    prompt_version: str
    results: dict[str, Any]
    created_at: datetime


class TraceRunListResponse(BaseModel):
    runs: list[StoredTraceRun]


class RegressionPoint(BaseModel):
    run_id: int
    trace_id: str
    pass_rate: float


class RegressionSummary(BaseModel):
    total_runs: int
    delta: float
    points: list[RegressionPoint]


class TranslationBundle(BaseModel):
    source_language: str
    translated_text: str
    target_language: str = "en"


class DashboardFailure(BaseModel):
    trace_id: str
    contract: str
    failure_type: str
    severity: str
    rationale: str


class DashboardOverview(BaseModel):
    total_runs: int
    average_pass_rate: float
    latest_pass_rate: float
    failing_runs: int
    tracked_prompt_versions: list[str]
    recent_failures: list[DashboardFailure]
