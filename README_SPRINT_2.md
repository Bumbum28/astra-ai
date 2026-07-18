# Astra AI — Sprint 2

Sprint 2 adds the production-oriented authentication and provider-independent LLM foundation.

## Install into the existing repository

Extract this ZIP directly into:

```text
G:\Model AI chat\astra-ai
```

Allow the extractor to replace files with the same names. Legacy Sprint 1 modules may remain on disk, but the application imports the new domain-oriented modules.

## Start

```powershell
cd "G:\Model AI chat\astra-ai"
docker compose up --build
```

The backend runs Alembic migrations before Uvicorn when `RUN_MIGRATIONS=true`.

## Verify

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health/live
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

Swagger:

```text
http://localhost:8000/docs
```

## Tests

```powershell
docker compose --profile test run --rm backend-test
```

## Quality

From `backend/` after installing `requirements-dev.txt`:

```powershell
black --check .
ruff check .
mypy app
pytest -m "not integration"
```

See `docs/sprint-02-platform-foundation.md` for the complete review and endpoint examples.
