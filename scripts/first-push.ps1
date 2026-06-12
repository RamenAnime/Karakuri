# First push: you as the only contributor
# Run from the Karakuri folder after creating an empty repo at https://github.com/RamenAnime/Karakuri

param(
    [string]$Email = ""
)

$ErrorActionPreference = "Stop"

if (-not $Email) {
    Write-Host "Usage: .\scripts\first-push.ps1 -Email your-github-email@example.com"
    Write-Host ""
    Write-Host "Use the same email as your GitHub account (RamenAnime)."
    exit 1
}

git config user.name "RamenAnime"
git config user.email $Email

Write-Host "Git author set to RamenAnime <$Email>"
Write-Host ""

if (-not (git remote get-url origin 2>$null)) {
    git remote add origin https://github.com/RamenAnime/Karakuri.git
}

Write-Host "Pushing to https://github.com/RamenAnime/Karakuri ..."
git push -u origin main

Write-Host ""
Write-Host "Done. Check GitHub Insights > Contributors. Only RamenAnime should appear."
Write-Host "Repo description to paste: see .github/repo-description.txt"
