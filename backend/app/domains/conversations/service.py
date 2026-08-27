from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException, ValidationException
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.conversations.model import Conversation
from app.domains.conversations.schemas import (
    ConversationCreateRequest,
    ConversationPageResponse,
    ConversationResponse,
    ConversationUpdateRequest,
)
from app.domains.messages.schemas import MessagePageResponse, MessageResponse
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
        """Create an owned conversation with provider-independent settings."""
        provider = request.provider or self._config.default_llm_provider
        self._validate_provider(provider)
        model = request.model or self._config.default_llm_model
        await self._validate_context_references(user_id, request.character_id, request.persona_id)
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            title=request.title,
            provider=provider,
            model=model,
            system_prompt=request.system_prompt,
            character_id=request.character_id,
            persona_id=request.persona_id,
            conversation_metadata=request.metadata,
        )
        async with self._uow_factory() as uow:
            await uow.conversations.add(conversation)
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
        """Update mutable conversation settings without exposing the ORM entity."""
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
            if "character_id" in fields or "persona_id" in fields:
                await self._validate_context_references(
                    user_id,
                    request.character_id if "character_id" in fields else conversation.character_id,
                    request.persona_id if "persona_id" in fields else conversation.persona_id,
                )
            if "character_id" in fields:
                conversation.character_id = request.character_id
            if "persona_id" in fields:
                conversation.persona_id = request.persona_id
            if "provider" in fields:
                provider = request.provider or self._config.default_llm_provider
                self._validate_provider(provider)
                conversation.provider = provider
            if "model" in fields:
                conversation.model = request.model or self._config.default_llm_model

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
            next_cursor = encode_cursor(
                CursorPosition(oldest.created_at, oldest.id)
            )
        newest_first.reverse()
        return MessagePageResponse(
            items=[MessageResponse.model_validate(item) for item in newest_first],
            next_cursor=next_cursor,
        )


    async def _validate_context_references(
        self, user_id: UUID, character_id: UUID | None, persona_id: UUID | None
    ) -> None:
        async with self._uow_factory() as uow:
            if character_id is not None:
                character = await uow.characters.get_owned(character_id, user_id)
                if character is None:
                    raise ValidationException("Character does not belong to this user.")
            if persona_id is not None:
                persona = await uow.personas.get_owned(persona_id, user_id)
                if persona is None:
                    raise ValidationException("Persona does not belong to this user.")

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
