"""Add Character, Persona, Memory and conversation context references.

Revision ID: 20260729_0003
Revises: 20260722_0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260729_0003"
down_revision: str | None = "20260722_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "characters",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("tagline", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("scenario", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("greeting", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(length=2048), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_characters_user_id", "characters", ["user_id"])
    op.create_index("ix_characters_name", "characters", ["name"])

    op.create_table(
        "personas",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personas_user_id", "personas", ["user_id"])
    op.create_index("ix_personas_name", "personas", ["name"])
    op.create_index("ix_personas_is_default", "personas", ["is_default"])

    op.add_column("conversations", sa.Column("character_id", sa.Uuid(), nullable=True))
    op.add_column("conversations", sa.Column("persona_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_conversations_character_id_characters", "conversations", "characters", ["character_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_conversations_persona_id_personas", "conversations", "personas", ["persona_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_conversations_character_id", "conversations", ["character_id"])
    op.create_index("ix_conversations_persona_id", "conversations", ["persona_id"])

    op.create_table(
        "memories",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("character_id", sa.Uuid(), nullable=True),
        sa.Column("source_message_id", sa.Uuid(), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memories_user_id", "memories", ["user_id"])
    op.create_index("ix_memories_conversation_id", "memories", ["conversation_id"])
    op.create_index("ix_memories_character_id", "memories", ["character_id"])
    op.create_index("ix_memories_source_message_id", "memories", ["source_message_id"])
    op.create_index("ix_memories_scope", "memories", ["scope"])
    op.create_index("ix_memories_kind", "memories", ["kind"])
    op.create_index("ix_memories_archived_at", "memories", ["archived_at"])
    op.create_index("ix_memories_user_scope_importance", "memories", ["user_id", "scope", "importance"])


def downgrade() -> None:
    op.drop_index("ix_memories_user_scope_importance", table_name="memories")
    op.drop_index("ix_memories_archived_at", table_name="memories")
    op.drop_index("ix_memories_kind", table_name="memories")
    op.drop_index("ix_memories_scope", table_name="memories")
    op.drop_index("ix_memories_source_message_id", table_name="memories")
    op.drop_index("ix_memories_character_id", table_name="memories")
    op.drop_index("ix_memories_conversation_id", table_name="memories")
    op.drop_index("ix_memories_user_id", table_name="memories")
    op.drop_table("memories")
    op.drop_index("ix_conversations_persona_id", table_name="conversations")
    op.drop_index("ix_conversations_character_id", table_name="conversations")
    op.drop_constraint("fk_conversations_persona_id_personas", "conversations", type_="foreignkey")
    op.drop_constraint("fk_conversations_character_id_characters", "conversations", type_="foreignkey")
    op.drop_column("conversations", "persona_id")
    op.drop_column("conversations", "character_id")
    op.drop_index("ix_personas_is_default", table_name="personas")
    op.drop_index("ix_personas_name", table_name="personas")
    op.drop_index("ix_personas_user_id", table_name="personas")
    op.drop_table("personas")
    op.drop_index("ix_characters_name", table_name="characters")
    op.drop_index("ix_characters_user_id", table_name="characters")
    op.drop_table("characters")
