# KARAKURI Windows 11 setup
# Run from repo root: .\scripts\install-windows.ps1

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "KARAKURI Windows installer"
Write-Host "  Root: $RepoRoot"
Write-Host ""

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists git)) {
    Write-Error "Git not found. Install Git for Windows: https://git-scm.com/download/win"
}

$PythonCmd = $null
foreach ($candidate in @("python", "py")) {
    if (Test-CommandExists $candidate) {
        $PythonCmd = $candidate
        break
    }
}
if (-not $PythonCmd) {
    Write-Error "Python not found. Install Python 3.11+ and ensure it is on PATH."
}

if ($PythonCmd -eq "py") {
    $versionOutput = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
} else {
    $versionOutput = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
}
$parts = $versionOutput.Trim().Split(".")
$major = [int]$parts[0]
$minor = [int]$parts[1]
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    Write-Error "Python 3.10+ required (found $versionOutput). Install 3.11 or 3.12."
}
Write-Host "  Python: $versionOutput"

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..."
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force ".venv"
    }
    if ($PythonCmd -eq "py") {
        & py -3 -m venv .venv
    } else {
        & python -m venv .venv
    }
}

$pip = Join-Path $RepoRoot ".venv\Scripts\pip.exe"
$python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

Write-Host "Installing package (editable, dev extras)..."
& $python -m pip install --upgrade pip setuptools wheel
& $pip install -e ".[dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host ""
Write-Host "Running karakuri doctor..."
& $python -m karakuri doctor
$doctorExit = $LASTEXITCODE

Write-Host ""
Write-Host "Next steps:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  karakuri doctor"
Write-Host "  karakuri stop          # test kill switch"
Write-Host "  karakuri stop --clear"
Write-Host "  pytest"
Write-Host ""
Write-Host "Windows guide: docs/WINDOWS.md"
Write-Host "GitHub setup:  docs/GITHUB.md"

if ($doctorExit -ne 0) {
    Write-Host ""
    Write-Warning "doctor reported issues (exit $doctorExit). See output above."
    exit $doctorExit
}
