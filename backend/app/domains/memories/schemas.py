from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.memories.model import MemoryKind, MemoryScope, MemoryStatus


class MemoryCreateRequest(BaseModel):
    scope: MemoryScope
    kind: MemoryKind
    content: str = Field(min_length=1, max_length=4000)
    normalized_key: str | None = Field(default=None, max_length=255)
    conversation_id: UUID | None = None
    character_id: UUID | None = None
    persona_id: UUID | None = None
    importance: float = Field(default=0.7, ge=0, le=1)
    confidence: float = Field(default=1.0, ge=0, le=1)
    expires_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


class MemoryUpdateRequest(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=4000)
    importance: float | None = Field(default=None, ge=0, le=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    expires_at: datetime | None = None
    status: MemoryStatus | None = None


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    conversation_id: UUID | None
    character_id: UUID | None
    persona_id: UUID | None
    source_message_id: UUID | None
    scope: MemoryScope
    kind: MemoryKind
    status: MemoryStatus
    normalized_key: str
    content: str
    importance: float
    confidence: float
    last_accessed_at: datetime | None
    access_count: int
    expires_at: datetime | None
    metadata: dict[str, Any] = Field(validation_alias="memory_metadata")
    created_at: datetime
    updated_at: datetime


class MemoryPage(BaseModel):
    items: list[MemoryResponse]
    next_cursor: str | None = None


class ConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    content: str
    covered_through_message_id: UUID | None
    covered_through_created_at: datetime | None
    source_message_count: int
    estimated_tokens: int
    provider: str | None
    model: str | None
    updated_at: datetime


class ConversationMemorySnapshot(BaseModel):
    summary: ConversationSummaryResponse | None
    memories: list[MemoryResponse]
    pending_tasks: int = 0


class MemoryRefreshResponse(BaseModel):
    queued: bool
    task_id: UUID | None = None


class ExtractedMemory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: MemoryScope
    kind: MemoryKind
    normalized_key: str = Field(min_length=2, max_length=255)
    content: str = Field(min_length=2, max_length=1200)
    importance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class MemoryExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=8000)
    memories: list[ExtractedMemory] = Field(max_length=16)
