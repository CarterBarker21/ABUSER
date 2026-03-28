"""
Error handling utilities for ABUSER bot
Provides decorators and helper functions for consistent error handling
"""

import asyncio
import functools
import logging
from typing import Callable, Optional, TypeVar, Union
from discord.ext import commands
import discord

logger = logging.getLogger("ABUSER")

T = TypeVar('T')


def handle_errors(
    log_errors: bool = True,
    reraise: bool = False,
    default_return: Optional[T] = None
) -> Callable:
    """
    Decorator for handling errors in functions
    
    Args:
        log_errors: Whether to log errors
        reraise: Whether to re-raise the exception after handling
        default_return: Value to return if an error occurs
    
    Example:
        @handle_errors(log_errors=True, default_return=None)
        async def fetch_data(url):
            return await session.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                if reraise:
                    raise
                return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                if reraise:
                    raise
                return default_return
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> Callable:
    """
    Decorator for retrying functions on failure
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
    
    Example:
        @with_retry(max_retries=3, delay=1.0, exceptions=(ConnectionError,))
        async def connect_to_api():
            return await api.connect()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_retries}): {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception:
                            pass
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        return async_wrapper
    return decorator


class CommandCooldownManager:
    """
    Manages custom cooldowns for commands beyond discord.py's built-in system
    """
    
    def __init__(self):
        self._cooldowns: dict = {}
    
    def is_on_cooldown(self, user_id: int, command_name: str, cooldown_seconds: float) -> bool:
        """Check if a user is on cooldown for a command"""
        key = (user_id, command_name)
        last_used = self._cooldowns.get(key)
        
        if last_used is None:
            return False
        
        elapsed = asyncio.get_event_loop().time() - last_used
        return elapsed < cooldown_seconds
    
    def get_remaining(self, user_id: int, command_name: str, cooldown_seconds: float) -> float:
        """Get remaining cooldown time in seconds"""
        key = (user_id, command_name)
        last_used = self._cooldowns.get(key)
        
        if last_used is None:
            return 0
        
        elapsed = asyncio.get_event_loop().time() - last_used
        return max(0, cooldown_seconds - elapsed)
    
    def update(self, user_id: int, command_name: str):
        """Update the last used time for a command"""
        key = (user_id, command_name)
        self._cooldowns[key] = asyncio.get_event_loop().time()
    
    def reset(self, user_id: Optional[int] = None, command_name: Optional[str] = None):
        """Reset cooldowns. If no arguments, resets all."""
        if user_id is None and command_name is None:
            self._cooldowns.clear()
        elif command_name is None:
            # Reset all commands for user
            keys_to_remove = [k for k in self._cooldowns if k[0] == user_id]
            for key in keys_to_remove:
                del self._cooldowns[key]
        elif user_id is None:
            # Reset command for all users
            keys_to_remove = [k for k in self._cooldowns if k[1] == command_name]
            for key in keys_to_remove:
                del self._cooldowns[key]
        else:
            # Reset specific user/command
            self._cooldowns.pop((user_id, command_name), None)


def format_discord_error(error: Exception) -> str:
    """
    Format a Discord API error into a user-friendly message
    
    Args:
        error: The exception to format
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, discord.Forbidden):
        return "🔒 I don't have permission to do that."
    
    if isinstance(error, discord.NotFound):
        return "❌ The requested resource was not found."
    
    if isinstance(error, discord.HTTPException):
        status_codes = {
            429: "⏱ Rate limited! Please slow down.",
            500: "⚠️ Discord is having issues. Try again later.",
            502: "⚠️ Discord gateway error. Try again later.",
            503: "⚠️ Discord service unavailable. Try again later.",
        }
        return status_codes.get(
            error.status, 
            f"❌ Discord API error (HTTP {error.status})"
        )
    
    if isinstance(error, discord.ConnectionClosed):
        return "🔌 Connection to Discord was lost."
    
    if isinstance(error, asyncio.TimeoutError):
        return "⏱ The operation timed out. Please try again."
    
    return f"❌ An error occurred: {str(error)[:100]}"


class ErrorRateLimiter:
    """
    Prevents error spam by limiting how often errors are reported
    """
    
    def __init__(self, cooldown_seconds: float = 5.0):
        self.cooldown_seconds = cooldown_seconds
        self._last_errors: dict = {}
    
    def should_report(self, error_key: str) -> bool:
        """Check if this error should be reported (not rate limited)"""
        now = asyncio.get_event_loop().time()
        last_time = self._last_errors.get(error_key, 0)
        
        if now - last_time >= self.cooldown_seconds:
            self._last_errors[error_key] = now
            return True
        return False
    
    def reset(self, error_key: Optional[str] = None):
        """Reset error rate limiting"""
        if error_key is None:
            self._last_errors.clear()
        else:
            self._last_errors.pop(error_key, None)


def safe_delete_message(message, delay: float = 0.0) -> asyncio.Task:
    """
    Safely delete a message, ignoring common errors
    
    Args:
        message: The message to delete
        delay: Delay in seconds before deletion
        
    Returns:
        Task that deletes the message
    """
    async def _delete():
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass
    
    return asyncio.create_task(_delete())


async def safe_send(
    destination,
    content: Optional[str] = None,
    *,
    embed: Optional[discord.Embed] = None,
    delete_after: Optional[float] = None,
    fallback_to_content: bool = True
) -> Optional[discord.Message]:
    """
    Safely send a message with fallback and error handling
    
    Args:
        destination: Where to send (ctx, channel, etc.)
        content: Message content
        embed: Message embed
        delete_after: Seconds after which to delete
        fallback_to_content: If embed fails, try sending as content
        
    Returns:
        The sent message or None
    """
    try:
        return await destination.send(content=content, embed=embed, delete_after=delete_after)
    except discord.Forbidden:
        logger.warning(f"Cannot send message: Forbidden")
        return None
    except discord.HTTPException as e:
        # Try fallback if embed failed
        if embed and fallback_to_content and content:
            try:
                return await destination.send(content=content, delete_after=delete_after)
            except Exception:
                pass
        logger.warning(f"Cannot send message: HTTP {e.status}")
        return None
    except Exception as e:
        logger.error(f"Cannot send message: {e}")
        return None


# Global cooldown manager instance
cooldown_manager = CommandCooldownManager()
