# ADR-010: Versioned Character and Persona profiles

## Status

Accepted

## Decision

Character and Persona use stable root tables plus append-only version tables.
Conversations store both the root ID and exact version ID selected at creation or
explicit update.

## Consequences

- Historical conversations keep deterministic profile context.
- Profile edits do not mutate old roleplay history.
- New conversations can use the latest version.
- Version cleanup requires retention rules and cannot blindly delete referenced
  rows.
