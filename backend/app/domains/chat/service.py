import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.context.assembler import ContextAssembler
from app.context.contracts import ContextAssemblyRequest
from app.common.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.chat.schemas import (
    ChatStreamCompleted,
    ChatStreamDelta,
    ChatStreamError,
    ChatStreamStarted,
)
from app.domains.chat.sse import encode_sse
from app.domains.conversations.model import Conversation
from app.domains.messages.model import (
    Message,
    MessageContentType,
    MessageRole,
    MessageStatus,
)
from app.domains.messages.schemas import (
    ChatExchangeResponse,
    MessageResponse,
    MessageSendRequest,
)
from app.llm.contracts import LLMChunk, LLMMessage, LLMMessageRole, LLMRequest, LLMResponse


class ChatGenerationService(Protocol):
    async def generate(self, provider_name: str, request: LLMRequest) -> LLMResponse: ...

    def stream(
        self, provider_name: str, request: LLMRequest
    ) -> AsyncIterator[LLMChunk]: ...


@dataclass(frozen=True, slots=True)
class PreparedExchange:
    conversation_id: UUID
    provider: str
    llm_request: LLMRequest
    user_message: MessageResponse
    assistant_message: MessageResponse
    needs_generation: bool
    reused: bool


@dataclass(frozen=True, slots=True)
class PreparedChatStream:
    events: AsyncIterator[str]


