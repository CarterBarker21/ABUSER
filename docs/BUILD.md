# Building ABUSER.exe

## Quick Start

1. **Install PyInstaller** (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. **Run the build script**:
   ```bash
   build.bat
   ```

3. **Find your exe**:
   ```
   dist\ABUSER.exe
   ```

## What Gets Built

- **Single-file executable**: `ABUSER.exe` (~54 MB)
- **No console window**: Runs as a windowed GUI application
- **Portable**: The exe can be moved anywhere — it creates `config/` and `data/` folders next to itself on first run
- **No Python required**: All dependencies are bundled inside the exe

## Build Configuration

The build is controlled by `ABUSER.spec`:
- **Excludes tests**: `pytest`, `pytest_qt`, and test infrastructure are excluded to keep the exe lean
- **Bundles assets**: SVG icons and default config files are embedded
- **Windowed mode**: `console=False` prevents the console window from appearing
- **UPX compression**: Enabled to reduce exe size

## Troubleshooting

### "PyInstaller not found"
Install it: `pip install pyinstaller`

### Build fails with import errors
Make sure all dependencies are installed:
```bash
pip install -r dev/requirements.txt
```

### Exe won't start
Check `data/logs/startup_*.log` next to the exe for error details.

## Distribution

The built `ABUSER.exe` is standalone and can be distributed as-is. Users just need to:
1. Download `ABUSER.exe`
2. Double-click to run
3. Enter their Discord token in the Login tab

The exe will automatically create `config/` and `data/` folders next to itself for storing settings and tokens.
