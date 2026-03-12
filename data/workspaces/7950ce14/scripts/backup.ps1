$ROOT = "C:\Users\Thinkpad\Desktop\KonstanceAI"
$STAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$DEST = "$ROOT\backups\snapshot-$STAMP"
New-Item -ItemType Directory -Force $DEST | Out-Null
Copy-Item "$ROOT\bot.py" "$DEST\bot.py" -Force -ErrorAction SilentlyContinue
Copy-Item "$ROOT\data\*" "$DEST\data\" -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "Backup written: $DEST"
