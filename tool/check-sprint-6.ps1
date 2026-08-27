$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."
docker compose --profile test run --rm backend-test
Set-Location frontend
flutter pub get
dart format --output=none --set-exit-if-changed .
flutter analyze
flutter test
