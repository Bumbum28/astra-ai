from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.llm.contracts.message import LLMMessage
from app.llm.contracts.tool import LLMToolDefinition


class LLMRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    messages: list[LLMMessage] = Field(min_length=1)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    tools: list[LLMToolDefinition] = Field(default_factory=list)
    tool_choice: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
