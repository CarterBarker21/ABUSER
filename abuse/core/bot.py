"""
ABUSER Bot Core Engine
Main bot class and initialization with enhanced error handling and robustness
"""

import os
import sys
import json
import asyncio
import logging
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO
from collections import deque
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import discord
from discord.ext import commands
from discord.errors import LoginFailure, ConnectionClosed, HTTPException
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

from abuse.app_paths import (
    bootstrap_runtime_layout,
    bot_config_path,
    legacy_token_file_path,
    log_file_path,
)

# Import screen manager
from abuse.utils.screen_manager import get_screen_manager, ScreenManager
from abuse.utils.rate_limiter import RateLimiter, RateLimitConfig, get_rate_limiter, RateLimitTier

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional at runtime
    load_dotenv = None

bootstrap_runtime_layout()
if load_dotenv is not None:
    from abuse.app_paths import env_file_path

    load_dotenv(env_file_path(), override=False)


class ConnectionRetryConfig:
    """Configuration for connection retry logic"""
    MAX_RETRIES = 5
    INITIAL_DELAY = 1.0
    MAX_DELAY = 60.0
    BACKOFF_MULTIPLIER = 2.0
    RETRYABLE_EXCEPTIONS = (ConnectionClosed, HTTPException, asyncio.TimeoutError, OSError)


