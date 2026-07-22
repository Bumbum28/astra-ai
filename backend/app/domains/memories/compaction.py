from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.chat.language_guard import VietnameseOutputGuard
from app.domains.memories.model import (
    ConversationSummary,
    Memory,
    MemoryScope,
    MemoryStatus,
    MemoryTaskStatus,
)
from app.domains.memories.sanitizer import MemorySanitizer
from app.domains.memories.schemas import ExtractedMemory, MemoryExtractionResult
from app.embeddings.service import EmbeddingService
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.contracts import LLMMessage, LLMMessageRole, LLMRequest
from app.llm.contracts.request import ReasoningEffort
from app.utils.cursors import CursorPosition


class MemoryCompactionService:
    _INSTRUCTION = (
        "You maintain private long-term memory for a Vietnamese roleplay chat. "
        "Return only the requested structured JSON. Update the compact summary from "
        "the previous summary and new transcript. Extract only stable, useful facts, "
        "preferences, boundaries, goals, promises, relationship developments, or "
        "world events. Do not store passwords, API keys, seed phrases, credentials, "
        "or transient small talk. Do not infer sensitive facts that were not stated. "
        "Use concise Vietnamese. normalized_key must be stable lowercase ASCII-like "
        "tokens such as user.favorite-drink or world.lighthouse-location. Scope rules: "
        "user for facts/preferences about the user across chats; character for stable "
        "facts about the selected character; relationship for shared relationship "
        "state; world for fictional world facts; conversation for scene-specific "
        "continuity."
    )

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        llm_service: LLMChatService,
        embeddings: EmbeddingService,
        config: AppConfig,
        sanitizer: MemorySanitizer | None = None,
        language_guard: VietnameseOutputGuard | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._llm = llm_service
        self._embeddings = embeddings
        self._config = config
        self._sanitizer = sanitizer or MemorySanitizer()
        self._language_guard = language_guard or VietnameseOutputGuard()

    async def process_task(self, task_id: UUID) -> None:
        async with self._uow_factory() as uow:
            task = await uow.memory_tasks.get_by_id(task_id, for_update=True)
            if task is None:
                return
            conversation = await uow.conversations.get_by_id(task.conversation_id)
            if conversation is None:
                task.status = MemoryTaskStatus.COMPLETED
                task.finished_at = datetime.now(UTC)
                await uow.commit()
                return
            summary = await uow.conversation_summaries.get_by_conversation(
                conversation.id
            )
            after = None
            if (
                summary is not None
                and summary.covered_through_created_at is not None
                and summary.covered_through_message_id is not None
            ):
                after = CursorPosition(
                    summary.covered_through_created_at,
                    summary.covered_through_message_id,
                )
            messages = list(
                await uow.messages.list_completed_after(
                    conversation.id,
                    after=after,
                    limit=self._config.memory_compaction_batch_size,
                )
            )
            forced = bool(task.task_metadata.get("forced"))
            if not messages:
                task.status = MemoryTaskStatus.COMPLETED
                task.finished_at = datetime.now(UTC)
                task.task_metadata = {
                    **task.task_metadata,
                    "skipped": "no_new_messages",
                }
                await uow.commit()
                return
            if (
                len(messages) < self._config.memory_compaction_message_threshold
                and not forced
            ):
                task.status = MemoryTaskStatus.COMPLETED
                task.finished_at = datetime.now(UTC)
                task.task_metadata = {**task.task_metadata, "skipped": "threshold"}
                await uow.commit()
                return
            raw_previous_summary = summary.content if summary is not None else ""
            previous_summary = self._language_guard.sanitize_fragment(
                self._sanitizer.redact_secrets(raw_previous_summary)
            ).content.strip()
            conversation_snapshot = (
                conversation.user_id,
                conversation.character_id,
                conversation.persona_id,
            )

        transcript = "\n".join(
            f"{item.role.value}: "
            f"{self._sanitizer.redact_secrets(item.content)}"
            for item in messages
        )
        request = LLMRequest(
            messages=[
                LLMMessage(role=LLMMessageRole.SYSTEM, content=self._INSTRUCTION),
                LLMMessage(
                    role=LLMMessageRole.USER,
                    content=(
                        f"PREVIOUS SUMMARY:\n{previous_summary or '(none)'}\n\n"
                        f"NEW TRANSCRIPT:\n{transcript}"
                    ),
                ),
            ],
            model=self._config.memory_extraction_model,
            max_tokens=self._config.memory_extraction_max_tokens,
            reasoning_effort=cast(
                ReasoningEffort,
                self._config.memory_extraction_reasoning_effort,
            ),
            response_schema_name="astra_memory_extraction",
            response_schema=MemoryExtractionResult.model_json_schema(),
            store=False,
            metadata={"memory_task_id": str(task_id)},
        )
        response = await self._llm.generate(
            self._config.memory_extraction_provider,
            request,
        )
        result = MemoryExtractionResult.model_validate_json(response.content)
        guarded_summary = self._language_guard.sanitize_fragment(
            self._sanitizer.redact_secrets(result.summary)
        ).content.strip()
        safe_summary = guarded_summary or previous_summary or (
            "Chưa có đủ nội dung an toàn để tạo tóm tắt."
        )
        safe_items: list[ExtractedMemory] = []
        for item in result.memories:
            if not self._sanitizer.is_safe(item.content):
                continue
            guarded_content = self._language_guard.sanitize_fragment(
                item.content
            ).content.strip()
            if not guarded_content:
                continue
            safe_items.append(item.model_copy(update={"content": guarded_content}))
        try:
            embeddings = await self._embeddings.embed_many(
                [item.content for item in safe_items]
            )
        except Exception:
            embeddings = [None for _ in safe_items]
        last = messages[-1]
        user_id, character_id, persona_id = conversation_snapshot

        async with self._uow_factory() as uow:
            task = await uow.memory_tasks.get_by_id(task_id, for_update=True)
            if task is None:
                return
            summary = await uow.conversation_summaries.get_by_conversation(
                task.conversation_id,
                for_update=True,
            )
            if summary is None:
                summary = ConversationSummary(
                    id=uuid4(),
                    conversation_id=task.conversation_id,
                    content=safe_summary,
                    covered_through_message_id=last.id,
                    covered_through_created_at=last.created_at,
                    source_message_count=len(messages),
                    estimated_tokens=max(len(safe_summary) // 4, 1),
                    provider=response.provider,
                    model=response.model,
                    summary_metadata={},
                )
                await uow.conversation_summaries.add(summary)
            else:
                summary.content = safe_summary
                summary.covered_through_message_id = last.id
                summary.covered_through_created_at = last.created_at
                summary.source_message_count += len(messages)
                summary.estimated_tokens = max(len(safe_summary) // 4, 1)
                summary.provider = response.provider
                summary.model = response.model

            for extracted, embedding in zip(safe_items, embeddings, strict=True):
                if extracted.scope == MemoryScope.CHARACTER and character_id is None:
                    continue
                conversation_id = (
                    task.conversation_id
                    if extracted.scope
                    in {
                        MemoryScope.RELATIONSHIP,
                        MemoryScope.WORLD,
                        MemoryScope.CONVERSATION,
                    }
                    else None
                )
                scoped_character_id = (
                    character_id if extracted.scope == MemoryScope.CHARACTER else None
                )
                normalized_key = self._sanitizer.normalize_key(
                    extracted.normalized_key
                )
                existing = await uow.memories.find_active_by_key(
                    user_id,
                    scope=extracted.scope,
                    normalized_key=normalized_key,
                    conversation_id=conversation_id,
                    character_id=scoped_character_id,
                    persona_id=persona_id,
                    for_update=True,
                )
                if existing is None:
                    memory = Memory(
                        id=uuid4(),
                        user_id=user_id,
                        conversation_id=conversation_id,
                        character_id=scoped_character_id,
                        persona_id=persona_id,
                        source_message_id=last.id,
                        scope=extracted.scope,
                        kind=extracted.kind,
                        status=MemoryStatus.ACTIVE,
                        normalized_key=normalized_key,
                        content=extracted.content,
                        importance=extracted.importance,
                        confidence=extracted.confidence,
                        embedding=embedding,
                        access_count=0,
                        memory_metadata={"source": "automatic"},
                    )
                    await uow.memories.add(memory)
                else:
                    existing.kind = extracted.kind
                    existing.content = extracted.content
                    existing.importance = extracted.importance
                    existing.confidence = extracted.confidence
                    existing.embedding = embedding
                    existing.source_message_id = last.id
            task.status = MemoryTaskStatus.COMPLETED
            task.finished_at = datetime.now(UTC)
            task.locked_at = None
            task.last_error = None
            task.task_metadata = {
                **task.task_metadata,
                "extracted_memories": len(safe_items),
                "provider": response.provider,
                "model": response.model,
            }
            await uow.commit()

    async def mark_failure(self, task_id: UUID, exc: BaseException) -> None:
        async with self._uow_factory() as uow:
            task = await uow.memory_tasks.get_by_id(task_id, for_update=True)
            if task is None:
                return
            task.last_error = str(exc)[:4000]
            task.locked_at = None
            if task.attempts >= self._config.memory_worker_max_attempts:
                task.status = MemoryTaskStatus.FAILED
                task.finished_at = datetime.now(UTC)
            else:
                task.status = MemoryTaskStatus.PENDING
                delay = self._config.memory_worker_retry_base_seconds * (
                    2 ** max(task.attempts - 1, 0)
                )
                task.available_at = datetime.now(UTC) + timedelta(seconds=delay)
            await uow.commit()
