"""Pure, staged command-builder model. Preview and apply use the same entries."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import math
import re

from mangomod.config_parser import (
    AxisBindingEntry, BindingEntry, ConfigDocument, GestureBindingEntry,
    KeyModeEntry, MouseBindingEntry, SwitchBindingEntry,
)
from mangomod.mango_schema import get_dispatcher
from mangomod.mango_compat import validate_value

BINDING_TYPES = (BindingEntry, MouseBindingEntry, AxisBindingEntry, GestureBindingEntry, SwitchBindingEntry)
KINDS = ('key', 'mouse', 'axis', 'gesture', 'switch')
TEMPLATES = [
    ('Launch an app', 'spawn', {'command': 'foot'}),
    ('Move a window', 'move_client', {'dir': 'left'}),
    ('Switch workspace', 'view', {'mask': '1'}),
    ('Resize a window', 'resizewin', {'w': '+10', 'h': '0'}),
    ('Toggle floating', 'togglefloating', {}),
    ('Change layout', 'setlayout', {'layout': 'tile'}),
]


def single_line(value):
    return not any(c in value for c in ('\n', '\r', '\x00'))


@dataclass
class Action:
    command: str
    values: dict[str, str] = field(default_factory=dict)
    raw_args: str | None = None

    @classmethod
    def create(cls, command):
        from mangomod.mango_schema import no_attributes_confirmed
        spec = get_dispatcher(command)
        if spec is None or (not spec['params'] and not no_attributes_confirmed(command)):
            return cls(command, raw_args='')
        return cls(command, {p['name']: p.get('default', '') for p in spec['params']})

    @classmethod
    def from_binding(cls, entry):
        action = cls.create(entry.command)
        spec = get_dispatcher(entry.command)
        if spec is None:
            action.raw_args = entry.args
            return action
        params = spec['params']
        parts = ([entry.args] if len(params) == 1 else entry.args.split(',')) if entry.args else []
        if len(parts) <= len(params):
            action.values = {p['name']: parts[i] if i < len(parts) else '' for i, p in enumerate(params)}
        if len(parts) > len(params) or action.arguments() != entry.args:
            action.raw_args = entry.args
        return action

    def arguments(self):
        if self.raw_args is not None:
            return self.raw_args
        spec = get_dispatcher(self.command)
        parts = [self.values.get(p['name'], '') for p in spec['params']] if spec else []
        # Empty interior slots are significant. Only trailing optional slots vanish.
        while parts and not parts[-1]:
            parts.pop()
        return ','.join(parts)

    def issues(self):
        errors, warnings = [], []
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', self.command):
            errors.append('Enter a command name without spaces or commas.')
        if not single_line(self.arguments()):
            errors.append('Arguments must fit on one config line.')
        spec = get_dispatcher(self.command)
        if spec is None:
            warnings.append('Custom command: MangoMod does not know its attributes. Mango will validate it when you save.')
        elif self.raw_args is not None:
            warnings.append('Raw arguments are preserved; attribute validation is unavailable.')
        else:
            for param in spec['params']:
                value = self.values.get(param['name'], '')
                error = validate_value(param, value)
                if param['type'] == 'enum' and error:
                    warnings.append(f"{param['label']}: custom value; check support in your Mango version.")
                elif error:
                    errors.append(f"{param['label']}: {error}")
                elif param['type'] == 'float' and value and not math.isfinite(float(value)):
                    errors.append(f"{param['label']}: enter a finite number.")
            if self.command in ('spawn', 'spawn_shell', 'spawn_on_empty') and not self.values.get('command', '').strip():
                errors.append('Enter an application or command to launch.')
        return errors, warnings


@dataclass
class Trigger:
    kind: str = 'key'
    modifiers: str = 'SUPER'
    key: str = 'Return'
    fingers: str = '3'
    flags: str = ''
    keymode: str = 'default'

    @classmethod
    def from_binding(cls, entry):
        kind = KINDS[BINDING_TYPES.index(type(entry))]
        key = getattr(entry, 'key', getattr(entry, 'button', getattr(entry, 'direction', getattr(entry, 'fold', ''))))
        return cls(kind, getattr(entry, 'modifiers', 'NONE'), key,
                   str(getattr(entry, 'fingers', 3)), getattr(entry, 'bind_type', 'bind')[4:], entry.keymode)

    def issues(self):
        errors = []
        if self.kind not in KINDS:
            errors.append('Choose an input type.')
        if not self.key.strip() or any(c.isspace() for c in self.key) or ',' in self.key:
            errors.append('Choose a trigger key, button, or direction without spaces or commas.')
        if not self.modifiers.strip() or ',' in self.modifiers:
            errors.append('Enter modifiers joined with +, or NONE.')
        if not self.keymode.strip() or any(c in self.keymode for c in ',#='):
            errors.append('Enter a key mode name without commas, #, or =.')
        if not re.fullmatch(r'[a-z]*', self.flags):
            errors.append('Flags must be lowercase letters without commas.')
        if self.kind == 'gesture' and (not self.fingers.isdigit() or int(self.fingers) < 1):
            errors.append('Enter a positive finger count.')
        if not all(single_line(v) for v in (self.key, self.modifiers, self.keymode, self.flags, self.fingers)):
            errors.append('Trigger fields must fit on one config line.')
        return errors

    def entry(self, action, multiple=False, shared=False):
        entry_data = dict(command=action.command, args=action.arguments(), keymode=self.keymode)
        if self.kind == 'key':
            flags = self.flags
            if (multiple or shared) and 'c' not in flags:
                flags += 'c'
            return BindingEntry(bind_type='bind' + flags, modifiers=self.modifiers, key=self.key, **entry_data)
        if self.kind == 'mouse':
            return MouseBindingEntry(modifiers=self.modifiers, button=self.key, **entry_data)
        if self.kind == 'axis':
            return AxisBindingEntry(modifiers=self.modifiers, direction=self.key, **entry_data)
        if self.kind == 'gesture':
            return GestureBindingEntry(modifiers=self.modifiers, direction=self.key, fingers=int(self.fingers), **entry_data)
        return SwitchBindingEntry(fold=self.key, **entry_data)


def overlaps(a, b):
    """Conservative conflict detection; common-mode bindings overlap every mode."""
    if a.kind != b.kind or a.key.casefold() != b.key.casefold():
        return False
    if a.keymode != b.keymode and 'common' not in (a.keymode, b.keymode):
        return False
    mods = lambda t: {m.upper() for m in re.split(r'[+\s]+', t.modifiers) if m and m.upper() != 'NONE'}
    if a.kind != 'switch' and mods(a) != mods(b):
        return False
    if a.kind == 'key' and ('r' in a.flags) != ('r' in b.flags):
        return False
    return a.kind != 'gesture' or a.fingers == b.fingers


@dataclass
class BuilderDraft:
    trigger: Trigger = field(default_factory=Trigger)
    actions: list[Action] = field(default_factory=list)
    source: object | None = None
    source_snapshot: str = ''

    @classmethod
    def from_binding(cls, entry):
        return cls(Trigger.from_binding(entry), [Action.from_binding(entry)], entry, entry.serialize())

    def issues(self):
        errors, warnings = self.trigger.issues(), []
        if not self.actions:
            errors.append('Add an action to start building.')
        for i, action in enumerate(self.actions, 1):
            bad, hints = action.issues()
            errors.extend(f'Action {i}: {msg}' for msg in bad)
            warnings.extend(f'Action {i}: {msg}' for msg in hints)
        if len(self.actions) > 1:
            warnings.append('Actions create separate bindings for one trigger; launched applications are not awaited.')
            if any(a.command in ('reload_config', 'load_config_file') for a in self.actions[:-1]):
                warnings.append('Reloading configuration stops the key event; later actions may not run.')
        return errors, warnings

    def conflicts(self, documents):
        return [entry for doc in documents for entry in doc.entries
                if isinstance(entry, BINDING_TYPES) and entry is not self.source
                and overlaps(self.trigger, Trigger.from_binding(entry))]

    def entries(self, shared=False):
        return [self.trigger.entry(a, len(self.actions) > 1, shared) for a in self.actions]

    def _share_existing_conflicts(self, result):
        for index, entry in enumerate(result.entries):
            if entry is self.source or not isinstance(entry, BindingEntry):
                continue
            if overlaps(self.trigger, Trigger.from_binding(entry)) and 'c' not in entry.bind_type:
                clone = deepcopy(entry)
                clone.bind_type += 'c'
                result.entries[index] = clone

    def proposed_document(self, doc, allow_conflicts=False):
        errors, _ = self.issues()
        if errors:
            raise ValueError('\n'.join(errors))
        result = ConfigDocument(list(doc.entries), doc.file_path)
        shared = bool(allow_conflicts and self.trigger.kind == 'key')
        entries = self.entries(shared)
        if shared:
            self._share_existing_conflicts(result)
        if self.source is not None:
            index = next((i for i, e in enumerate(result.entries) if e is self.source), None)
            if index is None or self.source.serialize() != self.source_snapshot:
                raise ValueError('This binding changed elsewhere. Open it again before applying.')
            # Preserve raw text and comments when the binding is unchanged.
            first = deepcopy(self.source) if type(entries[0]) is type(self.source) else entries[0]
            for attr in ('modifiers', 'key', 'button', 'direction', 'fold', 'fingers', 'bind_type', 'command', 'args', 'keymode'):
                if hasattr(entries[0], attr):
                    setattr(first, attr, getattr(entries[0], attr))
            first.inline_comment = self.source.inline_comment
            entries[0] = first
            restore_mode = self.source.keymode
            if self.trigger.keymode != restore_mode:
                entries = [KeyModeEntry(mode_name=self.trigger.keymode)] + entries + [KeyModeEntry(mode_name=restore_mode)]
            result.entries[index:index + 1] = entries
        else:
            restore_mode = next((e.mode_name for e in reversed(doc.entries) if isinstance(e, KeyModeEntry)), 'default')
            if self.trigger.keymode != restore_mode:
                entries = [KeyModeEntry(mode_name=self.trigger.keymode)] + entries + [KeyModeEntry(mode_name=restore_mode)]
            result.entries.extend(entries)
        for entry in entries:
            entry.source_file = doc.file_path
        return result
