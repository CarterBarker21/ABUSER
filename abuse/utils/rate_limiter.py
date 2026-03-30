"""
Comprehensive Rate Limiting System for ABUSER Bot
Prevents Discord API rate limits with multi-layer protection
"""

import asyncio
import time
import random
import logging
from typing import Dict, Optional, List, Tuple, Callable, Any, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import discord
from discord.ext import commands

logger = logging.getLogger("ABUSER")


class RateLimitTier(Enum):
    """Rate limit tiers for different command types"""
    CRITICAL = "critical"      # Server-destroying commands (nuke)
    HEAVY = "heavy"            # Bulk operations (purge)
    MODERATE = "moderate"      # Normal commands (serverinfo, ping)
    LIGHT = "light"            # Simple commands (help, 8ball)
    MINIMAL = "minimal"        # Read-only commands


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    # Global limits
    global_requests_per_second: float = 50.0
    global_burst_size: int = 10
    
    # Tier-specific limits (requests per second, burst size)
    tier_limits: Dict[RateLimitTier, Tuple[float, int]] = field(default_factory=lambda: {
        RateLimitTier.CRITICAL: (0.1, 1),      # 1 per 10 seconds
        RateLimitTier.HEAVY: (0.5, 3),         # 1 per 2 seconds
        RateLimitTier.MODERATE: (2.0, 5),      # 2 per second
        RateLimitTier.LIGHT: (5.0, 10),        # 5 per second
        RateLimitTier.MINIMAL: (10.0, 20),     # 10 per second
    })
    
    # Per-guild limits
    guild_requests_per_second: float = 10.0
    guild_burst_size: int = 5
    
    # Per-user limits
    user_requests_per_second: float = 5.0
    user_burst_size: int = 3
    
    # Exponential backoff settings
    base_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    backoff_multiplier: float = 2.0
    max_retries: int = 3
    
    # Queue settings
    queue_max_size: int = 100
    command_timeout: float = 30.0


