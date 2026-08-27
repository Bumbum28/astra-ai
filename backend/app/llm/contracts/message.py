from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.llm.contracts.tool import LLMToolCall


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
    tool_call_id: str | None = None
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
