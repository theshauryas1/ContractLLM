from backend.providers.embeddings import build_embedding_provider


class Embedder:
    def __init__(self) -> None:
        self.provider = build_embedding_provider()

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self.provider.embed(text) for text in texts]
