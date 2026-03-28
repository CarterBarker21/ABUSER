"""
Purge command - Bulk delete messages with safety checks
"""

import asyncio
import discord
from discord.ext import commands
from abuse.utils.rate_limiter import rate_limit_heavy, safe_api_call, RateLimitTier, get_rate_limiter


class PurgeCommand(commands.Cog):
    """Message purging command with safety checks and error handling"""
    
    def __init__(self, bot):
        self.bot = bot
        self._max_purge_amount = 100
        self._default_purge_amount = 10
    
    @commands.command(
        name="purge",
        aliases=["clear", "clean"],
        help="Delete multiple messages from the channel (requires Manage Messages permission)",
        brief="Delete messages"
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.cooldown(1, 10.0, commands.BucketType.channel)  # 1 use per 10 seconds per channel
    @rate_limit_heavy(custom_cooldown=(10.0, commands.BucketType.channel))
    async def purge(self, ctx, amount: int = None):
        """
        Delete messages from the channel
        
        Args:
            amount: Number of messages to delete (default: 10, max: 100)
        
        Usage:
            .purge 50 - Delete 50 messages
            .purge - Delete default amount (10)
        
        Required Permissions:
            - Manage Messages (user)
            - Manage Messages, Read Message History (bot)
        
        Cooldown: 5 seconds per channel
        """
        # Default amount if not specified
        if amount is None:
            amount = self._default_purge_amount
        
        # Validate amount
        if amount < 1:
            await ctx.send("❌ Amount must be at least 1!", delete_after=5)
            return
        
        if amount > self._max_purge_amount:
            await ctx.send(f"❌ Cannot delete more than {self._max_purge_amount} messages at once!", delete_after=5)
            return
        
        # Check if in DM
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server!", delete_after=5)
            return
        
        try:
            # Delete the command message too
            amount_to_delete = amount + 1
            
            # Calculate messages we can actually delete (respecting 14-day limit)
            # Discord doesn't allow bulk deleting messages older than 14 days
            # Use safe_api_call for rate limit protection
            limiter = get_rate_limiter()
            await limiter.acquire(
                tier=RateLimitTier.HEAVY,
                guild_id=ctx.guild.id if ctx.guild else None,
                user_id=ctx.author.id
            )
            
            deleted = await ctx.channel.purge(
                limit=amount_to_delete,
                check=lambda m: (discord.utils.utcnow() - m.created_at).days < 14
            )
            
            # Check if some messages couldn't be deleted (too old)
            actually_deleted = len(deleted) - 1  # Subtract 1 for command message
            
            # Plain text response
            message = f"✅ Deleted {max(0, actually_deleted)} messages"
            if actually_deleted < amount:
                message += "\n*Note: Some messages could not be deleted (older than 14 days)*"
            
            await ctx.send(message, delete_after=5)
            
        except discord.Forbidden:
            await ctx.send("🔒 I don't have permission to delete messages!", delete_after=5)
        except discord.HTTPException as e:
            if e.status == 429:
                await ctx.send("⏱ Rate limited by Discord! Please wait before purging again.", delete_after=5)
            else:
                await ctx.send(f"❌ Discord API error: {e.status}", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)[:100]}", delete_after=5)
    
    @purge.error
    async def purge_error(self, ctx, error):
        """Handle purge-specific errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🔒 You need `Manage Messages` permission to use this command!", delete_after=5)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("🤖 I need `Manage Messages` and `Read Message History` permissions!", delete_after=5)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱ Purge is on cooldown! Please wait {error.retry_after:.1f}s before purging again.", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Please provide a valid number!", delete_after=5)
        elif isinstance(error, commands.CheckFailure):
            # Rate limit check failed
            await ctx.send("⏱ Rate limited! Please slow down with purge commands.", delete_after=5)


async def setup(bot):
    await bot.add_cog(PurgeCommand(bot))
