"""Named config profiles: save, load, and switch Mango config snapshots."""

from __future__ import annotations

import shutil
from pathlib import Path

from mangomod import config_parser


def list_profiles() -> list[str]:
    """List all saved profile names."""
    if not config_parser.PROFILES_DIR.exists():
        return []
    names = [p.stem for p in config_parser.PROFILES_DIR.glob("*.conf")]
    names += [p.name for p in config_parser.PROFILES_DIR.iterdir() if p.is_dir()]
    return sorted(list(set(names)))


def save_profile(name: str, source_files: set[Path] | None = None) -> None:
    """Save the current configuration as a named profile."""
    config_parser.PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    if source_files and len(source_files) > 1:
        dest_dir = config_parser.PROFILES_DIR / name
        dest_dir.mkdir(exist_ok=True)
        base_dir = config_parser.MANGO_CONFIG.parent
        for p in source_files:
            if p.exists():
                try:
                    rel = p.relative_to(base_dir)
                    dest = dest_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, dest)
                except ValueError:
                    shutil.copy2(p, dest_dir / p.name)
    else:
        if config_parser.MANGO_CONFIG.exists():
            shutil.copy2(
                config_parser.MANGO_CONFIG,
                config_parser.PROFILES_DIR / f"{name}.conf",
            )


def load_profile(name: str) -> bool:
    """Load a named profile into the active configuration."""
    dir_profile = config_parser.PROFILES_DIR / name
    base_dir = config_parser.MANGO_CONFIG.parent

    if dir_profile.is_dir():
        for f in dir_profile.rglob("*"):
            if f.is_file():
                rel = f.relative_to(dir_profile)
                target = base_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
        return True

    file_profile = config_parser.PROFILES_DIR / f"{name}.conf"
    if file_profile.exists():
        base_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_profile, config_parser.MANGO_CONFIG)
        return True

    return False


def delete_profile(name: str) -> bool:
    """Delete a named profile."""
    dir_profile = config_parser.PROFILES_DIR / name
    if dir_profile.is_dir():
        shutil.rmtree(dir_profile, ignore_errors=True)
        return True

    file_profile = config_parser.PROFILES_DIR / f"{name}.conf"
    if file_profile.exists():
        file_profile.unlink(missing_ok=True)
        return True

    return False
