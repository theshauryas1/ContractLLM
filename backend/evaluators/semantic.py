from __future__ import annotations

import re

from backend.agents.semantic_judge import SemanticJudge
from backend.schemas import ContractDefinition, EvaluationResult, TracePayload


class SemanticEvaluator:
    def __init__(self) -> None:
        self.judge = SemanticJudge()

    def evaluate(self, trace: TracePayload, contract: ContractDefinition) -> EvaluationResult:
        verdict = self.judge.judge(trace.context, trace.output)
        claims = self._extract_claims(trace.output)
        unsupported = [claim for claim in claims if claim.lower() not in trace.context.lower()]
        status = "fail" if unsupported else verdict["status"]
        confidence = 0.81 if unsupported else verdict["confidence"]
        reasoning = verdict["reasoning"]
        if unsupported:
            reasoning = f"Unsupported claims detected: {unsupported[:3]}"

        evidence = verdict["evidence_pointers"]
        return EvaluationResult(
            contract=contract.id,
            status=status,
            confidence=confidence,
            reasoning_trace=reasoning,
            evidence_pointers=evidence,
        )

    def _extract_claims(self, output: str) -> list[str]:
        fragments = re.split(r"[.!?]\s+", output)
        return [fragment.strip() for fragment in fragments if len(fragment.strip().split()) >= 4]
