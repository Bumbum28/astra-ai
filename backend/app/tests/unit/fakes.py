from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from app.core.unit_of_work import UnitOfWork
from app.domains.auth.model import RefreshSession
from app.domains.auth.repository import RefreshSessionRepository
from app.domains.characters.model import Character, CharacterVersion
from app.domains.characters.repository import (
    CharacterRepository,
    CharacterVersionRepository,
)
from app.domains.conversations.model import Conversation
from app.domains.conversations.repository import ConversationRepository
from app.domains.messages.model import Message, MessageRole, MessageStatus
from app.domains.messages.repository import MessageRepository
from app.domains.memories.model import (
    ConversationSummary,
    Memory,
    MemoryScope,
    MemoryTask,
    MemoryTaskStatus,
)
from app.domains.memories.repository import (
    ConversationSummaryRepository,
    MemoryRepository,
    MemoryTaskRepository,
)
from app.domains.personas.model import Persona, PersonaVersion
from app.domains.personas.repository import PersonaRepository, PersonaVersionRepository
from app.domains.relationships.model import Relationship, RelationshipEvent
from app.domains.relationships.repository import (
    RelationshipEventRepository,
    RelationshipRepository,
)
from app.domains.users.model import User
from app.domains.users.repository import UserRepository
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


    async def list_completed_after(
        self,
        conversation_id: UUID,
        *,
        after: CursorPosition | None,
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
        if after is not None:
            items = [
                item
                for item in items
                if (item.created_at, item.id) > (after.timestamp, after.entity_id)
            ]
        return items[:limit]

    async def count_completed(self, conversation_id: UUID) -> int:
        return len(
            [
                item
                for item in self.items.values()
                if item.conversation_id == conversation_id
                and item.status == MessageStatus.COMPLETED
                and item.role in {MessageRole.USER, MessageRole.ASSISTANT}
            ]
        )


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

    async def find_active_by_key(
        self, user_id: UUID, **kwargs: object
    ) -> Memory | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.user_id == user_id
                and item.normalized_key == kwargs.get("normalized_key")
                and item.scope == kwargs.get("scope")
                and item.status.value == "active"
            ),
            None,
        )

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: CursorPosition | None = None,
        scope: object | None = None,
        conversation_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Memory]:
        items = [item for item in self.items.values() if item.user_id == user_id]
        if not include_archived:
            items = [item for item in items if item.status.value == "active"]
        if scope is not None:
            items = [item for item in items if item.scope == scope]
        if conversation_id is not None:
            items = [item for item in items if item.conversation_id == conversation_id]
        items.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
        return items[:limit]

    async def list_context_candidates(
        self, user_id: UUID, **kwargs: object
    ) -> list[Memory]:
        limit = int(kwargs.get("limit", 20))
        conversation_id = kwargs.get("conversation_id")
        character_id = kwargs.get("character_id")
        persona_id = kwargs.get("persona_id")
        items = []
        for item in self.items.values():
            if item.user_id != user_id or item.status.value != "active":
                continue
            if persona_id is None and item.persona_id is not None:
                continue
            if persona_id is not None and item.persona_id not in {None, persona_id}:
                continue
            in_scope = (
                item.scope == MemoryScope.USER
                or (
                    item.scope == MemoryScope.CHARACTER
                    and character_id is not None
                    and item.character_id == character_id
                )
                or (
                    item.scope
                    in {
                        MemoryScope.RELATIONSHIP,
                        MemoryScope.WORLD,
                        MemoryScope.CONVERSATION,
                    }
                    and item.conversation_id == conversation_id
                )
            )
            if in_scope:
                items.append(item)
        return items[:limit]

    async def touch_accessed(self, memory_ids: list[UUID]) -> None:
        for memory_id in memory_ids:
            item = self.items.get(memory_id)
            if item is not None:
                item.access_count += 1


class FakeConversationSummaryRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, ConversationSummary] = {}

    async def add(self, summary: ConversationSummary) -> None:
        self.items[summary.conversation_id] = summary

    async def get_by_conversation(
        self, conversation_id: UUID, *, for_update: bool = False
    ) -> ConversationSummary | None:
        return self.items.get(conversation_id)


class FakeMemoryTaskRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, MemoryTask] = {}

    async def add(self, task: MemoryTask) -> None:
        self.items[task.id] = task

    async def get_by_trigger_message(
        self, trigger_message_id: UUID
    ) -> MemoryTask | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.trigger_message_id == trigger_message_id
            ),
            None,
        )

    async def get_by_id(
        self, task_id: UUID, *, for_update: bool = False
    ) -> MemoryTask | None:
        return self.items.get(task_id)

    async def claim_next(
        self, *, max_attempts: int, lock_timeout_seconds: int
    ) -> MemoryTask | None:
        for item in self.items.values():
            if item.status == MemoryTaskStatus.PENDING and item.attempts < max_attempts:
                item.status = MemoryTaskStatus.PROCESSING
                item.attempts += 1
                return item
        return None

    async def count_pending(self, conversation_id: UUID) -> int:
        return len(
            [
                item
                for item in self.items.values()
                if item.conversation_id == conversation_id
                and item.status
                in {MemoryTaskStatus.PENDING, MemoryTaskStatus.PROCESSING}
            ]
        )


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
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Character | None:
        item = self.items.get(character_id)
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
    ) -> list[Character]:
        items = [
            item
            for item in self.items.values()
            if item.user_id == user_id and item.archived_at is None
        ]
        items.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
        if cursor is not None:
            items = [
                item
                for item in items
                if (item.updated_at, item.id) < (cursor.timestamp, cursor.entity_id)
            ]
        return items[:limit]


class FakeCharacterVersionRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, CharacterVersion] = {}

    async def add(self, version: CharacterVersion) -> None:
        self.items[version.id] = version

    async def get_by_id(self, version_id: UUID) -> CharacterVersion | None:
        return self.items.get(version_id)

    async def get_version(
        self, character_id: UUID, version: int
    ) -> CharacterVersion | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.character_id == character_id and item.version == version
            ),
            None,
        )

    async def list_current(
        self, items: list[Character]
    ) -> list[CharacterVersion]:
        pairs = {(item.id, item.current_version) for item in items}
        return [
            item
            for item in self.items.values()
            if (item.character_id, item.version) in pairs
        ]


class FakePersonaRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Persona] = {}

    async def add(self, persona: Persona) -> None:
        self.items[persona.id] = persona

    async def get_owned(
        self,
        persona_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        for_update: bool = False,
    ) -> Persona | None:
        item = self.items.get(persona_id)
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
    ) -> list[Persona]:
        items = [
            item
            for item in self.items.values()
            if item.user_id == user_id and item.archived_at is None
        ]
        items.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
        if cursor is not None:
            items = [
                item
                for item in items
                if (item.updated_at, item.id) < (cursor.timestamp, cursor.entity_id)
            ]
        return items[:limit]


class FakePersonaVersionRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, PersonaVersion] = {}

    async def add(self, version: PersonaVersion) -> None:
        self.items[version.id] = version

    async def get_by_id(self, version_id: UUID) -> PersonaVersion | None:
        return self.items.get(version_id)

    async def get_version(
        self, persona_id: UUID, version: int
    ) -> PersonaVersion | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.persona_id == persona_id and item.version == version
            ),
            None,
        )

    async def list_current(self, items: list[Persona]) -> list[PersonaVersion]:
        pairs = {(item.id, item.current_version) for item in items}
        return [
            item
            for item in self.items.values()
            if (item.persona_id, item.version) in pairs
        ]


class FakeRelationshipRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Relationship] = {}

    async def add(self, relationship: Relationship) -> None:
        self.items[relationship.id] = relationship

    async def get_by_conversation(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> Relationship | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.conversation_id == conversation_id
            ),
            None,
        )

    async def delete(self, relationship: Relationship) -> None:
        self.items.pop(relationship.id, None)


class FakeRelationshipEventRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, RelationshipEvent] = {}

    async def add(self, event: RelationshipEvent) -> None:
        self.items[event.id] = event

    async def list_for_relationship(
        self, relationship_id: UUID, *, limit: int
    ) -> list[RelationshipEvent]:
        items = [
            item
            for item in self.items.values()
            if item.relationship_id == relationship_id
        ]
        items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return items[:limit]


class FakeUnitOfWork:
    def __init__(
        self,
        users: FakeUserRepository,
        sessions: FakeRefreshSessionRepository,
        conversations: FakeConversationRepository,
        messages: FakeMessageRepository,
        memories: FakeMemoryRepository,
        conversation_summaries: FakeConversationSummaryRepository,
        memory_tasks: FakeMemoryTaskRepository,
        characters: FakeCharacterRepository,
        character_versions: FakeCharacterVersionRepository,
        personas: FakePersonaRepository,
        persona_versions: FakePersonaVersionRepository,
        relationships: FakeRelationshipRepository,
        relationship_events: FakeRelationshipEventRepository,
    ) -> None:
        self.users: UserRepository = users
        self.refresh_sessions: RefreshSessionRepository = sessions
        self.conversations: ConversationRepository = conversations
        self.messages: MessageRepository = messages
        self.memories: MemoryRepository = memories
        self.conversation_summaries: ConversationSummaryRepository = (
            conversation_summaries
        )
        self.memory_tasks: MemoryTaskRepository = memory_tasks
        self.characters: CharacterRepository = characters
        self.character_versions: CharacterVersionRepository = character_versions
        self.personas: PersonaRepository = personas
        self.persona_versions: PersonaVersionRepository = persona_versions
        self.relationships: RelationshipRepository = relationships
        self.relationship_events: RelationshipEventRepository = relationship_events
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
            *self.memories.items.values(),  # type: ignore[attr-defined]
            *self.conversation_summaries.items.values(),  # type: ignore[attr-defined]
            *self.memory_tasks.items.values(),  # type: ignore[attr-defined]
            *self.characters.items.values(),  # type: ignore[attr-defined]
            *self.character_versions.items.values(),  # type: ignore[attr-defined]
            *self.personas.items.values(),  # type: ignore[attr-defined]
            *self.persona_versions.items.values(),  # type: ignore[attr-defined]
            *self.relationships.items.values(),  # type: ignore[attr-defined]
            *self.relationship_events.items.values(),  # type: ignore[attr-defined]
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
        self.memories = FakeMemoryRepository()
        self.conversation_summaries = FakeConversationSummaryRepository()
        self.memory_tasks = FakeMemoryTaskRepository()
        self.characters = FakeCharacterRepository()
        self.character_versions = FakeCharacterVersionRepository()
        self.personas = FakePersonaRepository()
        self.persona_versions = FakePersonaVersionRepository()
        self.relationships = FakeRelationshipRepository()
        self.relationship_events = FakeRelationshipEventRepository()
        self.created: list[FakeUnitOfWork] = []

    def __call__(self) -> UnitOfWork:
        uow = FakeUnitOfWork(
            self.users,
            self.sessions,
            self.conversations,
            self.messages,
            self.memories,
            self.conversation_summaries,
            self.memory_tasks,
            self.characters,
            self.character_versions,
            self.personas,
            self.persona_versions,
            self.relationships,
            self.relationship_events,
        )
        self.created.append(uow)
        return uow
