"""Compatibility exports for the refactored per-page modules."""

from __future__ import annotations

from .pages import (
    BasePage,
    BaseTab,
    DMPage,
    DMTab,
    DocsPage,
    DocsTab,
    GuildItem,
    GuildsPage,
    GuildsTab,
    LoginPage,
    LoginTab,
    LogsPage,
    LogsTab,
    NukerPage,
    NukerTab,
    SettingsPage,
    SettingsTab,
)

# Import TokenFinderThread from the new location
from .token_finder_thread import TokenFinderThread

__all__ = [
    "BasePage",
    "BaseTab",
    "GuildItem",
    "LoginPage",
    "LoginTab",
    "DocsPage",
    "DocsTab",
    "GuildsPage",
    "GuildsTab",
    "NukerPage",
    "NukerTab",
    "DMPage",
    "DMTab",
    "LogsPage",
    "LogsTab",
    "SettingsPage",
    "SettingsTab",
    "TokenFinderThread",
]
