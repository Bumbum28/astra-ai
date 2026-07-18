# Sprint 3 Final Review

## Definition of Done

| Requirement | Result |
|---|---|
| Built on uploaded Sprint 2 source | Pass |
| Flutter project foundation | Pass |
| Riverpod dependency injection/state | Pass |
| GoRouter auth redirects | Pass |
| Dio networking isolated from UI | Pass |
| Secure token storage abstraction | Pass |
| Single-flight refresh rotation | Pass |
| Login UI | Pass |
| Registration UI | Pass |
| Session restore | Pass |
| Home shell | Pass |
| Responsive sidebar/drawer | Pass |
| Logout current device | Pass |
| Logout all devices | Pass |
| Light/dark/system theme | Pass |
| Unit tests added | Pass |
| Widget test added | Pass |
| Backend Black/Ruff/mypy | Pass |
| Backend unit tests | Pass — 8 tests |
| Dart syntax/import validation | Pass — 49 files |
| ADR documentation | Pass |
| Platform bootstrap script | Pass |

## Manual Review

- No widget imports or constructs Dio.
- No widget reads/writes secure tokens.
- Access and refresh tokens are not displayed or logged.
- Refresh uses a separate client and cannot recurse.
- Concurrent 401 responses share one refresh operation.
- A request is retried at most once.
- Invalid refresh credentials clear local credentials and change navigation state.
- Temporary network failure does not delete the stored session.
- Startup restoration state is separate from login/register action state.
- Failed logout-all preserves the active session.
- The UI uses backend schemas rather than ORM assumptions.
- Chat and Character features remain placeholders until their domain Sprint.
- Android local HTTP access is debug-only.
- Production API endpoints are injected with `--dart-define`.

## Environment limitation

The artifact build environment did not contain a Flutter SDK. Therefore native
platform templates, Freezed output, `flutter analyze`, and `flutter test` must
be generated/executed by `frontend/tool/bootstrap.ps1` on the development
machine. The ZIP contains all Astra-owned source and deterministic setup
scripts; it does not claim that Flutter binaries were executed in the artifact
environment. See `SPRINT_03_CHECKS.md` for the exact verification record.
