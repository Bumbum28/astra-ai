# ADR-011 — Explicit SQL memory foundation before semantic retrieval

Status: Accepted

## Context
Long-term memory needs provenance, ownership and stable persistence before semantic extraction/retrieval is added.

## Decision
Store typed Memory records in PostgreSQL with user, character and conversation scopes, importance and source-message provenance. Sprint 5 context selection is deterministic by scope/importance.

## Alternatives
- Store only prompt text on Character. Rejected because memories evolve over time.
- Introduce a vector database immediately. Rejected because Sprint 5 does not yet need semantic retrieval and it would couple memory persistence to one retrieval technology.

## Consequences
Sprint 6 can introduce RAG behind a Retriever interface. A later memory extractor can create/update Memory records without changing chat or provider contracts.
