"""Centralized filesystem layout for the desktop app."""

from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path


def _project_root() -> Path:
    """Return the directory that contains config/ and data/.

    When running from source: the repo root (two levels above this file).
    When running as a PyInstaller one-file exe: the directory containing the
    exe, so that config/ and data/ live next to ABUSER.exe.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _project_root()


def _env_or_path(env_var: str, relative_path: str) -> Path:
    override = os.environ.get(env_var)
    return Path(override) if override else PROJECT_ROOT / relative_path


def config_dir() -> Path:
    return _env_or_path("ABUSER_CONFIG_DIR", "config")


def data_dir() -> Path:
    return _env_or_path("ABUSER_DATA_DIR", "data")


def bot_config_path() -> Path:
    return _env_or_path("ABUSER_BOT_CONFIG_PATH", "config/config.json")


def gui_config_path() -> Path:
    return _env_or_path("ABUSER_GUI_CONFIG_PATH", "config/gui_config.json")


def theme_config_path() -> Path:
    return _env_or_path("ABUSER_THEME_CONFIG_PATH", "config/theme_config.json")


def env_file_path() -> Path:
    return _env_or_path("ABUSER_ENV_PATH", "config/.env")


def tokens_path() -> Path:
    return _env_or_path("ABUSER_TOKENS_PATH", "data/tokens.json")


def legacy_token_file_path() -> Path:
    return _env_or_path("ABUSER_TKN_PATH", "data/tkn.txt")


def logs_dir() -> Path:
    return _env_or_path("ABUSER_LOG_DIR", "data/logs")


def log_file_path() -> Path:
    return _env_or_path("ABUSER_LOG_FILE", "data/logs/abuse.log")


LEGACY_ROOT_FILES = {
    PROJECT_ROOT / "config.json": bot_config_path,
    PROJECT_ROOT / "gui_config.json": gui_config_path,
    PROJECT_ROOT / "theme_config.json": theme_config_path,
    PROJECT_ROOT / "tokens.json": tokens_path,
    PROJECT_ROOT / "tkn.txt": legacy_token_file_path,
    PROJECT_ROOT / ".env": env_file_path,
}


def ensure_runtime_dirs() -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    data_dir().mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)


def _move_file_if_needed(source: Path, target: Path) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    shutil.move(str(source), str(target))


def _move_logs_dir() -> None:
    source = PROJECT_ROOT / "logs"
    destination = logs_dir()
    if not source.exists() or source.resolve() == destination.resolve():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        target = destination / child.name
        if target.exists():
            continue
        shutil.move(str(child), str(target))
    try:
        source.rmdir()
    except OSError:
        pass


def migrate_legacy_layout() -> None:
    ensure_runtime_dirs()
    for source, target_factory in LEGACY_ROOT_FILES.items():
        _move_file_if_needed(source, target_factory())
    _move_logs_dir()


def bootstrap_runtime_layout() -> None:
    migrate_legacy_layout()
