"""
Nitro sniper - Automatically claim Discord Nitro gifts with error handling
"""

import re
import asyncio
import aiohttp
import discord
from discord.ext import commands
from typing import Set
from datetime import datetime
from abuse.utils.rate_limiter import rate_limit_moderate, RateLimitTier, get_rate_limiter


class NitroSniper(commands.Cog):
    """
    Nitro sniper - Auto-detect and claim Nitro codes with safety checks
    
    Monitors messages for discord.gift links and attempts to claim them
    """
    
    # Nitro code pattern (16-24 alphanumeric characters)
    NITRO_PATTERN = re.compile(
        r'(discord\.gift/|discord\.com/gifts/|discordapp\.com/gifts/)([a-zA-Z0-9]{16,24})',
        re.IGNORECASE
    )
    
    # API endpoint for claiming gifts
    GIFT_API_URL = "https://discord.com/api/v9/entitlements/gift-codes/{code}/redeem"
    
    def __init__(self, bot):
        self.bot = bot
        self.enabled = False
        self.claimed = 0
        self.failed = 0
        self._claimed_codes: Set[str] = set()  # Track already attempted codes
        self._rate_limit_delay = 1.0  # Seconds between claim attempts
        self._last_claim_time = 0
        self._lock = asyncio.Lock()
    
    @commands.group(name="snipe", invoke_without_command=True)
    @commands.cooldown(2, 5.0, commands.BucketType.user)  # 2 uses per 5 seconds
    @rate_limit_moderate(custom_cooldown=(2.0, commands.BucketType.user))
    async def snipe(self, ctx):
        """Sniper command group - show status"""
        try:
            status = "✅ Enabled" if self.enabled else "❌ Disabled"
            message = (
                f"🎯 **Sniper Status**\n\n"
                f"Nitro Sniper: {status}\n"
                f"Claimed: {self.claimed}\n"
                f"Failed: {self.failed}\n"
                f"Unique Codes: {len(self._claimed_codes)}\n\n"
                f"*Use {self.bot.prefix}snipe nitro to toggle*"
            )
            await ctx.send(message, delete_after=10)
        except Exception as e:
            await ctx.send(f"🎯 Nitro Sniper: {'ON' if self.enabled else 'OFF'} | ✓:{self.claimed} ✗:{self.failed}", delete_after=10)
    
    @snipe.command(name="nitro")
    @commands.cooldown(2, 5.0, commands.BucketType.user)  # 2 uses per 5 seconds
    @rate_limit_moderate(custom_cooldown=(2.0, commands.BucketType.user))
    async def toggle_nitro(self, ctx):
        """Toggle Nitro sniper"""
        self.enabled = not self.enabled
        status = "enabled" if self.enabled else "disabled"
        color = discord.Color.green() if self.enabled else discord.Color.red()
        
        message = f"🎯 Nitro sniper **{status}**"
        if self.enabled:
            message += "\n\n⚠️ **Warning:** Using a Nitro sniper may violate Discord's Terms of Service. Use at your own risk."
        
        await ctx.send(message, delete_after=10)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for Nitro codes with rate limiting and error handling"""
        if not self.enabled:
            return
        
        if message.author.bot:
            return
        
        # Skip messages from self
        if message.author.id == self.bot.user.id:
            return
        
        # Find Nitro codes in message
        content = message.content
        matches = self.NITRO_PATTERN.findall(content)
        
        if not matches:
            return
        
        async with self._lock:
            for match in matches:
                code = match[1]
                
                # Skip if already attempted
                if code in self._claimed_codes:
                    continue
                
                self._claimed_codes.add(code)
                
                # Rate limiting between attempts
                now = asyncio.get_event_loop().time()
                time_since_last = now - self._last_claim_time
                if time_since_last < self._rate_limit_delay:
                    await asyncio.sleep(self._rate_limit_delay - time_since_last)
                
                await self._attempt_claim(message, code)
                self._last_claim_time = asyncio.get_event_loop().time()
    
    async def _attempt_claim(self, message, code: str):
        """Attempt to claim a Nitro code with error handling"""
        try:
            # Log detection
            self.bot.logger.info(f"[NITRO SNIPER] Found code: {code[:4]}...{code[-4:]} from {message.author}")
            
            # Check if we have aiohttp session
            if not self.bot.session or self.bot.session.closed:
                self.bot.logger.warning("[NITRO SNIPER] No HTTP session available")
                return
            
            # Attempt to claim via API
            # Note: Actual implementation would require proper API request
            # This is a placeholder for the actual claiming logic
            
            # Example API call (commented out for safety):
            # url = self.GIFT_API_URL.format(code=code)
            # async with self.bot.session.post(url) as resp:
            #     if resp.status == 200:
            #         self.claimed += 1
            #         self.bot.logger.info(f"[NITRO SNIPER] Successfully claimed: {code[:4]}...")
            #     else:
            #         self.failed += 1
            #         data = await resp.json()
            #         self.bot.logger.warning(f"[NITRO SNIPER] Failed to claim: {data.get('message', 'Unknown error')}")
            
            # Placeholder logging
            self.bot.logger.info(f"[NITRO SNIPER] Would attempt to claim code (implementation placeholder)")
            
        except aiohttp.ClientError as e:
            self.failed += 1
            self.bot.logger.error(f"[NITRO SNIPER] HTTP error: {e}")
        except asyncio.TimeoutError:
            self.failed += 1
            self.bot.logger.error("[NITRO SNIPER] Request timeout")
        except Exception as e:
            self.failed += 1
            self.bot.logger.error(f"[NITRO SNIPER] Unexpected error: {e}")
    
    @snipe.error
    @toggle_nitro.error
    async def snipe_error(self, ctx, error):
        """Handle sniper command errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱ Sniper commands are on cooldown! Please wait {error.retry_after:.1f}s.", delete_after=3)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("⏱ Rate limited! Please wait a moment.", delete_after=3)


async def setup(bot):
    await bot.add_cog(NitroSniper(bot))
