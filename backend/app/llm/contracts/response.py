from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.llm.contracts.tool import LLMToolCall


class LLMUsage(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class LLMResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    usage: LLMUsage | None = None
    provider_response_id: str | None = None
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    provider_response_id: str | None = None
    usage: LLMUsage | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
