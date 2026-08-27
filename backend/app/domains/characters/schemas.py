from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CharacterCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    tagline: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=12000)
    personality: str | None = Field(default=None, max_length=12000)
    scenario: str | None = Field(default=None, max_length=12000)
    system_prompt: str | None = Field(default=None, max_length=20000)
    greeting: str | None = Field(default=None, max_length=12000)
    avatar_url: str | None = Field(default=None, max_length=2048)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "name",
        "tagline",
        "description",
        "personality",
        "scenario",
        "system_prompt",
        "greeting",
        "avatar_url",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CharacterUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    tagline: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=12000)
    personality: str | None = Field(default=None, max_length=12000)
    scenario: str | None = Field(default=None, max_length=12000)
    system_prompt: str | None = Field(default=None, max_length=20000)
    greeting: str | None = Field(default=None, max_length=12000)
    avatar_url: str | None = Field(default=None, max_length=2048)
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None

    @field_validator(
        "name",
        "tagline",
        "description",
        "personality",
        "scenario",
        "system_prompt",
        "greeting",
        "avatar_url",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CharacterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    name: str
    tagline: str | None
    description: str | None
    personality: str | None
    scenario: str | None
    system_prompt: str | None
    greeting: str | None
    avatar_url: str | None
    is_active: bool
    metadata: dict[str, Any] = Field(
        default_factory=dict, validation_alias="character_metadata"
    )
    created_at: datetime
    updated_at: datetime


class CharacterListResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[CharacterResponse]
