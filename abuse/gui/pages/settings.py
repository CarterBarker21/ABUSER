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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..components import (
    AppButton,
    AppComboBox,
    AppSpinBox,
    EmptyState,
    InfoBanner,
    PanelCard,
    SearchField,
    StatusChip,
    ToggleSwitch,
    rgba,
)
from ..config import DEFAULT_GUI_CONFIG, clear_remembered_sessions, load_gui_config
from ..routes import ROUTE_LABELS, STARTUP_OPTIONS
from ..theme import get_theme_manager
from .base import BasePage


class SettingRowWidget(QWidget):
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(4)
        layout.addLayout(text_column, 1)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        text_column.addLayout(title_row)

        self.title_label = QLabel(title)
        title_row.addWidget(self.title_label)
        if preview:
            self.preview_chip = StatusChip("Preview", "preview")
            title_row.addWidget(self.preview_chip)
        else:
            self.preview_chip = None
        title_row.addStretch(1)

        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        text_column.addWidget(self.description_label)

        self.control = control
        layout.addWidget(control, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

    def matches(self, query: str) -> bool:
        if not query:
            return True
        return query in self._search_text

    def refresh_theme(self, colors=None) -> None:
        if colors is None:
            from ..theme import get_theme_manager

            colors = get_theme_manager().theme
        self.title_label.setStyleSheet(f"color: {colors.text_primary}; font-weight: 600;")
        self.description_label.setStyleSheet(f"color: {colors.text_secondary}; font-size: 12px;")
        if self.preview_chip:
            self.preview_chip.refresh_theme()


class SettingsCard(PanelCard):
    def __init__(self, title: str, description: str, parent: Optional[QWidget] = None):
        self.rows: list[SettingRowWidget] = []
        super().__init__(title, description, parent=parent)

    def add_row(self, row: SettingRowWidget) -> None:
        self.rows.append(row)
        self.body_layout.addWidget(row)

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
        for row in self.rows:
            row.refresh_theme(self.theme)


class SettingsPage(BasePage):
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Settings",
            "Live appearance and startup controls with preview-only sections called out explicitly.",
            eyebrow="Preferences",
            parent=parent,
        )
        self._config = deepcopy(DEFAULT_GUI_CONFIG)
        self._original_config = deepcopy(DEFAULT_GUI_CONFIG)
        self._category_cards: dict[str, list[SettingsCard]] = {}
        self._build_ui()
        self.load_from_config(load_gui_config())

    def _build_ui(self) -> None:
        self.search_input = SearchField("Search settings")
        self.search_input.textChanged.connect(self._apply_search)
        self.root_layout.addWidget(self.search_input)

        main_row = QHBoxLayout()
        main_row.setSpacing(self.tokens.metrics.spacing_lg)
        self.root_layout.addLayout(main_row, 1)

        self.category_list = QListWidget()
        self.category_list.setFixedWidth(220)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        main_row.addWidget(self.category_list)

        self.content_stack = QStackedWidget()
        main_row.addWidget(self.content_stack, 1)

        self.search_empty = EmptyState("No settings match", "Try a broader term or clear the search field to restore the full settings surface.")

        self._add_category("Appearance", self._build_appearance_page())
        self._add_category("Behavior", self._build_behavior_page())
        self._add_category("Notifications", self._build_notifications_page())
        self._add_category("Privacy", self._build_privacy_page())
        self._add_category("About", self._build_about_page())
        self.content_stack.addWidget(self.search_empty)

        actions = QHBoxLayout()
        actions.addStretch(1)

        reset_button = AppButton("Reset to Defaults", "secondary")
        reset_button.clicked.connect(self._reset_to_defaults)
        actions.addWidget(reset_button)

        cancel_button = AppButton("Cancel", "tertiary")
        cancel_button.clicked.connect(self._restore_original)
        actions.addWidget(cancel_button)

        apply_button = AppButton("Apply Changes", "primary")
        apply_button.clicked.connect(self._apply_changes)
        actions.addWidget(apply_button)

        self.root_layout.addLayout(actions)
        self.category_list.setCurrentRow(0)
        self.refresh_theme()

    def _add_category(self, name: str, page: QWidget) -> None:
        item = QListWidgetItem(name)
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
        layout.setSpacing(self.tokens.metrics.spacing_lg)
        self._category_cards[category] = list(cards)
        for card in cards:
            layout.addWidget(card)
        layout.addStretch(1)
        return self._page_scroll(container)

    def _build_appearance_page(self) -> QWidget:
        card = SettingsCard("Appearance", "These controls are wired to the running desktop UI.")

        self.preset_combo = AppComboBox()
        self.preset_combo.addItems(["Midnight", "Obsidian", "Discord Dark", "Catppuccin Mocha"])
        card.add_row(
            SettingRowWidget(
                "Theme preset",
                "Select the active preset that ThemeManager will apply across the shell and pages.",
                self.preset_combo,
                keywords=("preset", "theme", "accent"),
            )
        )

        self.accent_combo = AppComboBox()
        self.accent_combo.addItems(["Red", "Discord Blue", "Green", "Purple", "Orange", "Pink", "Cyan", "Yellow"])
        card.add_row(
            SettingRowWidget(
                "Accent",
                "Applies the current accent color across navigation, primary actions, and status emphasis.",
                self.accent_combo,
                keywords=("accent", "color"),
            )
        )

        self.font_size_spin = AppSpinBox()
        self.font_size_spin.setRange(11, 18)
        card.add_row(
            SettingRowWidget(
                "Font size",
                "Changes the application font size so the full desktop UI responds consistently.",
                self.font_size_spin,
                keywords=("font", "text", "size"),
            )
        )

        self.startup_combo = AppComboBox()
        self.startup_combo.addItems(STARTUP_OPTIONS)
        card.add_row(
            SettingRowWidget(
                "Startup page",
                "Choose the first page shown at launch, or use Last Used to restore the previous route.",
                self.startup_combo,
                keywords=("startup", "launch", "page"),
            )
        )

        preview_card = SettingsCard("Surface Options", "Kept visible for product intent and marked honestly when not active.")
        self.animations_toggle = ToggleSwitch("Animations")
        self.animations_toggle.setEnabled(False)
        preview_card.add_row(
            SettingRowWidget(
                "Animations",
                "Animation tuning is not wired beyond lightweight page transitions yet.",
                self.animations_toggle,
                preview=True,
                keywords=("animation", "motion"),
            )
        )
        self.transparency_toggle = ToggleSwitch("Transparency")
        self.transparency_toggle.setEnabled(False)
        preview_card.add_row(
            SettingRowWidget(
                "Transparency",
                "Transparency remains a preview-only setting in this build.",
                self.transparency_toggle,
                preview=True,
                keywords=("opacity", "transparency"),
            )
        )
        self.compact_toggle = ToggleSwitch("Compact mode")
        self.compact_toggle.setEnabled(False)
        preview_card.add_row(
            SettingRowWidget(
                "Compact mode",
                "Compact density options are visible but intentionally unavailable for now.",
                self.compact_toggle,
                preview=True,
                keywords=("compact", "density"),
            )
        )

        return self._register_cards("Appearance", card, preview_card)

    def _build_behavior_page(self) -> QWidget:
        card = SettingsCard("Behavior", "Visible behavior toggles that are not yet backed by runtime implementation stay clearly in preview.")

        for title, text, keywords in (
            ("Confirm action dialogs", "Confirmation prompts for preview-only surfaces are not active yet.", ("confirm", "dialog")),
            ("Log commands", "Command logging is still owned by bot configuration outside the GUI.", ("commands", "logging")),
            ("Minimize to tray", "Tray integration is not implemented in the desktop shell.", ("tray", "minimize")),
            ("Auto-start bot", "Automatic startup is intentionally unavailable from this build.", ("auto", "start")),
            ("Auto-update checks", "Update checks are shown as intent only.", ("update", "checks")),
        ):
            toggle = ToggleSwitch(title)
            toggle.setEnabled(False)
            card.add_row(SettingRowWidget(title, text, toggle, preview=True, keywords=keywords))

        return self._register_cards("Behavior", card)

    def _build_notifications_page(self) -> QWidget:
        card = SettingsCard("Notifications", "Notification controls stay visible without implying they already work.")
        for title, text in (
            ("Error notifications", "Desktop notification hooks are not wired in this build."),
            ("Success notifications", "Desktop notification hooks are not wired in this build."),
            ("Update notifications", "Desktop notification hooks are not wired in this build."),
            ("Sound effects", "Audio cues are visible as preview-only intent."),
        ):
            toggle = ToggleSwitch(title)
            toggle.setEnabled(False)
            card.add_row(SettingRowWidget(title, text, toggle, preview=True, keywords=(title.lower(),)))
        return self._register_cards("Notifications", card)

    def _build_privacy_page(self) -> QWidget:
        card = SettingsCard("Privacy", "Only the settings that genuinely affect the current build are treated as live.")

        self.save_tokens_toggle = ToggleSwitch("Allow remembered sessions")
        card.add_row(
            SettingRowWidget(
                "Remembered sessions",
                "Controls whether the Login page can save a local remembered session after a successful login.",
                self.save_tokens_toggle,
                keywords=("token", "session", "remembered", "privacy"),
            )
        )

        self.encrypt_tokens_toggle = ToggleSwitch("Encrypt remembered sessions")
        self.encrypt_tokens_toggle.setEnabled(False)
        card.add_row(
            SettingRowWidget(
                "Encrypt remembered sessions",
                "Encryption is not implemented in the current local storage path.",
                self.encrypt_tokens_toggle,
                preview=True,
                keywords=("encrypt", "token", "privacy"),
            )
        )

        self.analytics_toggle = ToggleSwitch("Anonymous analytics")
        self.analytics_toggle.setEnabled(False)
        card.add_row(
            SettingRowWidget(
                "Anonymous analytics",
                "Analytics collection is not present in this build.",
                self.analytics_toggle,
                preview=True,
                keywords=("analytics", "privacy"),
            )
        )

        clear_card = SettingsCard("Stored Data", "Local state you can actually clear from the desktop UI.")
        clear_card.body_layout.addWidget(
            InfoBanner(
                "Available now",
                "Clearing remembered sessions removes entries from data/tokens.json without touching other preferences.",
                tone="success",
            )
        )
        clear_button = AppButton("Clear Remembered Sessions", "danger")
        clear_button.clicked.connect(self._clear_remembered_sessions)
        clear_card.body_layout.addWidget(clear_button)
        return self._register_cards("Privacy", card, clear_card)

    def _build_about_page(self) -> QWidget:
        card = SettingsCard("About This UI", "Current notes for the refactored desktop surface.")
        card.body_layout.addWidget(
            InfoBanner(
                "Design system",
                "Theme tokens, shared components, and route metadata are now centralized instead of being spread across shell-only styles and inline tab CSS.",
                tone="accent",
            )
        )
        card.body_layout.addWidget(
            InfoBanner(
                "Preview surfaces",
                "DM delivery, local token scanning, and destructive action execution remain intentionally unavailable from the GUI build.",
                tone="preview",
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
        self.category_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {dt.surface};
                color: {dt.text_secondary};
                border: 1px solid {dt.border};
                border-radius: 12px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 8px;
                font-weight: 600;
            }}
            QListWidget::item:selected {{
                background-color: {rgba(dt.accent, 0.16)};
                border: 1px solid {rgba(dt.accent, 0.3)};
                color: {dt.text_primary};
            }}
            """
        )
