# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


datas = [('assets\\logo.png', 'assets'), ('assets\\logo.ico', 'assets'), ('assets\\app_icon.ico', 'assets')]
if Path('assets/icons').exists():
    datas.append(('assets\\icons', 'assets\\icons'))

icon_path = 'assets\\icons\\docfill.ico' if Path('assets/icons/docfill.ico').exists() else 'assets\\app_icon.ico'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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
    name='DOCFILL PRO',
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
    icon=icon_path,
)
