# ABUSER Bot - AI Agent Guide

## Project Overview

ABUSER (Advanced Bot for User Server Enhancement & Raiding) is a comprehensive Discord selfbot framework with a PyQt6 desktop GUI. It provides utility, moderation, automation, and server management features through both a command-line interface and a modern graphical interface.

**Version:** 1.0.0  
**License:** MIT  
**Language:** English (all code comments and documentation)

---

## Technology Stack

### Core Dependencies
- **Python 3.8+** - Runtime environment
- **discord.py-self>=2.0.0** - Discord API wrapper (selfbot fork)
- **PyQt6>=6.4.0** - Desktop GUI framework
- **aiohttp>=3.8.0** - Async HTTP client
- **python-dotenv>=0.20.0** - Environment variable management
- **colorama>=0.4.5** - Terminal colors
- **pycryptodome>=3.15.0** - Encryption (for token finder)
- **pytest-qt>=4.5.0** - GUI testing framework

### Project Structure
```
ABUSER/
├── abuse/                      # Main package
│   ├── core/                   # Bot core engine
│   │   └── bot.py              # ABUSERBot main class (970 lines)
│   ├── cogs/                   # Command modules (by category)
│   │   ├── admin/              # Admin commands (serverinfo)
│   │   ├── automod/            # Automation (AFK)
│   │   ├── fun/                # Fun commands (8ball)
│   │   ├── moderation/         # Moderation (purge)
│   │   ├── nuke/               # Server destruction commands
│   │   ├── sniper/             # Nitro sniper
│   │   ├── utility/            # Utility (help, ping)
│   │   ├── voice/              # Voice features (placeholder)
│   │   └── web/                # Web commands (crypto)
│   ├── gui/                    # PyQt6 desktop GUI
│   │   ├── pages/              # GUI pages/tabs
│   │   │   ├── login.py        # Token login page
│   │   │   ├── guilds.py       # Guild browser
│   │   │   ├── nuker.py        # Nuke controls
│   │   │   ├── dm.py           # DM composition
│   │   │   ├── logs.py         # Log viewer
│   │   │   ├── settings.py     # App settings
│   │   │   └── docs.py         # Documentation
│   │   ├── bot_runner.py       # Bot thread management (1000+ lines)
│   │   ├── main_window.py      # Main GUI window
│   │   ├── theme.py            # Theme system
│   │   ├── routes.py           # Navigation routes
│   │   └── components.py       # Reusable UI components
│   ├── utils/                  # Utilities
│   │   ├── rate_limiter.py     # Rate limiting system (811 lines)
│   │   ├── token_manager.py    # Multi-token management
│   │   ├── token_finder.py     # Discord token finder
│   │   ├── logger.py           # Logging utilities
│   │   ├── error_handler.py    # Error handling
│   │   ├── colors.py           # Color utilities
│   │   ├── menu_system.py      # CLI menu system
│   │   └── screen_manager.py   # Terminal screen manager
│   ├── data/                   # Data storage
│   ├── app_paths.py            # Path management
│   └── tools/                  # Development tools
│       └── check_setup.py      # Setup diagnostic
├── config/                     # Configuration files
│   ├── config.json             # Bot configuration
│   ├── gui_config.json         # GUI settings
│   ├── theme_config.json       # Theme customization
│   └── .env                    # Environment variables
├── data/                       # Runtime data
│   ├── tokens.json             # Saved accounts
│   ├── tkn.txt                 # Legacy token file
│   └── logs/                   # Log files
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest configuration
│   └── test_gui_smoke.py       # GUI smoke tests
├── dev/                        # Development files
│   └── requirements.txt        # Python dependencies
├── main.py                     # GUI entry point
├── run.bat                     # Windows launcher (VBScript-based)
└── run_silent.bat              # Silent Windows launcher
```

---

## Build and Run Commands

### Installation
```bash
# Install dependencies
pip install -r dev/requirements.txt
```

