"""
Color definitions for console output
Uses colorama for cross-platform colored terminal output
"""

from colorama import Fore, Back, Style


class Colors:
    """Color constants for consistent theming"""
    
    # Primary colors
    PRIMARY = Fore.CYAN
    SUCCESS = Fore.GREEN
    ERROR = Fore.RED
    WARNING = Fore.YELLOW
    INFO = Fore.LIGHTBLUE_EX
    
    # Secondary colors
    HEADER = Fore.MAGENTA
    MUTED = Fore.LIGHTBLACK_EX
    HIGHLIGHT = Fore.LIGHTYELLOW_EX
    ACCENT = Fore.LIGHTGREEN_EX
    WHITE = Fore.LIGHTWHITE_EX
    
    # Background colors (for special highlighting)
    BG_SUCCESS = Back.GREEN
    BG_ERROR = Back.RED
    BG_WARNING = Back.YELLOW
    BG_INFO = Back.BLUE
    
    # Styles
    BRIGHT = Style.BRIGHT
    DIM = Style.DIM
    RESET = Style.RESET_ALL
    
    # Aliases for common use cases
    GREEN = SUCCESS
    RED = ERROR
    YELLOW = WARNING
    CYAN = PRIMARY
    BLUE = INFO
    MAGENTA = HEADER


def colorize(text: str, color: str) -> str:
    """
    Wrap text in color codes
    
    Args:
        text: Text to colorize
        color: Color from Colors class
        
    Returns:
        Colorized string
    """
    return f"{color}{text}{Style.RESET_ALL}"


def success(text: str) -> str:
    """Return green success text"""
    return colorize(text, Colors.SUCCESS)


def error(text: str) -> str:
    """Return red error text"""
    return colorize(text, Colors.ERROR)


def warning(text: str) -> str:
    """Return yellow warning text"""
    return colorize(text, Colors.WARNING)


def info(text: str) -> str:
    """Return cyan info text"""
    return colorize(text, Colors.INFO)
