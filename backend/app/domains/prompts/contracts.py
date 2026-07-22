from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from app.llm.contracts import LLMMessage

if TYPE_CHECKING:
    from app.core.unit_of_work import UnitOfWork
    from app.domains.conversations.model import Conversation


@dataclass(frozen=True, slots=True)
class CharacterPromptProfile:
    name: str
    summary: str | None
    personality: str | None
    speaking_style: str | None
    scenario: str | None
    greeting: str | None
    system_instructions: str | None


@dataclass(frozen=True, slots=True)
class PersonaPromptProfile:
    name: str
    description: str | None
    pronouns: str | None
    background: str | None
    traits: str | None
    writing_style: str | None


@dataclass(frozen=True, slots=True)
class RelationshipPromptState:
    level: str
    affection_score: int
    status: str | None
    turn_count: int
    context: str | None


@dataclass(frozen=True, slots=True)
class RoleplayPromptContext:
    character: CharacterPromptProfile | None = None
    persona: PersonaPromptProfile | None = None
    relationship: RelationshipPromptState | None = None


class PromptContextResolver(Protocol):
    async def resolve(
        self,
        uow: UnitOfWork,
        conversation: Conversation,
    ) -> RoleplayPromptContext: ...


class PromptComposer(Protocol):
    def compose(
        self,
        context: RoleplayPromptContext,
        conversation_system_prompt: str | None,
        latest_user_message: str | None = None,
    ) -> list[LLMMessage]: ...
