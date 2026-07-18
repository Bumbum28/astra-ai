# Sprint 2 Patch Notes

## Fixed

- Refresh-token rotation no longer violates the self-referential foreign key on `refresh_sessions.replaced_by_session_id`.
- The replacement refresh session is explicitly flushed before the previous session references it.
- Only PostgreSQL unique-constraint violations are translated to HTTP 409; unrelated integrity failures are no longer mislabeled as conflicts.
- Pytest cache is stored in `/tmp/pytest_cache` so the non-root test container can write it without warnings.

## Validation

- Black: pass
- Ruff: pass
- Mypy: pass
- Unit tests: 7 passed
- Foreign-key rotation regression simulation: pass
