"""Application settings and user preferences storage for MangoMod."""

from __future__ import annotations

import json
from pathlib import Path

from mangomod import config_parser

_SETTINGS_FILE = config_parser.APP_SETTINGS_DIR / "settings.json"

_DEFAULTS: dict = {
    "auto_backup": True,
    "backup_limit": 10,
    "hot_reload_on_save": True,
    "validate_on_save": True,
    "keyboard_geometry": "ANSI",
    "theme_accent": "mango_amber",
    "theme": "mango-dark",
    "color_scheme": "dark",
}

_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if _SETTINGS_FILE.exists():
        try:
            data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
            _cache = {**_DEFAULTS, **data}
            return _cache
        except Exception:
            pass
    _cache = dict(_DEFAULTS)
    return _cache


def _save(data: dict) -> None:
    global _cache
    config_parser.APP_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _cache = data


def get(key: str, default=None):
    return _load().get(key, default)


def set(key: str, value):  # noqa: A001
    data = dict(_load())
    data[key] = value
    _save(data)
