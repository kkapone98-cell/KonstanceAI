$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT
$python = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}
New-Item -ItemType Directory -Force -Path "$ROOT\logs" | Out-Null
while ($true) {
  & $python "$ROOT\scripts\cloud_relay_probe.py" | Out-File -FilePath "$ROOT\logs\cloud-probe-last.log" -Encoding utf8 -Force
  Start-Sleep -Seconds 120
}
