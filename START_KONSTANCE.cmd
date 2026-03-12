@echo off
setlocal
set ROOT=%~dp0
cd /d "%ROOT%"
echo Starting Konstance stack...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%launcher\start_konstance.ps1"
echo.
echo If this window closes, reopen START_KONSTANCE.cmd to restart everything.
pause
