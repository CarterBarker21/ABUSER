"""Settings page with live and preview sections."""

from __future__ import annotations

from copy import deepcopy
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..components import (
    AppButton,
    AppComboBox,
    AppSpinBox,
    InfoBanner,
    PanelCard,
    SearchField,
    StatusChip,
    ToggleSwitch,
    rgba,
    blend,
)
from ..config import DEFAULT_GUI_CONFIG, clear_remembered_sessions, load_gui_config
from ..routes import ROUTE_LABELS, STARTUP_OPTIONS
from ..theme import get_theme_manager
from .base import BasePage


class SettingRowWidget(QWidget):
    """A single setting row with title, description, control, and optional preview chip."""

    def __init__(
        self,
        title: str,
        description: str,
        control: QWidget,
        keywords: tuple[str, ...] = (),
        preview: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._search_text = " ".join((title, description, *keywords)).lower()
        self._preview = preview

        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(20)

        # Text column
        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(6)
        layout.addLayout(text_column, 1)

        # Title row with chip
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(10)
        text_column.addLayout(title_row)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("settingTitle")
        title_row.addWidget(self.title_label)

        if preview:
            self.preview_chip = StatusChip("Preview", "preview")
            self.preview_chip.setFixedHeight(20)
            title_row.addWidget(self.preview_chip)
        else:
            self.preview_chip = None
        title_row.addStretch(1)

        # Description
        self.description_label = QLabel(description)
        self.description_label.setObjectName("settingDescription")
        self.description_label.setWordWrap(True)
        text_column.addWidget(self.description_label)

        # Control
        self.control = control
        control.setMinimumWidth(140)
        layout.addWidget(control, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def matches(self, query: str) -> bool:
        if not query:
            return True
        return query in self._search_text

    def refresh_theme(self, colors=None) -> None:
        if colors is None:
            from ..theme import get_theme_manager
            colors = get_theme_manager().theme
        
        self.title_label.setStyleSheet(
            f"color: {colors.text_primary}; font-weight: 600; font-size: 14px; letter-spacing: 0.2px;"
        )
        self.description_label.setStyleSheet(
            f"color: {colors.text_secondary}; font-size: 12px; line-height: 1.5;"
        )
        if self.preview_chip:
            self.preview_chip.refresh_theme()


class SettingsCard(PanelCard):
    """A card containing multiple setting rows."""

    def __init__(self, title: str, description: str, parent: Optional[QWidget] = None):
        self.rows: list[SettingRowWidget] = []
        super().__init__(title, description, parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def add_row(self, row: SettingRowWidget) -> None:
        """Add a setting row to this card."""
        self.rows.append(row)
        self.body_layout.addWidget(row)
        
        # Add divider if not the first row
        if len(self.rows) > 1:
            divider = QFrame()
            divider.setObjectName("rowDivider")
            divider.setFixedHeight(1)
            self.body_layout.addWidget(divider)

    def apply_search(self, query: str) -> bool:
        any_match = False
        for row in self.rows:
            match = row.matches(query)
            row.setVisible(match)
            any_match = any_match or match
        self.setVisible(any_match or not query)
        return any_match

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens
        
        # Card styling with depth
        self.setStyleSheet(f"""
            QWidget#panelCard {{
                background-color: {blend(dt.surface, dt.background, 0.05)};
                border: 1px solid {rgba(dt.border_strong, 0.6)};
                border-radius: 16px;
            }}
            QWidget#panelCard:hover {{
                border-color: {rgba(dt.border_strong, 0.8)};
            }}
            QFrame#rowDivider {{
                background-color: {rgba(dt.border, 0.5)};
                border: none;
                max-height: 1px;
            }}
        """)
        
        for row in self.rows:
            row.refresh_theme()


class SearchEmptyState(QWidget):
    """Empty state shown when search returns no results."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Icon container
        icon_container = QWidget()
        icon_container.setFixedSize(80, 80)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("🔍")
        self.icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.icon_label)
        
        layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        self.title_label = QLabel("No settings found")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Description
        self.desc_label = QLabel("Try adjusting your search terms or browse by category")
        self.desc_label.setStyleSheet("font-size: 13px;")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.desc_label)

        layout.addStretch(1)

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens
        self.title_label.setStyleSheet(f"color: {dt.text_primary}; font-size: 18px; font-weight: 700;")
        self.desc_label.setStyleSheet(f"color: {dt.text_secondary}; font-size: 13px;")


class SettingsPage(BasePage):
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Settings",
            "Configure appearance, behavior, and privacy preferences",
            eyebrow="Preferences",
            parent=parent,
        )
        # Remove the header to match other tabs
        self.root_layout.removeWidget(self.header)
        self.header.hide()

        self._config = deepcopy(DEFAULT_GUI_CONFIG)
        self._original_config = deepcopy(DEFAULT_GUI_CONFIG)
        self._category_cards: dict[str, list[SettingsCard]] = {}
        self._build_ui()
        self.load_from_config(load_gui_config())

    def _build_ui(self) -> None:
        # Search bar
        self.search_input = SearchField("Search settings...")
        self.search_input.setMinimumHeight(44)
        self.search_input.textChanged.connect(self._apply_search)
        self.root_layout.addWidget(self.search_input)

        # Main content area
        main_row = QHBoxLayout()
        main_row.setSpacing(20)
        self.root_layout.addLayout(main_row, 1)

        # Category sidebar
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(200)
        self.category_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        main_row.addWidget(self.category_list)

        # Content stack
        self.content_stack = QStackedWidget()
        main_row.addWidget(self.content_stack, 1)

        # Empty state for search
        self.search_empty = SearchEmptyState()

        # Build category pages
        self._add_category("Appearance", self._build_appearance_page())
        self._add_category("Behavior", self._build_behavior_page())
        self._add_category("Notifications", self._build_notifications_page())
        self._add_category("Privacy", self._build_privacy_page())
        self._add_category("About", self._build_about_page())
        self.content_stack.addWidget(self.search_empty)

        # Action buttons
        actions = QHBoxLayout()
        actions.setSpacing(12)
        actions.addStretch(1)

        reset_button = AppButton("Reset Defaults", "secondary")
        reset_button.setMinimumWidth(120)
        reset_button.clicked.connect(self._reset_to_defaults)
        actions.addWidget(reset_button)

        cancel_button = AppButton("Cancel", "tertiary")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(self._restore_original)
        actions.addWidget(cancel_button)

        apply_button = AppButton("Apply Changes", "primary")
        apply_button.setMinimumWidth(140)
        apply_button.clicked.connect(self._apply_changes)
        actions.addWidget(apply_button)

        self.root_layout.addLayout(actions)
        self.category_list.setCurrentRow(0)
        self.refresh_theme()

    def _add_category(self, name: str, page: QWidget) -> None:
        item = QListWidgetItem(name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.category_list.addItem(item)
        self.content_stack.addWidget(page)

    def _page_scroll(self, content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    def _register_cards(self, category: str, *cards: SettingsCard) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self._category_cards[category] = list(cards)
        for card in cards:
            layout.addWidget(card)
        layout.addStretch(1)
        return self._page_scroll(container)

    def _build_appearance_page(self) -> QWidget:
        card = SettingsCard("Appearance", "Customize the visual style of the application")

        self.preset_combo = AppComboBox()
        self.preset_combo.addItems([
            "Midnight", "Discord Dark", "Tokyo Night", "Catppuccin Mocha", "Dracula",
        ])
        card.add_row(
            SettingRowWidget(
                "Theme preset",
                "Choose a color scheme that matches your preference",
                self.preset_combo,
                keywords=("preset", "theme", "accent", "color"),
            )
        )

        self.accent_combo = AppComboBox()
        self.accent_combo.addItems(["Blurple", "Red", "Green", "Pink", "Cyan"])
        card.add_row(
            SettingRowWidget(
                "Accent color",
                "Primary color used for buttons, links, and highlights",
                self.accent_combo,
                keywords=("accent", "color", "primary"),
            )
        )

        self.font_size_spin = AppSpinBox()
        self.font_size_spin.setRange(11, 18)
        card.add_row(
            SettingRowWidget(
                "Font size",
                "Adjust the base font size throughout the interface",
                self.font_size_spin,
                keywords=("font", "text", "size", "scale"),
            )
        )

        self.startup_combo = AppComboBox()
        self.startup_combo.addItems(STARTUP_OPTIONS)
        card.add_row(
            SettingRowWidget(
                "Startup page",
                "Page to show when the application launches",
                self.startup_combo,
                keywords=("startup", "launch", "page", "home"),
            )
        )

        # Preview card for future features
        preview_card = SettingsCard("Coming Soon", "Features planned for future releases")
        
        self.animations_toggle = ToggleSwitch("Animations")
        self.animations_toggle.setEnabled(False)
        preview_card.add_row(
            SettingRowWidget(
                "Animations",
                "Smooth transitions and micro-interactions (Preview)",
                self.animations_toggle,
                preview=True,
                keywords=("animation", "motion", "transition"),
            )
        )
        
        self.transparency_toggle = ToggleSwitch("Transparency effects")
        self.transparency_toggle.setEnabled(False)
        preview_card.add_row(
            SettingRowWidget(
                "Transparency effects",
                "Glassmorphism and blur effects (Preview)",
                self.transparency_toggle,
                preview=True,
                keywords=("opacity", "transparency", "blur", "glass"),
            )
        )

        return self._register_cards("Appearance", card, preview_card)

    def _build_behavior_page(self) -> QWidget:
        card = SettingsCard("Behavior", "Application behavior and interaction preferences")

        for title, text, keywords in (
            ("Confirm destructive actions", "Show confirmation dialogs before destructive operations (Preview)", ("confirm", "dialog", "destructive")),
            ("Log commands", "Record command history to log file (Preview)", ("commands", "logging", "history")),
            ("Minimize to tray", "Keep running in system tray when window closed (Preview)", ("tray", "minimize", "background")),
            ("Auto-start bot", "Automatically connect bot on application startup (Preview)", ("auto", "start", "connect")),
            ("Check for updates", "Automatically check for new versions (Preview)", ("update", "check", "version")),
        ):
            toggle = ToggleSwitch(title)
            toggle.setEnabled(False)
            card.add_row(SettingRowWidget(title, text, toggle, preview=True, keywords=keywords))

        return self._register_cards("Behavior", card)

    def _build_notifications_page(self) -> QWidget:
        card = SettingsCard("Notifications", "Desktop notification and alert preferences")
        
        for title, text in (
            ("Error notifications", "Show desktop notifications for errors (Preview)"),
            ("Success notifications", "Show desktop notifications for successful operations (Preview)"),
            ("Update notifications", "Notify when updates are available (Preview)"),
            ("Sound effects", "Play audio cues for important events (Preview)"),
        ):
            toggle = ToggleSwitch(title)
            toggle.setEnabled(False)
            card.add_row(SettingRowWidget(title, text, toggle, preview=True, keywords=(title.lower(),)))
            
        return self._register_cards("Notifications", card)

    def _build_privacy_page(self) -> QWidget:
        card = SettingsCard("Privacy", "Data storage and privacy settings")

        self.save_tokens_toggle = ToggleSwitch("Allow remembered sessions")
        card.add_row(
            SettingRowWidget(
                "Remembered sessions",
                "Save login sessions locally for quick reconnection",
                self.save_tokens_toggle,
                keywords=("token", "session", "remembered", "privacy", "save"),
            )
        )

        self.encrypt_tokens_toggle = ToggleSwitch("Encrypt remembered sessions")
        self.encrypt_tokens_toggle.setEnabled(False)
        card.add_row(
            SettingRowWidget(
                "Session encryption",
                "Encrypt saved sessions with a password (Preview)",
                self.encrypt_tokens_toggle,
                preview=True,
                keywords=("encrypt", "token", "privacy", "security"),
            )
        )

        self.analytics_toggle = ToggleSwitch("Anonymous analytics")
        self.analytics_toggle.setEnabled(False)
        card.add_row(
            SettingRowWidget(
                "Usage analytics",
                "Send anonymous usage data to improve the app (Preview)",
                self.analytics_toggle,
                preview=True,
                keywords=("analytics", "privacy", "telemetry", "data"),
            )
        )

        clear_card = SettingsCard("Data Management", "Manage your stored data")
        clear_card.body_layout.addWidget(
            InfoBanner(
                "Clear data",
                "Remove all remembered sessions from local storage. This action cannot be undone.",
                tone="warning",
            )
        )
        clear_button = AppButton("Clear All Remembered Sessions", "danger")
        clear_button.clicked.connect(self._clear_remembered_sessions)
        clear_card.body_layout.addWidget(clear_button)
        
        return self._register_cards("Privacy", card, clear_card)

    def _build_about_page(self) -> QWidget:
        card = SettingsCard("About ABUSER", "Information about this application")
        
        card.body_layout.addWidget(
            InfoBanner(
                "Version",
                "ABUSER Bot v1.0.0 - Discord selfbot framework with PyQt6 GUI",
                tone="accent",
            )
        )
        card.body_layout.addWidget(
            InfoBanner(
                "Design System",
                "Modern theme-based architecture with centralized tokens and shared components",
                tone="neutral",
            )
        )
        card.body_layout.addWidget(
            InfoBanner(
                "Notice",
                "Using selfbots violates Discord's Terms of Service. Use at your own risk.",
                tone="danger",
            )
        )
        return self._register_cards("About", card)

    def _clear_remembered_sessions(self) -> None:
        clear_remembered_sessions()

    def _on_category_changed(self, index: int) -> None:
        if index < 0:
            return
        self.content_stack.setCurrentIndex(index)

    def current_config(self) -> dict:
        config = deepcopy(self._config)
        config["appearance"]["preset"] = self.preset_combo.currentText()
        config["appearance"]["accent"] = self.accent_combo.currentText()
        config["appearance"]["font_size"] = self.font_size_spin.value()
        config["behavior"]["startup_page"] = self.startup_combo.currentText()
        config["privacy"]["save_tokens"] = self.save_tokens_toggle.isChecked()
        return config

    def load_from_config(self, config: dict) -> None:
        self._config = deepcopy(config)
        self._original_config = deepcopy(config)
        appearance = config.get("appearance", {})
        behavior = config.get("behavior", {})
        privacy = config.get("privacy", {})

        preset = appearance.get("preset", "Discord Dark")
        preset_index = self.preset_combo.findText(preset)
        if preset_index >= 0:
            self.preset_combo.setCurrentIndex(preset_index)

        accent = appearance.get("accent", "Red")
        accent_index = self.accent_combo.findText(accent)
        if accent_index >= 0:
            self.accent_combo.setCurrentIndex(accent_index)

        self.font_size_spin.setValue(appearance.get("font_size", 13))
        
        startup = behavior.get("startup_page", "Login")
        startup_index = self.startup_combo.findText(startup)
        if startup_index >= 0:
            self.startup_combo.setCurrentIndex(startup_index)

        self.save_tokens_toggle.setChecked(privacy.get("save_tokens", True))

    def _restore_original(self) -> None:
        self.load_from_config(self._original_config)

    def _reset_to_defaults(self) -> None:
        self.load_from_config(deepcopy(DEFAULT_GUI_CONFIG))

    def _apply_changes(self) -> None:
        self._config = self.current_config()
        self._original_config = deepcopy(self._config)
        self.settings_applied.emit(deepcopy(self._config))

    def _apply_search(self, text: str) -> None:
        query = text.lower().strip()
        any_match = False
        first_visible_index = None

        for index in range(self.category_list.count()):
            category_name = self.category_list.item(index).text()
            cards = self._category_cards.get(category_name, [])
            category_match = False
            for card in cards:
                category_match = card.apply_search(query) or category_match
            self.category_list.item(index).setHidden(bool(query) and not category_match)
            if category_match and first_visible_index is None:
                first_visible_index = index
            any_match = any_match or category_match

        if query and not any_match:
            self.content_stack.setCurrentWidget(self.search_empty)
            return

        if query and first_visible_index is not None:
            self.category_list.setCurrentRow(first_visible_index)
        elif not query:
            for index in range(self.category_list.count()):
                self.category_list.item(index).setHidden(False)
            if self.content_stack.currentWidget() is self.search_empty:
                self.content_stack.setCurrentIndex(max(self.category_list.currentRow(), 0))

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens
        
        # Category list styling
        self.category_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                padding: 8px 4px;
                outline: none;
            }}
            QListWidget::item {{
                color: {dt.text_secondary};
                padding: 14px 16px;
                border-radius: 10px;
                margin: 2px 4px;
                font-weight: 500;
                font-size: 13px;
            }}
            QListWidget::item:hover {{
                background-color: {rgba(dt.surface_raised, 0.5)};
                color: {dt.text_primary};
            }}
            QListWidget::item:selected {{
                background-color: {rgba(dt.accent, 0.12)};
                color: {dt.accent};
                font-weight: 600;
            }}
            QListWidget::item:selected:hover {{
                background-color: {rgba(dt.accent, 0.18)};
            }}
            QListWidget:focus {{
                outline: none;
            }}
            """
        )
        
        # Refresh all cards and empty state
        for cards in self._category_cards.values():
            for card in cards:
                card.refresh_theme()
        
        if hasattr(self.search_empty, 'refresh_theme'):
            self.search_empty.refresh_theme()
