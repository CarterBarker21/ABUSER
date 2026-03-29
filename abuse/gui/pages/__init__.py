"""Refactored page modules for the desktop GUI."""

from .base import BasePage, GuildItem
from .booster import BoosterPage
from .dm import DMPage
from .docs import DocsPage
from .guilds import GuildsPage
from .joiner import JoinerPage
from .login import LoginPage
from .logs import LogsPage
from .nuker import NukerPage
from .settings import SettingsPage

LoginTab = LoginPage
DocsTab = DocsPage
GuildsTab = GuildsPage
NukerTab = NukerPage
DMTab = DMPage
LogsTab = LogsPage
SettingsTab = SettingsPage
BaseTab = BasePage

__all__ = [
    "BasePage",
    "BaseTab",
    "BoosterPage",
    "GuildItem",
    "JoinerPage",
    "LoginPage",
    "DocsPage",
    "GuildsPage",
    "NukerPage",
    "DMPage",
    "LogsPage",
    "SettingsPage",
    "LoginTab",
    "DocsTab",
    "GuildsTab",
    "NukerTab",
    "DMTab",
    "LogsTab",
    "SettingsTab",
]
