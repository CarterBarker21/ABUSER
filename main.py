#!/usr/bin/env python3
"""ABUSER Bot - GUI Entry Point

PyQt6 Graphical Interface with Discord selfbot integration.
"""

import sys
import asyncio
import subprocess
import socket
from pathlib import Path
from datetime import datetime

# Single-instance check using socket (prevents multiple windows)
_SINGLE_INSTANCE_SOCKET = None

def _ensure_single_instance():
    """Ensure only one instance of ABUSER runs using a socket."""
    global _SINGLE_INSTANCE_SOCKET
    try:
        _SINGLE_INSTANCE_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _SINGLE_INSTANCE_SOCKET.bind(('127.0.0.1', 37429))  # Unique port for ABUSER
        _SINGLE_INSTANCE_SOCKET.listen(1)
        return True
    except socket.error:
        # Port is already in use, another instance is running
        return False

# Check single instance before anything else
if not _ensure_single_instance():
    print("ABUSER Bot is already running!")
    sys.exit(0)

# Redirect stdout/stderr to log file when running without console (pythonw.exe)
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
    
    _original_popen = _subprocess.Popen
    CREATE_NO_WINDOW = 0x08000000
    
    class NoWindowPopen(_original_popen):
        def __init__(self, *args, **kwargs):
            if 'creationflags' in kwargs:
                kwargs['creationflags'] |= CREATE_NO_WINDOW
            else:
                kwargs['creationflags'] = CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
    
    _subprocess.Popen = NoWindowPopen
    
    if 'subprocess' in sys.modules:
        sys.modules['subprocess'].Popen = NoWindowPopen
    
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
        pass

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
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
        QGraphicsDropShadowEffect, QPushButton
    )
    from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
    from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush
except ImportError:
    print("[ERROR] PyQt6 not installed!")
    print("Please run: pip install PyQt6")
    sys.exit(1)

from abuse.gui import MainWindow, get_theme_manager, BotRunner
from abuse.gui.config import load_gui_config


class SplashScreen(QWidget):
    """First-run splash screen with branding."""
    
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 320)
        
        self._build_ui()
        self._center_on_screen()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("ABUSER")
        title_font = QFont("Segoe UI", 36)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #FF4444; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Advanced Bot for User Server Enhancement & Raiding")
        subtitle_font = QFont("Segoe UI", 11)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #CCCCCC; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Version
        version = QLabel("v1.0.0")
        version_font = QFont("Segoe UI", 10)
        version.setFont(version_font)
        version.setStyleSheet("color: #888888; background: transparent;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        layout.addStretch(1)
        
        # Loading text
        self._loading = QLabel("Loading...")
        loading_font = QFont("Segoe UI", 10)
        self._loading.setFont(loading_font)
        self._loading.setStyleSheet("color: #666666; background: transparent;")
        self._loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._loading)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        
    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
    def fade_out(self):
        """Fade out and close."""
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(500)
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation.finished.connect(self.close)
        self._animation.finished.connect(self.finished.emit)
        self._animation.start()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(30, 30, 35))
        gradient.setColorAt(1, QColor(20, 20, 25))
        
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # Border
        painter.setPen(QColor(60, 60, 70))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)


def is_first_run():
    """Check if this is the first run by looking for a flag file."""
    first_run_file = project_root / "data" / ".first_run_complete"
    return not first_run_file.exists()


def mark_first_run_complete():
    """Mark first run as complete."""
    first_run_file = project_root / "data" / ".first_run_complete"
    try:
        first_run_file.touch()
    except Exception:
        pass


def setup_application():
    """Setup QApplication with high DPI support."""
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
    
    return app


def main():
    """Main entry point - starts GUI and bot runner."""
    app = setup_application()
    
    # Show splash screen on first run
    splash = None
    if is_first_run():
        splash = SplashScreen()
        splash.show()
        app.processEvents()
    
    theme_manager = get_theme_manager()
    appearance = load_gui_config().get("appearance", {})
    theme_manager.switch_theme(
        appearance.get("preset", "Discord Dark"),
        appearance.get("accent", "Red").lower().replace(" ", "_"),
    )
    theme_manager.apply_theme(app)
    
    window = MainWindow()
    window.load_and_apply_settings()
    
    # Close splash and show main window
    if splash:
        QTimer.singleShot(1500, lambda: _finish_splash(splash, window))
    else:
        window.show()
    
    bot_runner = BotRunner(parent=window)
    window.connect_bot_runner(bot_runner)
    
    print("[*] ABUSER Bot GUI started")
    print("[*] Please enter your token in the Login tab to connect")
    
    def on_exit():
        if bot_runner and bot_runner.is_running:
            print("[*] Shutting down bot...")
            bot_runner.stop_bot()
        # Close single-instance socket on exit
        global _SINGLE_INSTANCE_SOCKET
        if _SINGLE_INSTANCE_SOCKET:
            try:
                _SINGLE_INSTANCE_SOCKET.close()
            except Exception:
                pass
    
    app.aboutToQuit.connect(on_exit)
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        on_exit()
        sys.exit(0)


def _finish_splash(splash, window):
    """Finish splash screen and show main window."""
    mark_first_run_complete()
    splash.finished.connect(window.show)
    splash.fade_out()


if __name__ == "__main__":
    main()
