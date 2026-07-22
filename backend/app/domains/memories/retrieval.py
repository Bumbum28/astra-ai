import math
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWork
from app.domains.conversations.model import Conversation
from app.domains.memories.model import Memory
from app.domains.prompts.contracts import MemoryPromptItem, MemoryPromptState


@dataclass(frozen=True, slots=True)
class RankedMemory:
    memory: Memory
    score: float


class MemoryRetrievalService:
    """Hybrid lexical/vector ranking over a bounded PostgreSQL candidate set."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    async def retrieve(
        self,
        uow: UnitOfWork,
        conversation: Conversation,
        user_id: UUID,
        latest_user_message: str,
        query_embedding: list[float] | None,
    ) -> MemoryPromptState:
        if not self._config.memory_enabled:
            return MemoryPromptState()

        summary = await uow.conversation_summaries.get_by_conversation(
            conversation.id
        )
        candidates = list(
            await uow.memories.list_context_candidates(
                user_id,
                conversation_id=conversation.id,
                character_id=conversation.character_id,
                persona_id=conversation.persona_id,
                query_text=latest_user_message,
                limit=self._config.memory_retrieval_candidate_limit,
            )
        )
        ranked = self._rank(candidates, query_embedding)
        selected = ranked[: self._config.memory_retrieval_limit]
        await uow.memories.touch_accessed([item.memory.id for item in selected])
        return MemoryPromptState(
            conversation_summary=summary.content if summary is not None else None,
            items=tuple(
                MemoryPromptItem(
                    scope=item.memory.scope.value,
                    kind=item.memory.kind.value,
                    content=item.memory.content,
                    importance=item.memory.importance,
                    confidence=item.memory.confidence,
                )
                for item in selected
            ),
        )

    def _rank(
        self,
        candidates: list[Memory],
        query_embedding: list[float] | None,
    ) -> list[RankedMemory]:
        now = datetime.now(UTC)
        ranked: list[RankedMemory] = []
        for lexical_rank, memory in enumerate(candidates, start=1):
            lexical_score = 1.0 / (20.0 + lexical_rank)
            semantic_score = self._cosine(query_embedding, memory.embedding)
            age_days = max((now - memory.updated_at).total_seconds() / 86400, 0)
            recency = 1.0 / (1.0 + age_days / 30.0)
            access = min(math.log1p(memory.access_count) / 5.0, 1.0)
            score = (
                semantic_score * 0.55
                + lexical_score * 4.0 * 0.15
                + memory.importance * 0.15
                + memory.confidence * 0.08
                + recency * 0.05
                + access * 0.02
            )
            ranked.append(RankedMemory(memory=memory, score=score))
        ranked.sort(key=lambda item: (item.score, item.memory.updated_at), reverse=True)
        return ranked

    @staticmethod
    def _cosine(left: list[float] | None, right: list[float] | None) -> float:
        if left is None or right is None or len(left) != len(right) or not left:
            return 0.0
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return max(min(dot / (left_norm * right_norm), 1.0), -1.0)
