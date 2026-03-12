$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT
$python = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}
while ($true) {
  & $python "$ROOT\launcher.py"
  Start-Sleep -Seconds 3
}
