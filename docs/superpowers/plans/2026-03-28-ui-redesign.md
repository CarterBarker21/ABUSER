# ABUSER UI Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Achieve global visual consistency across all 7 pages by adding a semantic DesignTokens system, pruning to 4 curated themes, reordering the sidebar with a collapsible toggle, and sweeping every page to remove any inline hard-coded colors.

**Architecture:** A new `DesignTokens` frozen dataclass in `theme.py` provides semantic color aliases over the existing `Theme` fields. `ThemeManager` exposes `design_tokens` as a property. `ThemedWidget` gains a `dt` shortcut. All components and pages reference `dt` instead of raw `self.theme.{field}` calls. Shape/spacing constants stay in the existing `LayoutTokens`.

**Tech Stack:** Python 3.8+, PyQt6 6.4+, QSS, dataclasses, pytest-qt

---

## File Map

| File | Action | What changes |
|---|---|---|
| `abuse/gui/theme.py` | Modify | Add `DesignTokens`, `_rgba`, `make_design_tokens`, `ThemeManager.design_tokens`; prune `THEME_PRESETS` to 4; update `LIGHT_THEME_PRESETS`/`SPECIAL_THEME_PRESETS` |
| `abuse/gui/components.py` | Modify | Add `dt` property to `ThemedWidget`; update `refresh_theme()` in all components to use `self.dt` |
| `abuse/gui/routes.py` | Modify | Add `group` field to `RouteDefinition`; reorder `ROUTES` to Login→Guilds→Nuker→DM (core) then Logs→Settings→Docs (utility) |
| `abuse/gui/main_window.py` | Modify | Insert group divider in `_build_sidebar`; add collapse toggle button + `_toggle_sidebar()` |
| `abuse/gui/pages/login.py` | Modify | Remove inline `setStyleSheet` raw colors; use `InfoBanner` for all feedback |
| `abuse/gui/pages/guilds.py` | Modify | Remove inline `setStyleSheet` raw colors; use token-based labels |
| `abuse/gui/pages/nuker.py` | Modify | Remove inline `setStyleSheet` raw colors; use token-based labels |
| `abuse/gui/pages/dm.py` | Modify | Remove inline `setStyleSheet` raw colors |
| `abuse/gui/pages/logs.py` | Modify | Map log level colors to `DesignTokens` fields |
| `abuse/gui/pages/settings.py` | Modify | Update theme preset list to 4 curated names; remove family-filter UI |
| `abuse/gui/pages/docs.py` | Modify | Remove inline `setStyleSheet` raw colors |
| `config/gui_config.json` | Modify | Ensure `preset` is one of 4 curated names |
| `tests/test_design_tokens.py` | Create | Unit tests for `DesignTokens` factory |

---

## Task 1: Add DesignTokens to theme.py

**Files:**
- Modify: `abuse/gui/theme.py` (after `ThemeTokens` class, before `THEME_PRESETS`)
- Create: `tests/test_design_tokens.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_design_tokens.py`:
```python
import pytest
from abuse.gui.theme import (
    DesignTokens,
    make_design_tokens,
    create_theme_from_preset,
    get_theme_manager,
)


def test_design_tokens_fields_populated():
    theme = create_theme_from_preset("Midnight")
    dt = make_design_tokens(theme)
    assert dt.background == theme.bg_primary
    assert dt.surface == theme.surface
    assert dt.surface_raised == theme.surface_hover
    assert dt.border == theme.border
    assert dt.border_strong == theme.border_light
    assert dt.text_primary == theme.text_primary
    assert dt.text_secondary == theme.text_secondary
    assert dt.text_muted == theme.text_muted
    assert dt.text_disabled == theme.text_disabled
    assert dt.accent == theme.accent_primary
    assert dt.accent_hover == theme.accent_hover
    assert dt.accent_muted.startswith("rgba(")
    assert dt.danger == theme.error
    assert dt.danger_hover == theme.error_hover
    assert dt.success == theme.success
    assert dt.success_bright == theme.success_bright
    assert dt.warning == theme.warning


def test_design_tokens_all_four_themes():
    for name in ("Midnight", "Obsidian", "Discord Dark", "Catppuccin Mocha"):
        theme = create_theme_from_preset(name)
        dt = make_design_tokens(theme)
        assert isinstance(dt, DesignTokens)
        assert dt.background
        assert dt.accent


def test_theme_manager_design_tokens_property():
    manager = get_theme_manager()
    dt = manager.design_tokens
    assert isinstance(dt, DesignTokens)
    assert dt.accent == manager.theme.accent_primary
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_design_tokens.py -v
```
Expected: `ImportError` — `DesignTokens` and `make_design_tokens` do not exist yet.

- [ ] **Step 3: Add `_rgba` helper + `DesignTokens` dataclass + `make_design_tokens` to theme.py**

Open `abuse/gui/theme.py`. Find the line `@dataclass(frozen=True)` above `class LayoutTokens` (around line 170). Insert the following block **immediately after the `ThemeTokens` class ends** (after the `input` property):

