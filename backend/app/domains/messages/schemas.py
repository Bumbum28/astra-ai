from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.messages.model import (
    MessageContentType,
    MessageRole,
    MessageStatus,
)


class MessageSendRequest(BaseModel):
    content: str = Field(min_length=1)
    client_message_id: UUID
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32768)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message content cannot be blank.")
        return normalized


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    conversation_id: UUID
    parent_message_id: UUID | None
    client_message_id: UUID | None
    role: MessageRole
    content: str
    content_type: MessageContentType
    status: MessageStatus
    provider_message_id: str | None
    token_usage: dict[str, Any] | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="message_metadata",
    )
    created_at: datetime
    updated_at: datetime


class MessagePageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[MessageResponse]
    next_cursor: str | None = None


class ChatExchangeResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_message: MessageResponse
    assistant_message: MessageResponse
    reused: bool = False
