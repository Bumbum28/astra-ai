from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.domains.memories.model import (
    Memory,
    MemoryScope,
    MemoryStatus,
    MemoryTask,
    MemoryTaskStatus,
)
from app.domains.memories.sanitizer import MemorySanitizer
from app.domains.memories.schemas import (
    ConversationMemorySnapshot,
    ConversationSummaryResponse,
    MemoryCreateRequest,
    MemoryPage,
    MemoryRefreshResponse,
    MemoryResponse,
    MemoryUpdateRequest,
)
from app.embeddings.service import EmbeddingService
from app.utils.cursors import CursorPosition, decode_cursor, encode_cursor


class MemoryService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        embedding_service: EmbeddingService,
        config: AppConfig,
        sanitizer: MemorySanitizer | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._embeddings = embedding_service
        self._config = config
        self._sanitizer = sanitizer or MemorySanitizer()

    async def create(
        self, user_id: UUID, request: MemoryCreateRequest
    ) -> MemoryResponse:
        self._validate_scope(
            request.scope, request.conversation_id, request.character_id
        )
        if not self._sanitizer.is_safe(request.content):
            raise ValidationException(
                "Memory content may not contain credentials or secrets."
            )
        embedding = await self._safe_embedding(request.content)
        async with self._uow_factory() as uow:
            await self._validate_context_ownership(
                uow,
                user_id,
                request.conversation_id,
                request.character_id,
                request.persona_id,
            )
            normalized_key = self._sanitizer.normalize_key(
                request.normalized_key or request.content[:120]
            )
            existing = await uow.memories.find_active_by_key(
                user_id,
                scope=request.scope,
                normalized_key=normalized_key,
                conversation_id=request.conversation_id,
                character_id=request.character_id,
                persona_id=request.persona_id,
                for_update=True,
            )
            if existing is not None:
                raise ConflictException(
                    "An active memory with the same key already exists."
                )
            memory = Memory(
                id=uuid4(),
                user_id=user_id,
                conversation_id=request.conversation_id,
                character_id=request.character_id,
                persona_id=request.persona_id,
                scope=request.scope,
                kind=request.kind,
                status=MemoryStatus.ACTIVE,
                normalized_key=normalized_key,
                content=request.content,
                importance=request.importance,
                confidence=request.confidence,
                embedding=embedding,
                access_count=0,
                expires_at=request.expires_at,
                memory_metadata={"source": "manual"},
            )
            await uow.memories.add(memory)
            await uow.flush()
            response = MemoryResponse.model_validate(memory)
            await uow.commit()
            return response

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: str | None,
        scope: MemoryScope | None,
        conversation_id: UUID | None,
        include_archived: bool,
    ) -> MemoryPage:
        position = decode_cursor(cursor) if cursor else None
        async with self._uow_factory() as uow:
            items = list(
                await uow.memories.list_for_user(
                    user_id,
                    limit=limit + 1,
                    cursor=position,
                    scope=scope,
                    conversation_id=conversation_id,
                    include_archived=include_archived,
                )
            )
        has_more = len(items) > limit
        page_items = items[:limit]
        next_cursor = None
        if has_more and page_items:
            last = page_items[-1]
            next_cursor = encode_cursor(CursorPosition(last.updated_at, last.id))
        return MemoryPage(
            items=[MemoryResponse.model_validate(item) for item in page_items],
            next_cursor=next_cursor,
        )

    async def update(
        self,
        user_id: UUID,
        memory_id: UUID,
        request: MemoryUpdateRequest,
    ) -> MemoryResponse:
        embedding = None
        if request.content is not None:
            if not self._sanitizer.is_safe(request.content):
                raise ValidationException(
                    "Memory content may not contain credentials or secrets."
                )
            embedding = await self._safe_embedding(request.content)
        async with self._uow_factory() as uow:
            memory = await uow.memories.get_owned(memory_id, user_id, for_update=True)
            if memory is None:
                raise NotFoundException(
                    "Memory was not found.", code=ErrorCode.MEMORY_NOT_FOUND
                )
            if request.content is not None:
                memory.content = request.content.strip()
                memory.embedding = embedding
            if request.importance is not None:
                memory.importance = request.importance
            if request.confidence is not None:
                memory.confidence = request.confidence
            if "expires_at" in request.model_fields_set:
                memory.expires_at = request.expires_at
            if request.status is not None:
                memory.status = request.status
            await uow.flush()
            response = MemoryResponse.model_validate(memory)
            await uow.commit()
            return response

    async def archive(self, user_id: UUID, memory_id: UUID) -> None:
        async with self._uow_factory() as uow:
            memory = await uow.memories.get_owned(memory_id, user_id, for_update=True)
            if memory is None:
                raise NotFoundException(
                    "Memory was not found.", code=ErrorCode.MEMORY_NOT_FOUND
                )
            memory.status = MemoryStatus.ARCHIVED
            await uow.commit()

    async def conversation_snapshot(
        self, user_id: UUID, conversation_id: UUID
    ) -> ConversationMemorySnapshot:
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(conversation_id, user_id)
            if conversation is None:
                raise NotFoundException(
                    "Conversation was not found.",
                    code=ErrorCode.CONVERSATION_NOT_FOUND,
                )
            summary = await uow.conversation_summaries.get_by_conversation(
                conversation_id
            )
            memories = list(
                await uow.memories.list_context_candidates(
                    user_id,
                    conversation_id=conversation_id,
                    character_id=conversation.character_id,
                    persona_id=conversation.persona_id,
                    query_text="",
                    limit=100,
                )
            )
            pending = await uow.memory_tasks.count_pending(conversation_id)
        return ConversationMemorySnapshot(
            summary=(
                ConversationSummaryResponse.model_validate(summary)
                if summary is not None
                else None
            ),
            memories=[MemoryResponse.model_validate(item) for item in memories],
            pending_tasks=pending,
        )

    async def refresh(
        self, user_id: UUID, conversation_id: UUID
    ) -> MemoryRefreshResponse:
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(conversation_id, user_id)
            if conversation is None:
                raise NotFoundException(
                    "Conversation was not found.",
                    code=ErrorCode.CONVERSATION_NOT_FOUND,
                )
            messages = list(await uow.messages.list_context(conversation_id, limit=2))
            if not messages:
                return MemoryRefreshResponse(queued=False)
            trigger = messages[-1]
            existing = await uow.memory_tasks.get_by_trigger_message(trigger.id)
            if existing is not None:
                existing.status = MemoryTaskStatus.PENDING
                existing.attempts = 0
                existing.available_at = datetime.now(UTC)
                existing.last_error = None
                existing.task_metadata = {**existing.task_metadata, "forced": True}
                await uow.commit()
                return MemoryRefreshResponse(queued=True, task_id=existing.id)
            task = MemoryTask(
                id=uuid4(),
                conversation_id=conversation_id,
                trigger_message_id=trigger.id,
                status=MemoryTaskStatus.PENDING,
                attempts=0,
                available_at=datetime.now(UTC),
                task_metadata={"forced": True},
            )
            await uow.memory_tasks.add(task)
            await uow.commit()
            return MemoryRefreshResponse(queued=True, task_id=task.id)

    async def _safe_embedding(self, content: str) -> list[float] | None:
        try:
            return await self._embeddings.embed_one(content)
        except Exception:
            return None

    async def _validate_context_ownership(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        conversation_id: UUID | None,
        character_id: UUID | None,
        persona_id: UUID | None,
    ) -> None:
        # UnitOfWork is structural; keep calls explicit for mypy-friendly fakes.
        if conversation_id is not None:
            conversation = await uow.conversations.get_owned(conversation_id, user_id)
            if conversation is None:
                raise NotFoundException(
                    "Conversation was not found.",
                    code=ErrorCode.CONVERSATION_NOT_FOUND,
                )
        if character_id is not None:
            character = await uow.characters.get_owned(character_id, user_id)
            if character is None:
                raise NotFoundException(
                    "Character was not found.", code=ErrorCode.CHARACTER_NOT_FOUND
                )
        if persona_id is not None:
            persona = await uow.personas.get_owned(persona_id, user_id)
            if persona is None:
                raise NotFoundException(
                    "Persona was not found.", code=ErrorCode.PERSONA_NOT_FOUND
                )

    @staticmethod
    def _validate_scope(
        scope: MemoryScope,
        conversation_id: UUID | None,
        character_id: UUID | None,
    ) -> None:
        if scope == MemoryScope.USER:
            if conversation_id is not None or character_id is not None:
                raise ValidationException(
                    "User memory may not set conversation_id or character_id."
                )
            return
        if scope == MemoryScope.CHARACTER:
            if character_id is None:
                raise ValidationException("Character memory requires character_id.")
            if conversation_id is not None:
                raise ValidationException(
                    "Character memory may not set conversation_id."
                )
            return
        if conversation_id is None:
            raise ValidationException(
                f"{scope.value} memory requires conversation_id."
            )
        if character_id is not None:
            raise ValidationException(
                f"{scope.value} memory may not set character_id."
            )
