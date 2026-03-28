"""
AFK command - Set away status with error handling and performance optimization
"""

import asyncio
import discord
from discord.ext import commands
from collections import defaultdict
from typing import Dict, Any
from abuse.utils.rate_limiter import rate_limit_moderate, RateLimitTier, get_rate_limiter


class AFKCommand(commands.Cog):
    """AFK (Away From Keyboard) command with error handling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.afk_users: Dict[int, Dict[str, Any]] = {}
        self._recent_afk_messages: Dict[int, float] = defaultdict(float)
        self._afk_cooldown = 5.0  # Seconds between AFK mention responses
    
    @commands.command(
        name="afk",
        help="Set your AFK status",
        brief="Set AFK status"
    )
    @commands.cooldown(3, 10.0, commands.BucketType.user)  # 3 uses per 10 seconds
    @rate_limit_moderate(custom_cooldown=(3.0, commands.BucketType.user))
    async def afk(self, ctx, *, reason: str = "No reason provided"):
        """
        Set AFK status
        
        When someone mentions you, they'll see your AFK message
        
        Usage:
            .afk Going to eat
            .afk - Remove AFK status
        
        Cooldown: 3 uses per 10 seconds per user
        """
        try:
            # Check for "off" keywords to remove AFK
            off_keywords = ["off", "none", "-", "back", "done", "no", "false", "disable"]
            if reason.lower() in off_keywords or reason.lower().startswith("back "):
                if ctx.author.id in self.afk_users:
                    del self.afk_users[ctx.author.id]
                    await ctx.send(f"✅ Welcome back {ctx.author.mention}!")
                else:
                    await ctx.send("❌ You weren't AFK!")
                return
            
            # Validate reason length
            if len(reason) > 200:
                await ctx.send("❌ AFK reason too long! (max 200 characters)", delete_after=5)
                return
            
            # Set AFK status
            self.afk_users[ctx.author.id] = {
                "reason": reason,
                "time": discord.utils.utcnow(),
                "guild_id": ctx.guild.id if ctx.guild else None
            }
            
            message = f"💤 {ctx.author.mention} is now AFK: **{reason}**\n\n*Mention them to see this message*"
            await ctx.send(message, delete_after=10)
            
        except discord.Forbidden:
            await ctx.send("🔒 I don't have permission to send messages here.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Discord API error: {e.status}", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)[:100]}", delete_after=5)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for AFK mentions with rate limiting"""
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        # Check if author was AFK (they sent a message, so they're back)
        if message.author.id in self.afk_users:
            # Don't remove if they just mentioned themselves
            if self.user_mentioned(message, message.author.id):
                return
            
            afk_data = self.afk_users.pop(message.author.id)
            time_ago = discord.utils.utcnow() - afk_data["time"]
            minutes = int(time_ago.total_seconds() / 60)
            
            try:
                await message.channel.send(
                    f"✅ Welcome back {message.author.mention}! I removed your AFK status (was AFK for {minutes}m).",
                    delete_after=5
                )
            except (discord.Forbidden, discord.HTTPException):
                pass  # Ignore errors for automatic messages
        
        # Check for AFK mentions with rate limiting
        for user in message.mentions:
            if user.id == message.author.id:
                continue  # Skip self-mentions
            
            if user.id in self.afk_users:
                # Check rate limit for this AFK user
                now = asyncio.get_event_loop().time()
                if now - self._recent_afk_messages[user.id] < self._afk_cooldown:
                    continue  # Skip if on cooldown
                
                self._recent_afk_messages[user.id] = now
                
                afk_data = self.afk_users[user.id]
                time_ago = discord.utils.utcnow() - afk_data["time"]
                minutes = int(time_ago.total_seconds() / 60)
                
                # Format time string
                if minutes < 1:
                    time_str = "just now"
                elif minutes < 60:
                    time_str = f"{minutes}m ago"
                else:
                    hours = minutes // 60
                    time_str = f"{hours}h ago"
                
                try:
                    reply_msg = f"💤 {user.mention} is AFK: **{afk_data['reason']}** ({time_str})"
                    await message.reply(reply_msg, delete_after=10)
                except (discord.Forbidden, discord.HTTPException):
                    pass  # Ignore errors for automatic messages
    
    def user_mentioned(self, message, user_id: int) -> bool:
        """Check if a specific user is mentioned in the message"""
        return any(u.id == user_id for u in message.mentions)
    
    @afk.error
    async def afk_error(self, ctx, error):
        """Handle AFK-specific errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏱ AFK is on cooldown! Please wait {error.retry_after:.1f}s.",
                delete_after=3
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("⏱ Rate limited! Please wait a moment.", delete_after=3)


async def setup(bot):
    await bot.add_cog(AFKCommand(bot))
