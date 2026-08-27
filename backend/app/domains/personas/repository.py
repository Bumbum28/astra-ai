from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.personas.model import Persona


class PersonaRepository(Protocol):
    async def add(self, persona: Persona) -> None: ...

    async def get_owned(
        self, persona_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> Persona | None: ...

    async def list_for_user(self, user_id: UUID, *, limit: int = 100) -> Sequence[Persona]: ...

    async def clear_default(self, user_id: UUID, *, except_id: UUID | None = None) -> None: ...

    async def delete(self, persona: Persona) -> None: ...


class SQLAlchemyPersonaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, persona: Persona) -> None:
        self._session.add(persona)

    async def get_owned(
        self, persona_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> Persona | None:
        statement = select(Persona).where(
            Persona.id == persona_id, Persona.user_id == user_id
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: UUID, *, limit: int = 100
    ) -> Sequence[Persona]:
        statement = (
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.is_default.desc(), Persona.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def delete(self, persona: Persona) -> None:
        await self._session.delete(persona)

    async def clear_default(
        self, user_id: UUID, *, except_id: UUID | None = None
    ) -> None:
        statement = update(Persona).where(Persona.user_id == user_id)
        if except_id is not None:
            statement = statement.where(Persona.id != except_id)
        await self._session.execute(statement.values(is_default=False))
