$ErrorActionPreference = "Stop"
$FrontendRoot = Split-Path -Parent $PSScriptRoot

Push-Location $FrontendRoot
try {
  flutter pub get
  dart run build_runner build --delete-conflicting-outputs
  dart format --output=none --set-exit-if-changed .
  flutter analyze
  flutter test
}
finally {
  Pop-Location
}
