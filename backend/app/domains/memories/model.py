from datetime import datetime
from enum import Enum as PythonEnum
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseEntity


def _enum_values(enum_type: type[PythonEnum]) -> list[str]:
    return [str(member.value) for member in enum_type]


class MemoryScope(StrEnum):
    USER = "user"
    CHARACTER = "character"
    RELATIONSHIP = "relationship"
    WORLD = "world"
    CONVERSATION = "conversation"


class MemoryKind(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"
    EVENT = "event"
    PROMISE = "promise"
    BOUNDARY = "boundary"
    GOAL = "goal"
    RELATIONSHIP = "relationship"
    WORLD = "world"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class MemoryTaskStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Memory(BaseEntity):
    __tablename__ = "memories"
    __table_args__ = (
        CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name="ck_memories_importance_range",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_memories_confidence_range",
        ),
        Index("ix_memories_user_status_updated", "user_id", "status", "updated_at"),
        Index(
            "ix_memories_context_scope",
            "user_id",
            "scope",
            "conversation_id",
            "character_id",
        ),
        Index(
            "uq_memories_active_identity",
            "user_id",
            "scope",
            "normalized_key",
            "conversation_id",
            "character_id",
            "persona_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            postgresql_nulls_not_distinct=True,
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    character_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=True, index=True
    )
    persona_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("personas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    superseded_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("memories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scope: Mapped[MemoryScope] = mapped_column(
        Enum(
            MemoryScope,
            native_enum=False,
            length=20,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        index=True,
    )
    kind: Mapped[MemoryKind] = mapped_column(
        Enum(
            MemoryKind,
            native_enum=False,
            length=24,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        index=True,
    )
    status: Mapped[MemoryStatus] = mapped_column(
        Enum(
            MemoryStatus,
            native_enum=False,
            length=20,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        default=MemoryStatus.ACTIVE,
        index=True,
    )
    normalized_key: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    memory_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )


class ConversationSummary(BaseEntity):
    __tablename__ = "conversation_summaries"

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), unique=True, index=True
    )
    content: Mapped[str] = mapped_column(Text)
    covered_through_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    covered_through_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    source_message_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_tokens: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    summary_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )


class MemoryTask(BaseEntity):
    __tablename__ = "memory_tasks"
    __table_args__ = (
        Index("ix_memory_tasks_claim", "status", "available_at", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    trigger_message_id: Mapped[UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), unique=True, index=True
    )
    status: Mapped[MemoryTaskStatus] = mapped_column(
        Enum(
            MemoryTaskStatus,
            native_enum=False,
            length=20,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        default=MemoryTaskStatus.PENDING,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
