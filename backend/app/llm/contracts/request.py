from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.contracts.message import LLMMessage

ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh", "max"]


class LLMRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    messages: list[LLMMessage] = Field(min_length=1)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    reasoning_effort: ReasoningEffort | None = None
    response_schema_name: str | None = Field(default=None, min_length=1, max_length=64)
    response_schema: dict[str, Any] | None = None
    store: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
