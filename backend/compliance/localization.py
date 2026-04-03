from __future__ import annotations

from backend.schemas import ComplianceStatus, RequirementCategory, RiskSeverity


LANGUAGE_FALLBACK = {"hi": "en", "unknown": "en"}

STATUS_LABELS: dict[str, dict[ComplianceStatus, str]] = {
    "en": {"full": "Full", "partial": "Partial", "missing": "Missing"},
    "fr": {"full": "Complet", "partial": "Partiel", "missing": "Manquant"},
    "de": {"full": "Vollstandig", "partial": "Teilweise", "missing": "Fehlend"},
    "es": {"full": "Completo", "partial": "Parcial", "missing": "Faltante"},
    "nl": {"full": "Volledig", "partial": "Gedeeltelijk", "missing": "Ontbrekend"},
}

CATEGORY_LABELS: dict[str, dict[RequirementCategory, str]] = {
    "en": {
        "eligibility": "Eligibility",
        "technical": "Technical",
        "financial": "Financial",
        "legal": "Legal",
        "operational": "Operational",
    },
    "fr": {
        "eligibility": "Eligibilite",
        "technical": "Technique",
        "financial": "Financier",
        "legal": "Juridique",
        "operational": "Operationnel",
    },
    "de": {
        "eligibility": "Eignung",
        "technical": "Technisch",
        "financial": "Finanziell",
        "legal": "Rechtlich",
        "operational": "Operativ",
    },
    "es": {
        "eligibility": "Elegibilidad",
        "technical": "Tecnico",
        "financial": "Financiero",
        "legal": "Legal",
        "operational": "Operativo",
    },
    "nl": {
        "eligibility": "Geschiktheid",
        "technical": "Technisch",
        "financial": "Financieel",
        "legal": "Juridisch",
        "operational": "Operationeel",
    },
}

REASONING_TEMPLATES = {
    "en": {
        "full": "Company evidence strongly supports this requirement.",
        "partial": "Company evidence partially addresses this requirement, but important gaps remain.",
        "missing": "No reliable company evidence was found for this requirement.",
    },
    "fr": {
        "full": "Les preuves de l'entreprise soutiennent clairement cette exigence.",
        "partial": "Les preuves de l'entreprise couvrent partiellement cette exigence, mais des lacunes subsistent.",
        "missing": "Aucune preuve fiable de l'entreprise n'a ete trouvee pour cette exigence.",
    },
    "de": {
        "full": "Die Unternehmensnachweise stutzen diese Anforderung deutlich.",
        "partial": "Die Unternehmensnachweise decken diese Anforderung teilweise ab, aber wichtige Lucken bleiben.",
        "missing": "Es wurden keine verlasslichen Unternehmensnachweise fur diese Anforderung gefunden.",
    },
    "es": {
        "full": "La evidencia de la empresa respalda claramente este requisito.",
        "partial": "La evidencia de la empresa cubre parcialmente este requisito, pero quedan brechas importantes.",
        "missing": "No se encontro evidencia fiable de la empresa para este requisito.",
    },
    "nl": {
        "full": "Het bedrijfsbewijs ondersteunt deze eis duidelijk.",
        "partial": "Het bedrijfsbewijs dekt deze eis gedeeltelijk, maar er blijven belangrijke hiaten.",
        "missing": "Er is geen betrouwbaar bedrijfsbewijs gevonden voor deze eis.",
    },
}

ACTION_TEMPLATES = {
    "en": {
        "full": "Reference the strongest evidence directly in the response matrix.",
        "partial": "Add missing proof, certifications, or delivery detail before submission.",
        "missing": "Escalate immediately and decide whether to partner, qualify, or no-bid.",
    },
    "fr": {
        "full": "Referencez la preuve la plus solide directement dans la matrice de conformite.",
        "partial": "Ajoutez les preuves, certifications ou details de livraison manquants avant la soumission.",
        "missing": "Escalez immediatement et decidez d'un partenariat, d'une qualification ou d'un no-bid.",
    },
    "de": {
        "full": "Verweisen Sie direkt in der Compliance-Matrix auf den starksten Nachweis.",
        "partial": "Erganzen Sie vor der Einreichung fehlende Nachweise, Zertifikate oder Leistungsdetails.",
        "missing": "Eskalieren Sie sofort und entscheiden Sie uber Partnerschaft, Nachqualifizierung oder No-Bid.",
    },
    "es": {
        "full": "Cite la evidencia mas solida directamente en la matriz de cumplimiento.",
        "partial": "Agregue evidencia, certificaciones o detalles de entrega faltantes antes de presentar.",
        "missing": "Escale de inmediato y decida si asociarse, cualificar o no presentar oferta.",
    },
    "nl": {
        "full": "Verwijs rechtstreeks in de compliance-matrix naar het sterkste bewijs.",
        "partial": "Voeg ontbrekend bewijs, certificeringen of uitvoeringsdetails toe voor indiening.",
        "missing": "Escaleer direct en beslis over partneren, kwalificeren of niet inschrijven.",
    },
}

