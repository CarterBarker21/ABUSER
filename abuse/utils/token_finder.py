#!/usr/bin/env python3
"""
ABUSER Token Finder - Safe Local Token Extraction
Only searches YOUR computer for YOUR Discord token
"""

import os
import re
import json
import base64
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Debug mode
DEBUG = False

def debug_print(msg: str):
    """Print debug messages"""
    if DEBUG:
        print(f"  [DBG] {msg}")

def pause():
    """Pause before exiting"""
    print(f"\n  Press Enter to exit...")
    try:
        input()
    except:
        pass

# Check if Windows
if sys.platform != "win32":
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  [ERROR] Windows Required                                ║
╠══════════════════════════════════════════════════════════╣
║  Token finder only works on Windows                      ║
║  Discord stores tokens differently on other platforms    ║
╚══════════════════════════════════════════════════════════╝""")
    pause()
    sys.exit(1)

# Windows-specific imports
try:
    import ctypes
    from ctypes import POINTER, Structure, c_buffer, c_char, wintypes
    
    class DATA_BLOB(Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", POINTER(c_char))
        ]
    
    WINDOWS_AVAILABLE = True
    debug_print("Windows ctypes loaded")
except ImportError as e:
    print(f"  [ERROR] Failed to import Windows libraries: {e}")
    WINDOWS_AVAILABLE = False
    pause()
    sys.exit(1)

# Try to import Crypto
try:
    from Crypto.Cipher import AES
    CRYPTO_AVAILABLE = True
    debug_print("pycryptodome loaded")
except ImportError:
    print("  [ERROR] pycryptodome not installed - run: pip install pycryptodome")
    CRYPTO_AVAILABLE = False


class TokenFinder:
    """Safe local Discord token finder"""
    
    DISCORD_PATHS = [
        ("Discord", "Roaming", "Discord/Local Storage/leveldb"),
        ("Discord Canary", "Roaming", "discordcanary/Local Storage/leveldb"),
        ("Discord PTB", "Roaming", "discordptb/Local Storage/leveldb"),
        ("Lightcord", "Roaming", "Lightcord/Local Storage/leveldb"),
    ]
    
    TOKEN_PATTERNS = [
        r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{25,110}",  # Standard tokens (24-26 char ID segment)
        r"mfa\.[\w-]{80,110}",  # MFA tokens
    ]
    
    ENCRYPTED_TOKEN_PATTERN = r'dQw4w9WgXcQ:[^.*\[\'(.*)\'\].*$][^"]*'
    
    def __init__(self):
        self.tokens = []
        self.roaming = os.getenv("APPDATA")
        self.local = os.getenv("LOCALAPPDATA")
        debug_print(f"Roaming: {self.roaming}")
        debug_print(f"Local: {self.local}")
        
    def _get_data(self, blob_out: Structure) -> bytes:
        """Extract data from Windows data blob"""
        cb_data = int(blob_out.cbData)
        pb_data = blob_out.pbData
        buffer = c_buffer(cb_data)
        ctypes.cdll.msvcrt.memcpy(buffer, pb_data, cb_data)
        ctypes.windll.kernel32.LocalFree(pb_data)
        return buffer.raw
    
    def _crypt_unprotect(self, encrypted_bytes: bytes, entropy: bytes = b"") -> Optional[bytes]:
        """Decrypt using Windows CryptUnprotectData"""
        try:
            buffer_in = c_buffer(encrypted_bytes, len(encrypted_bytes))
            buffer_entropy = c_buffer(entropy, len(entropy))
            blob_in = DATA_BLOB(len(encrypted_bytes), buffer_in)
            blob_entropy = DATA_BLOB(len(entropy), buffer_entropy)
            blob_out = DATA_BLOB()
            
            if ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(blob_in), None, ctypes.byref(blob_entropy),
                None, None, 0x01, ctypes.byref(blob_out)
            ):
                return self._get_data(blob_out)
        except Exception as e:
            debug_print(f"CryptUnprotectData error: {e}")
        return None
    
    def _decrypt_token(self, buff: bytes, master_key: bytes) -> Optional[str]:
        """Decrypt token using AES-GCM"""
        if not CRYPTO_AVAILABLE:
            return None
            
        try:
            starts = buff.decode(encoding="utf8", errors="ignore")[:3]
            if starts in ("v10", "v11"):
                iv = buff[3:15]
                payload = buff[15:]
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt(payload)
                return decrypted[:-16].decode()
        except Exception as e:
            debug_print(f"Token decryption error: {e}")
        return None
    
    def _get_master_key(self, local_state_path: str) -> Optional[bytes]:
        """Get decryption key from Local State file"""
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            master_key = self._crypt_unprotect(encrypted_key[5:])
            debug_print(f"Got master key from: {local_state_path}")
            return master_key
        except Exception as e:
            debug_print(f"Master key error: {e}")
            return None
    
    def _extract_from_file(self, file_path: str, master_key: Optional[bytes] = None) -> List[str]:
        """Extract tokens from a single file"""
        found_tokens = []
        
        try:
            with open(file_path, "r", errors="ignore") as f:
                content = f.read()
                lines = [x.strip() for x in content.splitlines() if x.strip()]
        except Exception as e:
            debug_print(f"File read error {file_path}: {e}")
            return found_tokens
        
        for line in lines:
            # Try encrypted tokens first
            if master_key and CRYPTO_AVAILABLE:
                for match in re.finditer(self.ENCRYPTED_TOKEN_PATTERN, line):
                    try:
                        token_part = match.group().split("dQw4w9WgXcQ:")[1]
                        token_encrypted = base64.b64decode(token_part)
                        decrypted = self._decrypt_token(token_encrypted, master_key)
                        if decrypted and decrypted not in found_tokens:
                            found_tokens.append(decrypted)
                            debug_print(f"Found encrypted token in {file_path}")
                    except Exception as e:
                        debug_print(f"Decryption error: {e}")
                        continue
            
            # Try plain tokens
            for pattern in self.TOKEN_PATTERNS:
                for match in re.finditer(pattern, line):
                    token = match.group()
                    if token not in found_tokens:
                        found_tokens.append(token)
                        debug_print(f"Found plain token in {file_path}")
        
        return found_tokens
    
    def _get_request_headers(self, token: str) -> dict:
        """Get Discord API request headers with proper super properties"""
        import platform
        
        # Build super properties (base64 encoded)
        super_props = {
            "os": "Windows",
            "browser": "Discord Client",
            "release_channel": "stable",
            "client_version": "1.0.9016",
            "os_version": "10.0.19045",
            "system_locale": "en-US",
            "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9016 Chrome/108.0.5359.215 Electron/22.3.26 Safari/537.36",
            "browser_version": "22.3.26",
            "client_build_number": 999999,
            "native_build_number": None,
            "client_event_source": None
        }
        
        super_props_b64 = base64.b64encode(json.dumps(super_props).encode()).decode()
        
        return {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9016 Chrome/108.0.5359.215 Electron/22.3.26 Safari/537.36",
            "X-Super-Properties": super_props_b64,
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "America/New_York",
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://discord.com/",
            "Origin": "https://discord.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
    
    def _validate_token(self, token: str) -> bool:
        """Check if token is valid using Discord API"""
        try:
            import urllib.request
            
            headers = self._get_request_headers(token)
            
            req = urllib.request.Request(
                "https://discord.com/api/v9/users/@me",
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except urllib.error.HTTPError as e:
            # 401 = invalid token, 429 = rate limited
            if e.code == 401:
                debug_print("Token invalid (401)")
            elif e.code == 429:
                debug_print("Rate limited (429)")
            else:
                debug_print(f"HTTP error: {e.code}")
            return False
        except Exception as e:
            debug_print(f"Token validation error: {e}")
            return False
    
    def find_tokens(self) -> List[Tuple[str, str]]:
        """Find Discord tokens in local storage"""
        found_tokens = []
        
        print("  [*] Scanning Discord installations...")
        
        for client_name, location_type, relative_path in self.DISCORD_PATHS:
            if location_type == "Roaming":
                base_path = self.roaming
            else:
                base_path = self.local
            
            if not base_path:
                continue
            
            full_path = os.path.join(base_path, relative_path)
            local_state_path = os.path.join(
                base_path,
                relative_path.replace("/Local Storage/leveldb", ""),
                "Local State"
            )
            
            debug_print(f"Checking: {full_path}")
            
            if not os.path.exists(full_path):
                continue
            
            print(f"  [OK] Found {client_name}")
            
            # Get master key
            master_key = None
            if os.path.exists(local_state_path):
                master_key = self._get_master_key(local_state_path)
                if master_key:
                    debug_print(f"Got decryption key for {client_name}")
            
            # Search files
            try:
                files = [f for f in os.listdir(full_path) if f.endswith((".log", ".ldb"))]
                debug_print(f"Scanning {len(files)} files...")
                
                for filename in files:
                    file_path = os.path.join(full_path, filename)
                    tokens = self._extract_from_file(file_path, master_key)
                    
                    for token in tokens:
                        if self._validate_token(token):
                            found_tokens.append((client_name, token))
                            print(f"  [OK] Valid token found!")
            except Exception as e:
                debug_print(f"Scan error: {e}")
                continue
        
        # Remove duplicates
        seen = set()
        unique_tokens = []
        for client, token in found_tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append((client, token))
        
        return unique_tokens
    
    def get_token_info(self, token: str) -> Optional[dict]:
        """Get information about a token"""
        try:
            import urllib.request
            
            headers = self._get_request_headers(token)
            
            req = urllib.request.Request(
                "https://discord.com/api/v9/users/@me",
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return {
                    "username": data.get("username", "Unknown"),
                    "discriminator": data.get("discriminator", "0000"),
                    "id": data.get("id", "Unknown"),
                    "email": data.get("email", "Hidden"),
                    "verified": data.get("verified", False),
                }
        except Exception as e:
            debug_print(f"Get info error: {e}")
            return None


def prompt_token_usage(token: str, info: dict) -> bool:
    """Ask user if they want to use found token"""
    masked_token = f"{token[:15]}...{token[-10:]}"
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║              TOKEN FOUND - PERMISSION REQUIRED           ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Username:  {info['username'][:20]:<36}║
║  ID:        {info['id']:<36}║
║  Email:     {info['email'][:30]:<36}║
║  Verified:  {'Yes' if info['verified'] else 'No':<36}║
║                                                          ║
║  Token:     {masked_token:<36}║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║  ! Warning: Using this token violates Discord ToS        ║
║    Only use for educational purposes on YOUR account     ║
╚══════════════════════════════════════════════════════════╝""")
    
    while True:
        try:
            choice = input("\n  Use this token? [Y/n]: ").strip().lower()
            if choice in ("", "yes", "y"):
                return True
            elif choice in ("no", "n"):
                return False
            print("  Please enter 'y' or 'n'")
        except KeyboardInterrupt:
            print("\n  Cancelled.")
            return False


