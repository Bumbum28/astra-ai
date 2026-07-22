from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.relationships.model import Relationship, RelationshipEvent


class RelationshipRepository(Protocol):
    async def add(self, relationship: Relationship) -> None: ...

    async def get_by_conversation(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> Relationship | None: ...

    async def delete(self, relationship: Relationship) -> None: ...


class RelationshipEventRepository(Protocol):
    async def add(self, event: RelationshipEvent) -> None: ...

    async def list_for_relationship(
        self,
        relationship_id: UUID,
        *,
        limit: int,
    ) -> Sequence[RelationshipEvent]: ...


class SQLAlchemyRelationshipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, relationship: Relationship) -> None:
        self._session.add(relationship)

    async def get_by_conversation(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> Relationship | None:
        statement = select(Relationship).where(
            Relationship.conversation_id == conversation_id
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def delete(self, relationship: Relationship) -> None:
        await self._session.delete(relationship)


class SQLAlchemyRelationshipEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: RelationshipEvent) -> None:
        self._session.add(event)

    async def list_for_relationship(
        self,
        relationship_id: UUID,
        *,
        limit: int,
    ) -> Sequence[RelationshipEvent]:
        result = await self._session.execute(
            select(RelationshipEvent)
            .where(RelationshipEvent.relationship_id == relationship_id)
            .order_by(RelationshipEvent.created_at.desc(), RelationshipEvent.id.desc())
            .limit(limit)
        )
        return result.scalars().all()
