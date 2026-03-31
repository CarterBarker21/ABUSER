@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%dist\ABUSER\ABUSER.exe" (
    start "" "%SCRIPT_DIR%dist\ABUSER\ABUSER.exe" %*
) else (
    set "PYTHON=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
    if not exist "!PYTHON!" set "PYTHON=pythonw.exe"
    "!PYTHON!" "%SCRIPT_DIR%main.py" %*
)

exit /b 0
