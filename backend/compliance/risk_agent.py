from __future__ import annotations

from backend.compliance.localization import localize_risk_title
from backend.schemas import ComplianceMatrixRow, RiskFlag, RiskSeverity


class RiskAgent:
    def analyze(self, rows: list[ComplianceMatrixRow], output_language: str) -> tuple[list[RiskFlag], RiskSeverity]:
        risks: list[RiskFlag] = []
        highest = "low"

        for row in rows:
            severity = self._severity_for_row(row)
            highest = self._max_severity(highest, severity)
            if severity == "low" and not row.review_required:
                continue

            risks.append(
                RiskFlag(
                    requirement_id=row.requirement_id,
                    severity=severity,
                    title=localize_risk_title(severity, output_language),
                    rationale=self._rationale(severity, output_language),
                    mitigation=row.recommended_action,
                )
            )

        return risks, highest

    def _severity_for_row(self, row: ComplianceMatrixRow) -> RiskSeverity:
        if row.status == "missing" and row.category in {"eligibility", "legal"}:
            return "critical"
        if row.status == "missing":
            return "high"
        if row.status == "partial":
            return "medium"
        if row.review_required:
            return "low"
        return "low"

    def _max_severity(self, left: RiskSeverity, right: RiskSeverity) -> RiskSeverity:
        order = ["low", "medium", "high", "critical"]
        return left if order.index(left) >= order.index(right) else right

    def _rationale(self, severity: RiskSeverity, output_language: str) -> str:
        messages = {
            "en": {
                "critical": "This requirement appears unsupported and could disqualify the bid.",
                "high": "This requirement is unsupported and may create a major compliance gap.",
                "medium": "Evidence is incomplete and may reduce evaluator confidence.",
                "low": "Human review is advised before submission.",
            },
            "fr": {
                "critical": "Cette exigence semble non couverte et pourrait disqualifier l'offre.",
                "high": "Cette exigence n'est pas couverte et cree une lacune majeure de conformite.",
                "medium": "Les preuves sont incompletes et peuvent reduire la confiance de l'evaluateur.",
                "low": "Une verification humaine est recommandee avant la soumission.",
            },
            "de": {
                "critical": "Diese Anforderung scheint nicht belegt zu sein und konnte zum Ausschluss fuhren.",
                "high": "Diese Anforderung ist nicht belegt und schafft eine grosse Compliance-Lucke.",
                "medium": "Die Nachweise sind unvollstandig und konnen das Vertrauen der Prufenden senken.",
                "low": "Eine manuelle Prufung vor Einreichung wird empfohlen.",
            },
            "es": {
                "critical": "Este requisito parece no estar cubierto y podria descalificar la oferta.",
                "high": "Este requisito no esta cubierto y crea una brecha importante de cumplimiento.",
                "medium": "La evidencia es incompleta y puede reducir la confianza del evaluador.",
                "low": "Se recomienda revision humana antes de presentar.",
            },
            "nl": {
                "critical": "Deze eis lijkt niet onderbouwd en kan leiden tot uitsluiting.",
                "high": "Deze eis is niet onderbouwd en veroorzaakt een grote compliance-kloof.",
                "medium": "Het bewijs is onvolledig en kan het vertrouwen van beoordelaars verlagen.",
                "low": "Menselijke controle wordt aanbevolen voor indiening.",
            },
        }
        language = output_language if output_language in messages else "en"
        return messages[language][severity]
