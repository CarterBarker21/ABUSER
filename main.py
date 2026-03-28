#!/usr/bin/env python3
"""
ABUSER Bot - GUI Entry Point with Bot Integration
PyQt6 Graphical Interface with Login-based Bot Connection

Usage:
    python main.py
    or
    double-click run.bat

Features:
    - Login tab for Discord token authentication
    - Real-time guild list display
    - Live log viewer with color-coded levels
    - Connection status with latency monitoring
    - Auto-updates when bot connects/disconnects
"""

import sys
import asyncio
import subprocess
from pathlib import Path

# =============================================================================
# PREVENT CONSOLE WINDOWS FROM SUBPROCESS CALLS (Windows only)
# This must be done before any other imports that might use subprocess
# =============================================================================
if sys.platform == "win32":
    import subprocess as _subprocess
    
    # Store original Popen
    _original_popen = _subprocess.Popen
    
    # Windows API constant to prevent console window creation
    CREATE_NO_WINDOW = 0x08000000
    
    class NoWindowPopen(_original_popen):
        """Popen subclass that never creates console windows on Windows"""
        def __init__(self, *args, **kwargs):
            # Add CREATE_NO_WINDOW flag to creationflags if on Windows
            if 'creationflags' in kwargs:
                kwargs['creationflags'] |= CREATE_NO_WINDOW
            else:
                kwargs['creationflags'] = CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
    
    # Monkey-patch subprocess.Popen
    _subprocess.Popen = NoWindowPopen
    
    # Also patch the global subprocess module if already imported elsewhere
    if 'subprocess' in sys.modules:
        sys.modules['subprocess'].Popen = NoWindowPopen
    
    # Also configure asyncio to use the same flags for subprocess calls
    # This affects asyncio.create_subprocess_* functions
    try:
        import asyncio.windows_events
        _original_asyncio_popen = asyncio.windows_events.Popen
        
        class AsyncioNoWindowPopen(_original_asyncio_popen):
            def __init__(self, *args, **kwargs):
                if 'creationflags' in kwargs:
                    kwargs['creationflags'] |= CREATE_NO_WINDOW
                else:
                    kwargs['creationflags'] = CREATE_NO_WINDOW
                super().__init__(*args, **kwargs)
        
        asyncio.windows_events.Popen = AsyncioNoWindowPopen
    except (ImportError, AttributeError):
        pass  # Not on Windows or windows_events not available

# =============================================================================

# Add project root to path
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

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
except ImportError:
    print("[ERROR] PyQt6 not installed!")
    print("Please run: pip install PyQt6")
    sys.exit(1)

from abuse.gui import MainWindow, get_theme_manager, BotRunner
from abuse.gui.config import load_gui_config


def setup_application():
    """Setup QApplication with proper attributes"""
    # Enable high DPI scaling BEFORE creating QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # App metadata
    app.setApplicationName("ABUSER Bot")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ABUSER")
    
    # Default font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    
    return app


def main():
    """Main entry point - starts GUI and sets up bot runner"""
    # Create application
    app = setup_application()
    
    # Load and apply the current GUI theme before the first paint.
    theme_manager = get_theme_manager()
    appearance = load_gui_config().get("appearance", {})
    theme_manager.switch_theme(
        appearance.get("preset", "Discord Dark"),
        appearance.get("accent", "Red").lower().replace(" ", "_"),
    )
    theme_manager.apply_theme(app)
    
    # Create main window
    window = MainWindow()
    
    # Load and apply user settings (accent color, etc.)
    window.load_and_apply_settings()
    
    window.show()
    
    # Create bot runner (does NOT auto-start)
    bot_runner = BotRunner(parent=window)
    
    # Connect bot runner to main window
    # This sets up:
    # - LoginTab.login_requested -> bot_runner.start_bot(token)
    # - LoginTab.logout_requested -> bot_runner.stop_bot()
    # - BotRunner signals -> UI updates
    window.connect_bot_runner(bot_runner)
    
    print("[*] ABUSER Bot GUI started")
    print("[*] Please enter your token in the Login tab to connect")
    
    # Cleanup on exit
    def on_exit():
        if bot_runner and bot_runner.is_running:
            print("[*] Shutting down bot...")
            bot_runner.stop_bot()
    
    app.aboutToQuit.connect(on_exit)
    
    # Run event loop
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        on_exit()
        sys.exit(0)


if __name__ == "__main__":
    main()
