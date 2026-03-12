# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets\\images\\ico4.ico', 'assets\\images'), ('assets\\images\\icon.ico', 'assets\\images'), ('assets\\images\\logo.png', 'assets\\images'), ('assets\\images\\Portal  WG ico.png', 'assets\\images'), ('assets\\images\\Zapret.bat.png', 'assets\\images'), ('assets\\images\\Zapret2.ico', 'assets\\images'), ('config.json', '.'), ('processes_to_kill.txt', '.')],
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
    name='Permissiveness',
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
    icon=['assets\\images\\ico4.ico'],
)
