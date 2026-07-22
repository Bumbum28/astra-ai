from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=150)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32768)
    character_id: UUID | None = None
    persona_id: UUID | None = None
    system_prompt: str | None = Field(default=None, max_length=20000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "provider", "model", "system_prompt")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ConversationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=150)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32768)
    character_id: UUID | None = None
    persona_id: UUID | None = None
    system_prompt: str | None = Field(default=None, max_length=20000)

    @field_validator("title", "provider", "model", "system_prompt")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    title: str | None
    character_id: UUID | None
    character_version_id: UUID | None
    persona_id: UUID | None
    persona_version_id: UUID | None
    provider: str | None
    model: str | None
    temperature: float | None
    max_tokens: int | None
    system_prompt: str | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="conversation_metadata",
    )
    last_message_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ConversationPageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[ConversationResponse]
    next_cursor: str | None = None
