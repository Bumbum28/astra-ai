from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.model import RefreshSession


class RefreshSessionRepository(Protocol):
    async def add(self, refresh_session: RefreshSession) -> None: ...

    async def get_by_id(
        self, session_id: UUID, *, for_update: bool = False
    ) -> RefreshSession | None: ...

    async def revoke_all_for_user(self, user_id: UUID) -> int: ...

    async def revoke_family(self, family_id: UUID) -> int: ...


class SQLAlchemyRefreshSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, refresh_session: RefreshSession) -> None:
        self._session.add(refresh_session)

    async def get_by_id(
        self, session_id: UUID, *, for_update: bool = False
    ) -> RefreshSession | None:
        statement = select(RefreshSession).where(RefreshSession.id == session_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        now = datetime.now(UTC)
        statement = (
            update(RefreshSession)
            .where(
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = cast(
            CursorResult[Any],
            await self._session.execute(statement),
        )
        return int(result.rowcount or 0)

    async def revoke_family(self, family_id: UUID) -> int:
        now = datetime.now(UTC)
        statement = (
            update(RefreshSession)
            .where(
                RefreshSession.token_family_id == family_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = cast(
            CursorResult[Any],
            await self._session.execute(statement),
        )
        return int(result.rowcount or 0)
