from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: LLMMessageRole
    content: str
    name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
