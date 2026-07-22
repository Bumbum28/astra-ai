from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domains.messages.schemas import MessageResponse


class ChatStreamStarted(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_message: MessageResponse
    assistant_message: MessageResponse
    reused: bool = False


class ChatStreamDelta(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_id: UUID
    delta: str


class ChatStreamCompleted(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: MessageResponse


class ChatStreamError(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_id: UUID
    code: str
    message: str
    details: Any | None = None
