from __future__ import annotations

import json
from abc import ABC, abstractmethod

import httpx

from backend.utils.config import get_settings


class LLMProvider(ABC):
    @abstractmethod
    def judge_grounding(self, context: str, output: str) -> dict:
        raise NotImplementedError


class HeuristicJudgeProvider(LLMProvider):
    def judge_grounding(self, context: str, output: str) -> dict:
        supported = output.lower() in context.lower() or any(
            sentence.strip().lower() in context.lower()
            for sentence in output.split(".")
            if len(sentence.strip()) > 12
        )
        return {
            "status": "pass" if supported else "fail",
            "confidence": 0.84 if supported else 0.79,
            "reasoning": (
                "Heuristic judge found the response grounded in the supplied context."
                if supported
                else "Heuristic judge detected claims that are not directly supported by context."
            ),
            "evidence_pointers": ["context", "output"],
            "provider": "heuristic",
        }


class OpenAIJudgeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def judge_grounding(self, context: str, output: str) -> dict:
        prompt = (
            "Evaluate whether the output is fully grounded in the provided context. "
            "Return strict JSON with keys: status, confidence, reasoning, evidence_pointers.\n"
            f"Context:\n{context}\n\nOutput:\n{output}"
        )
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a grounding judge for LLM evaluation."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        parsed["provider"] = "xai"
        return parsed


def build_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "xai" and settings.xai_api_key:
        return OpenAIJudgeProvider(api_key=settings.xai_api_key, model=settings.llm_model, base_url=settings.xai_base_url)
    return HeuristicJudgeProvider()
