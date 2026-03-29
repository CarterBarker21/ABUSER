# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for ABUSER — single-file windowed exe (no console)

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # SVG icon assets
        (str(ROOT / 'abuse' / 'gui' / 'assets'), 'abuse/gui/assets'),
        # Config defaults
        (str(ROOT / 'config'), 'config'),
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # discord.py-self
        'discord',
        'discord.ext',
        'discord.ext.commands',
        'aiohttp',
        'aiohttp.connector',
        'aiohttp.client',
        # dotenv
        'dotenv',
        # stdlib
        'asyncio',
        'asyncio.windows_events',
        'json',
        'pathlib',
        'logging',
        'concurrent.futures',
        # multiprocessing for single-instance check
        'multiprocessing',
        'multiprocessing.reduction',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test infrastructure
        'pytest',
        '_pytest',
        'pytest_qt',
        'pytestqt',
        'unittest',
        'doctest',
        # Unused stdlib
        'tkinter',
        'turtle',
        'xml.etree.ElementTree',
        'pydoc',
        'setuptools',
        'pkg_resources',
        'node_modules',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ABUSER',
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
