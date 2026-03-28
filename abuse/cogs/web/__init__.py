"""
Web commands for ABUSE bot
External API integrations
"""

import importlib
from pathlib import Path


async def setup(bot):
    """Load all web commands"""
    cog_dir = Path(__file__).parent
    command_files = [f.stem for f in cog_dir.glob("*.py") if f.name != "__init__.py"]
    
    for cmd_file in command_files:
        try:
            module = importlib.import_module(f"abuse.cogs.web.{cmd_file}")
            if hasattr(module, 'setup'):
                await module.setup(bot)
        except Exception as e:
            print(f"Failed to load web command {cmd_file}: {e}")
