$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$paths = @(
    "backend/app/tests/unit/test_intelligence_pipeline.py",
    "backend/app/tests/unit/test_memory_system.py",
    "backend/app/tests/unit/test_vietnamese_benchmark_dataset.py",
    "backend/app/tests/unit/test_chat_prompt_integration.py",
    "backend/app/tests/unit/test_roleplay_profiles.py",
    "backend/app/tests/integration/test_memory_api.py",
    "backend/app/tests/integration/test_roleplay_api.py"
)

foreach ($relativePath in $paths) {
    $path = Join-Path $repoRoot $relativePath
    if (Test-Path $path) {
        Remove-Item -Force $path
        Write-Host "Removed superseded test: $relativePath"
    }
}

Write-Host "Superseded Sprint 5 tests are no longer part of the active Sprint 7 suite."