class ABUSERBot(commands.Bot):
    """
    Main ABUSER Bot class
    Extends discord.ext.commands.Bot with additional functionality,
    enhanced error handling, and robustness features
    """
    
    def __init__(self):
        # Load config
        self.config = self._load_config()
        self.start_time = datetime.now()
        
        # Track connection state
        self._connection_attempts = 0
        self._last_connection_time: Optional[datetime] = None
        self._is_shutting_down = False
        self._shutdown_event = asyncio.Event()
        
        # Performance tracking
        self._command_stats: Dict[str, Dict[str, Any]] = {}
        self._error_counts: Dict[str, int] = {}
        self._last_error_time: Optional[datetime] = None
        self._error_cooldown = timedelta(seconds=5)
        
        # Set up logging
        self._setup_logging()
        
        # Brand name
        self.brand_name = "ABUSER"
        
        # Bot configuration
        self.prefix = self.config.get("bot", {}).get("prefix", ".")
        self.token = self._get_token()
        
        # Cog loading tracking
        self._loaded_cogs: List[str] = []
        self._failed_cogs: List[str] = []
        
        # Rate limiter
        self._rate_limiter: Optional[RateLimiter] = None
        self._rate_limit_enabled = self.config.get("performance", {}).get("rate_limiting_enabled", True)
        
        # Build options for discord.py-self
        options = {
            'command_prefix': self.prefix,
            'self_bot': True,
            'help_command': None,
            'max_messages': 10000,  # Limit message cache for performance
            'heartbeat_timeout': 60.0,  # Connection timeout
            'guild_ready_timeout': 10.0,  # Guild subscription timeout
        }
        
        # Only add intents for standard discord.py
        if hasattr(discord, 'Intents'):
            options['intents'] = discord.Intents.all()
        
        super().__init__(**options)
        
        # Store references
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Register signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Set up OS signal handlers for graceful shutdown"""
        try:
            if sys.platform != 'win32':
                # Unix signal handlers - only if event loop exists and is running
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        for sig in (signal.SIGTERM, signal.SIGINT):
                            try:
                                loop.add_signal_handler(
                                    sig, lambda: asyncio.create_task(self._signal_handler())
                                )
                            except (NotImplementedError, ValueError):
                                pass
                except RuntimeError:
                    # No event loop in current thread, skip signal handlers
                    pass
            else:
                # Windows signal handling via loop exception handler
                pass
        except Exception as e:
            # Don't crash if signal handlers can't be set up
            if hasattr(self, 'logger'):
                self.logger.warning(f"Could not set up signal handlers: {e}")
    
    async def _signal_handler(self):
        """Handle shutdown signals gracefully"""
        self.logger.info("Shutdown signal received, initiating graceful shutdown...")
        await self.shutdown()
        
    def _load_config(self) -> dict:
        """Load configuration from config.json with enhanced error handling"""
        config_path = bot_config_path()
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    logging_config = config.setdefault("logging", {})
                    configured_log = logging_config.get("file")
                    if configured_log in (None, "", "./logs/abuse.log", "logs/abuse.log"):
                        logging_config["file"] = str(log_file_path())
                    self.logger.info("Configuration loaded successfully") if hasattr(self, 'logger') else None
                    return config
            except json.JSONDecodeError as e:
                print(f"{Fore.RED}[ERROR] Invalid config.json: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[WARN] Using default configuration{Style.RESET_ALL}")
                return self._get_default_config()
            except Exception as e:
                print(f"{Fore.RED}[ERROR] Cannot load config: {e}{Style.RESET_ALL}")
                return self._get_default_config()
        return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Return default configuration"""
        return {
            "bot": {
                "prefix": ".",
                "status": "online",
                "activity": {
                    "type": "playing",
                    "name": "ABUSER SelfBot"
                }
            },
            "security": {
                "safe_mode": True,
                "confirm_destructive": True,
                "log_commands": True
            },
            "logging": {
                "level": "INFO",
                "file": str(log_file_path())
            }
        }
    
    def _get_token(self) -> str:
        """Get Discord token from various sources with validation"""
        
        # First priority: Token selected via menu system
        menu_token = os.getenv("ABUSER_SELECTED_TOKEN")
        if self._validate_token(menu_token):
            return menu_token
        
        # Second priority: tokens.json (selected account)
        try:
            from abuse.utils.token_manager import get_token_manager
            tm = get_token_manager()
            if tm.selected_account and self._validate_token(tm.selected_account.token):
                return tm.selected_account.token
        except Exception:
            pass
        
        # Legacy fallbacks
        # Try tkn.txt
        tkn_path = legacy_token_file_path()
        if tkn_path.exists():
            try:
                with open(tkn_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line == "YOUR_DISCORD_TOKEN_HERE":
                            continue
                        if self._validate_token(line):
                            return line
            except Exception:
                pass
        
        # Try environment variable
        token = os.getenv("DISCORD_TOKEN")
        if self._validate_token(token):
            return token
        
        # Fall back to config
        token = self.config.get("bot", {}).get("token", "")
        if self._validate_token(token):
            return token
        
        # No token found
        error_msg = f"""
{Fore.RED}╔══════════════════════════════════════════════════════════╗
║  [ERROR] No Discord Token Found                          ║
╠══════════════════════════════════════════════════════════╣
║  Please run without arguments to use the menu system     ║
║  Or configure your token in one of:                      ║
║    1. Use the Account Management menu                    ║
║    2. tkn.txt file                                       ║
║    3. Environment variable: DISCORD_TOKEN                ║
║    4. config.json file                                   ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(error_msg)
        raise RuntimeError("No Discord token found. Please configure a token.")
    
    def _validate_token(self, token: Optional[str]) -> bool:
        """Validate a Discord token format"""
        if not token:
            return False
        if token in ("YOUR_TOKEN_HERE", "YOUR_DISCORD_TOKEN_HERE", "FROM_TKN_FILE"):
            return False
        # Basic format check: Discord tokens are typically 59+ characters
        if len(token) < 20:
            return False
        return True
    
    def _setup_logging(self):
        """Configure logging with screen management and error handling"""
        log_config = self.config.get("logging", {})
        level = log_config.get("level", "INFO")
        log_file = log_config.get("file", str(log_file_path()))
        
        # Ensure logs directory exists
        try:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Cannot create logs directory: {e}{Style.RESET_ALL}")
            log_file = None
        
        # Initialize screen manager
        self.screen_manager = get_screen_manager()
        self._log_buffer: deque = deque(maxlen=100)  # Efficient circular buffer
        self._header_printed = False
        
        # Set up root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level))
        
        # Remove ALL existing handlers from root and known loggers
        root_logger.handlers = []
        for logger_name in ['discord', 'discord.http', 'discord.gateway', 'discord.client', 'websockets', 'asyncio']:
            logger = logging.getLogger(logger_name)
            logger.handlers = []
            logger.propagate = True  # Let them propagate to root
        
        # File handler (no colors, always logs everything including discord)
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setLevel(getattr(logging, level))
                file_format = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                file_handler.setFormatter(file_format)
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"{Fore.YELLOW}[WARN] Cannot create log file: {e}{Style.RESET_ALL}")
        
        # Custom stream handler that buffers for screen manager (filters noisy logs)
        self.log_handler = self._create_screen_handler(getattr(logging, level))
        root_logger.addHandler(self.log_handler)
        
        # Get our logger
        self.logger = logging.getLogger("ABUSER")
        
        # Set discord logger to propagate to root (so it goes to file but gets filtered from console)
        discord_logger = logging.getLogger("discord")
        discord_logger.handlers = []  # Remove any existing handlers
        discord_logger.propagate = True
        discord_logger.setLevel(getattr(logging, level))
        
    def _create_screen_handler(self, level):
        """Create a handler that buffers logs for screen display"""
        
        class ScreenHandler(logging.Handler):
            # Loggers to suppress from console (too noisy)
            SUPPRESSED_LOGGERS = {'discord', 'websockets', 'asyncio', 'urllib3', 'requests'}
            
            def __init__(self, bot_instance, level=logging.NOTSET):
                super().__init__(level)
                self.bot = bot_instance
                self.setFormatter(logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%H:%M:%S"
                ))
                
            def emit(self, record):
                try:
                    # Filter out noisy library logs from console display
                    # (they still go to file via root logger's FileHandler)
                    logger_name = record.name.split('.')[0]
                    if logger_name in self.SUPPRESSED_LOGGERS:
                        return
                    
                    msg = self.format(record)
                    # Add to buffer
                    self.bot._add_log_line(msg)
                except Exception:
                    self.handleError(record)
                    
        return ScreenHandler(self, level)
        
    def _add_log_line(self, line: str):
        """Add a log line to buffer and refresh display"""
        self._log_buffer.append(line)
        if self._header_printed:
            try:
                self._refresh_display()
            except Exception:
                pass  # Don't crash on display errors
            
    def _clear_screen(self):
        """Clear terminal screen using ANSI codes"""
        try:
            sys.stdout.write('\033[2J\033[H')
            sys.stdout.flush()
        except Exception:
            pass
        
    def _refresh_display(self):
        """Refresh the entire display with banner, stats, and logs"""
        import shutil
        
        try:
            terminal_height = shutil.get_terminal_size().lines
        except:
            terminal_height = 24
            
        # Clear screen
        self._clear_screen()
        
        # Print banner (capture line count)
        banner_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = banner_output
        self._print_banner_raw()
        sys.stdout = old_stdout
        banner_text = banner_output.getvalue()
        banner_lines = banner_text.count('\n')
        print(banner_text, end='')
        
        # Print stats
        stats_output = StringIO()
        sys.stdout = stats_output
        self._print_status_raw()
        sys.stdout = old_stdout
        stats_text = stats_output.getvalue()
        stats_lines = stats_text.count('\n')
        print(stats_text, end='')
        
        # Calculate available space for logs
        header_lines = banner_lines + stats_lines
        available_lines = max(1, terminal_height - header_lines - 1)
        
        # Print recent logs
        recent_logs = list(self._log_buffer)[-available_lines:]
        for log in recent_logs:
            # Colorize based on log level
            colored_log = self._colorize_log(log)
            print(colored_log)
            
    def _colorize_log(self, log: str) -> str:
        """Apply colors to log level only"""
        # Match standard log format: "HH:MM:SS - NAME - LEVEL - Message"
        parts = log.split(' - ', 3)
        if len(parts) == 4:
            time, name, level, message = parts
            level_colors = {
                'ERROR': Fore.RED,
                'WARNING': Fore.YELLOW,
                'INFO': Fore.GREEN,
                'DEBUG': Fore.BLUE
            }
            if level in level_colors:
                colored_level = f"{level_colors[level]}{level}{Style.RESET_ALL}"
                return f"{time} - {name} - {colored_level} - {message}"
        return log
        
    def _print_banner_raw(self):
        """Print banner without side effects"""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     {Fore.WHITE} █████╗ ██████╗ ██╗   ██╗███████╗███████╗██████╗ {Fore.CYAN}    ║
║     {Fore.WHITE}██╔══██╗██╔══██╗██║   ██║██╔════╝██╔════╝██╔══██╗{Fore.CYAN}    ║
║     {Fore.WHITE}███████║██████╔╝██║   ██║███████╗█████╗  ██████╔╝{Fore.CYAN}    ║
║     {Fore.WHITE}██╔══██║██╔══██╗██║   ██║╚════██║██╔══╝  ██╔══██╗{Fore.CYAN}    ║
║     {Fore.WHITE}██║  ██║██████╔╝╚██████╔╝███████║███████╗██║  ██║{Fore.CYAN}    ║
║     {Fore.WHITE}╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝{Fore.CYAN}    ║
║                                                          ║
║              {Fore.WHITE}Advanced Bot for User Server                {Fore.CYAN}║
║                 {Fore.WHITE}Enhancement & Raiding{Fore.CYAN}                    ║
║                                                          ║
║                    {Fore.WHITE}Version 1.0.0{Fore.CYAN}                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        
    def _print_status_raw(self):
        """Print status without side effects"""
        if not self.user:
            return
        # Handle both old (username#discriminator) and new (username only) formats
        if self.user.discriminator and self.user.discriminator != "0":
            username = f"{self.user.name}#{self.user.discriminator}"
        else:
            username = self.user.name
        user_id = str(self.user.id)
        guilds = str(len(self.guilds))
        users = str(len(self.users))
        
        # Show connection status
        connection_status = f"✅ Ready (Attempt {self._connection_attempts})" if self.is_ready() else "⏳ Connecting..."
        
        print(f"""{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.WHITE}  Logged in as:  {Fore.GREEN}{username:<35}{Fore.CYAN}║
║{Fore.WHITE}  User ID:       {Fore.GREEN}{user_id:<35}{Fore.CYAN}║
╠══════════════════════════════════════════════════════════╣
║{Fore.WHITE}  Prefix:        {Fore.YELLOW}{self.prefix:<35}{Fore.CYAN}║
║{Fore.WHITE}  Guilds:        {Fore.GREEN}{guilds:<35}{Fore.CYAN}║
║{Fore.WHITE}  Users:         {Fore.GREEN}{users:<35}{Fore.CYAN}║
║{Fore.WHITE}  Status:        {Fore.GREEN if self.is_ready() else Fore.YELLOW}{connection_status:<35}{Fore.CYAN}║
╠══════════════════════════════════════════════════════════╣
║{Fore.WHITE}  Type {Fore.YELLOW}{self.prefix}help{Fore.WHITE} for commands{' '*23}{Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        
        # Show loaded cogs summary
        if self._loaded_cogs:
            cogs_str = ", ".join(self._loaded_cogs[:5])
            if len(self._loaded_cogs) > 5:
                cogs_str += f" (+{len(self._loaded_cogs) - 5} more)"
            print(f"{Fore.GREEN}[+] Loaded: {cogs_str}{Style.RESET_ALL}")
        
        if self._failed_cogs:
            print(f"{Fore.RED}[-] Failed: {', '.join(self._failed_cogs)}{Style.RESET_ALL}")
    
    def _print_banner(self):
        """Print the ABUSER banner (legacy, used before ready)"""
        self._print_banner_raw()
    
    def _print_status(self):
        """Print bot status information (legacy, used before ready)"""
        self._print_status_raw()
    
    async def setup_hook(self):
        """Called when bot is setting up with enhanced error handling"""
        self.logger.info("Bot setup hook started")
        
        # Initialize rate limiter
        if self._rate_limit_enabled:
            await self._init_rate_limiter()
        
        try:
            # Initialize aiohttp session for API calls
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": "ABUSER-SelfBot/1.0"}
            )
            self.logger.info("HTTP session initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize HTTP session: {e}")
        
        # Load cogs with retry logic
        await self._load_cogs_with_retry()
        
        self.logger.info("Setup hook completed")
    
    async def _init_rate_limiter(self):
        """Initialize the global rate limiter"""
        try:
            # Load rate limit config from config.json
            rate_limit_config = RateLimitConfig(
                global_requests_per_second=self.config.get("performance", {}).get("global_rate_limit", 50.0),
                global_burst_size=self.config.get("performance", {}).get("global_burst_size", 10),
                max_retries=self.config.get("performance", {}).get("max_retries", 3),
                base_retry_delay=self.config.get("performance", {}).get("retry_delay_seconds", 1.0),
            )
            
            self._rate_limiter = get_rate_limiter(rate_limit_config)
            await self._rate_limiter.start()
            
            self.logger.info(
                f"Rate limiter initialized: {rate_limit_config.global_requests_per_second} req/s max, "
                f"{rate_limit_config.max_retries} max retries"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize rate limiter: {e}")
            self._rate_limit_enabled = False
    
    @property
    def rate_limiter(self) -> Optional[RateLimiter]:
        """Get the rate limiter instance"""
        return self._rate_limiter
    
    async def check_rate_limit(
        self,
        tier: RateLimitTier = RateLimitTier.MODERATE,
        guild_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Check if a request can proceed under rate limits
        
        Returns:
            True if request can proceed, False if rate limited
        """
        if not self._rate_limit_enabled or not self._rate_limiter:
            return True
        
        status = await self._rate_limiter.check_rate_limit(
            tier=tier,
            guild_id=guild_id,
            user_id=user_id
        )
        
        return not status.is_limited
    
    async def _load_cogs_with_retry(self):
        """Load cogs with individual retry logic for each"""
        cog_folders = [
            "utility", "admin", "fun", "moderation",
            "automod", "nuke", "sniper", "voice", "web"
        ]
        
        for folder in cog_folders:
            await self._load_cog_with_retry(folder)
        
        total = len(self._loaded_cogs) + len(self._failed_cogs)
        if self._failed_cogs:
            self.logger.warning(f"Loaded {len(self._loaded_cogs)}/{total} modules (failed: {', '.join(self._failed_cogs)})")
        else:
            self.logger.info(f"Loaded {len(self._loaded_cogs)} modules successfully")
    
    async def _load_cog_with_retry(self, folder: str, max_retries: int = 3):
        """Load a single cog with retry logic"""
        extension_name = f"abuse.cogs.{folder}"
        
        for attempt in range(1, max_retries + 1):
            try:
                await self.load_extension(extension_name)
                self._loaded_cogs.append(folder)
                self.logger.debug(f"Loaded module: {folder}")
                return
            except commands.ExtensionAlreadyLoaded:
                self._loaded_cogs.append(folder)
                return
            except commands.ExtensionNotFound:
                self.logger.debug(f"Module not found: {folder}")
                return  # Don't count as failure - may not exist
            except Exception as e:
                if attempt < max_retries:
                    wait_time = attempt * 0.5  # Exponential backoff: 0.5s, 1s, 1.5s
                    self.logger.warning(f"Failed to load {folder} (attempt {attempt}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    self._failed_cogs.append(folder)
                    self.logger.error(f"Failed to load {folder} after {max_retries} attempts: {e}")
    
    async def _load_cogs(self):
        """Legacy cog loading method - redirects to retry version"""
        await self._load_cogs_with_retry()
    
    async def on_ready(self):
        """Called when bot is fully ready with enhanced error handling"""
        self._connection_attempts += 1
        self._last_connection_time = datetime.now()
        
        # Mark header as printed to enable screen refresh
        self._header_printed = True
        
        # Initial display refresh to show banner and stats
        try:
            self._refresh_display()
        except Exception:
            pass
        
        try:
            # Set status with retry
            await self._set_status_with_retry()
        except Exception as e:
            self.logger.warning(f"Could not set status: {e}")
        
        # Log ready message with guild count
        guild_count = len(self.guilds) if self.guilds else 0
        self.logger.info(f"ABUSER Bot ready as {self.user} - {guild_count} guilds in cache")
        
        # Debug: List all guilds
        if self.guilds:
            for guild in self.guilds:
                self.logger.debug(f"  - Guild: {guild.name} (ID: {guild.id})")
        
        # Start background tasks
        self._start_background_tasks()
    
    async def on_guild_available(self, guild):
        """Called when a guild becomes available (cached and ready)"""
        self.logger.debug(f"Guild available: {guild.name} (ID: {guild.id})")
    
    async def on_guild_unavailable(self, guild):
        """Called when a guild becomes unavailable"""
        self.logger.debug(f"Guild unavailable: {guild.name} (ID: {guild.id})")
    
    async def _set_status_with_retry(self, max_retries: int = 3):
        """Set bot status with retry logic"""
        activity_config = self.config.get("bot", {}).get("activity", {})
        if not activity_config:
            return
            
        activity_type = activity_config.get("type", "playing")
        activity_name = activity_config.get("name", "ABUSER SelfBot")
        
        activity = discord.Activity(
            type=getattr(discord.ActivityType, activity_type, discord.ActivityType.playing),
            name=activity_name
        )
        
        for attempt in range(max_retries):
            try:
                await self.change_presence(activity=activity)
                self.logger.debug(f"Status set to: {activity_type} {activity_name}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    raise e
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # These tasks run in the background for maintenance
        pass  # Add background tasks here if needed
    
    async def on_connect(self):
        """Called when bot connects to Discord"""
        self._connection_attempts += 1
        self.logger.info(f"Connected to Discord (attempt {self._connection_attempts})")
    
    async def on_disconnect(self):
        """Called when bot disconnects from Discord"""
        self.logger.warning("Disconnected from Discord")
        if not self._is_shutting_down:
            self.logger.info("Attempting to reconnect...")
    
    async def on_resumed(self):
        """Called when bot resumes session after disconnect"""
        self.logger.info("Session resumed")
    
    async def on_command(self, ctx):
        """Track command usage for performance monitoring with rate limit pre-check"""
        cmd_name = ctx.command.name if ctx.command else "unknown"
        
        # Pre-command rate limit check
        if self._rate_limit_enabled and self._rate_limiter:
            guild_id = ctx.guild.id if ctx.guild else None
            user_id = ctx.author.id
            
            # Determine tier based on command name/cog
            tier = self._get_command_tier(ctx.command)
            
            can_proceed = await self.check_rate_limit(
                tier=tier,
                guild_id=guild_id,
                user_id=user_id
            )
            
            if not can_proceed:
                # Log rate limit hit
                self.logger.warning(f"Rate limit hit for command: {cmd_name} by {ctx.author}")
                # Note: The actual rate limit message is sent by the decorator or error handler
        
        # Track command stats
        if cmd_name not in self._command_stats:
            self._command_stats[cmd_name] = {"count": 0, "errors": 0, "last_used": None, "rate_limited": 0}
        
        self._command_stats[cmd_name]["count"] += 1
        self._command_stats[cmd_name]["last_used"] = datetime.now()
        
        # Log command usage if enabled
        if self.config.get("security", {}).get("log_commands", True):
            self.logger.debug(f"Command executed: {cmd_name} by {ctx.author}")
    
    def _get_command_tier(self, command) -> RateLimitTier:
        """Determine rate limit tier for a command based on its cog"""
        if not command or not command.cog:
            return RateLimitTier.MODERATE
        
        cog_name = command.cog.__class__.__name__.lower()
        
        # Map cog names to tiers
        tier_mapping = {
            'nuke': RateLimitTier.CRITICAL,
            'purge': RateLimitTier.HEAVY,
            'moderation': RateLimitTier.HEAVY,
            'sniper': RateLimitTier.MODERATE,
            'automod': RateLimitTier.MODERATE,
            'admin': RateLimitTier.MODERATE,
            'utility': RateLimitTier.LIGHT,
            'fun': RateLimitTier.LIGHT,
            'help': RateLimitTier.MINIMAL,
            'ping': RateLimitTier.MINIMAL,
        }
        
        for key, tier in tier_mapping.items():
            if key in cog_name:
                return tier
        
        return RateLimitTier.MODERATE
    
    async def on_command_error(self, ctx, error):
        """Enhanced global command error handler with recovery logic"""
        
        # Prevent error spam with cooldown
        now = datetime.now()
        if self._last_error_time and (now - self._last_error_time) < self._error_cooldown:
            # Still log but don't send message to avoid spam
            should_notify = False
        else:
            should_notify = True
            self._last_error_time = now
        
        # Track error counts
        error_type = type(error).__name__
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        
        # Track per-command errors
        if ctx.command:
            cmd_name = ctx.command.name
            if cmd_name in self._command_stats:
                self._command_stats[cmd_name]["errors"] += 1
        
        try:
            # Command not found - silent ignore
            if isinstance(error, commands.CommandNotFound):
                return
            
            # Permission errors
            if isinstance(error, commands.MissingPermissions):
                missing = ", ".join(error.missing_permissions) if hasattr(error, 'missing_permissions') else "unknown"
                if should_notify:
                    await self._send_error_message(ctx, f"🔒 Missing permissions: `{missing}`")
                return
            
            if isinstance(error, commands.BotMissingPermissions):
                missing = ", ".join(error.missing_permissions) if hasattr(error, 'missing_permissions') else "unknown"
                if should_notify:
                    await self._send_error_message(ctx, f"🤖 I need permissions: `{missing}`")
                return
            
            # Cooldown errors
            if isinstance(error, commands.CommandOnCooldown):
                retry_after = getattr(error, 'retry_after', None)
                if retry_after:
                    if should_notify:
                        await self._send_error_message(ctx, f"⏱ Cooldown: Wait {retry_after:.1f}s", delete_after=3)
                return
            
            # Rate limit errors from our system
            if isinstance(error, commands.CheckFailure):
                # Check if it's a rate limit check failure
                if self._rate_limit_enabled and self._rate_limiter:
                    status = await self._rate_limiter.check_rate_limit(
                        guild_id=ctx.guild.id if ctx.guild else None,
                        user_id=ctx.author.id
                    )
                    if status.is_limited and should_notify:
                        await self._send_error_message(
                            ctx, 
                            f"⏱ Rate limited! Please wait {status.retry_after:.1f}s", 
                            delete_after=min(status.retry_after, 10)
                        )
                        return
            
            # Check failures
            if isinstance(error, commands.CheckFailure):
                if should_notify:
                    await self._send_error_message(ctx, "❌ You can't use this command")
                return
            
            # Argument errors
            if isinstance(error, commands.MissingRequiredArgument):
                param = error.param.name if hasattr(error, 'param') else "argument"
                if should_notify:
                    await self._send_error_message(ctx, f"❌ Missing required argument: `{param}`")
                return
            
            if isinstance(error, commands.BadArgument):
                if should_notify:
                    await self._send_error_message(ctx, f"❌ Invalid argument: {str(error)}")
                return
            
            if isinstance(error, commands.ArgumentParsingError):
                if should_notify:
                    await self._send_error_message(ctx, f"❌ Could not parse arguments: {str(error)}")
                return
            
            # Command invoke errors - unwrap the cause
            if isinstance(error, commands.CommandInvokeError):
                original = error.original
                
                # Handle specific Discord API errors
                if isinstance(original, discord.Forbidden):
                    if should_notify:
                        await self._send_error_message(ctx, "🔒 I don't have permission to do that")
                    return
                
                if isinstance(original, discord.NotFound):
                    if should_notify:
                        await self._send_error_message(ctx, "❌ Resource not found")
                    return
                
                if isinstance(original, discord.HTTPException):
                    if original.status == 429:  # Rate limited
                        if should_notify:
                            await self._send_error_message(ctx, "⚠️ Rate limited, please slow down")
                    else:
                        if should_notify:
                            await self._send_error_message(ctx, f"❌ Discord API error: {original.status}")
                    return
                
                # Log the full traceback for unexpected errors
                self.logger.error(f"Command error in {ctx.command}: {original}", exc_info=original)
                if should_notify:
                    await self._send_error_message(ctx, f"❌ An error occurred: {str(original)[:100]}")
                return
            
            # Catch-all for any other command errors
            self.logger.error(f"Unhandled command error: {error}", exc_info=error)
            if should_notify:
                await self._send_error_message(ctx, f"❌ Error: {str(error)[:100]}")
                
        except Exception as e:
            # Critical error in error handler - log to stderr
            self.logger.critical(f"Critical error in error handler: {e}", exc_info=e)
    
    async def _send_error_message(self, ctx, message: str, delete_after: int = 5):
        """Send error message with error handling"""
        try:
            await ctx.send(message, delete_after=delete_after)
        except discord.Forbidden:
            self.logger.warning(f"Cannot send error message: Forbidden in {ctx.channel.id}")
        except discord.HTTPException as e:
            self.logger.warning(f"Cannot send error message: HTTP {e.status}")
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")
    
    async def shutdown(self):
        """Graceful shutdown with cleanup"""
        if self._is_shutting_down:
            return
        
        self._is_shutting_down = True
        self.logger.info("Initiating graceful shutdown...")
        
        # Stop rate limiter
        if self._rate_limiter:
            try:
                await self._rate_limiter.stop()
                self.logger.info("Rate limiter stopped")
            except Exception as e:
                self.logger.error(f"Error stopping rate limiter: {e}")
        
        # Close aiohttp session
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                self.logger.info("HTTP session closed")
            except Exception as e:
                self.logger.error(f"Error closing HTTP session: {e}")
        
        # Log shutdown stats
        total_commands = sum(stats["count"] for stats in self._command_stats.values())
        total_errors = sum(stats["errors"] for stats in self._command_stats.values())
        total_rate_limited = sum(stats.get("rate_limited", 0) for stats in self._command_stats.values())
        self.logger.info(f"Session stats: {total_commands} commands, {total_errors} errors, {total_rate_limited} rate limited")
        
        # Close Discord connection
        try:
            await self.close()
            self.logger.info("Discord connection closed")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        # Signal shutdown complete
        self._shutdown_event.set()
        self.logger.info("Shutdown complete")
    
    async def wait_until_shutdown(self):
        """Wait for shutdown to complete"""
        await self._shutdown_event.wait()
    
    def run(self):
        """Run the bot with enhanced error handling and retry logic"""
        try:
            # Print startup message before screen manager takes over
            print(f"{Fore.CYAN}[*]{Style.RESET_ALL} Starting {self.brand_name} Bot...")
            
            # Run with auto-reconnect enabled
            super().run(self.token, reconnect=True)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!]{Style.RESET_ALL} Keyboard interrupt received")
            # Graceful shutdown is handled by the signal handler
            
        except LoginFailure as e:
            print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Invalid Discord token!")
            print(f"{Fore.RED}Details: {e}{Style.RESET_ALL}")
            sys.exit(1)
            
        except Exception as e:
            print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Fatal error: {e}")
            if self.logger:
                self.logger.exception("Fatal error")
            sys.exit(1)
