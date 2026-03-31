from __future__ import annotations

import json

from backend.schemas import ContractDefinition, EvaluationResult, TracePayload


class StructuralEvaluator:
    def evaluate(self, trace: TracePayload, contract: ContractDefinition) -> EvaluationResult:
        expected_format = contract.config.get("format", "json")
        status = "pass"
        confidence = 0.95
        reasoning = f"Checked output against expected format `{expected_format}`."
        evidence = ["output"]

        if expected_format == "json":
            try:
                json.loads(trace.output)
            except json.JSONDecodeError as exc:
                status = "fail"
                confidence = 0.9
                reasoning = f"Output is not valid JSON: {exc.msg}"

        return EvaluationResult(
            contract=contract.id,
            status=status,
            confidence=confidence,
            reasoning_trace=reasoning,
            evidence_pointers=evidence,
        )
