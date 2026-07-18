# ADR-005: Flutter Token Lifecycle

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

Sprint 2 introduced short-lived access tokens and stateful refresh-token
rotation. The Flutter client must persist sessions securely, retry expired
requests safely, avoid multiple simultaneous refresh calls, and immediately
clear a revoked session.

## Decision

Store the token pair through a `TokenStore` abstraction backed by
`flutter_secure_storage`. Keep a memory cache inside the store to avoid reading
platform storage for every request.

Attach access tokens in a Dio interceptor. When a request returns HTTP 401,
perform one shared in-flight refresh operation. Concurrent failed requests
await the same refresh future and are retried once. Refresh uses a separate Dio
client so the interceptor cannot recursively intercept itself.

If refresh fails, clear local tokens and publish a session-expired event. The
AuthController consumes that event and changes the application state to
unauthenticated, allowing GoRouter to redirect to Login.

## Alternatives

### Store tokens in shared preferences

Rejected because authentication tokens are sensitive credentials.

### Refresh independently for every failed request

Rejected because concurrent requests could reuse the same rotated refresh
token and trigger server-side reuse detection.

### Put refresh logic inside each repository method

Rejected because token lifecycle is cross-cutting transport behavior and would
be duplicated across future Chat, Character, Memory, and Upload repositories.

## Consequences

- Refresh is centralized and single-flight.
- Requests are retried no more than once.
- Local logout still succeeds if the server is temporarily unavailable.
- Production Web builds require HTTPS because browser-backed secure storage
  depends on the origin and WebCrypto protections.
