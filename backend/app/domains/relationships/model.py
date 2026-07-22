from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseEntity


class RelationshipLevel(StrEnum):
    L0 = "l0"
    L1 = "l1"
    L2 = "l2"
    L3 = "l3"
    L4 = "l4"
    L5 = "l5"
    L6 = "l6"


class Relationship(BaseEntity):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("conversation_id", name="uq_relationships_conversation_id"),
        CheckConstraint(
            "affection_score >= -100 AND affection_score <= 100",
            name="ck_relationships_affection_score_range",
        ),
        CheckConstraint(
            "turn_count >= 0",
            name="ck_relationships_turn_count_non_negative",
        ),
        CheckConstraint(
            "level IN ('l0','l1','l2','l3','l4','l5','l6')",
            name="ck_relationships_level_values",
        ),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    character_id: Mapped[UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[str] = mapped_column(String(20), default=RelationshipLevel.L0.value)
    affection_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    turn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    relationship_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )


class RelationshipEvent(BaseEntity):
    __tablename__ = "relationship_events"

    relationship_id: Mapped[UUID] = mapped_column(
        ForeignKey("relationships.id", ondelete="CASCADE"), index=True
    )
    source_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    previous_level: Mapped[str] = mapped_column(String(20), nullable=False)
    new_level: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_score: Mapped[int] = mapped_column(Integer, nullable=False)
    new_score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
