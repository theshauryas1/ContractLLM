from __future__ import annotations

from backend.core.contract_engine import ContractEngine
from backend.core.failure_taxonomy import FailureTaxonomy
from backend.core.repair_engine import RepairEngine
from backend.evaluators.pattern import PatternEvaluator
from backend.evaluators.rag_grounding import RAGGroundingEvaluator
from backend.evaluators.semantic import SemanticEvaluator
from backend.evaluators.structural import StructuralEvaluator
from backend.multilingual.language_detector import LanguageDetector
from backend.multilingual.translator import Translator
from backend.schemas import ContractDefinition, EvaluationBundle, EvaluationResult, FailureClassification, TracePayload


class EvaluationOrchestrator:
    def __init__(self) -> None:
        self.contract_engine = ContractEngine()
        self.failure_taxonomy = FailureTaxonomy()
        self.repair_engine = RepairEngine()
        self.language_detector = LanguageDetector()
        self.translator = Translator()
        self.evaluators = {
            "structural": StructuralEvaluator(),
            "pattern": PatternEvaluator(),
            "semantic": SemanticEvaluator(),
            "rag_grounding": RAGGroundingEvaluator(),
        }

    def evaluate_trace(self, trace: TracePayload, contract_path: str) -> EvaluationBundle:
        source_language = trace.metadata.get("language") or self.language_detector.detect(
            " ".join([trace.input_text, trace.context, trace.output])
        )
        normalized_trace = self._normalize_trace(trace, source_language)
        contracts = self.contract_engine.load_contracts(contract_path)
        results: list[EvaluationResult] = []
        for contract in contracts:
            result = self._evaluate_contract(normalized_trace, contract)
            results.append(result)

        failure_summary = [result.failure for result in results if result.failure is not None]
        suggested_repairs = self.repair_engine.suggest_repairs(normalized_trace, results)
        pass_rate = sum(1 for result in results if result.status == "pass") / max(len(results), 1)
        return EvaluationBundle(
            trace_id=trace.trace_id,
            source_language=source_language,
            pass_rate=round(pass_rate, 3),
            results=results,
            failures=failure_summary,
            suggested_repairs=suggested_repairs,
            translated_trace=normalized_trace if source_language != "en" else None,
        )

    def _evaluate_contract(self, trace: TracePayload, contract: ContractDefinition) -> EvaluationResult:
        evaluator = self.evaluators[contract.type]
        result = evaluator.evaluate(trace, contract)
        if result.status == "fail":
            failure: FailureClassification = self.failure_taxonomy.classify(result, contract)
            result.failure = failure
        return result

    def _normalize_trace(self, trace: TracePayload, source_language: str) -> TracePayload:
        if source_language == "en":
            return trace

        translated_input = self.translator.translate_to_english(trace.input_text, source_language)
        translated_context = self.translator.translate_to_english(trace.context, source_language)
        translated_output = self.translator.translate_to_english(trace.output, source_language)
        normalized_metadata = dict(trace.metadata)
        normalized_metadata["source_language"] = source_language
        normalized_metadata["translated"] = True
        return TracePayload(
            trace_id=trace.trace_id,
            prompt_version=trace.prompt_version,
            input_text=translated_input.translated_text,
            context=translated_context.translated_text,
            output=translated_output.translated_text,
            metadata=normalized_metadata,
        )
