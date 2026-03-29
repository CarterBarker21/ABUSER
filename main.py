#!/usr/bin/env python3
"""ABUSER Bot - GUI Entry Point"""

import sys

if __name__ == '__main__':
    # Delay ALL imports until inside __main__ block
    from pathlib import Path
    
    # Single instance check using file lock
    lock_file = Path(__file__).parent / "data" / ".abuser.lock"
    try:
        # Try to create lock file exclusively
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        fd = open(lock_file, 'w')
        import msvcrt
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
    except (IOError, OSError, ImportError):
        # Already running or can't lock
        sys.exit(0)
    
    # Now import PyQt6
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    
    app = QApplication(sys.argv)
    app.setApplicationName("ABUSER Bot")
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Simple window for testing
    window = QMainWindow()
    window.setWindowTitle("ABUSER Bot")
    window.setMinimumSize(800, 600)
    
    central = QWidget()
    layout = QVBoxLayout(central)
    
    label = QLabel("ABUSER Bot - Test Window")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    
    window.setCentralWidget(central)
    window.show()
    
    # Cleanup lock on exit
    def on_exit():
        try:
            fd.close()
            lock_file.unlink(missing_ok=True)
        except:
            pass
    
    import atexit
    atexit.register(on_exit)
    
    sys.exit(app.exec())