RISK_TITLES = {
    "en": {
        "critical": "Disqualification risk",
        "high": "Major compliance gap",
        "medium": "Scoring weakness",
        "low": "Review recommended",
    },
    "fr": {
        "critical": "Risque de disqualification",
        "high": "Lacune majeure de conformite",
        "medium": "Faiblesse de notation",
        "low": "Verification recommandee",
    },
    "de": {
        "critical": "Risiko der Disqualifikation",
        "high": "Grosse Compliance-Lucke",
        "medium": "Schwache Bewertungsposition",
        "low": "Prufung empfohlen",
    },
    "es": {
        "critical": "Riesgo de descalificacion",
        "high": "Brecha importante de cumplimiento",
        "medium": "Debilidad de puntuacion",
        "low": "Revision recomendada",
    },
    "nl": {
        "critical": "Risico op uitsluiting",
        "high": "Grote compliance-kloof",
        "medium": "Zwakke scorepositie",
        "low": "Beoordeling aanbevolen",
    },
}

OVERALL_RISK_LABELS: dict[str, dict[RiskSeverity, str]] = {
    "en": {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"},
    "fr": {"low": "Faible", "medium": "Moyen", "high": "Eleve", "critical": "Critique"},
    "de": {"low": "Niedrig", "medium": "Mittel", "high": "Hoch", "critical": "Kritisch"},
    "es": {"low": "Bajo", "medium": "Medio", "high": "Alto", "critical": "Critico"},
    "nl": {"low": "Laag", "medium": "Middel", "high": "Hoog", "critical": "Kritiek"},
}

SUMMARY_TEMPLATES = {
    "en": "Analysis found {full_count} full, {partial_count} partial, and {missing_count} missing requirements. Overall risk is {overall_risk}.",
    "fr": "L'analyse a trouve {full_count} exigences completes, {partial_count} partielles et {missing_count} manquantes. Le risque global est {overall_risk}.",
    "de": "Die Analyse ergab {full_count} vollstandige, {partial_count} teilweise und {missing_count} fehlende Anforderungen. Das Gesamtrisiko ist {overall_risk}.",
    "es": "El analisis encontro {full_count} requisitos completos, {partial_count} parciales y {missing_count} faltantes. El riesgo general es {overall_risk}.",
    "nl": "De analyse vond {full_count} volledige, {partial_count} gedeeltelijke en {missing_count} ontbrekende eisen. Het algemene risico is {overall_risk}.",
}


def _normalize_language(language: str) -> str:
    return LANGUAGE_FALLBACK.get(language, language if language in STATUS_LABELS else "en")


def localize_status(status: ComplianceStatus, language: str) -> str:
    language = _normalize_language(language)
    return STATUS_LABELS[language][status]


def localize_category(category: RequirementCategory, language: str) -> str:
    language = _normalize_language(language)
    return CATEGORY_LABELS[language][category]


def localize_reasoning(status: ComplianceStatus, language: str, source: str | None = None, feedback_hint: str = "") -> str:
    language = _normalize_language(language)
    reasoning = REASONING_TEMPLATES[language][status]
    if source:
        suffixes = {
            "en": f" Best evidence came from {source}.",
            "fr": f" La meilleure preuve provient de {source}.",
            "de": f" Der beste Nachweis stammt aus {source}.",
            "es": f" La mejor evidencia provino de {source}.",
            "nl": f" Het sterkste bewijs kwam uit {source}.",
        }
        reasoning += suffixes[language]
    if feedback_hint:
        hints = {
            "en": f" Reviewer feedback signal: {feedback_hint}.",
            "fr": f" Signal de retour reviseur : {feedback_hint}.",
            "de": f" Feedback-Hinweis der Prufung: {feedback_hint}.",
            "es": f" Senal de revision humana: {feedback_hint}.",
            "nl": f" Signaal uit reviewerfeedback: {feedback_hint}.",
        }
        reasoning += hints[language]
    return reasoning


def localize_action(status: ComplianceStatus, language: str) -> str:
    language = _normalize_language(language)
    return ACTION_TEMPLATES[language][status]


def localize_risk_title(severity: RiskSeverity, language: str) -> str:
    language = _normalize_language(language)
    return RISK_TITLES[language][severity]


def localize_overall_risk(severity: RiskSeverity, language: str) -> str:
    language = _normalize_language(language)
    return OVERALL_RISK_LABELS[language][severity]


def localize_summary(full_count: int, partial_count: int, missing_count: int, overall_risk: RiskSeverity, language: str) -> str:
    language = _normalize_language(language)
    return SUMMARY_TEMPLATES[language].format(
        full_count=full_count,
        partial_count=partial_count,
        missing_count=missing_count,
        overall_risk=localize_overall_risk(overall_risk, language),
    )
