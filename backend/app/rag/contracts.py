from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RetrievalQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=50)
    source_ids: tuple[UUID, ...] = ()


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: UUID
    chunk_id: UUID
    content: str
    score: float = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
