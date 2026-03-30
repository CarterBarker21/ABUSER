"""
ABUSER Bot - Bot Runner for PyQt6 GUI
Handles running the bot in a separate thread with signal emissions
"""

import asyncio
import logging
import sys
import re
import traceback
from typing import Optional, List, Dict, Any

from PyQt6.QtCore import (
    QObject, QRunnable, QThreadPool, pyqtSignal, QThread,
    QMetaObject, Qt, Q_ARG, QTimer
)
from PyQt6.QtWidgets import QApplication

# Import the bot core
from abuse.core.bot import ABUSERBot


class BotSignals(QObject):
    """
    Signals emitted by the BotRunner during bot lifecycle.
    These signals are thread-safe and can be connected to GUI elements.
    """
    # Connection status signals
    bot_connected = pyqtSignal()
    bot_ready = pyqtSignal(str, str, int)  # user_name, user_id, guild_count
    bot_disconnected = pyqtSignal()
    bot_error = pyqtSignal(str)  # error_message
    
    # Login-specific signals
    login_success = pyqtSignal(str, str)  # user_name, user_id
    login_failed = pyqtSignal(str)  # error_message
    logout_completed = pyqtSignal()
    
    # Log signals
    log_received = pyqtSignal(str, str)  # level, message
    
    # Guild signals
    guilds_updated = pyqtSignal(list)  # list of guild dicts
    
    # Nuke action signals
    nuke_action_completed = pyqtSignal(str, bool, str)  # action_id, success, message
    
    # Setup server signals
    setup_server_completed = pyqtSignal(bool, str)  # success, message
    
    # Status signals
    status_changed = pyqtSignal(str)  # status message
    connection_state_changed = pyqtSignal(bool)  # is_connected
    latency_updated = pyqtSignal(float)  # ping in milliseconds
    
    # Rate limit signals
    rate_limit_status_changed = pyqtSignal(dict)  # rate limit status dict
    rate_limit_warning = pyqtSignal(str)  # warning message


