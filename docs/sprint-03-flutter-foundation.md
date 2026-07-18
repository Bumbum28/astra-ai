# Sprint 3 — Flutter Application Foundation

## Goal

Create a production-oriented Flutter client that consumes the Sprint 2
authentication API and provides a stable shell for Chat and Character features.

## Source of truth

Sprint 3 was built directly from the uploaded `astra-ai.zip`. The uploaded
repository was already on `feature/sprint-3`; its backend Sprint 2 code was
preserved and the previously empty `frontend/` directory was implemented.

## Group 1 — Baseline and Architecture

### Deliverables

- Audited Sprint 2 API response and authentication contracts.
- Kept backend domain/authentication implementation intact.
- Added ADR-004, ADR-005, and ADR-006.
- Updated platform version to `0.3.0`.
- Expanded Git ignore rules for Flutter and Dart output.

### Review

The frontend follows:

```text
Widget
  ↓
AuthController
  ↓
AuthRepository
  ↓
AuthRemoteDataSource
  ↓
Dio
```

Widgets do not access Dio, secure storage, or token payloads directly.

## Group 2 — Flutter Core

### Deliverables

- Material 3 light/dark theme.
- Riverpod root `ProviderScope`.
- GoRouter navigation and authentication guards.
- Environment-aware API base URL.
- Responsive app shell.
- One-time platform bootstrap scripts.

### Routes

```text
/splash
/login
/register
/home
/chats
/characters
/profile
/settings
```

## Group 3 — Authentication Data and Application Layers

### Deliverables

- Immutable Freezed entities: User, AuthTokens, AuthSession.
- `TokenStore` contract with secure-storage implementation.
- Dio API client and API-envelope validation.
- Auth repository contract and implementation.
- Session restoration through `/auth/me`.
- Access-token attachment.
- Single-flight refresh-token rotation.
- One retry maximum after a 401.
- Session-expired event propagation.

## Group 4 — Presentation

### Deliverables

- Login form with validation and autofill.
- Registration form with validation and password confirmation.
- Loading/error presentation.
- Responsive Home shell using NavigationRail or NavigationDrawer.
- Profile view.
- Logout current device.
- Logout all devices.
- Theme settings.
- Intentional Chat and Character placeholders.

Chat and Character business logic is not faked in Sprint 3.

## Group 5 — Quality and Handoff

### Deliverables

- Unit tests for API envelopes and AuthController.
- Widget validation test for Login.
- Flutter bootstrap and quality-check scripts.
- GitHub Actions frontend CI.
- Sprint review and file tree.

## First run on Windows

```powershell
cd "G:\Model AI chat\astra-ai\frontend"
PowerShell -ExecutionPolicy Bypass -File .\tool\bootstrap.ps1
```

This command:

1. Generates Android, Web, and Windows platform folders.
2. Applies the local Android debug networking override.
3. Runs `flutter pub get`.
4. Runs Freezed and JSON generation.
5. Runs Dart format.
6. Runs Flutter analyze.
7. Runs Flutter tests.

## Run backend and client

Backend:

```powershell
cd "G:\Model AI chat\astra-ai"
docker compose up --build
```

Web:

```powershell
cd frontend
flutter run -d chrome --web-port=8080
```

Android Emulator:

```powershell
flutter run -d android
```

Physical Android device:

```powershell
flutter run `
  --dart-define=API_BASE_URL=http://YOUR_PC_LAN_IP:8000/api/v1
```

## Commit message

```text
feat(sprint-3): add Flutter authentication and application shell
```
