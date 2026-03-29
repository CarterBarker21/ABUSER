import json

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication

from abuse.gui import MainWindow


class FakeBotRunner(QObject):
    login_success = pyqtSignal(str, str)
    login_failed = pyqtSignal(str)
    logout_completed = pyqtSignal()
    guilds_updated = pyqtSignal(list)
    log_received = pyqtSignal(str, str)
    status_changed = pyqtSignal(str)
    connection_state_changed = pyqtSignal(bool)
    latency_updated = pyqtSignal(float)
    nuke_action_completed = pyqtSignal(str, bool, str)
    setup_server_completed = pyqtSignal(bool, str)

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


def _color_distance(color_a, color_b):
    return (
        abs(color_a.red() - color_b.red())
        + abs(color_a.green() - color_b.green())
        + abs(color_a.blue() - color_b.blue())
    )


def test_app_startup_and_navigation(qtbot):
    window = build_window(qtbot)

    assert window.content_stack.count() == 9
    # Theme name depends on persisted config; just verify it loaded something valid
    assert window.theme_manager.theme.name in (
        "Midnight", "Discord Dark", "Tokyo Night", "Catppuccin Mocha", "Dracula"
    )
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

    window.settings_tab.preset_combo.setCurrentText("Discord Dark")
    window.settings_tab.accent_combo.setCurrentText("Cyan")
    window.settings_tab.font_size_spin.setValue(15)
    window.settings_tab.startup_combo.setCurrentText("Guilds")
    window.settings_tab._apply_changes()

    config_path = window.settings_tab.current_config()
    assert config_path["behavior"]["startup_page"] == "Guilds"
    assert window.theme_manager.theme.name == "Discord Dark"
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

    from abuse.gui.pages.guilds import GuildStatCard
    guild_cards = [c for c in window.guilds_tab._guild_cards if isinstance(c, GuildStatCard)]
    assert len(guild_cards) == 2
    assert window.status_panel.guilds_value.text() == "2"
    assert window.status_panel.ping_value.text() == "123 ms"
    assert len(window.logs_tab._entries) == 1


def test_preview_only_controls_are_disabled(qtbot):
    window = build_window(qtbot)

    # DM tab send button should be disabled when not connected
    assert not window.dm_tab.send_button.isEnabled()

    # Nuker execute/select buttons should be disabled when not connected and no guild selected
    assert not window.nuker_tab.execute_btn.isEnabled()
    assert not window.nuker_tab.select_all_btn.isEnabled()

    # Connect fake bot runner to test enabled state
    fake_runner = FakeBotRunner()
    fake_runner.is_running = True
    window.connect_bot_runner(fake_runner)

    # Simulate login success
    fake_runner.login_success.emit("TestUser", "123456789")

    # After login, nuker tab should be marked as connected
    assert window.nuker_tab._is_connected

    # But buttons still disabled because no guild selected
    assert not window.nuker_tab.execute_btn.isEnabled()

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

    # Now action buttons should be enabled
    assert window.nuker_tab.execute_btn.isEnabled()


def test_title_bar_controls_are_present_and_sized(qtbot):
    window = build_window(qtbot)

    assert window.title_bar.height() == window.title_bar.FIXED_HEIGHT
    assert window.title_bar.minimize_btn.isEnabled()
    assert window.title_bar.close_btn.isEnabled()
    assert window.title_bar.minimize_btn.width() == 30
    assert window.title_bar.close_btn.width() == 30
    assert window.title_bar.minimize_btn.width() == window.title_bar.minimize_btn.height()
    assert window.title_bar.close_btn.width() == window.title_bar.close_btn.height()


def test_expanded_sidebar_uses_full_width_left_aligned_rows(qtbot):
    window = build_window(qtbot)

    sidebar_layout = window.sidebar.layout()
    margins = sidebar_layout.contentsMargins()
    available_width = window.sidebar.width() - margins.left() - margins.right()
    button = window.route_buttons["login"]

    assert button.geometry().x() == margins.left()
    assert button.width() >= available_width - 2
    assert button.icon_label.geometry().x() < button.title_label.geometry().x()


