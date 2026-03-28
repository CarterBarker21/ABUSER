"""
Admin commands for ABUSE bot
Server administration and management commands
"""

import os
import importlib
from pathlib import Path

from discord.ext import commands


async def setup(bot):
    """Load all admin commands"""
    cog_dir = Path(__file__).parent
    command_files = [f.stem for f in cog_dir.glob("*.py") if f.name != "__init__.py"]
    
    for cmd_file in command_files:
        try:
            module = importlib.import_module(f"abuse.cogs.admin.{cmd_file}")
            if hasattr(module, 'setup'):
                await module.setup(bot)
        except Exception as e:
            print(f"Failed to load admin command {cmd_file}: {e}")
