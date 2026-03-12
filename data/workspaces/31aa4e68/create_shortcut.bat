@echo off
setlocal

:: Create desktop shortcut for KonstanceAI (use when already installed)
set INSTALL_DIR=%~dp0
set INSTALL_DIR=%INSTALL_DIR:~0,-1%

echo Creating KonstanceAI desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\KonstanceAI.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\start_konstance.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%SystemRoot%\System32\SHELL32.dll,149'; $Shortcut.Save()"

echo.
echo Done. Double-click KonstanceAI.lnk on your desktop to start.
pause

endlocal
