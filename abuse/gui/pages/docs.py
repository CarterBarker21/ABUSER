"""Documentation page — two-column layout with category navigation."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..components import InfoBanner, rgba, blend
from ..theme import get_theme_manager
from .base import BasePage


SECTIONS: list[dict] = [
    {
        "key": "getting_started",
        "label": "Getting Started",
        "icon": "→",
        "entries": [
            (
                "Login flow",
                "Paste a token manually or load a remembered session. "
                "Successful login routes directly to Guilds so runtime state appears in a meaningful view.",
            ),
            (
                "Remembered sessions",
                "Remembered sessions are local-only and controlled by the Privacy setting. "
                "The Login page reflects whether local saving is enabled before it offers to save anything.",
            ),
            (
                "Connection lifecycle",
                "Connect, wait for ready, inspect guilds/logs, then disconnect from the same card. "
                "The footer and page headers update from the same BotRunner state.",
            ),
        ],
    },
    {
        "key": "commands",
        "label": "Commands",
        "icon": "⌘",
        "entries": [
            (
                "Command Prefix",
                "All commands use the dot prefix (.). Example: .ping, .help, .afk"
            ),
            (
                "Getting Help",
                "Use .help to see all command categories. Use .help <category> to see commands in a specific category."
            ),
            (
                "Rate Limiting",
                "Commands have built-in rate limits to prevent abuse and avoid Discord API bans. "
                "Cooldowns are shown per command and vary from 3-10 seconds."
            ),
        ],
    },
    {
        "key": "page_map",
        "label": "Page Map",
        "icon": "→",
        "entries": [
            ("Login",    "Connect, disconnect, and manage remembered sessions."),
            ("Guilds",   "Browse connected guilds, inspect stats, and search by name."),
            ("Nuker",    "Grouped action surfaces with safety gating and a quick-setup card."),
            ("DM",       "Compose drafts, manage a local queue, and review secondary tools."),
            ("Joiner",   "Auto-join servers via invite links — bot logic not yet wired."),
            ("Booster",  "Apply Nitro boosts to servers — bot logic not yet wired."),
            ("Logs",     "Filter runtime logs by level and search text; export on demand."),
            ("Settings", "Theme preset, accent, font size, startup page, and privacy behaviour."),
            ("Docs",     "This in-app guide. Always reflects the current build state."),
        ],
    },
    {
        "key": "settings",
        "label": "Settings",
        "icon": "→",
        "entries": [
            (
                "Live settings",
                "Theme preset, accent, font size, startup page, and local session saving "
                "apply to the actual running UI.",
            ),
            (
                "Preview settings",
                "Transparency, compact mode, tray behaviour, auto-update, encryption, "
                "analytics, and sound effects remain visible but explicitly marked preview-only.",
            ),
            (
                "Search",
                "The search field filters the settings surface itself — empty or unmatched states "
                "are clearly shown rather than hiding categories silently.",
            ),
        ],
    },
    {
        "key": "runtime",
        "label": "Runtime State",
        "icon": "→",
        "entries": [
            (
                "Single runtime source",
                "The window reads connection status, guild data, logs, and latency from BotRunner "
                "instead of mixing live state with direct bot references.",
            ),
            (
                "Guild refresh",
                "Guild refresh requests go through BotRunner; the sidebar server count "
                "comes from the same update path.",
            ),
            (
                "Logs",
                "The log console keeps a structured record in memory and renders filtered output "
                "on demand, so the toolbar stays quiet and predictable.",
            ),
        ],
    },
    {
        "key": "safety",
        "label": "Safety Notes",
        "icon": "→",
        "entries": [
            (
                "Preview-only surfaces",
                "High-risk or unsupported controls stay visible so the interface remains complete, "
                "but they are disabled and labelled honestly.",
            ),
            (
                "Manual token entry",
                "This build does not offer GUI-driven token scanning. "
                "Manual entry and local remembered sessions are the only surfaced session inputs.",
            ),
            (
                "Local state",
                "Clear text and banners explain when data is stored locally and what parts "
                "of the app are only present as UI previews.",
            ),
        ],
    },
    {
        "key": "faq",
        "label": "FAQ",
        "icon": "→",
        "entries": [
            (
                "Why do some buttons stay disabled?",
                "They represent surfaces that are intentionally unavailable in this build. "
                "The UI says that clearly instead of looking fully wired.",
            ),
            (
                "What happens after login?",
                "The app routes to Guilds, updates the sidebar footer, and starts feeding "
                "logs and latency from BotRunner.",
            ),
            (
                "Where do settings live?",
                "Appearance, behaviour, notification, and privacy preferences are persisted in "
                "config/gui_config.json. Theme details live in config/theme_config.json, "
                "and remembered sessions in data/tokens.json.",
            ),
            (
                "What is the status panel in the sidebar?",
                "It shows connection state, the logged-in username, guild count, and latency — "
                "all sourced from BotRunner and updated in real-time.",
            ),
        ],
    },
]


COMMAND_CATEGORIES: list[dict] = [
    {
        "name": "Utility",
        "icon": "ℹ️",
        "commands": [
            {
                "name": "help",
                "aliases": ["h", "commands"],
                "syntax": ".help [category]",
                "description": "Show help message with command categories or specific category commands.",
                "example": ".help moderation",
                "cooldown": "5 uses per 10 seconds",
            },
            {
                "name": "ping",
                "aliases": ["pong", "latency"],
                "syntax": ".ping",
                "description": "Check bot latency, response time, and uptime. Shows WebSocket latency and round-trip time.",
                "example": ".ping",
                "cooldown": "3 uses per 5 seconds",
            },
        ],
    },
    {
        "name": "Admin",
        "icon": "⚙️",
        "commands": [
            {
                "name": "serverinfo",
                "aliases": ["guildinfo", "si", "server"],
                "syntax": ".serverinfo",
                "description": "Display detailed server information including owner, creation date, members, channels, roles, boosts, and features.",
                "example": ".serverinfo",
                "cooldown": "3 uses per 5 seconds",
            },
        ],
    },
    {
        "name": "Fun",
        "icon": "🎮",
        "commands": [
            {
                "name": "8ball",
                "aliases": ["eightball", "8b"],
                "syntax": ".8ball <question>",
                "description": "Ask the magic 8-ball a question. Returns one of 20 possible responses (positive, neutral, or negative).",
                "example": ".8ball Will I win the lottery?",
                "cooldown": "5 uses per 10 seconds",
            },
        ],
    },
    {
        "name": "Moderation",
        "icon": "🛡️",
        "commands": [
            {
                "name": "purge",
                "aliases": ["clear", "clean"],
                "syntax": ".purge [amount]",
                "description": "Delete multiple messages from the channel. Requires Manage Messages permission. Default: 10, Max: 100.",
                "example": ".purge 50",
                "cooldown": "1 use per 10 seconds per channel",
                "permissions": "Manage Messages",
            },
        ],
    },
    {
        "name": "Automation",
        "icon": "🤖",
        "commands": [
            {
                "name": "afk",
                "aliases": [],
                "syntax": ".afk [reason]",
                "description": "Set your AFK status. When someone mentions you, they'll see your AFK message. Use .afk off/back to remove.",
                "example": ".afk Going to eat dinner",
                "cooldown": "3 uses per 10 seconds",
            },
        ],
    },
    {
        "name": "Web",
        "icon": "🌐",
        "commands": [
            {
                "name": "btc",
                "aliases": ["bitcoin"],
                "syntax": ".btc",
                "description": "Check current Bitcoin price in USD and EUR with 24h change percentage. Data from CoinGecko.",
                "example": ".btc",
                "cooldown": "3 uses per 15 seconds",
            },
            {
                "name": "eth",
                "aliases": ["ethereum"],
                "syntax": ".eth",
                "description": "Check current Ethereum price in USD and EUR with 24h change percentage. Data from CoinGecko.",
                "example": ".eth",
                "cooldown": "3 uses per 15 seconds",
            },
        ],
    },
    {
        "name": "Sniper",
        "icon": "🎯",
        "commands": [
            {
                "name": "snipe",
                "aliases": [],
                "syntax": ".snipe | .snipe nitro",
                "description": "Check sniper status or toggle Nitro sniper. Automatically detects and claims discord.gift codes when enabled.",
                "example": ".snipe nitro",
                "cooldown": "2 uses per 5 seconds",
            },
        ],
    },
]


class _NavItem(QWidget):
    """Single clickable item in the left category nav."""

    def __init__(self, label: str, callback, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._active = False
        self._callback = callback
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("docNavItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        self._label = QLabel(label)
        self._label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self._label, 1)

        self.refresh_theme()

    def set_active(self, active: bool) -> None:
        self._active = active
        self.refresh_theme()

    def mousePressEvent(self, event) -> None:
        self._callback()
        super().mousePressEvent(event)

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens
        if self._active:
            text = dt.accent
            font_weight = "600"
        else:
            text = dt.text_secondary
            font_weight = "500"

        self._label.setStyleSheet(
            f"color: {text}; font-weight: {font_weight}; background: transparent;"
        )


class _EntryRow(QWidget):
    """A single term + description row inside a section."""

    def __init__(self, term: str, description: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("docEntry")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._term = QLabel(term)
        font = QFont("Segoe UI", 12)
        font.setWeight(QFont.Weight.DemiBold)
        self._term.setFont(font)
        layout.addWidget(self._term)

        self._desc = QLabel(description)
        self._desc.setWordWrap(True)
        self._desc.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self._desc)

        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens
        self._term.setStyleSheet(f"color: {dt.text_primary}; background: transparent;")
        self._desc.setStyleSheet(
            f"color: {dt.text_secondary}; line-height: 1.5; background: transparent;"
        )


class _SectionCard(QFrame):
    """One full documentation section rendered as a styled card."""

    def __init__(self, section: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._section = section
        self.setObjectName("docSectionCard")
        self._entry_rows: list[_EntryRow] = []
        self._build()

    def _build(self) -> None:
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setObjectName("docSectionHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(12)

        accent_bar = QLabel()
        accent_bar.setObjectName("docAccentBar")
        accent_bar.setFixedWidth(4)
        accent_bar.setMinimumHeight(24)
        header_layout.addWidget(accent_bar)

        title = QLabel(self._section["label"])
        font = QFont("Segoe UI", 15)
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        title.setObjectName("docSectionTitle")
        header_layout.addWidget(title, 1)

        outer.addWidget(header)

        entries_widget = QWidget()
        entries_widget.setObjectName("docEntriesContainer")
        entries_layout = QVBoxLayout(entries_widget)
        entries_layout.setContentsMargins(20, 8, 20, 20)
        entries_layout.setSpacing(0)

        for i, (term, desc) in enumerate(self._section["entries"]):
            if i > 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setObjectName("docEntrySep")
                sep.setFixedHeight(1)
                entries_layout.addWidget(sep)
            row = _EntryRow(term, desc)
            row.setContentsMargins(0, 14, 0, 14)
            self._entry_rows.append(row)
            entries_layout.addWidget(row)

        outer.addWidget(entries_widget)
        
        self._header = header
        self._title = title
        self._accent_bar = accent_bar

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens

        self.setStyleSheet(f"""
            QFrame#docSectionCard {{
                background-color: {blend(dt.surface, dt.background, 0.05)};
                border: 1px solid {rgba(dt.border_strong, 0.6)};
                border-radius: 16px;
            }}
            QFrame#docSectionCard:hover {{
                border-color: {rgba(dt.border_strong, 0.8)};
            }}
        """)
        
        self._accent_bar.setStyleSheet(
            f"background-color: {dt.accent}; border-radius: 2px;"
        )
        self._title.setStyleSheet(f"color: {dt.text_primary}; background: transparent;")
        
        for sep in self.findChildren(QFrame):
            if sep.objectName() == "docEntrySep":
                sep.setStyleSheet(
                    f"QFrame {{ background-color: {rgba(dt.border_strong, 0.25)}; border: none; }}"
                )
        for row in self._entry_rows:
            row.refresh_theme()


class _CommandCard(QFrame):
    """A card displaying a single command with syntax, description, and details."""

    def __init__(self, command: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._command = command
        self.setObjectName("commandCard")
        self._build()

    def _build(self) -> None:
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)

        name_label = QLabel(f".{self._command['name']}")
        name_font = QFont("Consolas", 13)
        name_font.setWeight(QFont.Weight.Bold)
        name_label.setFont(name_font)
        header.addWidget(name_label)

        if self._command.get('aliases'):
            aliases_text = f"({', '.join(self._command['aliases'][:3])})"
            aliases_label = QLabel(aliases_text)
            aliases_font = QFont("Consolas", 10)
            aliases_label.setFont(aliases_font)
            header.addWidget(aliases_label)

        header.addStretch(1)
        layout.addLayout(header)

        syntax_label = QLabel(f"Syntax: {self._command['syntax']}")
        syntax_font = QFont("Consolas", 11)
        syntax_label.setFont(syntax_font)
        layout.addWidget(syntax_label)

        divider = QFrame()
        divider.setObjectName("commandDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        desc_label = QLabel(self._command['description'])
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(desc_label)

        example_label = QLabel(f"Example: {self._command['example']}")
        example_font = QFont("Consolas", 10)
        example_label.setFont(example_font)
        layout.addWidget(example_label)

        footer = QHBoxLayout()
        footer.setSpacing(12)

        cooldown_text = f"⏱ {self._command['cooldown']}"
        cooldown_label = QLabel(cooldown_text)
        cooldown_label.setFont(QFont("Segoe UI", 10))
        footer.addWidget(cooldown_label)

        if self._command.get('permissions'):
            perm_text = f"🔒 {self._command['permissions']}"
            perm_label = QLabel(perm_text)
            perm_font = QFont("Segoe UI", 10)
            perm_label.setFont(perm_font)
            footer.addWidget(perm_label)

        footer.addStretch(1)
        layout.addLayout(footer)

        self._name_label = name_label
        self._aliases_label = aliases_label if self._command.get('aliases') else None
        self._syntax_label = syntax_label
        self._desc_label = desc_label
        self._example_label = example_label
        self._cooldown_label = cooldown_label
        self._perm_label = footer.itemAt(1).widget() if self._command.get('permissions') and footer.count() > 1 else None
        self._divider = divider

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens

        self.setStyleSheet(f"""
            QFrame#commandCard {{
                background-color: {blend(dt.surface, dt.background, 0.05)};
                border: 1px solid {rgba(dt.border_strong, 0.5)};
                border-radius: 12px;
            }}
            QFrame#commandCard:hover {{
                border-color: {rgba(dt.accent, 0.4)};
            }}
        """)

        self._name_label.setStyleSheet(f"color: {dt.accent}; background: transparent;")
        
        if self._aliases_label:
            self._aliases_label.setStyleSheet(f"color: {dt.text_muted}; background: transparent;")

        self._syntax_label.setStyleSheet(f"color: {dt.text_secondary}; background: transparent;")
        self._desc_label.setStyleSheet(f"color: {dt.text_primary}; background: transparent;")
        self._example_label.setStyleSheet(f"color: {dt.accent}; background: transparent;")
        self._cooldown_label.setStyleSheet(f"color: {dt.text_muted}; background: transparent;")
        
        if self._perm_label:
            self._perm_label.setStyleSheet(f"color: {dt.warning}; background: transparent;")

        self._divider.setStyleSheet(
            f"QFrame {{ background-color: {rgba(dt.border_strong, 0.2)}; border: none; }}"
        )


class _CommandCategoryCard(QFrame):
    """A card containing all commands in a category."""

    def __init__(self, category: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._category = category
        self.setObjectName("commandCategoryCard")
        self._command_cards: list[_CommandCard] = []
        self._build()

    def _build(self) -> None:
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setObjectName("cmdCategoryHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(12)

        accent_bar = QLabel()
        accent_bar.setObjectName("cmdCategoryAccentBar")
        accent_bar.setFixedWidth(4)
        accent_bar.setMinimumHeight(24)
        header_layout.addWidget(accent_bar)

        title_text = f"{self._category['icon']} {self._category['name']}"
        title = QLabel(title_text)
        font = QFont("Segoe UI", 15)
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        title.setObjectName("cmdCategoryTitle")
        header_layout.addWidget(title, 1)

        outer.addWidget(header)

        commands_widget = QWidget()
        commands_widget.setObjectName("commandsContainer")
        commands_layout = QVBoxLayout(commands_widget)
        commands_layout.setContentsMargins(16, 8, 16, 16)
        commands_layout.setSpacing(12)

        for cmd in self._category['commands']:
            card = _CommandCard(cmd)
            self._command_cards.append(card)
            commands_layout.addWidget(card)

        outer.addWidget(commands_widget)
        
        self._header = header
        self._title = title
        self._accent_bar = accent_bar

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens

        self.setStyleSheet(f"""
            QFrame#commandCategoryCard {{
                background-color: {blend(dt.surface, dt.background, 0.05)};
                border: 1px solid {rgba(dt.border_strong, 0.6)};
                border-radius: 16px;
            }}
            QFrame#commandCategoryCard:hover {{
                border-color: {rgba(dt.border_strong, 0.8)};
            }}
        """)

        self._accent_bar.setStyleSheet(
            f"background-color: {dt.accent}; border-radius: 2px;"
        )
        self._title.setStyleSheet(f"color: {dt.text_primary}; background: transparent;")

        for card in self._command_cards:
            card.refresh_theme()


class DocsPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Documentation",
            "",
            eyebrow="Guide",
            parent=parent,
        )
        self.root_layout.removeWidget(self.header)
        self.header.hide()

        self._nav_items: dict[str, _NavItem] = {}
        self._section_cards: dict[str, _SectionCard] = {}
        self._command_category_cards: list[_CommandCategoryCard] = []
        self._active_key: str = SECTIONS[0]["key"]
        self._build_ui()

    def _build_ui(self) -> None:
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(0)
        self.root_layout.addLayout(container, 1)

        # Left nav panel
        self._nav_panel = QFrame()
        self._nav_panel.setObjectName("docNavPanel")
        self._nav_panel.setFixedWidth(200)
        self._nav_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        nav_layout = QVBoxLayout(self._nav_panel)
        nav_layout.setContentsMargins(12, 20, 12, 16)
        nav_layout.setSpacing(4)

        nav_heading = QLabel("DOCS")
        nav_heading.setObjectName("docNavHeading")
        nav_layout.addWidget(nav_heading)
        nav_layout.addSpacing(8)
        self._nav_heading = nav_heading

        for section in SECTIONS:
            key = section["key"]
            item = _NavItem(
                section["label"],
                callback=lambda k=key: self._jump_to(k),
            )
            nav_layout.addWidget(item)
            self._nav_items[key] = item

        nav_layout.addStretch(1)
        container.addWidget(self._nav_panel)

        # Vertical divider
        self._nav_divider = QFrame()
        self._nav_divider.setObjectName("docNavDivider")
        self._nav_divider.setFrameShape(QFrame.Shape.VLine)
        self._nav_divider.setFixedWidth(1)
        container.addWidget(self._nav_divider)

        # Content scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container.addWidget(self._scroll, 1)

        self._content_widget = QWidget()
        self._content_widget.setObjectName("docContent")
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        self._banner = InfoBanner(
            "Current build — v1.5",
            "Guild browsing, logs, settings, and connection state are live. "
            "DM delivery, Joiner, Booster, and destructive actions are honest preview surfaces.",
            tone="accent",
        )
        content_layout.addWidget(self._banner)

        for section in SECTIONS:
            if section["key"] == "commands":
                card = _SectionCard(section)
                self._section_cards[section["key"]] = card
                content_layout.addWidget(card)
                
                for category in COMMAND_CATEGORIES:
                    cat_card = _CommandCategoryCard(category)
                    self._command_category_cards.append(cat_card)
                    content_layout.addWidget(cat_card)
            else:
                card = _SectionCard(section)
                self._section_cards[section["key"]] = card
                content_layout.addWidget(card)

        content_layout.addStretch(1)
        self._scroll.setWidget(self._content_widget)

        self._set_active(self._active_key)
        self.refresh_theme()

    def _set_active(self, key: str) -> None:
        self._active_key = key
        for k, item in self._nav_items.items():
            item.set_active(k == key)

    def _jump_to(self, key: str) -> None:
        self._set_active(key)
        target = self._section_cards.get(key)
        if target:
            self._scroll.ensureWidgetVisible(target, 0, 16)

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens
        tm = get_theme_manager().theme

        self._nav_panel.setStyleSheet(
            f"""
            QFrame#docNavPanel {{
                background-color: transparent;
                border: none;
            }}
            """
        )
        self._nav_divider.setStyleSheet(
            f"QFrame#docNavDivider {{ background-color: {rgba(dt.border_strong, 0.5)}; border: none; }}"
        )
        self._nav_heading.setStyleSheet(
            f"color: {dt.text_muted}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 1.5px; background: transparent;"
        )
        
        self._content_widget.setStyleSheet(
            f"QWidget#docContent {{ background-color: {tm.bg_primary}; }}"
        )
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {tm.bg_primary}; border: none; }}"
        )

        for item in self._nav_items.values():
            item.refresh_theme()

        for card in self._section_cards.values():
            card.refresh_theme()

        for card in self._command_category_cards:
            card.refresh_theme()
