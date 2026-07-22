from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.personas.model import Persona, PersonaVersion
from app.utils.cursors import CursorPosition


class PersonaRepository(Protocol):
    async def add(self, persona: Persona) -> None: ...

    async def get_owned(
        self,
        persona_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Persona | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
    ) -> Sequence[Persona]: ...


class PersonaVersionRepository(Protocol):
    async def add(self, version: PersonaVersion) -> None: ...

    async def get_by_id(self, version_id: UUID) -> PersonaVersion | None: ...

    async def get_version(
        self,
        persona_id: UUID,
        version: int,
    ) -> PersonaVersion | None: ...

    async def list_current(
        self,
        items: Sequence[Persona],
    ) -> Sequence[PersonaVersion]: ...


class SQLAlchemyPersonaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, persona: Persona) -> None:
        self._session.add(persona)

    async def get_owned(
        self,
        persona_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Persona | None:
        statement = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id,
        )
        if not include_archived:
            statement = statement.where(Persona.archived_at.is_(None))
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
    ) -> Sequence[Persona]:
        statement = select(Persona).where(
            Persona.user_id == user_id,
            Persona.archived_at.is_(None),
        )
        if cursor is not None:
            statement = statement.where(
                or_(
                    Persona.updated_at < cursor.timestamp,
                    and_(
                        Persona.updated_at == cursor.timestamp,
                        Persona.id < cursor.entity_id,
                    ),
                )
            )
        statement = statement.order_by(
            Persona.updated_at.desc(), Persona.id.desc()
        ).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()


class SQLAlchemyPersonaVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, version: PersonaVersion) -> None:
        self._session.add(version)

    async def get_by_id(self, version_id: UUID) -> PersonaVersion | None:
        result = await self._session.execute(
            select(PersonaVersion).where(PersonaVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_version(
        self,
        persona_id: UUID,
        version: int,
    ) -> PersonaVersion | None:
        result = await self._session.execute(
            select(PersonaVersion).where(
                PersonaVersion.persona_id == persona_id,
                PersonaVersion.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def list_current(
        self,
        items: Sequence[Persona],
    ) -> Sequence[PersonaVersion]:
        if not items:
            return []
        conditions = [
            and_(
                PersonaVersion.persona_id == item.id,
                PersonaVersion.version == item.current_version,
            )
            for item in items
        ]
        result = await self._session.execute(
            select(PersonaVersion).where(or_(*conditions))
        )
        return result.scalars().all()
