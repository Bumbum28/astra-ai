from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.knowledge.model import KnowledgeChunk, KnowledgeSource, KnowledgeSourceStatus
from app.rag.contracts import RetrievedChunk


class KnowledgeRepository(Protocol):
    async def add_source(self, source: KnowledgeSource) -> None: ...
    async def add_chunks(self, chunks: Sequence[KnowledgeChunk]) -> None: ...
    async def get_source_owned(
        self, source_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> KnowledgeSource | None: ...
    async def list_sources(self, user_id: UUID, *, limit: int = 100) -> Sequence[KnowledgeSource]: ...
    async def search(
        self,
        user_id: UUID,
        query: str,
        *,
        top_k: int,
        source_ids: tuple[UUID, ...] = (),
    ) -> Sequence[RetrievedChunk]: ...


class SQLAlchemyKnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_source(self, source: KnowledgeSource) -> None:
        self._session.add(source)

    async def add_chunks(self, chunks: Sequence[KnowledgeChunk]) -> None:
        self._session.add_all(list(chunks))

    async def get_source_owned(
        self, source_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> KnowledgeSource | None:
        statement = select(KnowledgeSource).where(
            KnowledgeSource.id == source_id,
            KnowledgeSource.user_id == user_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_sources(
        self, user_id: UUID, *, limit: int = 100
    ) -> Sequence[KnowledgeSource]:
        statement = (
            select(KnowledgeSource)
            .where(
                KnowledgeSource.user_id == user_id,
                KnowledgeSource.status == KnowledgeSourceStatus.READY,
            )
            .order_by(KnowledgeSource.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def search(
        self,
        user_id: UUID,
        query: str,
        *,
        top_k: int,
        source_ids: tuple[UUID, ...] = (),
    ) -> Sequence[RetrievedChunk]:
        vector = func.to_tsvector("simple", KnowledgeChunk.content)
        tsquery = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(vector, tsquery)
        statement = (
            select(KnowledgeChunk, rank.label("score"))
            .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
            .where(
                KnowledgeChunk.user_id == user_id,
                KnowledgeSource.status == KnowledgeSourceStatus.READY,
                vector.op("@@")(tsquery),
            )
        )
        if source_ids:
            statement = statement.where(KnowledgeChunk.source_id.in_(source_ids))
        statement = statement.order_by(desc("score"), KnowledgeChunk.ordinal).limit(top_k)
        result = await self._session.execute(statement)
        rows = result.all()
        return [
            RetrievedChunk(
                source_id=chunk.source_id,
                chunk_id=chunk.id,
                content=chunk.content,
                score=max(float(score or 0), 0.0),
                metadata=chunk.chunk_metadata,
            )
            for chunk, score in rows
        ]
