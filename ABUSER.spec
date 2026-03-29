# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for ABUSER — ONE DIRECTORY build (prevents spawning issues)

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'abuse' / 'gui' / 'assets'), 'abuse/gui/assets'),
        (str(ROOT / 'config'), 'config'),
    ],
    hiddenimports=[
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'discord',
        'discord.ext',
        'discord.ext.commands',
        'aiohttp',
        'aiohttp.connector',
        'aiohttp.client',
        'dotenv',
        'asyncio',
        'asyncio.windows_events',
        'json',
        'pathlib',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        '_pytest',
        'pytest_qt',
        'pytestqt',
        'unittest',
        'doctest',
        'tkinter',
        'turtle',
        'xml.etree.ElementTree',
        'pydoc',
        'setuptools',
        'pkg_resources',
        'node_modules',
        'multiprocessing',
        'concurrent.futures.process',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ABUSER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ONE DIRECTORY mode - creates a folder with EXE inside
# This prevents the subprocess spawning that one-file mode causes
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ABUSER',
)