class ChatApplicationService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        llm_service: ChatGenerationService,
        config: AppConfig,
        context_assembler: ContextAssembler,
    ) -> None:
        self._uow_factory = uow_factory
        self._llm_service = llm_service
        self._config = config
        self._context_assembler = context_assembler

    async def send_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request: MessageSendRequest,
    ) -> ChatExchangeResponse:
        """Persist a user message, call the LLM, and atomically finalize its reply."""
        prepared = await self._prepare_exchange(
            user_id,
            conversation_id,
            request,
            streaming=False,
        )
        if not prepared.needs_generation:
            return ChatExchangeResponse(
                user_message=prepared.user_message,
                assistant_message=prepared.assistant_message,
                reused=True,
            )

        try:
            response = await self._llm_service.generate(
                prepared.provider,
                prepared.llm_request,
            )
        except asyncio.CancelledError as exc:
            await asyncio.shield(
                self._finalize_failure(prepared.assistant_message.id, "", exc)
            )
            raise
        except Exception as exc:
            await self._finalize_failure(prepared.assistant_message.id, "", exc)
            raise

        assistant = await self._finalize_success(
            prepared.assistant_message.id,
            response.content,
            provider_response_id=response.provider_response_id,
            token_usage=(
                response.usage.model_dump(exclude_none=True)
                if response.usage is not None
                else None
            ),
            metadata={
                "provider": response.provider,
                "model": response.model,
                "finish_reason": response.finish_reason,
                **response.metadata,
            },
        )
        return ChatExchangeResponse(
            user_message=prepared.user_message,
            assistant_message=assistant,
            reused=prepared.reused,
        )

    async def start_stream(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request: MessageSendRequest,
    ) -> PreparedChatStream:
        """Prepare persistence before headers and return an SSE event iterator."""
        prepared = await self._prepare_exchange(
            user_id,
            conversation_id,
            request,
            streaming=True,
        )
        chunks = (
            self._llm_service.stream(prepared.provider, prepared.llm_request)
            if prepared.needs_generation
            else None
        )
        return PreparedChatStream(events=self._stream_events(prepared, chunks))

    async def _prepare_exchange(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request: MessageSendRequest,
        *,
        streaming: bool,
    ) -> PreparedExchange:
        if len(request.content) > self._config.chat_max_message_length:
            raise ValidationException(
                f"Message exceeds {self._config.chat_max_message_length} characters."
            )

        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(
                conversation_id,
                user_id,
                for_update=True,
            )
            if conversation is None:
                raise NotFoundException(
                    "Conversation was not found.",
                    code=ErrorCode.CONVERSATION_NOT_FOUND,
                )

            now = datetime.now(UTC)
            existing_user = await uow.messages.get_by_client_message_id(
                conversation_id,
                request.client_message_id,
            )
            reused = existing_user is not None
            if existing_user is None:
                user_message = Message(
                    id=uuid4(),
                    conversation_id=conversation_id,
                    client_message_id=request.client_message_id,
                    role=MessageRole.USER,
                    content=request.content,
                    content_type=MessageContentType.MARKDOWN,
                    status=MessageStatus.COMPLETED,
                    created_at=now,
                    updated_at=now,
                    message_metadata={},
                )
                assistant_message = Message(
                    id=uuid4(),
                    conversation_id=conversation_id,
                    parent_message_id=user_message.id,
                    role=MessageRole.ASSISTANT,
                    content="",
                    content_type=MessageContentType.MARKDOWN,
                    status=(
                        MessageStatus.STREAMING
                        if streaming
                        else MessageStatus.PENDING
                    ),
                    created_at=now + timedelta(microseconds=1),
                    updated_at=now + timedelta(microseconds=1),
                    message_metadata={},
                )
                await uow.messages.add(user_message)
                await uow.messages.add(assistant_message)
            else:
                user_message = existing_user
                assistant_message = await uow.messages.get_assistant_reply(
                    user_message.id,
                    for_update=True,
                )
                if assistant_message is None:
                    assistant_message = Message(
                        id=uuid4(),
                        conversation_id=conversation_id,
                        parent_message_id=user_message.id,
                        role=MessageRole.ASSISTANT,
                        content="",
                        content_type=MessageContentType.MARKDOWN,
                        status=(
                            MessageStatus.STREAMING
                            if streaming
                            else MessageStatus.PENDING
                        ),
                        created_at=now + timedelta(microseconds=1),
                        updated_at=now + timedelta(microseconds=1),
                        message_metadata={},
                    )
                    await uow.messages.add(assistant_message)
                elif assistant_message.status == MessageStatus.COMPLETED:
                    await uow.flush()
                    return self._build_reused_prepared(
                        conversation, user_message, assistant_message, request
                    )
                elif assistant_message.status in {
                    MessageStatus.PENDING,
                    MessageStatus.STREAMING,
                }:
                    raise ConflictException(
                        "This message is already being processed.",
                        code=ErrorCode.CHAT_REQUEST_IN_PROGRESS,
                    )
                else:
                    assistant_message.content = ""
                    assistant_message.status = (
                        MessageStatus.STREAMING
                        if streaming
                        else MessageStatus.PENDING
                    )
                    assistant_message.provider_message_id = None
                    assistant_message.token_usage = None
                    assistant_message.message_metadata = {}

            if conversation.title is None:
                conversation.title = self._derive_title(request.content)
            conversation.last_message_at = now

            await uow.flush()
            context_messages = list(
                await uow.messages.list_context(
                    conversation_id,
                    limit=self._config.chat_context_message_limit,
                )
            )
            assembled = await self._context_assembler.assemble(
                ContextAssemblyRequest(
                    user_id=user_id,
                    conversation=conversation,
                    history=context_messages,
                )
            )
            prepared = self._build_prepared_from_context(
                conversation,
                user_message,
                assistant_message,
                request,
                assembled.messages,
                memory_ids=assembled.memory_ids,
                needs_generation=True,
                reused=reused,
            )
            await uow.commit()
            return prepared

    def _build_reused_prepared(
        self,
        conversation: Conversation,
        user_message: Message,
        assistant_message: Message,
        request: MessageSendRequest,
    ) -> PreparedExchange:
        return self._build_prepared_from_context(
            conversation,
            user_message,
            assistant_message,
            request,
            messages=[],
            memory_ids=(),
            needs_generation=False,
            reused=True,
        )

    def _build_prepared_from_context(
        self,
        conversation: Conversation,
        user_message: Message,
        assistant_message: Message,
        request: MessageSendRequest,
        messages: list[LLMMessage],
        *,
        memory_ids: tuple[UUID, ...],
        needs_generation: bool,
        reused: bool,
    ) -> PreparedExchange:
        provider = conversation.provider or self._config.default_llm_provider
        llm_messages = messages
        if needs_generation and not llm_messages:
            raise RuntimeError("Context assembler returned no messages for generation.")
        return PreparedExchange(
            conversation_id=conversation.id,
            provider=provider,
            llm_request=LLMRequest(
                messages=llm_messages or [
                    LLMMessage(role=LLMMessageRole.USER, content=user_message.content)
                ],
                model=conversation.model or self._config.default_llm_model,
                temperature=(
                    request.temperature
                    if request.temperature is not None
                    else self._config.chat_default_temperature
                ),
                max_tokens=(
                    request.max_tokens
                    if request.max_tokens is not None
                    else self._config.chat_default_max_tokens
                ),
                metadata={
                    "user_id": str(conversation.user_id),
                    "conversation_id": str(conversation.id),
                    "user_message_id": str(user_message.id),
                    "assistant_message_id": str(assistant_message.id),
                    "character_id": str(conversation.character_id)
                    if conversation.character_id
                    else None,
                    "persona_id": str(conversation.persona_id)
                    if conversation.persona_id
                    else None,
                    "memory_ids": [str(item) for item in memory_ids],
                    "execution_mode": request.execution_mode.value,
                    "agent_allowed_tools": request.agent_allowed_tools,
                },
            ),
            user_message=MessageResponse.model_validate(user_message),
            assistant_message=MessageResponse.model_validate(assistant_message),
            needs_generation=needs_generation,
            reused=reused,
        )

    async def _stream_events(
        self,
        prepared: PreparedExchange,
        chunks: AsyncIterator[LLMChunk] | None,
    ) -> AsyncIterator[str]:
        started = ChatStreamStarted(
            user_message=prepared.user_message,
            assistant_message=prepared.assistant_message,
            reused=prepared.reused,
        )
        yield encode_sse("message.created", started.model_dump(mode="json"))

        if not prepared.needs_generation:
            completed = ChatStreamCompleted(message=prepared.assistant_message)
            yield encode_sse("message.completed", completed.model_dump(mode="json"))
            return

        content_parts: list[str] = []
        provider_response_id: str | None = None
        finish_reason: str | None = None
        token_usage: dict[str, Any] | None = None
        runtime_metadata: dict[str, Any] = {}
        try:
            if chunks is None:
                raise RuntimeError("Streaming provider was not initialized.")
            async for chunk in self._with_heartbeats(chunks):
                if chunk is None:
                    yield ": keep-alive\n\n"
                    continue
                provider_response_id = (
                    chunk.provider_response_id or provider_response_id
                )
                finish_reason = chunk.finish_reason or finish_reason
                if chunk.usage is not None:
                    token_usage = chunk.usage.model_dump(exclude_none=True)
                if chunk.metadata:
                    runtime_metadata.update(chunk.metadata)
                if not chunk.content:
                    continue
                content_parts.append(chunk.content)
                delta = ChatStreamDelta(
                    message_id=prepared.assistant_message.id,
                    delta=chunk.content,
                )
                yield encode_sse("message.delta", delta.model_dump(mode="json"))

            assistant = await self._finalize_success(
                prepared.assistant_message.id,
                "".join(content_parts),
                provider_response_id=provider_response_id,
                token_usage=token_usage,
                metadata={
                    "provider": prepared.provider,
                    "model": prepared.llm_request.model,
                    "finish_reason": finish_reason,
                    **runtime_metadata,
                },
            )
            completed = ChatStreamCompleted(message=assistant)
            yield encode_sse("message.completed", completed.model_dump(mode="json"))
        except asyncio.CancelledError as exc:
            await asyncio.shield(
                self._finalize_failure(
                    prepared.assistant_message.id,
                    "".join(content_parts),
                    exc,
                )
            )
            raise
        except Exception as exc:
            await self._finalize_failure(
                prepared.assistant_message.id,
                "".join(content_parts),
                exc,
            )
            error = self._stream_error(prepared.assistant_message.id, exc)
            yield encode_sse("error", error.model_dump(mode="json"))

    async def _with_heartbeats(
        self,
        chunks: AsyncIterator[LLMChunk],
    ) -> AsyncIterator[LLMChunk | None]:
        """Keep the SSE connection active without cancelling a slow provider read."""
        iterator = chunks.__aiter__()
        next_chunk = asyncio.create_task(anext(iterator))
        try:
            while True:
                done, _ = await asyncio.wait(
                    {next_chunk},
                    timeout=self._config.chat_stream_heartbeat_seconds,
                )
                if not done:
                    yield None
                    continue
                try:
                    chunk = next_chunk.result()
                except StopAsyncIteration:
                    return
                yield chunk
                next_chunk = asyncio.create_task(anext(iterator))
        finally:
            if not next_chunk.done():
                next_chunk.cancel()
                with suppress(asyncio.CancelledError):
                    await next_chunk
            close = getattr(iterator, "aclose", None)
            if close is not None:
                with suppress(Exception):
                    await close()

    async def _finalize_success(
        self,
        assistant_message_id: UUID,
        content: str,
        *,
        provider_response_id: str | None,
        token_usage: dict[str, Any] | None,
        metadata: dict[str, Any],
    ) -> MessageResponse:
        async with self._uow_factory() as uow:
            assistant = await uow.messages.get_by_id(
                assistant_message_id,
                for_update=True,
            )
            if assistant is None:
                raise RuntimeError("Assistant message disappeared during generation.")
            assistant.content = content
            assistant.status = MessageStatus.COMPLETED
            assistant.provider_message_id = provider_response_id
            assistant.token_usage = token_usage
            assistant.message_metadata = {
                key: value for key, value in metadata.items() if value is not None
            }
            conversation = await uow.conversations.get_by_id(
                assistant.conversation_id,
                for_update=True,
            )
            if conversation is not None:
                conversation.last_message_at = datetime.now(UTC)
            await uow.flush()
            response = MessageResponse.model_validate(assistant)
            await uow.commit()
            return response

    async def _finalize_failure(
        self,
        assistant_message_id: UUID,
        partial_content: str,
        exc: BaseException,
    ) -> None:
        async with self._uow_factory() as uow:
            assistant = await uow.messages.get_by_id(
                assistant_message_id,
                for_update=True,
            )
            if assistant is None:
                return
            assistant.content = partial_content
            assistant.status = MessageStatus.FAILED
            assistant.message_metadata = {
                "error_code": (
                    exc.code.value
                    if isinstance(exc, AppException)
                    else "INTERNAL_ERROR"
                )
            }
            await uow.commit()

    @staticmethod
    def _derive_title(content: str) -> str:
        collapsed = " ".join(content.split())
        return collapsed if len(collapsed) <= 72 else f"{collapsed[:69].rstrip()}..."

    @staticmethod
    def _stream_error(message_id: UUID, exc: BaseException) -> ChatStreamError:
        if isinstance(exc, AppException):
            return ChatStreamError(
                message_id=message_id,
                code=exc.code.value,
                message=exc.message,
                details=exc.details,
            )
        return ChatStreamError(
            message_id=message_id,
            code=ErrorCode.CHAT_MESSAGE_FAILED.value,
            message="The assistant could not complete this response.",
        )
