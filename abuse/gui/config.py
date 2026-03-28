"""Configuration helpers for the desktop GUI."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Optional

from abuse.app_paths import gui_config_path as shared_gui_config_path
from abuse.app_paths import migrate_legacy_layout
from abuse.app_paths import tokens_path as shared_tokens_path


DEFAULT_GUI_CONFIG: Dict[str, Any] = {
    "appearance": {
        "preset": "Discord Dark",
        "theme_mode": 0,
        "accent": "Red",
        "font_size": 13,
        "animations": True,
        "transparency": False,
        "compact": False,
    },
    "behavior": {
        "confirm_actions": True,
        "log_commands": True,
        "minimize_tray": False,
        "auto_start": False,
        "auto_update": True,
        "startup_page": "Login",
        "last_route": "login",
    },
    "bot": {
        "prefix": ".",
        "timeout": 30,
        "case_sensitive": False,
        "mention_prefix": True,
        "delete_commands": False,
    },
    "notifications": {
        "notify_errors": True,
        "notify_success": True,
        "notify_updates": True,
        "sound_effects": False,
    },
    "privacy": {
        "save_tokens": True,
        "encrypt_tokens": False,
        "analytics": False,
    },
    "version": "2.0",
}


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def gui_config_path():
    migrate_legacy_layout()
    return shared_gui_config_path()


def tokens_path():
    migrate_legacy_layout()
    return shared_tokens_path()


def load_gui_config() -> Dict[str, Any]:
    path = gui_config_path()
    if not path.exists():
        return deepcopy(DEFAULT_GUI_CONFIG)

    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception:
        return deepcopy(DEFAULT_GUI_CONFIG)

    return _merge_dicts(DEFAULT_GUI_CONFIG, raw)


def save_gui_config(config: Dict[str, Any]) -> bool:
    path = gui_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = _merge_dicts(DEFAULT_GUI_CONFIG, config)
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(merged, handle, indent=2)
        return True
    except Exception:
        return False


def update_last_route(route_key: str) -> bool:
    config = load_gui_config()
    config.setdefault("behavior", {})["last_route"] = route_key
    return save_gui_config(config)


def load_remembered_sessions() -> list[dict[str, Any]]:
    path = tokens_path()
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return []

    accounts = data.get("accounts", [])
    return [account for account in accounts if isinstance(account, dict) and account.get("token")]


def get_latest_session() -> Optional[dict[str, Any]]:
    sessions = load_remembered_sessions()
    if not sessions:
        return None

    def sort_key(item: dict[str, Any]) -> tuple[str, str]:
        return (
            item.get("last_used", ""),
            item.get("added_at", ""),
        )

    return sorted(sessions, key=sort_key, reverse=True)[0]


def save_remembered_session(token: str, username: str = "Unknown") -> bool:
    token = token.strip()
    if not token:
        return False

    path = tokens_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        else:
            data = {"accounts": []}
    except Exception:
        data = {"accounts": []}

    accounts = [account for account in data.get("accounts", []) if isinstance(account, dict)]
    now = datetime.now().isoformat(timespec="seconds")
    existing = next((account for account in accounts if account.get("token") == token), None)

    if existing:
        existing["name"] = username or existing.get("name", "Unknown")
        existing["last_used"] = now
    else:
        accounts.insert(
            0,
            {
                "token": token,
                "name": username or "Unknown",
                "added_at": now,
                "last_used": now,
            },
        )

    data["accounts"] = accounts[:10]
    data["last_updated"] = now

    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        return True
    except Exception:
        return False


def clear_remembered_sessions() -> bool:
    path = tokens_path()
    if not path.exists():
        return True

    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"accounts": [], "last_updated": datetime.now().isoformat(timespec="seconds")}, handle, indent=2)
        return True
    except Exception:
        return False


def mask_token(token: str) -> str:
    token = token.strip()
    if len(token) <= 10:
        return token
    return f"{token[:4]}...{token[-4:]}"
