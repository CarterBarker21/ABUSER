# ABUSER Bot - AI Agent Guide

## Project Overview

ABUSER is a Discord selfbot framework with a PyQt6 desktop GUI, providing utility, moderation, automation, and server management features.

**Version:** 1.0.0  
**Python:** 3.8+  
**License:** MIT

---

## Technology Stack

- **discord.py-self** - Discord API wrapper (selfbot fork)
- **PyQt6** - Desktop GUI framework
- **aiohttp** - Async HTTP client
- **python-dotenv** - Environment variables
- **colorama** - Terminal colors
- **pycryptodome** - Encryption for token finder

### Project Structure
```
ABUSER/
├── abuse/                      # Main package
│   ├── core/bot.py            # ABUSERBot class
│   ├── cogs/                  # Command modules (utility, mod, nuke, etc.)
│   ├── gui/                   # PyQt6 GUI
│   │   ├── pages/             # GUI pages (login, guilds, nuker, etc.)
│   │   ├── bot_runner.py      # Bot thread management
│   │   ├── main_window.py     # Main GUI window
│   │   └── theme.py           # Theme system
│   └── utils/                 # Utilities (rate_limiter, token_manager, etc.)
├── config/                     # Configuration files
├── data/                       # Runtime data (tokens, logs)
├── tests/                      # Test suite
├── docs/                       # Documentation
│   ├── ABUSER_FRAMEWORK.md    # Technical framework docs
│   ├── BUILD.md               # Build instructions
│   └── TOKEN_LOGIN_VERIFICATION.md
├── main.py                     # GUI entry point
├── run.bat                     # Windows launcher
├── build.bat                   # PyInstaller build script
└── requirements.txt            # Python dependencies
```

---

## Build and Run

### Installation
```bash
pip install -r requirements.txt
```

### Running
```bash
# Windows (no console window)
run.bat

# Or directly with Python
python main.py
```

### Building EXE
```bash
build.bat
```

### Tests
```bash
pytest
```

---

## Code Style

- **PEP 8** with 4-space indentation, 120 char line length
- **Classes:** `PascalCase`
- **Functions:** `snake_case`
- **Constants:** `UPPER_CASE`
- **Private:** leading `_underscore`

### Import Order
1. Standard library
2. Third-party (PyQt6, discord)
3. Local package (from abuse...)

---

## Architecture

### Bot Core (`abuse/core/bot.py`)
- Extends `discord.ext.commands.Bot` with `self_bot=True`
- Auto-loads cogs from `abuse/cogs/`
- Rate limiting integration
- Graceful shutdown handling

### GUI (`abuse/gui/`)
- **Pattern:** MVC-like with signal-based communication
- **BotRunner:** Manages bot thread, bridges GUI and bot
- **Theme system:** 12 presets + 8 accent colors
- **Routes:** login, docs, guilds, nuker, dm, logs, settings

### Rate Limiting (`abuse/utils/rate_limiter.py`)
- **Token bucket algorithm** at multiple levels:
  - Global: 50 req/s max
  - Tiers: Critical (0.1/s), Heavy (0.5/s), Moderate (2/s), Light (5/s), Minimal (10/s)
- **Decorators:** `@rate_limit_critical`, `@rate_limit_heavy`, etc.
- **Auto-retry** with exponential backoff

---

## Configuration

### `config/config.json`
- Command prefix (default: `.`)
- Security settings (safe mode, confirm destructive)
- Performance (rate limits, retries)

### `config/gui_config.json`
- Appearance (theme, accent, font)
- Behavior (startup page, confirmations)
- Privacy (token saving)

### `data/tokens.json`
Saved accounts with validation status.

### Environment Variables
- `DISCORD_TOKEN` - Discord token
- `ABUSER_SELECTED_TOKEN` - Selected account token
- `ABUSER_CONFIG_DIR` - Config directory override
- `ABUSER_DATA_DIR` - Data directory override

---

## Development

### Adding a Command
1. Create file in `abuse/cogs/<category>/`
2. Extend `commands.Cog`
3. Add `setup(bot)` async function
4. Apply rate limit decorator

### Adding a GUI Page
1. Create file in `abuse/gui/pages/`
2. Extend `BasePage`
3. Add route to `routes.py`
4. Register in `main_window.py`

### Thread Safety
- Bot runs in separate thread via `BotWorker`
- Use Qt signals for cross-thread communication
- Never access Discord API from GUI thread

---

## Security

- Tokens stored in `data/tokens.json`
- Token validation before use
- Multiple token sources supported
- Rate limiting prevents API bans
- Safe mode prevents destructive operations

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run from project root |
| Token not found | Check `config/.env` or `data/tokens.json` |
| Rate limited | Check logs for limiter status |
| Qt platform errors | Set `QT_QPA_PLATFORM=offscreen` |

---

## Resources

- [discord.py docs](https://discordpy.readthedocs.io/)
- [PyQt6 docs](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Discord API](https://discord.com/developers/docs)
