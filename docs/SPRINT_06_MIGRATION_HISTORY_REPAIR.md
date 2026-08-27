# Astra AI Sprint 6 — Alembic history repair

## Root cause

The revised Sprint 5/6 package replaced already-published Alembic revisions
`20260722_0003` and `20260723_0004` with a new branch
`20260729_0003 -> 20260805_0004`.

The user's PostgreSQL volume had already recorded `20260723_0004`, so Alembic
could not locate that revision after the source files were overwritten.

## Repair policy

Published migrations are immutable. This repair restores the original lineage
and appends compatibility migrations instead of rewriting history:

`20260718_0001`
→ `20260722_0002`
→ `20260722_0003`
→ `20260723_0004`
→ `20260827_0005`
→ `20260827_0006`

`20260827_0005` upgrades the legacy Character/Persona/Memory tables in place to
the revised Sprint 5 ORM contract while preserving existing roleplay and memory
rows. Legacy version/history tables are intentionally retained.

`20260827_0006` is the RAG/Tool Calling database migration, renumbered so it
follows the compatibility bridge.

## Apply

1. Extract this patch into the repository root.
2. Run:

```powershell
PowerShell -ExecutionPolicy Bypass -File ".\tool\apply-sprint6-migration-repair.ps1"
```

3. Start only infrastructure first:

```powershell
docker compose up -d postgres redis
```

4. Check the existing database revision:

```powershell
docker compose exec postgres psql -U astra -d astra_ai -c "SELECT version_num FROM alembic_version;"
```

5. Rebuild backend and verify one Alembic head:

```powershell
docker compose build --no-cache backend
docker compose run --rm --entrypoint alembic backend heads
```

Expected:

`20260827_0006 (head)`

6. Upgrade and start:

```powershell
docker compose run --rm --entrypoint alembic backend upgrade head
docker compose up -d
```

Do not use `docker compose down -v` unless all development database data may be
discarded.
