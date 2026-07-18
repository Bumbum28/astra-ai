from types import TracebackType
from typing import Self
from uuid import UUID

from app.core.unit_of_work import UnitOfWork
from app.domains.auth.model import RefreshSession
from app.domains.auth.repository import RefreshSessionRepository
from app.domains.users.model import User
from app.domains.users.repository import UserRepository


class FakeUserRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.items.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((item for item in self.items.values() if item.email == email), None)

    async def get_by_username(self, username: str) -> User | None:
        return next(
            (item for item in self.items.values() if item.username == username), None
        )

    async def add(self, user: User) -> None:
        self.items[user.id] = user


class FakeRefreshSessionRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, RefreshSession] = {}

    async def add(self, refresh_session: RefreshSession) -> None:
        self.items[refresh_session.id] = refresh_session

    async def get_by_id(
        self, session_id: UUID, *, for_update: bool = False
    ) -> RefreshSession | None:
        return self.items.get(session_id)

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        count = 0
        from datetime import UTC, datetime

        for item in self.items.values():
            if item.user_id == user_id and item.revoked_at is None:
                item.revoked_at = datetime.now(UTC)
                count += 1
        return count

    async def revoke_family(self, family_id: UUID) -> int:
        count = 0
        from datetime import UTC, datetime

        for item in self.items.values():
            if item.token_family_id == family_id and item.revoked_at is None:
                item.revoked_at = datetime.now(UTC)
                count += 1
        return count


class FakeUnitOfWork:
    def __init__(
        self,
        users: FakeUserRepository,
        sessions: FakeRefreshSessionRepository,
    ) -> None:
        self.users: UserRepository = users
        self.refresh_sessions: RefreshSessionRepository = sessions
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def flush(self) -> None:
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        for user in self.users.items.values():  # type: ignore[attr-defined]
            if user.created_at is None:
                user.created_at = now
            if user.updated_at is None:
                user.updated_at = now

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


class FakeUnitOfWorkFactory:
    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.sessions = FakeRefreshSessionRepository()
        self.created: list[FakeUnitOfWork] = []

    def __call__(self) -> UnitOfWork:
        uow = FakeUnitOfWork(self.users, self.sessions)
        self.created.append(uow)
        return uow
