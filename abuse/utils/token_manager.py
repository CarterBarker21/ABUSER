"""
Token Manager for ABUSER Bot
Handles multiple tokens, account selection, and token operations
"""

import os
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

import aiohttp
from colorama import Fore, Style

from abuse.app_paths import bootstrap_runtime_layout, legacy_token_file_path, tokens_path

bootstrap_runtime_layout()


@dataclass
class Account:
    """Represents a Discord account with token"""
    token: str
    name: str = "Unknown"
    user_id: str = ""
    discriminator: str = "0000"
    avatar_url: str = ""
    email: str = ""
    phone: str = ""
    mfa_enabled: bool = False
    verified: bool = False
    nitro_type: int = 0  # 0=None, 1=Classic, 2=Nitro, 3=Basic
    guild_count: int = 0
    friend_count: int = 0
    source: str = "manual"  # Where token was found (manual, discord, file, etc)
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    is_valid: Optional[bool] = None
    error_message: str = ""
    
    @property
    def display_name(self) -> str:
        """Get formatted display name"""
        if self.name != "Unknown":
            # Handle both old and new Discord username formats
            if self.discriminator and self.discriminator != "0":
                return f"{self.name}#{self.discriminator}"
            return self.name
        # Don't expose much of the token
        return f"Account ({self.token[:4]}...{self.token[-4:]})"
        
    @property
    def nitro_status(self) -> str:
        """Get Nitro status string"""
        nitro_map = {0: "None", 1: "Nitro Classic", 2: "Nitro", 3: "Nitro Basic"}
        return nitro_map.get(self.nitro_type, "Unknown")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        """Create from dictionary with validation"""
        try:
            # Filter only valid fields
            valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_fields}
            return cls(**filtered)
        except Exception as e:
            # Return basic account with error info
            token = data.get('token', 'unknown')
            account = cls(token=token)
            account.is_valid = False
            account.error_message = f"Failed to load: {e}"
            return account


