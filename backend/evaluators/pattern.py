from __future__ import annotations

import re

from backend.schemas import ContractDefinition, EvaluationResult, TracePayload


class PatternEvaluator:
    def evaluate(self, trace: TracePayload, contract: ContractDefinition) -> EvaluationResult:
        pattern = contract.config.get("pattern", r"\b\d{3}-\d{2}-\d{4}\b")
        compiled = re.compile(pattern)
        matched = bool(compiled.search(trace.output))
        status = "fail" if matched else "pass"
        confidence = 0.92 if matched else 0.88
        reasoning = "Pattern matched forbidden content." if matched else "No forbidden pattern detected."
        return EvaluationResult(
            contract=contract.id,
            status=status,
            confidence=confidence,
            reasoning_trace=reasoning,
            evidence_pointers=["output"],
        )
