# ADR-013: OpenAI Responses intelligence pipeline

- Status: Accepted
- Date: 2026-07-22

## Context

A single small local model call produced replies that were often generic, missed
subtext, lost continuity, or violated language/style constraints. Astra already
had a provider-neutral LLM abstraction, but the OpenAI adapter used the older
chat-completions shape and the application had no response-quality gate.

The solution must improve quality without importing provider SDKs into domain
services or persisting hidden reasoning.

## Decision

1. OpenAI integration uses the Responses API behind `OpenAIProvider`.
2. The visible response defaults to `gpt-5.6-terra` with medium reasoning.
3. A cheaper `gpt-5.6-luna` call produces a strict structured response plan.
4. A second Luna call returns a strict structured critic verdict.
5. One rewrite is allowed when the draft fails the configured threshold.
6. Planner and critic output are concise typed contracts, not free-form
   chain-of-thought, and are not stored as user-visible message content.
7. Requests default to `store=false`.
8. A local application budget limits the prompt to approximately 16K tokens.
9. Pipeline failure degrades gracefully to the best available draft.
10. The provider-neutral `LLMRequest` carries reasoning and response-schema
    options, while ChatService remains SDK-independent.

## Consequences

### Positive

- Better understanding of intent, emotional subtext, continuity, and constraints.
- Deterministic parsing for planner and critic through Structured Outputs.
- Model/provider choices remain configuration-driven.
- Hidden planning is not exposed to the user.
- The same internal pipeline can later work with another capable provider.

### Negative

- Normal replies use three API requests; a rewrite uses four.
- Latency and cost increase compared with one-pass generation.
- Planner/critic outages may reduce quality, though replies still degrade
  gracefully.
- The heuristic token estimator is conservative and not a replacement for a
  provider tokenizer.

## Rejected alternatives

- **Put all rules into one prompt:** inexpensive, but did not reliably address
  reasoning, continuity, and quality failures.
- **Expose chain-of-thought:** unnecessary, brittle, and inappropriate for the
  product contract.
- **Replace provider abstraction with direct SDK calls in ChatService:** rejected
  because it violates Astra's architecture and prevents provider portability.
- **Unlimited context:** rejected because it increases cost and eventually makes
  raw history noisy; Sprint 6 will add memory retrieval and compaction.
