"""Add chat lifecycle, pagination, and idempotency fields.

Revision ID: 20260722_0002
Revises: 20260718_0001
Create Date: 2026-07-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0002"
down_revision: str | None = "20260718_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_conversations_last_message_at"),
        "conversations",
        ["last_message_at"],
    )
    op.create_index(
        op.f("ix_conversations_archived_at"),
        "conversations",
        ["archived_at"],
    )
    op.create_index(
        "ix_conversations_user_activity",
        "conversations",
        ["user_id", sa.text("COALESCE(last_message_at, created_at)"), "id"],
    )

    op.add_column(
        "messages", sa.Column("parent_message_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "messages", sa.Column("client_message_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_messages_parent_message_id_messages"),
        "messages",
        "messages",
        ["parent_message_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_messages_parent_message_id"),
        "messages",
        ["parent_message_id"],
    )
    op.create_index(
        op.f("ix_messages_client_message_id"),
        "messages",
        ["client_message_id"],
    )
    op.create_index(
        "uq_messages_conversation_client_message_id",
        "messages",
        ["conversation_id", "client_message_id"],
        unique=True,
        postgresql_where=sa.text("client_message_id IS NOT NULL"),
    )
    op.create_index(
        "ix_messages_conversation_timeline",
        "messages",
        ["conversation_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_timeline", table_name="messages")
    op.drop_index(
        "uq_messages_conversation_client_message_id", table_name="messages"
    )
    op.drop_index(op.f("ix_messages_client_message_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_parent_message_id"), table_name="messages")
    op.drop_constraint(
        op.f("fk_messages_parent_message_id_messages"),
        "messages",
        type_="foreignkey",
    )
    op.drop_column("messages", "client_message_id")
    op.drop_column("messages", "parent_message_id")

    op.drop_index("ix_conversations_user_activity", table_name="conversations")
    op.drop_index(op.f("ix_conversations_archived_at"), table_name="conversations")
    op.drop_index(
        op.f("ix_conversations_last_message_at"), table_name="conversations"
    )
    op.drop_column("conversations", "archived_at")
    op.drop_column("conversations", "last_message_at")
