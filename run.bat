@echo off
:: ABUSER Bot Launcher

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Use venv python if available, otherwise system python
set "PYTHON=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
if not exist "%PYTHON%" set "PYTHON=pythonw.exe"

:: Launch directly - single instance check is handled in Python
"%PYTHON%" "%SCRIPT_DIR%main.py"

exit /b 0
