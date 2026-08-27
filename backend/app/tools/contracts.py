from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    input_schema: dict[str, Any]


class ToolContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    conversation_id: UUID | None = None
    allowed_tools: frozenset[str] | None = None


class ToolExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    tool_name: str
    content: str
    data: dict[str, Any] = Field(default_factory=dict)
