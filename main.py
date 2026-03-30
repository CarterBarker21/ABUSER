#!/usr/bin/env python3
"""ABUSER Bot - GUI Entry Point"""

import sys

# CRITICAL: Must be first to prevent subprocess spawning in PyInstaller builds
if __name__ == '__main__':
    from multiprocessing import spawn
    if spawn.is_forking(sys.argv) or "--multiprocessing-fork" in sys.argv:
        sys.exit(0)
    # Windows single-instance guard (prevents brief duplicate windows)
    if sys.platform == "win32":
        import ctypes
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "ABUSER_APP_SINGLE_INSTANCE")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            sys.exit(0)
    if getattr(sys, 'frozen', False):
        import multiprocessing
        multiprocessing.freeze_support()
    from pathlib import Path
    
    # Single instance check
    lock_file = Path(__file__).parent / "data" / ".abuser.lock"
    try:
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        fd = open(lock_file, 'w')
        import msvcrt
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
    except (IOError, OSError, ImportError):
        sys.exit(0)
    
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
    from PyQt6.QtCore import Qt
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
    window.show()
    
    # Bot runner
    bot_runner = BotRunner(parent=window)
    window.connect_bot_runner(bot_runner)
    
    print("[*] ABUSER Bot GUI started")
    print("[*] Please enter your token in the Login tab to connect")
    
    def on_exit():
        try:
            if bot_runner and bot_runner.is_running:
                print("[*] Shutting down bot...")
                bot_runner.stop_bot()
            fd.close()
            lock_file.unlink(missing_ok=True)
        except:
            pass
    
    import atexit
    atexit.register(on_exit)
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        on_exit()
        sys.exit(0)
