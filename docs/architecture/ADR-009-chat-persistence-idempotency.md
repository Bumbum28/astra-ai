# ADR-009: Persistent Chat Idempotency and Cursor Pagination

- **Status:** Accepted
- **Date:** 2026-07-22

## Context

Mobile and web clients may retry a message when network state is ambiguous.
Without an idempotency key, one user action could create duplicate messages and
multiple billable LLM calls. Offset pagination also becomes unstable when new
messages arrive while older history is being loaded.

## Decision

Every user send operation includes a UUID `client_message_id`. PostgreSQL
enforces uniqueness per conversation. Assistant messages point to their user
message through `parent_message_id`.

If a completed exchange already exists, Astra returns/replays it without a new
LLM call. A failed assistant reply can be retried with the same client ID. An
exchange still marked pending or streaming returns a conflict.

Conversation lists and message history use opaque keyset cursors containing a
timestamp and UUID tie-breaker. API consumers never depend on cursor internals.
Conversations are archived with `archived_at` instead of being physically
deleted.

## Alternatives

- **Random server-only IDs:** rejected because they cannot deduplicate an
  ambiguous client retry.
- **Offset pagination:** rejected because inserts can cause duplicates or gaps.
- **Hard delete:** rejected because recovery, moderation, and audit workflows
  will need retained history.

## Consequences

- Client-generated UUIDs become part of the public chat contract.
- The migration adds a partial unique index and self-referencing message FK.
- Future tool calls can reuse `parent_message_id` without replacing the schema.