```python
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


def make_design_tokens(theme: "Theme") -> DesignTokens:
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
```

- [ ] **Step 4: Add `design_tokens` property to `ThemeManager`**

In `abuse/gui/theme.py`, find the `tokens` property of `ThemeManager` (around line 1531):
```python
    @property
    def tokens(self) -> ThemeTokens:
        """Return typed theme/layout tokens for shared widgets."""
        return ThemeTokens(self.theme.copy())
```

Add the new property immediately after it:
```python
    @property
    def design_tokens(self) -> DesignTokens:
        """Return semantic design tokens built from the active theme."""
        return make_design_tokens(self.theme)
```

- [ ] **Step 5: Run tests to verify they pass**

```
pytest tests/test_design_tokens.py -v
```
Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_design_tokens.py abuse/gui/theme.py
git commit -m "feat: add DesignTokens semantic color layer to theme system"
```

---

## Task 2: Expose `dt` on ThemedWidget

**Files:**
- Modify: `abuse/gui/components.py`

- [ ] **Step 1: Update the `from .theme import` line at the top of `components.py`**

Find the existing import (line 26):
```python
from .theme import get_theme_manager
```
Replace with:
```python
from .theme import DesignTokens, get_theme_manager
```

- [ ] **Step 2: Add `dt` property to `ThemedWidget`**

Find the `ThemedWidget` class (around line 59). After the `tokens` property, add:
```python
    @property
    def dt(self) -> DesignTokens:
        """Semantic design tokens — use this instead of raw ``self.theme`` in new code."""
        return get_theme_manager().design_tokens
```

The full updated class:
```python
class ThemedWidget:
    """Mixin for widgets that read tokens from ThemeManager."""

    @property
    def theme(self):
        return get_theme_manager().theme

    @property
    def tokens(self):
        return get_theme_manager().tokens

    @property
    def dt(self) -> DesignTokens:
        """Semantic design tokens — use this instead of raw ``self.theme`` in new code."""
        return get_theme_manager().design_tokens

    def refresh_theme(self) -> None:  # pragma: no cover - interface hook
        pass
```

- [ ] **Step 3: Update `StatusChip.refresh_theme()` to use `self.dt`**

Find `StatusChip.refresh_theme()` (around line 87) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        palette = {
            "neutral":  (rgba(dt.text_secondary, 0.14), dt.text_secondary,  rgba(dt.border_strong, 0.9)),
            "accent":   (rgba(dt.accent, 0.16),         dt.accent,           rgba(dt.accent, 0.42)),
            "success":  (rgba(dt.success_bright, 0.16), dt.success_bright,   rgba(dt.success_bright, 0.42)),
            "warning":  (rgba(dt.warning, 0.16),        dt.warning,          rgba(dt.warning, 0.42)),
            "danger":   (rgba(dt.danger, 0.16),         dt.danger,           rgba(dt.danger, 0.42)),
            "preview":  (rgba(dt.text_muted, 0.14),     dt.text_muted,       rgba(dt.text_muted, 0.36)),
        }
        background, text, border = palette.get(self._tone, palette["neutral"])
        radius = self.tokens.metrics.control_height_sm // 2
        self.setStyleSheet(
            f"""
            QLabel#statusChip {{
                background-color: {background};
                color: {text};
                border: 1px solid {border};
                border-radius: {radius}px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 600;
            }}
            """
        )
```

- [ ] **Step 4: Update `PageHeader.refresh_theme()` to use `self.dt`**

Find `PageHeader.refresh_theme()` (around line 161) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        self.eyebrow_label.setStyleSheet(
            f"color: {dt.text_muted}; font-size: 11px; font-weight: 700; letter-spacing: 1.8px;"
        )
        self.title_label.setStyleSheet(f"color: {dt.text_primary};")
        self.description_label.setStyleSheet(
            f"color: {dt.text_secondary}; font-size: 13px; line-height: 1.4em;"
        )
        self.status_chip.refresh_theme()
```

- [ ] **Step 5: Update `SectionLabel.refresh_theme()` to use `self.dt`**

Find `SectionLabel.refresh_theme()` (around line 178) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"color: {dt.text_muted}; font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )
```

- [ ] **Step 6: Update `PanelCard.refresh_theme()` to use `self.dt`**

Find `PanelCard.refresh_theme()` (around line 224) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        border_map = {
            "neutral": rgba(dt.border_strong, 0.9),
            "accent":  rgba(dt.accent, 0.45),
            "warning": rgba(dt.warning, 0.48),
            "danger":  rgba(dt.danger, 0.48),
            "success": rgba(dt.success_bright, 0.48),
        }
        border = border_map.get(self._tone, border_map["neutral"])
        self.setStyleSheet(
            f"""
            QFrame#panelCard {{
                background-color: {dt.surface};
                border: 1px solid {border};
                border-radius: {self.tokens.metrics.card_radius}px;
            }}
            """
        )
        self.title_label.setStyleSheet(f"color: {dt.text_primary};")
        self.description_label.setStyleSheet(
            f"color: {dt.text_secondary}; font-size: 12px; line-height: 1.4em;"
        )
