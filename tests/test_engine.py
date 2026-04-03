import json
from pathlib import Path

from backend.agents.semantic_judge import SemanticJudge
from backend.core.evaluator import EvaluationOrchestrator
from backend.multilingual.translator import Translator
from backend.providers.embeddings import build_embedding_provider
from backend.providers.llm import build_llm_provider
from backend.evaluators.rag_grounding import RAGGroundingEvaluator
from backend.schemas import TracePayload
from backend.utils.config import get_settings


def test_evaluator_returns_bundle() -> None:
    raw = json.loads(Path("tests/sample_traces.json").read_text(encoding="utf-8"))
    trace = TracePayload(**raw)
    bundle = EvaluationOrchestrator().evaluate_trace(trace, "contracts/default.yaml")
    assert bundle.trace_id == "trace-001"
    assert len(bundle.results) == 4
    assert 0 <= bundle.pass_rate <= 1


def test_structural_failure_is_classified() -> None:
    trace = TracePayload(
        trace_id="trace-002",
        input_text="Return JSON",
        output="not-json",
        context="Return JSON with the answer.",
    )
    bundle = EvaluationOrchestrator().evaluate_trace(trace, "contracts/default.yaml")
    result = next(item for item in bundle.results if item.contract == "response_format")
    assert result.status == "fail"
    assert result.failure is not None
    assert result.failure.failure_type == "format_violation"


def test_multilingual_metadata_is_preserved_in_bundle() -> None:
    trace = TracePayload(
        trace_id="trace-003",
        prompt_version="v3",
        input_text="Zusammenfassen Sie die Richtlinie.",
        output='{"summary": "30 day refund window"}',
        context="30 day refund window",
        metadata={"language": "de"},
    )
    bundle = EvaluationOrchestrator().evaluate_trace(trace, "contracts/default.yaml")
    assert bundle.source_language == "de"
    assert bundle.translated_trace is not None
    assert "summarize the policy" in bundle.translated_trace.input_text.lower()


def test_translator_supports_supported_languages_to_english() -> None:
    translator = Translator()
    samples = {
        "fr": "Résumez la politique de remboursement.",
        "de": "Zusammenfassen Sie die Rückerstattungsrichtlinie.",
        "es": "Resume la política de reembolso.",
        "nl": "Vat het terugbetalingsbeleid samen.",
    }

    for language, text in samples.items():
        translated = translator.translate_to_english(text, language)
        assert translated.translated_text != text
        assert "refund policy" in translated.translated_text.lower()


def test_translator_translates_json_output_payloads() -> None:
    translator = Translator()
    translated = translator.translate_to_english('{"Zusammenfassung":"30 Tage Rückerstattungsfrist"}', "de")
    assert translated.translated_text == '{"summary": "30 day refund window"}'


def test_semantic_failure_generates_repair_suggestion() -> None:
    trace = TracePayload(
        trace_id="trace-004",
        input_text="Summarize the policy.",
        output="Customers get lifetime refunds with no receipt required.",
        context="Customers have a 30 day refund window when a receipt is provided.",
    )
    bundle = EvaluationOrchestrator().evaluate_trace(trace, "contracts/default.yaml")
    semantic_result = next(item for item in bundle.results if item.contract == "context_faithfulness")
    assert semantic_result.status == "fail"
    assert any(item.contract == "context_faithfulness" for item in bundle.suggested_repairs)


def test_rag_evaluator_returns_support_when_kb_matches() -> None:
    evaluator = RAGGroundingEvaluator()
    trace = TracePayload(
        trace_id="trace-005",
        input_text="Ground the response.",
        output="Products must only cite facts that are present in the retrieved support documents.",
        context="",
    )
    contract = next(
        item
        for item in EvaluationOrchestrator().contract_engine.load_contracts("contracts/default.yaml")
        if item.id == "rag_support"
    )
    result = evaluator.evaluate(trace, contract)
    assert result.status == "pass"
    assert result.evidence_pointers


def test_default_provider_selection_stays_local_without_keys() -> None:
    settings = get_settings()
    settings.llm_provider = "heuristic"
    settings.embedding_provider = "lexical"
    settings.xai_api_key = ""
    assert build_llm_provider().__class__.__name__ == "HeuristicJudgeProvider"
    assert build_embedding_provider().__class__.__name__ == "LexicalEmbeddingProvider"


def test_semantic_judge_exposes_provider_metadata() -> None:
    settings = get_settings()
    settings.llm_provider = "heuristic"
    judge = SemanticJudge()
    result = judge.judge("receipt required for 30 day refund window", "30 day refund window")
    assert result["provider"] == "heuristic"


def test_xai_provider_selection_uses_hosted_provider_when_key_present() -> None:
    settings = get_settings()
    settings.llm_provider = "xai"
    settings.embedding_provider = "xai"
    settings.xai_api_key = "test-key"
    assert build_llm_provider().__class__.__name__ == "OpenAIJudgeProvider"
    assert build_embedding_provider().__class__.__name__ == "OpenAIEmbeddingProvider"
