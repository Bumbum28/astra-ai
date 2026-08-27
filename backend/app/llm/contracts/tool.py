from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    input_schema: dict[str, Any]


class LLMToolCall(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
