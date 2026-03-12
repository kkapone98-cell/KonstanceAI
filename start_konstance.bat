@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\start_konstance.ps1"
if errorlevel 1 pause
