# ADR-007: Native Ollama provider

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

The earlier roleplay prototype used a separate Express service to forward requests
to Ollama. Astra AI already has provider-independent LLM contracts, a registry,
a factory, and a resolver. Keeping an extra proxy would duplicate configuration,
error handling, and deployment responsibilities.

## Decision

Add a native `OllamaProvider` to Astra's existing LLM layer.

The provider:

- accepts and returns Astra internal DTOs;
- calls Ollama's native chat and model-list endpoints;
- supports complete and streamed responses;
- can receive an injected HTTP client for tests;
- is registered through `ProviderRegistry`, without provider-selection `if/elif`;
- uses environment configuration for base URL, model, and timeout.

Docker Desktop reaches a host Ollama instance through
`host.docker.internal`. Direct local backend execution uses `localhost`.

## Alternatives

### Keep the old Node.js proxy

Rejected because it adds another runtime, another port, duplicated CORS handling,
and an unnecessary network hop.

### Call Ollama through OpenAI compatibility mode

Deferred. A native adapter preserves Ollama-specific model discovery and token
metadata without coupling local support to a compatibility surface.

### Wait until the chat sprint

Rejected because the current LLM abstraction is already the correct extension
point and the implementation is isolated from chat, character, and memory domains.

## Consequences

- Local LLM support can be enabled without changing `ChatService`.
- `httpx` becomes a backend runtime dependency.
- Ollama remains optional; startup does not fail when it is unavailable.
- Production deployments must configure an explicit reachable Ollama URL if the
  provider is enabled.
