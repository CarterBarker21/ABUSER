"""Base page classes for the refactored GUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from ..components import PageHeader, refresh_themed_tree
from ..theme import get_theme_manager


@dataclass
class GuildItem:
    guild_id: int
    name: str
    member_count: int = 0
    icon_url: Optional[str] = None
    owner_id: Optional[int] = None
    created_at: Optional[datetime] = None
    channels_count: int = 0
    roles_count: int = 0
    boost_count: int = 0
    my_permissions: int = 0  # The bot's permissions in this guild
    is_owner: bool = False  # True if bot is the server owner
    icon_data: Optional[bytes] = None  # Raw icon image bytes

    @property
    def id(self) -> int:
        return self.guild_id


class BasePage(QWidget):
    """Common page shell with a consistent header and margins."""

    def __init__(self, title: str, description: str = "", eyebrow: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.tokens = self.theme_manager.tokens

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(
            self.tokens.metrics.spacing_lg,
            self.tokens.metrics.spacing_lg,
            self.tokens.metrics.spacing_lg,
            self.tokens.metrics.spacing_lg,
        )
        self.root_layout.setSpacing(self.tokens.metrics.spacing_lg)

        self.header = PageHeader(title, description, eyebrow)
        self.root_layout.addWidget(self.header)

    @property
    def theme(self):
        return self.theme_manager.theme

    def create_scroll_body(self, max_width: Optional[int] = None) -> tuple[QScrollArea, QWidget, QVBoxLayout]:
        max_width = max_width or self.tokens.metrics.content_max_width

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        wrapper_layout.addStretch(1)

        body = QWidget()
        body.setMaximumWidth(max_width)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(self.tokens.metrics.spacing_lg)

        wrapper_layout.addWidget(body)
        wrapper_layout.addStretch(1)

        scroll.setWidget(wrapper)
        return scroll, body, body_layout

    def refresh_theme(self) -> None:
        self.tokens = self.theme_manager.tokens
        self.header.refresh_theme()
        refresh_themed_tree(self)
