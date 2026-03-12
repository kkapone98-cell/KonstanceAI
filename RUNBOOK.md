# Konstance RUNBOOK

## Startup (single-instance)
1) Start ONE bot instance only.
2) Start ONE autonomy dispatcher only.
3) Confirm /status and queue processing.

## Never do
- Don’t run manual bot + scheduled bot simultaneously.
- Don’t patch bot.py inline repeatedly.
- Don’t paste live tokens in chat.

## Safe change flow
1) Edit module file in scripts/ or agents/
2) Compile: python -m py_compile <file>
3) Run module test
4) Verify in Telegram
5) Backup if stable

## Emergency recovery
1) Stop all python
2) Restore latest known-good bot.py
3) Compile + start single bot

## Daily checks
- /status
- /jobs
- /money_menu
- /best_play

