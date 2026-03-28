@echo off
:: ABUSER Bot Silent Launcher
:: Launches the GUI application without any console window flickering
:: Double-click this file to start the bot

:: Use cscript to run the VBScript launcher which handles everything silently
cscript //nologo "%~dp0launcher.vbs"

:: The VBScript launches pythonw with a hidden window (windowstyle=0)
:: and immediately exits, leaving only the GUI visible
exit /b
