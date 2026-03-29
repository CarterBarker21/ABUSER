@echo off
:: ABUSER Bot Launcher

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Use venv python if available, otherwise system python
set "PYTHON=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
if not exist "%PYTHON%" set "PYTHON=pythonw.exe"

:: Launch directly - no 'start' command to avoid extra windows
:: Single-instance check is handled in Python code
"%PYTHON%" "%SCRIPT_DIR%main.py"

exit /b 0
