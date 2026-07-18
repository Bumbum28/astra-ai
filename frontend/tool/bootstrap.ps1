$ErrorActionPreference = "Stop"

$FrontendRoot = Split-Path -Parent $PSScriptRoot
$TempRoot = Join-Path $env:TEMP ("astra_flutter_" + [guid]::NewGuid().ToString("N"))

Write-Host "Generating Flutter platform files..."
flutter create `
  --project-name astra_ai `
  --org com.astra.ai `
  --platforms=android,web,windows `
  --no-pub `
  $TempRoot

foreach ($Directory in @("android", "web", "windows")) {
  $Source = Join-Path $TempRoot $Directory
  $Destination = Join-Path $FrontendRoot $Directory
  if (Test-Path $Destination) {
    Remove-Item $Destination -Recurse -Force
  }
  Copy-Item $Source $Destination -Recurse
}

Copy-Item `
  (Join-Path $TempRoot ".metadata") `
  (Join-Path $FrontendRoot ".metadata") `
  -Force

$DebugManifest = Join-Path `
  $PSScriptRoot `
  "platform_overrides/android/app/src/debug/AndroidManifest.xml"
$DebugManifestTarget = Join-Path `
  $FrontendRoot `
  "android/app/src/debug/AndroidManifest.xml"
Copy-Item $DebugManifest $DebugManifestTarget -Force

Remove-Item $TempRoot -Recurse -Force

Push-Location $FrontendRoot
try {
  Write-Host "Resolving dependencies..."
  flutter pub get

  Write-Host "Generating Freezed and JSON files..."
  dart run build_runner build --delete-conflicting-outputs

  Write-Host "Formatting..."
  dart format .

  Write-Host "Analyzing..."
  flutter analyze

  Write-Host "Running tests..."
  flutter test
}
finally {
  Pop-Location
}

Write-Host "Astra AI Flutter foundation is ready."
