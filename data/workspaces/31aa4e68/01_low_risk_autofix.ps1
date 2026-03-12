# KonstanceAI Repair Script 1 - Low-Risk Automated Fixes
# Save this as 01_low_risk_autofix.ps1 in your KonstanceAI folder

param(
    [string]$Root = "$PSScriptRoot"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "" ; Write-Host "[>>] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!!] $msg" -ForegroundColor Yellow }

function Backup-File($path) {
    $ts  = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $bak = "$path.bak.$ts"
    Copy-Item -Path $path -Destination $bak -Force
    Write-OK "Backed up: $(Split-Path $path -Leaf) -> $([System.IO.Path]::GetFileName($bak))"
    return $bak
}

function Compile-Check($pyFile) {
    $result = & python -m py_compile $pyFile 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Compile check FAILED for $pyFile"
        Write-Warn "$result"
        return $false
    }
    return $true
}

if (-not (Test-Path "$Root\bot.py")) {
    Write-Host "ERROR: bot.py not found in '$Root'" -ForegroundColor Red
    Write-Host "Usage: .\01_low_risk_autofix.ps1 -Root C:\path\to\KonstanceAI" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor White
Write-Host " KonstanceAI Low-Risk Auto-Fix  (Root: $Root)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor White

# FIX 1: Clear stale bot.lock
Write-Step "FIX 1 - Clear stale bot.lock"
$lockFile = "$Root\data\bot.lock"
if (Test-Path $lockFile) {
    $content = Get-Content $lockFile -Raw -ErrorAction SilentlyContinue
    if ($content -match "pid=(\d+)") {
        $lockedPid = [int]$Matches[1]
        $running = Get-Process -Id $lockedPid -ErrorAction SilentlyContinue
        if ($null -eq $running) {
            Backup-File $lockFile
            Clear-Content $lockFile
            Write-OK "Stale lock cleared (PID $lockedPid not running)"
        } else {
            Write-Warn "Bot is running as PID $lockedPid - stop it first then re-run"
        }
    } else {
        Backup-File $lockFile
        Clear-Content $lockFile
        Write-OK "Lock file cleared (no valid PID found)"
    }
} else {
    Write-OK "No lock file found - nothing to clear"
}

# FIX 2: Normalize CRLF to LF in all .py files
Write-Step "FIX 2 - Normalize line endings (CRLF to LF) in Python files"
$pyFiles = Get-ChildItem -Path $Root -Filter "*.py" -Recurse | Where-Object { $_.FullName -notmatch "\\.git\\" }
foreach ($file in $pyFiles) {
    $raw = [System.IO.File]::ReadAllBytes($file.FullName)
    $hasCRLF = $false
    for ($i = 0; $i -lt ($raw.Length - 1); $i++) {
        if ($raw[$i] -eq 13 -and $raw[$i+1] -eq 10) { $hasCRLF = $true; break }
    }
    if ($hasCRLF) {
        Backup-File $file.FullName | Out-Null
        $text = [System.IO.File]::ReadAllText($file.FullName)
        $text = $text -replace "`r`n", "`n"
        if ($text.StartsWith([char]0xFEFF)) { $text = $text.Substring(1) }
        [System.IO.File]::WriteAllText($file.FullName, $text, [System.Text.UTF8Encoding]::new($false))
        Write-OK "Normalized: $($file.Name)"
    }
}

# FIX 3: Create data/llm.json if missing
Write-Step "FIX 3 - Ensure data/llm.json exists"
$llmJson = "$Root\data\llm.json"
if (-not (Test-Path $llmJson)) {
    $llmContent = '{ "fallback": "qwen2.5:3b" }'
    Set-Content -Path $llmJson -Value $llmContent -Encoding UTF8
    Write-OK "Created data/llm.json with default model: qwen2.5:3b"
} else {
    Write-OK "data/llm.json already exists - skipped"
}

# FIX 4: Guard main.py against accidental execution
Write-Step "FIX 4 - Add runtime guard to legacy main.py"
$mainPy = "$Root\main.py"
if (Test-Path $mainPy) {
    $mainContent = Get-Content $mainPy -Raw
    if ($mainContent -notmatch "LEGACY_GUARD_ADDED") {
        Backup-File $mainPy
        $guard = "# LEGACY_GUARD_ADDED`nimport sys`nprint('ERROR: main.py is a legacy stub. Run: python launcher.py')`nsys.exit(1)`n`n"
        $newContent = $guard + $mainContent
        [System.IO.File]::WriteAllText($mainPy, $newContent, [System.Text.UTF8Encoding]::new($false))
        Write-OK "Added runtime guard to main.py"
    } else {
        Write-OK "main.py guard already in place - skipped"
    }
} else {
    Write-Warn "main.py not found - skipped"
}

# FIX 5: Create tests scaffold if missing
Write-Step "FIX 5 - Create tests/ scaffold"
$testsDir = "$Root\tests"
if (-not (Test-Path $testsDir)) {
    New-Item -ItemType Directory -Path $testsDir | Out-Null
    Write-OK "Created tests/ directory"
}

$testInit = "$testsDir\__init__.py"
if (-not (Test-Path $testInit)) {
    Set-Content -Path $testInit -Value "# tests package" -Encoding UTF8
    Write-OK "Created tests/__init__.py"
}

$testBot = "$testsDir\test_bot_config.py"
if (-not (Test-Path $testBot)) {
$testBotContent = @'
import os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class TestBotConfig(unittest.TestCase):
    def test_root_exists(self):
        self.assertTrue(ROOT.exists())
    def test_bot_py_exists(self):
        self.assertTrue((ROOT / "bot.py").exists())
    def test_launcher_py_exists(self):
        self.assertTrue((ROOT / "launcher.py").exists())
    def test_token_present(self):
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        env_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        file_token = (ROOT / "telegram_token.txt").exists()
        self.assertTrue(bool(env_token) or file_token)
    def test_data_dir(self):
        d = ROOT / "data"
        d.mkdir(parents=True, exist_ok=True)
        self.assertTrue(d.is_dir())

if __name__ == "__main__":
    unittest.main()
'@
    Set-Content -Path $testBot -Value $testBotContent -Encoding UTF8
    Write-OK "Created tests/test_bot_config.py"
}

$testEngine = "$testsDir\test_smart_reply_engine.py"
if (-not (Test-Path $testEngine)) {
$testEngineContent = @'
import os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.modules.smart_reply_engine import style_text, smart_reply

class TestStyleText(unittest.TestCase):
    def test_short_truncates(self):
        result = style_text("x" * 1000, {"verbosity": "short"})
        self.assertLessEqual(len(result), 910)
    def test_medium_truncates(self):
        result = style_text("y" * 3000, {"verbosity": "medium"})
        self.assertLessEqual(len(result), 2410)
    def test_long_no_truncation(self):
        result = style_text("z" * 3000, {"verbosity": "long"})
        self.assertEqual(len(result), 3000)
    def test_empty_returns_placeholder(self):
        self.assertEqual(style_text("", {}), "...")

class TestFallback(unittest.TestCase):
    def test_echo_fallback(self):
        os.environ.pop("OPENCLAW_RELAY_URL", None)
        result = smart_reply("hello world", {"verbosity": "medium"}, {})
        self.assertIn("hello world", result)

if __name__ == "__main__":
    unittest.main()
'@
    Set-Content -Path $testEngine -Value $testEngineContent -Encoding UTF8
    Write-OK "Created tests/test_smart_reply_engine.py"
}

# FIX 6: Check OWNER_ID
Write-Step "FIX 6 - Check OWNER_ID security setting"
$envFile = "$Root\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -notmatch "OWNER_ID=\d+") {
        Write-Warn "OWNER_ID is NOT set - any Telegram user can run owner commands!"
        Write-Warn "Get your ID from @userinfobot on Telegram, then add to .env:"
        Write-Warn "  OWNER_ID=123456789"
    } else {
        Write-OK "OWNER_ID is set in .env"
    }
}

