"""
Server info command - Display guild information
"""

import discord
from discord.ext import commands
from datetime import datetime
from abuse.utils.rate_limiter import rate_limit_moderate


class ServerInfoCommand(commands.Cog):
    """Server information command"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        name="serverinfo",
        aliases=["guildinfo", "si", "server"],
        help="Display detailed server information",
        brief="Server info"
    )
    @commands.cooldown(3, 5.0, commands.BucketType.user)  # 3 uses per 5 seconds
    @rate_limit_moderate(custom_cooldown=(2.0, commands.BucketType.user))
    async def serverinfo(self, ctx):
        """Show server/guild information"""
        guild = ctx.guild
        
        if not guild:
            await ctx.send("❌ This command can only be used in a server!", delete_after=5)
            return
        
        try:
            # Build server info text
            lines = [
                f"**{guild.name}**",
                f"Server ID: `{guild.id}`",
                ""
            ]
            
            # Owner info
            owner = guild.owner
            if owner:
                owner_value = owner.mention
            else:
                owner_value = f"ID: {guild.owner_id}" if guild.owner_id else "Unknown"
            lines.append(f"**Owner:** {owner_value}")
            
            # Creation date
            try:
                created_at = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
                days_ago = (datetime.now(datetime.timezone.utc) - guild.created_at).days
                lines.append(f"**Created:** {created_at} ({days_ago} days ago)")
            except Exception:
                lines.append("**Created:** Unknown")
            
            # Members
            total_members = guild.member_count or len(guild.members)
            if total_members <= 1000:
                humans = sum(1 for m in guild.members if not m.bot)
                bots = total_members - humans
                lines.append(f"**Members:** {total_members} total ({humans} humans, {bots} bots)")
            else:
                lines.append(f"**Members:** {total_members}")
            
            # Channels
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            lines.append(f"**Channels:** {text_channels} text, {voice_channels} voice, {categories} categories")
            
            # Roles
            roles_count = len(guild.roles) - 1  # Exclude @everyone
            lines.append(f"**Roles:** {roles_count}")
            
            # Boost status
            try:
                boost_level = guild.premium_tier
                boost_count = guild.premium_subscription_count or 0
                lines.append(f"**Boosts:** Level {boost_level} ({boost_count} boosts)")
            except Exception:
                pass
            
            # Verification level
            lines.append(f"**Verification:** {guild.verification_level.name.replace('_', ' ').title()}")
            
            # Features (limit to first 5)
            if guild.features:
                features = ", ".join([f.replace("_", " ").title() for f in guild.features[:5]])
                if len(guild.features) > 5:
                    features += "..."
                lines.append(f"**Features:** {features}")
            
            await ctx.send("\n".join(lines), delete_after=30)
            
        except discord.Forbidden:
            await ctx.send("🔒 I don't have permission to send messages here.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Discord API error: {e.status}", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)[:100]}", delete_after=5)
    
    @serverinfo.error
    async def serverinfo_error(self, ctx, error):
        """Handle serverinfo-specific errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏱ Server info is on cooldown! Please wait {error.retry_after:.1f}s.",
                delete_after=3
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("⏱ Rate limited! Please wait a moment.", delete_after=3)


async def setup(bot):
    await bot.add_cog(ServerInfoCommand(bot))
