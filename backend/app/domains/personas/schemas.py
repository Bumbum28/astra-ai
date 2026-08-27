from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonaCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=12000)
    instructions: str | None = Field(default=None, max_length=12000)
    is_default: bool = False
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "description", "instructions")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PersonaUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=12000)
    instructions: str | None = Field(default=None, max_length=12000)
    is_default: bool | None = None
    attributes: dict[str, Any] | None = None

    @field_validator("name", "description", "instructions")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PersonaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    name: str
    description: str | None
    instructions: str | None
    is_default: bool
    attributes: dict[str, Any] = Field(
        default_factory=dict, validation_alias="persona_attributes"
    )
    created_at: datetime
    updated_at: datetime


class PersonaListResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[PersonaResponse]
