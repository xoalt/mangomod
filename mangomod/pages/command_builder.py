"""Scratch-style binding studio: a simple canvas and contextual attribute sidebar."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import difflib
import json

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, GLib, GObject, Gtk, Pango

from mangomod.builder_model import Action, BuilderDraft, Trigger, BINDING_TYPES, KINDS, TEMPLATES
from mangomod.i18n import localize_tree
from mangomod.config_parser import BindingEntry
from mangomod.mango_rules import TRIGGER_TYPES
from mangomod.mango_schema import CATEGORIES, DISPATCHERS, get_dispatcher, dispatcher_category, no_attributes_confirmed
from mangomod.pages.base import BasePage
from mangomod.ui_compat import present_content_dialog
from mangomod import config_parser, storage
from mangomod.mango_compat import validate_value


FLAGS = [('l', 'Works while locked'), ('s', 'Match typed symbol'), ('r', 'On key release'),
         ('p', 'Pass key to application'), ('c', 'Allow shared shortcut')]
ICONS = {'launch': 'system-run-symbolic', 'window': 'view-restore-symbolic',
         'focus': 'go-next-symbolic', 'tags': 'view-paged-symbolic',
         'layout': 'view-grid-symbolic', 'monitor': 'video-display-symbolic'}


def text(value, css=None, wrap=False):
    widget = Gtk.Label(label=value, xalign=0, wrap=wrap)
    if css:
        widget.add_css_class(css)
    return widget


def config_text(value, css=None):
    """Keep Mango syntax readable inside both LTR and RTL interfaces."""
    widget = text(value, css)
    widget.set_direction(Gtk.TextDirection.LTR)
    widget.set_xalign(0)
    return widget


def clear(box):
    while child := box.get_first_child():
        box.remove(child)


def button(title, callback, css='flat', icon=None):
    widget = Gtk.Button(icon_name=icon) if icon else Gtk.Button(label=title)
    widget.set_tooltip_text(title)
    widget.add_css_class(css)
    widget.connect('clicked', lambda *_: callback())
    return widget


class CommandBuilderPage(BasePage):
    def __init__(self, window):
        super().__init__(window)
        self.draft = BuilderDraft()
        self._selected = None
        self._trigger_ready = False
        self._history = []
        self._future = []
        self._baseline = self._fingerprint()
        self._parameter_widgets = {}
        self._recovery_id = None
        self._config_path = config_parser.MANGO_CONFIG
        self._source_path = None

    @property
    def _binding_doc(self):
        if self._source_path is not None:
            for doc, path in self._win.app_state.documents():
                if path == self._source_path:
                    return doc
            # Do not silently move a shortcut whose source has disappeared.
            return config_parser.ConfigDocument()
        return self._win.app_state.doc

    def has_pending_draft(self):
        return self._fingerprint() != self._baseline

    def _recovery_path(self):
        import hashlib
        key = hashlib.sha256(str(self._config_path).encode()).hexdigest()[:24]
        return config_parser.APP_SETTINGS_DIR / 'drafts' / (key + '.json')

    def save_recovery(self):
        if self._recovery_id is not None:
            GLib.source_remove(self._recovery_id)
            self._recovery_id = None
        if not self.has_pending_draft():
            return
        record = {'version': 1, 'trigger': asdict(self.draft.trigger),
                  'actions': [asdict(action) for action in self.draft.actions],
                  'ready': self._trigger_ready, 'source': self.draft.source_snapshot,
                  'source_path': str(self._source_path) if self._source_path else None}
        try:
            storage.write_files({self._recovery_path(): json.dumps(record, ensure_ascii=False).encode('utf-8')})
        except OSError as exc:
            self.show_toast(str(exc))

    def _queue_recovery(self):
        if self._recovery_id is not None:
            GLib.source_remove(self._recovery_id)
        def save():
            self._recovery_id = None
            self.save_recovery()
            return False
        self._recovery_id = GLib.timeout_add(400, save)

    def _restore_recovery(self):
        try:
            record = json.loads(self._recovery_path().read_text(encoding='utf-8'))
            if record.get('version') != 1:
                raise ValueError('Unsupported draft version')
            draft = BuilderDraft(Trigger(**record['trigger']), [Action(**a) for a in record['actions']])
            draft.source_snapshot = record.get('source', '')
            if draft.source_snapshot:
                draft.source = next((e for e in config_parser.parse_config_text(draft.source_snapshot).entries
                                     if isinstance(e, BINDING_TYPES)), None)
            self.draft = draft
            from pathlib import Path
            self._source_path = Path(record['source_path']) if record.get('source_path') else None
            self.rebind_source()
            self._trigger_ready = bool(record['ready'])
            self._selected = self.draft.actions[-1] if self.draft.actions else None
            self._set_stage_layout()
            self._render_canvas()
            self._show_attributes()
            self._restore_button.set_visible(False)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.show_toast(str(exc))

    def rebind_source(self):
        if self.draft.source is not None:
            matches = [entry for entry in self._binding_doc.entries if isinstance(entry, BINDING_TYPES)
                       and entry.serialize() == self.draft.source_snapshot]
            if len(matches) == 1:
                self.draft.source = matches[0]

    def dispose(self):
        self.save_recovery()

    def build(self):
        tb, header, _, _ = self._make_toolbar_page('Command Builder')
        header.pack_start(button('Open binding', self._open_existing))
        header.pack_start(button('New', lambda: self._confirm_replace(self._new_draft)))
        self._restore_button = button('Recover draft', lambda: self._confirm_replace(self._restore_recovery))
        self._restore_button.set_visible(self._recovery_path().is_file())
        header.pack_start(self._restore_button)
        self._apply_btn = button('Apply to config', self._apply, 'suggested-action')
        header.pack_end(self._apply_btn)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_start(20)
        outer.set_margin_end(20)
        outer.set_margin_top(18)
        outer.set_margin_bottom(18)
        outer.append(text('Build a shortcut', 'mm-page-title'))
        outer.append(text('Choose a trigger, then add actions. Select a block to edit it.', 'dim-label', True))
        split = Gtk.Box(spacing=16, vexpand=True)
        self._workspace = self._build_canvas()
        split.append(self._workspace)
        self._sidebar = self._build_sidebar()
        split.append(self._sidebar)
        responsive = Adw.BreakpointBin()
        responsive.set_size_request(360, 320)
        responsive.set_child(split)
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse('max-width: 680sp'))
        narrow.add_setter(split, 'orientation', Gtk.Orientation.VERTICAL)
        narrow.add_setter(self._sidebar, 'width-request', -1)
        narrow.add_setter(self._sidebar, 'height-request', 260)
        responsive.add_breakpoint(narrow)
        outer.append(responsive)
        tb.set_content(outer)
        self._set_stage_layout()
        self._render_canvas()
        self._show_intro()
        self._update()
        return tb

    def _build_canvas(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, hexpand=True, vexpand=True)
        box.add_css_class('mm-builder-workspace')
        top = Gtk.Box(spacing=8)
        title = text('YOUR SHORTCUT', 'mm-builder-step')
        title.set_hexpand(True)
        top.append(title)
        self._draft_undo = button('Undo draft edit', lambda: self._travel(False), icon='edit-undo-symbolic')
        self._draft_redo = button('Redo draft edit', lambda: self._travel(True), icon='edit-redo-symbolic')
        top.append(self._draft_undo)
        top.append(self._draft_redo)
        box.append(top)
        self._canvas_scroll = Gtk.ScrolledWindow(vexpand=True)
        self._canvas_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.canvas.add_css_class('mm-builder-canvas')
        self._canvas_scroll.set_child(self.canvas)
        drop = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
        drop.connect('drop', lambda t, v, x, y: self._drop(v))
        self.canvas.add_controller(drop)
        box.append(self._canvas_scroll)
        self._status = text('', 'mm-builder-status', True)
        box.append(self._status)
        self._conflict_ack = Gtk.CheckButton(label='Share this keyboard shortcut')
        self._conflict_ack.set_visible(False)
        self._conflict_ack.connect('toggled', lambda *_: self._update())
        box.append(self._conflict_ack)
        preview_expander = Gtk.Expander(label='Config preview')
        self._preview_expander = preview_expander
        self._preview = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                     wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._preview.set_direction(Gtk.TextDirection.LTR)
        self._preview.add_css_class('mm-preview')
        preview_scroll = Gtk.ScrolledWindow(min_content_height=100, max_content_height=150)
        preview_scroll.set_child(self._preview)
        preview_expander.set_child(preview_scroll)
        box.append(preview_expander)
        bottom = Gtk.Box(spacing=8)
        self._footer = bottom
        bottom.add_css_class('mm-builder-footer')
        note = text('Draft only · Apply stages changes for Save', 'mm-preview-caption', True)
        note.set_hexpand(True)
        bottom.append(note)
        self._diff_btn = button('Review diff', self._review_diff)
        bottom.append(self._diff_btn)
        box.append(bottom)
        return box

    def _build_sidebar(self):
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, width_request=320)
        side.add_css_class('mm-builder-sidebar')
        heading = Gtk.Box(spacing=8)
        self._side_title = text('Add an action', 'mm-builder-heading', True)
        self._side_title.set_hexpand(True)
        heading.append(self._side_title)
        self._browse_btn = button('Browse actions', self._show_library)
        heading.append(self._browse_btn)
        side.append(heading)
        self._side_hint = text('Choose what happens when the shortcut runs.', 'dim-label', True)
        side.append(self._side_hint)
        side.append(Gtk.Separator())
        self._side_stack = Gtk.Stack(vexpand=True, transition_type=Gtk.StackTransitionType.CROSSFADE)
        self._side_stack.set_hhomogeneous(False)
        self._side_stack.set_vhomogeneous(False)
        intro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        intro.append(text('Start with the trigger', 'mm-card-title'))
        intro_hint = text('Choose a key, mouse button, gesture, or switch. Actions appear after this step.', 'dim-label', True)
        intro_hint.set_max_width_chars(34)
        intro.append(intro_hint)
        intro.append(button('Choose trigger', self._select_trigger, 'suggested-action'))
        self._side_stack.add_named(intro, 'intro')
        self._side_stack.add_named(self._build_library(), 'library')
        scroll = Gtk.ScrolledWindow(vexpand=True)
        self._inspector_scroll = scroll
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._inspector = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        scroll.set_child(self._inspector)
        self._side_stack.add_named(scroll, 'attributes')
        side.append(self._side_stack)
        return side

    def _build_library(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._search = Gtk.SearchEntry(placeholder_text='Find an action…')
        self._search.connect('search-changed', lambda *_: self._filter_library())
        box.append(self._search)
        self._category_ids = ['all'] + list(CATEGORIES)
        self._category = Gtk.DropDown.new_from_strings(['All actions'] + list(CATEGORIES.values()))
        self._category.connect('notify::selected', lambda *_: self._filter_library())
        box.append(self._category)
        presets = Gtk.Expander(label='Quick-start templates')
        presets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for title, command, values in TEMPLATES:
            presets_box.append(button(title, lambda c=command, v=values: self.add_action(c, v)))
        presets.set_child(presets_box)
        box.append(presets)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        library = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._library_rows = []
        for category, entries in DISPATCHERS.items():
            for entry in entries:
                command = entry['cmd']
                row = button(entry['desc'], lambda c=command: self.add_action(c), 'mm-builder-palette')
                child = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                child.append(text(entry['desc'], 'mm-card-title', True))
                child.append(config_text(command, 'mm-config-path'))
                row.set_child(child)
                self._drag_source(row, {'command': command}, Gdk.DragAction.COPY)
                self._library_rows.append((row, category, (command + ' ' + entry['desc']).lower()))
                library.append(row)
        self._no_results = text('No matching actions. Use a custom command below.', 'dim-label', True)
        self._no_results.set_visible(False)
        library.append(self._no_results)
        scroll.set_child(library)
        box.append(scroll)
        box.append(button('＋ Custom command', lambda: self.add_action('custom_command')))
        return box

    def _filter_library(self):
        if not hasattr(self, '_library_rows'):
            return
        query = self._search.get_text().strip().lower()
        category = self._category_ids[self._category.get_selected()]
        count = 0
        for row, cat, haystack in self._library_rows:
            visible = (category == 'all' or category == cat) and (not query or query in haystack)
            row.set_visible(visible)
            count += visible
        self._no_results.set_visible(count == 0)

    def _conflict_state(self):
        docs = [doc for doc, _ in self._win.app_state.documents()]
        conflicts = self.draft.conflicts(docs)
        in_main = lambda entry: any(item is entry for item in self._binding_doc.entries)
        shareable = bool(conflicts) and self.draft.trigger.kind == 'key' and all(isinstance(e, BindingEntry) and in_main(e) for e in conflicts)
        return conflicts, shareable

    def _allow_shared_conflicts(self, conflicts=None, shareable=False):
        return bool(conflicts and shareable and self._conflict_ack.get_active())

    def _proposed_document(self, conflicts=None, shareable=False):
        return self.draft.proposed_document(self._binding_doc, self._allow_shared_conflicts(conflicts, shareable))

    def _preview_diff(self, proposed):
        return ''.join(difflib.unified_diff(
            self._binding_doc.serialize().splitlines(keepends=True),
            proposed.serialize().splitlines(keepends=True),
            fromfile='Current configuration',
            tofile='After applying draft',
        ))

    def _render_canvas(self):
        clear(self.canvas)
        trigger = self.draft.trigger
        self._trigger_button = button('Edit trigger', self._select_trigger, 'mm-builder-trigger')
        trigger_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        trigger_box.append(text('01 · WHEN', 'mm-builder-step'))
        self._trigger_title = config_text('', 'mm-card-title')
        self._trigger_title.set_hexpand(True)
        trigger_box.append(self._trigger_title)
        trigger_box.append(text('Select to change input or record a shortcut', 'mm-card-description', True))
        self._trigger_button.set_child(trigger_box)
        self.canvas.append(self._trigger_button)
        self._cards = []
        for index, action in enumerate(self.draft.actions):
            connector = Gtk.Box(height_request=8, width_request=42, halign=Gtk.Align.START)
            connector.add_css_class('mm-builder-connector')
            self.canvas.append(connector)
            card = button('Edit action attributes', lambda a=action: self._select_action(a), 'mm-builder-action')
            card.add_css_class('mm-builder-' + dispatcher_category(action.command))
            body = Gtk.Box(spacing=12)
            number = text(f'{index + 2:02}', 'mm-builder-number')
            body.append(number)
            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True)
            title = text('', 'mm-card-title', True)
            summary = config_text('', 'mm-config-path')
            summary.set_ellipsize(Pango.EllipsizeMode.END)
            summary.set_max_width_chars(35)
            info.append(title)
            info.append(summary)
            body.append(info)
            body.append(Gtk.Image.new_from_icon_name('go-next-symbolic'))
            card.set_child(body)
            self._drag_source(card, {'index': index}, Gdk.DragAction.MOVE)
            target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
            target.connect('drop', lambda t, v, x, y, i=index: self._drop(v, i))
            card.add_controller(target)
            self._cards.append((card, title, summary, action))
            self.canvas.append(card)
        if self._trigger_ready and not self.draft.actions:
            empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            empty.add_css_class('mm-builder-empty')
            empty.append(text('02 · ADD AN ACTION', 'mm-builder-step'))
            empty.append(text('What should happen?', 'mm-builder-heading'))
            empty.append(text('Pick an action on the side, or try one of these.', 'dim-label', True))
            for title, command, values in TEMPLATES[:3]:
                empty.append(button(title + '  →', lambda c=command, v=values: self.add_action(c, v)))
            self.canvas.append(empty)
        elif self._trigger_ready:
            self.canvas.append(button('＋ Add another action', self._show_library, 'mm-builder-add'))
        self._update()

    def _field(self, box, title, value, changed, options=None, hint=''):
        group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        group.append(text(title, 'mm-card-title', True))
        entry = Gtk.Entry(text=value, hexpand=True)
        entry.set_direction(Gtk.TextDirection.LTR)
        if hint:
            entry.set_placeholder_text(hint)
        if options:
            opts = list(options)
            dropdown = Gtk.DropDown.new_from_strings([v if v else 'Default' for v in opts] + ['Custom…'])
            dropdown.set_selected(opts.index(value) if value in opts else len(opts))
            entry.set_visible(value not in opts)
            def selected(widget, _):
                custom = widget.get_selected() == len(opts)
                entry.set_visible(custom)
                if not custom:
                    entry.set_text(opts[widget.get_selected()])
                else:
                    entry.grab_focus()
            dropdown.connect('notify::selected', selected)
            group.append(dropdown)
        entry.connect('changed', lambda e: changed(e.get_text()))
        group.append(entry)
        if hint:
            group.append(text(hint, 'mm-card-description', True))
        error_label = text('', 'error', True)
        error_label.set_visible(False)
        entry._mm_error_label = error_label
        group.append(error_label)
        box.append(group)
        return entry

    def _show_library(self):
        if not self._trigger_ready:
            self._show_intro()
            return
        self._sidebar.set_visible(True)
        self._side_stack.set_visible_child_name('library')
        self._side_title.set_text('Add an action')
        self._side_hint.set_text('Choose what happens when the shortcut runs.')
        self._browse_btn.set_visible(False)
        self._localize_panel()

    def _show_intro(self):
        self._sidebar.set_visible(False)
        self._side_stack.set_visible_child_name('intro')
        self._side_title.set_text('Step 1 · Trigger')
        self._side_hint.set_text('Choose what starts this shortcut.')
        self._browse_btn.set_visible(False)
        self._localize_panel()

    def _set_stage_layout(self):
        expanded = self._trigger_ready
        alignment = Gtk.Align.FILL if expanded else Gtk.Align.START
        self._workspace.set_valign(alignment)
        self._sidebar.set_valign(alignment)
        self._canvas_scroll.set_vexpand(expanded)
        self._canvas_scroll.set_min_content_height(0 if expanded else 118)
        self._side_stack.set_vexpand(expanded)
        self._inspector_scroll.set_min_content_height(0 if expanded else 390)
        for widget in (self._status, self._conflict_ack, self._preview_expander, self._footer):
            widget.set_visible(expanded)

    def _select_trigger(self):
        self._selected = None
        self._show_attributes()
        self._update()

    def _select_action(self, action):
        self._selected = action
        self._show_attributes()
        self._update()

    def _show_attributes(self):
        self._sidebar.set_visible(True)
        self._side_stack.set_visible_child_name('attributes')
        self._side_title.set_text('Trigger settings' if self._selected is None else 'Action settings')
        self._side_hint.set_text('Changes update the shortcut blocks immediately.')
        self._browse_btn.set_visible(self._trigger_ready)
        clear(self._inspector)
        self._parameter_widgets = {}
        if self._selected is None:
            self._trigger_attributes()
            self._localize_panel()
            return
        action = self._selected
        spec = get_dispatcher(action.command)
        self._inspector.append(text('ACTION ATTRIBUTES', 'mm-builder-step'))
        self._inspector.append(text(spec['desc'] if spec else 'Custom command', 'mm-card-title', True))
        unconfirmed = spec is not None and not spec['params'] and not no_attributes_confirmed(action.command)
        if action.raw_args is not None or unconfirmed:
            self._parameter_widgets['command'] = self._field(self._inspector, 'Command', action.command,
                lambda v: self._edit_action('command', v))
            self._parameter_widgets['raw_args'] = self._field(self._inspector, 'Arguments', action.arguments(),
                lambda v: self._edit_action('raw_args', v), hint='Keep the exact argument order and commas Mango expects.')
            self._inspector.append(text('The documentation does not confirm the attributes for this action. Arguments remain editable.' if unconfirmed else
                'Custom and future commands stay editable without losing their arguments.', 'dim-label', True))
        else:
            self._inspector.append(config_text(action.command, 'mm-config-path'))
            for param in spec['params']:
                name = param['name']
                self._parameter_widgets[name] = self._field(self._inspector, param.get('label', name), action.values.get(name, ''),
                    lambda v, n=name: self._edit_value(n, v), options=param.get('options'), hint=param.get('hint', ''))
            if no_attributes_confirmed(action.command):
                self._inspector.append(text('This action has no attributes to configure.', 'dim-label', True))
            self._inspector.append(button('Edit raw command and arguments', self._use_raw))
        tools = Gtk.Box(spacing=6, homogeneous=True)
        index = self._index(action)
        up = button('Move up', lambda: self._move(index, index - 1), icon='go-up-symbolic')
        up.set_sensitive(index > 0)
        down = button('Move down', lambda: self._move(index, index + 1), icon='go-down-symbolic')
        down.set_sensitive(index < len(self.draft.actions) - 1)
        tools.append(up)
        tools.append(down)
        tools.append(button('Duplicate action', self._duplicate, icon='edit-copy-symbolic'))
        tools.append(button('Remove action', self._remove_selected, icon='user-trash-symbolic'))
        self._inspector.append(Gtk.Separator())
        self._inspector.append(tools)
        self._localize_panel()
        self._update()

    def _localize_panel(self):
        localize_tree(self._sidebar, self._win._language)

    def _trigger_attributes(self):
        trigger = self.draft.trigger
        self._inspector.append(text('TRIGGER ATTRIBUTES', 'mm-builder-step'))
        types = Gtk.DropDown.new_from_strings(['Keyboard', 'Mouse button', 'Scroll wheel', 'Touchpad gesture', 'Lid switch'])
        types.set_selected(KINDS.index(trigger.kind))
        types.connect('notify::selected', lambda d, _: self._change_kind(KINDS[d.get_selected()]))
        self._inspector.append(types)
        if trigger.kind == 'key':
            self._inspector.append(button('● Record shortcut', self._capture_shortcut, 'suggested-action'))
        fields = next(t['fields'] for t in TRIGGER_TYPES if t['id'] == trigger.kind)
        key_spec = next(f for f in fields if f['name'] == 'key')
        self._parameter_widgets['key'] = self._field(self._inspector, key_spec['label'], trigger.key,
                lambda v: self._edit_trigger('key', v), options=key_spec.get('options'))
        if trigger.kind != 'switch':
            mods = Gtk.Grid(column_spacing=6, row_spacing=6)
            active = trigger.modifiers.upper().replace('+', ' ').split()
            for position, modifier in enumerate(('SUPER', 'CTRL', 'ALT', 'SHIFT')):
                toggle = Gtk.ToggleButton(label=modifier.title())
                toggle.set_hexpand(True)
                toggle.set_active(modifier in active)
                toggle.connect('toggled', lambda b, m=modifier: self._toggle_modifier(m, b.get_active()))
                mods.attach(toggle, position % 2, position // 2, 1, 1)
            self._inspector.append(text('Modifiers', 'mm-card-title'))
            self._inspector.append(mods)
        if trigger.kind == 'gesture':
            self._parameter_widgets['fingers'] = self._field(self._inspector, 'Fingers', trigger.fingers,
                lambda v: self._edit_trigger('fingers', v), options=['3', '4'])
        advanced = Gtk.Expander(label='Advanced trigger options')
        options = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._field(options, 'Key mode', trigger.keymode, lambda v: self._edit_trigger('keymode', v),
                    hint='default for normal shortcuts; common for every mode.')
        if trigger.kind == 'key':
            for flag, title in FLAGS:
                check = Gtk.CheckButton(label=title)
                check.set_active(flag in trigger.flags)
                check.connect('toggled', lambda b, f=flag: self._toggle_flag(f, b.get_active()))
                options.append(check)
        advanced.set_child(options)
        self._inspector.append(advanced)
        if not self._trigger_ready:
            self._inspector.append(button('Continue to actions', self._confirm_trigger, 'suggested-action'))

    def _confirm_trigger(self):
        errors = self.draft.trigger.issues()
        if errors:
            self.show_toast(errors[0])
            return
        self._remember()
        self._trigger_ready = True
        self._set_stage_layout()
        self._render_canvas()
        self._show_library()

    def _fingerprint(self):
        return repr((self.draft.trigger, self.draft.actions, self._trigger_ready))

    def _snapshot(self):
        return deepcopy(self.draft.trigger), deepcopy(self.draft.actions), self._trigger_ready

    def _remember(self):
        self._history.append(self._snapshot())
        self._history = self._history[-100:]
        self._future.clear()
        if hasattr(self, '_conflict_ack'):
            self._conflict_ack.set_active(False)

    def _travel(self, redo):
        source, target = (self._future, self._history) if redo else (self._history, self._future)
        if not source:
            return
        target.append(self._snapshot())
        self.draft.trigger, self.draft.actions, self._trigger_ready = source.pop()
        self._set_stage_layout()
        self._selected = self.draft.actions[-1] if self.draft.actions else None
        self._render_canvas()
        if self._trigger_ready:
            self._show_attributes()
        else:
            self._show_intro()

    def _index(self, action):
        return next(i for i, item in enumerate(self.draft.actions) if item is action)

    def add_action(self, command, values=None, position=None):
        self._remember()
        self._trigger_ready = True
        self._set_stage_layout()
        action = Action.create(command)
        if values:
            action.values.update(values)
        if position is None:
            self.draft.actions.append(action)
        else:
            self.draft.actions.insert(position, action)
        self._selected = action
        self._render_canvas()
        self._select_action(action)
        return action

    def _edit_value(self, name, value):
        if self._selected.values.get(name) == value:
            return
        self._remember()
        self._selected.values[name] = value
        self._update()

    def _edit_action(self, name, value):
        if getattr(self._selected, name) == value:
            return
        self._remember()
        setattr(self._selected, name, value)
        self._update()

    def _edit_trigger(self, name, value):
        if getattr(self.draft.trigger, name) == value:
            return
        self._remember()
        setattr(self.draft.trigger, name, value)
        self._update()

    def _toggle_modifier(self, name, active):
        mods = self.draft.trigger.modifiers.replace('+', ' ').split()
        mods = [m for m in mods if m.upper() not in (name, 'NONE')]
        if active:
            mods.append(name)
        self._edit_trigger('modifiers', '+'.join(mods) or 'NONE')

    def _toggle_flag(self, flag, active):
        flags = self.draft.trigger.flags.replace(flag, '') + (flag if active else '')
        self._edit_trigger('flags', flags)

    def _change_kind(self, kind):
        if kind == self.draft.trigger.kind:
            return
        self._remember()
        self.draft.trigger.kind = kind
        self.draft.trigger.key = dict(key='Return', mouse='btn_left', axis='UP', gesture='left', switch='fold')[kind]
        self._show_attributes()
        self._update()

    def _use_raw(self):
        self._remember()
        self._selected.raw_args = self._selected.arguments()
        self._show_attributes()
        self._update()

    def _duplicate(self):
        self._remember()
        index = self._index(self._selected)
        action = deepcopy(self._selected)
        self.draft.actions.insert(index + 1, action)
        self._selected = action
        self._render_canvas()
        self._show_attributes()

    def _remove_selected(self):
        self._remember()
        index = self._index(self._selected)
        self.draft.actions.pop(index)
        self._selected = self.draft.actions[min(index, len(self.draft.actions)-1)] if self.draft.actions else None
        self._render_canvas()
        self._show_attributes()

    def _move(self, old, new):
        if old == new or not 0 <= old < len(self.draft.actions) or not 0 <= new < len(self.draft.actions):
            return
        self._remember()
        action = self.draft.actions.pop(old)
        self.draft.actions.insert(new, action)
        self._selected = action
        self._render_canvas()
        self._show_attributes()

    def _drag_source(self, widget, data, actions):
        source = Gtk.DragSource(actions=actions)
        source.connect('prepare', lambda s, x, y: Gdk.ContentProvider.new_for_value(json.dumps(data)))
        widget.add_controller(source)

    def _drop(self, raw, position=None):
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                return False
            if 'command' in data and isinstance(data['command'], str) and get_dispatcher(data['command']):
                self.add_action(data['command'], position=position)
            elif type(data.get('index')) is int and self.draft.actions:
                old = data['index']
                if not 0 <= old < len(self.draft.actions):
                    return False
                target = len(self.draft.actions)-1 if position is None else position - (old < position)
                self._move(old, target)
            else:
                return False
            return True
        except (TypeError, ValueError):
            return False

    def _update(self):
        if not hasattr(self, '_status'):
            return
        if self.has_pending_draft():
            self._queue_recovery()
        if self._selected is not None and self._selected.raw_args is None:
            spec = get_dispatcher(self._selected.command)
            for param in spec['params'] if spec else []:
                entry = self._parameter_widgets.get(param['name'])
                if entry is None:
                    continue
                error = validate_value(param, self._selected.values.get(param['name'], ''))
                if param['type'] == 'enum':
                    error = None  # A newer Mango may support this value.
                label = getattr(entry, '_mm_error_label', None)
                if label is not None:
                    label.set_text(self._win.tr(error) if error else '')
                    label.set_visible(bool(error))
                    if error:
                        entry.add_css_class('error')
                    else:
                        entry.remove_css_class('error')
        trigger = self.draft.trigger
        self._trigger_title.set_direction(
            Gtk.TextDirection.LTR if self._trigger_ready or self._win._language != 'ar' else Gtk.TextDirection.RTL
        )
        self._trigger_title.set_halign(
            Gtk.Align.FILL if self._trigger_ready or self._win._language != 'ar' else Gtk.Align.START
        )
        self._trigger_title.set_xalign(0 if self._trigger_ready or self._win._language != 'ar' else 1)
        self._trigger_title.set_text(
            (f'{trigger.modifiers} + {trigger.key}' if trigger.kind != 'switch' else f'Lid {trigger.key}')
            if self._trigger_ready else 'Choose a trigger'
        )
        if not self._trigger_ready:
            self._status.set_text('Choose a trigger to begin.')
            self._status.remove_css_class('error')
            self._conflict_ack.set_visible(False)
            self._apply_btn.set_sensitive(False)
            self._diff_btn.set_sensitive(False)
            self._preview.get_buffer().set_text('Choose a trigger first.')
            self._draft_undo.set_sensitive(bool(self._history))
            self._draft_redo.set_sensitive(bool(self._future))
            page = self._win._pages.get('command_builder')
            if page is not None:
                localize_tree(page, self._win._language)
            return
        for card, title, summary, action in getattr(self, '_cards', []):
            spec = get_dispatcher(action.command)
            title.set_text(spec['desc'] if spec else action.command)
            summary.set_text(action.arguments() or ('No attributes needed' if no_attributes_confirmed(action.command) else 'No arguments entered'))
            summary.set_tooltip_text(action.arguments())
            if action is self._selected:
                card.add_css_class('mm-builder-selected')
            else:
                card.remove_css_class('mm-builder-selected')
        errors, warnings = self.draft.issues()
        conflicts, shareable = self._conflict_state()
        self._conflict_ack.set_visible(bool(conflicts))
        if conflicts:
            commands = ', '.join(e.command for e in conflicts[:3])
            if shareable:
                self._conflict_ack.set_label('Share this keyboard shortcut (adds c to matching bindings in this file)')
                warnings.insert(0, f'Trigger overlaps {len(conflicts)} existing binding(s): {commands}. Enable sharing to keep both.')
            else:
                self._conflict_ack.set_label('Share this keyboard shortcut')
                if self._conflict_ack.get_active():
                    self._conflict_ack.set_active(False)
                warnings.insert(0, f'Trigger overlaps {len(conflicts)} existing binding(s): {commands}. Change the trigger or open the original binding.')
            self._conflict_ack.set_sensitive(shareable)
        self._status.set_text('\n'.join(errors + warnings) if errors or warnings else 'Ready to apply. Your configuration is unchanged until you apply.')
        self._status.remove_css_class('error')
        if errors and self.draft.actions:
            self._status.add_css_class('error')
        can_apply = not errors and (not conflicts or self._allow_shared_conflicts(conflicts, shareable))
        self._apply_btn.set_sensitive(can_apply)
        self._diff_btn.set_sensitive(can_apply)
        if not errors:
            try:
                if conflicts and not self._allow_shared_conflicts(conflicts, shareable):
                    self._preview.get_buffer().set_text('Resolve the conflict or enable sharing to preview the staged config.')
                else:
                    proposed = self._proposed_document(conflicts, shareable)
                    self._preview.get_buffer().set_text(self._preview_diff(proposed) or 'No changes to apply.')
            except ValueError as exc:
                self._preview.get_buffer().set_text(str(exc))
        else:
            self._preview.get_buffer().set_text('Complete the fields above to generate valid config.')
        self._draft_undo.set_sensitive(bool(self._history))
        self._draft_redo.set_sensitive(bool(self._future))
        page = self._win._pages.get('command_builder')
        if page is not None:
            localize_tree(page, self._win._language)

    def _review_diff(self):
        try:
            conflicts, shareable = self._conflict_state()
            if conflicts and not self._allow_shared_conflicts(conflicts, shareable):
                self.show_toast('Resolve the shortcut conflict before reviewing the diff.')
                return None
            proposed = self._proposed_document(conflicts, shareable)
        except ValueError as exc:
            self.show_toast(str(exc))
            return
        diff = self._preview_diff(proposed)
        view = Gtk.TextView(editable=False, monospace=True, left_margin=16, top_margin=16)
        view.get_buffer().set_text(diff or 'No changes to apply.')
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(view)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(scroll)
        return present_content_dialog(self._win, toolbar, 'Review shortcut changes', 800, 480)

    def _apply(self):
        self._update()
        if not self._apply_btn.get_sensitive():
            return
        try:
            conflicts, shareable = self._conflict_state()
            proposed = self._proposed_document(conflicts, shareable)
        except ValueError as exc:
            self.show_toast(str(exc))
            return
        before = self._binding_doc.serialize()
        after = proposed.serialize()
        if before != after:
            self._binding_doc.entries = proposed.entries
            self._win.push_undo('apply command-builder shortcut', before, after)
        self._new_draft()
        self.show_toast('Shortcut staged. Use Save changes to write the config.')

    def _new_draft(self):
        if self._recovery_id is not None:
            GLib.source_remove(self._recovery_id)
            self._recovery_id = None
        self._recovery_path().unlink(missing_ok=True)
        self.draft = BuilderDraft()
        self._source_path = None
        self._selected = None
        self._trigger_ready = False
        self._history.clear()
        self._future.clear()
        self._baseline = self._fingerprint()
        self._conflict_ack.set_active(False)
        self._set_stage_layout()
        self._render_canvas()
        self._show_intro()
        self._restore_button.set_visible(False)

    def _confirm_replace(self, callback):
        if self._fingerprint() == self._baseline:
            callback()
            return
        dialog = Adw.MessageDialog.new(self._win, 'Discard this draft?', 'Your unapplied shortcut edits will be discarded.')
        dialog.add_response('cancel', 'Keep editing')
        dialog.add_response('discard', 'Discard draft')
        dialog.set_response_appearance('discard', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.connect('response', lambda d, r: callback() if r == 'discard' else None)
        localize_tree(dialog, self._win._language)
        dialog.present()

    def load_binding(self, entry):
        self._source_path = next((path for doc, path in self._win.app_state.documents()
                                  if any(e is entry for e in doc.entries)), None)
        self.draft = BuilderDraft.from_binding(entry)
        self._trigger_ready = True
        self._set_stage_layout()
        self._selected = self.draft.actions[0]
        self._history.clear()
        self._future.clear()
        self._baseline = self._fingerprint()
        self._conflict_ack.set_active(False)
        self._render_canvas()
        self._select_action(self._selected)

    def _open_existing(self):
        dialog = Adw.Window(title='Open existing binding', transient_for=self._win, modal=True)
        dialog.set_default_size(640, 520)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                          margin_start=20, margin_end=20, margin_top=16, margin_bottom=16)
        content.append(text('Bindings in your configuration and sources', 'mm-card-title'))
        search = Gtk.SearchEntry(placeholder_text='Find a key or command…')
        content.append(search)
        rows = []
        listing = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for entry in [e for doc, _ in self._win.app_state.documents() for e in doc.entries]:
            if not isinstance(entry, BINDING_TYPES):
                continue
            trigger = Trigger.from_binding(entry)
            title = f'{trigger.modifiers} {trigger.key} · {entry.command}'
            def load(e=entry):
                dialog.close()
                self._confirm_replace(lambda: self.load_binding(e))
            row = button(title, load, 'mm-builder-palette')
            row.set_tooltip_text(entry.serialize().strip())
            rows.append((row, (title + ' ' + entry.args + ' ' + trigger.keymode).lower()))
            listing.append(row)
        if not rows:
            listing.append(text('No bindings yet. Start with an action or template.', 'dim-label', True))
        search.connect('search-changed', lambda e: [r.set_visible(e.get_text().lower() in haystack) for r, haystack in rows])
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(listing)
        content.append(scroll)
        toolbar.set_content(content)
        dialog.set_content(toolbar)
        localize_tree(dialog, self._win._language)
        dialog.present()

    def _capture_shortcut(self):
        dialog = Adw.Window(title='Record shortcut', transient_for=self._win, modal=True)
        dialog.set_default_size(440, 220)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        box.append(text('Press your shortcut', 'mm-card-title'))
        box.append(text('Escape cancels. If your compositor intercepts it, enter the key manually.', 'dim-label', True))
        box.append(button('Cancel', dialog.close))
        toolbar.set_content(box)
        dialog.set_content(toolbar)
        controller = Gtk.EventControllerKey()
        controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        def pressed(c, keyval, keycode, state):
            if keyval == Gdk.KEY_Escape:
                dialog.close()
                return True
            name = Gdk.keyval_name(keyval)
            if not name or name in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Super_L', 'Super_R', 'Meta_L', 'Meta_R'):
                return True
            self.record_shortcut(keyval, state)
            dialog.close()
            return True
        controller.connect('key-pressed', pressed)
        dialog.add_controller(controller)
        localize_tree(dialog, self._win._language)
        dialog.present()

    def record_shortcut(self, keyval, state):
        modifiers = [name for name, mask in [('SUPER', Gdk.ModifierType.SUPER_MASK), ('CTRL', Gdk.ModifierType.CONTROL_MASK),
                     ('ALT', Gdk.ModifierType.ALT_MASK), ('SHIFT', Gdk.ModifierType.SHIFT_MASK)] if state & mask]
        self._remember()
        self.draft.trigger.kind = 'key'
        self.draft.trigger.key = Gdk.keyval_name(Gdk.keyval_to_lower(keyval))
        self.draft.trigger.modifiers = '+'.join(modifiers) or 'NONE'
        self._selected = None
        self._trigger_ready = True
        self._set_stage_layout()
        self._render_canvas()
        self._show_library()

    def on_shown(self):
        self._update()