### Running the Application

**GUI Mode (Windows):**
```bash
# Using the batch file (no console window)
run.bat

# Or directly with Python
python main.py

# For testing/debugging (with console)
python main.py
```

**Setup Diagnostic:**
```bash
python -m abuse.tools.check_setup
```

### Running Tests

```bash
# Run all tests
pytest

# Run GUI tests with offscreen platform
pytest tests/test_gui_smoke.py -v

# Run with coverage
pytest --cov=abuse tests/
```

---

## Code Style Guidelines

### Python Style
- **PEP 8** compliant with 4-space indentation
- **Line length:** 120 characters maximum
- **Quotes:** Double quotes for docstrings, single quotes acceptable elsewhere
- **Type hints:** Encouraged for function signatures
- **Docstrings:** Google-style docstrings for all public functions/classes

### Naming Conventions
- **Classes:** `PascalCase` (e.g., `ABUSERBot`, `MainWindow`, `RateLimiter`)
- **Functions/Methods:** `snake_case` (e.g., `start_bot`, `check_rate_limit`)
- **Constants:** `UPPER_CASE` (e.g., `ROUTE_LOGIN`, `MAX_RETRIES`)
- **Private:** Leading underscore (e.g., `_load_config`, `_is_running`)
- **Modules:** `snake_case` (e.g., `rate_limiter.py`, `token_manager.py`)

### Import Order
1. Standard library imports
2. Third-party imports (PyQt6, discord)
3. Local package imports (from abuse...)

### Async/Await Patterns
- All Discord API calls are async
- GUI uses Qt signals/slots for thread safety
- Bot runs in separate thread via `BotWorker`

---

## Testing Instructions

### Test Configuration
Tests use `pytest-qt` with an offscreen platform for headless testing:

```python
# conftest.py sets up:
QT_QPA_PLATFORM = offscreen
ABUSER_GUI_CONFIG_PATH = temp path
ABUSER_TOKENS_PATH = temp path
ABUSER_THEME_CONFIG_PATH = temp path
```

### Writing GUI Tests
```python
def test_example(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Interact with GUI
    qtbot.mouseClick(window.some_button, Qt.MouseButton.LeftButton)
    
    # Assert state
    assert window.some_label.text() == "Expected"
```

### Test Coverage Areas
- GUI navigation and routing
- Bot runner signal connections
- Settings persistence
- Token management
- Theme switching

---

## Architecture Details

### Bot Core (`abuse/core/bot.py`)
- Extends `discord.ext.commands.Bot`
- Selfbot mode enabled (`self_bot=True`)
- Automatic cog loading from `abuse/cogs/`
- Built-in rate limiting integration
- Graceful shutdown handling
- Screen manager for terminal display

### GUI Architecture (`abuse/gui/`)
- **MVC-like pattern:** Pages are views, BotRunner is controller
- **Signal-based communication:** Thread-safe updates from bot to GUI
- **Theme system:** 10+ presets with 8 accent colors
- **Route-based navigation:** 7 main routes (login, docs, guilds, nuker, dm, logs, settings)

### Rate Limiting (`abuse/utils/rate_limiter.py`)
- **Token bucket algorithm** at multiple levels:
  - Global: 50 req/s max
  - Tier-based: Critical (0.1/s), Heavy (0.5/s), Moderate (2/s), Light (5/s), Minimal (10/s)
  - Per-guild: 10 req/s
  - Per-user: 5 req/s
- **Command decorators:** `@rate_limit_critical`, `@rate_limit_heavy`, etc.
- **Automatic retry** with exponential backoff
- **Command queue** with priority handling

### Cog Structure
Each cog folder contains:
- `__init__.py` - Auto-loads all command modules
- Individual command files (e.g., `purge.py`, `help.py`)

Example cog:
```python
from discord.ext import commands

class MyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def mycmd(self, ctx):
        """Command description"""
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(MyCommand(bot))
```