```

- [ ] **Step 7: Update `AppButton.refresh_theme()` to use `self.dt`**

Find `AppButton.refresh_theme()` (around line 261) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        variants = {
            "primary":   (dt.accent,                    "#FFFFFF",          dt.accent_hover,    rgba(dt.accent, 0.7)),
            "secondary": (dt.surface,                   dt.text_primary,    dt.surface_raised,  rgba(dt.border_strong, 1.0)),
            "tertiary":  (rgba(dt.surface, 0.45),       dt.text_secondary,  rgba(dt.surface_raised, 0.85), rgba(dt.border_strong, 0.8)),
            "danger":    (dt.danger,                    "#FFFFFF",          dt.danger_hover,    rgba(dt.danger, 0.6)),
            "success":   (dt.success,                   "#FFFFFF",          dt.success,         rgba(dt.success_bright, 0.6)),
            "preview":   (rgba(dt.text_muted, 0.12),    dt.text_muted,      rgba(dt.text_muted, 0.18), rgba(dt.text_muted, 0.35)),
        }
        background, text, hover, border = variants.get(self._variant, variants["secondary"])
        disabled_bg   = rgba(dt.text_muted, 0.12)
        disabled_text = blend(dt.text_muted, dt.background, 0.05)
        pressed = hover if hover.startswith("rgba") else blend(hover, dt.background, 0.18)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {background};
                color: {text};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 0 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
            QPushButton:disabled {{
                background-color: {disabled_bg};
                color: {disabled_text};
                border-color: {rgba(dt.text_muted, 0.25)};
            }}
            """
        )
```

- [ ] **Step 8: Update `SidebarNavButton.refresh_theme()` to use `self.dt`**

Find `SidebarNavButton.refresh_theme()` (around line 354) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QPushButton#sidebarNavButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton#sidebarNavButton:hover {{
                background-color: {rgba(dt.surface_raised, 0.7)};
                border-color: {rgba(dt.border_strong, 0.7)};
            }}
            QPushButton#sidebarNavButton:checked {{
                background-color: {dt.accent_muted};
                border: 1px solid {rgba(dt.accent, 0.36)};
                border-left: 3px solid {dt.accent};
            }}
            QPushButton#sidebarNavButton:checked:hover {{
                background-color: {rgba(dt.accent, 0.2)};
            }}
            """
        )
        checked = self.isChecked()
        icon_color = dt.accent if checked else dt.text_muted
        title_fg   = dt.text_primary if checked else dt.text_secondary
        self.icon_label.setStyleSheet("background-color: transparent;")
        self._update_icon(icon_color)
        self.title_label.setStyleSheet(f"color: {title_fg}; background-color: transparent;")
```

- [ ] **Step 9: Update `AppLineEdit.refresh_theme()` to use `self.dt`**

Find `AppLineEdit.refresh_theme()` (around line 395) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 10px;
                padding: 0 12px;
                selection-background-color: {rgba(dt.accent, 0.35)};
            }}
            QLineEdit:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QLineEdit:focus {{
                border-color: {dt.accent};
            }}
            """
        )
```

- [ ] **Step 10: Update `AppComboBox.refresh_theme()` to use `self.dt`**

Find `AppComboBox.refresh_theme()` (around line 427) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 10px;
                padding: 0 12px;
            }}
            QComboBox:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QComboBox:focus {{
                border-color: {dt.accent};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 22px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {dt.surface};
                color: {dt.text_primary};
                border: 1px solid {dt.border};
                selection-background-color: {rgba(dt.accent, 0.28)};
            }}
            """
        )
```

- [ ] **Step 11: Update `AppTextEdit.refresh_theme()` to use `self.dt`**

