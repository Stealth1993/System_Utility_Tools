# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Mass_FTP.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python313\\DLLs\\tcl86t.dll', 'tcl'), ('C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python313\\DLLs\\tk86t.dll', 'tk'), ('C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\PIL', 'PIL')],
    hiddenimports=['qrcode', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'numpy', 'matplotlib', 'pandas', 'pygame'],
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
    name='MagicWormholeTransfer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Wormhole.ico'],
)
