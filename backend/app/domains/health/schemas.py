from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DependencyHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["up", "down"]
    latency_ms: float = Field(ge=0)
    detail: str | None = None


class LivenessResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ready", "not_ready"]
    service: str
    version: str
    timestamp: datetime
    checks: dict[str, DependencyHealth]
