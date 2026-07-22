"""Add versioned Character, Persona, Relationship, and prompt profile links.

Revision ID: 20260722_0003
Revises: 20260722_0002
Create Date: 2026-07-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260722_0003"
down_revision: str | None = "20260722_0002"
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
        "characters",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("avatar_url", sa.String(length=2048), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("model", sa.String(length=150), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_characters_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_characters")),
    )
    op.create_index(op.f("ix_characters_user_id"), "characters", ["user_id"])
    op.create_index(
        op.f("ix_characters_archived_at"), "characters", ["archived_at"]
    )
    op.create_index(
        "ix_characters_user_updated",
        "characters",
        ["user_id", "updated_at", "id"],
    )

    op.create_table(
        "character_versions",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("speaking_style", sa.Text(), nullable=True),
        sa.Column("scenario", sa.Text(), nullable=True),
        sa.Column("greeting", sa.Text(), nullable=True),
        sa.Column("system_instructions", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            name=op.f("fk_character_versions_character_id_characters"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_character_versions")),
        sa.UniqueConstraint(
            "character_id",
            "version",
            name="uq_character_versions_character_id_version",
        ),
    )
    op.create_index(
        op.f("ix_character_versions_character_id"),
        "character_versions",
        ["character_id"],
    )

    op.create_table(
        "personas",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_personas_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_personas")),
    )
    op.create_index(op.f("ix_personas_user_id"), "personas", ["user_id"])
    op.create_index(op.f("ix_personas_archived_at"), "personas", ["archived_at"])
    op.create_index(
        "ix_personas_user_updated",
        "personas",
        ["user_id", "updated_at", "id"],
    )

    op.create_table(
        "persona_versions",
        sa.Column("persona_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pronouns", sa.String(length=120), nullable=True),
        sa.Column("background", sa.Text(), nullable=True),
        sa.Column("traits", sa.Text(), nullable=True),
        sa.Column("writing_style", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["persona_id"],
            ["personas.id"],
            name=op.f("fk_persona_versions_persona_id_personas"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_persona_versions")),
        sa.UniqueConstraint(
            "persona_id",
            "version",
            name="uq_persona_versions_persona_id_version",
        ),
    )
    op.create_index(
        op.f("ix_persona_versions_persona_id"),
        "persona_versions",
        ["persona_id"],
    )

    for name, target in (
        ("character_id", "characters.id"),
        ("character_version_id", "character_versions.id"),
        ("persona_id", "personas.id"),
        ("persona_version_id", "persona_versions.id"),
    ):
        op.add_column("conversations", sa.Column(name, sa.Uuid(), nullable=True))
        op.create_foreign_key(
            op.f(f"fk_conversations_{name}_{target.split('.')[0]}"),
            "conversations",
            target.split(".")[0],
            [name],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(op.f(f"ix_conversations_{name}"), "conversations", [name])
    op.add_column("conversations", sa.Column("temperature", sa.Float(), nullable=True))
    op.add_column("conversations", sa.Column("max_tokens", sa.Integer(), nullable=True))

    op.create_table(
        "relationships",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("affection_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=120), nullable=True),
        sa.Column("turn_count", sa.Integer(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("last_change_reason", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.CheckConstraint(
            "affection_score >= -100 AND affection_score <= 100",
            name=op.f("ck_relationships_affection_score_range"),
        ),
        sa.CheckConstraint(
            "turn_count >= 0",
            name=op.f("ck_relationships_turn_count_non_negative"),
        ),
        sa.CheckConstraint(
            "level IN ('l0','l1','l2','l3','l4','l5','l6')",
            name=op.f("ck_relationships_level_values"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_relationships_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_relationships_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            name=op.f("fk_relationships_character_id_characters"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_relationships")),
        sa.UniqueConstraint(
            "conversation_id", name="uq_relationships_conversation_id"
        ),
    )
    op.create_index(
        op.f("ix_relationships_conversation_id"),
        "relationships",
        ["conversation_id"],
    )
    op.create_index(op.f("ix_relationships_user_id"), "relationships", ["user_id"])
    op.create_index(
        op.f("ix_relationships_character_id"),
        "relationships",
        ["character_id"],
    )

    op.create_table(
        "relationship_events",
        sa.Column("relationship_id", sa.Uuid(), nullable=False),
        sa.Column("source_message_id", sa.Uuid(), nullable=True),
        sa.Column("previous_level", sa.String(length=20), nullable=False),
        sa.Column("new_level", sa.String(length=20), nullable=False),
        sa.Column("previous_score", sa.Integer(), nullable=False),
        sa.Column("new_score", sa.Integer(), nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["relationships.id"],
            name=op.f("fk_relationship_events_relationship_id_relationships"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["messages.id"],
            name=op.f("fk_relationship_events_source_message_id_messages"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_relationship_events")),
    )
    op.create_index(
        op.f("ix_relationship_events_relationship_id"),
        "relationship_events",
        ["relationship_id"],
    )
    op.create_index(
        op.f("ix_relationship_events_source_message_id"),
        "relationship_events",
        ["source_message_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_relationship_events_source_message_id"),
        table_name="relationship_events",
    )
    op.drop_index(
        op.f("ix_relationship_events_relationship_id"),
        table_name="relationship_events",
    )
    op.drop_table("relationship_events")

    op.drop_index(op.f("ix_relationships_character_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_user_id"), table_name="relationships")
    op.drop_index(
        op.f("ix_relationships_conversation_id"), table_name="relationships"
    )
    op.drop_table("relationships")

    op.drop_column("conversations", "max_tokens")
    op.drop_column("conversations", "temperature")
    for name, target in reversed(
        (
            ("character_id", "characters"),
            ("character_version_id", "character_versions"),
            ("persona_id", "personas"),
            ("persona_version_id", "persona_versions"),
        )
    ):
        op.drop_index(op.f(f"ix_conversations_{name}"), table_name="conversations")
        op.drop_constraint(
            op.f(f"fk_conversations_{name}_{target}"),
            "conversations",
            type_="foreignkey",
        )
        op.drop_column("conversations", name)

    op.drop_index(op.f("ix_persona_versions_persona_id"), table_name="persona_versions")
    op.drop_table("persona_versions")
    op.drop_index("ix_personas_user_updated", table_name="personas")
    op.drop_index(op.f("ix_personas_archived_at"), table_name="personas")
    op.drop_index(op.f("ix_personas_user_id"), table_name="personas")
    op.drop_table("personas")

    op.drop_index(
        op.f("ix_character_versions_character_id"), table_name="character_versions"
    )
    op.drop_table("character_versions")
    op.drop_index("ix_characters_user_updated", table_name="characters")
    op.drop_index(op.f("ix_characters_archived_at"), table_name="characters")
    op.drop_index(op.f("ix_characters_user_id"), table_name="characters")
    op.drop_table("characters")
