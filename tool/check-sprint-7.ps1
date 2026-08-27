$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."

Write-Host "[Sprint 7] Checking Alembic head..."
$heads = docker compose run --rm --entrypoint alembic backend heads
$heads | Write-Host
if (($heads | Select-String "20260828_0007 \(head\)").Count -ne 1) {
    throw "Expected exactly one Sprint 7 Alembic head: 20260828_0007."
}

Write-Host "[Sprint 7] Checking current database revision..."
docker compose run --rm --entrypoint alembic backend current

Write-Host "[Sprint 7] Running backend test profile..."
docker compose --profile test run --rm backend-test

Write-Host "[Sprint 7] Running Flutter checks..."
Push-Location frontend
try {
    flutter pub get
    dart format --output=none --set-exit-if-changed .
    flutter analyze
    flutter test
}
finally {
    Pop-Location
}

Write-Host "Sprint 7 checks completed."
