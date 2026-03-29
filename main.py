#!/usr/bin/env python3
"""ABUSER Bot - GUI Entry Point"""

import sys

if __name__ == '__main__':
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
    
    # STEP 1: Add app_paths import only
    from abuse.app_paths import bootstrap_runtime_layout, env_file_path
    bootstrap_runtime_layout()
    
    # STEP 2: Add theme import
    from abuse.gui.theme import get_theme_manager
    
    # STEP 3: Add PyQt6
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    
    app = QApplication(sys.argv)
    app.setApplicationName("ABUSER Bot")
    app.setFont(QFont("Segoe UI", 10))
    
    # Get theme
    theme_manager = get_theme_manager()
    
    window = QMainWindow()
    window.setWindowTitle("ABUSER Bot")
    window.setMinimumSize(800, 600)
    
    central = QWidget()
    layout = QVBoxLayout(central)
    
    label = QLabel("ABUSER Bot - With abuse.app_paths and theme")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    
    window.setCentralWidget(central)
    window.show()
    
    def on_exit():
        try:
            fd.close()
            lock_file.unlink(missing_ok=True)
        except:
            pass
    
    import atexit
    atexit.register(on_exit)
    
    sys.exit(app.exec())
