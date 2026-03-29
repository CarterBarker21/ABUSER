# ABUSER Bot - Complete Technical Framework

> **Version:** 1.0.0  
> **Type:** Discord Selfbot Framework with PyQt6 GUI  
> **Language:** Python 3.8+  
> **License:** MIT

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [GUI System](#gui-system)
5. [Rate Limiting System](#rate-limiting-system)
6. [Command System (Cogs)](#command-system-cogs)
7. [Token Management](#token-management)
8. [Theme System](#theme-system)
9. [Configuration](#configuration)
10. [Complete Source Code](#complete-source-code)
11. [Build & Run Instructions](#build--run-instructions)

---

## Architecture Overview

ABUSER follows a **multi-threaded architecture** with clear separation between GUI and bot logic:

```
┌─────────────────────────────────────────────────────────────┐
│                        MAIN THREAD                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PyQt6 GUI (MainWindow)                 │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │   │
│  │  │  Login  │ │ Guilds  │ │  Nuker  │ │ Settings │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         │ Qt Signals/Slots                  │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            BotRunner (Controller)                   │   │
│  │         - Manages bot thread lifecycle              │   │
│  │         - Bridges GUI and Bot                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Thread Boundary
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BOT THREAD                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ABUSERBot (discord.py-self)            │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │   │
│  │  │   Cogs      │ │ RateLimiter │ │ TokenManager │  │   │
│  │  │  (Commands) │ │  (811 lines)│ │              │  │   │
│  │  └─────────────┘ └─────────────┘ └──────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│              Discord API (discord.com)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
ABUSER/
├── abuse/                          # Main Python package
│   ├── __init__.py
│   ├── app_paths.py               # Path management system
│   ├── core/                      # Bot engine
│   │   ├── __init__.py
│   │   └── bot.py                 # ABUSERBot class (970 lines)
│   ├── cogs/                      # Command modules
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   └── serverinfo.py
│   │   ├── automod/
│   │   │   ├── __init__.py
│   │   │   └── afk.py
│   │   ├── fun/
│   │   │   ├── __init__.py
│   │   │   └── 8ball.py
│   │   ├── moderation/
│   │   │   ├── __init__.py
│   │   │   └── purge.py
│   │   ├── nuke/
│   │   │   ├── __init__.py
│   │   │   └── template.py
│   │   ├── sniper/
│   │   │   ├── __init__.py
│   │   │   └── nitro.py
│   │   ├── utility/
│   │   │   ├── __init__.py
│   │   │   ├── help.py
│   │   │   └── ping.py
│   │   ├── voice/
│   │   │   └── __init__.py
│   │   └── web/
│   │       ├── __init__.py
│   │       └── crypto.py
│   ├── gui/                       # PyQt6 Desktop GUI
│   │   ├── __init__.py
│   │   ├── bot_runner.py          # Bot thread manager (1000+ lines)
│   │   ├── components.py          # Reusable UI components
│   │   ├── config.py              # GUI configuration
│   │   ├── main_window.py         # Main window with custom title bar
│   │   ├── routes.py              # Navigation routing
│   │   ├── tabs.py                # Tab management
│   │   ├── theme.py               # Theme engine
│   │   ├── token_finder_thread.py # Token scanner thread
│   │   ├── pages/                 # Individual GUI pages
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Base page class
│   │   │   ├── login.py           # Token login page
│   │   │   ├── guilds.py          # Guild browser
│   │   │   ├── nuker.py           # Nuke controls
│   │   │   ├── dm.py              # DM composition
│   │   │   ├── logs.py            # Log viewer
│   │   │   ├── settings.py        # App settings
│   │   │   └── docs.py            # Documentation viewer
│   │   └── assets/
│   │       └── icons/             # SVG icons
│   ├── utils/                     # Utility modules
│   │   ├── __init__.py
│   │   ├── colors.py              # Terminal colors
│   │   ├── error_handler.py       # Error handling
│   │   ├── logger.py              # Logging utilities
│   │   ├── menu_system.py         # CLI menu system
│   │   ├── rate_limiter.py        # Rate limiting (811 lines)
│   │   ├── screen_manager.py      # Terminal display manager
│   │   ├── token_finder.py        # Discord token finder
│   │   └── token_manager.py       # Multi-token management
│   ├── data/                      # Data storage
│   │   └── __init__.py
│   └── tools/                     # Development tools
│       └── check_setup.py         # Setup diagnostic
├── config/                        # Configuration files
│   ├── config.json                # Bot configuration
│   ├── gui_config.json            # GUI settings
│   ├── theme_config.json          # Theme customization
│   └── .env                       # Environment variables
├── data/                          # Runtime data
│   ├── tokens.json                # Saved accounts
│   ├── tkn.txt                    # Legacy token file
│   └── logs/                      # Log files
├── tests/                         # Test suite
│   ├── conftest.py                # Pytest configuration
│   └── test_gui_smoke.py          # GUI smoke tests
├── dev/
│   └── requirements.txt           # Python dependencies
├── main.py                        # GUI entry point (215 lines)
├── run.bat                        # Windows launcher
└── AGENTS.md                      # AI agent guide
```

---

## Core Components

### 1. Entry Point (main.py)

**Purpose:** Initialize PyQt6 application, handle Windows consoleless mode, setup theme

**Key Features:**
- Redirects stdout/stderr to log file when running with pythonw.exe (no console)
- Prevents console window creation on Windows subprocess calls
- Sets up high DPI scaling
- Initializes theme before first paint

```python
#!/usr/bin/env python3
"""ABUSER Bot - GUI Entry Point"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Windows: Prevent console windows from subprocess calls
if sys.platform == "win32":
    import subprocess as _subprocess
    _original_popen = _subprocess.Popen
    CREATE_NO_WINDOW = 0x08000000
    
    class NoWindowPopen(_original_popen):
        def __init__(self, *args, **kwargs):
            if 'creationflags' in kwargs:
                kwargs['creationflags'] |= CREATE_NO_WINDOW
            else:
                kwargs['creationflags'] = CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
    
    _subprocess.Popen = NoWindowPopen

def main():
    from PyQt6.QtWidgets import QApplication
    from abuse.gui import MainWindow, get_theme_manager, BotRunner
    from abuse.gui.config import load_gui_config
    
    # Setup application
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("ABUSER Bot")
    app.setApplicationVersion("1.0.0")
    
    # Apply theme before creating window
    theme_manager = get_theme_manager()
    appearance = load_gui_config().get("appearance", {})
    theme_manager.switch_theme(
        appearance.get("preset", "Discord Dark"),
        appearance.get("accent", "Red").lower().replace(" ", "_"),
    )
    theme_manager.apply_theme(app)
    
    # Create window and bot runner
    window = MainWindow()
    bot_runner = BotRunner(parent=window)
    window.connect_bot_runner(bot_runner)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### 2. Bot Core (abuse/core/bot.py)

**Purpose:** Main bot class extending discord.ext.commands.Bot

**Key Features:**
- Selfbot mode enabled
- Automatic cog loading from abuse/cogs/
- Multi-layer rate limiting integration
- Graceful shutdown handling
- Connection retry logic with exponential backoff
- Performance tracking (command stats, error counts)
- Terminal screen management with banner

```python
import discord
from discord.ext import commands
from abuse.utils.rate_limiter import RateLimiter, RateLimitTier

class ABUSERBot(commands.Bot):
    def __init__(self):
        self.config = self._load_config()
        self.prefix = self.config.get("bot", {}).get("prefix", ".")
        self.token = self._get_token()
        self._rate_limit_enabled = True
        self._rate_limiter = None
        self._command_stats = {}
        self._error_counts = {}
        
        options = {
            'command_prefix': self.prefix,
            'self_bot': True,
            'help_command': None,
            'max_messages': 10000,
            'heartbeat_timeout': 60.0,
            'guild_ready_timeout': 10.0,
            'intents': discord.Intents.all()
        }
        super().__init__(**options)
    
    def _get_token(self) -> str:
        """Token priority: menu > tokens.json > tkn.txt > env > config"""
        # Implementation with validation
        pass
    
    async def setup_hook(self):
        """Initialize rate limiter and load cogs"""
        if self._rate_limit_enabled:
            await self._init_rate_limiter()
        await self._load_cogs_with_retry()
    
    async def _load_cogs_with_retry(self):
        """Load all cog folders with retry logic"""
        cog_folders = [
            "utility", "admin", "fun", "moderation",
            "automod", "nuke", "sniper", "voice", "web"
        ]
        for folder in cog_folders:
            await self._load_cog_with_retry(folder)
    
    async def on_ready(self):
        """Display banner and start background tasks"""
        self._refresh_display()
        await self._set_status_with_retry()
    
    async def on_command_error(self, ctx, error):
        """Global error handler with cooldown to prevent spam"""
        # Handles: CommandNotFound, MissingPermissions, Cooldown, etc.
        pass
```

### 3. Path Management (abuse/app_paths.py)

**Purpose:** Centralized path resolution supporting environment overrides

```python
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).parent.parent

# Environment variable overrides
ENV_OVERRIDES = {
    "ABUSER_CONFIG_DIR": "config_dir",
    "ABUSER_DATA_DIR": "data_dir",
    "ABUSER_BOT_CONFIG_PATH": "bot_config",
    "ABUSER_GUI_CONFIG_PATH": "gui_config",
    "ABUSER_TOKENS_PATH": "tokens",
    "ABUSER_LOG_FILE": "log_file",
}

def bot_config_path() -> Path:
    """Get bot config.json path"""
    if env := os.getenv("ABUSER_BOT_CONFIG_PATH"):
        return Path(env)
    return PROJECT_ROOT / "config" / "config.json"

def data_dir() -> Path:
    """Get data directory"""
    if env := os.getenv("ABUSER_DATA_DIR"):
        return Path(env)
    return PROJECT_ROOT / "data"

def tokens_file_path() -> Path:
    """Get tokens.json path"""
    if env := os.getenv("ABUSER_TOKENS_PATH"):
        return Path(env)
    return data_dir() / "tokens.json"

def legacy_token_file_path() -> Path:
    """Get legacy tkn.txt path"""
    return data_dir() / "tkn.txt"

def env_file_path() -> Path:
    """Get .env file path"""
    return PROJECT_ROOT / "config" / ".env"

def log_file_path() -> Path:
    """Get log file path"""
    if env := os.getenv("ABUSER_LOG_FILE"):
        return Path(env)
    return data_dir() / "logs" / "abuse.log"

def bootstrap_runtime_layout():
    """Ensure all required directories exist"""
    data_dir().mkdir(parents=True, exist_ok=True)
    (data_dir() / "logs").mkdir(parents=True, exist_ok=True)
```

---

## GUI System

### Architecture

```
MainWindow (QMainWindow)
├── TitleBar (Custom QWidget)
│   ├── Brand Label ("ABUSER")
│   ├── Minimize Button
│   └── Close Button
├── Sidebar (QWidget)
│   ├── Navigation Buttons (SidebarNavButton)
│   └── Status Panel (SidebarStatusPanel)
└── Content Area (QStackedWidget)
    ├── LoginPage
    ├── GuildsPage
    ├── NukerPage
    ├── DMPage
    ├── LogsPage
    ├── SettingsPage
    └── DocsPage
```

### Main Window (abuse/gui/main_window.py)

**Features:**
- Frameless window with custom title bar
- Drag-to-move functionality
- Acrylic/blur effects support
- Theme-aware styling
- Signal-based navigation

```python
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, QPoint

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Central widget
        self.central = QWidget()
        self.setCentralWidget(self.central)
        
        # Layout: Sidebar + Content
        layout = QHBoxLayout(self.central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = self._build_sidebar()
        layout.addWidget(self.sidebar)
        
        # Content area with stacked pages
        self.content = QStackedWidget()
        layout.addWidget(self.content)
        
        # Build pages
        self._build_pages()
        
        # Connect navigation
        self._setup_routes()
    
    def _build_sidebar(self):
        """Create sidebar with nav buttons"""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        
        # Navigation buttons
        self.nav_buttons = {
            "login": SidebarNavButton("Login", "login"),
            "guilds": SidebarNavButton("Guilds", "guilds"),
            "nuker": SidebarNavButton("Nuker", "nuker"),
            "dm": SidebarNavButton("DM", "dm"),
            "logs": SidebarNavButton("Logs", "logs"),
            "settings": SidebarNavButton("Settings", "settings"),
            "docs": SidebarNavButton("Docs", "docs"),
        }
        
        for btn in self.nav_buttons.values():
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Status panel
        self.status_panel = SidebarStatusPanel()
        layout.addWidget(self.status_panel)
        
        return sidebar
    
    def _build_pages(self):
        """Initialize all pages"""
        from .pages import LoginPage, GuildsPage, NukerPage, DMPage, LogsPage, SettingsPage, DocsPage
        
        self.pages = {
            "login": LoginPage(),
            "guilds": GuildsPage(),
            "nuker": NukerPage(),
            "dm": DMPage(),
            "logs": LogsPage(),
            "settings": SettingsPage(),
            "docs": DocsPage(),
        }
        
        for page in self.pages.values():
            self.content.addWidget(page)
    
    def navigate_to(self, route: str):
        """Switch to page by route name"""
        if route in self.pages:
            self.content.setCurrentWidget(self.pages[route])
            # Update sidebar button states
            for name, btn in self.nav_buttons.items():
                btn.set_active(name == route)
    
    def connect_bot_runner(self, bot_runner):
        """Connect BotRunner signals to UI"""
        # Login signals
        self.pages["login"].login_requested.connect(bot_runner.start_bot)
        self.pages["login"].logout_requested.connect(bot_runner.stop_bot)
        
        # Status signals
        bot_runner.status_changed.connect(self.status_panel.update_status)
        bot_runner.connection_changed.connect(self._on_connection_changed)
        
        # Guild list
        bot_runner.guilds_updated.connect(self.pages["guilds"].update_guilds)
```

### Bot Runner (abuse/gui/bot_runner.py)

**Purpose:** Manages bot lifecycle in separate thread, bridges GUI and Bot

**Signals Emitted:**
- `status_changed(str)` - Connection status updates
- `connection_changed(bool)` - Connected/disconnected
- `guilds_updated(list)` - Guild list updates
- `logs_updated(str)` - New log lines
- `latency_updated(int)` - Ping/latency updates

```python
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from abuse.core.bot import ABUSERBot

class BotWorker(QThread):
    """Runs bot in separate thread"""
    
    log_received = pyqtSignal(str)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    guilds_ready = pyqtSignal(list)
    
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.bot = None
        self._running = False
    
    def run(self):
        """Thread entry point"""
        self._running = True
        self.bot = ABUSERBot()
        
        # Override logger to emit signals
        # ... setup logging redirection
        
        try:
            self.bot.run()
        except Exception as e:
            self.log_received.emit(f"[ERROR] {e}")
        finally:
            self._running = False
            self.disconnected.emit()
    
    def stop(self):
        """Request graceful shutdown"""
        if self.bot:
            asyncio.run_coroutine_threadsafe(
                self.bot.shutdown(),
                self.bot.loop
            )

class BotRunner(QObject):
    """Controller managing BotWorker thread"""
    
    status_changed = pyqtSignal(str)
    connection_changed = pyqtSignal(bool)
    guilds_updated = pyqtSignal(list)
    logs_updated = pyqtSignal(str)
    latency_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.thread = None
        self.is_running = False
    
    def start_bot(self, token: str):
        """Start bot in new thread"""
        if self.is_running:
            return
        
        self.worker = BotWorker(token)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.connected.connect(self._on_connected)
        self.worker.disconnected.connect(self._on_disconnected)
        self.worker.log_received.connect(self.logs_updated)
        self.worker.guilds_ready.connect(self.guilds_updated)
        
        self.thread.started.connect(self.worker.run)
        self.thread.start()
        self.is_running = True
        self.status_changed.emit("Connecting...")
    
    def stop_bot(self):
        """Stop bot gracefully"""
        if self.worker and self.is_running:
            self.worker.stop()
            self.thread.quit()
            self.thread.wait(5000)
            self.is_running = False
    
    def _on_connected(self):
        self.connection_changed.emit(True)
        self.status_changed.emit("Connected")
    
    def _on_disconnected(self):
        self.connection_changed.emit(False)
        self.status_changed.emit("Disconnected")
```

---

## Rate Limiting System

### Architecture

The rate limiter uses a **multi-layer token bucket** approach:

```
Request Flow:
┌─────────────┐
│   Command   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│       Global Rate Limiter           │
│   (50 req/s max, burst: 10)        │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│        Tier Rate Limiter            │
│  CRITICAL: 0.1/s  MODERATE: 2/s    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│       Guild Rate Limiter            │
│      (10 req/s per guild)          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│       User Rate Limiter             │
│       (5 req/s per user)           │
└──────┬──────────────────────────────┘
       │
       ▼
   [Execute]
```

### Implementation (abuse/utils/rate_limiter.py)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple
import asyncio
import time

class RateLimitTier(Enum):
    CRITICAL = "critical"      # 0.1 req/s - Nuke commands
    HEAVY = "heavy"            # 0.5 req/s - Bulk operations
    MODERATE = "moderate"      # 2.0 req/s - Normal commands
    LIGHT = "light"            # 5.0 req/s - Simple commands
    MINIMAL = "minimal"        # 10.0 req/s - Read-only

@dataclass
class RateLimitConfig:
    global_requests_per_second: float = 50.0
    global_burst_size: int = 10
    
    tier_limits: Dict[RateLimitTier, Tuple[float, int]] = None
    
    def __post_init__(self):
        if self.tier_limits is None:
            self.tier_limits = {
                RateLimitTier.CRITICAL: (0.1, 1),
                RateLimitTier.HEAVY: (0.5, 3),
                RateLimitTier.MODERATE: (2.0, 5),
                RateLimitTier.LIGHT: (5.0, 10),
                RateLimitTier.MINIMAL: (10.0, 20),
            }

class TokenBucket:
    """Token bucket algorithm for smooth rate limiting"""
    
    def __init__(self, rate: float, burst_size: int):
        self.rate = rate
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            
            # Replenish tokens based on elapsed time
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            
            # Calculate retry after time
            needed = tokens - self.tokens
            retry_after = needed / self.rate
            return False, retry_after

class RateLimiter:
    """Multi-layer rate limiter"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        
        # Global bucket
        self.global_bucket = TokenBucket(
            self.config.global_requests_per_second,
            self.config.global_burst_size
        )
        
        # Tier buckets
        self.tier_buckets: Dict[RateLimitTier, TokenBucket] = {}
        for tier, (rate, burst) in self.config.tier_limits.items():
            self.tier_buckets[tier] = TokenBucket(rate, burst)
        
        # Per-guild and per-user buckets
        self.guild_buckets: Dict[int, TokenBucket] = {}
        self.user_buckets: Dict[int, TokenBucket] = {}
    
    async def check_rate_limit(
        self,
        tier: RateLimitTier = RateLimitTier.MODERATE,
        guild_id: int = None,
        user_id: int = None
    ) -> RateLimitStatus:
        """Check all rate limit layers"""
        
        # Check global
        global_ok, global_retry = await self.global_bucket.consume()
        if not global_ok:
            return RateLimitStatus(
                is_limited=True,
                retry_after=global_retry,
                remaining_requests=0,
                total_requests=0,
                queue_size=0
            )
        
        # Check tier
        tier_bucket = self.tier_buckets[tier]
        tier_ok, tier_retry = await tier_bucket.consume()
        if not tier_ok:
            return RateLimitStatus(
                is_limited=True,
                retry_after=tier_retry,
                remaining_requests=0,
                total_requests=0,
                queue_size=0
            )
        
        # Check guild-specific (if applicable)
        if guild_id:
            if guild_id not in self.guild_buckets:
                self.guild_buckets[guild_id] = TokenBucket(10.0, 5)
            guild_ok, guild_retry = await self.guild_buckets[guild_id].consume()
            if not guild_ok:
                return RateLimitStatus(
                    is_limited=True,
                    retry_after=guild_retry,
                    remaining_requests=0,
                    total_requests=0,
                    queue_size=0
                )
        
        # Check user-specific (if applicable)
        if user_id:
            if user_id not in self.user_buckets:
                self.user_buckets[user_id] = TokenBucket(5.0, 3)
            user_ok, user_retry = await self.user_buckets[user_id].consume()
            if not user_ok:
                return RateLimitStatus(
                    is_limited=True,
                    retry_after=user_retry,
                    remaining_requests=0,
                    total_requests=0,
                    queue_size=0
                )
        
        # All checks passed
        return RateLimitStatus(
            is_limited=False,
            retry_after=0.0,
            remaining_requests=int(self.global_bucket.tokens),
            total_requests=0,
            queue_size=0
        )

# Convenience decorators for commands
def rate_limit_critical(func):
    """Decorator for CRITICAL tier commands"""
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        bot = ctx.bot
        if hasattr(bot, 'rate_limiter') and bot.rate_limiter:
            status = await bot.check_rate_limit(
                tier=RateLimitTier.CRITICAL,
                guild_id=ctx.guild.id if ctx.guild else None,
                user_id=ctx.author.id
            )
            if status.is_limited:
                await ctx.send(f"⏱ Rate limited! Wait {status.retry_after:.1f}s")
                return
        return await func(self, ctx, *args, **kwargs)
    return wrapper

def rate_limit_heavy(func):
    """Decorator for HEAVY tier commands"""
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        # Similar implementation with HEAVY tier
        pass
    return wrapper

# Additional decorators: rate_limit_moderate, rate_limit_light, rate_limit_minimal
```

---

## Command System (Cogs)

### Cog Structure

Each cog folder contains:
- `__init__.py` - Auto-loads all command modules
- Individual command files

### Example Cog Implementation

```python
# abuse/cogs/moderation/purge.py
from discord.ext import commands
from abuse.utils.rate_limiter import rate_limit_heavy

class Purge(commands.Cog):
    """Message purge commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @rate_limit_heavy  # 0.5 req/s limit
    async def purge(self, ctx, amount: int = 10):
        """Delete messages from channel"""
        if amount < 1 or amount > 1000:
            await ctx.send("Amount must be between 1 and 1000")
            return
        
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"Deleted {len(deleted)} messages", delete_after=5)
    
    @commands.command()
    @rate_limit_heavy
    async def clean(self, ctx, amount: int = 10):
        """Delete only bot messages"""
        def is_bot(m):
            return m.author.bot
        
        deleted = await ctx.channel.purge(limit=amount, check=is_bot)
        await ctx.send(f"Cleaned {len(deleted)} bot messages", delete_after=5)

async def setup(bot):
    await bot.add_cog(Purge(bot))
```

### Cog Loader (__init__.py)

```python
# abuse/cogs/moderation/__init__.py
import os
import importlib
from discord.ext import commands

async def setup(bot: commands.Bot):
    """Automatically load all modules in this package"""
    current_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'abuse.cogs.moderation.{module_name}')
                if hasattr(module, 'setup'):
                    await module.setup(bot)
            except Exception as e:
                print(f"Failed to load {module_name}: {e}")
```

### Nuke Template (Placeholder)

```python
# abuse/cogs/nuke/template.py
from discord.ext import commands
from abuse.utils.rate_limiter import rate_limit_critical

class NukeTemplate(commands.Cog):
    """
    Nuke commands template - IMPLEMENT WITH CAUTION
    ⚠️ WARNING: These commands can destroy servers!
    Rate limited to CRITICAL tier (1 per 10 seconds)
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    # Template only - NOT IMPLEMENTED
    # @commands.command()
    # @rate_limit_critical
    # async def nuke(self, ctx):
    #     """⚠️ DESTROY SERVER - USE WITH EXTREME CAUTION"""
    #     pass

async def setup(bot):
    await bot.add_cog(NukeTemplate(bot))
```

---

## Token Management

### Token Manager (abuse/utils/token_manager.py)

```python
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class Account:
    token: str
    name: str = ""
    user_id: str = ""
    is_valid: bool = False

class TokenManager:
    """Manages multiple Discord tokens"""
    
    def __init__(self, tokens_path: Path = None):
        self.tokens_path = tokens_path or tokens_file_path()
        self.accounts: List[Account] = []
        self.selected_account: Optional[Account] = None
        self._load_accounts()
    
    def _load_accounts(self):
        """Load accounts from tokens.json"""
        if not self.tokens_path.exists():
            return
        
        try:
            with open(self.tokens_path, 'r') as f:
                data = json.load(f)
            
            for acc_data in data.get('accounts', []):
                account = Account(
                    token=acc_data.get('token', ''),
                    name=acc_data.get('name', ''),
                    user_id=acc_data.get('user_id', ''),
                    is_valid=acc_data.get('is_valid', False)
                )
                self.accounts.append(account)
        except Exception as e:
            print(f"Error loading accounts: {e}")
    
    def save_accounts(self):
        """Save accounts to tokens.json"""
        data = {
            'accounts': [
                {
                    'token': acc.token,
                    'name': acc.name,
                    'user_id': acc.user_id,
                    'is_valid': acc.is_valid
                }
                for acc in self.accounts
            ]
        }
        
        self.tokens_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tokens_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_account(self, token: str, name: str = "", user_id: str = ""):
        """Add new account"""
        account = Account(token=token, name=name, user_id=user_id)
        self.accounts.append(account)
        self.save_accounts()
    
    def select_account(self, index: int) -> Optional[Account]:
        """Select account by index"""
        if 0 <= index < len(self.accounts):
            self.selected_account = self.accounts[index]
            return self.selected_account
        return None
    
    def remove_account(self, index: int):
        """Remove account by index"""
        if 0 <= index < len(self.accounts):
            self.accounts.pop(index)
            self.save_accounts()

# Singleton instance
_token_manager: Optional[TokenManager] = None

def get_token_manager() -> TokenManager:
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
```

---

## Theme System

### Theme Engine (abuse/gui/theme.py)

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class ThemeColors:
    """Complete color palette for a theme"""
    # Backgrounds
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    
    # Surfaces
    surface: str
    surface_hover: str
    surface_active: str
    
    # Accents
    accent_primary: str
    accent_secondary: str
    
    # Text
    text_primary: str
    text_secondary: str
    text_muted: str
    
    # Borders
    border_light: str
    border_dark: str
    
    # Status
    success: str
    warning: str
    error: str
    info: str

class ThemeManager:
    """Manages application themes"""
    
    PRESETS = {
        "Midnight": ThemeColors(
            bg_primary="#0a0a0f",
            bg_secondary="#0f0f16",
            bg_tertiary="#13131f",
            surface="#1a1a24",
            surface_hover="#22222e",
            surface_active="#2a2a38",
            accent_primary="#6366f1",
            accent_secondary="#818cf8",
            text_primary="#fafafa",
            text_secondary="#a1a1aa",
            text_muted="#71717a",
            border_light="#27272a",
            border_dark="#18181b",
            success="#22c55e",
            warning="#eab308",
            error="#ef4444",
            info="#3b82f6",
        ),
        "Discord Dark": ThemeColors(
            bg_primary="#36393f",
            bg_secondary="#2f3136",
            bg_tertiary="#202225",
            surface="#40444b",
            surface_hover="#4f545c",
            surface_active="#5d6269",
            accent_primary="#5865f2",
            accent_secondary="#7289da",
            text_primary="#ffffff",
            text_secondary="#b9bbbe",
            text_muted="#72767d",
            border_light="#40444b",
            border_dark="#202225",
            success="#3ba55d",
            warning="#faa81a",
            error="#ed4245",
            info="#5865f2",
        ),
        # ... more presets
    }
    
    ACCENTS = {
        "discord_blue": "#5865f2",
        "red": "#ef4444",
        "green": "#22c55e",
        "purple": "#a855f7",
        "orange": "#f97316",
        "pink": "#ec4899",
        "cyan": "#06b6d4",
        "yellow": "#eab308",
    }
    
    def __init__(self):
        self.current_preset = "Discord Dark"
        self.current_accent = "red"
        self.colors = self._build_colors()
    
    def _build_colors(self) -> ThemeColors:
        """Build theme colors with accent override"""
        base = self.PRESETS[self.current_preset]
        accent = self.ACCENTS[self.current_accent]
        
        # Create new colors with accent override
        return ThemeColors(
            **{**base.__dict__, 'accent_primary': accent}
        )
    
    def switch_theme(self, preset: str, accent: str):
        """Change theme preset and accent"""
        if preset in self.PRESETS:
            self.current_preset = preset
        if accent in self.ACCENTS:
            self.current_accent = accent
        self.colors = self._build_colors()
    
    def apply_theme(self, app):
        """Apply theme to QApplication"""
        c = self.colors
        stylesheet = f"""
        QMainWindow {{
            background-color: {c.bg_primary};
            color: {c.text_primary};
        }}
        QWidget {{
            background-color: {c.bg_primary};
            color: {c.text_primary};
            font-family: "Segoe UI", sans-serif;
        }}
        QPushButton {{
            background-color: {c.surface};
            color: {c.text_primary};
            border: 1px solid {c.border_light};
            border-radius: 6px;
            padding: 8px 16px;
        }}
        QPushButton:hover {{
            background-color: {c.surface_hover};
        }}
        QPushButton:pressed {{
            background-color: {c.surface_active};
        }}
        QLineEdit {{
            background-color: {c.surface};
            color: {c.text_primary};
            border: 1px solid {c.border_light};
            border-radius: 4px;
            padding: 8px;
        }}
        QTextEdit {{
            background-color: {c.bg_secondary};
            color: {c.text_primary};
            border: 1px solid {c.border_light};
            border-radius: 4px;
        }}
        QListWidget {{
            background-color: {c.bg_secondary};
            color: {c.text_primary};
            border: 1px solid {c.border_light};
            border-radius: 4px;
        }}
        """
        app.setStyleSheet(stylesheet)

# Singleton
theme_manager = ThemeManager()

def get_theme_manager():
    return theme_manager
```

---

## Configuration

### config/config.json

```json
{
  "bot": {
    "prefix": ".",
    "status": "online",
    "activity": {
      "type": "playing",
      "name": "ABUSER SelfBot"
    }
  },
  "security": {
    "safe_mode": true,
    "confirm_destructive": true,
    "log_commands": true
  },
  "performance": {
    "rate_limiting_enabled": true,
    "global_rate_limit": 50.0,
    "global_burst_size": 10,
    "max_retries": 3,
    "retry_delay_seconds": 1.0
  },
  "logging": {
    "level": "INFO",
    "file": "./data/logs/abuse.log"
  },
  "connection": {
    "auto_reconnect": true,
    "max_reconnect_attempts": 5,
    "reconnect_delay": 5.0
  }
}
```

### config/gui_config.json

```json
{
  "appearance": {
    "theme_preset": "Discord Dark",
    "accent": "Red",
    "font_size": 10,
    "font_family": "Segoe UI"
  },
  "behavior": {
    "startup_page": "login",
    "confirm_exit": true,
    "minimize_to_tray": false
  },
  "privacy": {
    "save_tokens": true,
    "encrypt_tokens": false,
    "auto_login": false
  },
  "window": {
    "width": 1200,
    "height": 800,
    "remember_position": true
  }
}
```

---

## Complete Source Code

### Key Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| main.py | 215 | Entry point, PyQt6 init |
| abuse/core/bot.py | 970 | Main bot class |
| abuse/gui/bot_runner.py | 1000+ | Thread management |
| abuse/utils/rate_limiter.py | 811 | Rate limiting |
| abuse/gui/main_window.py | 500+ | Main GUI window |
| abuse/gui/theme.py | 300+ | Theme engine |

---

## Build & Run Instructions

### Requirements (dev/requirements.txt)

```
PyQt6>=6.4.0
discord.py-self>=2.0.0
aiohttp>=3.8.0
python-dotenv>=0.20.0
colorama>=0.4.5
pycryptodome>=3.15.0
pytest-qt>=4.5.0
```

### Installation

```bash
# Clone repository
git clone <repo-url>
cd ABUSER

# Install dependencies
pip install -r dev/requirements.txt
```

### Running

```bash
# GUI Mode (Windows - no console window)
run.bat

# Or directly with Python
python main.py

# Setup diagnostic
python -m abuse.tools.check_setup
```

### Building Executable (Optional)

```bash
# Using PyInstaller
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --icon=icon.ico main.py
```

---

## Security & Safety Features

1. **Rate Limiting:** Multi-layer protection prevents API bans
2. **Safe Mode:** Config prevents destructive operations
3. **Confirmation Dialogs:** Destructive actions require confirmation
4. **Token Validation:** Tokens validated before use
5. **Error Cooldowns:** Prevents error message spam

---

## Thread Safety Model

```
┌─────────────────┐     Qt Signals      ┌─────────────────┐
│   GUI Thread    │ ◄─────────────────► │   Bot Thread    │
│  (MainWindow)   │                     │  (ABUSERBot)    │
└─────────────────┘                     └─────────────────┘
       │                                         │
       │         All UI updates                  │
       │         must use signals                │
       │                                         │
       └────────► Never call Discord API ◄───────┘
                  directly from GUI!
```

---

**End of Framework Documentation**
