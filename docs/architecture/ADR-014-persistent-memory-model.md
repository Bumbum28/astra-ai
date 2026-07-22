# ADR-014: Persistent memory model

- Status: Accepted
- Date: 2026-07-23

## Context

Raw message history eventually exceeds the application prompt budget and becomes
noisy. Roleplay continuity requires stable facts, preferences, promises, world
state, and relationship developments to survive after old messages are omitted.
The user must also be able to inspect and forget stored information.

## Decision

1. Store compact continuity in one `conversation_summaries` row per conversation.
2. Store reusable facts as typed `memories` with explicit scope, kind, confidence,
   importance, provenance, expiry, and archive state.
3. Keep user, character, relationship, world, and conversation scopes separate so
   scene-specific information does not leak into unrelated chats.
4. Store embeddings as optional JSON arrays in Sprint 6. Candidate sets remain
   bounded and cosine ranking occurs in the application layer.
5. Use PostgreSQL full-text search for lexical candidate ordering.
6. Soft-archive forgotten memories rather than physically deleting them.
7. Reject credentials and sanitize forbidden scripts before persistence.
8. Treat the newest explicit user message as authoritative when memory conflicts.

## Consequences

### Positive

- Old raw messages can leave the prompt without losing essential continuity.
- Retrieval remains available without embeddings or an OpenAI key.
- Memory ownership and scope are explicit and queryable.
- Users can inspect and forget persisted memory.
- The design works on the existing PostgreSQL image without a vector extension.

### Negative

- JSON embeddings consume more storage and application CPU than a native vector
  index.
- Semantic ranking is intentionally bounded and is not suitable for millions of
  memories per user.
- Automatic extraction adds API cost and can still require user correction.

## Rejected alternatives

- **Send the entire transcript forever:** rejected for cost, latency, and noise.
- **Opaque provider-managed memory:** rejected because ownership, deletion, and
  portability would be unclear.
- **Require pgvector immediately:** rejected to avoid changing the existing
  PostgreSQL deployment during this sprint. A future migration can replace the
  storage adapter without changing memory contracts.
- **Store only one summary:** rejected because a summary alone cannot retrieve a
  specific preference or promise precisely.
