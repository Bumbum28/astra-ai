from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonaCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=8000)
    pronouns: str | None = Field(default=None, max_length=120)
    background: str | None = Field(default=None, max_length=12000)
    traits: str | None = Field(default=None, max_length=8000)
    writing_style: str | None = Field(default=None, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Persona name cannot be blank.")
        return normalized

    @field_validator(
        "description", "pronouns", "background", "traits", "writing_style"
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PersonaUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=8000)
    pronouns: str | None = Field(default=None, max_length=120)
    background: str | None = Field(default=None, max_length=12000)
    traits: str | None = Field(default=None, max_length=8000)
    writing_style: str | None = Field(default=None, max_length=8000)

    @field_validator(
        "name", "description", "pronouns", "background", "traits", "writing_style"
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PersonaResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    current_version: int
    name: str
    description: str | None
    pronouns: str | None
    background: str | None
    traits: str | None
    writing_style: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PersonaPageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[PersonaResponse]
    next_cursor: str | None = None
