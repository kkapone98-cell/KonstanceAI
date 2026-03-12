$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT

$python = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

New-Item -ItemType Directory -Force -Path (Join-Path $ROOT "logs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ROOT "data") | Out-Null

& $python "$ROOT\launcher\preflight.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Preflight failed. Fix the reported issues before starting KonstanceAI." -ForegroundColor Red
    exit 1
}

Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\run-forever.ps1`"" -WindowStyle Normal | Out-Null
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\start-worker.ps1`"" -WindowStyle Minimized | Out-Null
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\start-cloud-monitor.ps1`"" -WindowStyle Minimized | Out-Null

Write-Host "KonstanceAI launcher started: supervisor, worker, and cloud monitor."