class TokenManager:
    """
    Manages multiple Discord tokens/accounts
    Handles loading, saving, validation, and selection
    """
    
    TOKEN_FILE = tokens_path()
    
    def __init__(self):
        self.accounts: List[Account] = []
        self.selected_account: Optional[Account] = None
        self._load_tokens()
        
    def _load_tokens(self):
        """Load tokens from file"""
        if self.TOKEN_FILE.exists():
            try:
                with open(self.TOKEN_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for acc_data in data.get('accounts', []):
                        self.accounts.append(Account.from_dict(acc_data))
            except Exception as e:
                print(f"{Fore.YELLOW}[!] Failed to load tokens: {e}{Style.RESET_ALL}")
                
    def _save_tokens(self):
        """Save tokens to file atomically"""
        import os
        try:
            data = {
                'accounts': [acc.to_dict() for acc in self.accounts],
                'last_updated': datetime.now().isoformat()
            }
            # Atomic write: write to temp file, then rename
            temp_file = self.TOKEN_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, self.TOKEN_FILE)  # Atomic on most OS
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to save tokens: {e}{Style.RESET_ALL}")
            
    def add_token(self, token: str, source: str = "manual", validate: bool = True) -> Optional[Account]:
        """Add a new token/account"""
        # Check if already exists
        for acc in self.accounts:
            if acc.token == token:
                return None  # Return None to indicate already exists
                
        account = Account(token=token, source=source)
        self.accounts.append(account)
        self._save_tokens()  # Always save first
        
        return account
        
    def remove_account(self, index: int) -> bool:
        """Remove an account by index"""
        if 0 <= index < len(self.accounts):
            removed = self.accounts.pop(index)
            if self.selected_account == removed:
                self.selected_account = None
            self._save_tokens()
            return True
        return False
        
    def get_account(self, index: int) -> Optional[Account]:
        """Get account by index"""
        if 0 <= index < len(self.accounts):
            return self.accounts[index]
        return None
        
    def select_account(self, index: int) -> Optional[Account]:
        """Select an account as active"""
        account = self.get_account(index)
        if account:
            self.selected_account = account
            account.last_used = datetime.now().isoformat()
            self._save_tokens()
        return account
        
    def get_selected_token(self) -> Optional[str]:
        """Get the selected account's token"""
        if self.selected_account:
            return self.selected_account.token
        return None
        
    async def validate_account(self, account: Account, session: aiohttp.ClientSession = None) -> bool:
        """Validate a token by fetching user info from Discord API"""
        close_session = False
        if session is None:
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            session = aiohttp.ClientSession(timeout=timeout)
            close_session = True
            
        try:
            headers = {
                "Authorization": account.token,
                "Content-Type": "application/json"
            }
            
            async with session.get("https://discord.com/api/v10/users/@me", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    account.name = data.get('username', 'Unknown')
                    account.user_id = data.get('id', '')
                    account.discriminator = data.get('discriminator', '0000')
                    avatar = data.get('avatar')
                    user_id = data.get('id')
                    if avatar and user_id:
                        account.avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png"
                    else:
                        account.avatar_url = ""
                    account.email = data.get('email', '')
                    account.phone = data.get('phone', '')
                    account.mfa_enabled = data.get('mfa_enabled', False)
                    account.verified = data.get('verified', False)
                    account.nitro_type = data.get('premium_type', 0)
                    account.is_valid = True
                    account.error_message = ""
                    
                    # Get guild count
                    try:
                        async with session.get("https://discord.com/api/v10/users/@me/guilds", headers=headers) as guild_resp:
                            if guild_resp.status == 200:
                                guilds = await guild_resp.json()
                                account.guild_count = len(guilds)
                    except Exception:
                        pass
                        
                    self._save_tokens()
                    return True
                    
                elif resp.status == 401:
                    account.is_valid = False
                    account.error_message = "Invalid or expired token"
                    return False
                elif resp.status == 403:
                    account.is_valid = False
                    account.error_message = "Token locked or disabled"
                    return False
                else:
                    account.is_valid = False
                    account.error_message = f"HTTP {resp.status}"
                    return False
                    
        except Exception as e:
            account.is_valid = False
            account.error_message = str(e)
            return False
            
        finally:
            if close_session and session:
                try:
                    await session.close()
                except Exception:
                    pass  # Don't suppress original exception
                
    async def validate_all(self, delay: float = 0.5) -> Dict[str, Any]:
        """Validate all accounts with rate limiting"""
        results = {'valid': 0, 'invalid': 0, 'errors': []}
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for i, account in enumerate(self.accounts):
                if i > 0:
                    await asyncio.sleep(delay)  # Rate limit protection
                is_valid = await self.validate_account(account, session)
                if is_valid:
                    results['valid'] += 1
                else:
                    results['invalid'] += 1
                    results['errors'].append(f"{account.display_name}: {account.error_message}")
                    
        self._save_tokens()
        return results
        
    def get_token_from_tkn_txt(self) -> Optional[str]:
        """Load token from tkn.txt (legacy support)"""
        tkn_path = legacy_token_file_path()
        if tkn_path.exists():
            try:
                with open(tkn_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if len(line) > 20 and line != "YOUR_DISCORD_TOKEN_HERE":
                            return line
            except Exception:
                pass
        return None
        
    def get_token_from_env(self) -> Optional[str]:
        """Get token from environment"""
        token = os.getenv("DISCORD_TOKEN")
        if token and token != "YOUR_TOKEN_HERE":
            return token
        return None
        
    def import_from_legacy(self):
        """Import tokens from legacy sources"""
        imported = 0
        
        # From tkn.txt
        tkn_token = self.get_token_from_tkn_txt()
        if tkn_token:
            acc = self.add_token(tkn_token, source="tkn.txt", validate=False)
            if acc:
                imported += 1
                
        # From env
        env_token = self.get_token_from_env()
        if env_token:
            acc = self.add_token(env_token, source="environment", validate=False)
            if acc:
                imported += 1
                
        if imported > 0:
            self._save_tokens()
            
        return imported


# Global instance
token_manager = TokenManager()


def get_token_manager() -> TokenManager:
    """Get the global token manager instance"""
    return token_manager
