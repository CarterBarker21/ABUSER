"""
Automod commands for ABUSE bot
Automation and auto-response commands
"""

import importlib
from pathlib import Path


async def setup(bot):
    """Load all automod commands"""
    cog_dir = Path(__file__).parent
    command_files = [f.stem for f in cog_dir.glob("*.py") if f.name != "__init__.py"]
    
    for cmd_file in command_files:
        try:
            module = importlib.import_module(f"abuse.cogs.automod.{cmd_file}")
            if hasattr(module, 'setup'):
                await module.setup(bot)
        except Exception as e:
            print(f"Failed to load automod command {cmd_file}: {e}")
