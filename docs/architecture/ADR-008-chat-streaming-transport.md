# ADR-008: Server-Sent Events for Chat Streaming

- **Status:** Accepted
- **Date:** 2026-07-22

## Context

Astra needs token-by-token responses on Flutter Web, mobile, and desktop while
keeping provider SDK objects inside provider adapters. WebSocket would add a
second bidirectional session protocol before Astra needs client-to-server live
events. Plain JSON responses cannot expose partial model output.

## Decision

Chat streaming uses an authenticated HTTP `POST` that returns
`text/event-stream`. Dio consumes the response body as a byte stream, and an
Astra-owned SSE decoder emits provider-independent events:

- `message.created`
- `message.delta`
- `message.completed`

Comment-only heartbeat frames are emitted while a provider read is pending so
reverse proxies do not mistake a slow local-model response for an idle stream.
- `error`

The user message and an assistant placeholder are committed before response
headers are returned. LLM provider streaming happens after that transaction.
The assistant message is finalized in a new transaction, so a slow provider
does not hold a database connection or row lock.

## Alternatives

- **WebSocket:** rejected for Sprint 4 because chat input is request/response and
  does not yet need bidirectional realtime presence.
- **Polling:** rejected because it increases latency and database load.
- **Provider-specific streaming payloads:** rejected because they would leak SDK
  contracts into Flutter and ChatService.

## Consequences

- Streaming is compatible with OpenAI and Ollama through `BaseLLMProvider`.
- Reverse proxies must disable buffering for this endpoint.
- Errors after headers are represented as SSE events rather than HTTP status
  codes.
- Client disconnects mark partial assistant messages as failed and retryable.
