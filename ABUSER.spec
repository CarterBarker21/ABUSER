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
        # Config defaults (created at runtime if absent)
        (str(ROOT / 'config'), 'config'),
    ],
    hiddenimports=[
        # PyQt6 modules not always auto-detected
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # discord.py-self async internals
        'discord',
        'discord.ext',
        'discord.ext.commands',
        'aiohttp',
        'aiohttp.connector',
        'aiohttp.client',
        # dotenv
        'dotenv',
        # stdlib used at runtime
        'asyncio',
        'asyncio.windows_events',
        'json',
        'pathlib',
        'logging',
        'concurrent.futures',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test infrastructure — keeps the exe lean
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
        # Node / npm artefacts that sometimes get picked up
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
    console=False,          # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='path/to/icon.ico',  # add a .ico here when available
)
