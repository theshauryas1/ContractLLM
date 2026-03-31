from backend.schemas import ContractDefinition, EvaluationResult, FailureClassification


class FailureTaxonomy:
    def classify(self, result: EvaluationResult, contract: ContractDefinition) -> FailureClassification:
        failure_type = "instruction_drift"
        severity = "medium"

        if contract.type == "semantic":
            failure_type = "hallucination"
            severity = "high"
        elif contract.type == "structural":
            failure_type = "format_violation"
            severity = "medium"
        elif contract.type == "pattern":
            failure_type = "inconsistency"
            severity = "high" if result.confidence > 0.7 else "medium"
        elif contract.type == "rag_grounding":
            failure_type = "hallucination"
            severity = "high"

        return FailureClassification(
            failure_type=failure_type,
            severity=severity,
            rationale=result.reasoning_trace or "Derived from evaluator outcome.",
        )
