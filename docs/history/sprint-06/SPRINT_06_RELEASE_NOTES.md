# Astra AI Sprint 6 release notes

Version: `0.6.0`

Sprint 6 adds persistent long-term memory, compact conversation summaries,
hybrid retrieval, a durable background worker, and a Flutter memory inspector.

## Database

Alembic head:

```text
20260723_0004
```

New tables:

```text
memories
conversation_summaries
memory_tasks
```

## Runtime

Docker Compose now starts `memory-worker` in addition to `backend`, `postgres`,
and `redis`. Memory extraction runs asynchronously and does not block the visible
chat response.

## Safety

- Real `.env` and API keys are excluded from the release ZIP.
- Credentials and recovery phrases are blocked or redacted from memory.
- Chinese/Japanese scripts are removed from generated memory before prompt reuse.
- Users can archive individual memories from the Chat memory inspector.

## Compatibility

- Existing conversations remain valid.
- No raw message data is deleted by the migration.
- Embeddings are optional; lexical retrieval remains available when disabled.
- Rollback target is `20260722_0003`.
