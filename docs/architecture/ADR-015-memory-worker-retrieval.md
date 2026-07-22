# ADR-015: Durable memory worker and hybrid retrieval

- Status: Accepted
- Date: 2026-07-23

## Context

Generating a summary and embeddings can take seconds and may fail because of
provider limits or network errors. Performing that work inside the visible chat
request would increase latency and hold application resources. In-memory queues
would lose work during a restart.

## Decision

1. A successful assistant reply inserts a durable `memory_tasks` database row.
2. A separate `memory-worker` service claims tasks with `FOR UPDATE SKIP LOCKED`.
3. Claims track attempts, lock time, availability, completion, and failure details.
4. Failed tasks retry with exponential backoff; stale processing locks can be
   reclaimed.
5. Summary/extraction calls use provider-neutral LLM contracts and Structured
   Outputs.
6. Chat retrieval first obtains a bounded lexical candidate set and optionally
   reranks it by embedding similarity plus importance, confidence, recency, and
   access signals.
7. Worker failure must never prevent the primary chat response from completing.

## Consequences

### Positive

- Chat latency is decoupled from compaction latency.
- Tasks survive container restarts.
- Multiple workers can safely claim different tasks.
- Provider or embedding failure degrades to retries or lexical retrieval.

### Negative

- Docker Compose gains another long-running service.
- Memory becomes eventually consistent rather than immediate.
- Database polling adds a small steady query load.
- Operators must monitor failed tasks and worker health.

## Rejected alternatives

- **FastAPI background tasks:** rejected because work can be lost on process exit.
- **Redis-only queue in this sprint:** rejected because it would add queue lifecycle
  and acknowledgement behavior while PostgreSQL is already transactional with the
  message write.
- **Synchronous extraction:** rejected because it directly increases user-visible
  response time.
