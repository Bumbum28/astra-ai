from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    user_id: UUID
    conversation_id: UUID
    user_message_id: UUID | None
    assistant_message_id: UUID | None
    provider: str
    model: str | None
    status: str
    allowed_tools: list[str] = Field(default_factory=list)
    step_count: int
    tool_call_count: int
    started_at: datetime
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="run_metadata",
    )
    created_at: datetime
    updated_at: datetime


class AgentStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    agent_run_id: UUID
    step_number: int
    kind: str
    status: str
    tool_call_id: str | None
    tool_name: str | None
    input: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="input_payload",
    )
    output: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="output_payload",
    )
    duration_ms: int | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class AgentRunListResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[AgentRunResponse]


class AgentStepListResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[AgentStepResponse]
