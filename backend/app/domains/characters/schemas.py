from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CharacterCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=4000)
    personality: str | None = Field(default=None, max_length=12000)
    speaking_style: str | None = Field(default=None, max_length=8000)
    scenario: str | None = Field(default=None, max_length=12000)
    greeting: str | None = Field(default=None, max_length=4000)
    system_instructions: str | None = Field(default=None, max_length=12000)
    avatar_url: str | None = Field(default=None, max_length=2048)
    provider: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=150)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32768)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Character name cannot be blank.")
        return normalized

    @field_validator(
        "summary",
        "personality",
        "speaking_style",
        "scenario",
        "greeting",
        "system_instructions",
        "avatar_url",
        "provider",
        "model",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CharacterUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=4000)
    personality: str | None = Field(default=None, max_length=12000)
    speaking_style: str | None = Field(default=None, max_length=8000)
    scenario: str | None = Field(default=None, max_length=12000)
    greeting: str | None = Field(default=None, max_length=4000)
    system_instructions: str | None = Field(default=None, max_length=12000)
    avatar_url: str | None = Field(default=None, max_length=2048)
    provider: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=150)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32768)

    @field_validator(
        "name",
        "summary",
        "personality",
        "speaking_style",
        "scenario",
        "greeting",
        "system_instructions",
        "avatar_url",
        "provider",
        "model",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CharacterResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    current_version: int
    name: str
    summary: str | None
    personality: str | None
    speaking_style: str | None
    scenario: str | None
    greeting: str | None
    system_instructions: str | None
    avatar_url: str | None
    provider: str | None
    model: str | None
    temperature: float | None
    max_tokens: int | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CharacterPageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[CharacterResponse]
    next_cursor: str | None = None
