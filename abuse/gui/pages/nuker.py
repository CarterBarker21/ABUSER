"""Nuker page with clean, professional design."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor
from PyQt6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget, QMessageBox,
)

from ..components import (
    AppButton,
    AppComboBox,
    AppLineEdit,
    AppSpinBox,
    InfoBanner,
    StatusChip,
    rgba,
)
from .base import BasePage, GuildItem


class NukerPage(BasePage):
    """Clean Nuker page with professional design."""

    nuke_action_requested = pyqtSignal(str, str)
    setup_server_requested = pyqtSignal(str)
    guild_selection_changed = pyqtSignal(str)

    ICON_SIZE = 44

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            "Nuker",
            "Server management and destruction tools.",
            eyebrow="Destructive",
            parent=parent,
        )
        self.root_layout.removeWidget(self.header)
        self.header.hide()

        self._selected_guild: Optional[GuildItem] = None
        self._guilds_list: list[GuildItem] = []
        self._is_connected: bool = False
        self._action_buttons: dict[str, AppButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        # Scroll area - matching Guilds tab style
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(16)

        scroll.setWidget(body)
        self.root_layout.addWidget(scroll, 1)

        # === TARGET SERVER ===
        target_card = QWidget()
        target_card.setObjectName("nukerCard")
        target_layout = QVBoxLayout(target_card)
        target_layout.setContentsMargins(18, 18, 18, 18)
        target_layout.setSpacing(14)

        # Header row
        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        self.target_icon = QLabel()
        self.target_icon.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        self._set_placeholder_icon(None)
        header_row.addWidget(self.target_icon)

        name_col = QVBoxLayout()
        name_col.setSpacing(4)

        self.target_name = QLabel("Select a server")
        self.target_name.setStyleSheet("font-size: 18px; font-weight: 700;")
        name_col.addWidget(self.target_name)

        dropdown_row = QHBoxLayout()
        dropdown_row.setSpacing(12)

        self.guild_dropdown = AppComboBox()
        self.guild_dropdown.setPlaceholderText("Choose a server...")
        self.guild_dropdown.currentIndexChanged.connect(self._on_dropdown_changed)
        dropdown_row.addWidget(self.guild_dropdown, 1)

        self.status_chip = StatusChip("Disconnected", "danger")
        dropdown_row.addWidget(self.status_chip)

        name_col.addLayout(dropdown_row)
        header_row.addLayout(name_col, 1)

        target_layout.addLayout(header_row)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        target_layout.addWidget(line)

        # Stats
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)

        self.stat_members = QLabel("Members: -")
        self.stat_channels = QLabel("Channels: -")
        self.stat_roles = QLabel("Roles: -")
        self.stat_boosts = QLabel("Boosts: -")

        for label in [self.stat_members, self.stat_channels, self.stat_roles, self.stat_boosts]:
            label.setStyleSheet("font-size: 13px;")
            stats_row.addWidget(label)

        stats_row.addStretch(1)
        target_layout.addLayout(stats_row)

        body_layout.addWidget(target_card)

        # === ACTIONS GRID ===
        actions_card = QWidget()
        actions_card.setObjectName("nukerCard")
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(18, 18, 18, 18)
        actions_layout.setSpacing(14)

        # Section title
        actions_title = QLabel("Actions")
        actions_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        actions_layout.addWidget(actions_title)

        # Actions in a clean grid
        actions_grid = QHBoxLayout()
        actions_grid.setSpacing(12)

        # Content column
        content_col = QVBoxLayout()
        content_col.setSpacing(8)
        content_label = QLabel("Content")
        content_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #888;")
        content_col.addWidget(content_label)

        self._add_action_btn(content_col, "delete_emojis", "Delete Emojis", "preview")
        self._add_action_btn(content_col, "delete_stickers", "Delete Stickers", "preview")
        actions_grid.addLayout(content_col)

        # Structure column
        struct_col = QVBoxLayout()
        struct_col.setSpacing(8)
        struct_label = QLabel("Structure")
        struct_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #888;")
        struct_col.addWidget(struct_label)

        self._add_action_btn(struct_col, "delete_channels", "Delete Channels", "preview")
        self._add_action_btn(struct_col, "delete_roles", "Delete Roles", "preview")
        self._add_action_btn(struct_col, "rename_server", "Rename Server", "preview")
        actions_grid.addLayout(struct_col)

        # Members column
        members_col = QVBoxLayout()
        members_col.setSpacing(8)
        members_label = QLabel("Members")
        members_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #888;")
        members_col.addWidget(members_label)

        self._add_action_btn(members_col, "kick_all", "Kick All", "preview")
        self._add_action_btn(members_col, "ban_all", "Ban All", "danger")
        actions_grid.addLayout(members_col)

        actions_layout.addLayout(actions_grid)

        # Nuke button - full width
        self._add_action_btn(actions_layout, "nuke_server", "NUKE SERVER", "danger")
        self._action_buttons["nuke_server"].setMinimumHeight(44)

        # Status banner
        self.status_banner = InfoBanner(
            "Ready",
            "Select a server to enable actions.",
            tone="neutral",
        )
        actions_layout.addWidget(self.status_banner)

        body_layout.addWidget(actions_card)

        # === QUICK SETUP ===
        setup_card = QWidget()
        setup_card.setObjectName("nukerCard")
        setup_layout = QHBoxLayout(setup_card)
        setup_layout.setContentsMargins(18, 18, 18, 18)
        setup_layout.setSpacing(16)

        # Inputs
        name_container = QVBoxLayout()
        name_container.setSpacing(4)
        name_lbl = QLabel("Name")
        name_lbl.setStyleSheet("font-size: 11px; color: #888;")
        self.server_name_input = AppLineEdit()
        self.server_name_input.setText("Test Server")
        name_container.addWidget(name_lbl)
        name_container.addWidget(self.server_name_input)
        setup_layout.addLayout(name_container, 2)

        roles_container = QVBoxLayout()
        roles_container.setSpacing(4)
        roles_lbl = QLabel("Roles")
        roles_lbl.setStyleSheet("font-size: 11px; color: #888;")
        self.roles_spinner = AppSpinBox()
        self.roles_spinner.setRange(1, 50)
        self.roles_spinner.setValue(5)
        roles_container.addWidget(roles_lbl)
        roles_container.addWidget(self.roles_spinner)
        setup_layout.addLayout(roles_container, 1)

        channels_container = QVBoxLayout()
        channels_container.setSpacing(4)
        channels_lbl = QLabel("Channels")
        channels_lbl.setStyleSheet("font-size: 11px; color: #888;")
        self.channels_spinner = AppSpinBox()
        self.channels_spinner.setRange(1, 50)
        self.channels_spinner.setValue(5)
        channels_container.addWidget(channels_lbl)
        channels_container.addWidget(self.channels_spinner)
        setup_layout.addLayout(channels_container, 1)

        self.setup_button = AppButton("Setup", "accent")
        self.setup_button.setEnabled(False)
        self.setup_button.clicked.connect(self._on_setup_clicked)
        setup_layout.addWidget(self.setup_button)

        body_layout.addWidget(setup_card)
        body_layout.addStretch(1)

        self.refresh_theme()
        self._update_button_states()



    def _add_action_btn(self, layout, action_id: str, label: str, variant: str) -> None:
        """Add an action button to a layout."""
        btn = AppButton(label, variant)
        btn.setEnabled(False)
        btn.setMinimumHeight(36)
        btn.clicked.connect(lambda checked=False, a=action_id: self._on_action_clicked(a))
        layout.addWidget(btn)
        self._action_buttons[action_id] = btn

    def _set_placeholder_icon(self, guild: Optional[GuildItem]) -> None:
        """Set placeholder icon."""
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if guild:
            colors = ["#5865F2", "#EB459E", "#3BA55D", "#FAA81A", "#ED4245", "#57F287", "#9B59B6", "#1ABC9C"]
            color_idx = sum(ord(c) for c in guild.name) % len(colors)
            bg_color = QColor(colors[color_idx])
            first_letter = guild.name[0].upper() if guild.name else "?"
        else:
            bg_color = QColor("#5865F2")
            first_letter = "?"

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.ICON_SIZE, self.ICON_SIZE)

        painter.setPen(Qt.GlobalColor.white)
        font = painter.font()
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, first_letter)
        painter.end()

        self.target_icon.setPixmap(pixmap)

    def _on_dropdown_changed(self, index: int) -> None:
        """Handle dropdown change."""
        if index < 0:
            self._selected_guild = None
            self._set_placeholder_icon(None)
            return

        guild_id = self.guild_dropdown.itemData(index)
        if guild_id is not None:
            guild_id_int = int(guild_id)
            for guild in self._guilds_list:
                if guild.guild_id == guild_id_int:
                    self._selected_guild = guild
                    self._set_placeholder_icon(guild)
                    self.set_selected_guild(guild)
                    self.guild_selection_changed.emit(str(guild_id))
                    break

    PERM_BAN_MEMBERS = 1 << 2
    PERM_MANAGE_CHANNELS = 1 << 4

    def _has_manage_permissions(self, guild: GuildItem) -> bool:
        """Check if user can manage guild."""
        if guild.is_owner:
            return True
        perms = guild.my_permissions
        has_ban = bool(perms & self.PERM_BAN_MEMBERS)
        has_manage = bool(perms & self.PERM_MANAGE_CHANNELS)
        return has_ban and has_manage

    def update_guild_list(self, guilds: list[GuildItem]) -> None:
        """Update guild dropdown."""
        manageable = [g for g in guilds if self._has_manage_permissions(g)]
        self._guilds_list = manageable

        current_id = None
        if self._selected_guild:
            current_id = self._selected_guild.guild_id

        self.guild_dropdown.clear()

        for guild in sorted(manageable, key=lambda g: g.member_count, reverse=True):
            self.guild_dropdown.addItem(f"{guild.name} ({guild.member_count:,})", str(guild.guild_id))

        if current_id:
            for i in range(self.guild_dropdown.count()):
                if int(self.guild_dropdown.itemData(i)) == current_id:
                    self.guild_dropdown.setCurrentIndex(i)
                    break
            else:
                self._selected_guild = None
                self._set_placeholder_icon(None)

        self._update_button_states()

    def _get_selected_guild(self) -> Optional[GuildItem]:
        """Get selected guild."""
        index = self.guild_dropdown.currentIndex()
        if index < 0:
            return None

        guild_id = self.guild_dropdown.itemData(index)
        if guild_id is None:
            return None

        guild_id_int = int(guild_id)
        for guild in self._guilds_list:
            if guild.guild_id == guild_id_int:
                return guild
        return None

    def _on_setup_clicked(self) -> None:
        """Handle setup click."""
        guild = self._get_selected_guild()
        if guild is None:
            QMessageBox.warning(self, "No Server", "Select a server first.")
            return
        if not self._is_connected:
            QMessageBox.warning(self, "Not Connected", "Connect to Discord first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Setup",
            f"Setup '{guild.name}'?\n\n"
            f"Rename: {self.server_name_input.text()}\n"
            f"Roles: {self.roles_spinner.value()}\n"
            f"Channels: {self.channels_spinner.value()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.setup_server_requested.emit(str(guild.guild_id))
            self._update_status(f"Setting up {guild.name}...", "warning")

    def _on_action_clicked(self, action_id: str) -> None:
        """Handle action click."""
        guild = self._get_selected_guild()
        if guild is None:
            QMessageBox.warning(self, "No Server", "Select a server first.")
            return
        if not self._is_connected:
            QMessageBox.warning(self, "Not Connected", "Connect to Discord first.")
            return
        if not self._confirm_action(action_id, guild):
            return

        self.nuke_action_requested.emit(action_id, str(guild.guild_id))
        self._update_status(f"Executing: {action_id}...", "warning")

    def _confirm_action(self, action_id: str, guild: GuildItem) -> bool:
        """Confirm destructive action."""
        names = {
            "delete_emojis": "Delete Emojis",
            "delete_stickers": "Delete Stickers",
            "rename_server": "Rename Server",
            "kick_all": "Kick All Members",
            "delete_channels": "Delete Channels",
            "delete_roles": "Delete Roles",
            "ban_all": "Ban All Members",
            "nuke_server": "NUKE SERVER",
        }
        name = names.get(action_id, action_id)

        warnings = {
            "delete_emojis": "Delete all custom emojis.",
            "delete_stickers": "Delete all stickers.",
            "rename_server": "Rename the server.",
            "kick_all": f"Kick all from '{guild.name}'.",
            "delete_channels": f"Delete ALL channels in '{guild.name}'.",
            "delete_roles": f"Delete ALL roles in '{guild.name}'.",
            "ban_all": f"BAN all from '{guild.name}'.",
            "nuke_server": f"DESTROY '{guild.name}' completely.",
        }

        reply = QMessageBox.question(
            self,
            f"Confirm: {name}",
            f"{warnings.get(action_id, 'This cannot be undone!')}\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def set_selected_guild(self, guild: Optional[GuildItem]) -> None:
        """Update selected guild display."""
        self._selected_guild = guild
        if guild is None:
            self.target_name.setText("Select a server")
            self.stat_members.setText("Members: -")
            self.stat_channels.setText("Channels: -")
            self.stat_roles.setText("Roles: -")
            self.stat_boosts.setText("Boosts: -")
        else:
            self.target_name.setText(guild.name)
            self.stat_members.setText(f"Members: {guild.member_count:,}")
            self.stat_channels.setText(f"Channels: {guild.channels_count}")
            self.stat_roles.setText(f"Roles: {guild.roles_count}")
            self.stat_boosts.setText(f"Boosts: {guild.boost_count}")
        self._update_button_states()

    def set_connected(self, connected: bool) -> None:
        """Update connection state."""
        self._is_connected = connected
        self.status_chip.setText("Connected" if connected else "Disconnected")
        self.status_chip.set_tone("success" if connected else "danger")
        self._update_button_states()
        if not connected:
            self._update_status("Disconnected. Connect to enable actions.", "neutral")

    def _update_button_states(self) -> None:
        """Enable/disable buttons."""
        has_guild = self.guild_dropdown.currentIndex() >= 0 and self.guild_dropdown.count() > 0
        enabled = self._is_connected and has_guild

        for btn in self._action_buttons.values():
            btn.setEnabled(enabled)
        self.setup_button.setEnabled(enabled)

    def _update_status(self, message: str, tone: str = "neutral") -> None:
        """Update status."""
        self.status_banner.title_label.setText(message)
        self.status_banner._tone = tone
        self.status_banner.refresh_theme()

    def on_action_completed(self, action_id: str, success: bool, message: str = "") -> None:
        """Action completed callback."""
        if success:
            self._update_status(f"Done: {action_id}", "success")
        else:
            self._update_status(f"Failed: {message}", "danger")

    def on_setup_completed(self, success: bool, message: str = "") -> None:
        """Setup completed callback."""
        if success:
            self._update_status("Setup complete", "success")
        else:
            self._update_status(f"Setup failed: {message}", "danger")

    def refresh_theme(self) -> None:
        """Refresh theme - matches Guilds tab styling."""
        super().refresh_theme()

        colors = self.theme

        # Set body background to match theme
        body = self.findChild(QScrollArea).widget()
        if body:
            body.setStyleSheet(f"background-color: {colors.bg_primary};")

        # Style cards - matching Guilds tab exactly
        for card in self.findChildren(QWidget):
            if card.objectName() == "nukerCard":
                card.setStyleSheet(f"""
                    QWidget#nukerCard {{
                        background-color: {colors.card_bg};
                        border: 1px solid {rgba(colors.border_light, 0.9)};
                        border-radius: 12px;
                    }}
                """)

        self.target_name.setStyleSheet(f"color: {colors.text_primary}; font-size: 16px; font-weight: 700;")

        for stat in [self.stat_members, self.stat_channels, self.stat_roles, self.stat_boosts]:
            stat.setStyleSheet(f"color: {colors.text_secondary}; font-size: 12px;")

        for frame in self.findChildren(QFrame):
            frame.setStyleSheet(f"background-color: {colors.divider};")

        self.status_banner.refresh_theme()
