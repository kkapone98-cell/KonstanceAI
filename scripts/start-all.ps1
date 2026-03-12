$ROOT = "C:\Users\Thinkpad\Desktop\KonstanceAI"
Set-Location -LiteralPath $ROOT

Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\run-forever.ps1`"" -WindowStyle Normal
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\start-worker.ps1`"" -WindowStyle Normal

Write-Host "Konstance supervisor started: bot + worker"
