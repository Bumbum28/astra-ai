from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.memories.model import (
    ConversationSummary,
    Memory,
    MemoryScope,
    MemoryStatus,
    MemoryTask,
    MemoryTaskStatus,
)
from app.utils.cursors import CursorPosition


class MemoryRepository(Protocol):
    async def add(self, memory: Memory) -> None: ...

    async def get_owned(
        self,
        memory_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> Memory | None: ...

    async def find_active_by_key(
        self,
        user_id: UUID,
        *,
        scope: MemoryScope,
        normalized_key: str,
        conversation_id: UUID | None,
        character_id: UUID | None,
        persona_id: UUID | None,
        for_update: bool = False,
    ) -> Memory | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
        scope: MemoryScope | None = None,
        conversation_id: UUID | None = None,
        include_archived: bool = False,
    ) -> Sequence[Memory]: ...

    async def list_context_candidates(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID,
        character_id: UUID | None,
        persona_id: UUID | None,
        query_text: str,
        limit: int,
    ) -> Sequence[Memory]: ...

    async def touch_accessed(self, memory_ids: Sequence[UUID]) -> None: ...


class ConversationSummaryRepository(Protocol):
    async def add(self, summary: ConversationSummary) -> None: ...

    async def get_by_conversation(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationSummary | None: ...


class MemoryTaskRepository(Protocol):
    async def add(self, task: MemoryTask) -> None: ...

    async def get_by_trigger_message(
        self,
        trigger_message_id: UUID,
    ) -> MemoryTask | None: ...

    async def get_by_id(
        self,
        task_id: UUID,
        *,
        for_update: bool = False,
    ) -> MemoryTask | None: ...

    async def claim_next(
        self,
        *,
        max_attempts: int,
        lock_timeout_seconds: int,
    ) -> MemoryTask | None: ...

    async def count_pending(self, conversation_id: UUID) -> int: ...


class SQLAlchemyMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, memory: Memory) -> None:
        self._session.add(memory)

    async def get_owned(
        self,
        memory_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> Memory | None:
        statement = select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == user_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def find_active_by_key(
        self,
        user_id: UUID,
        *,
        scope: MemoryScope,
        normalized_key: str,
        conversation_id: UUID | None,
        character_id: UUID | None,
        persona_id: UUID | None,
        for_update: bool = False,
    ) -> Memory | None:
        statement = select(Memory).where(
            Memory.user_id == user_id,
            Memory.scope == scope,
            Memory.normalized_key == normalized_key,
            Memory.status == MemoryStatus.ACTIVE,
            Memory.conversation_id.is_(conversation_id)
            if conversation_id is None
            else Memory.conversation_id == conversation_id,
            Memory.character_id.is_(character_id)
            if character_id is None
            else Memory.character_id == character_id,
            Memory.persona_id.is_(persona_id)
            if persona_id is None
            else Memory.persona_id == persona_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
        scope: MemoryScope | None = None,
        conversation_id: UUID | None = None,
        include_archived: bool = False,
    ) -> Sequence[Memory]:
        statement = select(Memory).where(Memory.user_id == user_id)
        if not include_archived:
            statement = statement.where(Memory.status == MemoryStatus.ACTIVE)
        if scope is not None:
            statement = statement.where(Memory.scope == scope)
        if conversation_id is not None:
            statement = statement.where(Memory.conversation_id == conversation_id)
        if cursor is not None:
            statement = statement.where(
                or_(
                    Memory.updated_at < cursor.timestamp,
                    and_(
                        Memory.updated_at == cursor.timestamp,
                        Memory.id < cursor.entity_id,
                    ),
                )
            )
        statement = statement.order_by(
            Memory.updated_at.desc(), Memory.id.desc()
        ).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def list_context_candidates(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID,
        character_id: UUID | None,
        persona_id: UUID | None,
        query_text: str,
        limit: int,
    ) -> Sequence[Memory]:
        now = datetime.now(UTC)
        context_filter = or_(
            Memory.scope == MemoryScope.USER,
            and_(
                Memory.scope == MemoryScope.CHARACTER,
                Memory.character_id == character_id,
            )
            if character_id is not None
            else false(),
            and_(
                Memory.scope.in_(
                    [
                        MemoryScope.RELATIONSHIP,
                        MemoryScope.WORLD,
                        MemoryScope.CONVERSATION,
                    ]
                ),
                Memory.conversation_id == conversation_id,
            ),
        )
        statement = select(Memory).where(
            Memory.user_id == user_id,
            Memory.status == MemoryStatus.ACTIVE,
            or_(Memory.expires_at.is_(None), Memory.expires_at > now),
            context_filter,
        )
        if persona_id is None:
            statement = statement.where(Memory.persona_id.is_(None))
        else:
            statement = statement.where(
                or_(Memory.persona_id.is_(None), Memory.persona_id == persona_id)
            )

        normalized_query = query_text.strip()
        if normalized_query:
            query = func.websearch_to_tsquery("simple", normalized_query)
            rank = func.ts_rank_cd(
                func.to_tsvector("simple", Memory.content),
                query,
            )
            statement = statement.order_by(
                rank.desc(),
                Memory.importance.desc(),
                Memory.updated_at.desc(),
            )
        else:
            statement = statement.order_by(
                Memory.importance.desc(), Memory.updated_at.desc()
            )
        result = await self._session.execute(statement.limit(limit))
        return result.scalars().all()

    async def touch_accessed(self, memory_ids: Sequence[UUID]) -> None:
        if not memory_ids:
            return
        result = await self._session.execute(
            select(Memory).where(Memory.id.in_(memory_ids)).with_for_update()
        )
        now = datetime.now(UTC)
        for memory in result.scalars().all():
            memory.last_accessed_at = now
            memory.access_count += 1


class SQLAlchemyConversationSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, summary: ConversationSummary) -> None:
        self._session.add(summary)

    async def get_by_conversation(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationSummary | None:
        statement = select(ConversationSummary).where(
            ConversationSummary.conversation_id == conversation_id
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()


class SQLAlchemyMemoryTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: MemoryTask) -> None:
        self._session.add(task)

    async def get_by_trigger_message(
        self,
        trigger_message_id: UUID,
    ) -> MemoryTask | None:
        result = await self._session.execute(
            select(MemoryTask).where(
                MemoryTask.trigger_message_id == trigger_message_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        task_id: UUID,
        *,
        for_update: bool = False,
    ) -> MemoryTask | None:
        statement = select(MemoryTask).where(MemoryTask.id == task_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def claim_next(
        self,
        *,
        max_attempts: int,
        lock_timeout_seconds: int,
    ) -> MemoryTask | None:
        now = datetime.now(UTC)
        stale_before = now - timedelta(seconds=lock_timeout_seconds)
        result = await self._session.execute(
            select(MemoryTask)
            .where(
                or_(
                    and_(
                        MemoryTask.status == MemoryTaskStatus.PENDING,
                        MemoryTask.available_at <= now,
                    ),
                    and_(
                        MemoryTask.status == MemoryTaskStatus.PROCESSING,
                        MemoryTask.locked_at.is_not(None),
                        MemoryTask.locked_at < stale_before,
                    ),
                ),
                MemoryTask.attempts < max_attempts,
            )
            .order_by(MemoryTask.available_at, MemoryTask.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        task = result.scalar_one_or_none()
        if task is None:
            return None
        task.status = MemoryTaskStatus.PROCESSING
        task.locked_at = now
        task.attempts += 1
        return task

    async def count_pending(self, conversation_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(MemoryTask.id)).where(
                MemoryTask.conversation_id == conversation_id,
                MemoryTask.status.in_(
                    [MemoryTaskStatus.PENDING, MemoryTaskStatus.PROCESSING]
                ),
            )
        )
        return int(result.scalar_one())
