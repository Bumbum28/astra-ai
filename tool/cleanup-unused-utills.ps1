$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$unusedPath = Join-Path $projectRoot "backend\app\utills"

if (Test-Path $unusedPath) {
    Remove-Item $unusedPath -Recurse -Force
    Write-Host "Removed unused backend/app/utills directory."
} else {
    Write-Host "No unused backend/app/utills directory was found."
}
