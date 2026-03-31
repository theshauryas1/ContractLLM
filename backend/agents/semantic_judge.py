from __future__ import annotations

from backend.providers.llm import build_llm_provider

class SemanticJudge:
    def __init__(self) -> None:
        self.provider = build_llm_provider()

    def judge(self, context: str, output: str) -> dict:
        return self.provider.judge_grounding(context, output)
