from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from app.core.unit_of_work import UnitOfWork
from app.domains.characters.model import Character
from app.domains.characters.repository import CharacterRepository
from app.domains.auth.model import RefreshSession
from app.domains.auth.repository import RefreshSessionRepository
from app.domains.conversations.model import Conversation
from app.domains.conversations.repository import ConversationRepository
from app.domains.knowledge.model import KnowledgeChunk, KnowledgeSource
from app.domains.knowledge.repository import KnowledgeRepository
from app.domains.memories.model import Memory
from app.domains.memories.repository import MemoryRepository
from app.domains.messages.model import Message, MessageRole, MessageStatus
from app.domains.messages.repository import MessageRepository
from app.domains.personas.model import Persona
from app.domains.personas.repository import PersonaRepository
from app.domains.users.model import User
from app.domains.users.repository import UserRepository
from app.rag.contracts import RetrievedChunk
from app.utils.cursors import CursorPosition


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
        for item in self.items.values():
            if item.user_id == user_id and item.revoked_at is None:
                item.revoked_at = datetime.now(UTC)
                count += 1
        return count

    async def revoke_family(self, family_id: UUID) -> int:
        count = 0
        for item in self.items.values():
            if item.token_family_id == family_id and item.revoked_at is None:
                item.revoked_at = datetime.now(UTC)
                count += 1
        return count


class FakeConversationRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Conversation] = {}

    async def add(self, conversation: Conversation) -> None:
        self.items[conversation.id] = conversation

    async def get_by_id(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> Conversation | None:
        return self.items.get(conversation_id)

    async def get_owned(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Conversation | None:
        item = self.items.get(conversation_id)
        if item is None or item.user_id != user_id:
            return None
        if not include_archived and item.archived_at is not None:
            return None
        return item

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
    ) -> list[Conversation]:
        items = [
            item
            for item in self.items.values()
            if item.user_id == user_id and item.archived_at is None
        ]
        items.sort(
            key=lambda item: (item.last_message_at or item.created_at, item.id),
            reverse=True,
        )
        if cursor is not None:
            items = [
                item
                for item in items
                if (item.last_message_at or item.created_at, item.id)
                < (cursor.timestamp, cursor.entity_id)
            ]
        return items[:limit]


class FakeMessageRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Message] = {}

    async def add(self, message: Message) -> None:
        self.items[message.id] = message

    async def get_by_id(
        self,
        message_id: UUID,
        *,
        for_update: bool = False,
    ) -> Message | None:
        return self.items.get(message_id)

    async def get_by_client_message_id(
        self,
        conversation_id: UUID,
        client_message_id: UUID,
    ) -> Message | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.conversation_id == conversation_id
                and item.client_message_id == client_message_id
            ),
            None,
        )

    async def get_assistant_reply(
        self,
        user_message_id: UUID,
        *,
        for_update: bool = False,
    ) -> Message | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.parent_message_id == user_message_id
                and item.role == MessageRole.ASSISTANT
            ),
            None,
        )

    async def list_page(
        self,
        conversation_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
    ) -> list[Message]:
        items = [
            item
            for item in self.items.values()
            if item.conversation_id == conversation_id
        ]
        items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        if cursor is not None:
            items = [
                item
                for item in items
                if (item.created_at, item.id)
                < (cursor.timestamp, cursor.entity_id)
            ]
        return items[:limit]

    async def list_context(
        self,
        conversation_id: UUID,
        *,
        limit: int,
    ) -> list[Message]:
        items = [
            item
            for item in self.items.values()
            if item.conversation_id == conversation_id
            and item.status == MessageStatus.COMPLETED
            and item.role in {MessageRole.USER, MessageRole.ASSISTANT}
        ]
        items.sort(key=lambda item: (item.created_at, item.id))
        return items[-limit:]


class FakeCharacterRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Character] = {}

    async def add(self, character: Character) -> None:
        self.items[character.id] = character

    async def get_owned(
        self,
        character_id: UUID,
        user_id: UUID,
        *,
        include_inactive: bool = False,
        for_update: bool = False,
    ) -> Character | None:
        item = self.items.get(character_id)
        if item is None or item.user_id != user_id:
            return None
        if not include_inactive and not item.is_active:
            return None
        return item

    async def list_for_user(
        self, user_id: UUID, *, include_inactive: bool = False, limit: int = 100
    ) -> list[Character]:
        items = [item for item in self.items.values() if item.user_id == user_id]
        if not include_inactive:
            items = [item for item in items if item.is_active]
        return items[:limit]


class FakePersonaRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Persona] = {}

    async def add(self, persona: Persona) -> None:
        self.items[persona.id] = persona

    async def get_owned(
        self, persona_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> Persona | None:
        item = self.items.get(persona_id)
        return item if item is not None and item.user_id == user_id else None

    async def list_for_user(self, user_id: UUID, *, limit: int = 100) -> list[Persona]:
        return [item for item in self.items.values() if item.user_id == user_id][:limit]

    async def clear_default(
        self, user_id: UUID, *, except_id: UUID | None = None
    ) -> None:
        for item in self.items.values():
            if item.user_id == user_id and item.id != except_id:
                item.is_default = False

    async def delete(self, persona: Persona) -> None:
        self.items.pop(persona.id, None)


class FakeMemoryRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Memory] = {}

    async def add(self, memory: Memory) -> None:
        self.items[memory.id] = memory

    async def get_owned(
        self, memory_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> Memory | None:
        item = self.items.get(memory_id)
        return item if item is not None and item.user_id == user_id else None

    async def list_for_user(self, user_id: UUID, *, limit: int = 100) -> list[Memory]:
        items = [
            item
            for item in self.items.values()
            if item.user_id == user_id and item.archived_at is None
        ]
        items.sort(key=lambda item: item.importance, reverse=True)
        return items[:limit]

    async def list_for_context(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID,
        character_id: UUID | None,
        limit: int,
        min_importance: float,
    ) -> list[Memory]:
        items = [
            item
            for item in self.items.values()
            if item.user_id == user_id
            and item.archived_at is None
            and item.importance >= min_importance
            and (
                item.scope.value == "user"
                or item.conversation_id == conversation_id
                or (character_id is not None and item.character_id == character_id)
            )
        ]
        items.sort(key=lambda item: item.importance, reverse=True)
        return items[:limit]


class FakeKnowledgeRepository:
    def __init__(self) -> None:
        self.sources: dict[UUID, KnowledgeSource] = {}
        self.chunks: dict[UUID, KnowledgeChunk] = {}

    async def add_source(self, source: KnowledgeSource) -> None:
        self.sources[source.id] = source

    async def add_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        for chunk in chunks:
            self.chunks[chunk.id] = chunk

    async def get_source_owned(
        self, source_id: UUID, user_id: UUID, *, for_update: bool = False
    ) -> KnowledgeSource | None:
        item = self.sources.get(source_id)
        return item if item is not None and item.user_id == user_id else None

    async def list_sources(
        self, user_id: UUID, *, limit: int = 100
    ) -> list[KnowledgeSource]:
        return [
            item
            for item in self.sources.values()
            if item.user_id == user_id and item.status.value == "ready"
        ][:limit]

    async def search(
        self,
        user_id: UUID,
        query: str,
        *,
        top_k: int,
        source_ids: tuple[UUID, ...] = (),
    ) -> list[RetrievedChunk]:
        terms = [term for term in query.casefold().split() if term]
        hits: list[RetrievedChunk] = []
        for chunk in self.chunks.values():
            if chunk.user_id != user_id:
                continue
            if source_ids and chunk.source_id not in source_ids:
                continue
            folded = chunk.content.casefold()
            score = sum(1 for term in terms if term in folded)
            if score == 0:
                continue
            hits.append(
                RetrievedChunk(
                    source_id=chunk.source_id,
                    chunk_id=chunk.id,
                    content=chunk.content,
                    score=float(score),
                    metadata=chunk.chunk_metadata,
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]


class FakeUnitOfWork:
    def __init__(
        self,
        users: FakeUserRepository,
        sessions: FakeRefreshSessionRepository,
        conversations: FakeConversationRepository,
        messages: FakeMessageRepository,
        characters: FakeCharacterRepository,
        personas: FakePersonaRepository,
        memories: FakeMemoryRepository,
        knowledge: FakeKnowledgeRepository,
    ) -> None:
        self.users: UserRepository = users
        self.refresh_sessions: RefreshSessionRepository = sessions
        self.conversations: ConversationRepository = conversations
        self.messages: MessageRepository = messages
        self.characters: CharacterRepository = characters
        self.personas: PersonaRepository = personas
        self.memories: MemoryRepository = memories
        self.knowledge: KnowledgeRepository = knowledge
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
        now = datetime.now(UTC)
        items: list[object] = [
            *self.users.items.values(),  # type: ignore[attr-defined]
            *self.conversations.items.values(),  # type: ignore[attr-defined]
            *self.messages.items.values(),  # type: ignore[attr-defined]
            *self.characters.items.values(),  # type: ignore[attr-defined]
            *self.personas.items.values(),  # type: ignore[attr-defined]
            *self.memories.items.values(),  # type: ignore[attr-defined]
            *self.knowledge.sources.values(),  # type: ignore[attr-defined]
            *self.knowledge.chunks.values(),  # type: ignore[attr-defined]
        ]
        for item in items:
            if getattr(item, "created_at", None) is None:
                setattr(item, "created_at", now)
            if getattr(item, "updated_at", None) is None:
                setattr(item, "updated_at", now)

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


class FakeUnitOfWorkFactory:
    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.sessions = FakeRefreshSessionRepository()
        self.conversations = FakeConversationRepository()
        self.messages = FakeMessageRepository()
        self.characters = FakeCharacterRepository()
        self.personas = FakePersonaRepository()
        self.memories = FakeMemoryRepository()
        self.knowledge = FakeKnowledgeRepository()
        self.created: list[FakeUnitOfWork] = []

    def __call__(self) -> UnitOfWork:
        uow = FakeUnitOfWork(
            self.users,
            self.sessions,
            self.conversations,
            self.messages,
            self.characters,
            self.personas,
            self.memories,
            self.knowledge,
        )
        self.created.append(uow)
        return uow