---

## Configuration Files

### `config/config.json`
Bot configuration including:
- Command prefix (default: `.`)
- Security settings (safe mode, confirm destructive)
- Performance settings (rate limits, retries)
- Connection settings (reconnect behavior)

### `config/gui_config.json`
GUI settings including:
- Appearance (theme, accent, font size)
- Behavior (startup page, confirmations)
- Privacy (token saving, encryption)

### `config/theme_config.json`
Custom theme colors (CSS-style hex values)

### `config/.env`
Environment variables:
```bash
DISCORD_TOKEN=your_token_here
```

### `data/tokens.json`
Saved accounts with metadata:
```json
{
  "accounts": [
    {
      "token": "...",
      "name": "username",
      "user_id": "...",
      "is_valid": true
    }
  ]
}
```

---

## Path Management

All paths centralized in `abuse/app_paths.py`:
- Supports environment variable overrides
- Legacy path migration
- Cross-platform compatibility

Environment variable overrides:
- `ABUSER_CONFIG_DIR` - Config directory
- `ABUSER_DATA_DIR` - Data directory
- `ABUSER_BOT_CONFIG_PATH` - Bot config file
- `ABUSER_GUI_CONFIG_PATH` - GUI config file
- `ABUSER_TOKENS_PATH` - Tokens file
- `ABUSER_LOG_FILE` - Log file path

---

## Security Considerations

### Token Management
- Tokens stored in `data/tokens.json` (JSON format)
- Optional encryption support (planned)
- Token validation before use
- Multiple token sources supported (file, env, config, tokens.json)

### Rate Limiting
- Prevents Discord API bans
- Tier-based limits for destructive operations
- Automatic retry with exponential backoff
- Queue system for command overflow

### Safe Mode
- `safe_mode` setting in config prevents destructive operations
- `confirm_destructive` shows confirmation dialogs
- Nuke commands are rate-limited to CRITICAL tier

---

## Development Notes

### Adding a New Command
1. Create file in appropriate `abuse/cogs/<category>/` folder
2. Implement as `commands.Cog` subclass
3. Add `setup(bot)` async function
4. Apply appropriate rate limit decorator
5. Add error handler for command-specific errors

### Adding a New GUI Page
1. Create file in `abuse/gui/pages/`
2. Extend `BasePage` class
3. Add route to `routes.py`
4. Register in `main_window.py` `_build_ui()`
5. Add navigation button in `_build_sidebar()`

### Thread Safety
- Bot runs in separate thread via `BotWorker`
- Use Qt signals for cross-thread communication
- Never access Discord API directly from GUI thread

---

## Troubleshooting

### Common Issues
1. **Import errors:** Ensure you're in the project root when running
2. **Qt platform errors:** Set `QT_QPA_PLATFORM=offscreen` for headless
3. **Token not found:** Check `config/.env` or `data/tokens.json`
4. **Rate limited:** Check rate limiter status in logs

### Debug Mode
```python
# In config.json
"logging": {
    "level": "DEBUG"
}
```

---

## Available Themes

The GUI supports multiple preset themes:
- **Midnight** (very dark)
- **Obsidian** (pure black/dark gray)
- **Discord Dark** (classic Discord)
- **Catppuccin Mocha** (popular dark theme)
- **Dracula** (purple-tinted dark)
- **Nord** (arctic bluish dark)
- **Light** (clean white)
- **GitHub Light** (professional light)
- **Solarized Light**
- **Cyberpunk** (neon accents on dark)
- **Sunset** (warm oranges/reds)
- **Forest** (green tones)

### Accent Colors
- Discord Blue
- Red
- Green
- Purple
- Orange
- Pink
- Cyan
- Yellow

---

## Additional Resources

- **discord.py docs:** https://discordpy.readthedocs.io/
- **PyQt6 docs:** https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Discord API:** https://discord.com/developers/docs
