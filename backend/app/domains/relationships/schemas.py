from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.relationships.model import RelationshipLevel


class RelationshipUpdateRequest(BaseModel):
    level: RelationshipLevel | None = None
    affection_score: int | None = Field(default=None, ge=-100, le=100)
    status: str | None = Field(default=None, max_length=120)
    context: str | None = Field(default=None, max_length=8000)
    reason: str = Field(min_length=1, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Relationship change reason cannot be blank.")
        return normalized

    @field_validator("status", "context")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    conversation_id: UUID
    character_id: UUID
    level: RelationshipLevel
    affection_score: int
    status: str | None
    turn_count: int
    context: str | None
    last_change_reason: str | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="relationship_metadata",
    )
    created_at: datetime
    updated_at: datetime


class RelationshipEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    relationship_id: UUID
    source_message_id: UUID | None
    previous_level: RelationshipLevel
    new_level: RelationshipLevel
    previous_score: int
    new_score: int
    score_delta: int
    reason: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="event_metadata",
    )
    created_at: datetime


class RelationshipHistoryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[RelationshipEventResponse]