Find `AppTextEdit.refresh_theme()` (around line 464) and replace:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 12px;
                padding: 10px 12px;
                selection-background-color: {rgba(dt.accent, 0.35)};
            }}
            QTextEdit:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QTextEdit:focus {{
                border-color: {dt.accent};
            }}
            """
        )
```

- [ ] **Step 12: Update `AppSpinBox.refresh_theme()` to use `self.dt`**

Find `AppSpinBox.refresh_theme()` (around line 492). Replace the body so it reads:
```python
    def refresh_theme(self) -> None:
        dt = self.dt
        self.setStyleSheet(
            f"""
            QSpinBox {{
                background-color: {dt.background};
                color: {dt.text_primary};
                border: 1px solid {rgba(dt.border_strong, 0.95)};
                border-radius: 10px;
                padding: 0 12px;
            }}
            QSpinBox:hover {{
                border-color: {rgba(dt.text_secondary, 0.6)};
            }}
            QSpinBox:focus {{
                border-color: {dt.accent};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                background: transparent;
                width: 16px;
            }}
            """
        )
```

- [ ] **Step 13: Find and update remaining components that use `self.theme` directly**

Run this to find any remaining `self.theme` usages in components.py (there should be very few left — only in `ToggleSwitch`, `InfoBanner`, `EmptyState`, `ActionTileButton`, `SidebarStatusPanel`):
```
grep -n "self\.theme\." abuse/gui/components.py
```

For each match, replace `colors = self.theme` / `self.theme.{field}` with the equivalent `self.dt.{field}` using the mapping:
- `colors.bg_primary` / `self.theme.bg_primary` → `dt.background`
- `colors.surface` → `dt.surface`
- `colors.surface_hover` → `dt.surface_raised`
- `colors.border` → `dt.border`
- `colors.border_light` → `dt.border_strong`
- `colors.text_primary` → `dt.text_primary`
- `colors.text_secondary` → `dt.text_secondary`
- `colors.text_muted` → `dt.text_muted`
- `colors.text_disabled` → `dt.text_disabled`
- `colors.accent_primary` → `dt.accent`
- `colors.accent_hover` → `dt.accent_hover`
- `colors.error` → `dt.danger`
- `colors.error_hover` → `dt.danger_hover`
- `colors.success` → `dt.success`
- `colors.success_bright` → `dt.success_bright`
- `colors.warning` → `dt.warning`
- `colors.card_bg` → `dt.surface`
- `colors.input_bg` → `dt.background`
- `colors.bg_secondary` → `dt.surface`

In each `refresh_theme()` method, replace the opening `colors = self.theme` line with `dt = self.dt` and update all references accordingly.

- [ ] **Step 14: Smoke-test that components initialise correctly**

```
pytest tests/test_gui_smoke.py -v
```
Expected: all existing tests PASS.

- [ ] **Step 15: Commit**

```bash
git add abuse/gui/components.py
git commit -m "refactor: update all components to use DesignTokens via self.dt"
```

---

## Task 3: Prune THEME_PRESETS to 4 curated themes

**Files:**
- Modify: `abuse/gui/theme.py`
- Modify: `config/gui_config.json`

- [ ] **Step 1: Delete the 8 removed themes from `THEME_PRESETS` in `theme.py`**

In `abuse/gui/theme.py`, find `THEME_PRESETS` (around line 219). Delete the following keys and their entire dict bodies (from the opening `"Name": {` to the closing `},`):
- `"Dracula"`
- `"Nord"`
- `"Cyberpunk"`
- `"Light"`
- `"GitHub Light"`
- `"Solarized Light"`
- `"Sunset"`
- `"Forest"`
- `"Ocean"`

Only these 4 entries should remain: `"Midnight"`, `"Obsidian"`, `"Discord Dark"`, `"Catppuccin Mocha"`.

- [ ] **Step 2: Update the theme family sets**

Find and replace:
```python
LIGHT_THEME_PRESETS = {"Light", "GitHub Light", "Solarized Light"}
SPECIAL_THEME_PRESETS = {"Cyberpunk", "Sunset", "Forest", "Ocean"}
```
with:
```python
LIGHT_THEME_PRESETS: set[str] = set()
SPECIAL_THEME_PRESETS: set[str] = set()
```

- [ ] **Step 3: Verify `config/gui_config.json` uses a valid preset**

Read `config/gui_config.json`. If `appearance.preset` is not one of `Midnight`, `Obsidian`, `Discord Dark`, `Catppuccin Mocha`, change it to `"Midnight"`. Example valid file:
```json
{
  "appearance": {
    "preset": "Midnight",
    "theme_mode": 0,
    "accent": "Red",
    "font_size": 13,
    "animations": true
  },
  "behavior": {
    "confirm_actions": true,
    "log_commands": true,
    "startup_page": "Login",
    "last_route": "login"
  },
  "privacy": {
    "save_tokens": true,
    "encrypt_tokens": false
  }
}
```

- [ ] **Step 4: Run all tests**

```
pytest -v
```
Expected: all tests PASS. (The conftest uses "Discord Dark" which is still valid.)

- [ ] **Step 5: Commit**

```bash
git add abuse/gui/theme.py config/gui_config.json
git commit -m "feat: prune theme presets to 4 curated dark themes"
```

---

## Task 4: Reorder ROUTES and add group field

**Files:**
- Modify: `abuse/gui/routes.py`

- [ ] **Step 1: Write a failing test**

Add to `tests/test_design_tokens.py`:
```python
from abuse.gui.routes import ROUTES, ROUTE_DM, ROUTE_LOGS


def test_routes_order_core_before_utility():
    keys = [r.key for r in ROUTES]
    assert keys.index(ROUTE_DM) < keys.index(ROUTE_LOGS), (
        "DM (core) must appear before Logs (utility)"
    )


def test_routes_have_group_field():
    for route in ROUTES:
        assert route.group in ("core", "utility"), (
            f"Route {route.key} has invalid group '{route.group}'"
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_design_tokens.py::test_routes_order_core_before_utility tests/test_design_tokens.py::test_routes_have_group_field -v
```
Expected: FAIL — `RouteDefinition` has no `group` attribute.

- [ ] **Step 3: Update `routes.py`**

Replace the entire contents of `abuse/gui/routes.py` with:
```python
"""Route metadata shared by the sidebar, settings, and startup flow."""

from __future__ import annotations

from dataclasses import dataclass, field


ROUTE_LOGIN    = "login"
ROUTE_DOCS     = "docs"
ROUTE_GUILDS   = "guilds"
ROUTE_NUKER    = "nuker"
ROUTE_DM       = "dm"
ROUTE_LOGS     = "logs"
ROUTE_SETTINGS = "settings"
ROUTE_LAST_USED = "last_used"


@dataclass(frozen=True)
class RouteDefinition:
    key: str
    label: str
    icon_name: str
    description: str
    group: str = "core"   # "core" | "utility"


ROUTES = [
    # ── Core tools (top of sidebar) ──────────────────────────────────────────
    RouteDefinition(ROUTE_LOGIN,    "Login",    "login",    "Connect, disconnect, and manage remembered sessions.", group="core"),
    RouteDefinition(ROUTE_GUILDS,   "Guilds",   "guilds",   "Browse connected guilds and inspect their details.",  group="core"),
    RouteDefinition(ROUTE_NUKER,    "Nuker",    "nuker",    "Preview grouped action surfaces and safety gating.",  group="core"),
    RouteDefinition(ROUTE_DM,       "DM",       "dm",       "Compose drafts and review messaging controls.",       group="core"),
    # ── Utility (bottom of sidebar) ──────────────────────────────────────────
    RouteDefinition(ROUTE_LOGS,     "Logs",     "logs",     "Inspect runtime logs with filtering and export.",     group="utility"),
    RouteDefinition(ROUTE_SETTINGS, "Settings", "settings", "Adjust appearance, startup behavior, and privacy.",  group="utility"),
    RouteDefinition(ROUTE_DOCS,     "Docs",     "docs",     "Read the in-app guide and current UI notes.",         group="utility"),
]

ROUTE_INDEX  = {route.key: index for index, route in enumerate(ROUTES)}
ROUTE_LABELS = {route.key: route.label for route in ROUTES}
LABEL_TO_ROUTE = {route.label: route.key for route in ROUTES}
LABEL_TO_ROUTE["Last Used"] = ROUTE_LAST_USED
LABEL_TO_ROUTE["Commands"]  = ROUTE_GUILDS

STARTUP_OPTIONS = [route.label for route in ROUTES] + ["Last Used"]


def get_route_index(route_key: str) -> int:
    return ROUTE_INDEX.get(route_key, 0)


def get_route_label(route_key: str) -> str:
    return ROUTE_LABELS.get(route_key, ROUTE_LABELS[ROUTE_LOGIN])


def normalize_route(route_key: str | None) -> str:
    if not route_key:
        return ROUTE_LOGIN
    normalized = route_key.lower().strip().replace(" ", "_")
    if normalized == "last_used":
        return ROUTE_LAST_USED
    return normalized if normalized in ROUTE_INDEX else ROUTE_LOGIN


def route_from_label(label: str | None) -> str:
    if not label:
        return ROUTE_LOGIN
    return LABEL_TO_ROUTE.get(label, ROUTE_LOGIN)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_design_tokens.py -v
```
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add abuse/gui/routes.py tests/test_design_tokens.py
git commit -m "feat: reorder sidebar routes — core tools first, utility at bottom"
```

---

## Task 5: Add group divider to sidebar

**Files:**
- Modify: `abuse/gui/main_window.py`

- [ ] **Step 1: Update `_build_sidebar` to insert a divider between route groups**

In `abuse/gui/main_window.py`, find `_build_sidebar`. Replace the loop that creates nav buttons:

**Before:**
```python
        self.route_buttons: dict[str, SidebarNavButton] = {}
        for route in ROUTES:
            button = SidebarNavButton(route.icon_name, route.label)
            button.clicked.connect(lambda checked=False, key=route.key: self.switch_route(key))
            layout.addWidget(button)
            self.route_buttons[route.key] = button
```

**After:**
```python
        self.route_buttons: dict[str, SidebarNavButton] = {}
        prev_group: str | None = None
        for route in ROUTES:
            if prev_group is not None and route.group != prev_group:
                divider = QFrame()
                divider.setObjectName("sidebarDivider")
                divider.setFrameShape(QFrame.Shape.HLine)
                divider.setFixedHeight(1)
                layout.addWidget(divider)
            prev_group = route.group
            button = SidebarNavButton(route.icon_name, route.label)
            button.clicked.connect(lambda checked=False, key=route.key: self.switch_route(key))
            layout.addWidget(button)
            self.route_buttons[route.key] = button
```

- [ ] **Step 2: Style the divider in `refresh_theme` (add to end of `MainWindow.refresh_theme`)**

Find `MainWindow.refresh_theme` (search for `def refresh_theme`). At the end of the method, before the closing, add:

```python
        tm = self.theme_manager.theme
        for child in self.sidebar.findChildren(QFrame):
            if child.objectName() == "sidebarDivider":
                child.setStyleSheet(f"background-color: {tm.divider}; border: none;")
```

- [ ] **Step 3: Smoke-test**

```
pytest tests/test_gui_smoke.py -v
```
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add abuse/gui/main_window.py
git commit -m "feat: insert visual divider between sidebar route groups"
```

---

## Task 6: Add collapsible sidebar

**Files:**
- Modify: `abuse/gui/main_window.py`

- [ ] **Step 1: Add necessary import**

At the top of `main_window.py`, add `QPushButton` to the existing `QWidgets` import if not already present:
```python
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,          # add this if missing
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
```

- [ ] **Step 2: Add collapse state + toggle button at the bottom of `_build_sidebar`**

In `_build_sidebar`, find the lines after the nav loop (currently `layout.addStretch(1)` then `self.status_panel = SidebarStatusPanel()`). Replace that stretch+panel section with:

```python
        layout.addStretch(1)
        self.status_panel = SidebarStatusPanel()
        layout.addWidget(self.status_panel)

        # ── Collapse toggle ───────────────────────────────────────────────────
        self._sidebar_collapsed = False
        collapse_row = QHBoxLayout()
        collapse_row.setContentsMargins(0, 8, 0, 8)
        self._collapse_btn = QPushButton("◀")
        self._collapse_btn.setObjectName("sidebarCollapseBtn")
        self._collapse_btn.setFixedSize(28, 28)
        self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_btn.setToolTip("Collapse sidebar")
        self._collapse_btn.clicked.connect(self._toggle_sidebar)
        collapse_row.addStretch(1)
        collapse_row.addWidget(self._collapse_btn)
        layout.addLayout(collapse_row)

        return sidebar
```

Make sure the existing `return sidebar` line is removed from wherever it was and replaced by this block (the return is now inside this block).

- [ ] **Step 3: Add `_toggle_sidebar` method to `MainWindow`**

Add this method to the `MainWindow` class (after `_build_sidebar`):

```python
    def _toggle_sidebar(self) -> None:
        """Collapse or expand the sidebar between icon-only and full width."""
        self._sidebar_collapsed = not self._sidebar_collapsed
        expanded_width = self.theme_manager.tokens.metrics.sidebar_width

        if self._sidebar_collapsed:
            self.sidebar.setFixedWidth(56)
            self._collapse_btn.setText("▶")
            self._collapse_btn.setToolTip("Expand sidebar")
            self.brand_title.setVisible(False)
            self.brand_meta.setVisible(False)
            self.nav_heading.setVisible(False)
            for btn in self.route_buttons.values():
                btn.title_label.setVisible(False)
            # Hide dividers too
            for child in self.sidebar.findChildren(QFrame):
                if child.objectName() == "sidebarDivider":
                    child.setVisible(False)
        else:
            self.sidebar.setFixedWidth(expanded_width)
            self._collapse_btn.setText("◀")
            self._collapse_btn.setToolTip("Collapse sidebar")
            self.brand_title.setVisible(True)
            self.brand_meta.setVisible(True)
            self.nav_heading.setVisible(True)
            for btn in self.route_buttons.values():
                btn.title_label.setVisible(True)
            for child in self.sidebar.findChildren(QFrame):
                if child.objectName() == "sidebarDivider":
                    child.setVisible(True)
```

- [ ] **Step 4: Style the collapse button in `refresh_theme`**

In `MainWindow.refresh_theme`, add styling for the collapse button (add after the divider styling from Task 5):

```python
        if hasattr(self, "_collapse_btn"):
            self._collapse_btn.setStyleSheet(
                f"""
                QPushButton#sidebarCollapseBtn {{
                    background-color: transparent;
                    color: {tm.text_muted};
                    border: 1px solid transparent;
                    border-radius: 6px;
                    font-size: 10px;
                }}
                QPushButton#sidebarCollapseBtn:hover {{
                    background-color: {tm.surface_hover};
                    color: {tm.text_primary};
                    border-color: {tm.border_light};
                }}
                """
            )
```

- [ ] **Step 5: Smoke-test**

```
pytest tests/test_gui_smoke.py -v
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add abuse/gui/main_window.py
git commit -m "feat: add collapsible sidebar toggle (56px icon-only mode)"
```

---

## Task 7: Sweep Login page

**Files:**
- Modify: `abuse/gui/pages/login.py`

- [ ] **Step 1: Find all inline raw-color styling**

```
grep -n "setStyleSheet\|#[0-9A-Fa-f]\{6\}\|rgb(" abuse/gui/pages/login.py
```

- [ ] **Step 2: Replace each match**

For every `setStyleSheet(...)` call in `login.py` that contains a raw hex color (e.g. `#ED4245`, `#57F287`) or a direct `self.theme.{field}` reference:

Replace patterns like:
```python
some_label.setStyleSheet(f"color: {self.theme.error};")
```
with the `dt`-based equivalent:
```python
some_label.setStyleSheet(f"color: {get_theme_manager().design_tokens.danger};")
```

Or better — if the label is decorative/status, replace with a `StatusChip` or `InfoBanner` component that handles its own theming.

Add this import at the top if not present:
```python
from ..theme import get_theme_manager
```

- [ ] **Step 3: Verify page uses `InfoBanner` for all status feedback**

Search for any `QLabel` being used to display error/success messages:
```
grep -n "show_error\|error_label\|status_label" abuse/gui/pages/login.py
```

If `show_error` sets a raw color on a `QLabel`, update it to call `self.status_banner.set_tone("danger")` and use the existing `InfoBanner` component (`self.status_banner` already exists in the class).

- [ ] **Step 4: Smoke-test**

```
pytest tests/test_gui_smoke.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add abuse/gui/pages/login.py
git commit -m "fix: remove inline hard-coded colors from Login page"
```

---

## Task 8: Sweep Guilds page

**Files:**
- Modify: `abuse/gui/pages/guilds.py`

- [ ] **Step 1: Find inline raw-color styling**

```
grep -n "setStyleSheet\|#[0-9A-Fa-f]\{6\}" abuse/gui/pages/guilds.py
```

- [ ] **Step 2: Replace each raw-color match using the token map**

For each `setStyleSheet` call containing a raw hex or direct `self.theme.{field}` reference, replace with the `dt` equivalent. Example pattern:

Before:
```python
self.name_label.setStyleSheet(f"color: {self.theme.text_primary}; font-weight: 700;")
self.id_label.setStyleSheet("color: #80848E;")
```

After:
```python
dt = get_theme_manager().design_tokens
self.name_label.setStyleSheet(f"color: {dt.text_primary}; font-weight: 700;")
self.id_label.setStyleSheet(f"color: {dt.text_muted};")
```

Import at top of file if not present:
```python
from ..theme import get_theme_manager
```

- [ ] **Step 3: Ensure `GuildStatCard.refresh_theme()` calls `get_theme_manager().design_tokens`**

Find `GuildStatCard.refresh_theme()`. If it sets any label styles with raw colors or `self.theme.*`, update all of them to use `dt = get_theme_manager().design_tokens` and the token map from Task 2 Step 13.

- [ ] **Step 4: Smoke-test**

```
pytest tests/test_gui_smoke.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add abuse/gui/pages/guilds.py
git commit -m "fix: remove inline hard-coded colors from Guilds page"
```

---

## Task 9: Sweep Nuker page

**Files:**
- Modify: `abuse/gui/pages/nuker.py`

- [ ] **Step 1: Find inline raw-color styling**

```
grep -n "setStyleSheet\|#[0-9A-Fa-f]\{6\}" abuse/gui/pages/nuker.py
```

- [ ] **Step 2: Update all status/label styling to use design tokens**

Same pattern as Task 8 Step 2. Pay special attention to:
- `self.target_name` label — should use `dt.text_primary`
- Any `stat_*` labels — should use `dt.text_secondary` / `dt.text_muted`
- `status_chip` tone calls — these are already token-based via `StatusChip`, verify they pass `"danger"` / `"warning"` / `"success"` (not raw colors)

- [ ] **Step 3: Verify `InfoBanner` is used for action feedback**

The `_update_status` method should be calling `self.status_banner.set_tone(...)` with one of the valid string tones (`"neutral"`, `"warning"`, `"danger"`, `"success"`), not setting raw `setStyleSheet`. If it does, update it.

- [ ] **Step 4: Smoke-test + commit**

```
pytest tests/test_gui_smoke.py -v
git add abuse/gui/pages/nuker.py
git commit -m "fix: remove inline hard-coded colors from Nuker page"
```

---

## Task 10: Sweep DM page

**Files:**
- Modify: `abuse/gui/pages/dm.py`

- [ ] **Step 1: Find inline raw-color styling**

```
grep -n "setStyleSheet\|#[0-9A-Fa-f]\{6\}" abuse/gui/pages/dm.py
```

- [ ] **Step 2: Update all styling to use design tokens**

Same pattern as Task 8 Step 2. Special attention to:
- `character_count` label — should use `dt.text_muted`
- `queue_count_label` — should use `dt.text_secondary`

Add `from ..theme import get_theme_manager` import if missing.

- [ ] **Step 3: Smoke-test + commit**

```
pytest tests/test_gui_smoke.py -v
git add abuse/gui/pages/dm.py
git commit -m "fix: remove inline hard-coded colors from DM page"
```

---

## Task 11: Sweep Logs page — map level colors to tokens

**Files:**
- Modify: `abuse/gui/pages/logs.py`

- [ ] **Step 1: Find the `LEVEL_COLORS` dict**

```
grep -n "LEVEL_COLORS\|#[0-9A-Fa-f]\{6\}" abuse/gui/pages/logs.py
```

Currently `LEVEL_COLORS` is a class-level dict with raw hex values:
```python
LEVEL_COLORS = {
    "DEBUG":    "#6D6F78",
    "INFO":     "#57F287",
    "WARNING":  "#FAA81A",
    "ERROR":    "#ED4245",
    "CRITICAL": "#FF6B6B",
}
```

- [ ] **Step 2: Replace `LEVEL_COLORS` with a token-based method**

Remove the class-level `LEVEL_COLORS` dict. Add a method `_level_color` that reads from `DesignTokens`:

```python
def _level_color(self, level: str) -> str:
    dt = get_theme_manager().design_tokens
    return {
        "DEBUG":    dt.text_disabled,
        "INFO":     dt.text_primary,
        "WARNING":  dt.warning,
        "ERROR":    dt.danger,
        "CRITICAL": dt.danger,
    }.get(level.upper(), dt.text_muted)
```

Add import at top:
```python
from ..theme import get_theme_manager
```

- [ ] **Step 3: Update all `LEVEL_COLORS` references to call `self._level_color(level)`**

Find every place that reads `self.LEVEL_COLORS.get(...)` or `LogsPage.LEVEL_COLORS` and replace with `self._level_color(level)`.

- [ ] **Step 4: Find and fix any other raw-color styling in logs.py**

```
grep -n "setStyleSheet\|#[0-9A-Fa-f]\{6\}" abuse/gui/pages/logs.py
```

Update the log text area background (likely `self.logs_view.setStyleSheet(...)`) to use `dt.background` for the background color and `dt.text_primary` for the base text color.

- [ ] **Step 5: Smoke-test + commit**

```
pytest tests/test_gui_smoke.py -v
git add abuse/gui/pages/logs.py
git commit -m "fix: map log level colors to DesignTokens instead of hard-coded hex"
```

---

## Task 12: Sweep Settings page — update theme picker to 4 curated themes

**Files:**
- Modify: `abuse/gui/pages/settings.py`

- [ ] **Step 1: Find where the theme preset list is populated**

```
grep -n "preset_combo\|get_preset_names\|get_available_themes\|theme_mode" abuse/gui/pages/settings.py
```

- [ ] **Step 2: Replace `get_preset_names()` call with curated list**

Find the line that populates `preset_combo` with theme names (likely `self.preset_combo.addItems(get_preset_names())` or similar). Replace with:

```python
from ..theme import get_preset_names  # already imported or add it

# Replace the addItems call:
self.preset_combo.addItems(["Midnight", "Obsidian", "Discord Dark", "Catppuccin Mocha"])
```

This ensures the picker only shows the 4 curated themes regardless of what `THEME_PRESETS` contains.

- [ ] **Step 3: Remove the theme-mode / light-dark filter control if present**

Search for any UI control that filters themes by "Dark" / "Light" / "Special" family:
```
grep -n "theme_mode\|theme_family\|LIGHT_THEME\|SPECIAL_THEME" abuse/gui/pages/settings.py
```

If such a control exists, remove it and its associated signal connection — all 4 curated themes are dark, no filtering needed.

- [ ] **Step 4: Find and fix remaining raw-color styling in settings.py**

```
grep -n "setStyleSheet\|#[0-9A-Fa-f]\{6\}" abuse/gui/pages/settings.py
```

Update any raw-color `setStyleSheet` calls using the token map from Task 2 Step 13.

- [ ] **Step 5: Smoke-test + commit**

```
pytest tests/test_gui_smoke.py -v
git add abuse/gui/pages/settings.py
git commit -m "fix: settings page — limit theme picker to 4 curated presets, remove inline colors"
```

---

## Task 13: Sweep Docs page

**Files:**
- Modify: `abuse/gui/pages/docs.py`

- [ ] **Step 1: Find inline raw-color styling**

```
grep -n "setStyleSheet\|#[0-9A-Fa-f]\{6\}" abuse/gui/pages/docs.py
```

- [ ] **Step 2: Update all styling to use design tokens**

Same pattern as Task 8 Step 2. The docs page likely has heading labels and code-block-style widgets styled with raw colors. Replace all with token equivalents:

```python
dt = get_theme_manager().design_tokens
heading.setStyleSheet(f"color: {dt.text_primary}; font-size: 15px; font-weight: 700;")
body.setStyleSheet(f"color: {dt.text_secondary}; font-size: 13px;")
code_block.setStyleSheet(f"background-color: {dt.surface}; color: {dt.text_primary}; border-radius: 6px; padding: 8px;")
```

- [ ] **Step 3: Final full test run**

```
pytest -v
```
Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add abuse/gui/pages/docs.py
git commit -m "fix: remove inline hard-coded colors from Docs page"
```

---

## Done

All tasks complete. The app now has:
- A semantic `DesignTokens` layer controlling all UI colors from a single source
- All components using `self.dt` exclusively — no raw hex or direct `Theme` field access
- 4 curated dark themes (Midnight, Obsidian, Discord Dark, Catppuccin Mocha)
- Sidebar: core tools at top, utility at bottom, collapsible to 56px icon mode
- Every page clean of inline hard-coded colors — switching theme affects 100% of the UI
