# Sprint 7 checks

## Executed in artifact environment

- Python `compileall`: PASS for backend application modules.
- Alembic graph: PASS, exactly one head (`20260828_0007`).
- Alembic offline upgrade SQL through Sprint 7: PASS.
- Alembic offline downgrade `20260828_0007 → 20260827_0006`: PASS.
- Focused Agent/Tool/RAG/Chat regression tests: PASS (19 tests).
- Agent trace hardening: model text is not persisted in step traces; only content length, structured tool calls and usage metadata are stored.
- Agent policy regression: requested tools outside the configured allow-list are rejected.
- Token usage aggregation across multi-step Agent calls: PASS.
- Secret policy: final package excludes `.env`, archives, caches and local database dumps.

## Run on the developer machine

```powershell
docker compose up --build
docker compose run --rm --entrypoint alembic backend current
docker compose --profile test run --rm backend-test

cd frontend
flutter pub get
flutter analyze
flutter test
```

The developer Docker image contains the full pinned backend dependencies that are not all present in the artifact-building sandbox. GitHub now also includes `backend-ci.yml` to exercise the full backend suite with PostgreSQL and Redis services after push/PR.
