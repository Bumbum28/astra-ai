from enum import Enum as PythonEnum
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseEntity

if TYPE_CHECKING:
    from app.domains.conversations.model import Conversation


def _enum_values(enum_type: type[PythonEnum]) -> list[str]:
    """Persist enum values instead of Python member names."""
    return [str(member.value) for member in enum_type]


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MessageContentType(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"


class MessageStatus(StrEnum):
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


class Message(BaseEntity):
    __tablename__ = "messages"
    __table_args__ = (
        Index(
            "uq_messages_conversation_client_message_id",
            "conversation_id",
            "client_message_id",
            unique=True,
            postgresql_where=text("client_message_id IS NOT NULL"),
        ),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    parent_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    client_message_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            native_enum=False,
            length=20,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[MessageContentType] = mapped_column(
        Enum(
            MessageContentType,
            native_enum=False,
            length=20,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        default=MessageContentType.TEXT,
    )
    status: Mapped[MessageStatus] = mapped_column(
        Enum(
            MessageStatus,
            native_enum=False,
            length=20,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        default=MessageStatus.COMPLETED,
        index=True,
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    message_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    parent: Mapped["Message | None"] = relationship(
        remote_side="Message.id", foreign_keys=[parent_message_id]
    )
