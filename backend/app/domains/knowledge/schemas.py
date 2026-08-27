from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.knowledge.model import KnowledgeSourceStatus, KnowledgeSourceType


class KnowledgeSourceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=2_000_000)
    source_type: KnowledgeSourceType = KnowledgeSourceType.TEXT
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "content")
    @classmethod
    def strip_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value cannot be blank")
        return normalized


class KnowledgeSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    name: str
    source_type: KnowledgeSourceType
    status: KnowledgeSourceStatus
    metadata: dict[str, Any] = Field(
        default_factory=dict, validation_alias="source_metadata"
    )
    created_at: datetime
    updated_at: datetime


class KnowledgeSourceListResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[KnowledgeSourceResponse]


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=50)
    source_ids: list[UUID] = Field(default_factory=list)


class KnowledgeSearchHit(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: UUID
    chunk_id: UUID
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[KnowledgeSearchHit]
