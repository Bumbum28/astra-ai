# ADR-012: Relationship state with transactional history

## Status

Accepted

## Decision

Relationship is a conversation-scoped domain object. Mutable current state is
stored in `relationships`; meaningful manual changes append immutable
`relationship_events` in the same transaction.

Level and affection score are independent. The application does not infer one
from the other.

## Consequences

- Current prompt context is inexpensive to load.
- Changes are auditable.
- Narrative relationship levels can represent non-linear states.
- Automatic model-driven updates require an explicit future policy and are not
  silently introduced.
