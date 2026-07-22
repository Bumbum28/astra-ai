from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException, ValidationException
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.domains.characters.model import Character, CharacterVersion
from app.domains.conversations.model import Conversation
from app.domains.conversations.schemas import (
    ConversationCreateRequest,
    ConversationPageResponse,
    ConversationResponse,
    ConversationUpdateRequest,
)
from app.domains.messages.schemas import MessagePageResponse, MessageResponse
from app.domains.personas.model import Persona, PersonaVersion
from app.domains.relationships.model import Relationship, RelationshipLevel
from app.llm.registry import LLMProviderName
from app.utils.cursors import CursorPosition, decode_cursor, encode_cursor


class ConversationService:
    def __init__(self, uow_factory: UnitOfWorkFactory, config: AppConfig) -> None:
        self._uow_factory = uow_factory
        self._config = config

    async def create(
        self,
        user_id: UUID,
        request: ConversationCreateRequest,
    ) -> ConversationResponse:
        """Create an owned conversation with immutable profile version snapshots."""
        async with self._uow_factory() as uow:
            character, character_version = await self._resolve_character(
                uow,
                user_id,
                request.character_id,
            )
            persona, persona_version = await self._resolve_persona(
                uow,
                user_id,
                request.persona_id,
            )
            provider = (
                request.provider
                or (character.provider if character is not None else None)
                or self._config.default_llm_provider
            )
            self._validate_provider(provider)
            model = (
                request.model
                or (character.model if character is not None else None)
                or self._config.default_llm_model
            )
            temperature = (
                request.temperature
                if request.temperature is not None
                else character.temperature if character is not None else None
            )
            max_tokens = (
                request.max_tokens
                if request.max_tokens is not None
                else character.max_tokens if character is not None else None
            )
            conversation = Conversation(
                id=uuid4(),
                user_id=user_id,
                title=request.title,
                character_id=character.id if character is not None else None,
                character_version_id=(
                    character_version.id if character_version is not None else None
                ),
                persona_id=persona.id if persona is not None else None,
                persona_version_id=(
                    persona_version.id if persona_version is not None else None
                ),
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=request.system_prompt,
                conversation_metadata=request.metadata,
            )
            await uow.conversations.add(conversation)
            if character is not None:
                await uow.relationships.add(
                    self._new_relationship(conversation.id, user_id, character.id)
                )
            await uow.flush()
            response = ConversationResponse.model_validate(conversation)
            await uow.commit()
            return response

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: str | None,
    ) -> ConversationPageResponse:
        """Return conversations using stable keyset pagination."""
        page_size = min(limit, self._config.conversation_page_size_max)
        decoded = decode_cursor(cursor) if cursor else None
        async with self._uow_factory() as uow:
            rows = list(
                await uow.conversations.list_for_user(
                    user_id,
                    limit=page_size + 1,
                    cursor=decoded,
                )
            )

        has_more = len(rows) > page_size
        items = rows[:page_size]
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_cursor(
                CursorPosition(
                    timestamp=last.last_message_at or last.created_at,
                    entity_id=last.id,
                )
            )
        return ConversationPageResponse(
            items=[ConversationResponse.model_validate(item) for item in items],
            next_cursor=next_cursor,
        )

    async def get(self, user_id: UUID, conversation_id: UUID) -> ConversationResponse:
        """Return one active conversation owned by the current user."""
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(
                conversation_id,
                user_id,
            )
            if conversation is None:
                raise self._not_found()
            return ConversationResponse.model_validate(conversation)

    async def update(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request: ConversationUpdateRequest,
    ) -> ConversationResponse:
        """Update settings while pinning selected Character and Persona versions."""
        fields = request.model_fields_set
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(
                conversation_id,
                user_id,
                for_update=True,
            )
            if conversation is None:
                raise self._not_found()

            if "title" in fields:
                conversation.title = request.title
            if "system_prompt" in fields:
                conversation.system_prompt = request.system_prompt
            if "provider" in fields:
                provider = request.provider or self._config.default_llm_provider
                self._validate_provider(provider)
                conversation.provider = provider
            if "model" in fields:
                conversation.model = request.model or self._config.default_llm_model
            if "temperature" in fields:
                conversation.temperature = request.temperature
            if "max_tokens" in fields:
                conversation.max_tokens = request.max_tokens
            if "character_id" in fields:
                await self._replace_character(
                    uow,
                    user_id,
                    conversation,
                    request.character_id,
                )
            if "persona_id" in fields:
                persona, version = await self._resolve_persona(
                    uow,
                    user_id,
                    request.persona_id,
                )
                conversation.persona_id = persona.id if persona is not None else None
                conversation.persona_version_id = (
                    version.id if version is not None else None
                )

            await uow.flush()
            response = ConversationResponse.model_validate(conversation)
            await uow.commit()
            return response

    async def archive(self, user_id: UUID, conversation_id: UUID) -> None:
        """Soft-delete a conversation so history can be recovered later."""
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(
                conversation_id,
                user_id,
                for_update=True,
            )
            if conversation is None:
                raise self._not_found()
            conversation.archived_at = datetime.now(UTC)
            await uow.commit()

    async def list_messages(
        self,
        user_id: UUID,
        conversation_id: UUID,
        *,
        limit: int,
        cursor: str | None,
    ) -> MessagePageResponse:
        """Return a timeline page ordered oldest-to-newest for rendering."""
        page_size = min(limit, self._config.conversation_page_size_max)
        decoded = decode_cursor(cursor) if cursor else None
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(
                conversation_id,
                user_id,
            )
            if conversation is None:
                raise self._not_found()
            rows = list(
                await uow.messages.list_page(
                    conversation_id,
                    limit=page_size + 1,
                    cursor=decoded,
                )
            )

        has_more = len(rows) > page_size
        newest_first = rows[:page_size]
        next_cursor = None
        if has_more and newest_first:
            oldest = newest_first[-1]
            next_cursor = encode_cursor(CursorPosition(oldest.created_at, oldest.id))
        newest_first.reverse()
        return MessagePageResponse(
            items=[MessageResponse.model_validate(item) for item in newest_first],
            next_cursor=next_cursor,
        )

    async def _resolve_character(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        character_id: UUID | None,
    ) -> tuple[Character | None, CharacterVersion | None]:
        if character_id is None:
            return None, None
        character = await uow.characters.get_owned(character_id, user_id)
        if character is None:
            raise NotFoundException(
                "Character was not found.",
                code=ErrorCode.CHARACTER_NOT_FOUND,
            )
        version = await uow.character_versions.get_version(
            character.id,
            character.current_version,
        )
        if version is None:
            raise RuntimeError("Character current version is missing.")
        return character, version

    async def _resolve_persona(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        persona_id: UUID | None,
    ) -> tuple[Persona | None, PersonaVersion | None]:
        if persona_id is None:
            return None, None
        persona = await uow.personas.get_owned(persona_id, user_id)
        if persona is None:
            raise NotFoundException(
                "Persona was not found.",
                code=ErrorCode.PERSONA_NOT_FOUND,
            )
        version = await uow.persona_versions.get_version(
            persona.id,
            persona.current_version,
        )
        if version is None:
            raise RuntimeError("Persona current version is missing.")
        return persona, version

    async def _replace_character(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        conversation: Conversation,
        character_id: UUID | None,
    ) -> None:
        character, version = await self._resolve_character(
            uow,
            user_id,
            character_id,
        )
        existing = await uow.relationships.get_by_conversation(
            conversation.id,
            for_update=True,
        )
        if existing is not None and (
            character is None or existing.character_id != character.id
        ):
            await uow.relationships.delete(existing)
            # Flush the DELETE before inserting a replacement with the same
            # unique conversation_id. SQLAlchemy may otherwise INSERT before
            # DELETE and violate uq_relationships_conversation_id.
            await uow.flush()
            existing = None

        conversation.character_id = character.id if character is not None else None
        conversation.character_version_id = version.id if version is not None else None
        if character is not None and existing is None:
            await uow.relationships.add(
                self._new_relationship(conversation.id, user_id, character.id)
            )

    def _new_relationship(
        self,
        conversation_id: UUID,
        user_id: UUID,
        character_id: UUID,
    ) -> Relationship:
        return Relationship(
            id=uuid4(),
            conversation_id=conversation_id,
            user_id=user_id,
            character_id=character_id,
            level=RelationshipLevel.L0.value,
            affection_score=0,
            turn_count=0,
            relationship_metadata={},
        )

    @staticmethod
    def _validate_provider(provider: str) -> None:
        try:
            LLMProviderName(provider)
        except ValueError as exc:
            raise ValidationException(
                f"Unsupported LLM provider '{provider}'."
            ) from exc

    @staticmethod
    def _not_found() -> NotFoundException:
        return NotFoundException(
            "Conversation was not found.",
            code=ErrorCode.CONVERSATION_NOT_FOUND,
        )
