from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.memories.model import MemoryKind, MemoryScope


class MemoryCreateRequest(BaseModel):
    scope: MemoryScope
    kind: MemoryKind = MemoryKind.FACT
    content: str = Field(min_length=1, max_length=12000)
    importance: float = Field(default=0.5, ge=0, le=1)
    conversation_id: UUID | None = None
    character_id: UUID | None = None
    source_message_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scope_target(self) -> "MemoryCreateRequest":
        if self.scope == MemoryScope.CHARACTER and self.character_id is None:
            raise ValueError("character_id is required for character memories")
        if self.scope == MemoryScope.CONVERSATION and self.conversation_id is None:
            raise ValueError("conversation_id is required for conversation memories")
        return self


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    scope: MemoryScope
    kind: MemoryKind
    content: str
    importance: float
    conversation_id: UUID | None
    character_id: UUID | None
    source_message_id: UUID | None
    archived_at: datetime | None
    last_accessed_at: datetime | None
    metadata: dict[str, Any] = Field(
        default_factory=dict, validation_alias="memory_metadata"
    )
    created_at: datetime
    updated_at: datetime


class MemoryListResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[MemoryResponse]
