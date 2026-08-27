"""Bridge the legacy roleplay/memory schema to the revised Sprint 5 model.

Revision ID: 20260827_0005
Revises: 20260723_0004

This migration intentionally preserves the already-published 20260722_0003 and
20260723_0004 revisions.  It upgrades those tables in place instead of
rewriting Alembic history, so databases that already reached the legacy
20260723_0004 revision can continue safely.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260827_0005"
down_revision: str | None = "20260723_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # characters: project the active legacy version onto the revised
    # single-row Character model.  Legacy version tables are preserved so
    # no historical data is discarded.
    # ------------------------------------------------------------------
    op.add_column("characters", sa.Column("name", sa.String(length=120), nullable=True))
    op.add_column("characters", sa.Column("tagline", sa.String(length=255), nullable=True))
    op.add_column("characters", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("personality", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("scenario", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("system_prompt", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("greeting", sa.Text(), nullable=True))
    op.add_column(
        "characters",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    op.execute(
        """
        UPDATE characters AS c
        SET
            name = cv.name,
            tagline = LEFT(COALESCE(cv.summary, ''), 255),
            description = cv.summary,
            personality = cv.personality,
            scenario = cv.scenario,
            system_prompt = cv.system_instructions,
            greeting = cv.greeting,
            is_active = (c.archived_at IS NULL)
        FROM character_versions AS cv
        WHERE cv.character_id = c.id
          AND cv.version = c.current_version
        """
    )
    op.execute(
        "UPDATE characters SET name = 'Character' WHERE name IS NULL OR btrim(name) = ''"
    )
    op.alter_column("characters", "name", nullable=False)
    # Current ORM no longer writes current_version; keep the legacy column
    # usable for new rows without requiring a version-table insert.
    op.alter_column(
        "characters",
        "current_version",
        existing_type=sa.Integer(),
        server_default=sa.text("1"),
        existing_nullable=False,
    )
    op.create_index("ix_characters_name", "characters", ["name"])

    # ------------------------------------------------------------------
    # personas: same compatibility projection as characters.
    # ------------------------------------------------------------------
    op.add_column("personas", sa.Column("name", sa.String(length=120), nullable=True))
    op.add_column("personas", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("personas", sa.Column("instructions", sa.Text(), nullable=True))
    op.add_column(
        "personas",
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "personas",
        sa.Column(
            "attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE personas AS p
        SET
            name = pv.name,
            description = pv.description,
            instructions = NULLIF(
                concat_ws(
                    E'\\n\\n',
                    CASE WHEN pv.background IS NOT NULL AND btrim(pv.background) <> ''
                         THEN 'Background: ' || pv.background END,
                    CASE WHEN pv.traits IS NOT NULL AND btrim(pv.traits) <> ''
                         THEN 'Traits: ' || pv.traits END,
                    CASE WHEN pv.writing_style IS NOT NULL AND btrim(pv.writing_style) <> ''
                         THEN 'Writing style: ' || pv.writing_style END
                ),
                ''
            ),
            attributes = jsonb_strip_nulls(
                jsonb_build_object(
                    'pronouns', pv.pronouns,
                    'background', pv.background,
                    'traits', pv.traits,
                    'writing_style', pv.writing_style
                )
            )
        FROM persona_versions AS pv
        WHERE pv.persona_id = p.id
          AND pv.version = p.current_version
        """
    )
    op.execute(
        "UPDATE personas SET name = 'Persona' WHERE name IS NULL OR btrim(name) = ''"
    )
    op.alter_column("personas", "name", nullable=False)
    op.alter_column(
        "personas",
        "current_version",
        existing_type=sa.Integer(),
        server_default=sa.text("1"),
        existing_nullable=False,
    )
    op.create_index("ix_personas_name", "personas", ["name"])
    op.create_index("ix_personas_is_default", "personas", ["is_default"])

    # ------------------------------------------------------------------
    # memories: preserve legacy rows while relaxing columns that the revised
    # ORM no longer writes. Unsupported legacy enum-like values are mapped to
    # the revised vocabulary and the original value is retained in metadata.
    # ------------------------------------------------------------------
    op.add_column(
        "memories",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Drop legacy vocabulary constraints before normalizing values. PostgreSQL
    # validates CHECK constraints on every UPDATE, so changing a legacy kind
    # such as ``event`` to the revised ``note`` value while the old constraint
    # is still present would fail the migration.
    op.drop_constraint(op.f("ck_memories_scope_values"), "memories", type_="check")
    op.drop_constraint(op.f("ck_memories_kind_values"), "memories", type_="check")
    op.drop_constraint(op.f("ck_memories_status_values"), "memories", type_="check")

    op.execute(
        """
        UPDATE memories
        SET metadata = COALESCE(metadata, '{}'::jsonb)
                       || jsonb_build_object('legacy_scope', scope)
        WHERE scope IN ('relationship', 'world')
        """
    )
    op.execute(
        """
        UPDATE memories
        SET scope = CASE
            WHEN scope = 'relationship' AND character_id IS NOT NULL THEN 'character'
            WHEN scope IN ('relationship', 'world') THEN 'user'
            ELSE scope
        END
        WHERE scope IN ('relationship', 'world')
        """
    )
    op.execute(
        """
        UPDATE memories
        SET metadata = COALESCE(metadata, '{}'::jsonb)
                       || jsonb_build_object('legacy_kind', kind)
        WHERE kind IN ('event', 'promise', 'boundary', 'goal', 'world')
        """
    )
    op.execute(
        """
        UPDATE memories
        SET kind = 'note'
        WHERE kind IN ('event', 'promise', 'boundary', 'goal', 'world')
        """
    )
    op.execute(
        """
        UPDATE memories
        SET archived_at = COALESCE(
            archived_at,
            CASE
                WHEN status IN ('archived', 'superseded') THEN updated_at
                WHEN expires_at IS NOT NULL AND expires_at <= now() THEN expires_at
                ELSE NULL
            END
        )
        """
    )

    # The revised service does not populate these legacy bookkeeping fields.
    for column, type_ in (
        ("status", sa.String(length=20)),
        ("normalized_key", sa.String(length=255)),
        ("confidence", sa.Float()),
        ("access_count", sa.Integer()),
    ):
        op.alter_column(
            "memories",
            column,
            existing_type=type_,
            nullable=True,
            existing_nullable=False,
        )

    # The legacy uniqueness policy relies on status/normalized_key, neither of
    # which is part of the revised memory API.
    op.drop_index("uq_memories_active_identity", table_name="memories")

    # Match the revised on-delete semantics without discarding rows.
    op.drop_constraint(
        "fk_memories_conversation_id_conversations",
        "memories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_memories_conversation_id_conversations",
        "memories",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_memories_character_id_characters",
        "memories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_memories_character_id_characters",
        "memories",
        "characters",
        ["character_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index("ix_memories_archived_at", "memories", ["archived_at"])
    op.create_index(
        "ix_memories_user_scope_importance",
        "memories",
        ["user_id", "scope", "importance"],
    )


def downgrade() -> None:
    # Restore legacy memory compatibility first.
    op.drop_index("ix_memories_user_scope_importance", table_name="memories")
    op.drop_index("ix_memories_archived_at", table_name="memories")

    op.drop_constraint(
        "fk_memories_character_id_characters",
        "memories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_memories_character_id_characters",
        "memories",
        "characters",
        ["character_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_memories_conversation_id_conversations",
        "memories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_memories_conversation_id_conversations",
        "memories",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Fill legacy bookkeeping fields for rows created by the revised app.
    op.execute(
        """
        UPDATE memories
        SET
            status = COALESCE(status, CASE WHEN archived_at IS NULL THEN 'active' ELSE 'archived' END),
            normalized_key = COALESCE(normalized_key, 'migrated:' || id::text),
            confidence = COALESCE(confidence, 1.0),
            access_count = COALESCE(access_count, 0)
        """
    )
    # Legacy schema has a smaller kind vocabulary. Preserve revised values in
    # metadata before mapping them to `fact` for rollback compatibility.
    op.execute(
        """
        UPDATE memories
        SET metadata = COALESCE(metadata, '{}'::jsonb)
                       || jsonb_build_object('revised_kind', kind),
            kind = 'fact'
        WHERE kind IN ('summary', 'note')
        """
    )

    for column, type_ in (
        ("status", sa.String(length=20)),
        ("normalized_key", sa.String(length=255)),
        ("confidence", sa.Float()),
        ("access_count", sa.Integer()),
    ):
        op.alter_column(
            "memories",
            column,
            existing_type=type_,
            nullable=False,
            existing_nullable=True,
        )

    op.create_check_constraint(
        op.f("ck_memories_scope_values"),
        "memories",
        "scope IN ('user','character','relationship','world','conversation')",
    )
    op.create_check_constraint(
        op.f("ck_memories_kind_values"),
        "memories",
        "kind IN ('fact','preference','event','promise','boundary','goal','relationship','world')",
    )
    op.create_check_constraint(
        op.f("ck_memories_status_values"),
        "memories",
        "status IN ('active','superseded','archived')",
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
    op.drop_column("memories", "archived_at")

    # Synchronize the legacy version rows with current values before removing
    # revised columns. This makes downgrade schema-safe for data created after
    # this bridge.
    op.execute(
        """
        INSERT INTO character_versions (
            character_id, version, name, summary, personality, scenario,
            greeting, system_instructions, metadata, id, created_at, updated_at
        )
        SELECT
            c.id, 1, c.name, c.description, c.personality, c.scenario,
            c.greeting, c.system_prompt, '{}'::jsonb,
            gen_random_uuid(), now(), now()
        FROM characters AS c
        WHERE NOT EXISTS (
            SELECT 1 FROM character_versions AS cv WHERE cv.character_id = c.id
        )
        """
    )
    op.execute(
        """
        UPDATE character_versions AS cv
        SET
            name = c.name,
            summary = c.description,
            personality = c.personality,
            scenario = c.scenario,
            greeting = c.greeting,
            system_instructions = c.system_prompt,
            updated_at = now()
        FROM characters AS c
        WHERE cv.character_id = c.id
          AND cv.version = c.current_version
        """
    )
    op.drop_index("ix_characters_name", table_name="characters")
    op.alter_column(
        "characters",
        "current_version",
        existing_type=sa.Integer(),
        server_default=None,
        existing_nullable=False,
    )
    for column in (
        "is_active",
        "greeting",
        "system_prompt",
        "scenario",
        "personality",
        "description",
        "tagline",
        "name",
    ):
        op.drop_column("characters", column)

    op.execute(
        """
        INSERT INTO persona_versions (
            persona_id, version, name, description, background, traits,
            writing_style, metadata, id, created_at, updated_at
        )
        SELECT
            p.id, 1, p.name, p.description,
            p.attributes ->> 'background',
            p.attributes ->> 'traits',
            p.attributes ->> 'writing_style',
            '{}'::jsonb,
            gen_random_uuid(), now(), now()
        FROM personas AS p
        WHERE NOT EXISTS (
            SELECT 1 FROM persona_versions AS pv WHERE pv.persona_id = p.id
        )
        """
    )
    op.execute(
        """
        UPDATE persona_versions AS pv
        SET
            name = p.name,
            description = p.description,
            background = COALESCE(p.attributes ->> 'background', pv.background),
            traits = COALESCE(p.attributes ->> 'traits', pv.traits),
            writing_style = COALESCE(p.attributes ->> 'writing_style', pv.writing_style),
            updated_at = now()
        FROM personas AS p
        WHERE pv.persona_id = p.id
          AND pv.version = p.current_version
        """
    )
    op.drop_index("ix_personas_is_default", table_name="personas")
    op.drop_index("ix_personas_name", table_name="personas")
    op.alter_column(
        "personas",
        "current_version",
        existing_type=sa.Integer(),
        server_default=None,
        existing_nullable=False,
    )
    for column in (
        "attributes",
        "is_default",
        "instructions",
        "description",
        "name",
    ):
        op.drop_column("personas", column)
