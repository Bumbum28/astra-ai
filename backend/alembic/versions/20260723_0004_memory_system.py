"""Add persistent conversation summaries, long-term memories, and worker tasks.

Revision ID: 20260723_0004
Revises: 20260722_0003
Create Date: 2026-07-23
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0004"
down_revision: str | None = "20260722_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("character_id", sa.Uuid(), nullable=True),
        sa.Column("persona_id", sa.Uuid(), nullable=True),
        sa.Column("source_message_id", sa.Uuid(), nullable=True),
        sa.Column("superseded_by_id", sa.Uuid(), nullable=True),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("normalized_key", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "embedding",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.CheckConstraint(
            "scope IN ('user','character','relationship','world','conversation')",
            name=op.f("ck_memories_scope_values"),
        ),
        sa.CheckConstraint(
            "kind IN ('fact','preference','event','promise',"
            "'boundary','goal','relationship','world')",
            name=op.f("ck_memories_kind_values"),
        ),
        sa.CheckConstraint(
            "status IN ('active','superseded','archived')",
            name=op.f("ck_memories_status_values"),
        ),
        sa.CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name=op.f("ck_memories_importance_range"),
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name=op.f("ck_memories_confidence_range"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_memories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_memories_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            name=op.f("fk_memories_character_id_characters"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["persona_id"],
            ["personas.id"],
            name=op.f("fk_memories_persona_id_personas"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["messages.id"],
            name=op.f("fk_memories_source_message_id_messages"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"],
            ["memories.id"],
            name=op.f("fk_memories_superseded_by_id_memories"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memories")),
    )
    for column in (
        "user_id",
        "conversation_id",
        "character_id",
        "persona_id",
        "source_message_id",
        "superseded_by_id",
        "scope",
        "kind",
        "status",
        "normalized_key",
        "expires_at",
    ):
        op.create_index(op.f(f"ix_memories_{column}"), "memories", [column])
    op.create_index(
        "ix_memories_user_status_updated",
        "memories",
        ["user_id", "status", "updated_at"],
    )
    op.create_index(
        "ix_memories_context_scope",
        "memories",
        ["user_id", "scope", "conversation_id", "character_id"],
    )
    op.create_index(
        "uq_memories_active_identity",
        "memories",
        [
            "user_id",
            "scope",
            "normalized_key",
            "conversation_id",
            "character_id",
            "persona_id",
        ],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        postgresql_nulls_not_distinct=True,
    )
    op.execute(
        "CREATE INDEX ix_memories_content_fts ON memories USING gin "
        "(to_tsvector('simple', content))"
    )

    op.create_table(
        "conversation_summaries",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("covered_through_message_id", sa.Uuid(), nullable=True),
        sa.Column(
            "covered_through_created_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("source_message_count", sa.Integer(), nullable=False),
        sa.Column("estimated_tokens", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("model", sa.String(length=150), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f(
                "fk_conversation_summaries_conversation_id_conversations"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["covered_through_message_id"],
            ["messages.id"],
            name=op.f(
                "fk_conversation_summaries_covered_through_message_id_messages"
            ),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_summaries")),
        sa.UniqueConstraint(
            "conversation_id",
            name=op.f("uq_conversation_summaries_conversation_id"),
        ),
    )
    op.create_index(
        op.f("ix_conversation_summaries_conversation_id"),
        "conversation_summaries",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_conversation_summaries_covered_through_created_at"),
        "conversation_summaries",
        ["covered_through_created_at"],
    )

    op.create_table(
        "memory_tasks",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("trigger_message_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending','processing','completed','failed')",
            name=op.f("ck_memory_tasks_status_values"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_memory_tasks_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trigger_message_id"],
            ["messages.id"],
            name=op.f("fk_memory_tasks_trigger_message_id_messages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_tasks")),
        sa.UniqueConstraint(
            "trigger_message_id", name=op.f("uq_memory_tasks_trigger_message_id")
        ),
    )
    for column in (
        "conversation_id",
        "trigger_message_id",
        "status",
        "available_at",
    ):
        op.create_index(op.f(f"ix_memory_tasks_{column}"), "memory_tasks", [column])
    op.create_index(
        "ix_memory_tasks_claim",
        "memory_tasks",
        ["status", "available_at", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_memory_tasks_claim", table_name="memory_tasks")
    for column in reversed(
        ("conversation_id", "trigger_message_id", "status", "available_at")
    ):
        op.drop_index(op.f(f"ix_memory_tasks_{column}"), table_name="memory_tasks")
    op.drop_table("memory_tasks")

    op.drop_index(
        op.f("ix_conversation_summaries_covered_through_created_at"),
        table_name="conversation_summaries",
    )
    op.drop_index(
        op.f("ix_conversation_summaries_conversation_id"),
        table_name="conversation_summaries",
    )
    op.drop_table("conversation_summaries")

    op.execute("DROP INDEX IF EXISTS ix_memories_content_fts")
    op.drop_index("uq_memories_active_identity", table_name="memories")
    op.drop_index("ix_memories_context_scope", table_name="memories")
    op.drop_index("ix_memories_user_status_updated", table_name="memories")
    for column in reversed(
        (
            "user_id",
            "conversation_id",
            "character_id",
            "persona_id",
            "source_message_id",
            "superseded_by_id",
            "scope",
            "kind",
            "status",
            "normalized_key",
            "expires_at",
        )
    ):
        op.drop_index(op.f(f"ix_memories_{column}"), table_name="memories")
    op.drop_table("memories")
