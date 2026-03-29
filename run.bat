@echo off
:: ABUSER Bot Silent Launcher
:: Launches the GUI application without any console window flickering
:: Double-click this file to start the bot

setlocal
cd /d "%~dp0"

:: Prefer the VBScript launcher when present, but keep a direct pythonw
:: fallback so the app still starts if launcher.vbs is missing.
if exist "%~dp0launcher.vbs" (
    cscript //nologo "%~dp0launcher.vbs"
    exit /b %errorlevel%
)

set "PYTHONW=%~dp0venv\Scripts\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=pythonw.exe"

start "" "%PYTHONW%" "%~dp0main.py"
exit /b 0
