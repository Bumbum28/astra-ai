from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException, ValidationException
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.memories.model import Memory, MemoryScope
from app.domains.memories.schemas import (
    MemoryCreateRequest,
    MemoryListResponse,
    MemoryResponse,
)


class MemoryService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self, user_id: UUID, request: MemoryCreateRequest
    ) -> MemoryResponse:
        """Store an explicit long-term memory after validating its ownership scope."""
        async with self._uow_factory() as uow:
            if request.character_id is not None:
                character = await uow.characters.get_owned(request.character_id, user_id)
                if character is None:
                    raise ValidationException("Character does not belong to this user.")
            if request.conversation_id is not None:
                conversation = await uow.conversations.get_owned(
                    request.conversation_id, user_id
                )
                if conversation is None:
                    raise ValidationException("Conversation does not belong to this user.")
            if request.scope == MemoryScope.USER:
                conversation_id = None
                character_id = None
            else:
                conversation_id = request.conversation_id
                character_id = request.character_id
            memory = Memory(
                id=uuid4(),
                user_id=user_id,
                scope=request.scope,
                kind=request.kind,
                content=request.content.strip(),
                importance=request.importance,
                conversation_id=conversation_id,
                character_id=character_id,
                source_message_id=request.source_message_id,
                memory_metadata=request.metadata,
            )
            await uow.memories.add(memory)
            await uow.flush()
            response = MemoryResponse.model_validate(memory)
            await uow.commit()
            return response

    async def list_for_user(self, user_id: UUID) -> MemoryListResponse:
        """List active long-term memories ordered by relevance hints."""
        async with self._uow_factory() as uow:
            items = await uow.memories.list_for_user(user_id)
        return MemoryListResponse(
            items=[MemoryResponse.model_validate(item) for item in items]
        )

    async def archive(self, user_id: UUID, memory_id: UUID) -> None:
        """Archive a memory without losing provenance for future audit/debugging."""
        async with self._uow_factory() as uow:
            memory = await uow.memories.get_owned(memory_id, user_id, for_update=True)
            if memory is None:
                raise NotFoundException(
                    "Memory was not found.", code=ErrorCode.MEMORY_NOT_FOUND
                )
            memory.archived_at = datetime.now(UTC)
            await uow.commit()
