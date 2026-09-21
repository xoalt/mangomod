"""Automatic and manual configuration backup management."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from mangomod import config_parser


def backup_all_sources(source_files: set[Path], limit: int = 10) -> Path | None:
    """Create a timestamped generation backup of all source config files."""
    if not source_files:
        return None

    config_parser.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    existing_gens = []
    for p in config_parser.BACKUP_DIR.iterdir():
        if p.is_dir():
            m = re.match(r"^(?:\(Gen|v|gen)(\d+)", p.name, re.IGNORECASE)
            if m:
                existing_gens.append(int(m.group(1)))
    next_gen = max(existing_gens) + 1 if existing_gens else 1

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest_dir = config_parser.BACKUP_DIR / f"(Gen{next_gen}){ts}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    base_dir = config_parser.MANGO_CONFIG.parent

    for src in sorted(source_files):
        if not src.exists():
            continue
        try:
            rel = src.relative_to(base_dir)
            dest = dest_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        except ValueError:
            shutil.copy2(src, dest_dir / src.name)

    if limit > 0:
        backups = sorted(
            [p for p in config_parser.BACKUP_DIR.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
        )
        while len(backups) > limit:
            oldest = backups.pop(0)
            shutil.rmtree(oldest, ignore_errors=True)

    return dest_dir


def list_backups() -> list[dict]:
    """List all available backups sorted newest first."""
    if not config_parser.BACKUP_DIR.exists():
        return []

    results = []
    for p in config_parser.BACKUP_DIR.iterdir():
        if p.is_dir():
            files = list(p.rglob("*"))
            m = re.match(r"^\(Gen(\d+)\)(.*)$", p.name)
            gen = int(m.group(1)) if m else 0
            ts_str = m.group(2) if m else p.name
            results.append({
                "path": p,
                "name": p.name,
                "generation": gen,
                "timestamp": ts_str,
                "file_count": len([f for f in files if f.is_file()]),
                "mtime": p.stat().st_mtime,
            })

    results.sort(key=lambda x: x["mtime"], reverse=True)
    return results


def restore_backup(backup_dir: Path) -> bool:
    """Restore configuration files from a backup directory."""
    if not backup_dir.exists() or not backup_dir.is_dir():
        return False

    base_dir = config_parser.MANGO_CONFIG.parent
    base_dir.mkdir(parents=True, exist_ok=True)

    for item in backup_dir.rglob("*"):
        if item.is_file():
            rel = item.relative_to(backup_dir)
            target = base_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

    return True
