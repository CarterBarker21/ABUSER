"""
Crypto command - Check cryptocurrency prices with error handling and caching
"""

import asyncio
import aiohttp
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from abuse.utils.rate_limiter import rate_limit_moderate


class CryptoCommand(commands.Cog):
    """Cryptocurrency price checker with caching and error handling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.coingecko.com/api/v3/simple/price"
        
        # Cache for price data
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(seconds=30)  # Cache for 30 seconds
        self._rate_limit_remaining = 10
        self._rate_limit_reset = datetime.now()
    
    @commands.command(
        name="btc",
        aliases=["bitcoin"],
        help="Check Bitcoin price",
        brief="Bitcoin price"
    )
    @commands.cooldown(3, 15.0, commands.BucketType.user)  # 3 uses per 15 seconds
    @rate_limit_moderate(custom_cooldown=(3.0, commands.BucketType.user))
    async def btc(self, ctx):
        """Get current Bitcoin price"""
        await self.get_crypto_price(ctx, "bitcoin", "BTC", "🟠")
    
    @commands.command(
        name="eth",
        aliases=["ethereum"],
        help="Check Ethereum price",
        brief="Ethereum price"
    )
    @commands.cooldown(3, 15.0, commands.BucketType.user)  # 3 uses per 15 seconds
    @rate_limit_moderate(custom_cooldown=(3.0, commands.BucketType.user))
    async def eth(self, ctx):
        """Get current Ethereum price"""
        await self.get_crypto_price(ctx, "ethereum", "ETH", "🟣")
    
    def _get_cached_price(self, coin_id: str) -> Optional[Dict]:
        """Get cached price data if still valid"""
        if coin_id in self._cache:
            data = self._cache[coin_id]
            if datetime.now() - data["timestamp"] < self._cache_ttl:
                return data["price"]
        return None
    
    def _cache_price(self, coin_id: str, price_data: Dict):
        """Cache price data"""
        self._cache[coin_id] = {
            "price": price_data,
            "timestamp": datetime.now()
        }
    
    def _check_rate_limit(self) -> bool:
        """Check if we can make a request (rate limit tracking)"""
        now = datetime.now()
        
        # Reset rate limit counter if enough time passed
        if now > self._rate_limit_reset:
            self._rate_limit_remaining = 10
            self._rate_limit_reset = now + timedelta(minutes=1)
        
        return self._rate_limit_remaining > 0
    
    async def get_crypto_price(self, ctx, coin_id: str, symbol: str, emoji: str):
        """Fetch crypto price from API with caching and error handling"""
        
        # Check cache first
        cached = self._get_cached_price(coin_id)
        if cached:
            await self._send_price_embed(ctx, coin_id, symbol, emoji, cached, cached=True)
            return
        
        # Check rate limit
        if not self._check_rate_limit():
            await ctx.send("⏱ Rate limited by API. Please wait a moment.", delete_after=5)
            return
        
        # Check if we have HTTP session
        if not self.bot.session or self.bot.session.closed:
            await ctx.send("❌ HTTP session not available.", delete_after=5)
            return
        
        try:
            params = {
                "ids": coin_id,
                "vs_currencies": "usd,eur",
                "include_24hr_change": "true"
            }
            
            async with self.bot.session.get(
                self.api_url, 
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                self._rate_limit_remaining -= 1
                
                if resp.status == 200:
                    data = await resp.json()
                    coin_data = data.get(coin_id, {})
                    
                    if not coin_data:
                        await ctx.send(f"❌ No data found for {symbol}.", delete_after=5)
                        return
                    
                    # Cache the result
                    self._cache_price(coin_id, coin_data)
                    
                    await self._send_price_embed(ctx, coin_id, symbol, emoji, coin_data)
                    
                elif resp.status == 429:
                    await ctx.send("⏱ API rate limit hit. Please wait a moment.", delete_after=5)
                else:
                    await ctx.send(f"❌ API error (HTTP {resp.status})", delete_after=5)
                    
        except aiohttp.ClientError as e:
            await ctx.send(f"❌ Connection error: {str(e)[:50]}", delete_after=5)
        except asyncio.TimeoutError:
            await ctx.send("⏱ Request timed out. Please try again.", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)[:100]}", delete_after=5)
    
    async def _send_price_embed(
        self, 
        ctx, 
        coin_id: str, 
        symbol: str, 
        emoji: str, 
        coin_data: Dict,
        cached: bool = False
    ):
        """Send price embed with given data"""
        try:
            usd_price = coin_data.get("usd", 0)
            eur_price = coin_data.get("eur", 0)
            change = coin_data.get("usd_24h_change", 0)
            
            # Determine color and emoji based on change
            if change > 0:
                color = discord.Color.green()
                change_emoji = "📈"
            elif change < 0:
                color = discord.Color.red()
                change_emoji = "📉"
            else:
                color = discord.Color.blue()
                change_emoji = "➖"
            
            # Plain text format
            cache_note = " (cached)" if cached else ""
            message = (
                f"{emoji} **{symbol} Price**{cache_note}\n\n"
                f"```\n"
                f"USD:        ${usd_price:,.2f}\n"
                f"EUR:        €{eur_price:,.2f}\n"
                f"24h Change: {change_emoji} {change:+.2f}%\n"
                f"```\n"
                f"*Prices from CoinGecko*"
            )
            
            await ctx.send(message, delete_after=20)
            
        except Exception as e:
            await ctx.send(f"❌ Error displaying price: {str(e)[:50]}", delete_after=5)
    
    @btc.error
    @eth.error
    async def crypto_error(self, ctx, error):
        """Handle crypto command errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏱ Crypto commands are on cooldown! Please wait {error.retry_after:.1f}s.",
                delete_after=3
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("⏱ Rate limited! Please wait a moment.", delete_after=3)


async def setup(bot):
    await bot.add_cog(CryptoCommand(bot))
