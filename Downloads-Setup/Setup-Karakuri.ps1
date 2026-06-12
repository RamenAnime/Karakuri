# Creates Downloads\Karakuri and installs KARAKURI
# Right-click > Run with PowerShell   OR   paste into Windows Terminal

param(
    [Parameter(Mandatory = $true)]
    [string]$Email
)

$ErrorActionPreference = "Stop"
$Karakuri = Join-Path $env:USERPROFILE "Downloads\Karakuri"

Write-Host "KARAKURI setup" -ForegroundColor Cyan
Write-Host "Target folder: $Karakuri"
Write-Host ""

New-Item -ItemType Directory -Force -Path $Karakuri | Out-Null
Set-Location $Karakuri

git config --global user.name "RamenAnime"
git config --global user.email $Email

if (Test-Path (Join-Path $Karakuri ".git")) {
    Write-Host "Git repo already present."
} else {
    Write-Host "Cloning from GitHub..."
    git clone https://github.com/RamenAnime/Karakuri.git .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Clone failed (repo may be empty). Initializing local repo..." -ForegroundColor Yellow
        git init -b main
        git remote add origin https://github.com/RamenAnime/Karakuri.git
    }
}

Write-Host "Creating Python venv..."
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -e ".[dev,research]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

python -m karakuri doctor

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Folder:  $Karakuri"
Write-Host "Cursor:  File > Open Folder > Downloads > Karakuri"
Write-Host ""
Write-Host "If GitHub was empty, copy project files here then run:"
Write-Host "  git add -A"
Write-Host "  git commit -m `"Initial KARAKURI fusion stack`""
Write-Host "  git push -u origin main"
