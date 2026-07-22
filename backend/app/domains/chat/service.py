import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.chat.language_guard import VietnameseOutputGuard
from app.domains.chat.schemas import (
    ChatStreamCompleted,
    ChatStreamDelta,
    ChatStreamError,
    ChatStreamStarted,
)
from app.domains.chat.sse import encode_sse
from app.domains.conversations.model import Conversation
from app.domains.intelligence.service import IntelligencePipeline
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
from app.domains.prompts.composer import StructuredPromptComposer
from app.domains.prompts.contracts import (
    PromptComposer,
    PromptContextResolver,
    RoleplayPromptContext,
)
from app.domains.prompts.service import RoleplayPromptContextResolver
from app.domains.prompts.token_budget import PromptTokenBudgeter
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.contracts import (
    LLMChunk,
    LLMMessage,
    LLMMessageRole,
    LLMRequest,
    LLMResponse,
)
from app.llm.contracts.request import ReasoningEffort


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
        llm_service: LLMChatService,
        config: AppConfig,
        prompt_context_resolver: PromptContextResolver | None = None,
        prompt_composer: PromptComposer | None = None,
        language_guard: VietnameseOutputGuard | None = None,
        intelligence_pipeline: IntelligencePipeline | None = None,
        token_budgeter: PromptTokenBudgeter | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._llm_service = llm_service
        self._config = config
        self._prompt_context_resolver = (
            prompt_context_resolver or RoleplayPromptContextResolver()
        )
        self._prompt_composer = prompt_composer or StructuredPromptComposer()
        self._language_guard = language_guard or VietnameseOutputGuard()
        self._intelligence = intelligence_pipeline or IntelligencePipeline(
            llm_service, config
        )
        self._token_budgeter = token_budgeter or PromptTokenBudgeter()

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
            response = await self._generate_with_language_guard(prepared)
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
                **response.metadata,
                "provider": response.provider,
                "model": response.model,
                "finish_reason": response.finish_reason,
            },
        )
        return ChatExchangeResponse(
            user_message=prepared.user_message,
            assistant_message=assistant,
            reused=prepared.reused,
        )

    async def _generate_with_language_guard(
        self,
        prepared: PreparedExchange,
    ) -> LLMResponse:
        intelligence_result = await self._intelligence.generate(
            prepared.provider,
            prepared.llm_request,
        )
        first_response = intelligence_result.response
        if not self._language_guard.contains_forbidden_script(
            first_response.content
        ):
            return first_response

        strict_retry_instruction = LLMMessage(
            role=LLMMessageRole.SYSTEM,
            content=(
                "The previous generation violated the language policy. Regenerate "
                "the answer from scratch using Vietnamese only. Preserve the "
                "current user-writing-style mode already specified in the system "
                "prompt: use full standard Vietnamese for a standard user message, "
                "or mirror moderate teencode only when the latest user message uses "
                "it. Do not output Chinese characters, pinyin, or a translation "
                "section."
            ),
        )
        retry_request = prepared.llm_request.model_copy(
            update={
                "messages": [
                    strict_retry_instruction,
                    *prepared.llm_request.messages,
                ],
                "temperature": min(
                    prepared.llm_request.temperature
                    if prepared.llm_request.temperature is not None
                    else 0.3,
                    0.3,
                ),
            }
        )
        try:
            retry_response = await self._llm_service.generate(
                prepared.provider,
                retry_request,
            )
        except Exception:
            guarded = self._language_guard.sanitize(first_response.content)
            return first_response.model_copy(
                update={
                    "content": guarded.content,
                    "metadata": {
                        **first_response.metadata,
                        "language_guard_triggered": True,
                        "language_guard_retry_failed": True,
                    },
                }
            )

        guarded = self._language_guard.sanitize(retry_response.content)
        return retry_response.model_copy(
            update={
                "content": guarded.content,
                "metadata": {
                    **retry_response.metadata,
                    "language_guard_triggered": True,
                    "language_guard_sanitized": guarded.changed,
                },
            }
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
        if self._config.intelligence_enabled:
            return PreparedChatStream(
                events=self._intelligent_stream_events(prepared)
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
                    return self._build_prepared(
                        conversation,
                        user_message,
                        assistant_message,
                        request,
                        context_messages=[],
                        prompt_context=RoleplayPromptContext(),
                        needs_generation=False,
                        reused=True,
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
            prompt_context = await self._prompt_context_resolver.resolve(
                uow,
                conversation,
            )
            prepared = self._build_prepared(
                conversation,
                user_message,
                assistant_message,
                request,
                context_messages=context_messages,
                prompt_context=prompt_context,
                needs_generation=True,
                reused=reused,
            )
            await uow.commit()
            return prepared

    def _build_prepared(
        self,
        conversation: Conversation,
        user_message: Message,
        assistant_message: Message,
        request: MessageSendRequest,
        *,
        context_messages: list[Message],
        prompt_context: RoleplayPromptContext,
        needs_generation: bool,
        reused: bool,
    ) -> PreparedExchange:
        provider = conversation.provider or self._config.default_llm_provider
        messages = self._prompt_composer.compose(
            prompt_context,
            conversation.system_prompt,
            user_message.content,
        )
        messages.extend(
            LLMMessage(
                role=LLMMessageRole(item.role.value),
                content=item.content,
            )
            for item in context_messages
        )
        if not context_messages or context_messages[-1].id != user_message.id:
            messages.append(
                LLMMessage(role=LLMMessageRole.USER, content=user_message.content)
            )
        budget = self._token_budgeter.trim(
            messages,
            token_budget=self._config.chat_context_token_budget,
        )

        return PreparedExchange(
            conversation_id=conversation.id,
            provider=provider,
            llm_request=LLMRequest(
                messages=budget.messages,
                model=conversation.model or self._config.default_llm_model,
                temperature=(
                    request.temperature
                    if request.temperature is not None
                    else conversation.temperature
                    if conversation.temperature is not None
                    else self._config.chat_default_temperature
                ),
                max_tokens=(
                    request.max_tokens
                    if request.max_tokens is not None
                    else conversation.max_tokens
                    if conversation.max_tokens is not None
                    else self._config.chat_default_max_tokens
                ),
                reasoning_effort=cast(
                    ReasoningEffort, self._config.openai_reasoning_effort
                ),
                store=False,
                metadata={
                    "context_token_budget": self._config.chat_context_token_budget,
                    "context_estimated_tokens": budget.estimated_tokens,
                    "context_dropped_messages": budget.dropped_messages,
                    "context_truncated_system_messages": (
                        budget.truncated_system_messages
                    ),
                    "conversation_id": str(conversation.id),
                    "character_id": (
                        str(conversation.character_id)
                        if conversation.character_id is not None
                        else None
                    ),
                    "persona_id": (
                        str(conversation.persona_id)
                        if conversation.persona_id is not None
                        else None
                    ),
                },
            ),
            user_message=MessageResponse.model_validate(user_message),
            assistant_message=MessageResponse.model_validate(assistant_message),
            needs_generation=needs_generation,
            reused=reused,
        )

    async def _intelligent_stream_events(
        self,
        prepared: PreparedExchange,
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

        try:
            response = await self._generate_with_language_guard(prepared)
            for content in self._display_chunks(response.content):
                delta = ChatStreamDelta(
                    message_id=prepared.assistant_message.id,
                    delta=content,
                )
                yield encode_sse("message.delta", delta.model_dump(mode="json"))
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
                    **response.metadata,
                    "provider": response.provider,
                    "model": response.model,
                    "finish_reason": response.finish_reason,
                },
            )
            completed = ChatStreamCompleted(message=assistant)
            yield encode_sse("message.completed", completed.model_dump(mode="json"))
        except asyncio.CancelledError as exc:
            await asyncio.shield(
                self._finalize_failure(prepared.assistant_message.id, "", exc)
            )
            raise
        except Exception as exc:
            await self._finalize_failure(prepared.assistant_message.id, "", exc)
            error = self._stream_error(prepared.assistant_message.id, exc)
            yield encode_sse("error", error.model_dump(mode="json"))

    @staticmethod
    def _display_chunks(content: str, target_size: int = 96) -> list[str]:
        if not content:
            return []
        words = content.split(" ")
        chunks: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if current and len(candidate) > target_size:
                chunks.append(current + " ")
                current = word
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks

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
        language_guard_triggered = False
        provider_response_id: str | None = None
        finish_reason: str | None = None
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
                if not chunk.content:
                    continue
                guarded_chunk = self._language_guard.sanitize_fragment(
                    chunk.content
                )
                language_guard_triggered = (
                    language_guard_triggered or guarded_chunk.changed
                )
                if not guarded_chunk.content:
                    continue
                content_parts.append(guarded_chunk.content)
                delta = ChatStreamDelta(
                    message_id=prepared.assistant_message.id,
                    delta=guarded_chunk.content,
                )
                yield encode_sse("message.delta", delta.model_dump(mode="json"))

            final_content = "".join(content_parts).strip()
            if language_guard_triggered and not final_content:
                final_content = self._language_guard.fallback_message
                delta = ChatStreamDelta(
                    message_id=prepared.assistant_message.id,
                    delta=final_content,
                )
                yield encode_sse("message.delta", delta.model_dump(mode="json"))

            assistant = await self._finalize_success(
                prepared.assistant_message.id,
                final_content,
                provider_response_id=provider_response_id,
                token_usage=None,
                metadata={
                    "provider": prepared.provider,
                    "model": prepared.llm_request.model,
                    "finish_reason": finish_reason,
                    "language_guard_triggered": language_guard_triggered,
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
            relationship = await uow.relationships.get_by_conversation(
                assistant.conversation_id,
                for_update=True,
            )
            if relationship is not None:
                relationship.turn_count += 1
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
