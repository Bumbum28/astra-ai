# Sprint 2 Verification Report

Verification performed on 2026-07-18.

## Passed locally

- Python 3.13 source compilation.
- `black --check .`
- `ruff check .`
- `mypy app`
- Unit tests: 7 passed.
- Application import and bootstrap.
- Root endpoint returns HTTP 200.
- Liveness endpoint returns HTTP 200.
- Shared validation handler returns the standardized error envelope.
- Alembic offline upgrade SQL generation.
- Alembic offline downgrade SQL generation.
- Docker Compose YAML parsing and service/profile structure review.
- `pip check` reports no broken dependency requirements.

## Not executable in the build environment

The build environment did not provide Docker or a PostgreSQL daemon. The PostgreSQL integration test is included but was skipped locally. Run the following on the target Windows machine with Docker Desktop:

```powershell
docker compose --profile test run --rm backend-test
```

That command starts a dedicated PostgreSQL test container and executes migration upgrade → downgrade → upgrade before the authentication API integration flow.

## Final architecture checks

- No `print()` calls in application code.
- No SQLAlchemy query construction in service files.
- OpenAI SDK imports are isolated to the provider adapter and its adapter unit test.
- Routers delegate authentication behavior to `AuthService`.
- Response schemas do not expose password hashes or ORM entities.
- Provider resolution uses a registry rather than an `if/elif` provider switch.
- `main.py` remains an application bootstrap module.
