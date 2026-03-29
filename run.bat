@echo off
:: ABUSER Bot Launcher
:: Launches the GUI application
:: Double-click this file to start the bot

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check for virtual environment Python first, then system Python
set "PYTHON=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
set "PYTHON_CONSOLE=%SCRIPT_DIR%venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    set "PYTHON=pythonw.exe"
    set "PYTHON_CONSOLE=python.exe"
)

:: Check if python is available by trying to run it
%PYTHON_CONSOLE% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ or ensure venv exists.
    echo.
    echo To create a virtual environment:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: Test if required packages are installed
%PYTHON_CONSOLE% -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [ERROR] PyQt6 not installed!
    echo Please run: %PYTHON_CONSOLE% -m pip install -r requirements.txt
    pause
    exit /b 1
)

%PYTHON_CONSOLE% -c "import discord" 2>nul
if errorlevel 1 (
    echo [ERROR] discord.py-self not installed!
    echo Please run: %PYTHON_CONSOLE% -m pip install -r requirements.txt
    pause
    exit /b 1
)

:: Launch with pythonw (no console window)
:: If this fails, errors are logged to data\logs\startup_*.log
start "" "%PYTHON%" "%SCRIPT_DIR%main.py"

exit /b 0
