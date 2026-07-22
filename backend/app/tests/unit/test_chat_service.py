from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import ConflictException
from app.core.config import AppConfig
from app.domains.chat.service import ChatApplicationService
from app.domains.conversations.schemas import ConversationCreateRequest
from app.domains.conversations.service import ConversationService
from app.domains.messages.model import MessageStatus
from app.domains.messages.schemas import MessageSendRequest
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.contracts import LLMChunk, LLMRequest, LLMResponse
from app.tests.unit.fakes import FakeUnitOfWorkFactory


class FakeLLMChatService(LLMChatService):
    def __init__(self) -> None:
        pass

    async def generate(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> LLMResponse:
        return LLMResponse(
            content="Xin chào từ Astra.",
            model=request.model or "roleplay-engine",
            provider=provider_name,
            finish_reason="stop",
        )

    def stream(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> AsyncIterator[LLMChunk]:
        async def iterator() -> AsyncIterator[LLMChunk]:
            for content in ("Xin ", "chào."):
                yield LLMChunk(
                    content=content,
                    model=request.model or "roleplay-engine",
                    provider=provider_name,
                )

        return iterator()


@pytest.mark.asyncio
async def test_chat_service_persists_exchange_and_reuses_client_id() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(
        default_llm_provider="ollama",
        default_llm_model="roleplay-engine",
        intelligence_enabled=False,
    )
    user_id = uuid4()
    conversation = await ConversationService(uow_factory, config).create(
        user_id,
        ConversationCreateRequest(),
    )
    service = ChatApplicationService(uow_factory, FakeLLMChatService(), config)
    client_message_id = uuid4()
    request = MessageSendRequest(
        content="Chào Astra",
        client_message_id=client_message_id,
    )

    first = await service.send_message(user_id, conversation.id, request)
    second = await service.send_message(user_id, conversation.id, request)

    assert first.assistant_message.content == "Xin chào từ Astra."
    assert first.assistant_message.status == MessageStatus.COMPLETED
    assert second.reused is True
    assert second.user_message.id == first.user_message.id
    assert len(uow_factory.messages.items) == 2


@pytest.mark.asyncio
async def test_chat_service_streams_sse_and_finalizes_message() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(
        default_llm_provider="ollama",
        default_llm_model="roleplay-engine",
        intelligence_enabled=False,
    )
    user_id = uuid4()
    conversation = await ConversationService(uow_factory, config).create(
        user_id,
        ConversationCreateRequest(),
    )
    service = ChatApplicationService(uow_factory, FakeLLMChatService(), config)

    stream = await service.start_stream(
        user_id,
        conversation.id,
        MessageSendRequest(content="Bắt đầu", client_message_id=uuid4()),
    )
    events = [event async for event in stream.events]

    assert any("event: message.created" in event for event in events)
    assert sum("event: message.delta" in event for event in events) == 2
    assert any("event: message.completed" in event for event in events)
    assistant = next(
        item
        for item in uow_factory.messages.items.values()
        if item.status == MessageStatus.COMPLETED and item.content == "Xin chào."
    )
    assert assistant.content == "Xin chào."


class ToggleStreamingLLMService(FakeLLMChatService):
    def __init__(self, *, fail: bool) -> None:
        self.fail = fail

    def stream(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> AsyncIterator[LLMChunk]:
        async def iterator() -> AsyncIterator[LLMChunk]:
            yield LLMChunk(
                content="Một phần",
                model=request.model or "roleplay-engine",
                provider=provider_name,
            )
            if self.fail:
                raise RuntimeError("provider interrupted")
            yield LLMChunk(
                content=" hoàn chỉnh.",
                model=request.model or "roleplay-engine",
                provider=provider_name,
            )

        return iterator()


@pytest.mark.asyncio
async def test_failed_stream_can_retry_with_the_same_client_message_id() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(
        default_llm_provider="ollama",
        default_llm_model="roleplay-engine",
        intelligence_enabled=False,
    )
    user_id = uuid4()
    conversation = await ConversationService(uow_factory, config).create(
        user_id,
        ConversationCreateRequest(),
    )
    llm = ToggleStreamingLLMService(fail=True)
    service = ChatApplicationService(uow_factory, llm, config)
    request = MessageSendRequest(content="Thử lại", client_message_id=uuid4())

    failed_stream = await service.start_stream(user_id, conversation.id, request)
    failed_events = [event async for event in failed_stream.events]

    assert any("event: error" in event for event in failed_events)
    failed_assistant = next(
        item
        for item in uow_factory.messages.items.values()
        if item.role.value == "assistant"
    )
    assert failed_assistant.status == MessageStatus.FAILED
    assert failed_assistant.content == "Một phần"

    llm.fail = False
    retry_stream = await service.start_stream(user_id, conversation.id, request)
    retry_events = [event async for event in retry_stream.events]

    assert any("event: message.completed" in event for event in retry_events)
    assert failed_assistant.status == MessageStatus.COMPLETED
    assert failed_assistant.content == "Một phần hoàn chỉnh."
    assert len(uow_factory.messages.items) == 2


@pytest.mark.asyncio
async def test_duplicate_request_is_rejected_while_stream_is_in_progress() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(
        default_llm_provider="ollama",
        default_llm_model="roleplay-engine",
        intelligence_enabled=False,
    )
    user_id = uuid4()
    conversation = await ConversationService(uow_factory, config).create(
        user_id,
        ConversationCreateRequest(),
    )
    service = ChatApplicationService(uow_factory, FakeLLMChatService(), config)
    request = MessageSendRequest(content="Đang xử lý", client_message_id=uuid4())

    await service.start_stream(user_id, conversation.id, request)

    with pytest.raises(ConflictException) as exc_info:
        await service.start_stream(user_id, conversation.id, request)

    assert exc_info.value.code == ErrorCode.CHAT_REQUEST_IN_PROGRESS
