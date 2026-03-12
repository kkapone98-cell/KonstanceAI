$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT

$python = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$targets = @("bot.py", "launcher.py", "openclaw_relay.py", "run-forever.ps1")

Get-CimInstance Win32_Process | Where-Object {
    $cmd = $_.CommandLine
    if (-not $cmd) { return $false }
    if (-not ($_.Name -match '^python(\.exe)?$' -or $_.Name -ieq 'powershell.exe')) { return $false }
    if (-not $cmd.Contains($ROOT)) { return $false }
    foreach ($target in $targets) {
        if ($cmd.Contains($target)) { return $true }
    }
    return $false
} | ForEach-Object {
    try {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    } catch {
    }
}

Start-Sleep -Milliseconds 600

& $python "$ROOT\launcher.py"
if ($LASTEXITCODE -eq 11) {
    Write-Host "KonstanceAI is already running. Keeping existing instance." -ForegroundColor Cyan
    exit 0
}
exit $LASTEXITCODE
