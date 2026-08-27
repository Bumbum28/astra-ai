param(
    [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$versions = Join-Path $repoRoot "backend\alembic\versions"

if (-not (Test-Path (Join-Path $repoRoot "docker-compose.yml"))) {
    throw "Run this script from the Astra AI repository extracted with the repair patch."
}
if (-not (Test-Path $versions)) {
    throw "Alembic versions directory was not found: $versions"
}

$obsolete = @(
    "20260729_0003_character_persona_memory.py",
    "20260805_0004_rag_tool_foundation.py"
)

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $repoRoot "migration_backup\$stamp"

foreach ($name in $obsolete) {
    $path = Join-Path $versions $name
    if (Test-Path $path) {
        if (-not $SkipBackup) {
            New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
            Copy-Item $path (Join-Path $backupDir $name) -Force
        }
        Remove-Item $path -Force
        Write-Host "Removed obsolete rewritten migration: $name"
    }
}

$required = @(
    "20260718_0001_platform_foundation.py",
    "20260722_0002_chat_streaming_foundation.py",
    "20260722_0003_roleplay_profiles.py",
    "20260723_0004_memory_system.py",
    "20260827_0005_revised_roleplay_compatibility.py",
    "20260827_0006_rag_tool_foundation.py"
)

$missing = @()
foreach ($name in $required) {
    if (-not (Test-Path (Join-Path $versions $name))) {
        $missing += $name
    }
}
if ($missing.Count -gt 0) {
    throw "Repair is incomplete. Missing migration files: $($missing -join ', ')"
}

Write-Host ""
Write-Host "Astra AI migration files are now linear:"
Write-Host "20260718_0001 -> 20260722_0002 -> 20260722_0003 -> 20260723_0004 -> 20260827_0005 -> 20260827_0006"
if ((Test-Path $backupDir) -and (-not $SkipBackup)) {
    Write-Host "Obsolete migration backup: $backupDir"
}