# FIX 7: Update .env.example
Write-Step "FIX 7 - Update .env.example"
$envExamplePath = "$Root\.env.example"
$envExampleContent = "# KonstanceAI Environment Config`n# Copy to .env and fill in values`n`nTELEGRAM_BOT_TOKEN=your_token_here`nOWNER_ID=your_telegram_user_id`nOPENCLAW_RELAY_URL=ws://127.0.0.1:18789`nOPENCLAW_RELAY_TOKEN=your_relay_token_here`n"
Set-Content -Path $envExamplePath -Value $envExampleContent -Encoding UTF8
Write-OK "Updated .env.example"

# FIX 8: Final syntax check
Write-Step "FIX 8 - Syntax compile check on all Python files"
$allPassed = $true
foreach ($file in $pyFiles) {
    $ok = Compile-Check $file.FullName
    if ($ok) {
        Write-OK "Syntax OK: $($file.Name)"
    } else {
        $allPassed = $false
    }
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor White
if ($allPassed) {
    Write-Host " REPAIR COMPLETE - All checks passed" -ForegroundColor Green
} else {
    Write-Host " REPAIR COMPLETE - Some syntax checks failed, review above" -ForegroundColor Yellow
}
Write-Host "============================================================" -ForegroundColor White
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "  1. pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "  2. Add OWNER_ID to .env (get from @userinfobot on Telegram)" -ForegroundColor Gray
Write-Host "  3. python -m unittest discover -s tests -v" -ForegroundColor Gray
Write-Host "  4. python launcher.py" -ForegroundColor Gray
Write-Host ""