def test_sidebar_brand_block_is_removed(qtbot):
    window = build_window(qtbot)

    assert not window._brand_widget.isVisible()

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)

    assert not window._brand_widget.isVisible()


def test_title_bar_renders_a_distinct_surface(qtbot):
    window = build_window(qtbot)

    assert window.title_bar.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    title_image = window.title_bar.grab().toImage()
    content_image = window.content_shell.grab().toImage()
    sample_x = title_image.width() // 2
    title_color = title_image.pixelColor(sample_x, window.title_bar.height() // 2)
    content_color = content_image.pixelColor(
        min(sample_x, content_image.width() - 1),
        min(40, content_image.height() - 1),
    )

    assert _color_distance(title_color, content_color) >= 110


def test_sidebar_collapse_updates_tooltip_width_and_label_visibility(qtbot):
    window = build_window(qtbot)

    expanded_width = window.sidebar.width()
    assert not window._sidebar_collapsed
    assert not window._collapse_btn.isChecked()
    assert window.route_buttons["login"].title_label.isVisible()
    assert window.status_panel.isVisible()
    assert not window.sidebar_status_pill.isVisible()

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)

    assert window._sidebar_collapsed
    assert window._collapse_btn.isChecked()
    assert window.sidebar.width() < expanded_width
    assert not window.route_buttons["login"].title_label.isVisible()
    assert window.route_buttons["login"].icon_label.isVisible()
    assert window.route_buttons["login"].icon_label.pixmap() is not None
    assert not window.status_panel.isVisible()
    assert window.sidebar_status_pill.isVisible()
    assert window.sidebar_status_pill.text() == "Offline"

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)

    assert not window._sidebar_collapsed
    assert not window._collapse_btn.isChecked()
    assert window.sidebar.width() == expanded_width
    assert window.route_buttons["login"].title_label.isVisible()
    assert window.status_panel.isVisible()
    assert not window.sidebar_status_pill.isVisible()


def test_collapsed_sidebar_buttons_fit_inside_icon_rail(qtbot):
    window = build_window(qtbot)

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)

    sidebar_layout = window.sidebar.layout()
    margins = sidebar_layout.contentsMargins()
    available_width = window.sidebar.width() - margins.left() - margins.right()

    for button in window.route_buttons.values():
        assert button.width() <= available_width
        assert button.geometry().x() >= margins.left()
        assert button.geometry().right() <= window.sidebar.width() - margins.right()


def test_collapsed_sidebar_buttons_use_compact_rail_sizing(qtbot):
    window = build_window(qtbot)
    expanded_button = window.route_buttons["login"]
    expanded_height = expanded_button.height()

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)

    collapsed_button = window.route_buttons["login"]
    assert window.sidebar.width() == 84
    assert collapsed_button.width() == 56
    assert collapsed_button.height() == 44
    assert collapsed_button.icon_label.width() == 18
    assert collapsed_button.icon_label.height() == 18
    assert collapsed_button.height() == 44  # collapsed buttons are intentionally taller than wide


def test_nuker_actions_do_not_wrap_standard_groups_in_extra_panels(qtbot):
    window = build_window(qtbot)

    assert not hasattr(window.nuker_tab, "_group_panels")
    assert not hasattr(window.nuker_tab, "_danger_panel")


def test_collapsed_sidebar_status_pill_tracks_connection_state(qtbot):
    window = build_window(qtbot)
    runner = FakeBotRunner()
    window.connect_bot_runner(runner)

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)
    assert window.sidebar_status_pill.text() == "Offline"

    runner.login_success.emit("tester", "123")

    assert window.sidebar_status_pill.isVisible()
    assert window.sidebar_status_pill.text() == "Online"

    runner.logout_completed.emit()

    assert window.sidebar_status_pill.text() == "Offline"
