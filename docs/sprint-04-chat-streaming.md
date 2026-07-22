# Sprint 4 — Conversation and Streaming Chat

## Goal

Deliver the first complete Astra AI feature that crosses Flutter, FastAPI,
PostgreSQL, and the provider abstraction: persistent multi-conversation chat
with real-time streaming.

## Groups

### Group 1 — Domain and migration

- Conversation lifecycle fields (`last_message_at`, `archived_at`).
- Message idempotency (`client_message_id`).
- Parent/reply relationship (`parent_message_id`).
- Reversible Alembic migration `20260722_0002`.
- Stable cursor encoding.

### Group 2 — Repository and application services

- Conversation and message repositories own all SQLAlchemy queries.
- Unit of Work exposes the two repositories.
- Conversation service handles create/list/get/update/archive/history.
- Chat application service coordinates persistence and provider-independent LLM
  calls.

### Group 3 — API and streaming

- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET/PATCH/DELETE /api/v1/conversations/{id}`
- `GET /api/v1/conversations/{id}/messages`
- `POST /api/v1/conversations/{id}/messages`
- `POST /api/v1/conversations/{id}/messages/stream`

The streaming endpoint emits SSE and does not use the JSON `ApiResponse`
envelope after headers are sent.

### Group 4 — Flutter Chat

- Responsive two-pane desktop layout and mobile list/detail navigation.
- Conversation create/list/archive.
- Message history and loading older pages.
- Dio POST streaming with a chunk-safe SSE decoder.
- SSE heartbeat comments keep slow local-model responses alive through proxies.
- Riverpod controllers for list and timeline state.
- Markdown rendering.
- Retry for failed assistant messages.

### Group 5 — Tests and quality

- Unit tests for conversation service, chat persistence, streaming, and SSE
  decoding.
- Integration test covers auth → conversation → stream → history.
- Backend and frontend CI scripts remain the source of truth for final local
  verification.

## Run migration

```powershell
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Rollback only the Sprint 4 migration:

```powershell
docker compose exec backend alembic downgrade 20260718_0001
docker compose exec backend alembic upgrade head
```

## Run checks

```powershell
docker compose --profile test run --rm backend-test
cd frontend
flutter pub get
dart run build_runner build --delete-conflicting-outputs
dart format .
flutter analyze
flutter test
```

## Architecture decisions

- `ADR-008-chat-streaming-transport.md`
- `ADR-009-chat-persistence-idempotency.md`

## Security and operational notes

- The Sprint 4 ZIP intentionally excludes `.env`; it does not remove the local
  file already present in the repository.
- The backend persists no raw provider objects.
- The client never receives provider API keys.
- Production reverse proxies must not buffer the SSE endpoint.