class GUILogHandler(logging.Handler):
    """
    Custom logging handler that forwards log records to the GUI via signals.
    """
    
    def __init__(self, signals: BotSignals):
        super().__init__()
        self.signals = signals
        self.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        ))
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record as a GUI signal"""
        try:
            msg = self.format(record)
            # Split level from message for better GUI handling
            level = record.levelname
            self.signals.log_received.emit(level, msg)
        except Exception:
            self.handleError(record)


class BotWorker(QRunnable):
    """
    Worker runnable that runs the bot asyncio event loop in a separate thread.
    Uses QThreadPool for efficient thread management.
    """
    
    def __init__(self, bot: ABUSERBot, signals: BotSignals):
        super().__init__()
        self.bot = bot
        self.signals = signals
        self._is_running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def run(self):
        """Run the bot in a dedicated asyncio event loop"""
        self._is_running = True
        
        try:
            # Create a new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # Set up signal emission from bot events
            self._setup_bot_hooks()
            
            # Emit connected signal
            self.signals.bot_connected.emit()
            self.signals.status_changed.emit("Connecting to Discord...")
            
            # Run the bot
            self._loop.run_until_complete(self._run_bot())
            
        except Exception as e:
            error_msg = f"Bot worker error: {str(e)}"
            self.signals.bot_error.emit(error_msg)
            self.signals.login_failed.emit(str(e))
            self.signals.log_received.emit("ERROR", f"{error_msg}\n{traceback.format_exc()}")
        finally:
            self._is_running = False
            self.signals.bot_disconnected.emit()
            self.signals.connection_state_changed.emit(False)
            self.signals.status_changed.emit("Disconnected")
            
            # Clean up the event loop
            try:
                if self._loop and not self._loop.is_closed():
                    # Cancel any remaining tasks
                    pending = asyncio.all_tasks(self._loop) if hasattr(asyncio, 'all_tasks') else asyncio.Task.all_tasks(self._loop)
                    for task in pending:
                        task.cancel()
                    
                    # Run loop briefly to allow task cancellation to complete
                    if pending:
                        try:
                            self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        except Exception:
                            pass
                    
                    self._loop.close()
            except Exception as e:
                self.signals.log_received.emit("ERROR", f"Error closing event loop: {e}")
    
    async def _run_bot(self):
        """Async method to run the bot with proper lifecycle management"""
        try:
            await self.bot.start(self.bot.token)
        except Exception as e:
            error_msg = f"Bot runtime error: {str(e)}"
            self.signals.bot_error.emit(error_msg)
            self.signals.login_failed.emit(str(e))
            # Log the error but don't re-raise to prevent thread crash
            import traceback
            self.signals.log_received.emit("ERROR", f"{error_msg}\n{traceback.format_exc()}")
    
    def _setup_bot_hooks(self):
        """Set up hooks to forward bot events to GUI signals"""
        # Use getattr to safely get original handlers (may not exist)
        original_on_ready = getattr(self.bot, 'on_ready', None)
        original_on_disconnect = getattr(self.bot, 'on_disconnect', None)
        original_on_connect = getattr(self.bot, 'on_connect', None)
        
        async def hooked_on_ready():
            """Hook for on_ready event"""
            if original_on_ready:
                await original_on_ready()
            
            # Get user info - check if bot.user exists to avoid AttributeError
            if self.bot.user is None:
                self.signals.log_received.emit("ERROR", "Bot user is None in on_ready")
                return
            
            user_name = str(self.bot.user)
            user_id = str(self.bot.user.id)
            guild_count = len(self.bot.guilds) if self.bot.guilds else 0
            
            # Emit ready signal
            self.signals.bot_ready.emit(user_name, user_id, guild_count)
            self.signals.login_success.emit(user_name, user_id)
            self.signals.connection_state_changed.emit(True)
            self.signals.status_changed.emit(f"Ready as {user_name}")
            
            # Update guilds
            self._update_guilds()
        
        async def hooked_on_disconnect():
            """Hook for on_disconnect event"""
            if original_on_disconnect:
                await original_on_disconnect()
            self.signals.bot_disconnected.emit()
            self.signals.connection_state_changed.emit(False)
            self.signals.status_changed.emit("Disconnected")
        
        async def hooked_on_connect():
            """Hook for on_connect event"""
            if original_on_connect:
                await original_on_connect()
            self.signals.bot_connected.emit()
            self.signals.status_changed.emit("Connected to Discord")
        
        # Replace methods with hooked versions
        self.bot.on_ready = hooked_on_ready
        self.bot.on_disconnect = hooked_on_disconnect
        self.bot.on_connect = hooked_on_connect
        
        # Set up guild update hook (use getattr to handle missing attributes)
        original_on_guild_join = getattr(self.bot, 'on_guild_join', None)
        original_on_guild_remove = getattr(self.bot, 'on_guild_remove', None)
        
        async def hooked_on_guild_join(guild):
            """Hook for on_guild_join event"""
            if original_on_guild_join:
                await original_on_guild_join(guild)
            self._update_guilds()
        
        async def hooked_on_guild_remove(guild):
            """Hook for on_guild_remove event"""
            if original_on_guild_remove:
                await original_on_guild_remove(guild)
            self._update_guilds()
        
        # Only set hooks if the bot has these events or we want to add them
        if not hasattr(self.bot, 'on_guild_join') or original_on_guild_join:
            self.bot.on_guild_join = hooked_on_guild_join
        if not hasattr(self.bot, 'on_guild_remove') or original_on_guild_remove:
            self.bot.on_guild_remove = hooked_on_guild_remove
    
    async def _fetch_icon_data(self, icon_url: str) -> Optional[bytes]:
        """Fetch guild icon image data from URL.
        
        Args:
            icon_url: The icon URL
            
        Returns:
            Image bytes if successful, None otherwise
        """
        if not icon_url:
            return None
        try:
            session = getattr(self.bot, 'session', None)
            if session is None:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(icon_url) as response:
                        return await response.read() if response.status == 200 else None
            else:
                async with session.get(icon_url) as response:
                    return await response.read() if response.status == 200 else None
        except Exception:
            return None
    
    def _update_guilds(self):
        """Update guild list and emit signal (sync wrapper for async)"""
        # Schedule the async work in the bot's event loop
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._update_guilds_async(), self._loop)
    
    async def _update_guilds_async(self):
        """Async implementation of guild list update with icon fetching."""
        try:
            guild_list = []
            # Handle case where bot.guilds might not be available
            guilds = getattr(self.bot, 'guilds', [])
            for guild in guilds:
                try:
                    # Calculate creation date from snowflake ID
                    created_at = None
                    if hasattr(guild, 'id'):
                        try:
                            from datetime import datetime, timezone
                            # Discord snowflake to timestamp: (id >> 22) + 1420070400000
                            created_timestamp = ((guild.id >> 22) + 1420070400000) / 1000
                            created_at = datetime.fromtimestamp(created_timestamp, tz=timezone.utc)
                        except Exception:
                            pass
                    
                    # Get channel count
                    channels_count = 0
                    if hasattr(guild, 'channels'):
                        try:
                            channels_count = len(guild.channels)
                        except Exception:
                            pass
                    
                    # Get role count
                    roles_count = 0
                    if hasattr(guild, 'roles'):
                        try:
                            roles_count = len(guild.roles)
                        except Exception:
                            pass
                    
                    # Get boost count (premium_subscription_count in discord.py)
                    boost_count = 0
                    if hasattr(guild, 'premium_subscription_count'):
                        try:
                            boost_count = guild.premium_subscription_count or 0
                        except Exception:
                            pass
                    
                    # Get bot permissions and owner status
                    my_permissions = 0
                    is_owner = False
                    bot_user_id = None
                    
                    # Get bot user ID - for selfbots, this is the user's account
                    if self.bot and self.bot.user:
                        bot_user_id = getattr(self.bot.user, 'id', None)
                    
                    # Get guild owner ID - try owner_id first, then fall back to owner.id
                    guild_owner_id = getattr(guild, 'owner_id', None)
                    if guild_owner_id is None and hasattr(guild, 'owner') and guild.owner:
                        guild_owner_id = getattr(guild.owner, 'id', None)
                    
                    # Check if bot is owner (convert both to int for comparison)
                    # For selfbots: the bot IS the user, so we compare user.id with guild.owner_id
                    if bot_user_id and guild_owner_id:
                        try:
                            bot_id_int = int(bot_user_id)
                            owner_id_int = int(guild_owner_id)
                            is_owner = bot_id_int == owner_id_int
                        except (ValueError, TypeError) as e:
                            # Fallback to string comparison if int conversion fails
                            is_owner = str(bot_user_id) == str(guild_owner_id)
                        
                        # Debug logging - always log the comparison details
                        self.signals.log_received.emit(
                            "DEBUG", 
                            f"OWNER CHECK: {guild.name} | bot_id={bot_user_id} (type={type(bot_user_id).__name__}) | "
                            f"owner_id={guild_owner_id} (type={type(guild_owner_id).__name__}) | is_owner={is_owner}"
                        )
                        
                        # INFO level log for owned servers
                        if is_owner:
                            self.signals.log_received.emit("INFO", f"OWNERSHIP: {guild.name} - You are the server owner")
                    else:
                        # Log missing IDs for debugging
                        self.signals.log_received.emit(
                            "DEBUG", 
                            f"OWNER CHECK MISSING: {guild.name} | bot_user_id={bot_user_id} | owner_id={guild_owner_id}"
                        )
                    
                    # Get bot's permissions in this guild
                    if hasattr(guild, 'me') and guild.me:
                        try:
                            perms = getattr(guild.me, 'guild_permissions', None)
                            if perms:
                                my_permissions = perms.value
                        except Exception:
                            pass
                    
                    # Get icon URL
                    icon_url = None
                    if hasattr(guild, 'icon') and guild.icon:
                        try:
                            icon_url = str(guild.icon.url)
                        except Exception:
                            pass
                    
                    # Fetch icon data asynchronously
                    icon_data = None
                    if icon_url:
                        icon_data = await self._fetch_icon_data(icon_url)
                    
                    guild_info = {
                        'id': str(guild.id) if hasattr(guild, 'id') else 'unknown',
                        'name': getattr(guild, 'name', 'Unknown Guild'),
                        'member_count': getattr(guild, 'member_count', 0),
                        'icon_url': icon_url,
                        'owner_id': str(guild.owner_id) if hasattr(guild, 'owner_id') else None,
                        'created_at': created_at.isoformat() if created_at else None,
                        'channels_count': channels_count,
                        'roles_count': roles_count,
                        'boost_count': boost_count,
                        'my_permissions': my_permissions,
                        'is_owner': is_owner,
                        'icon_data': icon_data,  # Raw image bytes
                    }
                    guild_list.append(guild_info)
                except Exception as e:
                    # Skip guilds that can't be processed
                    self.signals.log_received.emit("WARNING", f"Error processing guild: {e}")
            
            self.signals.guilds_updated.emit(guild_list)
        except Exception as e:
            self.signals.log_received.emit("ERROR", f"Error updating guilds: {e}")
    
    def stop(self):
        """Stop the bot gracefully"""
        if self._loop and self._is_running:
            try:
                # Schedule shutdown in the event loop
                future = asyncio.run_coroutine_threadsafe(
                    self._shutdown(), self._loop
                )
                # Wait for shutdown with timeout
                future.result(timeout=10)
            except Exception as e:
                self.signals.log_received.emit("ERROR", f"Error stopping bot: {e}")
    
    async def _shutdown(self):
        """Async shutdown sequence"""
        try:
            await self.bot.shutdown()
        except Exception as e:
            self.signals.log_received.emit("ERROR", f"Shutdown error: {e}")


class BotRunner(QObject):
    """
    Main class for running the ABUSER bot within the PyQt6 GUI.
    
    This class manages the bot lifecycle in a separate thread,
    emitting signals that can be connected to GUI elements for
    real-time status updates, logging, and guild information.
    
    Signals:
        bot_connected(): Emitted when bot connects to Discord
        bot_ready(user_name, user_id, guild_count): Emitted when bot is ready
        bot_disconnected(): Emitted when bot disconnects
        bot_error(error_message): Emitted when an error occurs
        login_success(user_name, user_id): Emitted when login is successful
        login_failed(error_message): Emitted when login fails
        logout_completed(): Emitted when logout is complete
        log_received(level, message): Emitted when a log message is received
        guilds_updated(guild_list): Emitted when guild list changes
        status_changed(status_message): Emitted when status changes
        connection_state_changed(is_connected): Emitted when connection state changes
        rate_limit_status_changed(status): Emitted when rate limit status changes
        rate_limit_warning(message): Emitted when rate limit warning occurs
    
    Example:
        runner = BotRunner()
        runner.login_success.connect(on_login_success)
        runner.login_failed.connect(on_login_failed)
        runner.start_bot("your_token_here")
    """
    
    # Re-export signals for easy access
    bot_connected = pyqtSignal()
    bot_ready = pyqtSignal(str, str, int)
    bot_disconnected = pyqtSignal()
    bot_error = pyqtSignal(str)
    login_success = pyqtSignal(str, str)
    login_failed = pyqtSignal(str)
    logout_completed = pyqtSignal()
    log_received = pyqtSignal(str, str)
    guilds_updated = pyqtSignal(list)
    nuke_action_completed = pyqtSignal(str, bool, str)  # action_id, success, message
    setup_server_completed = pyqtSignal(bool, str)  # success, message
    status_changed = pyqtSignal(str)
    connection_state_changed = pyqtSignal(bool)
    latency_updated = pyqtSignal(float)
    rate_limit_status_changed = pyqtSignal(dict)
    rate_limit_warning = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create signals object
        self.signals = BotSignals()
        
        # Forward all signals
        self.signals.bot_connected.connect(self.bot_connected)
        self.signals.bot_ready.connect(self.bot_ready)
        self.signals.bot_disconnected.connect(self.bot_disconnected)
        self.signals.bot_error.connect(self.bot_error)
        self.signals.login_success.connect(self.login_success)
        self.signals.login_failed.connect(self.login_failed)
        self.signals.logout_completed.connect(self.logout_completed)
        self.signals.log_received.connect(self.log_received)
        self.signals.guilds_updated.connect(self.guilds_updated)
        self.signals.nuke_action_completed.connect(self.nuke_action_completed)
        self.signals.setup_server_completed.connect(self.setup_server_completed)
        self.signals.status_changed.connect(self.status_changed)
        self.signals.connection_state_changed.connect(self.connection_state_changed)
        self.signals.latency_updated.connect(self.latency_updated)
        self.signals.rate_limit_status_changed.connect(self.rate_limit_status_changed)
        self.signals.rate_limit_warning.connect(self.rate_limit_warning)
        
        # Bot instance and worker
        self._bot: Optional[ABUSERBot] = None
        self._worker: Optional[BotWorker] = None
        self._thread_pool = QThreadPool()
        
        # State tracking
        self._is_running = False
        self._is_connected = False
        self._user_name: Optional[str] = None
        self._user_id: Optional[str] = None
        self._guilds: List[Dict[str, Any]] = []
        self._token: Optional[str] = None
        self._latency_ms: Optional[float] = None
        self._gui_handler: Optional[GUILogHandler] = None
        
        # Rate limit tracking
        self._rate_limit_status: Dict[str, Any] = {}
        self._rate_limit_update_timer = None
        self._last_rate_limit_warning = 0

        self._latency_timer = QTimer(self)
        self._latency_timer.setInterval(3000)
        self._latency_timer.timeout.connect(self._emit_latency_update)

        self.signals.bot_ready.connect(self._on_bot_ready)
        self.signals.bot_disconnected.connect(self._on_bot_disconnected)
        self.signals.guilds_updated.connect(self._on_guilds_updated)
        self.signals.connection_state_changed.connect(self._on_connection_changed)
    
    @property
    def is_running(self) -> bool:
        """Check if the bot is currently running"""
        return self._is_running
    
    @property
    def is_connected(self) -> bool:
        """Check if the bot is connected to Discord"""
        return self._is_connected
    
    @property
    def user_name(self) -> Optional[str]:
        """Get the bot user's name (available after ready)"""
        return self._user_name
    
    @property
    def user_id(self) -> Optional[str]:
        """Get the bot user's ID (available after ready)"""
        return self._user_id
    
    @property
    def guilds(self) -> List[Dict[str, Any]]:
        """Get the list of guilds the bot is in"""
        return self._guilds.copy()
    
    @property
    def token(self) -> Optional[str]:
        """Get the current token"""
        return self._token

    @property
    def latency_ms(self) -> Optional[float]:
        """Get the last known latency in milliseconds."""
        return self._latency_ms
    
    @staticmethod
    def validate_token(token: str) -> tuple[bool, str]:
        """
        Validate Discord token format.
        
        Args:
            token: The Discord token to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not token:
            return False, "Token is required"
        
        token = token.strip()
        
        if len(token) < 50:
            return False, "Token is too short"
        
        # Discord tokens typically have 3 parts separated by dots
        # or are a single long string for bot tokens
        parts = token.split('.')
        
        if len(parts) == 3:
            # User token format: base64.user_id.timestamp_hmac
            try:
                import base64
                # Try to decode the first part (should be base64 encoded user ID)
                padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
                decoded = base64.urlsafe_b64decode(padded)
                # Should be a valid snowflake/ID
                user_id = int(decoded)
                if user_id <= 0:
                    return False, "Invalid token format (invalid user ID)"
            except Exception:
                return False, "Invalid token format (not a valid base64 encoded ID)"
        elif len(parts) == 1:
            # Bot token format - typically longer than 50 chars
            # Just check length as bot tokens don't have a standard format we can validate
            pass
        else:
            return False, "Invalid token format (unexpected structure)"
        
        return True, ""
    
    def start_bot(self, token: Optional[str] = None) -> bool:
        """
        Start the bot in a separate thread with the provided token.
        
        Args:
            token: Discord token. Must be provided for login flow.
        
        Returns:
            True if bot was started successfully, False otherwise
        """
        if self._is_running:
            self.signals.log_received.emit("WARNING", "Bot is already running")
            return False
        
        # Validate token if provided
        if token:
            is_valid, error_msg = self.validate_token(token)
            if not is_valid:
                self.signals.login_failed.emit(f"Invalid token: {error_msg}")
                self.signals.log_received.emit("ERROR", f"Token validation failed: {error_msg}")
                return False
            self._token = token
        elif not self._token:
            error_msg = "No token provided"
            self.signals.login_failed.emit(error_msg)
            self.signals.log_received.emit("ERROR", error_msg)
            return False
        
        try:
            # Create bot instance with the provided token
            # Pass token to constructor so it's set before discord.py initializes
            actual_token = token if token else self._token
            self._bot = ABUSERBot(token=actual_token)
            
            # Set up log forwarding
            self._setup_log_forwarding()
            
            # Create and start worker
            self._worker = BotWorker(self._bot, self.signals)
            self._thread_pool.start(self._worker)
            
            self._is_running = True
            
            self.signals.log_received.emit("INFO", "Bot runner started")
            self.signals.status_changed.emit("Starting bot...")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start bot: {str(e)}"
            self.signals.login_failed.emit(error_msg)
            self.signals.bot_error.emit(error_msg)
            self.signals.log_received.emit("ERROR", error_msg)
            self._is_running = False
            return False
    
    def stop_bot(self, timeout: int = 10) -> bool:
        """
        Stop the bot gracefully (logout).
        
        Args:
            timeout: Maximum seconds to wait for graceful shutdown
        
        Returns:
            True if stop was initiated successfully
        """
        if not self._is_running or not self._worker:
            self.signals.log_received.emit("WARNING", "Bot is not running")
            return False
        
        self.signals.status_changed.emit("Stopping bot...")
        self.signals.log_received.emit("INFO", "Stopping bot...")
        
        # Signal worker to stop
        self._worker.stop()
        
        self._is_running = False
        self._is_connected = False
        self._user_name = None
        self._user_id = None
        self._guilds = []
        self._latency_ms = None
        self._latency_timer.stop()
        
        # Emit logout completed after a short delay for cleanup
        self.signals.logout_completed.emit()
        
        return True
    
    def restart_bot(self, token: Optional[str] = None) -> bool:
        """
        Restart the bot.
        
        Args:
            token: Optional new token to use. If not provided, uses previous token.
        
        Returns:
            True if restart was initiated successfully
        """
        use_token = token if token else self._token
        if self._is_running:
            self.stop_bot()
            QTimer.singleShot(1000, lambda: self.start_bot(use_token))
            return True
        return self.start_bot(use_token)
    
    def send_command(self, command: str, *args) -> bool:
        """
        Send a command to the bot for execution.
        
        Args:
            command: Command name to execute
            *args: Command arguments
        
        Returns:
            True if command was queued successfully
        """
        if not self._is_running or not self._bot:
            self.signals.log_received.emit("ERROR", "Bot is not running")
            return False
        
        # Commands can only be executed in the bot's event loop
        # This is a placeholder for future command execution
        self.signals.log_received.emit("INFO", f"Command queued: {command}")
        return True
    
    def execute_nuke_action(self, action_id: str, guild_id: int) -> bool:
        """
        Execute a nuke action on a specific guild.
        
        Args:
            action_id: The action to execute (e.g., 'delete_channels', 'ban_all', 'nuke_server')
            guild_id: The target guild ID
        
        Returns:
            True if action was queued successfully
        """
        if not self._is_running or not self._bot:
            self.signals.log_received.emit("ERROR", "Bot is not running")
            return False
        
        if not self._is_connected:
            self.signals.log_received.emit("ERROR", "Bot is not connected")
            return False
        
        # Validate action_id
        valid_actions = [
            "delete_channels", "delete_roles", "ban_all", "nuke_server",
            "delete_emojis", "delete_stickers", "rename_server", "kick_all"
        ]
        if action_id not in valid_actions:
            self.signals.log_received.emit("ERROR", f"Invalid action: {action_id}")
            return False
        
        # Schedule the action in the bot's event loop
        try:
            if self._worker and self._worker._loop:
                import asyncio
                asyncio.run_coroutine_threadsafe(
                    self._execute_nuke_action_async(action_id, guild_id),
                    self._worker._loop
                )
                self.signals.log_received.emit("INFO", f"Nuke action queued: {action_id} for guild {guild_id}")
                self.signals.status_changed.emit(f"Executing: {action_id}...")
                return True
            else:
                self.signals.log_received.emit("ERROR", "Bot event loop not available")
                return False
        except Exception as e:
            self.signals.log_received.emit("ERROR", f"Failed to queue nuke action: {e}")
            return False
    
    async def _execute_nuke_action_async(self, action_id: str, guild_id: int) -> None:
        """Async implementation of nuke actions."""
        try:
            # Ensure guild_id is an integer
            try:
                guild_id = int(guild_id)
            except (ValueError, TypeError) as e:
                error_msg = f"Invalid guild ID format: {guild_id} ({e})"
                self.signals.log_received.emit("ERROR", error_msg)
                self.signals.status_changed.emit("Error: Invalid guild ID")
                self.signals.nuke_action_completed.emit(action_id, False, error_msg)
                return

            # Get the guild from cache first
            guild = self._bot.get_guild(guild_id)
            
            # If not in cache, try to find it in the raw guilds list
            if not guild and self._bot.guilds:
                for g in self._bot.guilds:
                    if g.id == guild_id:
                        guild = g
                        break
            
            # If still not found, try to fetch from API
            if not guild:
                self.signals.log_received.emit("INFO", f"Guild {guild_id} not in cache, fetching from API...")
                try:
                    guild = await self._bot.fetch_guild(guild_id)
                except Exception:
                    pass
            
            if not guild:
                error_msg = f"Guild {guild_id} not found. Bot may not be a member of this guild."
                self.signals.log_received.emit("ERROR", error_msg)
                self.signals.status_changed.emit("Error: Guild not found")
                self.signals.nuke_action_completed.emit(action_id, False, error_msg)
                return
            
            self.signals.log_received.emit("INFO", f"Starting {action_id} on '{guild.name}'")
            
            # Execute based on action type
            if action_id == "delete_channels":
                await self._delete_all_channels(guild)
            elif action_id == "delete_roles":
                await self._delete_all_roles(guild)
            elif action_id == "ban_all":
                await self._ban_all_members(guild)
            elif action_id == "kick_all":
                await self._kick_all_members(guild)
            elif action_id == "delete_emojis":
                await self._delete_all_emojis(guild)
            elif action_id == "delete_stickers":
                await self._delete_all_stickers(guild)
            elif action_id == "rename_server":
                await self._rename_server(guild)
            elif action_id == "nuke_server":
                await self._nuke_server(guild)
            
            self.signals.status_changed.emit(f"Completed: {action_id}")
            self.signals.nuke_action_completed.emit(action_id, True, "Action completed successfully")
            
        except Exception as e:
            error_msg = f"Nuke action failed: {e}"
            self.signals.log_received.emit("ERROR", error_msg)
            self.signals.status_changed.emit(f"Error: {action_id}")
            self.signals.nuke_action_completed.emit(action_id, False, str(e))
    
    async def _delete_all_channels(self, guild) -> None:
        """Delete all channels in a guild."""
        channels = list(guild.channels)
        self.signals.log_received.emit("INFO", f"Deleting {len(channels)} channels...")
        
        deleted = 0
        failed = 0
        for channel in channels:
            try:
                await channel.delete()
                deleted += 1
                await asyncio.sleep(0.5)  # Rate limit protection
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to delete channel: {e}")
        
        self.signals.log_received.emit("INFO", f"Channels deleted: {deleted}, failed: {failed}")
    
    async def _delete_all_roles(self, guild) -> None:
        """Delete all roles except @everyone."""
        roles = [role for role in guild.roles if not role.is_default()]
        self.signals.log_received.emit("INFO", f"Deleting {len(roles)} roles...")
        
        deleted = 0
        failed = 0
        for role in roles:
            try:
                await role.delete()
                deleted += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to delete role: {e}")
        
        self.signals.log_received.emit("INFO", f"Roles deleted: {deleted}, failed: {failed}")
    
    async def _ban_all_members(self, guild) -> None:
        """Ban all members except the bot user."""
        if not self._bot.user:
            return
        
        # Try to fetch members if not cached
        if not guild.members or len(guild.members) < 2:
            self.signals.log_received.emit("INFO", "Fetching members from API...")
            try:
                async for member in guild.fetch_members(limit=None):
                    pass  # Just populate the cache
            except Exception as e:
                self.signals.log_received.emit("WARNING", f"Could not fetch members: {e}")
        
        members = [member for member in guild.members if member.id != self._bot.user.id]
        self.signals.log_received.emit("INFO", f"Banning {len(members)} members...")
        
        banned = 0
        failed = 0
        for member in members:
            try:
                await member.ban(reason="ABUSER Nuke")
                banned += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to ban {member}: {e}")
        
        self.signals.log_received.emit("INFO", f"Members banned: {banned}, failed: {failed}")
    
    async def _kick_all_members(self, guild) -> None:
        """Kick all members except the bot user."""
        if not self._bot.user:
            return
        
        # Try to fetch members if not cached
        if not guild.members or len(guild.members) < 2:
            self.signals.log_received.emit("INFO", "Fetching members from API...")
            try:
                async for member in guild.fetch_members(limit=None):
                    pass  # Just populate the cache
            except Exception as e:
                self.signals.log_received.emit("WARNING", f"Could not fetch members: {e}")
        
        members = [member for member in guild.members if member.id != self._bot.user.id]
        self.signals.log_received.emit("INFO", f"Kicking {len(members)} members...")
        
        kicked = 0
        failed = 0
        for member in members:
            try:
                await member.kick(reason="ABUSER Nuke")
                kicked += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to kick {member}: {e}")
        
        self.signals.log_received.emit("INFO", f"Members kicked: {kicked}, failed: {failed}")
    
    async def _delete_all_emojis(self, guild) -> None:
        """Delete all custom emojis."""
        emojis = list(guild.emojis)
        self.signals.log_received.emit("INFO", f"Deleting {len(emojis)} emojis...")
        
        deleted = 0
        failed = 0
        for emoji in emojis:
            try:
                await emoji.delete()
                deleted += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to delete emoji: {e}")
        
        self.signals.log_received.emit("INFO", f"Emojis deleted: {deleted}, failed: {failed}")
    
    async def _delete_all_stickers(self, guild) -> None:
        """Delete all custom stickers."""
        stickers = list(guild.stickers)
        self.signals.log_received.emit("INFO", f"Deleting {len(stickers)} stickers...")
        
        deleted = 0
        failed = 0
        for sticker in stickers:
            try:
                await sticker.delete()
                deleted += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to delete sticker: {e}")
        
        self.signals.log_received.emit("INFO", f"Stickers deleted: {deleted}, failed: {failed}")
    
    async def _rename_server(self, guild) -> None:
        """Rename the server to a random destructive name."""
        import random
        names = ["NUKED", "DESTROYED", "ABUSED", "RAIDED", "WASTED"]
        new_name = f"{random.choice(names)}-{random.randint(1000, 9999)}"
        
        try:
            await guild.edit(name=new_name)
            self.signals.log_received.emit("INFO", f"Server renamed to: {new_name}")
        except Exception as e:
            self.signals.log_received.emit("ERROR", f"Failed to rename server: {e}")
    
    async def _nuke_server(self, guild) -> None:
        """Execute all destructive actions."""
        self.signals.log_received.emit("INFO", "=== STARTING SERVER NUKE ===")
        
        # Execute all actions in sequence
        await self._delete_all_channels(guild)
        await self._delete_all_roles(guild)
        await self._delete_all_emojis(guild)
        await self._delete_all_stickers(guild)
        await self._ban_all_members(guild)
        await self._rename_server(guild)
        
        self.signals.log_received.emit("INFO", "=== SERVER NUKE COMPLETED ===")
    
    def execute_setup_server(self, guild_id: int, server_name: str = "Test Server", roles_count: int = 5, channels_count: int = 5) -> bool:
        """
        Execute setup server action to create test roles, channels, and emojis.
        
        Args:
            guild_id: The target guild ID
            server_name: New name for the server
            roles_count: Number of roles to create
            channels_count: Number of channels to create
        
        Returns:
            True if action was queued successfully
        """
        if not self._is_running or not self._bot:
            self.signals.log_received.emit("ERROR", "Bot is not running")
            return False
        
        if not self._is_connected:
            self.signals.log_received.emit("ERROR", "Bot is not connected")
            return False
        
        # Schedule the action in the bot's event loop
        try:
            if self._worker and self._worker._loop:
                import asyncio
                asyncio.run_coroutine_threadsafe(
                    self._execute_setup_server_async(guild_id, server_name, roles_count, channels_count),
                    self._worker._loop
                )
                self.signals.log_received.emit("INFO", f"Setup server queued for guild {guild_id}")
                self.signals.status_changed.emit("Setting up test server...")
                return True
            else:
                self.signals.log_received.emit("ERROR", "Bot event loop not available")
                return False
        except Exception as e:
            self.signals.log_received.emit("ERROR", f"Failed to queue setup server: {e}")
            return False
    
    async def _execute_setup_server_async(self, guild_id: int, server_name: str, roles_count: int, channels_count: int) -> None:
        """Async implementation of setup server action."""
        try:
            # Ensure guild_id is an integer
            try:
                guild_id = int(guild_id)
            except (ValueError, TypeError) as e:
                error_msg = f"Invalid guild ID format: {guild_id} ({e})"
                self.signals.log_received.emit("ERROR", error_msg)
                self.signals.status_changed.emit("Error: Invalid guild ID")
                self.signals.setup_server_completed.emit(False, error_msg)
                return

            # Get the guild from cache first
            guild = self._bot.get_guild(guild_id)
            
            # If not in cache, try to find it in the raw guilds list
            if not guild and self._bot.guilds:
                for g in self._bot.guilds:
                    if g.id == guild_id:
                        guild = g
                        break
            
            # If still not found, try to fetch from API
            if not guild:
                self.signals.log_received.emit("INFO", f"Guild {guild_id} not in cache, fetching from API...")
                try:
                    guild = await self._bot.fetch_guild(guild_id)
                except Exception as fetch_error:
                    self.signals.log_received.emit("WARNING", f"Failed to fetch guild: {fetch_error}")
            
            if not guild:
                error_msg = f"Guild {guild_id} not found. Bot may not be a member of this guild."
                self.signals.log_received.emit("ERROR", error_msg)
                self.signals.status_changed.emit("Error: Guild not found")
                self.signals.setup_server_completed.emit(False, error_msg)
                return
            
            self.signals.log_received.emit("INFO", f"Starting server setup on '{guild.name}'")
            self.signals.status_changed.emit(f"Setting up test server: {guild.name}")
            
            # Rename server first
            try:
                await guild.edit(name=server_name)
                self.signals.log_received.emit("INFO", f"Server renamed to: {server_name}")
            except Exception as e:
                self.signals.log_received.emit("WARNING", f"Failed to rename server: {e}")
            
            # Create test roles
            created_roles = await self._create_test_roles(guild, roles_count)
            
            # Create test channels
            created_channels = await self._create_test_channels(guild, channels_count)
            
            # Create test emojis
            created_emojis = await self._create_test_emojis(guild)
            
            # Report success
            success_msg = (
                f"Server setup completed: {created_roles} roles, "
                f"{created_channels} channels, {created_emojis} emojis created"
            )
            self.signals.log_received.emit("INFO", success_msg)
            self.signals.status_changed.emit("Server setup completed")
            self.signals.setup_server_completed.emit(True, success_msg)
            
        except Exception as e:
            error_msg = f"Setup server failed: {e}"
            self.signals.log_received.emit("ERROR", error_msg)
            self.signals.status_changed.emit("Error: Setup server failed")
            self.signals.setup_server_completed.emit(False, str(e))
    
    async def _create_test_roles(self, guild, count: int = 5) -> int:
        """Create test roles in the guild."""
        self.signals.log_received.emit("INFO", f"Creating {count} test roles...")
        created = 0
        failed = 0
        
        for i in range(1, count + 1):
            role_name = f"Test Role {i}"  # Moved outside try block
            try:
                await guild.create_role(name=role_name)
                created += 1
                self.signals.log_received.emit("INFO", f"Created role: {role_name}")
                await asyncio.sleep(0.5)  # Rate limit protection
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to create role '{role_name}': {e}")
        
        self.signals.log_received.emit("INFO", f"Roles created: {created}, failed: {failed}")
        return created
    
    async def _create_test_channels(self, guild, count: int = 5) -> int:
        """Create text channels in the guild."""
        self.signals.log_received.emit("INFO", f"Creating {count} test channels...")
        created = 0
        failed = 0
        
        for i in range(1, count + 1):
            channel_name = f"test-channel-{i}"  # Moved outside try block
            try:
                await guild.create_text_channel(channel_name)
                created += 1
                self.signals.log_received.emit("INFO", f"Created channel: {channel_name}")
                await asyncio.sleep(0.5)  # Rate limit protection
            except Exception as e:
                failed += 1
                self.signals.log_received.emit("WARNING", f"Failed to create channel '{channel_name}': {e}")
        
        self.signals.log_received.emit("INFO", f"Channels created: {created}, failed: {failed}")
        return created
    
    async def _create_test_emojis(self, guild) -> int:
        """Create 3 test emojis in the guild (if bot has permissions)."""
        self.signals.log_received.emit("INFO", "Creating 3 test emojis...")
        created = 0
        failed = 0
        
        # Simple colored square images as base64 (1x1 pixel PNGs)
        # These are minimal valid PNG files for different colors
        test_emojis = [
            ("test_red", "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="),
            ("test_green", "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAEBgIApD5fRAAAAABJRU5ErkJggg=="),
            ("test_blue", "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwEA60Hg6gAAAABJRU5ErkJggg=="),
        ]
        
        for emoji_name, image_data in test_emojis:
            try:
                # Extract base64 data
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                
                import base64
                image_bytes = base64.b64decode(image_data)
                
                await guild.create_custom_emoji(name=emoji_name, image=image_bytes)
                created += 1
                self.signals.log_received.emit("INFO", f"Created emoji: :{emoji_name}:")
                await asyncio.sleep(0.5)  # Rate limit protection
            except Exception as e:
                failed += 1
                # Check if it's a permission error
                if "permission" in str(e).lower() or "forbidden" in str(e).lower():
                    self.signals.log_received.emit("WARNING", f"Cannot create emoji '{emoji_name}': Insufficient permissions")
                else:
                    self.signals.log_received.emit("WARNING", f"Failed to create emoji '{emoji_name}': {e}")
        
        self.signals.log_received.emit("INFO", f"Emojis created: {created}, failed: {failed}")
        return created
    
    def refresh_guilds(self) -> bool:
        """
        Manually refresh the guild list.
        
        Returns:
            True if refresh was initiated
        """
        if not self._is_running or not self._worker:
            return False
        
        # Trigger guild update
        self._worker._update_guilds()
        return True
    
    def _setup_log_forwarding(self):
        """Set up log forwarding from bot to GUI"""
        if not self._bot:
            return
        
        # Create and add GUI log handler
        if self._gui_handler is None:
            self._gui_handler = GUILogHandler(self.signals)
            self._gui_handler.setLevel(logging.INFO)
        
        # Add to bot's logger and root logger
        if self._gui_handler not in self._bot.logger.handlers:
            self._bot.logger.addHandler(self._gui_handler)
        
        # Also capture discord.py logs
        discord_logger = logging.getLogger('discord')
        if self._gui_handler not in discord_logger.handlers:
            discord_logger.addHandler(self._gui_handler)
        
        # Set up rate limit status updates
        self._start_rate_limit_updates()
    
    def _on_bot_ready(self, user_name: str, user_id: str, guild_count: int):
        """Internal handler for bot ready signal"""
        self._user_name = user_name
        self._user_id = user_id
    
    def _on_bot_disconnected(self):
        """Internal handler for bot disconnected signal"""
        self._is_connected = False
        self._user_name = None
        self._user_id = None
        self._latency_ms = None
        self._latency_timer.stop()
        if hasattr(self, '_rate_limit_timer'):
            self._rate_limit_timer.stop()
    
    def _on_guilds_updated(self, guild_list: List[Dict[str, Any]]):
        """Internal handler for guilds updated signal"""
        self._guilds = guild_list
    
    def _on_connection_changed(self, is_connected: bool):
        """Internal handler for connection state changes"""
        self._is_connected = is_connected
        if is_connected:
            self._latency_timer.start()
            self._emit_latency_update()
        else:
            self._latency_timer.stop()
            if hasattr(self, '_rate_limit_timer'):
                self._rate_limit_timer.stop()
    
    def _start_rate_limit_updates(self):
        """Start periodic rate limit status updates"""
        self._rate_limit_timer = QTimer(self)
        self._rate_limit_timer.setInterval(2000)
        self._rate_limit_timer.timeout.connect(self._update_rate_limit_status)
        self._rate_limit_timer.start()
    
    def _update_rate_limit_status(self):
        """Update and emit rate limit status"""
        if not self._bot or not hasattr(self._bot, 'rate_limiter') or not self._bot.rate_limiter:
            return
        
        try:
            status = self._bot.rate_limiter.get_status()
            
            # Check for warnings
            if status.get('rate_limited_requests', 0) > self._last_rate_limit_warning + 5:
                self._last_rate_limit_warning = status.get('rate_limited_requests', 0)
                self.signals.rate_limit_warning.emit(
                    f"Rate limit hit! Total limited: {self._last_rate_limit_warning}"
                )
            
            self._rate_limit_status = status
            self.signals.rate_limit_status_changed.emit(status)
        except Exception:
            pass
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return self._rate_limit_status.copy()
    
    def is_rate_limit_enabled(self) -> bool:
        """Check if rate limiting is enabled"""
        if not self._bot:
            return False
        return getattr(self._bot, '_rate_limit_enabled', False)

    def _emit_latency_update(self):
        """Emit the current bot latency to the GUI when available."""
        if not self._bot or not self._is_running:
            return
        try:
            latency = getattr(self._bot, "latency", None)
            if latency is None:
                return
            self._latency_ms = float(latency) * 1000
            self.signals.latency_updated.emit(self._latency_ms)
        except Exception:
            pass


# Convenience function to create a BotRunner instance
def create_bot_runner(parent=None) -> BotRunner:
    """
    Create a new BotRunner instance.
    
    Args:
        parent: Optional parent QObject
    
    Returns:
        Configured BotRunner instance
    """
    return BotRunner(parent)
