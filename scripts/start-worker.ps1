$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT
$python = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}
New-Item -ItemType Directory -Force -Path "$ROOT\logs" | Out-Null
& $python -m scripts.job_worker
