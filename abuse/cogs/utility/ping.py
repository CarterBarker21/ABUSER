"""
Ping command - Check bot latency
"""

import time
import discord
from discord.ext import commands
from datetime import datetime

from abuse.utils.colors import info
from abuse.utils.rate_limiter import rate_limit_minimal


class PingCommand(commands.Cog):
    """
    Ping command - Check bot latency and response time
    
    Usage:
        .ping - Shows bot latency in milliseconds
    
    Aliases:
        pong, latency
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        name="ping",
        aliases=["pong", "latency"],
        help="Check bot latency and response time",
        brief="Check latency"
    )
    @commands.cooldown(3, 5.0, commands.BucketType.user)  # 3 uses per 5 seconds
    @rate_limit_minimal(custom_cooldown=(3.0, commands.BucketType.user))
    async def ping(self, ctx):
        """Check the bot's latency"""
        try:
            # Calculate WebSocket latency
            ws_latency = round(self.bot.latency * 1000)
            
            # Send initial message to measure round-trip
            start_time = time.perf_counter()
            message = await ctx.send("🏓 **Pong!** Calculating...", delete_after=10)
            end_time = time.perf_counter()
            
            # Calculate round-trip time
            rtt = round((end_time - start_time) * 1000)
            
            # Fallback to message timestamps if needed
            if rtt < 1:
                rtt = round((message.created_at - ctx.message.created_at).total_seconds() * 1000)
            
            # Calculate uptime
            uptime = datetime.now() - self.bot.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"
            
            # Status based on latency
            if ws_latency < 50:
                status = "🟢 Excellent"
            elif ws_latency < 100:
                status = "🟡 Very Good"
            elif ws_latency < 200:
                status = "🟡 Good"
            elif ws_latency < 500:
                status = "🟠 Fair"
            else:
                status = "🔴 Poor"
            
            # Format response
            response = (
                f"🏓 **Pong!**\n\n"
                f"```\n"
                f"WebSocket Latency: {ws_latency}ms\n"
                f"Round-Trip Time:   {rtt}ms\n"
                f"Uptime:            {uptime_str}\n"
                f"Status:            {status}\n"
                f"```"
            )
            
            await message.edit(content=response)
            
            # Console output
            print(f"{info('[ABUSER]')} Ping by {ctx.author} - Latency: {ws_latency}ms (RTT: {rtt}ms)")
            
        except discord.Forbidden:
            await ctx.send("🔒 I don't have permission to send messages here.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Discord API error: {e.status}", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)[:100]}", delete_after=5)
    
    @ping.error
    async def ping_error(self, ctx, error):
        """Handle ping-specific errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏱ Ping is on cooldown! Please wait {error.retry_after:.1f}s.",
                delete_after=3
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("⏱ Rate limited! Please wait a moment.", delete_after=3)


async def setup(bot):
    """Add the cog to the bot"""
    await bot.add_cog(PingCommand(bot))