@dataclass
class RateLimitStatus:
    """Current rate limit status"""
    is_limited: bool
    retry_after: float
    remaining_requests: int
    total_requests: int
    queue_size: int
    

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, rate: float, burst_size: int):
        """
        Initialize token bucket
        
        Args:
            rate: Tokens per second
            burst_size: Maximum tokens in bucket
        """
        self.rate = rate
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.monotonic()
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    async def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Try to consume tokens from the bucket
        
        Returns:
            Tuple of (success, retry_after_seconds)
        """
        async with self._get_lock():
            now = time.monotonic()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(self.burst_size, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            
            # Calculate retry after time
            needed = tokens - self.tokens
            retry_after = needed / self.rate
            return False, retry_after
    
    async def get_remaining(self) -> float:
        """Get remaining tokens"""
        async with self._get_lock():
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.burst_size, self.tokens + elapsed * self.rate)
            self.last_update = now
            return self.tokens
    
    def reset(self):
        """Reset the bucket to full"""
        self.tokens = self.burst_size
        self.last_update = time.monotonic()


class EndpointTracker:
    """Tracks rate limits for specific Discord API endpoints"""
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._endpoint_mapping: Dict[str, str] = {}  # endpoint -> bucket key
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    def _get_bucket_key(self, endpoint: str) -> str:
        """Get or create bucket key for an endpoint"""
        # Normalize endpoint (remove specific IDs)
        # e.g., /channels/123/messages -> /channels/{id}/messages
        parts = endpoint.split('/')
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append('{id}')
            else:
                normalized.append(part)
        return '/'.join(normalized)
    
    async def check_endpoint(self, endpoint: str, tokens: int = 1) -> Tuple[bool, float]:
        """Check if request can proceed for an endpoint"""
        bucket_key = self._get_bucket_key(endpoint)
        
        async with self._get_lock():
            if bucket_key not in self._buckets:
                # Create new bucket with Discord-like limits
                self._buckets[bucket_key] = TokenBucket(rate=5.0, burst_size=5)
        
        return await self._buckets[bucket_key].consume(tokens)
    
    async def update_from_response(self, endpoint: str, headers: dict):
        """Update rate limits based on Discord API response headers"""
        # Discord rate limit headers:
        # X-RateLimit-Limit: max requests
        # X-RateLimit-Remaining: remaining requests
        # X-RateLimit-Reset: reset timestamp
        # X-RateLimit-Reset-After: seconds until reset
        # X-RateLimit-Bucket: bucket identifier
        
        bucket_key = self._get_bucket_key(endpoint)
        
        limit = headers.get('X-RateLimit-Limit')
        remaining = headers.get('X-RateLimit-Remaining')
        reset_after = headers.get('X-RateLimit-Reset-After')
        
        if limit and remaining and reset_after:
            try:
                async with self._get_lock():
                    if bucket_key in self._buckets:
                        bucket = self._buckets[bucket_key]
                        bucket.burst_size = int(limit)
                        bucket.tokens = float(remaining)
                        bucket.rate = int(limit) / max(float(reset_after), 1.0)
            except (ValueError, TypeError):
                pass


class CommandQueue:
    """Queue system for commands with priority handling"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._queue: deque = deque(maxlen=max_size)
        self._processing = False
        self._lock: Optional[asyncio.Lock] = None
        self._item_available = asyncio.Event()

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    async def enqueue(self, item: Tuple[int, Callable, tuple, dict]) -> bool:
        """
        Add item to queue with priority
        
        Args:
            item: Tuple of (priority, func, args, kwargs)
        
        Returns:
            True if added, False if queue full
        """
        async with self._get_lock():
            if len(self._queue) >= self.max_size:
                return False
            
            # Insert maintaining priority order (lower priority number = higher priority)
            inserted = False
            for i, existing in enumerate(self._queue):
                if item[0] < existing[0]:  # Compare priorities
                    self._queue.insert(i, item)
                    inserted = True
                    break
            
            if not inserted:
                self._queue.append(item)
            
            self._item_available.set()
            return True
    
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Tuple]:
        """Get next item from queue"""
        try:
            await asyncio.wait_for(self._item_available.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        
        async with self._get_lock():
            if self._queue:
                item = self._queue.popleft()
                if not self._queue:
                    self._item_available.clear()
                return item
            return None
    
    def get_size(self) -> int:
        """Get current queue size"""
        return len(self._queue)
    
    def clear(self):
        """Clear all items from queue"""
        self._queue.clear()
        self._item_available.clear()


class RateLimiter:
    """
    Global Rate Limit Manager for ABUSER Bot
    
    Provides comprehensive rate limiting at multiple levels:
    - Global: Overall request rate
    - Tier-based: Per-command-type limits
    - Guild: Per-server limits
    - User: Per-user limits
    - Endpoint: Per-API-endpoint tracking
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Global rate limiter (50 req/s max)
        self._global_bucket = TokenBucket(
            rate=self.config.global_requests_per_second,
            burst_size=self.config.global_burst_size
        )
        
        # Tier-based limiters
        self._tier_buckets: Dict[RateLimitTier, TokenBucket] = {}
        for tier, (rate, burst) in self.config.tier_limits.items():
            self._tier_buckets[tier] = TokenBucket(rate=rate, burst_size=burst)
        
        # Guild-specific limiters
        self._guild_buckets: Dict[int, TokenBucket] = {}
        self._guild_lock: Optional[asyncio.Lock] = None
        
        # User-specific limiters
        self._user_buckets: Dict[int, TokenBucket] = {}
        self._user_lock: Optional[asyncio.Lock] = None
        
        # Endpoint tracking
        self._endpoint_tracker = EndpointTracker()
        
        # Command queues per tier
        self._command_queues: Dict[RateLimitTier, CommandQueue] = {
            tier: CommandQueue(self.config.queue_max_size)
            for tier in RateLimitTier
        }
        
        # Retry tracking
        self._retry_counts: Dict[str, int] = defaultdict(int)
        self._retry_lock: Optional[asyncio.Lock] = None
        
        # Statistics
        self._stats = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'queued_requests': 0,
            'retried_requests': 0,
            'failed_requests': 0,
        }
        self._stats_lock: Optional[asyncio.Lock] = None
        
        # Status callbacks (for GUI updates)
        self._status_callbacks: List[Callable] = []
        
        # Start queue processor
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._running = False

    def _get_guild_lock(self) -> asyncio.Lock:
        if self._guild_lock is None:
            self._guild_lock = asyncio.Lock()
        return self._guild_lock

    def _get_user_lock(self) -> asyncio.Lock:
        if self._user_lock is None:
            self._user_lock = asyncio.Lock()
        return self._user_lock

    def _get_retry_lock(self) -> asyncio.Lock:
        if self._retry_lock is None:
            self._retry_lock = asyncio.Lock()
        return self._retry_lock

    def _get_stats_lock(self) -> asyncio.Lock:
        if self._stats_lock is None:
            self._stats_lock = asyncio.Lock()
        return self._stats_lock
    
    async def start(self):
        """Start the rate limiter and queue processors"""
        self._running = True
        self._queue_processor_task = asyncio.create_task(self._process_queues())
        logger.info("Rate limiter started")
    
    async def stop(self):
        """Stop the rate limiter and cleanup"""
        self._running = False
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Clear all queues
        for queue in self._command_queues.values():
            queue.clear()
        
        logger.info("Rate limiter stopped")
    
    def _get_guild_bucket(self, guild_id: Optional[int]) -> TokenBucket:
        """Get or create guild-specific bucket"""
        if guild_id is None:
            # Use a default bucket for DMs
            guild_id = 0
        
        if guild_id not in self._guild_buckets:
            self._guild_buckets[guild_id] = TokenBucket(
                rate=self.config.guild_requests_per_second,
                burst_size=self.config.guild_burst_size
            )
        return self._guild_buckets[guild_id]
    
    def _get_user_bucket(self, user_id: int) -> TokenBucket:
        """Get or create user-specific bucket"""
        if user_id not in self._user_buckets:
            self._user_buckets[user_id] = TokenBucket(
                rate=self.config.user_requests_per_second,
                burst_size=self.config.user_burst_size
            )
        return self._user_buckets[user_id]
    
    async def check_rate_limit(
        self,
        tier: RateLimitTier = RateLimitTier.MODERATE,
        guild_id: Optional[int] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None
    ) -> RateLimitStatus:
        """
        Check all rate limits for a request
        
        Returns:
            RateLimitStatus indicating if request can proceed
        """
        async with self._get_stats_lock():
            self._stats['total_requests'] += 1
        
        # Check global limit
        global_ok, global_retry = await self._global_bucket.consume()
        if not global_ok:
            async with self._get_stats_lock():
                self._stats['rate_limited_requests'] += 1
            return RateLimitStatus(
                is_limited=True,
                retry_after=global_retry,
                remaining_requests=0,
                total_requests=self._stats['total_requests'],
                queue_size=await self._get_total_queue_size()
            )
        
        # Check tier limit
        tier_bucket = self._tier_buckets[tier]
        tier_ok, tier_retry = await tier_bucket.consume()
        if not tier_ok:
            async with self._get_stats_lock():
                self._stats['rate_limited_requests'] += 1
            return RateLimitStatus(
                is_limited=True,
                retry_after=tier_retry,
                remaining_requests=0,
                total_requests=self._stats['total_requests'],
                queue_size=await self._get_total_queue_size()
            )
        
        # Check guild limit
        if guild_id is not None:
            guild_bucket = self._get_guild_bucket(guild_id)
            guild_ok, guild_retry = await guild_bucket.consume()
            if not guild_ok:
                async with self._get_stats_lock():
                    self._stats['rate_limited_requests'] += 1
                return RateLimitStatus(
                    is_limited=True,
                    retry_after=guild_retry,
                    remaining_requests=0,
                    total_requests=self._stats['total_requests'],
                    queue_size=await self._get_total_queue_size()
                )
        
        # Check user limit
        if user_id is not None:
            user_bucket = self._get_user_bucket(user_id)
            user_ok, user_retry = await user_bucket.consume()
            if not user_ok:
                async with self._get_stats_lock():
                    self._stats['rate_limited_requests'] += 1
                return RateLimitStatus(
                    is_limited=True,
                    retry_after=user_retry,
                    remaining_requests=0,
                    total_requests=self._stats['total_requests'],
                    queue_size=await self._get_total_queue_size()
                )
        
        # Check endpoint limit
        if endpoint is not None:
            endpoint_ok, endpoint_retry = await self._endpoint_tracker.check_endpoint(endpoint)
            if not endpoint_ok:
                async with self._get_stats_lock():
                    self._stats['rate_limited_requests'] += 1
                return RateLimitStatus(
                    is_limited=True,
                    retry_after=endpoint_retry,
                    remaining_requests=0,
                    total_requests=self._stats['total_requests'],
                    queue_size=await self._get_total_queue_size()
                )
        
        return RateLimitStatus(
            is_limited=False,
            retry_after=0.0,
            remaining_requests=int(await self._global_bucket.get_remaining()),
            total_requests=self._stats['total_requests'],
            queue_size=await self._get_total_queue_size()
        )
    
    async def acquire(
        self,
        tier: RateLimitTier = RateLimitTier.MODERATE,
        guild_id: Optional[int] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire permission to make a request, waiting if necessary
        
        Returns:
            True if acquired, False if timeout
        """
        start_time = time.monotonic()
        
        while True:
            status = await self.check_rate_limit(tier, guild_id, user_id, endpoint)
            
            if not status.is_limited:
                return True
            
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed + status.retry_after > timeout:
                    return False
            
            await asyncio.sleep(min(status.retry_after, 5.0))  # Max 5 second wait per iteration
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        tier: RateLimitTier = RateLimitTier.MODERATE,
        guild_id: Optional[int] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute a function with automatic rate limit retry
        
        Uses exponential backoff when rate limited
        """
        operation_key = f"{func.__name__}:{guild_id}:{user_id}"
        
        for attempt in range(self.config.max_retries + 1):
            # Wait for rate limit
            acquired = await self.acquire(tier, guild_id, user_id, endpoint)
            if not acquired:
                raise RateLimitExceeded("Could not acquire rate limit token")
            
            try:
                result = await func(*args, **kwargs)
                
                # Reset retry count on success
                async with self._get_retry_lock():
                    self._retry_counts.pop(operation_key, None)
                
                return result
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    async with self._stats_lock:
                        self._stats['retried_requests'] += 1
                    
                    if attempt >= self.config.max_retries:
                        async with self._get_stats_lock():
                            self._stats['failed_requests'] += 1
                        raise RateLimitExceeded(f"Rate limited after {attempt + 1} attempts")
                    
                    # Calculate retry delay with exponential backoff
                    async with self._get_retry_lock():
                        retry_count = self._retry_counts[operation_key]
                        self._retry_counts[operation_key] = retry_count + 1
                    
                    delay = min(
                        self.config.base_retry_delay * (self.config.backoff_multiplier ** retry_count),
                        self.config.max_retry_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    delay += random.random() * 0.5
                    
                    logger.warning(f"Rate limited, retrying in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                else:
                    raise
        
        raise RateLimitExceeded("Max retries exceeded")
    
    async def queue_command(
        self,
        func: Callable,
        *args,
        priority: int = 5,
        tier: RateLimitTier = RateLimitTier.MODERATE,
        **kwargs
    ) -> bool:
        """
        Queue a command for execution
        
        Lower priority numbers are executed first (1 = highest)
        
        Returns:
            True if queued successfully
        """
        queue = self._command_queues[tier]
        item = (priority, func, args, kwargs)
        
        success = await queue.enqueue(item)
        if success:
            async with self._get_stats_lock():
                self._stats['queued_requests'] += 1
        
        return success
    
    async def _process_queues(self):
        """Background task to process queued commands"""
        while self._running:
            try:
                # Process highest priority items first
                for tier in [RateLimitTier.MINIMAL, RateLimitTier.LIGHT, 
                            RateLimitTier.MODERATE, RateLimitTier.HEAVY, RateLimitTier.CRITICAL]:
                    queue = self._command_queues[tier]
                    
                    # Try to get an item with short timeout
                    item = await queue.dequeue(timeout=0.1)
                    if item is None:
                        continue
                    
                    priority, func, args, kwargs = item
                    
                    # Wait for rate limit
                    guild_id = kwargs.get('guild_id')
                    user_id = kwargs.get('user_id')
                    
                    acquired = await self.acquire(tier, guild_id, user_id, timeout=self.config.command_timeout)
                    
                    if acquired:
                        try:
                            await func(*args, **kwargs)
                        except Exception as e:
                            logger.error(f"Error executing queued command: {e}")
                    else:
                        logger.warning(f"Command timed out waiting for rate limit")
                
                await asyncio.sleep(0.01)  # Small sleep to prevent busy-waiting
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(1)
    
    async def _get_total_queue_size(self) -> int:
        """Get total size of all command queues"""
        return sum(q.get_size() for q in self._command_queues.values())
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        return {
            'global_tokens': self._global_bucket.tokens,
            'global_rate': self._global_bucket.rate,
            'total_queue_size': sum(q.get_size() for q in self._command_queues.values()),
            'queue_sizes': {tier.value: q.get_size() for tier, q in self._command_queues.items()},
            'guild_buckets': len(self._guild_buckets),
            'user_buckets': len(self._user_buckets),
            **self._stats
        }
    
    def register_status_callback(self, callback: Callable):
        """Register a callback for status updates"""
        self._status_callbacks.append(callback)
    
    def unregister_status_callback(self, callback: Callable):
        """Unregister a status callback"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create global rate limiter instance"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(config)
    return _global_rate_limiter


def reset_rate_limiter():
    """Reset the global rate limiter (for testing)"""
    global _global_rate_limiter
    _global_rate_limiter = None


# Decorator for commands
def rate_limit(
    tier: RateLimitTier = RateLimitTier.MODERATE,
    custom_cooldown: Optional[Tuple[float, commands.BucketType]] = None,
    queue_if_limited: bool = False
):
    """
    Decorator to apply rate limiting to a command
    
    Args:
        tier: Rate limit tier for this command
        custom_cooldown: Optional (seconds, bucket) for additional discord.py cooldown
        queue_if_limited: Whether to queue the command if rate limited
    """
    def decorator(func):
        # Apply discord.py cooldown if specified
        if custom_cooldown:
            seconds, bucket_type = custom_cooldown
            func = commands.cooldown(1, seconds, bucket_type)(func)
        
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            limiter = get_rate_limiter()
            
            guild_id = ctx.guild.id if ctx.guild else None
            user_id = ctx.author.id
            
            # Check rate limits
            status = await limiter.check_rate_limit(
                tier=tier,
                guild_id=guild_id,
                user_id=user_id
            )
            
            if status.is_limited:
                if queue_if_limited:
                    # Queue the command for later
                    success = await limiter.queue_command(
                        func,
                        self, ctx, *args, **kwargs,
                        tier=tier,
                        guild_id=guild_id,
                        user_id=user_id
                    )
                    if success:
                        return await ctx.send(
                            f"⏳ Rate limited! Command queued (position: {status.queue_size}).",
                            delete_after=5
                        )
                    else:
                        return await ctx.send(
                            f"⏳ Rate limited! Queue full, please try again in {status.retry_after:.1f}s.",
                            delete_after=5
                        )
                else:
                    # Send rate limit message
                    return await ctx.send(
                        f"⏳ Rate limited! Please wait {status.retry_after:.1f}s before trying again.",
                        delete_after=min(status.retry_after, 10)
                    )
            
            # Execute the command
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator


# Tier-specific decorators
def rate_limit_critical(custom_cooldown: Optional[Tuple[float, commands.BucketType]] = None):
    """Rate limit decorator for critical tier commands"""
    return rate_limit(RateLimitTier.CRITICAL, custom_cooldown)

def rate_limit_heavy(custom_cooldown: Optional[Tuple[float, commands.BucketType]] = None):
    """Rate limit decorator for heavy tier commands"""
    return rate_limit(RateLimitTier.HEAVY, custom_cooldown)

def rate_limit_moderate(custom_cooldown: Optional[Tuple[float, commands.BucketType]] = None):
    """Rate limit decorator for moderate tier commands"""
    return rate_limit(RateLimitTier.MODERATE, custom_cooldown)

def rate_limit_light(custom_cooldown: Optional[Tuple[float, commands.BucketType]] = None):
    """Rate limit decorator for light tier commands"""
    return rate_limit(RateLimitTier.LIGHT, custom_cooldown)

def rate_limit_minimal(custom_cooldown: Optional[Tuple[float, commands.BucketType]] = None):
    """Rate limit decorator for minimal tier commands"""
    return rate_limit(RateLimitTier.MINIMAL, custom_cooldown)


# Safe API call wrapper with automatic retry
async def safe_api_call(
    func: Callable,
    *args,
    tier: RateLimitTier = RateLimitTier.MODERATE,
    guild_id: Optional[int] = None,
    user_id: Optional[int] = None,
    endpoint: Optional[str] = None,
    error_message: str = "API call failed",
    **kwargs
) -> Optional[Any]:
    """
    Make an API call with rate limiting and error handling
    
    Returns:
        Result of the function call, or None if failed
    """
    limiter = get_rate_limiter()
    
    try:
        return await limiter.execute_with_retry(
            func, *args,
            tier=tier,
            guild_id=guild_id,
            user_id=user_id,
            endpoint=endpoint,
            **kwargs
        )
    except RateLimitExceeded as e:
        logger.warning(f"{error_message}: {e}")
        return None
    except discord.HTTPException as e:
        logger.error(f"{error_message}: HTTP {e.status}")
        return None
    except Exception as e:
        logger.error(f"{error_message}: {e}")
        return None


# Update __all__ for exports
__all__ = [
    # Classes
    'RateLimiter',
    'RateLimitConfig',
    'RateLimitStatus',
    'RateLimitTier',
    'TokenBucket',
    'CommandQueue',
    'EndpointTracker',
    'RateLimitExceeded',
    
    # Functions
    'get_rate_limiter',
    'reset_rate_limiter',
    'rate_limit',
    'rate_limit_critical',
    'rate_limit_heavy',
    'rate_limit_moderate',
    'rate_limit_light',
    'rate_limit_minimal',
    'safe_api_call',
]
