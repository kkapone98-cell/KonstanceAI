# KonstanceAI Verify & Test Script
# Run after 01_low_risk_autofix.ps1 - read-only diagnostics only

param(
    [string]$Root = "$PSScriptRoot"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

function Write-Step($msg) { Write-Host "" ; Write-Host "[>>] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  [XX] $msg" -ForegroundColor Red }

if (-not (Test-Path "$Root\bot.py")) {
    Write-Host "ERROR: bot.py not found in '$Root'" -ForegroundColor Red
    Write-Host "Usage: .\02_verify_and_test.ps1 -Root C:\path\to\KonstanceAI" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor White
Write-Host " KonstanceAI Verify & Test  (Root: $Root)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor White

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

# CHECK 1: Python version
Write-Step "CHECK 1 - Python version"
try {
    $pyVer = & $Python --version 2>&1
    Write-OK "Python: $pyVer"
} catch {
    Write-Fail "Python not found in PATH"
    exit 1
}

# CHECK 2: Required packages
Write-Step "CHECK 2 - Required packages"
foreach ($pkg in @("telegram", "dotenv", "requests")) {
    $result = & $Python -c "import $pkg; print('OK')" 2>&1
    if ("$result" -match "OK") {
        Write-OK "Installed: $pkg"
    } else {
        Write-Warn "Missing: $pkg - run: pip install -r requirements.txt"
    }
}

# CHECK 3: Syntax check all project .py files
Write-Step "CHECK 3 - Syntax check Python files"
$projectFiles = @(
    "$Root\bot.py",
    "$Root\launcher.py",
    "$Root\main.py",
    "$Root\scripts\__init__.py",
    "$Root\scripts\modules\__init__.py",
    "$Root\scripts\modules\smart_reply_engine.py"
)
$syntaxFail = $false
foreach ($f in $projectFiles) {
    if (Test-Path $f) {
        $out = & $Python -m py_compile $f 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "SYNTAX ERROR: $(Split-Path $f -Leaf) - $out"
            $syntaxFail = $true
        } else {
            Write-OK "Syntax OK: $(Split-Path $f -Leaf)"
        }
    } else {
        Write-Warn "Not found: $(Split-Path $f -Leaf)"
    }
}

# CHECK 4: Telegram token
Write-Step "CHECK 4 - Telegram token configured"
$envFile = "$Root\.env"
$tokenFile = "$Root\telegram_token.txt"
$envHasToken = $false
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "TELEGRAM_BOT_TOKEN=\S+") { $envHasToken = $true }
}

# CHECK 4B: Launcher preflight
Write-Step "CHECK 4B - Launcher preflight"
Push-Location $Root
$preflightOut = & $Python launcher\preflight.py 2>&1
Pop-Location
if ($LASTEXITCODE -eq 0) {
    Write-OK "Launcher preflight passed"
} else {
    Write-Warn "Launcher preflight reported issues:"
    $preflightOut | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
}
$fileHasToken = Test-Path $tokenFile
if ($envHasToken -or $fileHasToken) {
    Write-OK "Token found"
} else {
    Write-Fail "No token found in .env or telegram_token.txt"
}

# CHECK 5: OWNER_ID
Write-Step "CHECK 5 - OWNER_ID security"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "OWNER_ID=\d+") {
        Write-OK "OWNER_ID is set"
    } else {
        Write-Warn "OWNER_ID not set - any user can run owner commands"
        Write-Warn "Get your ID from @userinfobot on Telegram then add to .env: OWNER_ID=123456789"
    }
}

# CHECK 6: Bot lock status
Write-Step "CHECK 6 - Bot lock file"
$lockFile = "$Root\data\bot.lock"
if (Test-Path $lockFile) {
    $lockContent = Get-Content $lockFile -Raw -ErrorAction SilentlyContinue
    if ($lockContent -match "pid=(\d+)") {
        $lockedPid = [int]$Matches[1]
        $running = Get-Process -Id $lockedPid -ErrorAction SilentlyContinue
        if ($null -ne $running) {
            Write-OK "Bot is running (PID $lockedPid)"
        } else {
            Write-Warn "Stale lock (PID $lockedPid not running) - safe to clear"
        }
    } else {
        Write-OK "Lock file is empty"
    }
} else {
    Write-OK "No lock file - ready to start"
}

# CHECK 7: data/llm.json
Write-Step "CHECK 7 - Ollama model config"
$llmJson = "$Root\data\llm.json"
if (Test-Path $llmJson) {
    $llmContent = (Get-Content $llmJson -Raw).Trim()
    Write-OK "data/llm.json: $llmContent"
} else {
    Write-Warn "data/llm.json missing - run: Set-Content '$Root\data\llm.json' '{""fallback"":""qwen2.5:3b""}'"
}

# CHECK 8: Ollama running
Write-Step "CHECK 8 - Ollama local LLM"
try {
    $ollamaResp = Invoke-WebRequest -Uri "http://127.0.0.1:11434" -TimeoutSec 3 -ErrorAction Stop
    Write-OK "Ollama is running at 127.0.0.1:11434"
} catch {
    Write-Warn "Ollama not detected - bot will use echo fallback if OpenClaw also unavailable"
}

# CHECK 9: Unit tests
Write-Step "CHECK 9 - Unit tests"
$testsDir = "$Root\tests"
if (Test-Path $testsDir) {
    Push-Location $Root
    $testOut = & $Python -m unittest discover -s tests -v 2>&1
    Pop-Location
    if ($LASTEXITCODE -eq 0) {
        Write-OK "All tests passed"
        $testOut | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    } else {
        Write-Warn "Some tests failed:"
        $testOut | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    }
} else {
    Write-Warn "tests/ directory not found - run FIX 5 from the autofix script"
}

# CHECK 10: Multiple Python processes
Write-Step "CHECK 10 - Python process count"
$pyProcs = Get-Process -Name "python*" -ErrorAction SilentlyContinue
if ($null -eq $pyProcs) {
    Write-OK "No Python processes running - safe to start"
} elseif (@($pyProcs).Count -eq 1) {
    Write-OK "One Python process running (expected if bot is active)"
} else {
    Write-Warn "$(@($pyProcs).Count) Python processes running - verify only ONE is the bot"
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor White
if (-not $syntaxFail) {
    Write-Host " VERIFICATION PASSED" -ForegroundColor Green
} else {
    Write-Host " VERIFICATION - ISSUES FOUND (see above)" -ForegroundColor Yellow
}
Write-Host "============================================================" -ForegroundColor White
Write-Host ""
Write-Host "  Start bot: $Python launcher.py" -ForegroundColor Gray
Write-Host "  Run tests: $Python -m unittest discover -s tests -v" -ForegroundColor Gray
Write-Host ""