"""Conflict-aware file replacement shared by saves and snapshot restoration."""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


def read_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


def write_files(contents: dict[Path, bytes | None], expected: dict[Path, bytes | None] | None = None) -> None:
    """Stage every file first; roll back completed replacements on write failure.

    Each replacement is atomic. A process/power failure during a multi-file
    replacement still requires recovery from the pre-save backup.
    """
    expected = expected or {}
    staged: dict[Path, Path | None] = {}
    originals: dict[Path, bytes | None] = {}
    modes: dict[Path, int] = {}
    replaced: list[Path] = []

    def check_conflicts():
        for path, old in expected.items():
            if read_bytes(path) != old:
                raise OSError(f"File changed outside MangoMod: {path}. Reload and review before saving.")

    def stage(path, data, mode):
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.mangomod-', delete=False) as stream:
            name = Path(stream.name)
            try:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
                os.fchmod(stream.fileno(), mode)
            except BaseException:
                name.unlink(missing_ok=True)
                raise
        return name

    try:
        check_conflicts()
        for path, data in contents.items():
            dest = path.resolve()  # Preserve symlinks used by dotfile managers.
            if dest in staged:
                raise OSError(f"Multiple config paths refer to the same file: {path}")
            originals[dest] = read_bytes(dest)
            modes[dest] = stat.S_IMODE(dest.stat().st_mode) if dest.exists() else 0o600
            staged[dest] = stage(dest, data, modes[dest]) if data is not None else None
        check_conflicts()
        for dest, temp in staged.items():
            if temp is None:
                dest.unlink(missing_ok=True)
            else:
                os.replace(temp, dest)
            replaced.append(dest)
    except Exception as failure:
        recovery_errors = []
        for dest in reversed(replaced):
            try:
                original = originals[dest]
                if original is None:
                    dest.unlink(missing_ok=True)
                else:
                    recovery = stage(dest, original, modes[dest])
                    try:
                        os.replace(recovery, dest)
                    finally:
                        recovery.unlink(missing_ok=True)
            except OSError as exc:
                recovery_errors.append(f'{dest}: {exc}')
        if recovery_errors:
            raise OSError(f'{failure}. Recovery also failed for: ' + '; '.join(recovery_errors) + '. Restore a backup before continuing.') from failure
        raise
    finally:
        for temp in staged.values():
            if temp is not None:
                temp.unlink(missing_ok=True)
