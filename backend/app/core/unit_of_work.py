from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import ConflictException
from app.core.database import AsyncSessionFactory
from app.domains.auth.repository import (
    RefreshSessionRepository,
    SQLAlchemyRefreshSessionRepository,
)
from app.domains.users.repository import SQLAlchemyUserRepository, UserRepository


class UnitOfWork(Protocol):
    @property
    def users(self) -> UserRepository: ...

    @property
    def refresh_sessions(self) -> RefreshSessionRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def flush(self) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...


class SQLAlchemyUnitOfWork:
    users: UserRepository
    refresh_sessions: RefreshSessionRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SQLAlchemyUserRepository(self._session)
        self.refresh_sessions = SQLAlchemyRefreshSessionRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        if exc_type is not None:
            await self._session.rollback()
        await self._session.close()

    def _require_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("Unit of work must be entered before use.")
        return self._session

    async def flush(self) -> None:
        await self._require_session().flush()

    async def commit(self) -> None:
        session = self._require_session()
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            sqlstate = getattr(exc.orig, "sqlstate", None)
            if sqlstate == "23505":
                raise ConflictException(
                    "A resource with the same unique value exists."
                ) from exc
            raise

    async def rollback(self) -> None:
        await self._require_session().rollback()


class SQLAlchemyUnitOfWorkFactory:
    def __call__(self) -> UnitOfWork:
        return SQLAlchemyUnitOfWork()


def get_uow_factory() -> UnitOfWorkFactory:
    return SQLAlchemyUnitOfWorkFactory()
