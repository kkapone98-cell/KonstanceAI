$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT
powershell -NoProfile -ExecutionPolicy Bypass -File "$ROOT\launcher\start_konstance.ps1"
