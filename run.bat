@echo off
:: ABUSER Bot Launcher - Prevents multiple instances

setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check if ABUSER is already running by checking window title
:: This prevents multiple windows from opening
tasklist /FI "WINDOWTITLE eq ABUSER Bot*" /FO CSV 2>nul | findstr /I "ABUSER" >nul
if !errorlevel! equ 0 (
    echo ABUSER Bot is already running!
    timeout /t 2 /nobreak >nul
    exit /b 0
)

:: Also check for pythonw.exe processes running main.py
tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV 2>nul | findstr /I "pythonw" >nul
if !errorlevel! equ 0 (
    for /f "tokens=2 delims=," %%a in ('tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV 2^>nul') do (
        set "PID=%%a"
        set "PID=!PID:"=!"
        :: Check if this pythonw is running our main.py
        wmic process where "ProcessId=!PID!" get CommandLine 2>nul | findstr /I "main.py" >nul
        if !errorlevel! equ 0 (
            echo ABUSER Bot is already running!
            timeout /t 2 /nobreak >nul
            exit /b 0
        )
    )
)

:: Check for virtual environment Python first, then system Python
set "PYTHON=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
set "PYTHON_CONSOLE=%SCRIPT_DIR%venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    set "PYTHON=pythonw.exe"
    set "PYTHON_CONSOLE=python.exe"
)

:: Check if python is available
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

:: Launch with pythonw directly (no 'start' command to avoid extra console windows)
"%PYTHON%" "%SCRIPT_DIR%main.py"

exit /b 0
