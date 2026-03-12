$ROOT = "C:\Users\Thinkpad\Desktop\KonstanceAI"
Set-Location -LiteralPath $ROOT
python -m py_compile "$ROOT\bot.py"
python "$ROOT\scripts\stabilize_audit.py"
