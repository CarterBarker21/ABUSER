@echo off
:: ============================================================
:: ABUSER — PyInstaller build script (ONE DIRECTORY mode)
:: Produces dist\ABUSER\ folder with ABUSER.exe inside
:: Run from the repo root (same directory as this file).
:: ============================================================
setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [*] ABUSER Build Script (One Directory Mode)
echo.

:: ── Python / PyInstaller ────────────────────────────────────
set "PYTHON=python"
set "PYINSTALLER=pyinstaller"

:: Prefer the venv if present
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    set "PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"
    set "PYINSTALLER=%SCRIPT_DIR%venv\Scripts\pyinstaller.exe"
)

:: Check Python exists
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [*] Using Python: 
"%PYTHON%" --version

:: Verify PyInstaller is available
set "PYINSTALLER_FOUND=0"
"%PYTHON%" -c "import PyInstaller" >nul 2>&1
if not errorlevel 1 set "PYINSTALLER_FOUND=1"
if exist "%PYINSTALLER%" set "PYINSTALLER_FOUND=1"

if "%PYINSTALLER_FOUND%"=="0" (
    echo [!] PyInstaller not found. Installing...
    "%PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [!] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo [*] PyInstaller ready
echo.

:: ── Clean previous build artefacts ─────────────────────────
echo [*] Cleaning previous build...
if exist dist\ABUSER  rmdir /s /q dist\ABUSER 2>nul
if exist build\ABUSER rmdir /s /q build\ABUSER 2>nul

:: ── Run PyInstaller ─────────────────────────────────────────
echo [*] Building ABUSER (one-directory mode)...
echo.

"%PYTHON%" -m PyInstaller ^
    --clean ^
    --noconfirm ^
    ABUSER.spec

if errorlevel 1 (
    echo.
    echo [!] Build failed
    pause
    exit /b 1
)

:: ── Done ────────────────────────────────────────────────────
echo.
echo [+] Build complete!
echo     Output: %SCRIPT_DIR%dist\ABUSER\ABUSER.exe
echo.
echo To run: dist\ABUSER\ABUSER.exe
echo.
pause
