# ADR-004: Flutter Client Architecture

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

The Flutter client must grow from authentication into chat, characters,
memory, voice, images, RAG, and tool calling. A screen-oriented structure that
calls Dio directly would couple presentation code to transport details and
make feature testing difficult.

## Decision

Use a feature-first Clean Architecture structure:

```text
Presentation
    ↓
Application controller
    ↓
Domain repository contract
    ↓
Data repository
    ↓
Remote/local data source
```

Riverpod is used for dependency injection and application state. GoRouter owns
navigation and authentication redirects. Dio is isolated in the networking
layer. Freezed defines immutable domain data. Platform configuration is read
through compile-time `--dart-define` values.

Shared cross-cutting code remains under `core/`; feature behavior remains
under `features/<feature>/`.

## Alternatives

### Organize only by technical layer

Rejected because `models/`, `services/`, and `screens/` become large shared
directories as Chat, Character, Memory, and Voice grow.

### Call Dio directly from widgets

Rejected because it mixes transport, persistence, state, and UI concerns.

### Use a global service locator

Rejected because dependencies become implicit and test overrides become
harder. Riverpod provides explicit, scoped, replaceable dependencies.

## Consequences

- Feature modules have clear ownership and can be tested independently.
- Some small features contain more files than a demo application.
- Repository contracts must remain domain-focused rather than mirroring every
  HTTP endpoint.
- Cross-feature abstractions require deliberate review before moving into
  `core/`.
