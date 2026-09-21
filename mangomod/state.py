"""Global application state management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mangomod import app_settings, backup, config_parser, mango_ipc
from mangomod.config_parser import ConfigDocument
from mangomod.undo import UndoEntry, UndoManager


@dataclass
class RuntimeInfo:
    mango_running: bool = False
    mango_version: str = "Not running"
    has_touchpad: bool = False


class AppState:
    def __init__(self) -> None:
        self.doc: ConfigDocument = ConfigDocument()
        self.include_docs: list[tuple[ConfigDocument, Path]] = []
        self._saved_text: str = ""
        self._undo: UndoManager = UndoManager()
        self._runtime: RuntimeInfo = RuntimeInfo()
        self._dirty: bool = False
        self._source_files: set[Path] = set()

    def load(self) -> None:
        """Load configuration from disk and detect compositor runtime."""
        running = mango_ipc.is_mango_running()
        version = mango_ipc.get_version() if running else "Not running"
        touchpad = mango_ipc.has_touchpad()
        self._runtime = RuntimeInfo(
            mango_running=running,
            mango_version=version,
            has_touchpad=touchpad,
        )

        self.doc, self.include_docs = config_parser.load_config_multi()
        self._source_files = {config_parser.MANGO_CONFIG}
        for _, path in self.include_docs:
            if path.exists():
                self._source_files.add(path)

        self._saved_text = self.doc.serialize()
        self._dirty = False

    @property
    def saved_text(self) -> str:
        return self._saved_text

    @property
    def source_files(self) -> set[Path]:
        return self._source_files

    @property
    def is_multi_file(self) -> bool:
        return bool(self.include_docs)

    @property
    def mango_running(self) -> bool:
        return self._runtime.mango_running

    @property
    def mango_version(self) -> str:
        return self._runtime.mango_version

    @property
    def has_touchpad(self) -> bool:
        return self._runtime.has_touchpad

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def mark_dirty(self) -> None:
        self._dirty = True

    def mark_clean(self) -> None:
        self._dirty = False

    @property
    def undo(self) -> UndoManager:
        return self._undo

    def push_undo(self, description: str, before: str, after: str) -> None:
        if before != after:
            self._undo.push(UndoEntry(description, before, after))
            self.mark_dirty()

    def register_include(self, path: Path) -> None:
        """Track a newly added include file in memory (no disk reload,
        so unsaved in-memory edits — like the new source= line — survive)."""
        if any(p == path for _, p in self.include_docs):
            return
        self.include_docs.append((ConfigDocument(file_path=path), path))
        self._source_files.add(path)

    def save(self, skip_validation: bool = False) -> tuple[bool, str]:
        """Save the current document, creating a backup and hot-reloading if applicable."""
        # Auto backup if enabled
        if app_settings.get("auto_backup", True):
            backup.backup_all_sources(self.source_files, limit=app_settings.get("backup_limit", 10))

        validate = app_settings.get("validate_on_save", True) and not skip_validation
        ok, msg = config_parser.save_config(self.doc, validate=validate)
        if not ok:
            return False, msg

        self._saved_text = self.doc.serialize()
        self.mark_clean()

        # Hot reload if enabled and running
        if app_settings.get("hot_reload_on_save", True) and self.mango_running:
            reload_ok, reload_msg = mango_ipc.reload_config()
            if reload_ok:
                return True, "Config saved & live reloaded!"
            return True, f"Config saved (reload notice: {reload_msg})"

        return True, "Config saved successfully"
