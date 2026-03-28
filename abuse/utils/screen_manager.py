"""
Screen management utilities for ABUSER bot
Handles terminal clearing and banner/stats display
"""

import sys
import shutil
from io import StringIO
from datetime import datetime
from typing import List, Optional

from colorama import Fore, Style


class ScreenManager:
    """
    Manages terminal display with fixed banner/stats at top
    and scrolling log output below
    """
    
    def __init__(self):
        self.banner_lines: int = 0
        self.stats_lines: int = 0
        self.log_buffer: List[str] = []
        self.max_logs: int = 100
        self.terminal_height: int = 0
        self._update_terminal_size()
        
    def _update_terminal_size(self):
        """Get current terminal dimensions"""
        try:
            self.terminal_height = shutil.get_terminal_size().lines
        except:
            self.terminal_height = 24  # default fallback
            
    def _clear_screen(self):
        """Clear the terminal screen"""
        # ANSI escape codes to clear screen and move cursor to top
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()
        
    def _move_cursor_to_top(self):
        """Move cursor to top of screen"""
        sys.stdout.write('\033[H')
        sys.stdout.flush()
        
    def _clear_from_cursor_down(self):
        """Clear screen from cursor position down"""
        sys.stdout.write('\033[J')
        sys.stdout.flush()
        
    def render_banner(self, banner_text: str):
        """
        Render the banner and store its line count
        """
        lines = banner_text.count('\n') + 1
        self.banner_lines = lines
        print(banner_text, end='')
        
    def render_stats(self, stats_text: str):
        """
        Render the stats panel and store its line count
        """
        lines = stats_text.count('\n') + 1
        self.stats_lines = lines
        print(stats_text, end='')
        
    def add_log(self, log_line: str):
        """
        Add a log line and refresh the display
        """
        # Add to buffer
        self.log_buffer.append(log_line)
        
        # Trim buffer if too large
        if len(self.log_buffer) > self.max_logs:
            self.log_buffer.pop(0)
            
        # Update terminal size
        self._update_terminal_size()
        
        # Calculate available space for logs
        header_lines = self.banner_lines + self.stats_lines
        available_log_lines = max(1, self.terminal_height - header_lines - 2)
        
        # Get recent logs that fit in available space
        recent_logs = self.log_buffer[-available_log_lines:]
        
        # Clear and redraw
        self._clear_screen()
        
        # Print banner at top
        # We need to re-render the banner and stats
        # This is done by the bot calling refresh_display()
        
    def refresh_display(self, banner_func, stats_func, logs: List[str]):
        """
        Full refresh of the display
        
        Args:
            banner_func: Function that prints the banner
            stats_func: Function that prints the stats
            logs: List of log lines to display
        """
        self._update_terminal_size()
        self._clear_screen()
        
        # Calculate header size
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        banner_func()
        banner_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        stats_func()
        stats_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        self.banner_lines = banner_output.count('\n')
        self.stats_lines = stats_output.count('\n')
        
        # Print banner and stats
        print(banner_output, end='')
        print(stats_output, end='')
        
        # Calculate available space for logs
        header_lines = self.banner_lines + self.stats_lines
        available_log_lines = max(1, self.terminal_height - header_lines - 2)
        
        # Print recent logs
        recent_logs = logs[-available_log_lines:]
        for log in recent_logs:
            print(log)
            
    def get_log_count(self) -> int:
        """Get current number of buffered log lines"""
        return len(self.log_buffer)


# Global screen manager instance
_screen_manager: Optional[ScreenManager] = None


def get_screen_manager() -> ScreenManager:
    """Get or create the global screen manager"""
    global _screen_manager
    if _screen_manager is None:
        _screen_manager = ScreenManager()
    return _screen_manager


def reset_screen_manager():
    """Reset the global screen manager"""
    global _screen_manager
    _screen_manager = None