def find_and_prompt_token(return_only: bool = False) -> Optional[str] or list:
    """
    Main function: Find token and ask for permission
    
    Args:
        return_only: If True, returns list of (token, source) tuples instead of prompting
    
    Returns:
        Single token string, list of (token, source) tuples, or None
    """
    print("  [*] Searching local Discord installation...")
    
    try:
        finder = TokenFinder()
        tokens = finder.find_tokens()
        
        if not tokens:
            if return_only:
                return []
            print(f"""
╔══════════════════════════════════════════════════════════╗
║  ! No Valid Tokens Found                                 ║
╠══════════════════════════════════════════════════════════╣
║  Make sure Discord is installed and you're logged in     ║
╚══════════════════════════════════════════════════════════╝""")
            pause()
            return None
        
        print(f"  [OK] Found {len(tokens)} valid token(s)\n")
        
        # Return list if requested (for menu system)
        if return_only:
            return [(token, client) for client, token in tokens]
        
        # Use first valid token
        client_name, token = tokens[0]
        
        # Get token info (may fail if token expired, but still offer it)
        info = finder.get_token_info(token)
        
        if info:
            # Ask for permission with account info
            if prompt_token_usage(token, info):
                print(f"  [OK] Token accepted\n")
                return token
            else:
                print(f"  ! Token rejected")
                pause()
                return None
        else:
            # Can't get info but token exists - offer it anyway
            print(f"""
╔══════════════════════════════════════════════════════════╗
║  Token Found (Account Info Unavailable)                  ║
╠══════════════════════════════════════════════════════════╣
║  Source: {client_name:<46} ║
║  Token: {token[:20]:<47}... ║
╠══════════════════════════════════════════════════════════╣
║  Note: Could not verify token with Discord API           ║
║  The token may have expired or been revoked              ║
║  You can still try to use it                             ║
╚══════════════════════════════════════════════════════════╝""")
            
            while True:
                try:
                    choice = input("\n  Use this token? [Y/n]: ").strip().lower()
                    if choice in ("", "yes", "y"):
                        print(f"  [OK] Token accepted\n")
                        return token
                    elif choice in ("no", "n"):
                        print(f"  ! Token rejected")
                        pause()
                        return None
                    print("  Please enter 'y' or 'n'")
                except KeyboardInterrupt:
                    print("\n  Cancelled.")
                    return None
            
    except Exception as e:
        print(f"  [ERROR] Token finder error: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        pause()
        return [] if return_only else None


if __name__ == "__main__":
    # Enable debug mode if --debug flag
    if "--debug" in sys.argv:
        DEBUG = True
        print("  [DEBUG MODE ENABLED]\n")
    
    try:
        token = find_and_prompt_token()
        if token:
            print(f"  [OK] Token ready: {token[:20]}...")
        else:
            print("  ! No token selected")
        pause()
    except Exception as e:
        print(f"  [ERROR] Fatal error: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        pause()
