"""Global application state management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mangomod import app_settings, backup, config_parser, mango_ipc
from mangomod.config_parser import ConfigDocument
from mangomod.undo import UndoEntry, UndoManager
from mangomod import storage


@dataclass
class RuntimeInfo:
    mango_running: bool = False
    mango_version: str = "Not running"
    has_touchpad: bool = False


class SettingsView:
    """Read and edit the scalar's effective occurrence in source order."""
    def __init__(self, state):
        self.state = state

    def __getattr__(self, name):
        return getattr(self.state.doc, name)

    def get_setting(self, key, default=None):
        found = self.state.setting_source(key)
        return found[0].get_setting(key, default) if found else default

    get_int = ConfigDocument.get_int
    get_float = ConfigDocument.get_float
    get_bool = ConfigDocument.get_bool

    def set_setting(self, key, value, section_hint=''):
        found = self.state.setting_source(key)
        doc = found[0] if found else self.state.doc
        doc.set_setting(key, value, section_hint)


class AppState:
    def __init__(self) -> None:
        self.doc: ConfigDocument = ConfigDocument()
        self.include_docs: list[tuple[ConfigDocument, Path]] = []
        self._saved_text: str = ""
        self._undo: UndoManager = UndoManager()
        self._runtime: RuntimeInfo = RuntimeInfo()
        self._dirty: bool = False
        self._source_files: set[Path] = set()
        self.saved_files: dict[str, str] = {}
        self._disk_bytes: dict[Path, bytes | None] = {}
        self._last_files: dict[str, str] = {}
        self.settings_view = SettingsView(self)

    def setting_source(self, key):
        docs = {path.resolve(): doc for doc, path in self.documents()}
        result = None
        def visit(doc, path, ancestors):
            nonlocal result
            if path.resolve() in ancestors:
                return
            ancestors = ancestors | {path.resolve()}
            for entry in doc.entries:
                if isinstance(entry, config_parser.SettingEntry) and entry.key == key:
                    result = (doc, path)
                elif isinstance(entry, config_parser.SourceEntry):
                    target = config_parser.resolve_include_path(path, entry.path)
                    if target.resolve() in docs:
                        visit(docs[target.resolve()], target, ancestors)
        visit(self.doc, config_parser.MANGO_CONFIG, set())
        return result

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
        self.saved_files = self.snapshot()
        self._last_files = dict(self.saved_files)
        self._disk_bytes = {Path(p): storage.read_bytes(Path(p)) for p in self.saved_files}
        self._undo.clear()
        self._dirty = False

    def documents(self):
        return [(self.doc, config_parser.MANGO_CONFIG), *self.include_docs]

    def snapshot(self) -> dict[str, str]:
        return {str(path): doc.serialize() for doc, path in self.documents()}

    def original_text(self, path: Path) -> str:
        return self.saved_files.get(str(path), (self._disk_bytes.get(path) or b'').decode('utf-8', errors='replace'))

    def disk_changes(self) -> list[Path]:
        """Watch loaded files and missing source targets, including symlinks."""
        expected = {path.resolve(): data for path, data in self._disk_bytes.items()}
        for doc, path in self.documents():
            for entry in doc.get_source_entries():
                target = config_parser.resolve_include_path(path, entry.path).resolve()
                if target not in expected:
                    expected[target] = None
        return [path for path, original in expected.items()
                if storage.read_bytes(path) != original]

    def commit(self, description: str) -> bool:
        self.sync_includes()
        current = self.snapshot()
        changed = current != self._last_files
        if current != self._last_files:
            main = str(config_parser.MANGO_CONFIG)
            self._undo.push(UndoEntry(description, self._last_files.get(main, ''), current[main],
                                      dict(self._last_files), current))
            self._last_files = current
        self._dirty = current != self.saved_files
        return changed

    def sync_includes(self):
        """Discover source lines added in the raw editor without reloading drafts."""
        seen = {config_parser.MANGO_CONFIG.resolve()}
        known = {path.resolve(): doc for doc, path in self.include_docs}
        def visit(doc, path):
            for entry in doc.get_source_entries():
                target = config_parser.resolve_include_path(path, entry.path)
                resolved = target.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                if resolved not in known and target.is_file():
                    self.register_include(target)
                    known[resolved] = self.include_docs[-1][0]
                if resolved in known:
                    visit(known[resolved], target)
        visit(self.doc, config_parser.MANGO_CONFIG)

    def restore_history(self, entry: UndoEntry, redo: bool = False) -> None:
        files = entry.files_after if redo else entry.files_before
        if files is None:
            files = self.snapshot()
            files[str(config_parser.MANGO_CONFIG)] = entry.snapshot_after if redo else entry.snapshot_before
        main = str(config_parser.MANGO_CONFIG)
        self.doc = config_parser.parse_config_text(files[main], config_parser.MANGO_CONFIG)
        self.include_docs = [(config_parser.parse_config_text(text, Path(path)), Path(path))
                             for path, text in files.items() if path != main]
        self._last_files = self.snapshot()
        self._source_files = {Path(p) for p in self._last_files}
        self._dirty = self._last_files != self.saved_files

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
            self.commit(description)

    def register_include(self, path: Path) -> None:
        """Track a newly added include file in memory (no disk reload,
        so unsaved in-memory edits — like the new source= line — survive)."""
        if any(p == path for _, p in self.include_docs):
            return
        data = storage.read_bytes(path)
        text = data.decode('utf-8', errors='replace') if data is not None else ''
        self.include_docs.append((config_parser.parse_config_text(text, path), path))
        self._disk_bytes[path] = data
        self._source_files.add(path)

    def save(self, skip_validation: bool = False, *, force_backup=False, activate=False) -> tuple[bool, str]:
        """Save the current document, creating a backup and hot-reloading if applicable."""
        reload_requested = (activate or app_settings.get('hot_reload_on_save', True)) and self.mango_running
        # Never send unchecked edits to the running compositor, even if the
        # user disabled validation for offline editing.
        validate = reload_requested or (app_settings.get("validate_on_save", True) and not skip_validation)
        current = self.snapshot()
        try:
            expected = {Path(path): self._disk_bytes[Path(path)] for path in current if Path(path) in self._disk_bytes}
            # Include dependencies are checked too: a changed include may alter
            # the meaning of an otherwise unchanged main configuration.
            for path, original in expected.items():
                if storage.read_bytes(path) != original:
                    return False, f"File changed outside MangoMod: {path}. Reload and review before saving."
            if validate:
                ok, msg = config_parser.validate_documents(self.documents())
                if not ok:
                    return False, f"Validation error:\n{msg}"
            else:
                msg = ""
            if reload_requested or force_backup or app_settings.get("auto_backup", True):
                backup.backup_all_sources(self.source_files, limit=app_settings.get("backup_limit", 10))
            changed = {Path(p): text.encode('utf-8') for p, text in current.items()
                       if text != self.original_text(Path(p)) or self._disk_bytes.get(Path(p)) is None}
            originals = {path: storage.read_bytes(path) for path in changed}
            storage.write_files(changed, expected)
        except (OSError, ValueError) as exc:
            return False, str(exc)

        if reload_requested:
            # Check the actual on-disk tree as well as the staged copy. IPC in
            # some Mango versions acknowledges dispatch without parse status.
            reload_ok, reload_msg = mango_ipc.validate_config(str(config_parser.MANGO_CONFIG))
            if reload_ok:
                reload_ok, reload_msg = mango_ipc.reload_config()
            if not reload_ok:
                try:
                    storage.write_files(originals, changed)
                except OSError as exc:
                    return False, f'Mango rejected the update: {reload_msg}\nAutomatic recovery failed: {exc}'
                # Keep the attempted edit as an unsaved draft for correction.
                restored_ok, restored_msg = mango_ipc.validate_config(str(config_parser.MANGO_CONFIG))
                if restored_ok:
                    restored_ok, restored_msg = mango_ipc.reload_config()
                detail = 'Previous configuration restored.' if restored_ok else f'Previous files restored; compositor recovery could not be confirmed: {restored_msg}'
                return False, f'Mango rejected the update: {reload_msg}\n{detail}\nYour edits remain unsaved.'

        self._saved_text = self.doc.serialize()
        self.saved_files = current
        self._last_files = dict(current)
        self._disk_bytes = {Path(p): storage.read_bytes(Path(p)) for p in current}
        self.mark_clean()
        notice = f"\n{msg}" if msg and msg != "Config syntax OK" else ""

        # Hot reload if enabled and running
        if reload_requested:
            return True, "Config saved & live reloaded!" + notice

        return True, "Config saved successfully" + notice

    def apply_files(self, files: dict[Path, bytes]) -> tuple[bool, str]:
        """Apply a preset/snapshot through the same checked save transaction."""
        main = config_parser.MANGO_CONFIG
        if main not in files:
            return False, 'This snapshot has no main configuration.'
        candidate = AppState()
        candidate.load()
        candidate.doc = config_parser.parse_config_text(files[main].decode('utf-8'), main)
        candidate.include_docs = [(config_parser.parse_config_text(data.decode('utf-8'), path), path)
                                  for path, data in files.items() if path != main]
        for path in files:
            candidate._disk_bytes.setdefault(path, storage.read_bytes(path))
        candidate._source_files.update(files)
        candidate.sync_includes()
        # Preset activation always checks installed Mango, regardless of the
        # preference for ordinary offline edits.
        ok, message = config_parser.validate_documents(candidate.documents())
        if not ok:
            return False, 'Validation error:\n' + message
        ok, message = candidate.save(force_backup=True, activate=True)
        if ok:
            self.load()
        return ok, message
