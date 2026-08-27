from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.common.exceptions import ConflictException, ValidationException
from app.core.config import AppConfig
from app.domains.conversations.model import Conversation
from app.domains.memories.model import Memory, MemoryKind, MemoryScope, MemoryStatus
from app.domains.memories.retrieval import MemoryRetrievalService
from app.domains.memories.sanitizer import MemorySanitizer
from app.domains.memories.schemas import MemoryCreateRequest
from app.domains.memories.service import MemoryService
from app.domains.prompts.composer import StructuredPromptComposer
from app.domains.prompts.contracts import (
    MemoryPromptItem,
    MemoryPromptState,
    RoleplayPromptContext,
)
from app.embeddings.service import EmbeddingService
from app.tests.unit.fakes import FakeUnitOfWorkFactory


def config() -> AppConfig:
    return AppConfig(
        _env_file=None,
        OPENAI_API_KEY="test-key",
        MEMORY_ENABLED=True,
        MEMORY_EMBEDDINGS_ENABLED=False,
    )


def test_prompt_composer_includes_summary_and_relevant_memories() -> None:
    context = RoleplayPromptContext(
        memory=MemoryPromptState(
            conversation_summary="Hai người đang trú trong ngọn hải đăng.",
            items=(
                MemoryPromptItem(
                    scope="user",
                    kind="preference",
                    content="Người dùng không thích bị tự mô tả hành động.",
                    importance=0.9,
                    confidence=1.0,
                ),
            ),
        )
    )
    messages = StructuredPromptComposer().compose(context, None, "Tiếp tục đi")
    assert "Conversation continuity summary" in messages[0].content
    assert "ngọn hải đăng" in messages[0].content
    assert "không thích bị tự mô tả" in messages[0].content


def test_memory_sanitizer_blocks_credentials() -> None:
    sanitizer = MemorySanitizer()
    assert sanitizer.is_safe("Người dùng thích cà phê đen")
    assert not sanitizer.is_safe("API_KEY=sk-abcdefghijklmnopqrstuvwxyz")
    assert sanitizer.normalize_key("User Favorite Drink") == "user-favorite-drink"
    redacted = sanitizer.redact_secrets(
        "Ghi chú bình thường\nAPI_KEY=sk-abcdefghijklmnopqrstuvwxyz"
    )
    assert "sk-" not in redacted
    assert "[REDACTED]" in redacted


@pytest.mark.asyncio
async def test_manual_memory_create_and_snapshot() -> None:
    factory = FakeUnitOfWorkFactory()
    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)
    factory.conversations.items[conversation_id] = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="Memory test",
        conversation_metadata={},
        created_at=now,
        updated_at=now,
    )
    service = MemoryService(factory, EmbeddingService(None), config())
    created = await service.create(
        user_id,
        MemoryCreateRequest(
            scope=MemoryScope.CONVERSATION,
            kind=MemoryKind.EVENT,
            conversation_id=conversation_id,
            content="Hai người đã tìm thấy ngọn hải đăng.",
        ),
    )
    assert created.status == MemoryStatus.ACTIVE
    snapshot = await service.conversation_snapshot(user_id, conversation_id)
    assert len(snapshot.memories) == 1
    assert "ngọn hải đăng" in snapshot.memories[0].content


@pytest.mark.asyncio
async def test_manual_memory_rejects_duplicate_active_key() -> None:
    factory = FakeUnitOfWorkFactory()
    user_id = uuid4()
    service = MemoryService(factory, EmbeddingService(None), config())
    request = MemoryCreateRequest(
        scope=MemoryScope.USER,
        kind=MemoryKind.PREFERENCE,
        normalized_key="user.reply-length",
        content="Người dùng thích câu trả lời ngắn.",
    )
    await service.create(user_id, request)
    with pytest.raises(ConflictException):
        await service.create(user_id, request)


