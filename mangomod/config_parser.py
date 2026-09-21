"""Comment-preserving and round-trip parser and serializer for Mango WM configuration files."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mangomod import mango_ipc

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "mango"
MANGO_CONFIG = DEFAULT_CONFIG_DIR / "config.conf"
PROFILES_DIR = DEFAULT_CONFIG_DIR / "profiles"
BACKUP_DIR = Path.home() / ".config" / "mangomod" / "backups"
APP_SETTINGS_DIR = Path.home() / ".config" / "mangomod"


def set_paths(config_path: str | Path | None = None, backup_path: str | Path | None = None) -> None:
    """Override default configuration and backup paths."""
    global MANGO_CONFIG, PROFILES_DIR, BACKUP_DIR, DEFAULT_CONFIG_DIR
    if config_path:
        p = Path(config_path).expanduser().resolve()
        DEFAULT_CONFIG_DIR = p.parent
        MANGO_CONFIG = p
    else:
        DEFAULT_CONFIG_DIR = Path.home() / ".config" / "mango"
        MANGO_CONFIG = DEFAULT_CONFIG_DIR / "config.conf"
    PROFILES_DIR = DEFAULT_CONFIG_DIR / "profiles"

    if backup_path:
        BACKUP_DIR = Path(backup_path).expanduser().resolve()
    else:
        BACKUP_DIR = Path.home() / ".config" / "mangomod" / "backups"


@dataclass
class BaseEntry:
    raw_text: str = ""
    source_file: Path | None = None

    def serialize(self) -> str:
        return self.raw_text


@dataclass
class EmptyLine(BaseEntry):
    def serialize(self) -> str:
        return "\n" if not self.raw_text.endswith("\n") else self.raw_text


@dataclass
class CommentLine(BaseEntry):
    text: str = ""

    def serialize(self) -> str:
        if self.raw_text:
            return self.raw_text if self.raw_text.endswith("\n") else self.raw_text + "\n"
        return f"# {self.text}\n"


@dataclass
class SettingEntry(BaseEntry):
    key: str = ""
    value: str = ""
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        return f"{self.key}={self.value}{cmt}\n"


@dataclass
class BindingEntry(BaseEntry):
    bind_type: str = "bind"  # bind, bindl, bindr, binds, bindc, etc.
    modifiers: str = "SUPER"
    key: str = ""
    command: str = ""
    args: str = ""
    keymode: str = "default"
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        if self.args:
            return f"{self.bind_type}={self.modifiers},{self.key},{self.command},{self.args}{cmt}\n"
        return f"{self.bind_type}={self.modifiers},{self.key},{self.command}{cmt}\n"


@dataclass
class MouseBindingEntry(BaseEntry):
    modifiers: str = "SUPER"
    button: str = "btn_left"
    command: str = "moveresize"
    args: str = "curmove"
    keymode: str = "default"
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        if self.args:
            return f"mousebind={self.modifiers},{self.button},{self.command},{self.args}{cmt}\n"
        return f"mousebind={self.modifiers},{self.button},{self.command}{cmt}\n"


@dataclass
class AxisBindingEntry(BaseEntry):
    modifiers: str = "SUPER"
    direction: str = "UP"
    command: str = ""
    args: str = ""
    keymode: str = "default"
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        if self.args:
            return f"axisbind={self.modifiers},{self.direction},{self.command},{self.args}{cmt}\n"
        return f"axisbind={self.modifiers},{self.direction},{self.command}{cmt}\n"


@dataclass
class GestureBindingEntry(BaseEntry):
    modifiers: str = "none"
    direction: str = "left"
    fingers: int = 3
    command: str = ""
    args: str = ""
    keymode: str = "default"
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        if self.args:
            return f"gesturebind={self.modifiers},{self.direction},{self.fingers},{self.command},{self.args}{cmt}\n"
        return f"gesturebind={self.modifiers},{self.direction},{self.fingers},{self.command}{cmt}\n"


@dataclass
class SwitchBindingEntry(BaseEntry):
    fold: str = "fold"  # fold or unfold
    command: str = ""
    args: str = ""
    keymode: str = "default"
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        if self.args:
            return f"switchbind={self.fold},{self.command},{self.args}{cmt}\n"
        return f"switchbind={self.fold},{self.command}{cmt}\n"


@dataclass
class KeyModeEntry(BaseEntry):
    mode_name: str = "default"
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        return f"keymode={self.mode_name}{cmt}\n"


@dataclass
class RuleEntry(BaseEntry):
    rule_type: str = "windowrule"  # windowrule, windowrule-once, layerrule, monitorrule, tagrule, devicerule
    params: dict[str, str] = field(default_factory=dict)
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        params_str = ",".join(f"{k}:{v}" for k, v in self.params.items())
        return f"{self.rule_type}={params_str}{cmt}\n"


@dataclass
class EnvEntry(BaseEntry):
    key: str = ""
    value: str = ""
    inline_comment: str = ""

    def serialize(self) -> str:
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        return f"env={self.key},{self.value}{cmt}\n"


@dataclass
class ExecEntry(BaseEntry):
    is_once: bool = True
    command: str = ""
    inline_comment: str = ""

    def serialize(self) -> str:
        prefix = "exec-once" if self.is_once else "exec"
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        return f"{prefix}={self.command}{cmt}\n"


@dataclass
class SourceEntry(BaseEntry):
    path: str = ""
    optional: bool = False
    inline_comment: str = ""

    def serialize(self) -> str:
        prefix = "source-optional" if self.optional else "source"
        cmt = f" # {self.inline_comment}" if self.inline_comment else ""
        return f"{prefix}={self.path}{cmt}\n"


def _split_inline_comment(line: str) -> tuple[str, str]:
    """Split a line into code content and inline comment."""
    # Do not split if inside quotes or part of command
    if "#" not in line:
        return line.strip(), ""
    parts = line.split("#", 1)
    code = parts[0].strip()
    comment = parts[1].strip()
    return code, comment


def _parse_key_value_params(param_str: str) -> dict[str, str]:
    """Parse comma-separated key:value or key:value params into dict."""
    res = {}
    tokens = [t.strip() for t in param_str.split(",") if t.strip()]
    for token in tokens:
        if ":" in token:
            k, v = token.split(":", 1)
            res[k.strip()] = v.strip()
        else:
            res[token] = ""
    return res


class ConfigDocument:
    """Represents a Mango WM configuration file or collection of lines."""

    def __init__(self, entries: list[BaseEntry] | None = None, file_path: Path | None = None):
        self.entries: list[BaseEntry] = entries or []
        self.file_path: Path | None = file_path

    # --- Scalar Settings Helpers ---

    def get_setting(self, key: str, default: Any = None) -> str | None:
        """Get the string value of a setting, or default if missing."""
        for entry in reversed(self.entries):
            if isinstance(entry, SettingEntry) and entry.key == key:
                return entry.value
        return default

    def get_int(self, key: str, default: int = 0) -> int:
        val = self.get_setting(key)
        if val is None:
            return default
        try:
            if val.startswith("0x") or val.startswith("0X"):
                return int(val, 16)
            return int(float(val))
        except ValueError:
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        val = self.get_setting(key)
        if val is None:
            return default
        try:
            return float(val)
        except ValueError:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self.get_setting(key)
        if val is None:
            return default
        return val.strip() in ("1", "true", "yes", "on", "True")

    def set_setting(self, key: str, value: Any, section_hint: str = "") -> None:
        """Set a setting value. If exists, update in-place; otherwise insert into document."""
        str_val = str(value)
        # Check if already present
        for entry in self.entries:
            if isinstance(entry, SettingEntry) and entry.key == key:
                entry.value = str_val
                return

        new_entry = SettingEntry(key=key, value=str_val, source_file=self.file_path)

        # Try to insert near section hint if provided
        if section_hint:
            for idx, entry in enumerate(self.entries):
                if isinstance(entry, CommentLine) and section_hint.lower() in entry.text.lower():
                    # insert below this section comment
                    self.entries.insert(idx + 1, new_entry)
                    return

        # Otherwise append at end
        self.entries.append(new_entry)

    def remove_setting(self, key: str) -> bool:
        """Remove a setting entry."""
        for idx, entry in enumerate(self.entries):
            if isinstance(entry, SettingEntry) and entry.key == key:
                self.entries.pop(idx)
                return True
        return False

    # --- Bindings Helpers ---

    def get_bindings(self) -> list[BindingEntry]:
        return [e for e in self.entries if isinstance(e, BindingEntry)]

    def add_binding(self, bind: BindingEntry) -> None:
        bind.source_file = self.file_path
        self.entries.append(bind)

    def remove_binding(self, bind: BindingEntry) -> bool:
        if bind in self.entries:
            self.entries.remove(bind)
            return True
        return False

    def add_mouse_binding(self, bind: MouseBindingEntry) -> None:
        bind.source_file = self.file_path
        self.entries.append(bind)

    def add_axis_binding(self, bind: AxisBindingEntry) -> None:
        bind.source_file = self.file_path
        self.entries.append(bind)

    def add_gesture_binding(self, bind: GestureBindingEntry) -> None:
        bind.source_file = self.file_path
        self.entries.append(bind)

    def add_switch_binding(self, bind: SwitchBindingEntry) -> None:
        bind.source_file = self.file_path
        self.entries.append(bind)

    def get_mouse_bindings(self) -> list[MouseBindingEntry]:
        return [e for e in self.entries if isinstance(e, MouseBindingEntry)]

    def get_axis_bindings(self) -> list[AxisBindingEntry]:
        return [e for e in self.entries if isinstance(e, AxisBindingEntry)]

    def get_gesture_bindings(self) -> list[GestureBindingEntry]:
        return [e for e in self.entries if isinstance(e, GestureBindingEntry)]

    def get_switch_bindings(self) -> list[SwitchBindingEntry]:
        return [e for e in self.entries if isinstance(e, SwitchBindingEntry)]

    # --- Rules Helpers ---

    def get_rules(self, rule_type: str | None = None) -> list[RuleEntry]:
        if rule_type:
            return [e for e in self.entries if isinstance(e, RuleEntry) and e.rule_type == rule_type]
        return [e for e in self.entries if isinstance(e, RuleEntry)]

    def add_rule(self, rule: RuleEntry) -> None:
        rule.source_file = self.file_path
        self.entries.append(rule)

    def remove_rule(self, rule: RuleEntry) -> bool:
        if rule in self.entries:
            self.entries.remove(rule)
            return True
        return False

    # --- Exec & Env Helpers ---

    def get_exec_entries(self) -> list[ExecEntry]:
        return [e for e in self.entries if isinstance(e, ExecEntry)]

    def add_exec(self, is_once: bool, command: str) -> ExecEntry:
        entry = ExecEntry(is_once=is_once, command=command, source_file=self.file_path)
        self.entries.append(entry)
        return entry

    def get_env_entries(self) -> list[EnvEntry]:
        return [e for e in self.entries if isinstance(e, EnvEntry)]

    def set_env(self, key: str, value: str) -> None:
        for entry in self.entries:
            if isinstance(entry, EnvEntry) and entry.key == key:
                entry.value = value
                return
        self.entries.append(EnvEntry(key=key, value=value, source_file=self.file_path))

    def remove_env(self, key: str) -> bool:
        for idx, entry in enumerate(self.entries):
            if isinstance(entry, EnvEntry) and entry.key == key:
                self.entries.pop(idx)
                return True
        return False

    # --- Sources / Includes ---

    def get_source_entries(self) -> list[SourceEntry]:
        return [e for e in self.entries if isinstance(e, SourceEntry)]

    # --- Serialization ---

    def serialize(self) -> str:
        lines = []
        for entry in self.entries:
            lines.append(entry.serialize())
        return "".join(lines)


def parse_line(line: str, current_keymode: str = "default", source_file: Path | None = None) -> tuple[BaseEntry, str]:
    """Parse a single configuration line. Returns (Entry, current_keymode)."""
    raw = line
    stripped = line.strip()

    if not stripped:
        return EmptyLine(raw_text=raw, source_file=source_file), current_keymode

    if stripped.startswith("#"):
        comment_text = stripped.lstrip("#").strip()
        return CommentLine(text=comment_text, raw_text=raw, source_file=source_file), current_keymode

    code, comment = _split_inline_comment(stripped)

    if "=" not in code:
        return BaseEntry(raw_text=raw, source_file=source_file), current_keymode

    key, val = code.split("=", 1)
    key = key.strip()
    val = val.strip()

    # Check keymode switch
    if key == "keymode":
        mode_name = val.strip() or "default"
        entry = KeyModeEntry(mode_name=mode_name, inline_comment=comment, raw_text=raw, source_file=source_file)
        return entry, mode_name

    # Check bindings
    if key.startswith("bind"):
        bind_type = key  # bind, bindl, bindr, bindc, binds, etc.
        parts = [p.strip() for p in val.split(",")]
        mods = parts[0] if len(parts) > 0 else "NONE"
        b_key = parts[1] if len(parts) > 1 else ""
        cmd = parts[2] if len(parts) > 2 else ""
        args = ",".join(parts[3:]) if len(parts) > 3 else ""
        entry = BindingEntry(
            bind_type=bind_type,
            modifiers=mods,
            key=b_key,
            command=cmd,
            args=args,
            keymode=current_keymode,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    if key == "mousebind":
        parts = [p.strip() for p in val.split(",")]
        mods = parts[0] if len(parts) > 0 else "NONE"
        btn = parts[1] if len(parts) > 1 else "btn_left"
        cmd = parts[2] if len(parts) > 2 else ""
        args = ",".join(parts[3:]) if len(parts) > 3 else ""
        entry = MouseBindingEntry(
            modifiers=mods,
            button=btn,
            command=cmd,
            args=args,
            keymode=current_keymode,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    if key == "axisbind":
        parts = [p.strip() for p in val.split(",")]
        mods = parts[0] if len(parts) > 0 else "NONE"
        direction = parts[1] if len(parts) > 1 else "UP"
        cmd = parts[2] if len(parts) > 2 else ""
        args = ",".join(parts[3:]) if len(parts) > 3 else ""
        entry = AxisBindingEntry(
            modifiers=mods,
            direction=direction,
            command=cmd,
            args=args,
            keymode=current_keymode,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    if key == "gesturebind":
        parts = [p.strip() for p in val.split(",")]
        mods = parts[0] if len(parts) > 0 else "none"
        direction = parts[1] if len(parts) > 1 else "left"
        fingers = 3
        if len(parts) > 2:
            try:
                fingers = int(parts[2])
            except ValueError:
                fingers = 3
        cmd = parts[3] if len(parts) > 3 else ""
        args = ",".join(parts[4:]) if len(parts) > 4 else ""
        entry = GestureBindingEntry(
            modifiers=mods,
            direction=direction,
            fingers=fingers,
            command=cmd,
            args=args,
            keymode=current_keymode,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    if key == "switchbind":
        parts = [p.strip() for p in val.split(",")]
        fold = parts[0] if len(parts) > 0 else "fold"
        cmd = parts[1] if len(parts) > 1 else ""
        args = ",".join(parts[2:]) if len(parts) > 2 else ""
        entry = SwitchBindingEntry(
            fold=fold,
            command=cmd,
            args=args,
            keymode=current_keymode,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    # Rules: windowrule, windowrule-once, layerrule, monitorrule, tagrule, devicerule
    if key in ("windowrule", "windowrule-once", "layerrule", "monitorrule", "tagrule", "devicerule"):
        params = _parse_key_value_params(val)
        entry = RuleEntry(
            rule_type=key,
            params=params,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    # Exec / Autostart
    if key in ("exec-once", "exec"):
        is_once = key == "exec-once"
        entry = ExecEntry(
            is_once=is_once,
            command=val,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    # Env
    if key == "env":
        parts = val.split(",", 1)
        env_k = parts[0].strip()
        env_v = parts[1].strip() if len(parts) > 1 else ""
        entry = EnvEntry(
            key=env_k,
            value=env_v,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    # Source
    if key in ("source", "source-optional"):
        optional = key == "source-optional"
        entry = SourceEntry(
            path=val,
            optional=optional,
            inline_comment=comment,
            raw_text=raw,
            source_file=source_file,
        )
        return entry, current_keymode

    # Normal scalar setting
    entry = SettingEntry(
        key=key,
        value=val,
        inline_comment=comment,
        raw_text=raw,
        source_file=source_file,
    )
    return entry, current_keymode


def parse_config_text(text: str, source_file: Path | None = None) -> ConfigDocument:
    """Parse text into a ConfigDocument."""
    entries: list[BaseEntry] = []
    current_keymode = "default"
    for line in text.splitlines(keepends=True):
        entry, current_keymode = parse_line(line, current_keymode, source_file)
        entries.append(entry)
    return ConfigDocument(entries=entries, file_path=source_file)


def resolve_include_path(base_file: Path, inc_path_str: str) -> Path:
    """Resolve an included source path relative to the base configuration."""
    expanded = Path(inc_path_str).expanduser()
    if expanded.is_absolute():
        return expanded
    return (base_file.parent / expanded).resolve()


def load_config_multi(config_path: Path | None = None) -> tuple[ConfigDocument, list[tuple[ConfigDocument, Path]]]:
    """Load main config and all sourced files.
    
    Returns (main_doc, list_of_(doc, path)).
    """
    target = config_path or MANGO_CONFIG
    fallback_sys = Path("/etc/mango/config.conf")

    if not target.exists():
        if fallback_sys.exists():
            target = fallback_sys
        else:
            # Create a default initial document
            doc = ConfigDocument(file_path=target)
            return doc, []

    text = target.read_text(encoding="utf-8", errors="replace")
    main_doc = parse_config_text(text, target)

    sub_docs: list[tuple[ConfigDocument, Path]] = []
    for entry in main_doc.get_source_entries():
        sub_path = resolve_include_path(target, entry.path)
        if sub_path.exists():
            sub_text = sub_path.read_text(encoding="utf-8", errors="replace")
            sub_doc = parse_config_text(sub_text, sub_path)
            sub_docs.append((sub_doc, sub_path))
        elif not entry.optional:
            # Missing mandatory file, create empty sub-doc representation
            sub_docs.append((ConfigDocument(file_path=sub_path), sub_path))

    return main_doc, sub_docs


def save_config(doc: ConfigDocument, target_path: Path | None = None, validate: bool = True) -> tuple[bool, str]:
    """Save a ConfigDocument to disk safely via temporary file and validation."""
    dest = target_path or doc.file_path or MANGO_CONFIG
    dest.parent.mkdir(parents=True, exist_ok=True)

    content = doc.serialize()

    # Write to temp file first
    temp_dir = dest.parent
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, prefix=".mangomod_tmp_", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        if validate:
            is_valid, msg = mango_ipc.validate_config(str(temp_path))
            if not is_valid:
                temp_path.unlink(missing_ok=True)
                return False, f"Validation error:\n{msg}"

        # Atomic replace
        os.replace(temp_path, dest)
        doc.file_path = dest
        return True, "Config successfully saved"
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        return False, f"Failed to save config: {exc}"
