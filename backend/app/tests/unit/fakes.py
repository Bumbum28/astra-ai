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
            self.characters,
            self.character_versions,
            self.personas,
            self.persona_versions,
            self.relationships,
            self.relationship_events,
        )
        self.created.append(uow)
        return uow
