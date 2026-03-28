"""
Utility commands for ABUSE bot
Basic utility and information commands
"""

import os
import importlib
from pathlib import Path

from discord.ext import commands


async def setup(bot):
    """
    Load all utility commands
    Automatically imports all .py files in this directory
    """
    cog_dir = Path(__file__).parent
    
    # Get all .py files except __init__.py
    command_files = [f.stem for f in cog_dir.glob("*.py") if f.name != "__init__.py"]
    
    for cmd_file in command_files:
        try:
            # Import the module
            module = importlib.import_module(f"abuse.cogs.utility.{cmd_file}")
            
            # If module has a setup function, call it
            if hasattr(module, 'setup'):
                await module.setup(bot)
            
        except Exception as e:
            print(f"Failed to load utility command {cmd_file}: {e}")


# Import specific commands for direct access
from .ping import PingCommand

__all__ = ["PingCommand"]
