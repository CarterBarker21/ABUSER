@echo off
:: ABUSER Bot Launcher - Direct Python (no console windows)

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Use venv Python directly to avoid Windows Store launcher flashes
set "PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"
set "PYTHONW=%SCRIPT_DIR%venv\Scripts\pythonw.exe"

:: Check Python availability
if not exist "%PYTHON%" (
    echo [ERROR] Python not found in venv. Run: python -m venv venv
    pause
    exit /b 1
)
if not exist "%PYTHONW%" (
    echo [ERROR] pythonw.exe not found in venv. Recreate the venv or install Python.
    pause
    exit /b 1
)

:: Check PyQt6 availability
"%PYTHON%" -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyQt6 not found. Run: pip install PyQt6
    pause
    exit /b 1
)

:: Run directly - all subprocess control is handled in Python via freeze_support()
"%PYTHONW%" "%SCRIPT_DIR%main.py" %*

exit /b 0
