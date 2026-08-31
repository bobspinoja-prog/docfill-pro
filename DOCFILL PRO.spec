# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


datas = []
if Path('assets').exists():
    datas.append(('assets', 'assets'))
for data_file in (
    'mappings.json',
    'template_semantic_mappings.json',
    'template_profiles.json',
    'history.json',
    'user_session.json',
):
    source = Path('data') / data_file
    if source.exists():
        datas.append((str(source), 'data'))

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
