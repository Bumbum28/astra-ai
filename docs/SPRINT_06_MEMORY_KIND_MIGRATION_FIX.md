# Sprint 6 memory-kind migration fix

## Problem

Revision `20260827_0005` attempted to normalize legacy memory kinds such as
`event`, `promise`, `boundary`, `goal`, and `world` to the revised value
`note` while the legacy `ck_memories_kind_values` CHECK constraint was still
active. PostgreSQL correctly rejected the UPDATE.

## Fix

The migration now drops the three legacy vocabulary CHECK constraints before
normalizing `scope` and `kind` values:

1. Add `archived_at`.
2. Drop legacy scope/kind/status vocabulary constraints.
3. Preserve legacy values in JSON metadata.
4. Normalize legacy scope/kind values.
5. Continue the in-place compatibility migration.

The Alembic revision identifiers are unchanged. This is a correction to an
unapplied/failing migration, not a new schema revision.

## Recovery

Because PostgreSQL DDL is transactional in this project, the failed upgrade
should remain at `20260723_0004`. Verify with:

```powershell
docker compose run --rm --entrypoint alembic backend current
```

Then rebuild and retry:

```powershell
docker compose build --no-cache backend
docker compose run --rm --entrypoint alembic backend heads
docker compose run --rm --entrypoint alembic backend upgrade head
docker compose run --rm --entrypoint alembic backend current
```

Expected head/current after success: `20260827_0006`.
