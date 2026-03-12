$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT
while ($true) {
  python "$ROOT\launcher.py"
  Start-Sleep -Seconds 3
}
