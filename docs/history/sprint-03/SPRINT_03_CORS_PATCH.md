# Sprint 3 CORS patch

This patch fixes Flutter Web login preflight requests that return HTTP 400.

Changes:

- Allows Private Network Access preflights in local development.
- Keeps compatibility with Starlette versions that do not yet expose the option.
- Adds `127.0.0.1:8080` to local development origins.
- Adds a regression test for the Flutter Web login preflight.

Production should set `CORS_ALLOW_PRIVATE_NETWORK=false` unless private-network browser access is explicitly required.
