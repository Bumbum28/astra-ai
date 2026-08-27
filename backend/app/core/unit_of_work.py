from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import ConflictException
from app.domains.auth.repository import (
    RefreshSessionRepository,
    SQLAlchemyRefreshSessionRepository,
)
from app.domains.characters.repository import (
    CharacterRepository,
    SQLAlchemyCharacterRepository,
)
from app.domains.conversations.repository import (
    ConversationRepository,
    SQLAlchemyConversationRepository,
)
from app.domains.knowledge.repository import KnowledgeRepository, SQLAlchemyKnowledgeRepository
from app.domains.memories.repository import MemoryRepository, SQLAlchemyMemoryRepository
from app.domains.messages.repository import (
    MessageRepository,
    SQLAlchemyMessageRepository,
)
from app.domains.personas.repository import PersonaRepository, SQLAlchemyPersonaRepository
from app.domains.users.repository import SQLAlchemyUserRepository, UserRepository


class UnitOfWork(Protocol):
    @property
    def users(self) -> UserRepository: ...

    @property
    def refresh_sessions(self) -> RefreshSessionRepository: ...

    @property
    def conversations(self) -> ConversationRepository: ...

    @property
    def messages(self) -> MessageRepository: ...

    @property
    def characters(self) -> CharacterRepository: ...

    @property
    def personas(self) -> PersonaRepository: ...

    @property
    def memories(self) -> MemoryRepository: ...

    @property
    def knowledge(self) -> KnowledgeRepository: ...

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
    conversations: ConversationRepository
    messages: MessageRepository
    characters: CharacterRepository
    personas: PersonaRepository
    memories: MemoryRepository
    knowledge: KnowledgeRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        if session_factory is None:
            from app.core.database import AsyncSessionFactory

            session_factory = AsyncSessionFactory
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SQLAlchemyUserRepository(self._session)
        self.refresh_sessions = SQLAlchemyRefreshSessionRepository(self._session)
        self.conversations = SQLAlchemyConversationRepository(self._session)
        self.messages = SQLAlchemyMessageRepository(self._session)
        self.characters = SQLAlchemyCharacterRepository(self._session)
        self.personas = SQLAlchemyPersonaRepository(self._session)
        self.memories = SQLAlchemyMemoryRepository(self._session)
        self.knowledge = SQLAlchemyKnowledgeRepository(self._session)
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
