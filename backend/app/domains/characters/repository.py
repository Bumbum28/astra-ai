from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.characters.model import Character, CharacterVersion
from app.utils.cursors import CursorPosition


class CharacterRepository(Protocol):
    async def add(self, character: Character) -> None: ...

    async def get_owned(
        self,
        character_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Character | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
    ) -> Sequence[Character]: ...


class CharacterVersionRepository(Protocol):
    async def add(self, version: CharacterVersion) -> None: ...

    async def get_by_id(self, version_id: UUID) -> CharacterVersion | None: ...

    async def get_version(
        self,
        character_id: UUID,
        version: int,
    ) -> CharacterVersion | None: ...

    async def list_current(
        self,
        items: Sequence[Character],
    ) -> Sequence[CharacterVersion]: ...


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
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Character | None:
        statement = select(Character).where(
            Character.id == character_id,
            Character.user_id == user_id,
        )
        if not include_archived:
            statement = statement.where(Character.archived_at.is_(None))
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
    ) -> Sequence[Character]:
        statement = select(Character).where(
            Character.user_id == user_id,
            Character.archived_at.is_(None),
        )
        if cursor is not None:
            statement = statement.where(
                or_(
                    Character.updated_at < cursor.timestamp,
                    and_(
                        Character.updated_at == cursor.timestamp,
                        Character.id < cursor.entity_id,
                    ),
                )
            )
        statement = statement.order_by(
            Character.updated_at.desc(), Character.id.desc()
        ).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()


class SQLAlchemyCharacterVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, version: CharacterVersion) -> None:
        self._session.add(version)

    async def get_by_id(self, version_id: UUID) -> CharacterVersion | None:
        result = await self._session.execute(
            select(CharacterVersion).where(CharacterVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_version(
        self,
        character_id: UUID,
        version: int,
    ) -> CharacterVersion | None:
        result = await self._session.execute(
            select(CharacterVersion).where(
                CharacterVersion.character_id == character_id,
                CharacterVersion.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def list_current(
        self,
        items: Sequence[Character],
    ) -> Sequence[CharacterVersion]:
        if not items:
            return []
        conditions = [
            and_(
                CharacterVersion.character_id == item.id,
                CharacterVersion.version == item.current_version,
            )
            for item in items
        ]
        result = await self._session.execute(
            select(CharacterVersion).where(or_(*conditions))
        )
        return result.scalars().all()
