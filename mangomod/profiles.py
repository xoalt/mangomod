"""Named config profiles: save, load, and switch Mango config snapshots."""

from __future__ import annotations

import shutil
from pathlib import Path

from mangomod import config_parser, snapshots


def presets_dir() -> Path:
    return config_parser.MANGO_CONFIG.parent / 'presets'


def _location(name: str) -> Path:
    validate_name(name)
    for root in (presets_dir(), config_parser.PROFILES_DIR):
        for path in (root / name, root / f'{name}.conf'):
            if path.exists():
                return path
    raise FileNotFoundError(name)


def validate_name(name: str) -> None:
    if (not name.strip() or name != name.strip() or len(name) > 80 or name.startswith('.')
            or any(c in name for c in '/\\\n\r\0')):
        raise ValueError('Choose a profile name without path characters.')


def list_profiles() -> list[str]:
    """List all saved profile names."""
    names = []
    for root in (presets_dir(), config_parser.PROFILES_DIR):
        if root.exists():
            names += [p.stem for p in root.glob('*.conf')]
            names += [p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith('.')]
    return sorted(list(set(names)))


def save_profile(name: str, source_files: set[Path] | None = None, texts: dict[str, str] | None = None) -> None:
    """Save the current configuration as a named profile."""
    validate_name(name)
    if name in list_profiles():
        raise ValueError('A profile with this name already exists.')
    sources = set(source_files or {config_parser.MANGO_CONFIG}) | {Path(p) for p in (texts or {})}
    snapshots.create(presets_dir() / name, sources, texts)


def load_profile(name: str) -> bool:
    """Activate either a new preset or a legacy profile with checked recovery."""
    from mangomod.state import AppState
    validate_name(name)
    try:
        state = AppState()
        state.load()
        ok, _message = state.apply_files(read_profile(name))
        return ok
    except (OSError, ValueError, KeyError, TypeError):
        return False


def read_profile(name: str) -> dict[Path, bytes]:
    validate_name(name)
    directory = _location(name)
    if directory.is_dir():
        return snapshots.contents(directory)
    return {config_parser.MANGO_CONFIG: directory.read_bytes()}


def delete_profile(name: str) -> bool:
    """Delete a named profile."""
    validate_name(name)
    try:
        dir_profile = _location(name)
    except FileNotFoundError:
        return False
    if dir_profile.is_dir():
        shutil.rmtree(dir_profile, ignore_errors=True)
        return True

    file_profile = dir_profile
    if file_profile.exists():
        file_profile.unlink(missing_ok=True)
        return True

    return False
