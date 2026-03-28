import json

import pytest


@pytest.fixture(autouse=True)
def gui_test_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("ABUSER_GUI_CONFIG_PATH", str(tmp_path / "gui_config.json"))
    monkeypatch.setenv("ABUSER_TOKENS_PATH", str(tmp_path / "tokens.json"))
    monkeypatch.setenv("ABUSER_THEME_CONFIG_PATH", str(tmp_path / "theme_config.json"))

    import abuse.gui.theme as theme_module

    theme_module._theme_manager = None
    with open(tmp_path / "gui_config.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "appearance": {
                    "preset": "Discord Dark",
                    "theme_mode": 0,
                    "accent": "Red",
                    "font_size": 13,
                },
                "behavior": {
                    "startup_page": "Login",
                    "last_route": "login",
                },
                "privacy": {
                    "save_tokens": True,
                },
            },
            handle,
            indent=2,
        )

    yield
    theme_module._theme_manager = None