@pytest.mark.asyncio
async def test_user_memory_rejects_conversation_context() -> None:
    factory = FakeUnitOfWorkFactory()
    service = MemoryService(factory, EmbeddingService(None), config())
    with pytest.raises(ValidationException):
        await service.create(
            uuid4(),
            MemoryCreateRequest(
                scope=MemoryScope.USER,
                kind=MemoryKind.FACT,
                conversation_id=uuid4(),
                content="Không được phép gắn vào hội thoại.",
            ),
        )


@pytest.mark.asyncio
async def test_memory_retrieval_prefers_semantic_match() -> None:
    factory = FakeUnitOfWorkFactory()
    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="Memory test",
        conversation_metadata={},
        created_at=now,
        updated_at=now,
    )
    factory.conversations.items[conversation_id] = conversation
    close = Memory(
        id=uuid4(),
        user_id=user_id,
        conversation_id=conversation_id,
        scope=MemoryScope.CONVERSATION,
        kind=MemoryKind.FACT,
        status=MemoryStatus.ACTIVE,
        normalized_key="place",
        content="Ngọn hải đăng nằm ở phía tây bắc.",
        importance=0.7,
        confidence=0.9,
        embedding=[1.0, 0.0],
        access_count=0,
        memory_metadata={},
        created_at=now,
        updated_at=now,
    )
    far = Memory(
        id=uuid4(),
        user_id=user_id,
        conversation_id=conversation_id,
        scope=MemoryScope.CONVERSATION,
        kind=MemoryKind.FACT,
        status=MemoryStatus.ACTIVE,
        normalized_key="weather",
        content="Trời đang lạnh.",
        importance=0.7,
        confidence=0.9,
        embedding=[0.0, 1.0],
        access_count=0,
        memory_metadata={},
        created_at=now,
        updated_at=now,
    )
    factory.memories.items[close.id] = close
    factory.memories.items[far.id] = far
    async with factory() as uow:
        state = await MemoryRetrievalService(config()).retrieve(
            uow,
            conversation,
            user_id,
            "Hải đăng ở đâu?",
            [1.0, 0.0],
        )
    assert state.items[0].content == close.content

@pytest.mark.asyncio
async def test_memory_retrieval_does_not_leak_another_persona() -> None:
    factory = FakeUnitOfWorkFactory()
    user_id = uuid4()
    conversation_id = uuid4()
    other_persona_id = uuid4()
    now = datetime.now(UTC)
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title="No persona",
        conversation_metadata={},
        created_at=now,
        updated_at=now,
    )
    generic = Memory(
        id=uuid4(),
        user_id=user_id,
        scope=MemoryScope.USER,
        kind=MemoryKind.PREFERENCE,
        status=MemoryStatus.ACTIVE,
        normalized_key="generic",
        content="Người dùng thích câu trả lời ngắn.",
        importance=0.8,
        confidence=1.0,
        embedding=[1.0, 0.0],
        access_count=0,
        memory_metadata={},
        created_at=now,
        updated_at=now,
    )
    persona_only = Memory(
        id=uuid4(),
        user_id=user_id,
        persona_id=other_persona_id,
        scope=MemoryScope.USER,
        kind=MemoryKind.PREFERENCE,
        status=MemoryStatus.ACTIVE,
        normalized_key="persona-only",
        content="Ký ức chỉ dành cho persona khác.",
        importance=1.0,
        confidence=1.0,
        embedding=[1.0, 0.0],
        access_count=0,
        memory_metadata={},
        created_at=now,
        updated_at=now,
    )
    factory.memories.items[generic.id] = generic
    factory.memories.items[persona_only.id] = persona_only
    async with factory() as uow:
        state = await MemoryRetrievalService(config()).retrieve(
            uow,
            conversation,
            user_id,
            "Trả lời ngắn nhé",
            [1.0, 0.0],
        )
    assert [item.content for item in state.items] == [generic.content]
