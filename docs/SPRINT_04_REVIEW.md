# Sprint 4 Review

## Definition of Done

| Requirement | Result |
|---|---|
| Built on latest uploaded Astra source | Complete |
| Conversation CRUD and ownership | Complete |
| Persistent message history | Complete |
| Cursor pagination | Complete |
| Client message idempotency | Complete |
| Non-stream chat endpoint | Complete |
| SSE streaming endpoint and heartbeat | Complete |
| Provider SDK isolated from ChatService | Complete |
| Ollama/OpenAI compatible contracts | Complete |
| Flutter conversation list | Complete |
| Flutter message timeline | Complete |
| Incremental streaming UI | Complete |
| Markdown rendering | Complete |
| Failed response retry | Complete |
| Reversible migration | Complete |
| Backend unit/integration tests added | Complete |
| Frontend unit tests added | Complete |

## Manual architecture review

- Routers contain request/response adaptation only.
- SQLAlchemy query construction exists only in repositories.
- Streaming does not hold a database transaction open while the LLM runs.
- API schemas never expose ORM entities.
- `client_message_id` prevents duplicate model calls after ambiguous retries.
- Character and Memory are not imported into ChatService; Sprint 5 can compose
  them through a prompt/context layer.
- Assistant partial output is retained with failed status after interruption.
- `.env` and API keys are excluded from the handoff ZIP.

## Artifact environment limitation

Python source compilation, migration SQL generation, Sprint 4 unit tests,
and artifact integrity are checked in the generation environment. That environment does not provide Docker, PostgreSQL, Flutter SDK,
or the pinned future-dated development binaries, so the final Black/Ruff/mypy,
integration, `flutter analyze`, and `flutter test` commands must run on the
user's development machine using the included Docker and Flutter scripts.
