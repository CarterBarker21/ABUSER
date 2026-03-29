# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - TEST with discord

from pathlib import Path

ROOT = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'abuse' / 'gui' / 'assets'), 'abuse/gui/assets'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'abuse.app_paths',
        'abuse.gui.theme',
        'abuse.gui.config',
        'abuse.gui.main_window',
        'abuse.gui.bot_runner',
        'abuse.gui.components',
        'abuse.gui.pages',
        'abuse.gui.pages.base',
        'abuse.gui.pages.login',
        'abuse.gui.pages.guilds',
        'abuse.gui.pages.nuker',
        'abuse.gui.pages.dm',
        'abuse.gui.pages.logs',
        'abuse.gui.pages.settings',
        'abuse.gui.pages.docs',
        'abuse.gui.pages.joiner',
        'abuse.gui.pages.booster',
        'abuse.gui.token_finder_thread',
        'abuse.utils.token_finder',
        # Add discord
        'discord',
        'discord.ext',
        'discord.ext.commands',
        'aiohttp',
        'aiohttp.connector',
        'aiohttp.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'colorama', 'Crypto',
        'pytest', 'unittest', 'doctest',
        'tkinter', 'turtle', 'pydoc',
        'multiprocessing', 'concurrent.futures',
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
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ABUSER',
)
