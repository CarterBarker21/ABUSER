import json

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from abuse.gui import MainWindow
from abuse.gui.components import ActionTileButton


class FakeBotRunner(QObject):
    login_success = pyqtSignal(str, str)
    login_failed = pyqtSignal(str)
    logout_completed = pyqtSignal()
    guilds_updated = pyqtSignal(list)
    log_received = pyqtSignal(str, str)
    status_changed = pyqtSignal(str)
    connection_state_changed = pyqtSignal(bool)
    latency_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.started_token = None
        self.stopped = False
        self.refreshes = 0
        self.is_running = False
        self.is_connected = False
        self.user_name = None

    def start_bot(self, token):
        self.started_token = token
        self.is_running = True
        return True

    def stop_bot(self):
        self.stopped = True
        self.is_running = False
        return True

    def refresh_guilds(self):
        self.refreshes += 1
        return True


def build_window(qtbot):
    window = MainWindow()
    window.load_and_apply_settings()
    qtbot.addWidget(window)
    window.show()
    return window


def test_app_startup_and_navigation(qtbot):
    window = build_window(qtbot)

    assert window.content_stack.count() == 7
    assert window.theme_manager.theme.name == "Discord Dark"
    assert window.theme_manager.theme.accent.name == "RED"
    assert window.route_buttons["login"].icon_label.pixmap() is not None
    window.switch_route("docs")
    assert window._current_route == "docs"
    assert window.route_buttons["docs"].isChecked()


def test_post_login_routes_to_guilds(qtbot):
    window = build_window(qtbot)
    runner = FakeBotRunner()
    window.connect_bot_runner(runner)

    token = "x" * 60
    window.login_tab.token_input.setText(token)
    runner.login_success.emit("tester", "123")

    assert window._current_route == "guilds"
    assert window.status_panel.user_value.text() == "tester"
    assert window.login_tab.primary_button.text() == "Disconnect"


def test_settings_apply_persists_and_updates_theme(qtbot):
    window = build_window(qtbot)

    window.settings_tab.preset_combo.setCurrentText("Obsidian")
    window.settings_tab.accent_combo.setCurrentText("Cyan")
    window.settings_tab.font_size_spin.setValue(15)
    window.settings_tab.startup_combo.setCurrentText("Guilds")
    window.settings_tab._apply_changes()

    config_path = window.settings_tab.current_config()
    assert config_path["behavior"]["startup_page"] == "Guilds"
    assert window.theme_manager.theme.name == "Obsidian"
    assert window.theme_manager.theme.accent.name == "CYAN"
    assert QApplication.instance().font().pointSize() == 15


def test_remembered_session_is_loaded_honestly(qtbot, tmp_path):
    token = "remembered-token-value-" * 3
    with open(tmp_path / "tokens.json", "w", encoding="utf-8") as handle:
        json.dump({"accounts": [{"token": token, "name": "Saved Account"}]}, handle)

    window = build_window(qtbot)
    assert window.login_tab.token_input.text() == token
    assert window.login_tab.saved_session_combo.count() == 2
    assert "Saved Account" in window.login_tab.status_banner.message_label.text()


def test_remembered_session_survives_restart(qtbot):
    first_window = build_window(qtbot)
    runner = FakeBotRunner()
    first_window.connect_bot_runner(runner)

    token = "persisted-token-value-" * 3
    first_window.login_tab.token_input.setText(token)
    first_window.login_tab.remember_toggle.setChecked(True)
    runner.login_success.emit("persisted-user", "321")
    first_window.close()

    second_window = build_window(qtbot)
    assert second_window.login_tab.token_input.text() == token
    assert second_window.login_tab.saved_session_combo.count() == 2
    assert "persisted-user" in second_window.login_tab.status_banner.message_label.text()


def test_guild_status_and_logs_update_from_runner(qtbot):
    window = build_window(qtbot)
    runner = FakeBotRunner()
    runner.user_name = "tester"
    window.connect_bot_runner(runner)

    runner.guilds_updated.emit(
        [
            {"id": "1", "name": "Alpha", "member_count": 4, "owner_id": "10"},
            {"id": "2", "name": "Beta", "member_count": 9, "owner_id": "11"},
        ]
    )
    runner.status_changed.emit("Ready as tester")
    runner.latency_updated.emit(123.0)
    runner.log_received.emit("INFO", "12:00:00 - ABUSER - INFO - Started")

    assert window.guilds_tab.guild_list.count() == 2
    assert window.status_panel.guilds_value.text() == "2"
    assert window.status_panel.ping_value.text() == "123 ms"
    assert len(window.logs_tab._entries) == 1


def test_preview_only_controls_are_disabled(qtbot):
    window = build_window(qtbot)

    # DM tab send button should be disabled when not connected
    assert not window.dm_tab.send_button.isEnabled()
    
    # Nuker buttons should be disabled when not connected and no guild selected
    preview_tiles = window.nuker_tab.findChildren(ActionTileButton)
    assert preview_tiles
    assert all(not tile.isEnabled() for tile in preview_tiles)
    
    # Connect fake bot runner to test enabled state
    fake_runner = FakeBotRunner()
    fake_runner.is_running = True
    window.connect_bot_runner(fake_runner)
    
    # Simulate login success
    fake_runner.login_success.emit("TestUser", "123456789")
    
    # After login, nuker tab should be marked as connected
    assert window.nuker_tab._is_connected
    
    # But buttons still disabled because no guild selected
    assert all(not tile.isEnabled() for tile in preview_tiles)
    
    # Simulate guild selection
    from abuse.gui.pages import GuildItem
    from datetime import datetime
    test_guild = GuildItem(
        guild_id=123456789,
        name="Test Server",
        member_count=100,
        icon_url=None,
        owner_id=987654321,
        created_at=datetime.now(),
        channels_count=10,
        roles_count=5,
    )
    window.nuker_tab.set_selected_guild(test_guild)
    
    # Now buttons should be enabled
    assert all(tile.isEnabled() for tile in preview_tiles)
