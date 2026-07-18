# ADR-001: Stateful refresh sessions and token rotation

- Status: Accepted
- Date: 2026-07-18

## Context

Astra AI must support multiple devices, explicit logout, logout-all, session revocation, and detection of a stolen refresh token being reused. A purely stateless refresh JWT cannot reliably provide those controls before token expiry.

## Decision

Access tokens remain short-lived JWTs. Every refresh token is linked to a persisted `refresh_sessions` row containing only a SHA-256 token hash, JTI, expiry, device metadata, family identifier, and revocation/replacement state. Refresh rotates the token under a database row lock. Reuse of a replaced token revokes the whole token family.

## Alternatives

1. Fully stateless refresh JWTs: simpler, but cannot provide immediate revocation or reliable reuse detection.
2. Store plaintext refresh tokens: easier comparison, but unnecessarily exposes bearer credentials if the database is leaked.
3. One global refresh token per user: prevents independent multi-device sessions.

## Consequences

Authentication refresh requires a database round trip and cleanup of expired rows in a future maintenance job. In exchange, device sessions are controllable and security events can be handled without waiting for token expiry.
