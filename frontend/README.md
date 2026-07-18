# Astra AI Flutter Client

Sprint 3 introduces the production-oriented Flutter foundation for Astra AI.

## First-time setup on Windows

```powershell
cd "G:\Model AI chat\astra-ai\frontend"
PowerShell -ExecutionPolicy Bypass -File .\tool\bootstrap.ps1
```

The script generates platform folders using the installed Flutter SDK, resolves
packages, generates Freezed/JSON code, formats the project, runs analysis, and
runs tests.

## Run against local Docker backend

Start the backend from the repository root:

```powershell
docker compose up --build
```

Run Flutter Web on the CORS-approved development port:

```powershell
cd frontend
flutter run -d chrome --web-port=8080
```

Run Android Emulator:

```powershell
flutter run -d android
```

Android Emulator uses `http://10.0.2.2:8000/api/v1` by default. A physical
device must use the computer's LAN address:

```powershell
flutter run `
  --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
```

Production builds must use HTTPS:

```powershell
flutter build apk `
  --release `
  --dart-define=API_BASE_URL=https://api.example.com/api/v1
```

## Quality checks

```powershell
PowerShell -ExecutionPolicy Bypass -File .\tool\check.ps1
```
