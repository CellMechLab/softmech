#!/usr/bin/env pwsh
# SoftMech UI Launcher - PowerShell Script
# Simple launcher for the SoftMech Designer UI

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Activate the virtual environment if it exists
$VenvActivate = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
} else {
    Write-Warning "Virtual environment not found at .venv"
    Write-Host "Please ensure you have activated the correct Python environment"
}

# Launch the UI
Write-Host "Launching SoftMech Designer UI..."
& python (Join-Path $ScriptDir "softmech_cli.py") ui

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to launch UI (exit code: $LASTEXITCODE)"
}
