from typing import Protocol

from app.rag.contracts import RetrievalQuery, RetrievedChunk


class Retriever(Protocol):
    async def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        """Return ranked chunks for a provider-independent RAG query."""
        ...
