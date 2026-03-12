param(
    [string]$WorktreePath = "",
    [string]$RootRepoPath = "$env:USERPROFILE\Desktop\KonstanceAI",
    [string]$TargetBranch = "main",
    [string]$CommitMessage = "Apply Cursor AI changes",
    [switch]$SkipCommit,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [string]$RepoPath,
        [string[]]$Args
    )

    Push-Location $RepoPath
    try {
        $output = & git @Args 2>&1
        $code = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    if ($code -ne 0) {
        $joined = ($Args -join " ")
        throw "git $joined failed in '$RepoPath':`n$output"
    }

    return $output
}

function Test-IsGitRepo {
    param([string]$RepoPath)
    try {
        $result = Invoke-Git -RepoPath $RepoPath -Args @("rev-parse", "--is-inside-work-tree")
        return (($result -join "`n").Trim() -eq "true")
    }
    catch {
        return $false
    }
}

function Resolve-WorktreePath {
    param(
        [string]$RequestedPath,
        [string]$RootPath
    )

    if ($RequestedPath -and (Test-Path $RequestedPath)) {
        return $RequestedPath
    }

    # Preferred source: git's own registered worktree list.
    try {
        $raw = Invoke-Git -RepoPath $RootPath -Args @("worktree", "list", "--porcelain")
        $lines = (($raw -join "`n") -split "`r?`n")
        $paths = @()
        foreach ($line in $lines) {
            if ($line -match "^worktree\s+(.+)$") {
                $paths += $Matches[1].Trim()
            }
        }

        $rootResolved = [IO.Path]::GetFullPath($RootPath).TrimEnd("\")
        foreach ($p in $paths) {
            $resolved = [IO.Path]::GetFullPath($p).TrimEnd("\")
            if ($resolved -ne $rootResolved -and (Test-Path $resolved) -and (Test-IsGitRepo -RepoPath $resolved)) {
                return $resolved
            }
        }
    }
    catch {
    }

    # Fallback: scan common Cursor worktree folder.
    $cursorBase = Join-Path $env:USERPROFILE ".cursor\worktrees\KonstanceAI"
    if (Test-Path $cursorBase) {
        $candidates = Get-ChildItem -Path $cursorBase -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending
        foreach ($dir in $candidates) {
            if (Test-IsGitRepo -RepoPath $dir.FullName) {
                return $dir.FullName
            }
        }
    }

    return ""
}

if (-not (Test-Path $RootRepoPath)) {
    throw "Root repo path does not exist: $RootRepoPath"
}

$WorktreePath = Resolve-WorktreePath -RequestedPath $WorktreePath -RootPath $RootRepoPath
if (-not $WorktreePath) {
    throw "Could not auto-detect a Cursor worktree path. Pass -WorktreePath explicitly."
}
if (-not (Test-IsGitRepo -RepoPath $WorktreePath)) {
    throw "Worktree path is not a git repo: $WorktreePath"
}
if (-not (Test-IsGitRepo -RepoPath $RootRepoPath)) {
    throw "Root repo path is not a git repo: $RootRepoPath"
}

Write-Host "Worktree: $WorktreePath" -ForegroundColor Cyan
Write-Host "Root repo: $RootRepoPath" -ForegroundColor Cyan
Write-Host "Target branch: $TargetBranch" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "DryRun enabled. Detection succeeded; no git changes made." -ForegroundColor DarkYellow
    return
}

if (-not $SkipCommit) {
    $status = Invoke-Git -RepoPath $WorktreePath -Args @("status", "--porcelain")
    $hasChanges = (($status -join "`n").Trim().Length -gt 0)

    if ($hasChanges) {
        Write-Host "Committing worktree changes..." -ForegroundColor Yellow
        Invoke-Git -RepoPath $WorktreePath -Args @("add", "-A") | Out-Null
        Invoke-Git -RepoPath $WorktreePath -Args @("commit", "-m", $CommitMessage) | Out-Null
    }
    else {
        Write-Host "No uncommitted changes in worktree; using current HEAD." -ForegroundColor DarkYellow
    }
}
else {
    Write-Host "SkipCommit enabled; using current worktree HEAD." -ForegroundColor DarkYellow
}

$hash = (Invoke-Git -RepoPath $WorktreePath -Args @("rev-parse", "HEAD") | Select-Object -Last 1).Trim()
if (-not $hash) {
    throw "Could not determine worktree HEAD commit hash."
}

Write-Host "Applying commit $hash to root repo..." -ForegroundColor Yellow
Invoke-Git -RepoPath $RootRepoPath -Args @("checkout", $TargetBranch) | Out-Null

try {
    Invoke-Git -RepoPath $RootRepoPath -Args @("cherry-pick", $hash) | Out-Null
}
catch {
    Write-Host "Cherry-pick failed, likely due to conflicts." -ForegroundColor Red
    Write-Host "Resolve conflicts in: $RootRepoPath" -ForegroundColor Red
    Write-Host "Then run: git add -A ; git cherry-pick --continue" -ForegroundColor Red
    throw
}

Write-Host ""
Write-Host "Done. Cursor worktree changes are now in the root repo." -ForegroundColor Green
Write-Host "Root: $RootRepoPath" -ForegroundColor Green
Write-Host "Commit: $hash" -ForegroundColor Green
