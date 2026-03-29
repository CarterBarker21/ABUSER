#!/usr/bin/env python3
"""ABUSER Bot - GUI Entry Point"""

import sys

# All imports and code inside __main__ block to prevent subprocess spawning
if __name__ == '__main__':
    import asyncio
    import socket
    from pathlib import Path
    from datetime import datetime

    # Single instance check - only runs in main process
    try:
        _SINGLE_INSTANCE_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _SINGLE_INSTANCE_SOCKET.bind(('127.0.0.1', 37429))
        _SINGLE_INSTANCE_SOCKET.listen(1)
    except socket.error:
        sys.exit(0)

    # Redirect stdout/stderr when running without console (pythonw.exe)
    if sys.platform == "win32" and sys.stdout is None:
        log_dir = Path(__file__).parent / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        class Logger:
            def __init__(self, filepath):
                self.file = open(filepath, "a", encoding="utf-8")
                self.file.write(f"[{datetime.now().isoformat()}] ABUSER Bot Starting...\n")
                self.file.flush()
            
            def write(self, msg):
                self.file.write(msg)
                self.file.flush()
            
            def flush(self):
                self.file.flush()
        
        sys.stdout = Logger(log_file)
        sys.stderr = sys.stdout
        
        def exception_hook(exc_type, exc_value, exc_traceback):
            import traceback
            sys.stdout.write(f"[{datetime.now().isoformat()}] UNHANDLED EXCEPTION:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            sys.stdout.flush()
        
        sys.excepthook = exception_hook

    # Prevent console window creation on Windows for subprocess calls
    if sys.platform == "win32":
        import subprocess as _subprocess
        CREATE_NO_WINDOW = 0x08000000
        
        class NoWindowPopen(_subprocess.Popen):
            def __init__(self, *args, **kwargs):
                if 'creationflags' in kwargs:
                    kwargs['creationflags'] |= CREATE_NO_WINDOW
                else:
                    kwargs['creationflags'] = CREATE_NO_WINDOW
                super().__init__(*args, **kwargs)
        
        _subprocess.Popen = NoWindowPopen

    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    from abuse.app_paths import bootstrap_runtime_layout, env_file_path

    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None

    bootstrap_runtime_layout()
    if load_dotenv is not None:
        load_dotenv(env_file_path(), override=False)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    from abuse.gui import MainWindow, get_theme_manager, BotRunner
    from abuse.gui.config import load_gui_config

    # Main entry point
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
    
    theme_manager = get_theme_manager()
    appearance = load_gui_config().get("appearance", {})
    theme_manager.switch_theme(
        appearance.get("preset", "Discord Dark"),
        appearance.get("accent", "Red").lower().replace(" ", "_"),
    )
    theme_manager.apply_theme(app)
    
    window = MainWindow()
    window.load_and_apply_settings()
    window.show()
    
    bot_runner = BotRunner(parent=window)
    window.connect_bot_runner(bot_runner)
    
    print("[*] ABUSER Bot GUI started")
    print("[*] Please enter your token in the Login tab to connect")
    
    def on_exit():
        if bot_runner and bot_runner.is_running:
            print("[*] Shutting down bot...")
            bot_runner.stop_bot()
    
    app.aboutToQuit.connect(on_exit)
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        on_exit()
        sys.exit(0)
