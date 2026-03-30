#!/usr/bin/env python3
"""ABUSER Bot - GUI Entry Point"""

import sys
import os

# CRITICAL: Prevent any subprocess spawning during imports (PyInstaller issue)
# Must be before ANY other imports
if __name__ == '__main__':
    # Block multiprocessing fork/spawn attempts
    if '--multiprocessing-fork' in sys.argv:
        sys.exit(0)
    
    # Set env vars to prevent subprocess spawning from discord/aiohttp
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['AIOHTTP_NO_PLUGINS'] = '1'
    
    # Windows: Hide console windows from subprocesses
    if sys.platform == 'win32':
        # Prevent console window creation by subprocesses
        import subprocess
        subprocess._USE_VFORK = False
        subprocess._USE_POSIX_SPAWN = False
        
        # Create mutex for single instance
        import ctypes
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "ABUSER_APP_SINGLE_INSTANCE")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    
    # freeze_support for PyInstaller
    if getattr(sys, 'frozen', False):
        import multiprocessing
        multiprocessing.freeze_support()

    from pathlib import Path
    
    # Single instance check
    lock_file = Path(__file__).parent / "data" / ".abuser.lock"
    fd = None
    try:
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        fd = open(lock_file, 'w')
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
    except (IOError, OSError, ImportError) as exc:
        print(f"[!] Failed to acquire single-instance lock: {exc}")
        sys.exit(1)
    
    # Bootstrap
    from abuse.app_paths import bootstrap_runtime_layout, env_file_path
    bootstrap_runtime_layout()
    
    # Environment
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file_path(), override=False)
    except ImportError:
        pass
    
    # GUI imports
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
    
    from abuse.gui import MainWindow, get_theme_manager
    from abuse.gui.config import load_gui_config
    # Import BotRunner lazily to avoid early discord import
    from abuse.gui.bot_runner import BotRunner
    
    # Setup app
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("ABUSER Bot")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ABUSER")
    
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    
    # Theme
    theme_manager = get_theme_manager()
    appearance = load_gui_config().get("appearance", {})
    theme_manager.switch_theme(
        appearance.get("preset", "Discord Dark"),
        appearance.get("accent", "Red").lower().replace(" ", "_"),
    )
    theme_manager.apply_theme(app)
    
    # Main window
    window = MainWindow()
    window.load_and_apply_settings()
    
    # Wire EVERYTHING before showing
    bot_runner = BotRunner(parent=window)
    window.connect_bot_runner(bot_runner)
    
    # Defer show to let Qt finish layout/style polish
    def _show_main_window():
        window.show()
        window.raise_()
        window.activateWindow()
    
    QTimer.singleShot(0, _show_main_window)
    
    print("[*] ABUSER Bot GUI started")
    print("[*] Please enter your token in the Login tab to connect")
    
    def on_exit():
        try:
            if bot_runner and bot_runner.is_running:
                print("[*] Shutting down bot...")
                bot_runner.stop_bot()
        except Exception as exc:
            print(f"[!] Bot shutdown error: {exc}")
        finally:
            try:
                if 'fd' in locals() and fd is not None and not fd.closed:
                    fd.close()
            except Exception:
                pass
            try:
                lock_file.unlink(missing_ok=True)
            except Exception:
                pass
    
    import atexit
    atexit.register(on_exit)
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        on_exit()
        sys.exit(0)
