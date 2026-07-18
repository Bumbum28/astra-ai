# Sprint 2 — Authentication and LLM Platform Foundation

## Goal

Add secure multi-device authentication and an extensible LLM boundary without coupling application services to provider SDKs.

## Architecture

```text
HTTP Router
    ↓
Application Service
    ↓
Unit of Work
    ↓
Domain Repositories
    ↓
SQLAlchemy / PostgreSQL
```

```text
ChatService
    ↓
LLMProviderResolver
    ↓
LLMFactory + ProviderRegistry
    ↓
BaseLLMProvider
    ↓
OpenAI adapter
```

## Authentication endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/logout-all`
- `GET /api/v1/auth/me`

## Start and migrate

```bash
docker compose up --build
```

The local backend automatically runs:

```bash
alembic upgrade head
```

Manual rollback verification:

```bash
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic upgrade head
```

## Test

```bash
docker compose --profile test run --rm backend-test
```

Unit only:

```bash
cd backend
pytest -m "not integration"
```

## Code quality

```bash
cd backend
black --check .
ruff check .
mypy app
```

## Security behavior

- Passwords are bcrypt-hashed and never included in response schemas.
- Bcrypt inputs are capped at 72 UTF-8 bytes.
- Access JWTs are short lived.
- Refresh JWTs are represented by hashed, revocable database sessions.
- Rotation revokes the old session and creates a replacement in the same family.
- Reuse of a replaced refresh token revokes the active family.
- Logout revokes one session; logout-all revokes all active sessions for the user.

## Deferred intentionally

Memory, Character, RAG, voice, image, tool calls, attachments, and a public chat endpoint are not implemented in Sprint 2. The data and LLM boundaries are prepared without adding unused placeholder services or tables.

## Review checklist

- [x] Domain-oriented modules for auth, users, conversations, messages, health, and LLM.
- [x] UUID identifiers and timestamp mixins.
- [x] Reversible first domain migration.
- [x] Router → Service → Repository → Database.
- [x] No SQLAlchemy query construction in services.
- [x] API response schemas do not expose ORM entities.
- [x] Stateful refresh rotation and reuse detection.
- [x] Provider registry without provider-selection conditionals.
- [x] ChatService imports only Astra LLM abstractions.
- [x] Unit and PostgreSQL integration tests.
- [x] Black, Ruff, and mypy configuration.
- [x] Three Architecture Decision Records.

## Suggested commits by group

```text
chore(backend): prepare sprint 2 development baseline
refactor(backend): introduce domain-oriented application structure
feat(common): standardize responses exceptions and config
feat(database): add uuid domain models and reversible migration
feat(auth): implement multi-device authentication and token rotation
feat(llm): add provider-independent llm foundation
 test: cover authentication database and llm boundaries
 docs(architecture): record sprint 2 platform decisions
```

Final squash/summary commit:

```text
feat(sprint-2): complete authentication and llm platform foundation
```
