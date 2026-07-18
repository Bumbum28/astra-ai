from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMModelInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    provider: str
    display_name: str | None = None
    capabilities: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)
