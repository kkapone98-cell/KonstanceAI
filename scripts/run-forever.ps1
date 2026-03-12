$ROOT = "C:\Users\Thinkpad\Desktop\KonstanceAI"
Set-Location -LiteralPath $ROOT
while ($true) {
  python "$ROOT\bot.py"
  Start-Sleep -Seconds 3
}
