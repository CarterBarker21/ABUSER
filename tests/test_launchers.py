from pathlib import Path


def test_run_bat_checks_python_and_pyqt6():
    """Verify run.bat checks for Python and PyQt6 before launching."""
    run_bat = Path("run.bat").read_text(encoding="utf-8")

    assert "python.exe" in run_bat
    assert "pythonw.exe" in run_bat
    assert "PyQt6" in run_bat
    assert "[ERROR]" in run_bat


def test_build_bat_detects_pyinstaller():
    """Verify build.bat properly detects and installs PyInstaller."""
    build_bat = Path("build.bat").read_text(encoding="utf-8")

    assert "PyInstaller" in build_bat
    assert "PYINSTALLER_FOUND" in build_bat
    assert "pip install" in build_bat
