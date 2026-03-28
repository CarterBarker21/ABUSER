"""
PyQt6 Theme System for ABUSER Bot GUI

Provides a complete theme system with multiple preset themes,
configurable accent colors, and QSS generation.

Available Themes:
- Midnight (very dark - current but darker)
- Obsidian (pure black/dark gray)
- Discord Dark (classic Discord)
- Catppuccin Mocha (popular dark theme)
- Dracula (purple-tinted dark)
- Nord (arctic bluish dark)
- Light (clean white)
- GitHub Light (professional light)
- Solarized Light
- Cyberpunk (neon accents on dark)
- Sunset (warm oranges/reds)
- Forest (green tones)
"""

import json
import os
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, Optional, Union, Callable, List
from pathlib import Path

from abuse.app_paths import migrate_legacy_layout, theme_config_path as shared_theme_config_path

class AccentColor(Enum):
    """Available accent colors for the theme."""
    DISCORD_BLUE = ("#5865F2", "#4752C4")
    RED = ("#ED4245", "#C03537")
    GREEN = ("#57F287", "#3BA55D")
    PURPLE = ("#9B59B6", "#8E44AD")
    ORANGE = ("#E67E22", "#D35400")
    PINK = ("#EB459E", "#C73E87")
    CYAN = ("#00D4AA", "#00A884")
    YELLOW = ("#FAA81A", "#D7940F")
    
    def __init__(self, primary: str, hover: str):
        self.primary = primary
        self.hover = hover
    
    @classmethod
    def from_string(cls, name: str) -> "AccentColor":
        """Get accent color from string name."""
        color_map = {
            "discord_blue": cls.DISCORD_BLUE,
            "red": cls.RED,
            "green": cls.GREEN,
            "purple": cls.PURPLE,
            "orange": cls.ORANGE,
            "pink": cls.PINK,
            "cyan": cls.CYAN,
            "yellow": cls.YELLOW,
        }
        return color_map.get(name.lower(), cls.DISCORD_BLUE)


@dataclass
class Theme:
    """
    Complete theme configuration with color definitions.
    
    Attributes:
        name: Theme name identifier
        accent: AccentColor enum value
        bg_primary: Main background (deepest)
        bg_secondary: Secondary/elevated background
        bg_tertiary: Tertiary/deeper background
        bg_card: Card backgrounds
        surface: Surface/card color
        surface_hover: Hover states
        text_primary: Primary text color
        text_secondary: Secondary/muted text color
        text_disabled: Disabled text color
        text_muted: Very muted text
        border: Border color
        border_light: Light borders
        divider: Dividers
        accent_primary: Primary accent color (auto from accent)
        accent_hover: Accent hover color (auto from accent)
        success: Success state color
        success_hover: Success hover state
        warning: Warning state color
        warning_hover: Warning hover state
        error: Error state color
        error_hover: Error hover state
        info: Info state color
        info_hover: Info hover state
    """
    name: str = "dark"
    accent: AccentColor = AccentColor.DISCORD_BLUE
    
    # Background colors
    bg_primary: str = "#1E1F22"      # Deepest background
    bg_secondary: str = "#2B2D31"    # Main background
    bg_tertiary: str = "#313338"     # Elevated surfaces
    bg_card: str = "#252729"         # Card backgrounds
    surface: str = "#383A40"         # Cards, inputs
    surface_hover: str = "#404249"   # Hover states
    
    # Text colors
    text_primary: str = "#F2F3F5"    # Primary text
    text_secondary: str = "#B5BAC1"  # Secondary text
    text_disabled: str = "#6D6F78"   # Disabled text
    text_muted: str = "#949BA4"      # Muted text
    
    # UI colors
    border: str = "#1E1F22"          # Borders
    border_light: str = "#3F4147"    # Light borders
    divider: str = "#2E3035"         # Dividers
    
    # State colors
    success: str = "#248046"
    success_hover: str = "#1A6334"
    warning: str = "#FAA81A"
    warning_hover: str = "#D7940F"
    error: str = "#ED4245"
    error_hover: str = "#C03537"
    info: str = "#00A8FC"
    info_hover: str = "#0084C9"
    
    # Extra colors for specific widgets
    card_bg: str = "#252729"
    card_border: str = "#3A3D44"
    input_bg: str = "#1E1F22"
    log_bg: str = "#0E0F12"
    success_bright: str = "#57F287"
    
    def __post_init__(self):
        """Ensure accent is an AccentColor enum."""
        if isinstance(self.accent, str):
            self.accent = AccentColor.from_string(self.accent)
    
    @property
    def accent_primary(self) -> str:
        """Get primary accent color."""
        return self.accent.primary
    
    @property
    def accent_hover(self) -> str:
        """Get accent hover color."""
        return self.accent.hover
    
    def to_dict(self) -> Dict:
        """Convert theme to dictionary."""
        data = asdict(self)
        data['accent'] = self.accent.name.lower()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Theme":
        """Create theme from dictionary."""
        accent_val = data.pop('accent', 'discord_blue')
        # Handle both string and AccentColor objects
        if isinstance(accent_val, AccentColor):
            accent = accent_val
        else:
            accent = AccentColor.from_string(accent_val)
        return cls(accent=accent, **data)
    
    def copy(self) -> "Theme":
        """Create a copy of this theme."""
        return Theme.from_dict(self.to_dict())


@dataclass(frozen=True)
class LayoutTokens:
    """Shared spacing and sizing tokens for the desktop UI."""

    spacing_xs: int = 8
    spacing_sm: int = 12
    spacing_md: int = 16
    spacing_lg: int = 24
    spacing_xl: int = 32
    control_height_sm: int = 32
    control_height_md: int = 40
    control_height_lg: int = 48
    card_radius: int = 12
    sidebar_width: int = 216
    content_max_width: int = 1180


@dataclass(frozen=True)
class ThemeTokens:
    """Typed access to theme colors plus shared layout metrics."""

    colors: Theme
    metrics: LayoutTokens = field(default_factory=LayoutTokens)

    @property
    def accent(self) -> str:
        return self.colors.accent_primary

    @property
    def accent_hover(self) -> str:
        return self.colors.accent_hover

    @property
    def surface(self) -> str:
        return self.colors.surface

    @property
    def card(self) -> str:
        return self.colors.card_bg

    @property
    def input(self) -> str:
        return self.colors.input_bg


