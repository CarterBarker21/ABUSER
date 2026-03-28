"""
Utility modules for ABUSER bot
"""

from .error_handler import (
    handle_errors,
    with_retry,
    format_discord_error,
    CommandCooldownManager,
    ErrorRateLimiter,
    safe_delete_message,
    safe_send,
    cooldown_manager,
)
from .logger import setup_logger, ColoredFormatter
from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStatus,
    RateLimitTier,
    TokenBucket,
    CommandQueue,
    EndpointTracker,
    RateLimitExceeded,
    get_rate_limiter,
    reset_rate_limiter,
    rate_limit,
    rate_limit_critical,
    rate_limit_heavy,
    rate_limit_moderate,
    rate_limit_light,
    rate_limit_minimal,
    safe_api_call,
)

__all__ = [
    # Error handling
    'handle_errors',
    'with_retry',
    'format_discord_error',
    'CommandCooldownManager',
    'ErrorRateLimiter',
    'safe_delete_message',
    'safe_send',
    'cooldown_manager',
    # Logging
    'setup_logger',
    'ColoredFormatter',
    # Rate limiting
    'RateLimiter',
    'RateLimitConfig',
    'RateLimitStatus',
    'RateLimitTier',
    'TokenBucket',
    'CommandQueue',
    'EndpointTracker',
    'RateLimitExceeded',
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
