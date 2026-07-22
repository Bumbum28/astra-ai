# ADR-011: Structured prompt composition

## Status

Accepted

## Decision

Prompt context is represented by typed contracts and composed by a dedicated
provider-independent service. The composer renders bounded known fields in a
stable order and does not dump metadata dictionaries or ORM objects.

## Consequences

- ChatService remains independent of provider SDKs.
- Prompt sections can be tested without a model.
- Future memory and RAG context can be added as typed sections with provenance.
- Provider-specific formatting remains inside provider implementations.
