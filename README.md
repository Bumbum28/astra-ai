# Astra AI Platform

Astra AI is a production-oriented AI platform, not a single-provider chatbot.
The repository contains a FastAPI backend and a Flutter client designed to
support multi-LLM chat, characters, personas, long-term memory, voice, images,
RAG, tool calling, streaming, and multi-device sessions.

## Current state

- Sprint 1: Docker, FastAPI, PostgreSQL, Redis, Alembic, health checks.
- Sprint 2: UUID domain models, authentication, refresh-token rotation,
  multi-device revoke, LLM abstraction.
- Sprint 3: Flutter foundation, secure authentication client, route guards,
  responsive home shell, sidebar, profile, and settings.
- Sprint 4: persistent conversations, cursor-paginated history, idempotent
  messages, SSE streaming, Markdown rendering, and responsive Flutter Chat.
- Sprint 5: versioned Characters and Personas, conversation profile snapshots,
  structured prompt composition, Relationship state/history, and Flutter
  management screens.

## Repository

```text
astra-ai/
├── backend/
├── frontend/
├── docker/
├── docs/
├── docker-compose.yml
└── README.md
```

## Start backend

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Swagger is available at `http://localhost:8000/docs` in development.

## Initialize Flutter client on Windows

Platform folders are generated from the Flutter SDK installed on the
developer's machine. This prevents stale Android, Web, and Windows template
files from being locked to an older Flutter release.

```powershell
cd frontend
PowerShell -ExecutionPolicy Bypass -File .\tool\bootstrap.ps1
```

Then run:

```powershell
flutter run -d chrome --web-port=8080
```

For Android Emulator:

```powershell
flutter run -d android
```

## Test

Backend:

```powershell
docker compose --profile test run --rm backend-test
```

Frontend:

```powershell
cd frontend
PowerShell -ExecutionPolicy Bypass -File .\tool\check.ps1
```

See `docs/sprint-05-roleplay-profiles.md` for the Sprint 5 API, migration, and verification guide.
