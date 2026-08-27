from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.memories.model import Memory, MemoryScope


class MemoryRepository(Protocol):
    async def add(self, memory: Memory) -> None: ...

    async def get_owned(
        self, memory_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> Memory | None: ...

    async def list_for_user(
        self, user_id: UUID, *, limit: int = 100
    ) -> Sequence[Memory]: ...

    async def list_for_context(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID,
        character_id: UUID | None,
        limit: int,
        min_importance: float,
    ) -> Sequence[Memory]: ...


class SQLAlchemyMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, memory: Memory) -> None:
        self._session.add(memory)

    async def get_owned(
        self, memory_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> Memory | None:
        statement = select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == user_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: UUID, *, limit: int = 100
    ) -> Sequence[Memory]:
        statement = (
            select(Memory)
            .where(Memory.user_id == user_id, Memory.archived_at.is_(None))
            .order_by(Memory.importance.desc(), Memory.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def list_for_context(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID,
        character_id: UUID | None,
        limit: int,
        min_importance: float,
    ) -> Sequence[Memory]:
        selectors = [
            Memory.scope == MemoryScope.USER,
            Memory.conversation_id == conversation_id,
        ]
        if character_id is not None:
            selectors.append(Memory.character_id == character_id)
        statement = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.archived_at.is_(None),
                Memory.importance >= min_importance,
                or_(*selectors),
            )
            .order_by(Memory.importance.desc(), Memory.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()
