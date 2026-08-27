from app.core.unit_of_work import UnitOfWorkFactory
from app.rag.contracts import RetrievalQuery, RetrievedChunk


class PostgresKeywordRetriever:
    """PostgreSQL full-text retriever behind the generic RAG contract."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        async with self._uow_factory() as uow:
            hits = await uow.knowledge.search(
                query.user_id,
                query.query,
                top_k=query.top_k,
                source_ids=query.source_ids,
            )
        return list(hits)
