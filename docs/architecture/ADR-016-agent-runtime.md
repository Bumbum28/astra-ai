# ADR-016 — Bounded Agent Runtime behind ChatOrchestrator

## Status
Accepted — Sprint 7

## Decision

Astra supports two explicit chat execution paths: `direct` and `agent`. The API router depends on `ChatOrchestrator`, which selects the path for each message. Both paths reuse `ChatApplicationService` for ownership, idempotency, chat persistence and SSE lifecycle.

Agent execution lives in `app/agents` and depends only on provider-independent LLM contracts plus `ToolRegistry`/`ToolExecutor`. It persists run/step traces in dedicated tables rather than encoding agent internals in chat messages.

## Why

Putting the Agent loop inside `ChatApplicationService` would couple chat persistence, tool policy, provider interaction and future planning/background execution. Keeping an execution boundary allows Direct Chat to remain simple while Agent capabilities evolve independently.

## Consequences

- Existing clients remain backward compatible because `execution_mode` defaults to `direct`.
- Agent mode can be enabled per message.
- Agent traces can be inspected without exposing private reasoning; only structured calls/results and a bounded model-content preview are stored.
- Future mutating tools can introduce confirmation/policy layers without changing the chat router.
- Future background/multi-agent work can build on `agent_runs` without reusing the `messages` table as a job log.
