# ADR-002: Provider-independent LLM contracts and registry

- Status: Accepted
- Date: 2026-07-18

## Context

Astra AI will support OpenAI, Gemini, Claude, DeepSeek, and local models. Allowing provider SDK types to escape adapters would couple chat, memory, RAG, and tool calling to a vendor-specific API.

## Decision

All application code uses Astra-owned DTOs: `LLMRequest`, `LLMMessage`, `LLMResponse`, `LLMChunk`, and `LLMModelInfo`. Providers implement `BaseLLMProvider`. `LLMFactory` resolves provider classes through `ProviderRegistry`; provider selection has no `if/elif` chain. Registry entries are classes so dependencies can be constructed per use and overridden in tests.

Sprint 2 implements only the OpenAI adapter because an empty provider file is not an implementation. Additional providers register without changing `ChatService`.

## Alternatives

1. Import every provider SDK in `ChatService`: direct but creates vendor lock-in.
2. A large conditional factory: works initially but violates open/closed design as providers grow.
3. Store provider instances globally: complicates test isolation and lifecycle management.

## Consequences

Adapters must translate all request, response, error, usage, and streaming types. This mapping cost buys stable application boundaries and enables fake providers in unit tests.
