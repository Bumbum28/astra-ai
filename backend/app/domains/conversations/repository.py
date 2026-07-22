from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.conversations.model import Conversation
from app.utils.cursors import CursorPosition


class ConversationRepository(Protocol):
    async def add(self, conversation: Conversation) -> None: ...

    async def get_by_id(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> Conversation | None: ...

    async def get_owned(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Conversation | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
    ) -> Sequence[Conversation]: ...


class SQLAlchemyConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, conversation: Conversation) -> None:
        self._session.add(conversation)

    async def get_by_id(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> Conversation | None:
        statement = select(Conversation).where(Conversation.id == conversation_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_owned(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        if not include_archived:
            statement = statement.where(Conversation.archived_at.is_(None))
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
    ) -> Sequence[Conversation]:
        activity = func.coalesce(
            Conversation.last_message_at,
            Conversation.created_at,
        )
        statement = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.archived_at.is_(None),
        )
        if cursor is not None:
            statement = statement.where(
                or_(
                    activity < cursor.timestamp,
                    and_(
                        activity == cursor.timestamp,
                        Conversation.id < cursor.entity_id,
                    ),
                )
            )
        statement = statement.order_by(activity.desc(), Conversation.id.desc()).limit(
            limit
        )
        result = await self._session.execute(statement)
        return result.scalars().all()
