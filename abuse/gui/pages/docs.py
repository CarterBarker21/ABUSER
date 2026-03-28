"""Documentation page for the refactored GUI."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from ..components import AppButton, InfoBanner, PanelCard, SectionLabel
from ..theme import get_theme_manager
from .base import BasePage


class DocsPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Documentation",
            "A current in-app guide for the desktop UI, runtime state, and the parts of the surface that are intentionally preview-only.",
            eyebrow="Guide",
            parent=parent,
        )
        self.section_widgets: dict[str, QWidget] = {}
        self._body_labels: list[QLabel] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self.scroll_area, _, body_layout = self.create_scroll_body(max_width=1160)
        self.root_layout.addWidget(self.scroll_area, 1)

        top_grid = QGridLayout()
        top_grid.setContentsMargins(0, 0, 0, 0)
        top_grid.setHorizontalSpacing(self.tokens.metrics.spacing_lg)
        top_grid.setVerticalSpacing(self.tokens.metrics.spacing_lg)
        top_grid.setColumnStretch(0, 6)
        top_grid.setColumnStretch(1, 5)
        body_layout.addLayout(top_grid)

        self.build_notes = InfoBanner(
            "Current build notes",
            "Guild browsing, logs, settings, and connection state are live. DM delivery, local token scanning, and destructive actions are shown as honest preview surfaces instead of pretending to work.",
            tone="accent",
        )
        top_grid.addWidget(self.build_notes, 0, 0)

        nav_card = PanelCard("Quick Navigation", "Jump to the section you want without hunting through the scroll view.")
        nav_grid = QGridLayout()
        nav_grid.setHorizontalSpacing(self.tokens.metrics.spacing_sm)
        nav_grid.setVerticalSpacing(self.tokens.metrics.spacing_sm)
        nav_card.body_layout.addLayout(nav_grid)

        nav_items = [
            ("getting_started", "Getting Started"),
            ("page_map", "Page Map"),
            ("settings", "Settings"),
            ("runtime", "Runtime State"),
            ("safety", "Safety Notes"),
            ("faq", "FAQ"),
        ]

        for index, (key, label) in enumerate(nav_items):
            button = AppButton(label, "tertiary")
            button.clicked.connect(lambda _checked=False, target=key: self._jump_to(target))
            nav_grid.addWidget(button, index // 3, index % 3)

        top_grid.addWidget(nav_card, 0, 1)

        sections_grid = QGridLayout()
        sections_grid.setContentsMargins(0, 0, 0, 0)
        sections_grid.setHorizontalSpacing(self.tokens.metrics.spacing_lg)
        sections_grid.setVerticalSpacing(self.tokens.metrics.spacing_lg)
        sections_grid.setColumnStretch(0, 1)
        sections_grid.setColumnStretch(1, 1)
        body_layout.addLayout(sections_grid)

        cards = [
            self._build_section_card(
                "getting_started",
                "Getting Started",
                [
                    (
                        "Login flow",
                        "Paste a token manually or load a remembered session. Successful login routes directly to Guilds so runtime state appears in a meaningful view.",
                    ),
                    (
                        "Remembered sessions",
                        "Remembered sessions are local-only and controlled by the Privacy setting. The Login page reflects whether local saving is enabled before it offers to save anything.",
                    ),
                    (
                        "Connection lifecycle",
                        "Connect, wait for ready, inspect guilds/logs, then disconnect from the same card. The footer and page headers update from the same BotRunner state.",
                    ),
                ],
            ),
            self._build_section_card(
                "page_map",
                "Page Map",
                [
                    ("Docs", "The in-app guide and UI notes for the current build."),
                    ("Guilds", "Search the connected guild list, select a guild, and inspect server details."),
                    ("Nuker", "Preview grouped action categories and safety messaging. This build does not execute destructive actions."),
                    ("DM", "Compose drafts, review the local queue, and see which tools are preview-only."),
                    ("Logs", "Filter runtime logs by level and search text, then export them if needed."),
                    ("Settings", "Adjust theme preset, accent, font size, startup page, and privacy behavior."),
                ],
            ),
            self._build_section_card(
                "settings",
                "Settings",
                [
                    ("Live settings", "Theme preset, accent, font size, startup page, and local remembered-session saving apply to the actual UI."),
                    ("Preview settings", "Transparency, compact mode, tray behavior, auto-update, encryption, analytics, and sound effects remain visible but explicitly marked as preview-only."),
                    ("Search", "Search filters the settings surface itself instead of only jumping categories, so empty or unmatched states are obvious."),
                ],
            ),
            self._build_section_card(
                "runtime",
                "Runtime State",
                [
                    ("Single runtime source", "The window reads connection status, guild data, logs, and latency from BotRunner instead of mixing live state with direct bot references."),
                    ("Guild refresh", "Guild refresh requests go through BotRunner, and the footer server count comes from the same update path."),
                    ("Logs", "The log console keeps a structured record in memory and renders filtered output on demand, so the toolbar stays quiet and predictable."),
                ],
            ),
            self._build_section_card(
                "safety",
                "Safety Notes",
                [
                    ("Preview-only surfaces", "High-risk or unsupported controls stay visible so the interface remains complete, but they are disabled and labeled honestly."),
                    ("Manual token entry", "This build does not offer GUI-driven token scanning. Manual entry and local remembered sessions are the only surfaced session inputs."),
                    ("Local state", "Clear text and banners explain when data is stored locally and what parts of the app are only present as UI previews."),
                ],
            ),
            self._build_section_card(
                "faq",
                "FAQ",
                [
                    ("Why do some buttons stay disabled?", "They represent visible surfaces that are intentionally unavailable in this build. The UI now says that clearly instead of looking fully wired."),
                    ("What happens after login?", "The app routes to Guilds, updates the sidebar footer, and starts feeding logs and latency from BotRunner."),
                    ("Where do settings live?", "Appearance, behavior, notification, and privacy preferences are persisted in config/gui_config.json. Theme details persist in config/theme_config.json, and remembered sessions live in data/tokens.json."),
                ],
            ),
        ]

        for index, card in enumerate(cards):
            sections_grid.addWidget(card, index // 2, index % 2)

        body_layout.addStretch(1)

    def _build_section_card(
        self,
        key: str,
        title: str,
        rows: list[tuple[str, str]],
    ) -> PanelCard:
        card = PanelCard(title, tone="neutral")
        self.section_widgets[key] = card

        row_grid = QGridLayout()
        row_grid.setContentsMargins(0, 0, 0, 0)
        row_grid.setHorizontalSpacing(self.tokens.metrics.spacing_md)
        row_grid.setVerticalSpacing(self.tokens.metrics.spacing_sm)
        row_grid.setColumnStretch(0, 0)
        row_grid.setColumnStretch(1, 1)
        card.body_layout.addLayout(row_grid)

        for index, (item_title, item_text) in enumerate(rows):
            label = SectionLabel(item_title)
            body = QLabel(item_text)
            body.setWordWrap(True)
            self._body_labels.append(body)
            row_grid.addWidget(label, index, 0)
            row_grid.addWidget(body, index, 1)

        return card

    def _jump_to(self, key: str) -> None:
        target = self.section_widgets.get(key)
        if target:
            self.scroll_area.ensureWidgetVisible(target, 0, 32)

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens
        for label in self._body_labels:
            label.setStyleSheet(f"color: {dt.text_secondary}; font-size: 13px; line-height: 1.45em;")
