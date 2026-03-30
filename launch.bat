@echo off
:: ABUSER Launcher for built executable (no console window)

setlocal
set "SCRIPT_DIR=%~dp0"

:: Check if we're in development or running built version
if exist "%SCRIPT_DIR%dist\ABUSER\ABUSER.exe" (
    :: Running built version - use start to avoid console window
    start "" "%SCRIPT_DIR%dist\ABUSER\ABUSER.exe" %*
) else (
    :: Development mode - use pythonw
    set "PYTHON=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
    if not exist "!PYTHON!" set "PYTHON=pythonw.exe"
    "!PYTHON!" "%SCRIPT_DIR%main.py" %*
)

exit /b 0
