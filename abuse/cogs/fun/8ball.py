"""
8-Ball command - Magic 8-ball fortune telling with error handling
"""

import random
import discord
from discord.ext import commands
from abuse.utils.rate_limiter import rate_limit_light


class EightBallCommand(commands.Cog):
    """Magic 8-ball command with cooldown and error handling"""
    
    responses = [
        # Positive (10)
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        # Neutral (5)
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        # Negative (5)
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    
    # Color coding for response types
    positive_responses = responses[:10]
    neutral_responses = responses[10:15]
    negative_responses = responses[15:]
    
    def __init__(self, bot):
        self.bot = bot
    
    def _get_response_color(self, response: str) -> discord.Color:
        """Get color based on response type"""
        if response in self.positive_responses:
            return discord.Color.green()
        elif response in self.negative_responses:
            return discord.Color.red()
        else:
            return discord.Color.yellow()
    
    @commands.command(
        name="8ball",
        aliases=["eightball", "8b"],
        help="Ask the magic 8-ball a question",
        brief="Magic 8-ball"
    )
    @commands.cooldown(5, 10.0, commands.BucketType.user)  # 5 uses per 10 seconds
    @rate_limit_light(custom_cooldown=(3.0, commands.BucketType.user))
    async def eightball(self, ctx, *, question: str = None):
        """
        Ask the magic 8-ball a question
        
        Usage:
            .8ball Will I win the lottery?
            .8ball Should I go outside?
        
        Cooldown: 3 uses per 10 seconds per user
        """
        # Check if question was provided
        if not question:
            await ctx.send(
                "❌ Please ask a question!\n"
                f"Usage: `{self.bot.prefix}8ball <question>`",
                delete_after=5
            )
            return
        
        # Validate question length
        if len(question) > 500:
            await ctx.send("❌ Question too long! (max 500 characters)", delete_after=5)
            return
        
        # Check for empty question (just spaces/punctuation)
        stripped = question.strip(" ?!.\n\t")
        if not stripped:
            await ctx.send("❌ Please ask a real question!", delete_after=5)
            return
        
        try:
            response = random.choice(self.responses)
            
            # Truncate question if too long
            display_question = question if len(question) < 200 else question[:197] + "..."
            
            # Plain text format (selfbots can't use embeds)
            message = (
                f"🎱 **Magic 8-Ball**\n\n"
                f"**Question:** {display_question}\n"
                f"**Answer:** {response}"
            )
            
            await ctx.send(message, delete_after=15)
            
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to send message: {e.text}", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)[:100]}", delete_after=5)
    
    @eightball.error
    async def eightball_error(self, ctx, error):
        """Handle 8ball-specific errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏱ 8-ball is on cooldown! Please wait {error.retry_after:.1f}s.",
                delete_after=3
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("⏱ Rate limited! Please wait a moment.", delete_after=3)
        else:
            # Log unexpected errors
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"8ball error: {error}")


async def setup(bot):
    await bot.add_cog(EightBallCommand(bot))
