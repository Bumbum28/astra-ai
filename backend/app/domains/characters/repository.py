from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.characters.model import Character


class CharacterRepository(Protocol):
    async def add(self, character: Character) -> None: ...

    async def get_owned(
        self,
        character_id: UUID,
        user_id: UUID,
        *,
        include_inactive: bool = False,
        for_update: bool = False,
    ) -> Character | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        include_inactive: bool = False,
        limit: int = 100,
    ) -> Sequence[Character]: ...


class SQLAlchemyCharacterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, character: Character) -> None:
        self._session.add(character)

    async def get_owned(
        self,
        character_id: UUID,
        user_id: UUID,
        *,
        include_inactive: bool = False,
        for_update: bool = False,
    ) -> Character | None:
        statement = select(Character).where(
            Character.id == character_id,
            Character.user_id == user_id,
        )
        if not include_inactive:
            statement = statement.where(Character.is_active.is_(True))
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        include_inactive: bool = False,
        limit: int = 100,
    ) -> Sequence[Character]:
        statement = select(Character).where(Character.user_id == user_id)
        if not include_inactive:
            statement = statement.where(Character.is_active.is_(True))
        statement = statement.order_by(Character.updated_at.desc()).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()
