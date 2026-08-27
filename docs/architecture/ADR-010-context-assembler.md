# ADR-010 — Central ContextAssembler

Status: Accepted

## Context
Character, Persona and Memory must influence both direct chat and future agents. Embedding that logic inside ChatApplicationService would make the service depend on every future context domain.

## Decision
Use a `ContextAssembler` contract. Direct chat supplies conversation and message history; the assembler resolves owned Character, Persona and Memory through repositories and returns provider-independent `LLMMessage` values.

## Alternatives
- Build prompts directly in ChatApplicationService. Rejected because it creates a growing orchestration class.
- Build prompts inside each LLM provider. Rejected because providers must remain transport adapters.

## Consequences
Agent Runtime can reuse the same context boundary in Sprint 7. Memory retrieval can later be upgraded without changing provider SDK adapters.
