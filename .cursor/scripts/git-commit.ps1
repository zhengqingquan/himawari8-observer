#Requires -Version 5.1
<#
.SYNOPSIS
    Stage and commit changes. Never pushes to remote.

.PARAMETER Message
    Commit message (required).

.PARAMETER Files
    Optional list of paths to stage. If omitted, stages all modified tracked files
    (git add -u). Untracked files are never auto-staged unless listed in -Files.

.EXAMPLE
    .\.cursor\scripts\git-commit.ps1 -Message "fix: remove invalid import" -Files src/main.py,src/dl/dlpic.py

.EXAMPLE
    .\.cursor\scripts\git-commit.ps1 -Message "Update requirements"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    [Parameter(Mandatory = $false)]
    [string[]]$Files
)

$ErrorActionPreference = "Stop"

# .cursor/scripts/git-commit.ps1 -> repo root (up 3 levels)
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
Set-Location $repoRoot

function Invoke-Git {
    param([string[]]$GitArgs)
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

Write-Host "==> git status"
Invoke-Git @("status", "--short")

$blockedPatterns = @(
    '\.env$',
    'credentials\.json$',
    '\.pid$',
    '\.har$'
)

if ($Files -and $Files.Count -gt 0) {
    foreach ($f in $Files) {
        foreach ($pat in $blockedPatterns) {
            if ($f -match $pat) {
                throw "Refusing to stage blocked path: $f (matches /$pat/)"
            }
        }
    }
    Write-Host "==> git add $($Files -join ', ')"
    Invoke-Git (@("add", "--") + $Files)
} else {
    Write-Host "==> git add -u (tracked modifications only)"
    Invoke-Git @("add", "-u")
}

$staged = & git diff --cached --name-only
if (-not $staged) {
    Write-Host "Nothing staged. Aborting commit (no empty commit)."
    Invoke-Git @("status", "--short")
    exit 1
}

Write-Host "==> staged files:"
$staged | ForEach-Object { Write-Host "  $_" }

Write-Host "==> git commit"
# Use -m only; do not push.
& git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    throw "git commit failed with exit code $LASTEXITCODE"
}

Write-Host "==> git status (after commit)"
Invoke-Git @("status", "--short")
Write-Host "Done. (No push performed.)"
