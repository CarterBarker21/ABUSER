"""Main window for the refactored desktop GUI."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .bot_runner import BotRunner
from .components import SidebarNavButton, SidebarStatusPanel, blend, rgba
from .config import load_gui_config, save_gui_config, update_last_route
from .pages import DMPage, DocsPage, GuildItem, GuildsPage, LoginPage, LogsPage, NukerPage, SettingsPage
from .routes import (
    ROUTE_DOCS,
    ROUTE_DM,
    ROUTE_GUILDS,
    ROUTE_LABELS,
    ROUTE_LAST_USED,
    ROUTE_LOGIN,
    ROUTE_LOGS,
    ROUTE_NUKER,
    ROUTE_SETTINGS,
    ROUTES,
    get_route_index,
    normalize_route,
    route_from_label,
)
from .theme import get_theme_manager


class MainWindow(QMainWindow):
    """Main application window for the desktop GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ABUSER")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self.theme_manager = get_theme_manager()
        self.theme_manager.set_theme_changed_callback(self._on_theme_changed)

        self.bot_runner: Optional[BotRunner] = None
        self._current_route = ROUTE_LOGIN
        self._config = load_gui_config()

        self._build_ui()
        self._connect_page_signals()
        self.refresh_theme()
        self.switch_route(ROUTE_LOGIN, persist=False)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("mainShell")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar)

        self.content_shell = QWidget()
        self.content_shell.setObjectName("contentShell")
        self.content_layout = QVBoxLayout(self.content_shell)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        root.addWidget(self.content_shell, 1)

        self.top_rail = QFrame()
        self.top_rail.setObjectName("topRail")
        self.top_rail.setFixedHeight(42)
        rail_layout = QHBoxLayout(self.top_rail)
        rail_layout.setContentsMargins(24, 0, 24, 0)
        rail_layout.setSpacing(12)
        self.rail_title = QLabel("Discord.gg/ABUSER")
        self.rail_detail = QLabel("Desktop UI")
        rail_layout.addWidget(self.rail_title)
        rail_layout.addStretch(1)
        rail_layout.addWidget(self.rail_detail)
        self.content_layout.addWidget(self.top_rail)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        self.content_layout.addWidget(self.content_stack, 1)

        self.login_tab = LoginPage()
        self.docs_tab = DocsPage()
        self.guilds_tab = GuildsPage()
        self.nuker_tab = NukerPage()
        self.dm_tab = DMPage()
        self.logs_tab = LogsPage()
        self.settings_tab = SettingsPage()

        self.pages = {
            ROUTE_LOGIN: self.login_tab,
            ROUTE_DOCS: self.docs_tab,
            ROUTE_GUILDS: self.guilds_tab,
            ROUTE_NUKER: self.nuker_tab,
            ROUTE_DM: self.dm_tab,
            ROUTE_LOGS: self.logs_tab,
            ROUTE_SETTINGS: self.settings_tab,
        }

        for route in ROUTES:
            self.content_stack.addWidget(self.pages[route.key])

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebarShell")
        sidebar.setFixedWidth(self.theme_manager.tokens.metrics.sidebar_width)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 0)
        layout.setSpacing(18)

        brand_column = QVBoxLayout()
        brand_column.setContentsMargins(0, 0, 0, 0)
        brand_column.setSpacing(6)
        layout.addLayout(brand_column)

        self.brand_title = QLabel("ABUSER")
        self.brand_meta = QLabel("Discord SelfBot | v1.5")
        brand_column.addWidget(self.brand_title)
        brand_column.addWidget(self.brand_meta)

        self.nav_heading = QLabel("NAVIGATION")
        layout.addWidget(self.nav_heading)

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
            for child in self.sidebar.findChildren(QFrame):
                if child.objectName() == "sidebarDivider":
                    child.setVisible(False)
            self.status_panel.setVisible(False)
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
            self.status_panel.setVisible(True)

    def _connect_page_signals(self) -> None:
        self.nuker_tab.nuke_action_requested.connect(self._on_nuke_action_requested)
        self.nuker_tab.setup_server_requested.connect(self._on_setup_server_requested)
        self.settings_tab.settings_applied.connect(self._on_settings_applied)

    def connect_bot_runner(self, bot_runner: BotRunner) -> None:
        self.bot_runner = bot_runner

        self.login_tab.login_requested.connect(self.bot_runner.start_bot)
        self.login_tab.logout_requested.connect(self.bot_runner.stop_bot)
        self.guilds_tab.refresh_requested.connect(self.bot_runner.refresh_guilds)

        self.bot_runner.login_success.connect(self._on_login_success)
        self.bot_runner.login_failed.connect(self._on_login_failed)
        self.bot_runner.logout_completed.connect(self._on_logout_completed)
        self.bot_runner.guilds_updated.connect(self._on_guilds_updated)
        self.bot_runner.log_received.connect(self._on_log_received)
        self.bot_runner.status_changed.connect(self._on_status_changed)
        self.bot_runner.connection_state_changed.connect(self._on_connection_state_changed)
        self.bot_runner.latency_updated.connect(self._on_latency_updated)
        self.bot_runner.nuke_action_completed.connect(self.nuker_tab.on_action_completed)
        self.bot_runner.setup_server_requested.connect(self.nuker_tab.on_setup_completed)

    def switch_ui_theme(self, theme_name: str, accent: Optional[str] = None):
        return self.theme_manager.switch_theme(theme_name, accent)

    def get_available_themes(self):
        return self.theme_manager.get_available_themes()

    def get_available_accents(self):
        return self.theme_manager.get_available_accents()

    def switch_tab(self, index: int):
        if 0 <= index < len(ROUTES):
            self.switch_route(ROUTES[index].key)

    def switch_route(self, route_key: str, persist: bool = True) -> None:
        route_key = normalize_route(route_key)
        self._current_route = route_key
        self.content_stack.setCurrentIndex(get_route_index(route_key))

        for key, button in self.route_buttons.items():
            button.setChecked(key == route_key)
            button.refresh_theme()

        self.rail_detail.setText(ROUTE_LABELS.get(route_key, "Desktop UI"))
        if persist:
            update_last_route(route_key)

    def _status_tone(self, message: str) -> str:
        message = message.lower()
        if "ready" in message or "connected" in message:
            return "success"
        if "error" in message or "fail" in message:
            return "danger"
        if "starting" in message or "connecting" in message or "stopping" in message:
            return "warning"
        return "neutral"

    def _on_login_success(self, user_name: str, _user_id: str) -> None:
        token = self.login_tab.token_input.text().strip()
        self.login_tab.save_token_if_requested(token, user_name)
        self.login_tab.on_login_success(user_name)
        self.status_panel.set_connection_state(True, user_name, f"Ready as {user_name}")
        self.guilds_tab.set_connected(True, user_name)
        self.nuker_tab.set_connected(True)
        self.switch_route(ROUTE_GUILDS)

    def _on_login_failed(self, error_message: str) -> None:
        self.login_tab.show_error(error_message)
        self.status_panel.set_connection_state(False, message=error_message)
        self.switch_route(ROUTE_LOGIN)

    def _on_logout_completed(self) -> None:
        self.login_tab.on_logout()
        self.guilds_tab.set_connected(False)
        self.nuker_tab.set_connected(False)
        self.nuker_tab.set_selected_guild(None)
        self.status_panel.set_connection_state(False)
        self.switch_route(ROUTE_LOGIN)

    def _on_guilds_updated(self, guild_list: list[dict]) -> None:
        from datetime import datetime
        guilds: list[GuildItem] = []
        for guild in guild_list:
            # Parse created_at from ISO format if present
            created_at = None
            if guild.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(guild["created_at"])
                except (ValueError, TypeError):
                    pass
            
            is_owner_val = guild.get("is_owner", False)
            
            # Debug: Log is_owner for all servers to check data type
            print(f"[MAIN WINDOW DEBUG] Server: {guild['name']}, is_owner={is_owner_val}, type={type(is_owner_val)}")
            
            # Debug: Log is_owner for owned servers
            if is_owner_val:
                print(f"[MAIN WINDOW DEBUG] Creating GuildItem for OWNED server: {guild['name']}, is_owner={is_owner_val}")
            
            item = GuildItem(
                guild_id=int(guild["id"]),
                name=guild["name"],
                member_count=guild.get("member_count", 0) or 0,
                icon_url=guild.get("icon_url"),
                owner_id=int(guild["owner_id"]) if guild.get("owner_id") else None,
                created_at=created_at,
                channels_count=guild.get("channels_count", 0) or 0,
                roles_count=guild.get("roles_count", 0) or 0,
                boost_count=guild.get("boost_count", 0) or 0,
                my_permissions=guild.get("my_permissions", 0) or 0,
                is_owner=is_owner_val,
                icon_data=guild.get("icon_data"),  # Pass icon bytes to UI
            )
            guilds.append(item)
        self.guilds_tab.update_guilds(guilds)
        self.nuker_tab.update_guild_list(guilds)
        self.status_panel.set_guild_count(len(guilds))

    def _on_log_received(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        name = "Bot"
        parsed_level = level.upper()
        parsed_message = message

        parts = message.split(" - ", 3)
        if len(parts) == 4:
            timestamp, name, parsed_level, parsed_message = parts

        self.logs_tab.add_log(timestamp, name, parsed_level, parsed_message)

    def _on_status_changed(self, message: str) -> None:
        tone = self._status_tone(message)
        self.status_panel.set_status_message(message, tone)
        if tone == "success" and self.bot_runner and self.bot_runner.user_name:
            self.status_panel.set_connection_state(True, self.bot_runner.user_name, message)

    def _on_connection_state_changed(self, is_connected: bool) -> None:
        if not is_connected and self.bot_runner and not self.bot_runner.is_running:
            self.status_panel.set_connection_state(False)
            self.guilds_tab.set_connected(False)

    def _on_latency_updated(self, ping_ms: float) -> None:
        self.status_panel.set_ping(ping_ms)

    def _on_nuke_requested(self, guild) -> None:
        """Handle nuke button click from Guilds page - switch to Nuker with guild pre-selected."""
        # Switch to Nuker tab with the guild pre-selected
        self.nuker_tab.set_selected_guild(guild)
        self.switch_route(ROUTE_NUKER)
    
    def _on_nuke_action_requested(self, action_id: str, guild_id_str: str) -> None:
        """Handle nuke action request from Nuker page."""
        # Convert guild_id from string to int (passed as string to avoid 32-bit truncation)
        guild_id = int(guild_id_str)
        
        if not self.bot_runner:
            QMessageBox.warning(self, "Error", "Bot runner not available.")
            return
        
        if not self.bot_runner.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to Discord first.")
            return
        
        # Verify the guild exists in the bot's guild list
        available_guild_ids = [g.guild_id for g in self.guilds_tab._guilds.values()] if hasattr(self.guilds_tab, '_guilds') else []
        
        if guild_id not in available_guild_ids:
            QMessageBox.warning(
                self, 
                "Guild Not Available", 
                f"Guild {guild_id} is not in the list of available guilds.\n\n"
                f"Available guilds: {available_guild_ids}\n\n"
                f"Please select a different guild from the Guilds tab."
            )
            return
        
        # Execute the action through the bot runner
        success = self.bot_runner.execute_nuke_action(action_id, guild_id)
        if not success:
            self.nuker_tab.on_action_completed(action_id, False, "Failed to queue action")

    def _on_setup_server_requested(self, guild_id_str: str) -> None:
        """Handle setup server request from Nuker page."""
        # Convert guild_id from string to int (passed as string to avoid 32-bit truncation)
        guild_id = int(guild_id_str)
        
        if not self.bot_runner:
            QMessageBox.warning(self, "Error", "Bot runner not available.")
            return
        
        if not self.bot_runner.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to Discord first.")
            return
        
        # Verify the guild exists in the bot's guild list
        available_guild_ids = [g.guild_id for g in self.guilds_tab._guilds.values()] if hasattr(self.guilds_tab, '_guilds') else []
        if guild_id not in available_guild_ids:
            QMessageBox.warning(
                self, 
                "Guild Not Available", 
                f"Guild {guild_id} is not in the list of available guilds.\n\n"
                f"Please select a guild from the Guilds tab first."
            )
            return
        
        # Execute the setup through the bot runner
        success = self.bot_runner.execute_setup_server(guild_id)
        if not success:
            self.nuker_tab.on_setup_completed(False, "Failed to queue setup action")

    def _on_settings_applied(self, config: dict) -> None:
        self._config = config
        save_gui_config(config)
        self.apply_settings(config)

    def apply_settings(self, config: dict) -> None:
        self._config = config
        appearance = config.get("appearance", {})

        preset = appearance.get("preset", "Discord Dark")
        accent = appearance.get("accent", "Red").lower().replace(" ", "_")
        self.theme_manager.switch_theme(preset, accent)
        self.theme_manager.save_theme()

        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(appearance.get("font_size", 13))
            app.setFont(font)

        self.login_tab.set_privacy_options(config.get("privacy", {}).get("save_tokens", True))
        if not self.login_tab.is_connected:
            self.login_tab.load_saved_tokens()
        self.settings_tab.load_from_config(config)
        self.refresh_theme()

    def load_and_apply_settings(self) -> None:
        self._config = load_gui_config()
        self.apply_settings(self._config)

        startup_label = self._config.get("behavior", {}).get("startup_page", "Login")
        if startup_label == "Last Used":
            route_key = normalize_route(self._config.get("behavior", {}).get("last_route", ROUTE_LOGIN))
        else:
            route_key = route_from_label(startup_label)
        self.switch_route(route_key, persist=False)

    def _on_theme_changed(self, _theme) -> None:
        self.refresh_theme()

    def refresh_theme(self) -> None:
        colors = self.theme_manager.tokens.colors

        self.setStyleSheet(f"QMainWindow {{ background-color: {colors.bg_primary}; }}")

        central = self.centralWidget()
        if central is not None:
            central.setStyleSheet(f"QWidget#mainShell {{ background-color: {colors.bg_primary}; }}")

        self.sidebar.setStyleSheet(
            f"""
            QFrame#sidebarShell {{
                background-color: {colors.bg_secondary};
                border-right: 1px solid {rgba(colors.border_light, 0.9)};
            }}
            """
        )
        self.brand_title.setStyleSheet(
            f"color: {colors.text_primary}; font-size: 18px; font-weight: 700; letter-spacing: 2px;"
        )
        self.brand_meta.setStyleSheet(f"color: {colors.text_muted}; font-size: 11px;")
        self.nav_heading.setStyleSheet(
            f"color: {colors.text_muted}; font-size: 10px; font-weight: 700; letter-spacing: 1.4px;"
        )

        self.top_rail.setStyleSheet(
            f"""
            QFrame#topRail {{
                background-color: {blend(colors.bg_secondary, colors.bg_primary, 0.22)};
                border-bottom: 1px solid {rgba(colors.border_light, 0.85)};
            }}
            """
        )
        self.rail_title.setStyleSheet(f"color: {colors.text_primary}; font-weight: 700;")
        self.rail_detail.setStyleSheet(f"color: {colors.text_secondary};")
        self.content_shell.setStyleSheet(f"QWidget#contentShell {{ background-color: {colors.bg_primary}; }}")
        self.content_stack.setStyleSheet(f"QStackedWidget#contentStack {{ background-color: {colors.bg_primary}; }}")

        for button in self.route_buttons.values():
            button.refresh_theme()

        self.status_panel.refresh_theme()
        for page in self.pages.values():
            refresh = getattr(page, "refresh_theme", None)
            if callable(refresh):
                refresh()

        tm = self.theme_manager.theme
        for child in self.sidebar.findChildren(QFrame):
            if child.objectName() == "sidebarDivider":
                child.setStyleSheet(f"background-color: {tm.divider}; border: none;")

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
