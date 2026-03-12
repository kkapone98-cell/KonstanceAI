$ROOT = "C:\Users\Thinkpad\Desktop\KonstanceAI"
Set-Location -LiteralPath $ROOT
while ($true) {
  python "$ROOT\scripts\cloud_relay_probe.py" | Out-File -FilePath "$ROOT\logs\cloud-probe-last.log" -Encoding utf8 -Force
  Start-Sleep -Seconds 120
}
