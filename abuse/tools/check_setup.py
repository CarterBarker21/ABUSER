#!/usr/bin/env python3
"""
ABUSER Setup Checker
Diagnoses common setup issues
"""

import sys
import os

def check():
    print("="*60)
    print("ABUSER Setup Diagnostic")
    print("="*60)
    print()
    
    # Python version
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Check if Windows
    if sys.platform != "win32":
        print("[WARNING] Token finder only works on Windows!")
        print("[INFO] Discord stores tokens in a Windows-specific way.")
    else:
        print("[OK] Running on Windows")
    
    # Check pycryptodome
    try:
        from Crypto.Cipher import AES
        print("[OK] pycryptodome is installed")
    except ImportError:
        print("[X] pycryptodome NOT installed")
        print("    Run: pip install pycryptodome")
    
    # Check colorama
    try:
        import colorama
        print("[OK] colorama is installed")
    except ImportError:
        print("[X] colorama NOT installed")
    
    # Check Discord paths
    print()
    print("Checking Discord installations...")
    roaming = os.getenv("APPDATA")
    local = os.getenv("LOCALAPPDATA")
    
    paths = [
        ("Discord", f"{roaming}/Discord"),
        ("Discord Canary", f"{roaming}/discordcanary"),
        ("Discord PTB", f"{roaming}/discordptb"),
    ]
    
    found_any = False
    for name, path in paths:
        if path and os.path.exists(path):
            print(f"[OK] {name} found at: {path}")
            # Check for Local Storage
            ls_path = os.path.join(path, "Local Storage", "leveldb")
            if os.path.exists(ls_path):
                print(f"    [OK] Token storage found")
                found_any = True
            else:
                print(f"    [!] No token storage (may need to login)")
        else:
            print(f"[ ] {name} not found")
    
    if not found_any:
        print()
        print("[WARNING] No Discord installations found!")
        print("[INFO] Make sure Discord is installed and you've logged in.")
    
    print()
    print("="*60)
    print("Diagnostic complete!")
    print("="*60)

if __name__ == "__main__":
    try:
        check()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    input("Press Enter to exit...")
