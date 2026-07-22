# Sprint 6 — Persistent Memory System

Sprint 6 replaces unlimited raw-history prompting with a bounded memory pipeline.
Astra now preserves conversation continuity through compact summaries and retrieves
only the most relevant long-term memories for each new message.

## Goals

- Keep useful user, character, relationship, world, and scene facts across chat.
- Summarize older dialogue without blocking the visible reply path.
- Retrieve a small, ranked memory set before composing the prompt.
- Let the user inspect, refresh, edit, or forget stored memories.
- Avoid storing credentials and prevent forbidden CJK text from returning through
  hidden memory.
- Preserve Router → Service → Repository → Database boundaries.

## Architecture

```text
Successful assistant reply
  -> persistent memory_tasks outbox row
  -> memory-worker claims task with SKIP LOCKED
  -> GPT structured extraction and summary compaction
  -> credential/CJK guard
  -> optional OpenAI embeddings
  -> PostgreSQL memories + conversation_summaries

Next user message
  -> lexical candidates from PostgreSQL FTS
  -> optional cosine reranking over stored embeddings
  -> top relevant memories + compact summary
  -> StructuredPromptComposer
  -> GPT intelligence pipeline
```

The visible chat transaction does not wait for memory extraction. A separate
`memory-worker` service processes durable database tasks with retry and stale-lock
recovery.

## Memory scopes

| Scope | Lifetime and purpose |
| --- | --- |
| `user` | Stable facts and preferences reusable across conversations. |
| `character` | Stable facts tied to one Character. |
| `relationship` | Shared developments for one conversation relationship. |
| `world` | Fictional world facts for the current conversation. |
| `conversation` | Scene continuity that should not leak to other chats. |

Memory kinds are `fact`, `preference`, `event`, `promise`, `boundary`, `goal`,
`relationship`, and `world`.

## Compaction policy

By default, a task is queued after every 12 completed user/assistant messages.
The worker reads only messages not already covered by the latest summary and
processes at most 40 messages per task.

```env
MEMORY_COMPACTION_MESSAGE_THRESHOLD=12
MEMORY_COMPACTION_BATCH_SIZE=40
```

A manual refresh endpoint can force processing before the automatic threshold.

## Retrieval policy

Retrieval uses a bounded candidate set. PostgreSQL full-text search orders lexical
candidates, then Astra combines:

- semantic cosine similarity when embeddings are available;
- lexical rank;
- importance and confidence;
- recency and prior access.

Only the top configured results enter the prompt. The latest explicit user message
always overrides conflicting memory.

Embeddings are optional. When the API key or embedding service is unavailable,
chat falls back to lexical ranking instead of failing.

## Privacy and language safety

Automatic memory extraction is instructed not to retain passwords, API keys,
seed phrases, or recovery phrases. The backend also rejects or redacts matching
content before persistence.

The Vietnamese output guard is applied to generated summaries and extracted
memories. Chinese/Japanese script is removed before memory can be injected into a
later prompt.

The real `.env` file remains excluded from source and release ZIP files.

## API

```text
POST   /api/v1/memories
GET    /api/v1/memories
PATCH  /api/v1/memories/{memory_id}
DELETE /api/v1/memories/{memory_id}

GET  /api/v1/conversations/{conversation_id}/memory
POST /api/v1/conversations/{conversation_id}/memory/refresh
```

Deleting a memory performs a soft archive so it no longer participates in
retrieval.

## Flutter

The Chat header now contains a memory icon. The inspector shows:

- the compact conversation summary;
- pending background task count;
- long-term memories relevant to the conversation;
- a manual refresh action;
- a forget/archive action for each memory.

## Configuration

Add these values to the root `.env`:

```env
APP_VERSION=0.6.0
OPENAI_BASE_URL=https://api.openai.com/v1

MEMORY_ENABLED=true
MEMORY_EMBEDDINGS_ENABLED=true
MEMORY_EMBEDDING_MODEL=text-embedding-3-small
MEMORY_EMBEDDING_DIMENSIONS=1536
MEMORY_EXTRACTION_PROVIDER=openai
MEMORY_EXTRACTION_MODEL=gpt-5.6-luna
MEMORY_EXTRACTION_REASONING_EFFORT=low
MEMORY_EXTRACTION_MAX_TOKENS=1800
MEMORY_COMPACTION_MESSAGE_THRESHOLD=12
MEMORY_COMPACTION_BATCH_SIZE=40
MEMORY_RETRIEVAL_LIMIT=8
MEMORY_RETRIEVAL_CANDIDATE_LIMIT=200
MEMORY_WORKER_POLL_SECONDS=2
MEMORY_WORKER_MAX_ATTEMPTS=5
MEMORY_WORKER_RETRY_BASE_SECONDS=15
MEMORY_WORKER_LOCK_TIMEOUT_SECONDS=300
```

Set `MEMORY_EMBEDDINGS_ENABLED=false` to disable embedding calls while keeping
summary extraction and lexical memory retrieval.

## Start and verify

Rebuild both backend and worker after extraction:

```powershell
docker compose up -d --build --force-recreate backend memory-worker
```

Check migration and services:

```powershell
docker compose exec backend alembic current
docker compose ps
docker compose logs memory-worker --tail=100
```

Expected Alembic head:

```text
20260723_0004 (head)
```

Force an update from the Flutter memory inspector, or call the refresh endpoint
after a conversation contains messages. The worker log should show task processing
and the inspector should eventually show a summary.

## Rollback

Stop the worker first:

```powershell
docker compose stop memory-worker
docker compose exec backend alembic downgrade 20260722_0003
```

Restore Sprint 6 later with:

```powershell
docker compose exec backend alembic upgrade head
docker compose up -d memory-worker
```
