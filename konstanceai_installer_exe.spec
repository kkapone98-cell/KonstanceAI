# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['konstanceai_installer_exe.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/Thinkpad/Desktop/KonstanceAI/.env', '.env'), ('C:/Users/Thinkpad/Desktop/KonstanceAI/telegram_token.txt', 'telegram_token.txt'), ('C:/Users/Thinkpad/Desktop/KonstanceAI/main.py', 'main.py'), ('C:/Users/Thinkpad/Desktop/KonstanceAI/scripts', 'scripts'), ('C:/Users/Thinkpad/Desktop/KonstanceAI/core', 'core'), ('C:/Users/Thinkpad/Desktop/KonstanceAI/memory', 'memory'), ('C:/Users/Thinkpad/Desktop/KonstanceAI/data', 'data')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='konstanceai_installer_exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