# ============================================
# Design Tokens — semantic color aliases
# ============================================

def _rgba(hex_color: str, alpha: float) -> str:
    """Inline rgba helper (avoids circular import with components.py)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha:.3f})"


@dataclass(frozen=True)
class DesignTokens:
    """Semantic color tokens — the single source of truth for all UI color styling.

    Every component and page must read colors exclusively from this dataclass.
    No widget may reference raw hex literals or ``Theme`` fields directly.
    """

    # Layer colors
    background: str       # Deepest app background
    surface: str          # Cards, panels, sidebar
    surface_raised: str   # Inputs, hover states
    # Borders
    border: str           # Subtle dividers / outlines
    border_strong: str    # Focused inputs, active states
    # Text hierarchy
    text_primary: str     # Main readable text
    text_secondary: str   # Descriptions, secondary info
    text_muted: str       # Section labels, very muted
    text_disabled: str    # Inactive / placeholder
    # Accent (overridden by accent picker)
    accent: str           # Brand / action color
    accent_hover: str     # Accent on hover
    accent_muted: str     # Accent at ~15 % opacity (backgrounds)
    # Semantic states
    danger: str           # Destructive actions
    danger_hover: str     # Danger on hover
    success: str          # Confirmed / connected
    success_bright: str   # Bright success for chips and icons
    warning: str          # Caution states


def make_design_tokens(theme: Theme) -> DesignTokens:
    """Build a :class:`DesignTokens` instance from the active ``Theme``."""
    return DesignTokens(
        background=theme.bg_primary,
        surface=theme.surface,
        surface_raised=theme.surface_hover,
        border=theme.border,
        border_strong=theme.border_light,
        text_primary=theme.text_primary,
        text_secondary=theme.text_secondary,
        text_muted=theme.text_muted,
        text_disabled=theme.text_disabled,
        accent=theme.accent_primary,
        accent_hover=theme.accent_hover,
        accent_muted=_rgba(theme.accent_primary, 0.15),
        danger=theme.error,
        danger_hover=theme.error_hover,
        success=theme.success,
        success_bright=theme.success_bright,
        warning=theme.warning,
    )


# ============================================
# Theme Presets
# ============================================

THEME_PRESETS: Dict[str, Dict] = {
    # ============================================
    # Dark Themes
    # ============================================
    
    "Midnight": {
        "name": "Midnight",
        "bg_primary": "#09090B",
        "bg_secondary": "#18181B",
        "bg_tertiary": "#27272A",
        "bg_card": "#18181B",
        "surface": "#27272A",
        "surface_hover": "#3F3F46",
        "text_primary": "#FAFAFA",
        "text_secondary": "#A1A1AA",
        "text_disabled": "#52525B",
        "text_muted": "#71717A",
        "border": "#27272A",
        "border_light": "#3F3F46",
        "divider": "#27272A",
        "accent": "discord_blue",
        "success": "#22C55E",
        "success_hover": "#16A34A",
        "success_bright": "#4ADE80",
        "warning": "#F59E0B",
        "warning_hover": "#D97706",
        "error": "#EF4444",
        "error_hover": "#DC2626",
        "info": "#3B82F6",
        "info_hover": "#2563EB",
        "card_bg": "#18181B",
        "card_border": "#27272A",
        "input_bg": "#09090B",
        "log_bg": "#000000",
    },
    
    "Obsidian": {
        "name": "Obsidian",
        "bg_primary": "#000000",
        "bg_secondary": "#0A0A0A",
        "bg_tertiary": "#141414",
        "bg_card": "#0A0A0A",
        "surface": "#141414",
        "surface_hover": "#1F1F1F",
        "text_primary": "#FFFFFF",
        "text_secondary": "#A1A1AA",
        "text_disabled": "#52525B",
        "text_muted": "#71717A",
        "border": "#1F1F1F",
        "border_light": "#27272A",
        "divider": "#1F1F1F",
        "accent": "discord_blue",
        "success": "#22C55E",
        "success_hover": "#16A34A",
        "success_bright": "#4ADE80",
        "warning": "#F59E0B",
        "warning_hover": "#D97706",
        "error": "#EF4444",
        "error_hover": "#DC2626",
        "info": "#3B82F6",
        "info_hover": "#2563EB",
        "card_bg": "#0A0A0A",
        "card_border": "#1F1F1F",
        "input_bg": "#000000",
        "log_bg": "#000000",
    },
    
    "Discord Dark": {
        "name": "Discord Dark",
        "bg_primary": "#111214",
        "bg_secondary": "#1E1F22",
        "bg_tertiary": "#2B2D31",
        "bg_card": "#2B2D31",
        "surface": "#313338",
        "surface_hover": "#383A40",
        "text_primary": "#DBDEE1",
        "text_secondary": "#B5BAC1",
        "text_disabled": "#5C5E66",
        "text_muted": "#80848E",
        "border": "#1E1F22",
        "border_light": "#313338",
        "divider": "#2B2D31",
        "accent": "discord_blue",
        "success": "#23A559",
        "success_hover": "#1D8749",
        "success_bright": "#23A559",
        "warning": "#FEE75C",
        "warning_hover": "#E3CE53",
        "error": "#DA373C",
        "error_hover": "#C23135",
        "info": "#00A8FC",
        "info_hover": "#0084C9",
        "card_bg": "#2B2D31",
        "card_border": "#1E1F22",
        "input_bg": "#1E1F22",
        "log_bg": "#111214",
    },
    
    "Catppuccin Mocha": {
        "name": "Catppuccin Mocha",
        "bg_primary": "#1E1E2E",
        "bg_secondary": "#252537",
        "bg_tertiary": "#2D2D44",
        "bg_card": "#28283E",
        "surface": "#363654",
        "surface_hover": "#414164",
        "text_primary": "#CDD6F4",
        "text_secondary": "#A6ADC8",
        "text_disabled": "#585B70",
        "text_muted": "#6C7086",
        "border": "#313244",
        "border_light": "#45475A",
        "divider": "#313244",
        "accent": "pink",
        "success": "#A6E3A1",
        "success_hover": "#8BE08A",
        "success_bright": "#94E2D5",
        "warning": "#F9E2AF",
        "warning_hover": "#F5D89A",
        "error": "#F38BA8",
        "error_hover": "#EB7A9A",
        "info": "#89B4FA",
        "info_hover": "#74A0F0",
        "card_bg": "#28283E",
        "card_border": "#45475A",
        "input_bg": "#1E1E2E",
        "log_bg": "#11111B",
    },
    
    "Dracula": {
        "name": "Dracula",
        "bg_primary": "#282A36",
        "bg_secondary": "#313442",
        "bg_tertiary": "#3B3D4D",
        "bg_card": "#35374A",
        "surface": "#44475A",
        "surface_hover": "#4D5066",
        "text_primary": "#F8F8F2",
        "text_secondary": "#BFBFBF",
        "text_disabled": "#6272A4",
        "text_muted": "#8BE9FD",
        "border": "#44475A",
        "border_light": "#6272A4",
        "divider": "#44475A",
        "accent": "purple",
        "success": "#50FA7B",
        "success_hover": "#3AE868",
        "success_bright": "#50FA7B",
        "warning": "#F1FA8C",
        "warning_hover": "#E5F56F",
        "error": "#FF5555",
        "error_hover": "#FF3838",
        "info": "#8BE9FD",
        "info_hover": "#6FE2FA",
        "card_bg": "#35374A",
        "card_border": "#44475A",
        "input_bg": "#282A36",
        "log_bg": "#1E1F29",
    },
    
    "Nord": {
        "name": "Nord",
        "bg_primary": "#2E3440",
        "bg_secondary": "#3B4252",
        "bg_tertiary": "#434C5E",
        "bg_card": "#3A4250",
        "surface": "#4C566A",
        "surface_hover": "#56667A",
        "text_primary": "#ECEFF4",
        "text_secondary": "#D8DEE9",
        "text_disabled": "#4C566A",
        "text_muted": "#81A1C1",
        "border": "#434C5E",
        "border_light": "#5E81AC",
        "divider": "#434C5E",
        "accent": "cyan",
        "success": "#A3BE8C",
        "success_hover": "#8FBF6E",
        "success_bright": "#A3BE8C",
        "warning": "#EBCB8B",
        "warning_hover": "#E5C070",
        "error": "#BF616A",
        "error_hover": "#B04F59",
        "info": "#81A1C1",
        "info_hover": "#6E94B8",
        "card_bg": "#3A4250",
        "card_border": "#434C5E",
        "input_bg": "#2E3440",
        "log_bg": "#242933",
    },
    
    "Cyberpunk": {
        "name": "Cyberpunk",
        "bg_primary": "#0D0D1A",
        "bg_secondary": "#141428",
        "bg_tertiary": "#1E1E3C",
        "bg_card": "#181830",
        "surface": "#2A2A50",
        "surface_hover": "#36366A",
        "text_primary": "#F0F0FF",
        "text_secondary": "#B8B8D9",
        "text_disabled": "#50507A",
        "text_muted": "#8080B3",
        "border": "#2A2A50",
        "border_light": "#00FFFF",
        "divider": "#1A1A3D",
        "accent": "cyan",
        "success": "#00FF9F",
        "success_hover": "#00E68F",
        "success_bright": "#00FF9F",
        "warning": "#FFD700",
        "warning_hover": "#E6C200",
        "error": "#FF0055",
        "error_hover": "#E6004C",
        "info": "#00FFFF",
        "info_hover": "#00E6E6",
        "card_bg": "#181830",
        "card_border": "#00FFFF",
        "input_bg": "#0D0D1A",
        "log_bg": "#080814",
    },
    
    # ============================================
    # Light Themes
    # ============================================
    
    "Light": {
        "name": "Light",
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F7F7F7",
        "bg_tertiary": "#F0F0F0",
        "bg_card": "#FAFAFA",
        "surface": "#E8E8E8",
        "surface_hover": "#E0E0E0",
        "text_primary": "#1A1A1A",
        "text_secondary": "#555555",
        "text_disabled": "#AAAAAA",
        "text_muted": "#888888",
        "border": "#D0D0D0",
        "border_light": "#E0E0E0",
        "divider": "#E5E5E5",
        "accent": "discord_blue",
        "success": "#2E7D32",
        "success_hover": "#1B5E20",
        "success_bright": "#4CAF50",
        "warning": "#ED6C02",
        "warning_hover": "#E65100",
        "error": "#D32F2F",
        "error_hover": "#C62828",
        "info": "#0288D1",
        "info_hover": "#0277BD",
        "card_bg": "#FAFAFA",
        "card_border": "#E0E0E0",
        "input_bg": "#FFFFFF",
        "log_bg": "#F5F5F5",
    },
    
    "GitHub Light": {
        "name": "GitHub Light",
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F6F8FA",
        "bg_tertiary": "#F3F4F6",
        "bg_card": "#FAFBFC",
        "surface": "#EAEEF2",
        "surface_hover": "#DFE4EA",
        "text_primary": "#24292F",
        "text_secondary": "#57606A",
        "text_disabled": "#8C959F",
        "text_muted": "#6E7781",
        "border": "#D0D7DE",
        "border_light": "#E1E4E8",
        "divider": "#D8DEE4",
        "accent": "discord_blue",
        "success": "#1A7F37",
        "success_hover": "#196C2E",
        "success_bright": "#2DA44E",
        "warning": "#9A6700",
        "warning_hover": "#7D4E00",
        "error": "#CF222E",
        "error_hover": "#A40E26",
        "info": "#0969DA",
        "info_hover": "#0550AE",
        "card_bg": "#FAFBFC",
        "card_border": "#D0D7DE",
        "input_bg": "#FFFFFF",
        "log_bg": "#F6F8FA",
    },
    
    "Solarized Light": {
        "name": "Solarized Light",
        "bg_primary": "#FDF6E3",
        "bg_secondary": "#EEE8D5",
        "bg_tertiary": "#E8E0C8",
        "bg_card": "#F5F0E1",
        "surface": "#D3CBB8",
        "surface_hover": "#C5BCA8",
        "text_primary": "#073642",
        "text_secondary": "#586E75",
        "text_disabled": "#93A1A1",
        "text_muted": "#657B83",
        "border": "#D3CBB8",
        "border_light": "#E8E0C8",
        "divider": "#D3CBB8",
        "accent": "cyan",
        "success": "#859900",
        "success_hover": "#6B7B00",
        "success_bright": "#93A1A1",
        "warning": "#B58900",
        "warning_hover": "#9A7600",
        "error": "#DC322F",
        "error_hover": "#C02624",
        "info": "#268BD2",
        "info_hover": "#207AB8",
        "card_bg": "#F5F0E1",
        "card_border": "#D3CBB8",
        "input_bg": "#FDF6E3",
        "log_bg": "#F7F1E4",
    },
    
    # ============================================
    # Specialty Themes
    # ============================================
    
    "Sunset": {
        "name": "Sunset",
        "bg_primary": "#1A1212",
        "bg_secondary": "#251A1A",
        "bg_tertiary": "#322222",
        "bg_card": "#2C1D1D",
        "surface": "#3D2828",
        "surface_hover": "#4A3131",
        "text_primary": "#FFF0E8",
        "text_secondary": "#D4A89A",
        "text_disabled": "#6B4A42",
        "text_muted": "#9E7064",
        "border": "#3D2828",
        "border_light": "#5C4038",
        "divider": "#2A1D1D",
        "accent": "orange",
        "success": "#7CB342",
        "success_hover": "#689F38",
        "success_bright": "#9CCC65",
        "warning": "#FFB74D",
        "warning_hover": "#FFA726",
        "error": "#E57373",
        "error_hover": "#EF5350",
        "info": "#4FC3F7",
        "info_hover": "#29B6F6",
        "card_bg": "#2C1D1D",
        "card_border": "#4A3131",
        "input_bg": "#1A1212",
        "log_bg": "#120D0D",
    },
    
    "Forest": {
        "name": "Forest",
        "bg_primary": "#0D1A0D",
        "bg_secondary": "#142614",
        "bg_tertiary": "#1D331D",
        "bg_card": "#182B18",
        "surface": "#264026",
        "surface_hover": "#335233",
        "text_primary": "#E8F5E8",
        "text_secondary": "#A3C9A3",
        "text_disabled": "#4A6B4A",
        "text_muted": "#6B8F6B",
        "border": "#264026",
        "border_light": "#3D5C3D",
        "divider": "#1D331D",
        "accent": "green",
        "success": "#66BB6A",
        "success_hover": "#4CAF50",
        "success_bright": "#81C784",
        "warning": "#FFCA28",
        "warning_hover": "#FFC107",
        "error": "#EF5350",
        "error_hover": "#E53935",
        "info": "#42A5F5",
        "info_hover": "#2196F3",
        "card_bg": "#182B18",
        "card_border": "#264026",
        "input_bg": "#0D1A0D",
        "log_bg": "#081208",
    },
    
    "Ocean": {
        "name": "Ocean",
        "bg_primary": "#0A1628",
        "bg_secondary": "#0F1E35",
        "bg_tertiary": "#152642",
        "bg_card": "#122238",
        "surface": "#1E3A5F",
        "surface_hover": "#264B7A",
        "text_primary": "#E8F4FC",
        "text_secondary": "#A3C9E8",
        "text_disabled": "#4A6B8F",
        "text_muted": "#6B9AC4",
        "border": "#1E3A5F",
        "border_light": "#2E5A8F",
        "divider": "#152642",
        "accent": "cyan",
        "success": "#4CAF50",
        "success_hover": "#388E3C",
        "success_bright": "#66BB6A",
        "warning": "#FF9800",
        "warning_hover": "#F57C00",
        "error": "#F44336",
        "error_hover": "#D32F2F",
        "info": "#03A9F4",
        "info_hover": "#0288D1",
        "card_bg": "#122238",
        "card_border": "#1E3A5F",
        "input_bg": "#0A1628",
        "log_bg": "#060D18",
    },
}

LIGHT_THEME_PRESETS = {"Light", "GitHub Light", "Solarized Light"}
SPECIAL_THEME_PRESETS = {"Cyberpunk", "Sunset", "Forest", "Ocean"}


def get_theme_family(name: str) -> str:
    """Return the preset family used by settings filtering and routing."""
    if name in LIGHT_THEME_PRESETS:
        return "light"
    if name in SPECIAL_THEME_PRESETS:
        return "special"
    return "dark"


def get_theme_preset(name: str) -> Dict:
    """
    Get a theme preset by name.
    
    Args:
        name: Theme preset name
        
    Returns:
        Theme dictionary (Discord Dark as default if not found)
    """
    return THEME_PRESETS.get(name, THEME_PRESETS["Discord Dark"]).copy()


def get_preset_names() -> List[str]:
    """
    Get list of available theme preset names.
    
    Returns:
        Sorted list of theme names
    """
    return sorted(list(THEME_PRESETS.keys()))


def create_theme_from_preset(name: str, accent: Optional[AccentColor] = None) -> Theme:
    """
    Create a Theme object from a preset.
    
    Args:
        name: Preset theme name
        accent: Optional custom accent color (uses preset default if None)
        
    Returns:
        Theme object configured from preset
    """
    preset = get_theme_preset(name)
    if accent:
        preset['accent'] = accent
    return Theme.from_dict(preset)


class ThemeManager:
    """
    Manages theme application, loading, saving, and runtime switching.
    
    Attributes:
        theme: Current active theme
        config_path: Path to theme configuration file
        _on_theme_changed: Callback for theme change events
    """
    
    # Default QSS template with placeholders
    QSS_TEMPLATE = """
    /* ============================================
       ABUSER Bot GUI - Qt StyleSheet
       Auto-generated from theme configuration
       Theme: %(name)s
       ============================================ */
    
    /* Global Styles */
    QWidget {
        background-color: transparent;
        color: %(text_primary)s;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
        border: none;
    }
    
    /* Clean Text Base - ensures all text elements have transparent backgrounds */
    QLabel, QCheckBox, QRadioButton, QGroupBox::title {
        background-color: transparent;
        border: none;
    }
    
    /* Main Window */
    QMainWindow {
        background-color: %(bg_primary)s;
    }
    
    /* Group Boxes */
    QGroupBox {
        background-color: transparent;
        border: 1px solid %(border)s;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
        padding: 12px;
        font-weight: 600;
        color: %(text_primary)s;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
        color: %(text_secondary)s;
        background-color: %(bg_secondary)s;
        border: none;
    }
    
    /* Buttons */
    QPushButton {
        background-color: %(accent_primary)s;
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 13px;
        min-width: 80px;
    }

    QPushButton:hover {
        background-color: %(accent_hover)s;
    }

    QPushButton:pressed {
        background-color: %(accent_primary)s;
        padding-top: 11px;
        padding-bottom: 9px;
    }

    QPushButton:disabled {
        background-color: %(surface)s;
        color: %(text_disabled)s;
    }

    QPushButton#secondary {
        background-color: %(surface)s;
        color: %(text_primary)s;
        border: 1px solid %(border)s;
        font-weight: 500;
    }

    QPushButton#secondary:hover {
        background-color: %(surface_hover)s;
        border-color: %(border_light)s;
    }

    QPushButton#danger {
        background-color: %(error)s;
    }

    QPushButton#danger:hover {
        background-color: %(error_hover)s;
    }

    QPushButton#success {
        background-color: %(success)s;
    }

    QPushButton#success:hover {
        background-color: %(success_hover)s;
    }

    /* Line Edits */
    QLineEdit {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        padding: 8px 12px;
        color: %(text_primary)s;
        selection-background-color: %(accent_primary)s;
        font-size: 13px;
    }

    QLineEdit:hover {
        border-color: %(border_light)s;
    }

    QLineEdit:focus {
        border: 1px solid %(accent_primary)s;
        background-color: %(bg_primary)s;
    }

    QLineEdit:disabled {
        background-color: %(surface)s;
        color: %(text_disabled)s;
        border-color: %(border)s;
    }
    
    /* Text Edits */
    QTextEdit, QPlainTextEdit {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        padding: 8px;
        color: %(text_primary)s;
        selection-background-color: %(accent_primary)s;
    }
    
    QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid %(accent_primary)s;
    }
    
    /* Combo Boxes */
    QComboBox {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 100px;
        color: %(text_primary)s;
    }
    
    QComboBox:hover {
        border: 1px solid %(border_light)s;
    }
    
    QComboBox:focus {
        border: 1px solid %(accent_primary)s;
    }
    
    QComboBox::drop-down {
        background-color: transparent;
        border: none;
        width: 24px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid %(text_secondary)s;
        background-color: transparent;
    }
    
    QComboBox QAbstractItemView {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        selection-background-color: %(accent_primary)s;
        selection-color: #FFFFFF;
        color: %(text_primary)s;
        padding: 4px;
    }

    QComboBox QAbstractItemView::item {
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
        padding: 6px 8px;
    }
    
    QComboBox QAbstractItemView::item:hover {
        background-color: %(surface)s;
    }
    
    QComboBox QAbstractItemView::item:selected {
        background-color: %(accent_primary)s;
        color: #FFFFFF;
    }
    
    QComboBox::editable {
        background-color: %(bg_primary)s;
    }
    
    QComboBox QAbstractItemView::item:!enabled {
        color: %(text_disabled)s;
    }
    
    /* Spin Boxes */
    QSpinBox, QDoubleSpinBox {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        padding: 10px;
        color: %(text_primary)s;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 2px solid %(accent_primary)s;
    }
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid %(border)s;
        border-top-right-radius: 6px;
    }
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 20px;
        border-left: 1px solid %(border)s;
        border-bottom-right-radius: 6px;
    }
    
    /* Check Boxes */
    QCheckBox {
        spacing: 8px;
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid %(text_secondary)s;
        border-radius: 4px;
        background-color: %(bg_primary)s;
    }
    
    QCheckBox::indicator:checked {
        background-color: %(accent_primary)s;
        border: 2px solid %(accent_primary)s;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
    }
    
    QCheckBox::indicator:hover {
        border: 2px solid %(accent_primary)s;
    }
    
    /* Radio Buttons */
    QRadioButton {
        spacing: 8px;
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
    }
    
    QRadioButton::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid %(text_secondary)s;
        border-radius: 9px;
        background-color: %(bg_primary)s;
    }
    
    QRadioButton::indicator:checked {
        background-color: %(accent_primary)s;
        border: 2px solid %(accent_primary)s;
    }
    
    QRadioButton::indicator::checked::indicator {
        background-color: %(accent_primary)s;
        border: 5px solid %(accent_primary)s;
        border-radius: 9px;
    }
    
    /* Sliders */
    QSlider::groove:horizontal {
        height: 4px;
        background-color: %(surface)s;
        border-radius: 2px;
    }
    
    QSlider::sub-page:horizontal {
        background-color: %(accent_primary)s;
        border-radius: 2px;
    }
    
    QSlider::handle:horizontal {
        background-color: %(text_primary)s;
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }
    
    QSlider::handle:horizontal:hover {
        background-color: %(accent_primary)s;
    }
    
    /* Progress Bars */
    QProgressBar {
        background-color: %(bg_primary)s;
        border: none;
        border-radius: 4px;
        height: 6px;
        text-align: center;
        color: %(text_primary)s;
        font-size: 11px;
        font-weight: 500;
    }

    QProgressBar::chunk {
        background-color: %(accent_primary)s;
        border-radius: 3px;
    }

    QProgressBar#success::chunk {
        background-color: %(success)s;
    }

    QProgressBar#warning::chunk {
        background-color: %(warning)s;
    }
    
    QProgressBar#error::chunk {
        background-color: %(error)s;
    }
    
    /* Scroll Bars - modernized, invisible track */
    QScrollBar:vertical {
        background-color: transparent;
        width: 8px;
        margin: 0px;
    }

    QScrollBar::handle:vertical {
        background-color: %(border_light)s;
        min-height: 30px;
        border-radius: 4px;
        margin: 0px 2px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: %(text_muted)s;
    }

    QScrollBar::handle:vertical:pressed {
        background-color: %(accent_primary)s;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
        height: 0px;
        border: none;
    }

    QScrollBar:horizontal {
        background-color: transparent;
        height: 8px;
        margin: 0px;
    }

    QScrollBar::handle:horizontal {
        background-color: %(border_light)s;
        min-width: 30px;
        border-radius: 4px;
        margin: 2px 0px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: %(text_muted)s;
    }

    QScrollBar::handle:horizontal:pressed {
        background-color: %(accent_primary)s;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
        width: 0px;
        border: none;
    }
    
    /* List Widgets */
    QListWidget {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 10px;
        padding: 6px;
        color: %(text_primary)s;
    }

    QListWidget::item {
        padding: 9px 14px;
        border-radius: 6px;
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
    }

    QListWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 %(accent_primary)s, stop:1 %(accent_hover)s);
        color: #FFFFFF;
        font-weight: 500;
    }

    QListWidget::item:hover:!selected {
        background-color: %(surface)s;
        color: %(text_primary)s;
    }

    QListWidget::item:!enabled {
        color: %(text_disabled)s;
        background-color: transparent;
    }
    
    /* Tree Widgets */
    QTreeWidget {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
    }

    QTreeWidget::item {
        padding: 6px;
        color: %(text_primary)s;
    }
    
    QTreeWidget::item:selected {
        background-color: %(accent_primary)s;
        color: #FFFFFF;
    }
    
    QTreeWidget::item:hover:!selected {
        background-color: %(surface)s;
    }
    
    QTreeWidget::branch {
        background-color: transparent;
    }
    
    /* Tab Widgets */
    QTabWidget::pane {
        background-color: %(bg_tertiary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        top: -1px;
    }
    
    QTabBar {
        background-color: transparent;
    }
    
    QTabBar::tab {
        background-color: %(surface)s;
        color: %(text_secondary)s;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        border: none;
    }
    
    QTabBar::tab:selected {
        background-color: %(accent_primary)s;
        color: #FFFFFF;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: %(surface_hover)s;
        color: %(text_primary)s;
    }
    
    QTabBar::tab:!enabled {
        color: %(text_disabled)s;
        background-color: %(surface)s;
    }
    
    QTabWidget QTabBar::tear-indicator {
        background-color: transparent;
    }
    
    /* Menu Bar */
    QMenuBar {
        background-color: %(bg_primary)s;
        color: %(text_primary)s;
        padding: 4px;
        border: none;
    }
    
    QMenuBar::item {
        padding: 6px 12px;
        border-radius: 4px;
        background-color: transparent;
        color: %(text_primary)s;
        border: none;
    }
    
    QMenuBar::item:selected {
        background-color: %(accent_primary)s;
        color: #FFFFFF;
    }
    
    QMenuBar::item:!enabled {
        color: %(text_disabled)s;
    }
    
    /* Menus */
    QMenu {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        padding: 6px;
    }
    
    QMenu::item {
        padding: 8px 24px;
        border-radius: 4px;
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
    }
    
    QMenu::item:selected {
        background-color: %(accent_primary)s;
        color: #FFFFFF;
    }
    
    QMenu::item:!enabled {
        color: %(text_disabled)s;
        background-color: transparent;
    }
    
    QMenu::separator {
        height: 1px;
        background-color: %(divider)s;
        margin: 6px 0;
    }
    
    QMenu::icon {
        background-color: transparent;
    }
    
    /* Tool Tips */
    QToolTip {
        background-color: %(bg_primary)s;
        color: %(text_primary)s;
        border: 1px solid %(border)s;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 12px;
    }
    
    /* Splitters */
    QSplitter::handle {
        background-color: %(divider)s;
    }
    
    QSplitter::handle:horizontal {
        width: 2px;
    }
    
    QSplitter::handle:vertical {
        height: 2px;
    }
    
    /* Headers */
    QHeaderView::section {
        background-color: %(surface)s;
        color: %(text_primary)s;
        padding: 8px;
        border: none;
        font-weight: 600;
    }
    
    QHeaderView::section:hover {
        background-color: %(surface_hover)s;
    }
    
    /* Tables */
    QTableWidget {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        gridline-color: %(divider)s;
    }
    
    QTableWidget::item {
        padding: 6px;
        color: %(text_primary)s;
    }
    
    QTableWidget::item:selected {
        background-color: %(accent_primary)s;
        color: #FFFFFF;
    }
    
    /* Dialogs */
    QDialog {
        background-color: %(bg_secondary)s;
    }
    
    /* Labels - Clean Text Rendering */
    QLabel {
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
        padding: 0px;
        margin: 0px;
    }
    
    QLabel#heading {
        font-size: 18px;
        font-weight: 600;
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
    }
    
    QLabel#subheading {
        font-size: 14px;
        font-weight: 500;
        color: %(text_secondary)s;
        background-color: transparent;
        border: none;
    }
    
    QLabel#muted {
        color: %(text_muted)s;
        background-color: transparent;
        border: none;
    }
    
    QLabel#accent {
        color: %(accent_primary)s;
        background-color: transparent;
        border: none;
    }
    
    QLabel#title {
        font-size: 20px;
        font-weight: 700;
        color: %(text_primary)s;
        background-color: transparent;
        border: none;
    }
    
    /* Status Bar */
    QStatusBar {
        background-color: %(bg_primary)s;
        color: %(text_secondary)s;
        border-top: 1px solid %(border)s;
    }
    
    QStatusBar::item {
        border: none;
        background-color: transparent;
    }
    
    QStatusBar QLabel {
        color: %(text_secondary)s;
        background-color: transparent;
        border: none;
    }
    
    /* Dock Widgets */
    QDockWidget {
        titlebar-close-icon: url(close.png);
        titlebar-normal-icon: url(undock.png);
        color: %(text_primary)s;
    }
    
    QDockWidget::title {
        background-color: %(surface)s;
        padding: 8px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: %(text_primary)s;
    }
    
    QDockWidget::close-button, QDockWidget::float-button {
        background-color: transparent;
        border-radius: 4px;
        padding: 2px;
        border: none;
    }
    
    QDockWidget::close-button:hover, QDockWidget::float-button:hover {
        background-color: %(accent_primary)s;
    }
    
    /* Tool Buttons */
    QToolButton {
        background-color: %(surface)s;
        border: none;
        border-radius: 6px;
        padding: 6px;
    }
    
    QToolButton:hover {
        background-color: %(surface_hover)s;
    }
    
    QToolButton:pressed {
        background-color: %(accent_primary)s;
    }
    
    QToolButton::menu-indicator {
        image: none;
    }
    
    /* Calendar Widget */
    QCalendarWidget {
        background-color: %(bg_primary)s;
    }
    
    QCalendarWidget QTableView {
        background-color: %(bg_primary)s;
        selection-background-color: %(accent_primary)s;
    }
    
    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background-color: %(surface)s;
    }
    
    QCalendarWidget QToolButton {
        background-color: transparent;
        color: %(text_primary)s;
        font-weight: 600;
    }
    
    QCalendarWidget QMenu {
        background-color: %(bg_primary)s;
    }
    
    /* Date/Time Edits */
    QDateEdit, QTimeEdit, QDateTimeEdit {
        background-color: %(bg_primary)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        padding: 8px;
        color: %(text_primary)s;
        selection-background-color: %(accent_primary)s;
    }
    
    QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {
        border: 2px solid %(accent_primary)s;
    }
    
    QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {
        border: none;
        width: 24px;
    }
    
    /* Frame */
    QFrame {
        background-color: transparent;
        border: none;
    }
    
    QFrame#card {
        background-color: %(bg_tertiary)s;
        border: 1px solid %(border)s;
        border-radius: 12px;
    }
    
    QFrame#divider {
        background-color: %(divider)s;
        max-height: 1px;
    }
    
    /* Scroll Area */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    /* Stacked Widget */
    QStackedWidget {
        background-color: transparent;
    }
    
    /* Input Dialogs */
    QInputDialog {
        background-color: %(bg_secondary)s;
    }
    
    QInputDialog QLineEdit {
        min-width: 200px;
    }
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize theme manager.
        
        Args:
            config_path: Path to theme configuration file. 
                        Defaults to 'theme_config.json' in project root.
        """
        if config_path is None:
            migrate_legacy_layout()
            self.config_path = shared_theme_config_path()
        else:
            self.config_path = Path(config_path)
        
        self.theme = self.load_theme() or self.create_default_theme()
        self._qss_cache: Optional[str] = None
        self._on_theme_changed: Optional[Callable[[Theme], None]] = None
        self._app: Optional[object] = None

    @property
    def tokens(self) -> ThemeTokens:
        """Return typed theme/layout tokens for shared widgets."""
        return ThemeTokens(self.theme.copy())

    @property
    def design_tokens(self) -> DesignTokens:
        """Return semantic design tokens built from the active theme."""
        return make_design_tokens(self.theme)

    def create_default_theme(self) -> Theme:
        """Create the release default theme: Discord Dark with a red accent."""
        return create_theme_from_preset("Discord Dark", AccentColor.RED)
    
    def set_theme_changed_callback(self, callback: Callable[[Theme], None]) -> None:
        """
        Set a callback to be called when the theme changes.
        
        Args:
            callback: Function that receives the new Theme object
        """
        self._on_theme_changed = callback
    
    def switch_theme(self, theme_name: str, accent: Optional[Union[AccentColor, str]] = None) -> bool:
        """
        Switch to a different theme preset at runtime.
        
        Args:
            theme_name: Name of the preset theme to switch to
            accent: Optional custom accent color
            
        Returns:
            True if theme was switched successfully
        """
        if theme_name not in THEME_PRESETS:
            print(f"[ThemeManager] Unknown theme: {theme_name}")
            return False
        
        # Convert accent string to enum if needed
        if isinstance(accent, str):
            accent = AccentColor.from_string(accent)
        
        # Create new theme from preset
        self.theme = create_theme_from_preset(theme_name, accent)
        self._qss_cache = None  # Invalidate cache
        
        # Reapply theme if we have an app reference
        if self._app is not None:
            self.apply_theme(self._app)
        
        # Notify callback
        if self._on_theme_changed:
            self._on_theme_changed(self.theme)
        
        return True
    
    def set_accent_color(self, color: Union[AccentColor, str]) -> None:
        """
        Set the accent color.
        
        Args:
            color: AccentColor enum or string name (e.g., 'red', 'green')
        """
        if isinstance(color, str):
            color = AccentColor.from_string(color)
        self.theme.accent = color
        self._qss_cache = None  # Invalidate cache
        
        # Reapply theme if we have an app reference
        if self._app is not None:
            self.apply_theme(self._app)
        
        # Notify callback
        if self._on_theme_changed:
            self._on_theme_changed(self.theme)
    
    def get_accent_color(self) -> AccentColor:
        """Get current accent color."""
        return self.theme.accent
    
    def get_available_accents(self) -> Dict[str, str]:
        """
        Get available accent colors with their hex values.
        
        Returns:
            Dictionary mapping color names to hex values
        """
        return {
            'Discord Blue': AccentColor.DISCORD_BLUE.primary,
            'Red': AccentColor.RED.primary,
            'Green': AccentColor.GREEN.primary,
            'Purple': AccentColor.PURPLE.primary,
            'Orange': AccentColor.ORANGE.primary,
            'Pink': AccentColor.PINK.primary,
            'Cyan': AccentColor.CYAN.primary,
            'Yellow': AccentColor.YELLOW.primary,
        }
    
    def get_available_themes(self) -> List[str]:
        """
        Get list of available theme preset names.
        
        Returns:
            List of theme names
        """
        return get_preset_names()
    
    def generate_qss(self) -> str:
        """
        Generate QSS stylesheet from current theme.
        
        Returns:
            Complete QSS string ready to apply to application
        """
        if self._qss_cache is not None:
            return self._qss_cache
        
        # Build color dictionary
        theme_dict = self.theme.to_dict()
        colors = {
            'name': self.theme.name,
            'accent_primary': self.theme.accent_primary,
            'accent_hover': self.theme.accent_hover,
            **{k: v for k, v in theme_dict.items() 
               if k not in ('accent',)}
        }
        
        self._qss_cache = self.QSS_TEMPLATE % colors
        return self._qss_cache
    
    def apply_theme(self, app) -> None:
        """
        Apply current theme to PyQt6 application.
        
        Args:
            app: QApplication instance
        """
        try:
            from PyQt6.QtWidgets import QApplication
            
            if not isinstance(app, QApplication):
                raise TypeError("app must be a QApplication instance")
            
            self._app = app  # Store reference for runtime switching
            qss = self.generate_qss()
            app.setStyleSheet(qss)
            
        except ImportError:
            raise ImportError("PyQt6 is required to apply themes")
    
    def save_theme(self) -> bool:
        """
        Save current theme to configuration file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'theme': self.theme.to_dict(),
                'version': '2.0'
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving theme: {e}")
            return False
    
    def load_theme(self) -> Optional[Theme]:
        """
        Load theme from configuration file.
        
        Returns:
            Theme object if successful, None otherwise
        """
        try:
            if not self.config_path.exists():
                return None
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            theme_data = config.get('theme', {})
            
            # Handle legacy field names (background_primary -> bg_primary, etc.)
            field_mapping = {
                'background_primary': 'bg_primary',
                'background_secondary': 'bg_secondary',
                'background_tertiary': 'bg_tertiary',
            }
            for old_key, new_key in field_mapping.items():
                if old_key in theme_data and new_key not in theme_data:
                    theme_data[new_key] = theme_data.pop(old_key)
            
            return Theme.from_dict(theme_data)
            
        except Exception as e:
            print(f"Error loading theme: {e}")
            return None
    
    def reset_to_default(self) -> None:
        """Reset theme to default dark theme."""
        self.theme = self.create_default_theme()
        self._qss_cache = None
        
        if self._app is not None:
            self.apply_theme(self._app)
        
        if self._on_theme_changed:
            self._on_theme_changed(self.theme)
    
    def get_current_theme_info(self) -> Dict:
        """
        Get information about the current theme.
        
        Returns:
            Dictionary with theme information
        """
        return {
            'name': self.theme.name,
            'accent': self.theme.accent.name,
            'is_dark': self._is_dark_theme(),
            'accent_primary': self.theme.accent_primary,
            'accent_hover': self.theme.accent_hover,
        }
    
    def _is_dark_theme(self) -> bool:
        """Check if current theme is dark based on background color."""
        # Simple heuristic: check if background is dark
        bg = self.theme.bg_primary.lstrip('#')
        r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128


