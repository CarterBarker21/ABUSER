"""
Help command - Custom help system
"""

import discord
from discord.ext import commands
from abuse.utils.rate_limiter import rate_limit_light


class HelpCommand(commands.Cog):
    """Custom help command"""
    
    def __init__(self, bot):
        self.bot = bot
        self._max_commands_display = 25
    
    @commands.command(
        name="help",
        aliases=["h", "commands"],
        help="Show this help message",
        brief="Show help"
    )
    @commands.cooldown(5, 10.0, commands.BucketType.user)  # 5 uses per 10 seconds
    @rate_limit_light(custom_cooldown=(3.0, commands.BucketType.user))
    async def help_cmd(self, ctx, category: str = None):
        """Show help information for commands"""
        try:
            prefix = self.bot.prefix
            
            if category is None:
                await self._show_main_help(ctx, prefix)
            else:
                await self._show_category_help(ctx, category.lower(), prefix)
                
        except discord.Forbidden:
            await ctx.send("🔒 I don't have permission to send messages.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Discord API error: {e.status}", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)[:100]}", delete_after=5)
    
    async def _show_main_help(self, ctx, prefix: str):
        """Show main help with categories"""
        
        categories = {
            "utility": "ℹ️ Utility commands",
            "admin": "⚙️ Admin commands",
            "fun": "🎮 Fun commands",
            "moderation": "🛡️ Moderation commands",
            "automod": "🤖 Automation commands",
            "nuke": "⚠️ Nuke commands (DANGEROUS)",
            "sniper": "🎯 Sniper commands",
            "voice": "🎤 Voice commands",
            "web": "🌐 Web commands"
        }
        
        # Build help text
        lines = [
            "📚 **ABUSER Bot Help**",
            "",
            f"Use `{prefix}help <category>` for specific commands",
            "",
            "**Categories:**",
        ]
        
        for cat, desc in categories.items():
            lines.append(f"`{prefix}help {cat}` - {desc}")
        
        # Add command count
        command_count = len(self.bot.commands)
        lines.append("")
        lines.append(f"*Prefix: {prefix} | Total Commands: {command_count}*")
        
        await ctx.send("\n".join(lines), delete_after=30)
    
    async def _show_category_help(self, ctx, category: str, prefix: str):
        """Show commands in specific category"""
        commands_list = []
        
        for cmd in self.bot.commands:
            if cmd.cog:
                # Extract category from cog name
                cog_name = cmd.cog.__class__.__name__.lower()
                # Remove common suffixes
                for suffix in ["command", "cog", "commands"]:
                    cog_name = cog_name.replace(suffix, "")
                
                if cog_name == category or category in cog_name:
                    commands_list.append(cmd)
        
        if not commands_list:
            await ctx.send(f"❌ No commands found in category: `{category}`", delete_after=5)
            return
        
        # Sort commands alphabetically
        commands_list.sort(key=lambda c: c.name)
        
        # Build command list text
        lines = [
            f"📚 **{category.title()} Commands**",
            "",
        ]
        
        # Add commands (respect limit)
        for cmd in commands_list[:self._max_commands_display]:
            name = f"`{prefix}{cmd.name}`"
            if cmd.aliases:
                name += f" *({', '.join(cmd.aliases[:3])})*"
            
            desc = cmd.help or cmd.brief or "No description"
            if len(desc) > 100:
                desc = desc[:97] + "..."
            
            lines.append(f"{name} - {desc}")
        
        # Add note if some commands were truncated
        if len(commands_list) > self._max_commands_display:
            lines.append("")
            lines.append(f"*Showing {self._max_commands_display} of {len(commands_list)} commands*")
        
        await ctx.send("\n".join(lines), delete_after=30)
    
    @help_cmd.error
    async def help_error(self, ctx, error):
        """Handle help-specific errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏱ Help is on cooldown! Please wait {error.retry_after:.1f}s.",
                delete_after=3
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("⏱ Rate limited! Please wait a moment.", delete_after=3)


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
