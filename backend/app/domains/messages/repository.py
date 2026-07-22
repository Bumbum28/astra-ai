from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.messages.model import Message, MessageRole, MessageStatus
from app.utils.cursors import CursorPosition


class MessageRepository(Protocol):
    async def add(self, message: Message) -> None: ...

    async def get_by_id(
        self,
        message_id: UUID,
        *,
        for_update: bool = False,
    ) -> Message | None: ...

    async def get_by_client_message_id(
        self,
        conversation_id: UUID,
        client_message_id: UUID,
    ) -> Message | None: ...

    async def get_assistant_reply(
        self,
        user_message_id: UUID,
        *,
        for_update: bool = False,
    ) -> Message | None: ...

    async def list_page(
        self,
        conversation_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
    ) -> Sequence[Message]: ...

    async def list_context(
        self,
        conversation_id: UUID,
        *,
        limit: int,
    ) -> Sequence[Message]: ...

    async def list_completed_after(
        self,
        conversation_id: UUID,
        *,
        after: CursorPosition | None,
        limit: int,
    ) -> Sequence[Message]: ...

    async def count_completed(self, conversation_id: UUID) -> int: ...


class SQLAlchemyMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: Message) -> None:
        self._session.add(message)

    async def get_by_id(
        self,
        message_id: UUID,
        *,
        for_update: bool = False,
    ) -> Message | None:
        statement = select(Message).where(Message.id == message_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_client_message_id(
        self,
        conversation_id: UUID,
        client_message_id: UUID,
    ) -> Message | None:
        result = await self._session.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.client_message_id == client_message_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_assistant_reply(
        self,
        user_message_id: UUID,
        *,
        for_update: bool = False,
    ) -> Message | None:
        statement = select(Message).where(
            Message.parent_message_id == user_message_id,
            Message.role == MessageRole.ASSISTANT,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_page(
        self,
        conversation_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
    ) -> Sequence[Message]:
        statement = select(Message).where(Message.conversation_id == conversation_id)
        if cursor is not None:
            statement = statement.where(
                or_(
                    Message.created_at < cursor.timestamp,
                    and_(
                        Message.created_at == cursor.timestamp,
                        Message.id < cursor.entity_id,
                    ),
                )
            )
        statement = statement.order_by(
            Message.created_at.desc(), Message.id.desc()
        ).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def list_context(
        self,
        conversation_id: UUID,
        *,
        limit: int,
    ) -> Sequence[Message]:
        result = await self._session.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.status == MessageStatus.COMPLETED,
                Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )
        items = list(result.scalars().all())
        items.reverse()
        return items

    async def list_completed_after(
        self,
        conversation_id: UUID,
        *,
        after: CursorPosition | None,
        limit: int,
    ) -> Sequence[Message]:
        statement = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.status == MessageStatus.COMPLETED,
            Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
        )
        if after is not None:
            statement = statement.where(
                or_(
                    Message.created_at > after.timestamp,
                    and_(
                        Message.created_at == after.timestamp,
                        Message.id > after.entity_id,
                    ),
                )
            )
        result = await self._session.execute(
            statement.order_by(Message.created_at, Message.id).limit(limit)
        )
        return result.scalars().all()

    async def count_completed(self, conversation_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id,
                Message.status == MessageStatus.COMPLETED,
                Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
            )
        )
        return int(result.scalar_one())

