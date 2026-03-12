@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo    KonstanceAI - One-Click Installer
echo ============================================
echo.

:: Configuration
set REPO_URL=https://github.com/kkapone98-cell/konsanse
set INSTALL_DIR=%USERPROFILE%\KonstanceAI
set BRANCH=ai-fixes-backup

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ from python.org
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/6] Python found.

:: Check for Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found. Please install Git from git-scm.com
    echo Download: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [2/6] Git found.

:: Remove old install if exists
if exist "%INSTALL_DIR%" (
    echo [3/6] Removing old installation...
    rmdir /s /q "%INSTALL_DIR%"
)

:: Clone repository
echo [4/6] Cloning KonstanceAI (branch: %BRANCH%)...
git clone --branch %BRANCH% --single-branch %REPO_URL% "%INSTALL_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to clone repository.
    pause
    exit /b 1
)

cd /d "%INSTALL_DIR%"

:: Install dependencies
echo [5/6] Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Check for token file
if not exist "telegram_token.txt" (
    echo.
    echo ============================================
    echo    TELEGRAM BOT TOKEN REQUIRED
echo ============================================
    echo.
    echo To get your token:
    echo 1. Message @BotFather on Telegram
echo 2. Send /newbot and follow instructions
echo 3. Copy the token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
    echo.
    set /p TOKEN="Enter your Telegram Bot Token: "
    echo !TOKEN! > telegram_token.txt
    echo.
    echo [OK] Token saved to telegram_token.txt
)

:: Create desktop shortcut for launcher
echo [6/6] Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\KonstanceAI.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\launcher.py'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%SystemRoot%\System32\SHELL32.dll,149'; $Shortcut.Save()"

echo.
echo ============================================
echo    INSTALLATION COMPLETE!
echo ============================================
echo.
echo Location: %INSTALL_DIR%
echo.
echo To start your bot:
echo   - Double-click KonstanceAI.lnk on your desktop
echo   - OR run: python "%INSTALL_DIR%\launcher.py"
echo.
echo To edit settings:
echo   - Open: %INSTALL_DIR%\.env
echo.
pause

:: Optional: Start immediately
set /p START_NOW="Start bot now? (y/n): "
if /i "%START_NOW%"=="y" (
    echo.
    echo Starting KonstanceAI...
    python launcher.py
)

endlocal
