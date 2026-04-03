from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from backend.utils.config import get_settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class LexicalEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        tokens = text.lower().split()
        return [float(len(tokens)), float(len(set(tokens))), float(len(text))]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def embed(self, text: str) -> list[float]:
        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": text},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["data"][0]["embedding"]


def build_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "xai" and settings.xai_api_key:
        return OpenAIEmbeddingProvider(
            api_key=settings.xai_api_key,
            model=settings.embedding_model,
            base_url=settings.xai_base_url,
        )
    return LexicalEmbeddingProvider()
