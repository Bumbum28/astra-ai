# Legacy roleplay prototype migration assessment

## Purpose

This document records what was reviewed in the earlier `ai-roleplay-app` project
and what should or should not be reused in Astra AI.

## Reused now

### Local LLM capability

The old project proved that a shared Ollama model can serve multiple characters.
Astra now implements this as `OllamaProvider` inside the existing LLM abstraction,
without retaining the extra Express proxy.

### Local model profile

The useful roleplay constraints from `RoleplayEngineModelfile` were retained in a
sanitized development asset under `infra/ollama/`.

## Concepts worth implementing in later sprints

### Structured prompt composition

The old prompt builder separated:

- character profile and speaking style;
- user memory;
- character emotional state;
- world state;
- conversation summary;
- recent messages;
- response rules.

Astra should keep this separation, but implement it as typed prompt sections and
services rather than one interpolated string. Prompt composition belongs after the
Character and Memory contracts exist.

### Memory compaction

The old prototype summarized after a fixed number of messages. Astra should retain
the idea but replace the fixed threshold with a policy based on tokens, provider
context window, conversation activity, and summary version. Summarization should
run as an idempotent background job and store source-message boundaries.

### Relationship state

The old project tracked affection score, relationship level, status, context,
turn count, and last change reason. These are useful product concepts. They should
be modeled as a separate relationship domain with an event/history table rather
than mutable JSON attached directly to a conversation.

### Persona identity per conversation

The old conversation records included the user's selected identity name and gender.
Astra should support a versioned Persona entity referenced by a conversation, so a
persona can be reused while historical conversations preserve the version they used.

### Model routing and usage tiers

The old `3 / 5 / 20 Opal` routing demonstrates product-level budget control. Astra
should eventually route through a policy service using task type, capabilities,
latency target, token budget, user entitlement, and provider health. It should not
copy the old message-length `if/else` router.

## Explicitly not migrated

- `.env` files or credentials;
- `node_modules`;
- JSON files as production persistence;
- synchronous filesystem reads and writes in request handlers;
- the monolithic `server.js`;
- hard-coded ports, model names, and provider URLs;
- direct SDK calls from route handlers;
- mock provider branches mixed into production code;
- prompts built from unbounded raw JSON;
- relationship updates without transactional history;
- user or character identifiers generated from timestamps and random strings.

## Recommended mapping to Astra roadmap

| Astra stage | Reusable concept |
|---|---|
| Sprint 4 | streaming chat, conversation/message repositories, Ollama smoke path |
| Sprint 5 | Character, Persona, prompt composer, relationship domain |
| Memory sprint | memory facts, summaries, compaction jobs, retrieval policy |
| Platform routing | model capability registry, cost/latency policy, entitlement |
| RAG/tool sprint | typed context blocks and provenance, not prompt-string dumping |

## Cleanup applied during this review

The reviewed Astra ZIP contained both `app/utils/` and an unused misspelled
`app/utills/` directory. No imports referenced the misspelled package, so it was
removed. Generated Python caches and the `.git` directory are excluded from the
updated handoff ZIP.
