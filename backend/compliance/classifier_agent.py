from __future__ import annotations

from backend.schemas import RequirementCategory


class ClassifierAgent:
    CATEGORY_KEYWORDS: dict[RequirementCategory, tuple[str, ...]] = {
        "eligibility": (
            "eligible",
            "eligibility",
            "registration",
            "license",
            "licence",
            "reference",
            "experience",
            "qualification",
        ),
        "technical": (
            "technical",
            "methodology",
            "quality",
            "iso",
            "specification",
            "service",
            "delivery",
            "staff",
        ),
        "financial": (
            "financial",
            "turnover",
            "revenue",
            "insurance",
            "bond",
            "statement",
            "balance",
            "audited",
        ),
        "legal": (
            "gdpr",
            "liability",
            "penalty",
            "contract",
            "legal",
            "compliance",
            "data protection",
            "terms",
        ),
        "operational": ("timeline", "response time", "support", "reporting", "sla", "deployment", "maintenance"),
    }

    MANDATORY_MARKERS = ("must", "shall", "required", "mandatory", "need to", "is required", "must provide")

    def classify(self, normalized_text: str) -> tuple[RequirementCategory, bool]:
        lowered = normalized_text.lower()
        mandatory = any(marker in lowered for marker in self.MANDATORY_MARKERS)

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return category, mandatory

        return "technical", mandatory
