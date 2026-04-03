from __future__ import annotations

from backend.compliance.localization import localize_action, localize_reasoning, localize_status
from backend.providers.compliance import HeuristicComplianceReasoningProvider, build_compliance_reasoning_provider
from backend.schemas import ComplianceMatrixRow, EvidenceItem, FeedbackExample
from backend.utils.config import get_settings


class ComplianceAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = build_compliance_reasoning_provider()

    def assess(
        self,
        requirement_id: str,
        requirement_text: str,
        category: str,
        category_label: str,
        evidence: list[EvidenceItem],
        output_language: str,
        feedback_examples: list[FeedbackExample] | None = None,
    ) -> ComplianceMatrixRow:
        feedback_examples = feedback_examples or []
        try:
            decision = self.provider.assess(
                requirement_text=requirement_text,
                category_label=category_label,
                evidence=evidence,
                output_language=output_language,
                feedback_examples=feedback_examples,
            )
        except Exception:
            decision = HeuristicComplianceReasoningProvider().assess(
                requirement_text=requirement_text,
                category_label=category_label,
                evidence=evidence,
                output_language=output_language,
                feedback_examples=feedback_examples,
            )

        best_source = evidence[0].source if evidence else None
        feedback_hint = feedback_examples[0].corrected_status if feedback_examples else ""
        reasoning = decision.reasoning or localize_reasoning(decision.status, output_language, best_source, feedback_hint)
        action = decision.recommended_action or localize_action(decision.status, output_language)

        audit_trail = ["Requirement extracted from tender text."]
        audit_trail.extend(decision.audit_notes)
        if evidence:
            audit_trail.append(f"Top evidence source: {evidence[0].source}.")

        return ComplianceMatrixRow(
            requirement_id=requirement_id,
            requirement_text=requirement_text,
            category=category,
            category_label=category_label,
            status=decision.status,
            status_label=localize_status(decision.status, output_language),
            reasoning=reasoning,
            evidence=evidence,
            confidence=decision.confidence,
            recommended_action=action,
            review_required=decision.review_required,
            feedback_examples=feedback_examples,
            audit_trail=audit_trail,
        )
