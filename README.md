# Astra AI Platform — Sprint 7

Production-oriented AI chat/roleplay platform. This package contains the cumulative source for Sprints 1–7.

Sprint 7 adds a bounded **AI Agent Runtime** on top of the Sprint 6 RAG and Tool Calling foundation. Direct chat remains the default; Agent mode is an explicit per-message execution mode.

## Sprint 7 highlights

- `ChatOrchestrator` selects Direct Chat or Agent execution without coupling the router to either runtime.
- `AgentRuntime` executes a bounded LLM → tool → result loop.
- Agent runs and individual steps are persisted for audit/debugging.
- Read-only built-in tools remain allow-listed by policy: `search_knowledge` and `search_conversation`.
- Hard limits: max model iterations, max tool calls, per-tool timeout and whole-run timeout.
- Tool failures are returned to the model as tool results so the agent can recover within its budget.
- Tool outputs are explicitly treated as untrusted data, not higher-priority instructions.
- Flutter Chat has an Agent toggle and labels completed Agent responses with step/tool counts.
- Reversible Alembic revision: `20260828_0007`.
- Backend GitHub Actions CI now verifies Python compilation, a single Alembic head, and the backend test suite against PostgreSQL/Redis services.

See `docs/sprint-07-agent-runtime.md` and `docs/architecture/ADR-016-agent-runtime.md`.

## Start

```bash
docker compose up --build
```

Frontend lives in `frontend/`. Secrets belong only in local `.env`; this archive intentionally does not include `.env`.
