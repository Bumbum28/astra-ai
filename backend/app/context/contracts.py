from dataclasses import dataclass
from uuid import UUID

from app.domains.conversations.model import Conversation
from app.domains.messages.model import Message
from app.llm.contracts import LLMMessage


@dataclass(frozen=True, slots=True)
class ContextAssemblyRequest:
    user_id: UUID
    conversation: Conversation
    history: list[Message]


@dataclass(frozen=True, slots=True)
class AssembledContext:
    messages: list[LLMMessage]
    character_id: UUID | None
    persona_id: UUID | None
    memory_ids: tuple[UUID, ...]
