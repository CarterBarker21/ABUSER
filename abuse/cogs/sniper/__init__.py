"""
Sniper commands for ABUSE bot
Nitro and giveaway sniping automation
"""

import importlib
from pathlib import Path


async def setup(bot):
    """Load all sniper commands"""
    cog_dir = Path(__file__).parent
    command_files = [f.stem for f in cog_dir.glob("*.py") if f.name != "__init__.py"]
    
    for cmd_file in command_files:
        try:
            module = importlib.import_module(f"abuse.cogs.sniper.{cmd_file}")
            if hasattr(module, 'setup'):
                await module.setup(bot)
        except Exception as e:
            print(f"Failed to load sniper command {cmd_file}: {e}")
