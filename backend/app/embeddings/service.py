from app.embeddings.base import BaseEmbeddingProvider


class EmbeddingService:
    def __init__(self, provider: BaseEmbeddingProvider | None) -> None:
        self._provider = provider

    @property
    def enabled(self) -> bool:
        return self._provider is not None

    async def embed_one(self, text: str) -> list[float] | None:
        if self._provider is None or not text.strip():
            return None
        results = await self._provider.embed([text.strip()])
        return results[0] if results else None

    async def embed_many(self, texts: list[str]) -> list[list[float] | None]:
        if not texts:
            return []
        if self._provider is None:
            return [None for _ in texts]
        results = await self._provider.embed(texts)
        return [*results]
