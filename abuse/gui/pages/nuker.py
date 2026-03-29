"""Nuker page — checkbox-driven action selection with grouped categories."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..components import (
    AppButton,
    AppComboBox,
    AppLineEdit,
    AppSpinBox,
    InfoBanner,
    PanelCard,
    SectionLabel,
    StatusChip,
    rgba,
)
from ..theme import get_theme_manager
from .base import BasePage, GuildItem


# ── Action definitions ────────────────────────────────────────────────────────

# (action_id, display_label, description)
_GROUP_CONTENT: list[tuple[str, str, str]] = [
    ("delete_emojis",   "Delete Emojis",   "Remove all custom emojis"),
    ("delete_stickers", "Delete Stickers", "Remove all custom stickers"),
]

_GROUP_STRUCTURE: list[tuple[str, str, str]] = [
    ("delete_channels", "Delete Channels", "Delete every channel"),
    ("delete_roles",    "Delete Roles",    "Delete every role"),
    ("rename_server",   "Rename Server",   "Set a new server name"),
]

_GROUP_MEMBERS: list[tuple[str, str, str]] = [
    ("kick_all", "Kick All",    "Kick all non-bot members"),
    ("ban_all",  "Ban All",     "Permanently ban all members"),
]

# Danger-tier — lives in its own red section
_GROUP_DANGER: list[tuple[str, str, str]] = [
    ("nuke_server", "Nuke Server", "Execute all selected actions in sequence"),
]


# ── Styled checkbox row ───────────────────────────────────────────────────────

class _ActionRow(QWidget):
    """A single action as a checkbox + description row."""

    def __init__(
        self,
        action_id: str,
        label: str,
        description: str,
        danger: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.action_id = action_id
        self._danger = danger
        self.setObjectName("actionRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("actionCheckbox")
        self.checkbox.setFixedSize(20, 20)
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label)
        self.label.setObjectName("actionLabel")
        lbl_font = QFont("Segoe UI", 10)
        lbl_font.setWeight(QFont.Weight.DemiBold)
        self.label.setFont(lbl_font)
        text_col.addWidget(self.label)

        self.desc = QLabel(description)
        self.desc.setObjectName("actionDesc")
        text_col.addWidget(self.desc)

        layout.addLayout(text_col, 1)

        # Click anywhere on the row toggles the checkbox
        self.checkbox.stateChanged.connect(self._on_state)
        self.refresh_theme()

    def mousePressEvent(self, event) -> None:
        self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def _on_state(self, _state) -> None:
        self.refresh_theme()

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_enabled(self, enabled: bool) -> None:
        self.checkbox.setEnabled(enabled)
        self.setEnabled(enabled)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens
        checked = self.checkbox.isChecked()
        enabled = self.isEnabled()

        if not enabled:
            row_bg     = "transparent"
            row_border = "transparent"
            lbl_color  = dt.text_muted
            desc_color = dt.text_muted
        elif self._danger and checked:
            row_bg     = rgba(dt.danger, 0.10)
            row_border = rgba(dt.danger, 0.40)
            lbl_color  = dt.danger
            desc_color = rgba(dt.danger, 0.75)
        elif checked:
            row_bg     = rgba(dt.accent, 0.10)
            row_border = rgba(dt.accent, 0.35)
            lbl_color  = dt.text_primary
            desc_color = dt.text_secondary
        else:
            row_bg     = "transparent"
            row_border = "transparent"
            lbl_color  = dt.text_primary
            desc_color = dt.text_muted

        self.setStyleSheet(
            f"""
            QWidget#actionRow {{
                background-color: {row_bg};
                border: 1px solid {row_border};
                border-radius: 8px;
            }}
            QWidget#actionRow:hover {{
                background-color: {rgba(dt.surface_raised, 0.5)};
                border-color: {rgba(dt.border_strong, 0.6)};
            }}
            """
        )
        # Checkbox indicator
        accent = dt.danger if self._danger else dt.accent
        self.checkbox.setStyleSheet(
            f"""
            QCheckBox {{
                background: transparent;
                border: none;
                spacing: 0px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 2px solid {rgba(accent if checked else dt.border_strong, 0.9)};
                background-color: {rgba(accent, 0.18) if checked else "transparent"};
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border-color: {accent};
                image: none;
            }}
            QCheckBox::indicator:disabled {{
                border-color: {rgba(dt.text_muted, 0.35)};
                background-color: transparent;
            }}
            """
        )
        self.label.setStyleSheet(
            f"color: {lbl_color}; background: transparent;"
        )
        self.desc.setStyleSheet(
            f"color: {desc_color}; font-size: 11px; background: transparent;"
        )


# ── Group block ───────────────────────────────────────────────────────────────

class _ActionGroup(QWidget):
    """A titled group of _ActionRow items inside a card."""

    def __init__(
        self,
        title: str,
        actions: list[tuple[str, str, str]],
        danger: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._rows: list[_ActionRow] = []
        self._danger = danger
        self.setObjectName("actionGroup")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Group heading
        heading = QLabel(title.upper())
        heading.setObjectName("groupHeading")
        hf = QFont("Segoe UI", 9)
        hf.setWeight(QFont.Weight.Bold)
        heading.setFont(hf)
        layout.addWidget(heading)
        self._heading = heading

        for action_id, label, desc in actions:
            row = _ActionRow(action_id, label, desc, danger=danger)
            self._rows.append(row)
            layout.addWidget(row)

    def checked_ids(self) -> list[str]:
        return [r.action_id for r in self._rows if r.is_checked()]

    def set_all_enabled(self, enabled: bool) -> None:
        for row in self._rows:
            row.set_enabled(enabled)

    def uncheck_all(self) -> None:
        for row in self._rows:
            row.checkbox.setChecked(False)

    def refresh_theme(self) -> None:
        dt = get_theme_manager().design_tokens
        color = rgba(dt.danger, 0.85) if self._danger else dt.text_muted
        self._heading.setStyleSheet(
            f"color: {color}; letter-spacing: 1.2px; background: transparent;"
        )
        for row in self._rows:
            row.refresh_theme()


# ── Main page ─────────────────────────────────────────────────────────────────

class NukerPage(BasePage):
    nuke_action_requested  = pyqtSignal(str, str)
    setup_server_requested = pyqtSignal(str, str, int, int)
    guild_selection_changed = pyqtSignal(str)

    ICON_SIZE = 40

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("Nuker", "", eyebrow="Destructive", parent=parent)
        self.root_layout.removeWidget(self.header)
        self.header.hide()

        self._selected_guild: Optional[GuildItem] = None
        self._guilds_list: list[GuildItem] = []
        self._is_connected: bool = False
        self._groups: list[_ActionGroup] = []
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll = scroll

        body = QWidget()
        self._body = body
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 24, 24, 24)
        bl.setSpacing(16)
        scroll.setWidget(body)
        self.root_layout.addWidget(scroll, 1)

        bl.addWidget(self._build_target_card())
        bl.addWidget(self._build_actions_card())
        bl.addWidget(self._build_setup_card())
        bl.addStretch(1)

        self.refresh_theme()
        self._update_states()

    # ── Target server card ────────────────────────────────────────────────────

    def _build_target_card(self) -> QWidget:
        card = PanelCard("Target Server", "Select the server you want to operate on.")
        self._target_card = card

        # Row: icon | name+dropdown | chip
        row = QHBoxLayout()
        row.setSpacing(16)

        self.target_icon = QLabel()
        self.target_icon.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        self.target_icon.setObjectName("serverIcon")
        self._set_icon(None)
        row.addWidget(self.target_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        name_col = QVBoxLayout()
        name_col.setSpacing(6)

        self.target_name = QLabel("No server selected")
        self.target_name.setObjectName("targetName")
        nf = QFont("Segoe UI", 14)
        nf.setWeight(QFont.Weight.Bold)
        self.target_name.setFont(nf)
        name_col.addWidget(self.target_name)

        self.guild_dropdown = AppComboBox()
        self.guild_dropdown.setPlaceholderText("Choose a server…")
        self.guild_dropdown.currentIndexChanged.connect(self._on_dropdown_changed)
        name_col.addWidget(self.guild_dropdown)

        row.addLayout(name_col, 1)

        self.status_chip = StatusChip("Disconnected", "danger")
        row.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignTop)

        card.body_layout.addLayout(row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        div.setObjectName("statsDivider")
        card.body_layout.addWidget(div)
        self._stats_divider = div

        # Stat pills row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(0)

        self._stat_containers: list[QWidget] = []
        self._stats: list[tuple[QLabel, QLabel]] = []
        for key in ("Members", "Channels", "Roles", "Boosts"):
            container, val_lbl, key_lbl = self._make_stat_pill(key, "—")
            self._stats.append((val_lbl, key_lbl))
            self._stat_containers.append(container)
            stats_row.addWidget(container)

        stats_row.addStretch(1)
        card.body_layout.addLayout(stats_row)

        return card

    def _make_stat_pill(self, key: str, value: str) -> tuple[QWidget, QLabel, QLabel]:
        """Create a small stat block; returns (container, value_label, key_label)."""
        container = QWidget()
        container.setObjectName("statPill")
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 24, 0)
        cl.setSpacing(2)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("statValue")
        vf = QFont("Segoe UI", 16)
        vf.setWeight(QFont.Weight.Bold)
        val_lbl.setFont(vf)
        cl.addWidget(val_lbl)

        key_lbl = QLabel(key.upper())
        key_lbl.setObjectName("statKey")
        kf = QFont("Segoe UI", 9)
        kf.setWeight(QFont.Weight.DemiBold)
        key_lbl.setFont(kf)
        cl.addWidget(key_lbl)

        return container, val_lbl, key_lbl

    # ── Actions card ──────────────────────────────────────────────────────────

    def _build_actions_card(self) -> QWidget:
        card = PanelCard(
            "Actions",
            "Select the operations to queue, then hit Execute.",
        )
        self._actions_card = card

        # Three standard groups in a horizontal row
        groups_row = QHBoxLayout()
        groups_row.setSpacing(12)

        g_content = _ActionGroup("Content", _GROUP_CONTENT)
        g_structure = _ActionGroup("Structure", _GROUP_STRUCTURE)
        g_members = _ActionGroup("Members", _GROUP_MEMBERS)

        self._groups = [g_content, g_structure, g_members]

        for group in self._groups:
            groups_row.addWidget(group, 1)

        card.body_layout.addLayout(groups_row)

        # Divider before danger zone
        danger_div = QFrame()
        danger_div.setFrameShape(QFrame.Shape.HLine)
        danger_div.setFixedHeight(1)
        danger_div.setObjectName("dangerDivider")
        card.body_layout.addWidget(danger_div)
        self._danger_div = danger_div

        # Danger zone row — checkbox + execute side by side
        danger_row = QHBoxLayout()
        danger_row.setSpacing(16)

        self._danger_group = _ActionGroup("Danger Zone", _GROUP_DANGER, danger=True)
        danger_row.addWidget(self._danger_group, 1)

        # Execute button + select-all toggle
        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        btn_col.setContentsMargins(0, 4, 0, 0)

        self.execute_btn = AppButton("Execute Selected", "danger")
        self.execute_btn.setMinimumHeight(44)
        self.execute_btn.setEnabled(False)
        self.execute_btn.clicked.connect(self._on_execute_clicked)
        btn_col.addWidget(self.execute_btn)

        self.select_all_btn = AppButton("Select All", "tertiary")
        self.select_all_btn.setEnabled(False)
        self.select_all_btn.clicked.connect(self._select_all)
        btn_col.addWidget(self.select_all_btn)

        self.clear_btn = AppButton("Clear All", "tertiary")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._clear_all)
        btn_col.addWidget(self.clear_btn)

        btn_col.addStretch(1)
        danger_row.addLayout(btn_col)

        card.body_layout.addLayout(danger_row)

        # Status banner
        self.status_banner = InfoBanner(
            "No server selected",
            "Select a server to enable actions.",
            tone="neutral",
        )
        card.body_layout.addWidget(self.status_banner)

        return card

    # ── Quick setup card ──────────────────────────────────────────────────────

    def _build_setup_card(self) -> QWidget:
        card = PanelCard(
            "Quick Setup",
            "Rename the server and scaffold channels and roles.",
        )
        self._setup_card = card

        row = QHBoxLayout()
        row.setSpacing(16)

        name_col = QVBoxLayout()
        name_col.setSpacing(6)
        name_col.addWidget(SectionLabel("Server Name"))
        self.server_name_input = AppLineEdit()
        self.server_name_input.setText("Test Server")
        name_col.addWidget(self.server_name_input)
        row.addLayout(name_col, 2)

        roles_col = QVBoxLayout()
        roles_col.setSpacing(6)
        roles_col.addWidget(SectionLabel("Roles"))
        self.roles_spinner = AppSpinBox()
        self.roles_spinner.setRange(1, 50)
        self.roles_spinner.setValue(5)
        roles_col.addWidget(self.roles_spinner)
        row.addLayout(roles_col, 1)

        channels_col = QVBoxLayout()
        channels_col.setSpacing(6)
        channels_col.addWidget(SectionLabel("Channels"))
        self.channels_spinner = AppSpinBox()
        self.channels_spinner.setRange(1, 50)
        self.channels_spinner.setValue(5)
        channels_col.addWidget(self.channels_spinner)
        row.addLayout(channels_col, 1)

        self.setup_button = AppButton("Setup Server", "accent")
        self.setup_button.setEnabled(False)
        self.setup_button.clicked.connect(self._on_setup_clicked)
        row.addWidget(self.setup_button, 0, Qt.AlignmentFlag.AlignBottom)

        card.body_layout.addLayout(row)
        return card

    # ── State helpers ─────────────────────────────────────────────────────────

    def _selected_action_ids(self) -> list[str]:
        ids: list[str] = []
        for g in self._groups:
            ids.extend(g.checked_ids())
        ids.extend(self._danger_group.checked_ids())
        return ids

    def _select_all(self) -> None:
        for g in self._groups:
            for row in g._rows:
                row.checkbox.setChecked(True)

    def _clear_all(self) -> None:
        for g in self._groups:
            g.uncheck_all()
        self._danger_group.uncheck_all()

    def _update_states(self) -> None:
        has_guild = (
            self._selected_guild is not None
            or (self.guild_dropdown.currentIndex() >= 0 and self.guild_dropdown.count() > 0)
        )
        active = self._is_connected and has_guild

        for g in self._groups:
            g.set_all_enabled(active)
        self._danger_group.set_all_enabled(active)

        self.execute_btn.setEnabled(active)
        self.select_all_btn.setEnabled(active)
        self.clear_btn.setEnabled(active)
        self.setup_button.setEnabled(active)

    def _update_status(self, message: str, tone: str = "neutral") -> None:
        self.status_banner.title_label.setText(message)
        self.status_banner.set_tone(tone)

    # ── Icon ──────────────────────────────────────────────────────────────────

    def _set_icon(self, guild: Optional[GuildItem]) -> None:
        sz = self.ICON_SIZE
        pixmap = QPixmap(sz, sz)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        palette = ["#5865F2", "#EB459E", "#3BA55D", "#FAA81A",
                   "#ED4245", "#57F287", "#9B59B6", "#1ABC9C"]
        if guild:
            bg = QColor(palette[sum(ord(c) for c in guild.name) % len(palette)])
            letter = guild.name[0].upper()
        else:
            bg = QColor("#5865F2")
            letter = "?"

        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, sz, sz, 10, 10)

        painter.setPen(Qt.GlobalColor.white)
        f = painter.font()
        f.setPointSize(16)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()

        self.target_icon.setPixmap(pixmap)

    # ── Signals / slots ───────────────────────────────────────────────────────

    def _on_dropdown_changed(self, index: int) -> None:
        if index < 0:
            self._selected_guild = None
            self._set_icon(None)
            self._update_states()
            return

        guild_id = self.guild_dropdown.itemData(index)
        if guild_id is not None:
            for guild in self._guilds_list:
                if guild.guild_id == int(guild_id):
                    self._selected_guild = guild
                    self._set_icon(guild)
                    self.set_selected_guild(guild)
                    self.guild_selection_changed.emit(str(guild_id))
                    break

    def _on_execute_clicked(self) -> None:
        guild = self._get_selected_guild()
        if not guild:
            QMessageBox.warning(self, "No Server", "Select a server first.")
            return
        if not self._is_connected:
            QMessageBox.warning(self, "Not Connected", "Connect to Discord first.")
            return

        selected = self._selected_action_ids()
        if not selected:
            QMessageBox.information(self, "Nothing Selected", "Tick at least one action to execute.")
            return

        action_names = {
            "delete_emojis":   "Delete Emojis",
            "delete_stickers": "Delete Stickers",
            "delete_channels": "Delete Channels",
            "delete_roles":    "Delete Roles",
            "rename_server":   "Rename Server",
            "kick_all":        "Kick All",
            "ban_all":         "Ban All",
            "nuke_server":     "NUKE SERVER",
        }
        names_str = "\n".join(f"  • {action_names.get(a, a)}" for a in selected)

        reply = QMessageBox.question(
            self,
            "Confirm Execution",
            f"Execute {len(selected)} action(s) on '{guild.name}'?\n\n{names_str}\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for action_id in selected:
            self.nuke_action_requested.emit(action_id, str(guild.guild_id))

        self._update_status(f"Queued {len(selected)} action(s) on {guild.name}…", "warning")
        self._clear_all()

    def _on_setup_clicked(self) -> None:
        guild = self._get_selected_guild()
        if not guild:
            QMessageBox.warning(self, "No Server", "Select a server first.")
            return
        if not self._is_connected:
            QMessageBox.warning(self, "Not Connected", "Connect to Discord first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Setup",
            f"Setup '{guild.name}'?\n\n"
            f"  New name: {self.server_name_input.text()}\n"
            f"  Roles: {self.roles_spinner.value()}\n"
            f"  Channels: {self.channels_spinner.value()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.setup_server_requested.emit(
                str(guild.guild_id),
                self.server_name_input.text().strip() or "Test Server",
                self.roles_spinner.value(),
                self.channels_spinner.value(),
            )
            self._update_status(f"Setting up {guild.name}…", "warning")

    # ── Public API ────────────────────────────────────────────────────────────

    PERM_BAN_MEMBERS    = 1 << 2
    PERM_MANAGE_CHANNELS = 1 << 4

    def _has_manage_permissions(self, guild: GuildItem) -> bool:
        if guild.is_owner:
            return True
        p = guild.my_permissions
        return bool(p & self.PERM_BAN_MEMBERS) and bool(p & self.PERM_MANAGE_CHANNELS)

    def update_guild_list(self, guilds: list[GuildItem]) -> None:
        manageable = [g for g in guilds if self._has_manage_permissions(g)]
        self._guilds_list = manageable

        current_id = self._selected_guild.guild_id if self._selected_guild else None
        self.guild_dropdown.clear()

        for guild in sorted(manageable, key=lambda g: g.member_count, reverse=True):
            self.guild_dropdown.addItem(
                f"{guild.name}  ({guild.member_count:,})",
                str(guild.guild_id),
            )

        if current_id:
            for i in range(self.guild_dropdown.count()):
                if int(self.guild_dropdown.itemData(i)) == current_id:
                    self.guild_dropdown.setCurrentIndex(i)
                    break
            else:
                self._selected_guild = None
                self._set_icon(None)

        self._update_states()

    def _get_selected_guild(self) -> Optional[GuildItem]:
        idx = self.guild_dropdown.currentIndex()
        if idx < 0:
            return None
        gid = self.guild_dropdown.itemData(idx)
        if gid is None:
            return None
        for g in self._guilds_list:
            if g.guild_id == int(gid):
                return g
        return None

    def set_selected_guild(self, guild: Optional[GuildItem]) -> None:
        self._selected_guild = guild
        stat_data = (
            (guild.member_count, guild.channels_count, guild.roles_count, guild.boost_count)
            if guild else ("—", "—", "—", "—")
        )
        name = guild.name if guild else "No server selected"
        self.target_name.setText(name)

        for (val_lbl, _), val in zip(self._stats, stat_data):
            text = f"{val:,}" if isinstance(val, int) else str(val)
            val_lbl.setText(text)

        self._update_states()

    def set_connected(self, connected: bool) -> None:
        self._is_connected = connected
        self.status_chip.setText("Connected" if connected else "Disconnected")
        self.status_chip.set_tone("success" if connected else "danger")
        self._update_states()
        if not connected:
            self._update_status("Connect to Discord to enable actions.", "neutral")

    def on_action_completed(self, action_id: str, success: bool, message: str = "") -> None:
        if success:
            self._update_status(f"Completed: {action_id}", "success")
        else:
            self._update_status(f"Failed: {message}", "danger")

    def on_setup_completed(self, success: bool, message: str = "") -> None:
        if success:
            self._update_status("Setup complete.", "success")
        else:
            self._update_status(f"Setup failed: {message}", "danger")

    # ── Theme ─────────────────────────────────────────────────────────────────

    def refresh_theme(self) -> None:
        super().refresh_theme()
        dt = get_theme_manager().design_tokens

        # Scroll body
        if hasattr(self, "_body"):
            self._body.setStyleSheet(
                f"background-color: {dt.background}; border: none;"
            )

        # Stat labels
        if hasattr(self, "_stats"):
            for val_lbl, key_lbl in self._stats:
                val_lbl.setStyleSheet(
                    f"color: {dt.text_primary}; background: transparent;"
                )
                key_lbl.setStyleSheet(
                    f"color: {dt.text_muted}; letter-spacing: 0.8px; background: transparent;"
                )

        if hasattr(self, "target_name"):
            self.target_name.setStyleSheet(
                f"color: {dt.text_primary}; background: transparent;"
            )

        # Dividers
        if hasattr(self, "_stats_divider"):
            self._stats_divider.setStyleSheet(
                f"QFrame {{ background-color: {rgba(dt.border_strong, 0.5)}; border: none; }}"
            )
        if hasattr(self, "_danger_div"):
            self._danger_div.setStyleSheet(
                f"QFrame {{ background-color: {rgba(dt.danger, 0.3)}; border: none; }}"
            )

        # Action groups
        if hasattr(self, "_groups"):
            for g in self._groups:
                g.refresh_theme()
        if hasattr(self, "_danger_group"):
            self._danger_group.refresh_theme()

        # Status banner
        if hasattr(self, "status_banner"):
            self.status_banner.refresh_theme()