# ============================================
# Convenience Functions
# ============================================

def get_theme(name: str) -> Dict:
    """Get a theme preset by name (legacy compatibility)."""
    return get_theme_preset(name)


def get_theme_names() -> List[str]:
    """Get list of available theme names (legacy compatibility)."""
    return get_preset_names()


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager(config_path: Optional[str] = None) -> ThemeManager:
    """
    Get or create the global theme manager instance.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        ThemeManager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager(config_path)
    return _theme_manager


def switch_theme(theme_name: str, accent: Optional[Union[str, AccentColor]] = None) -> bool:
    """
    Convenience function to switch theme using global theme manager.
    
    Args:
        theme_name: Name of theme preset
        accent: Optional accent color
        
    Returns:
        True if successful
    """
    manager = get_theme_manager()
    return manager.switch_theme(theme_name, accent)


# ============================================
# Example Usage
# ============================================

def example_usage():
    """
    Example usage of the theme system.
    """
    print("=" * 70)
    print("ABUSER Bot GUI - Theme System Example")
    print("=" * 70)
    
    print("\nAvailable Themes:")
    print("-" * 40)
    dark_themes = ["Midnight", "Obsidian", "Discord Dark", "Catppuccin Mocha", "Dracula", "Nord", "Cyberpunk"]
    light_themes = ["Light", "GitHub Light", "Solarized Light"]
    for name in get_preset_names():
        theme = create_theme_from_preset(name)
        if name in dark_themes:
            theme_type = "[Dark]"
        elif name in light_themes:
            theme_type = "[Light]"
        else:
            theme_type = "[Specialty]"
        print(f"  {theme_type:12} {name}")
    
    print("\nAvailable Accent Colors:")
    print("-" * 40)
    for name, color in AccentColor.__members__.items():
        print(f"  - {name.replace('_', ' ').title()}: {color.primary}")
    
    # Create theme manager
    manager = ThemeManager()
    
    print(f"\nCurrent Theme: {manager.theme.name}")
    print(f"   Accent: {manager.theme.accent.name}")
    print(f"   Is Dark: {manager._is_dark_theme()}")
    
    # Generate QSS preview
    qss = manager.generate_qss()
    print(f"\nGenerated QSS: {len(qss)} characters")
    
    # Demonstrate theme switching
    print("\nTheme Switching Demo:")
    print("-" * 40)
    
    for theme_name in ["Dracula", "Catppuccin Mocha", "GitHub Light", "Cyberpunk"]:
        manager.switch_theme(theme_name)
        print(f"  Switched to: {manager.theme.name} (accent: {manager.theme.accent.name})")
    
    # Reset to default
    manager.reset_to_default()
    print(f"\nReset to: {manager.theme.name}")
    
    print("\n" + "=" * 70)
    print("Usage in PyQt6 Application:")
    print("=" * 70)
    print("""
    from PyQt6.QtWidgets import QApplication
    from abuse.gui.theme import get_theme_manager, switch_theme
    
    app = QApplication(sys.argv)
    
    # Get theme manager and apply theme
    theme_manager = get_theme_manager()
    theme_manager.apply_theme(app)
    
    # Switch theme at runtime
    theme_manager.switch_theme("Dracula")
    
    # Or use convenience function
    switch_theme("Catppuccin Mocha", accent="pink")
    """)
    
    return manager


if __name__ == "__main__":
    example_usage()
