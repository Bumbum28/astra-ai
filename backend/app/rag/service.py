from app.rag.contracts import RetrievalQuery, RetrievedChunk
from app.rag.retriever import Retriever


class RAGService:
    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    async def search(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        """Retrieve knowledge without coupling callers to storage implementation."""
        return await self._retriever.retrieve(query)
