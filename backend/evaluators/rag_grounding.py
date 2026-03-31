from __future__ import annotations

from backend.rag.retriever import Retriever
from backend.schemas import ContractDefinition, EvaluationResult, TracePayload


class RAGGroundingEvaluator:
    def __init__(self) -> None:
        self.retriever = Retriever()

    def evaluate(self, trace: TracePayload, contract: ContractDefinition) -> EvaluationResult:
        evidence = self.retriever.retrieve(trace.output, top_k=3)
        status = "pass" if evidence else "fail"
        reasoning = "Retrieved grounding evidence for the response." if evidence else "No grounding evidence found."
        confidence = 0.76 if evidence else 0.68
        return EvaluationResult(
            contract=contract.id,
            status=status,
            confidence=confidence,
            reasoning_trace=reasoning,
            evidence_pointers=evidence,
        )
