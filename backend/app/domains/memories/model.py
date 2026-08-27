from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseEntity


def _enum_values(enum_type: type[StrEnum]) -> list[str]:
    """Persist StrEnum values rather than Python member names."""
    return [member.value for member in enum_type]


class MemoryScope(StrEnum):
    USER = "user"
    CHARACTER = "character"
    CONVERSATION = "conversation"


class MemoryKind(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"
    RELATIONSHIP = "relationship"
    SUMMARY = "summary"
    NOTE = "note"


class Memory(BaseEntity):
    __tablename__ = "memories"
    __table_args__ = (
        Index("ix_memories_user_scope_importance", "user_id", "scope", "importance"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    character_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scope: Mapped[MemoryScope] = mapped_column(
        Enum(
            MemoryScope,
            native_enum=False,
            values_callable=_enum_values,
            validate_strings=True,
            length=32,
        ), index=True
    )
    kind: Mapped[MemoryKind] = mapped_column(
        Enum(
            MemoryKind,
            native_enum=False,
            values_callable=_enum_values,
            validate_strings=True,
            length=32,
        ), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    memory_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
