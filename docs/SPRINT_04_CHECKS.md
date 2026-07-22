# Sprint 4 Artifact Checks

## Completed in the artifact environment

- Python compilation for `backend/app` and `backend/alembic`.
- All 64 non-test backend modules imported successfully.
- 24 backend unit tests passed. The artifact environment used lightweight
  import shims for external packages that were not installed there; the shims
  are not included in the handoff.
- Nine Sprint 4 backend unit tests passed for conversation behavior, streaming,
  retries, in-flight idempotency, and cursor validation.
- Alembic generated PostgreSQL SQL for both upgrade to `20260722_0002` and
  downgrade to `20260718_0001`.
- No SQLAlchemy import exists in service modules.
- Chat services contain no OpenAI or other provider SDK imports.
- All internal Dart package imports resolve to files in `frontend/lib`.
- Structural delimiter checks passed for 70 Dart source and test files.
- `pubspec.yaml` and `docker-compose.yml` parse as YAML.

## Required on the development machine

The artifact environment did not provide Docker, PostgreSQL, or Flutter SDK.
Run the authoritative checks locally:

```powershell
docker compose --profile test run --rm backend-test

cd frontend
PowerShell -ExecutionPolicy Bypass -File .\tool\check.ps1
```

These commands run the real pinned dependencies, PostgreSQL migrations,
`dart format`, `flutter analyze`, and `flutter test`.
