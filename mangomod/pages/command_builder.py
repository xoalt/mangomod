"""Scratch-style drag & drop Command Builder.

Compose an input binding (key, mouse button, scroll wheel, trackpad gesture or
lid switch) by dragging colored action blocks from the palette onto the
canvas, filling in each block's parameter slots and watching the live preview
serialize into a real mango config line.
"""

from __future__ import annotations

import json
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Adw, Gdk, GLib, GObject, Gtk

from mangomod.mango_rules import TRIGGER_TYPES
from mangomod.mango_schema import (
    BLOCK_CSS,
    CATEGORIES,
    DISPATCHERS,
    dispatcher_css,
    format_dispatcher,
    get_dispatcher,
)
from mangomod.mango_compat import available_next, validate_value
from mangomod.config_parser import (
    AxisBindingEntry,
    BindingEntry,
    GestureBindingEntry,
    MouseBindingEntry,
    SwitchBindingEntry,
)
from mangomod.pages.base import BasePage

_TYPE_STRING = GObject.TYPE_STRING
_CUSTOM_SENTINEL = "\u0000CUSTOM\u0000"


class _ActionBlock(Gtk.Box):
    """A single dispatcher block on the canvas: header + parameter slots."""

    _counter = 0

    def __init__(self, page: "CommandBuilderPage", cmd: str):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._page = page
        self.cmd = cmd
        _ActionBlock._counter += 1
        self.uid = _ActionBlock._counter
        self._param_widgets: dict[str, Any] = {}
        self._param_custom_entries: dict[str, Gtk.Entry] = {}

        entry = get_dispatcher(cmd)
        css = dispatcher_css(cmd)
        self.add_css_class("mm-action-block")
        self.add_css_class(css)

        desc = entry["desc"] if entry else ""

        # --- Header ---
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        head.add_css_class("mm-block-head")
        head.set_margin_top(4)
        head.set_margin_bottom(4)
        head.set_margin_start(8)
        head.set_margin_end(8)

        handle = Gtk.Image.new_from_icon_name("view-list-symbolic")
        handle.add_css_class("mm-block-handle")
        self._setup_handle_source(handle)
        head.append(handle)

        name_lbl = Gtk.Label(label=cmd, xalign=0)
        name_lbl.add_css_class("mm-block-name")
        name_lbl.set_hexpand(True)
        head.append(name_lbl)

        if desc:
            tip = Gtk.Label(label=desc)
            tip.set_tooltip_text(desc)
        else:
            tip = Gtk.Label()
        head.append(tip)

        del_btn = Gtk.Button(icon_name="user-trash-symbolic")
        del_btn.add_css_class("flat")
        del_btn.add_css_class("mm-block-delete")
        del_btn.set_tooltip_text("Remove block")
        del_btn.connect("clicked", self._on_delete)
        head.append(del_btn)

        self.append(head)

        # --- Parameter slot rows ---
        if entry:
            for p in entry["params"]:
                self._append_param(p)

        # --- Layout ---
        self.set_margin_bottom(6)
        self._setup_drop_target()

    def _setup_handle_source(self, handle: Gtk.Widget) -> None:
        source = Gtk.DragSource()
        source.set_actions(Gdk.DragAction.MOVE)

        def _prepare(s, x, y):
            value = GObject.Value()
            value.init(_TYPE_STRING)
            value.set_string(json.dumps({"kind": "move", "uid": self.uid}))
            return Gdk.ContentProvider.new_for_value(value)

        source.connect("prepare", _prepare)
        handle.add_controller(source)

    def _on_delete(self, *_):
        self._page.remove_block(self)

    def _setup_drop_target(self) -> None:
        target = Gtk.DropTarget()
        target.set_actions(Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
        target.set_gtypes([_TYPE_STRING])
        target.connect("drop", self._on_drop)
        self.add_controller(target)

    def _on_drop(self, target, value, x, y) -> bool:
        raw = value
        if hasattr(raw, "get_string"):
            raw = raw.get_string()
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return False
        if data.get("kind") == "move":
            uid = data.get("uid")
            self._page.move_block(uid, insert_before=self)
        else:
            cmd = data.get("cmd")
            if cmd:
                self._page.add_block(cmd, insert_after=self)
        return True

    def _append_param(self, p: dict[str, Any]) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_margin_top(2)
        row.set_margin_bottom(2)
        row.set_margin_start(20)
        row.set_margin_end(12)

        lbl = Gtk.Label(label=p["name"], xalign=0)
        lbl.add_css_class("mm-param-label")
        lbl.set_tooltip_text(p.get("hint", "") or p.get("label", p["name"]))
        lbl.set_size_request(110, -1)
        row.append(lbl)

        ptype = p.get("type", "str")
        self._append_select_or_custom(p, row)
        if p.get("hint"):
            hl = Gtk.Label(label="?", xalign=0)
            hl.add_css_class("mm-param-hint")
            hl.set_tooltip_text(p["hint"])
            row.append(hl)

        self.append(row)

    def _append_select_or_custom(self, p: dict[str, Any], row: Gtk.Box) -> None:
        """Schema-driven "select menu with custom input box" for *every* param.

        - enum params with real options -> DropDown of those options PLUS a
          trailing "Custom…" escape that reveals a free-text box;
        - str params *without* schema options (spawn's ``command`` today) still
          get the select affordance, with "Custom…" preselected, so the user
          always sees a chooser — never a naked box.

        Driven purely by the schema ``options`` field; nothing is invented.
        """
        options = list(p.get("options", []))
        has_real = bool(options)

        # Model: real options + a "Custom…" sentinel.
        model_items = options + [_CUSTOM_SENTINEL]
        slist = Gtk.StringList.new(model_items)
        dd = Gtk.DropDown(model=slist)
        dd.set_hexpand(True)

        default = p.get("default", "")
        custom_entry = Gtk.Entry()
        custom_entry.set_placeholder_text(p.get("hint", "Custom value"))
        custom_entry.set_hexpand(True)
        custom_entry.set_visible(False)
        custom_entry.connect("notify::text", lambda *_: self._page.on_block_change())

        def _sync_custom_vis(*_) -> None:
            item = dd.get_selected_item()
            is_custom = item is not None and item.get_string() == _CUSTOM_SENTINEL
            custom_entry.set_visible(is_custom)
            if not is_custom and item is not None:
                # A real option is pinned; show it as the value so params that
                # need an actual select (description/tooltip) still read typos-free.
                custom_entry.set_text(item.get_string())

        def _initial() -> None:
            if not has_real:
                # No schema options -> preselect Custom so the box is editable.
                dd.set_selected(0)
                custom_entry.set_text(default)
                custom_entry.set_visible(True)
                return
            try:
                dd.set_selected(options.index(default))
                custom_entry.set_visible(False)
            except ValueError:
                # Default isn't a listed option -> land in Custom with the text.
                dd.set_selected(len(options))
                custom_entry.set_text(default)
                custom_entry.set_visible(True)

        dd.connect("notify::selected", _sync_custom_vis)
        dd.connect("notify::selected", lambda *_: self._page.on_block_change())
        _initial()

        row.append(dd)
        row.append(custom_entry)
        self._param_widgets[p["name"]] = dd
        self._param_custom_entries[p["name"]] = custom_entry

    def get_values(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for name, widget in self._param_widgets.items():
            if isinstance(widget, Gtk.DropDown):
                item = widget.get_selected_item()
                out[name] = item.get_string() if item else ""
            else:
                out[name] = widget.get_text()
        return out


class CommandBuilderPage(BasePage):
    def __init__(self, window):
        super().__init__(window)
        self._blocks: list[_ActionBlock] = []
        self._trigger_widgets: dict[str, Any] = {}

    # ------------------------------------------------------------------ UI --

    def build(self) -> Gtk.Widget:
        tb, header, _, _ = self._make_toolbar_page("Command Builder")

        save_btn = Gtk.Button(icon_name="document-save-symbolic")
        save_btn.set_tooltip_text("Save script to config")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", lambda *_: self._save_script())
        header.pack_end(save_btn)

        clear_btn = Gtk.Button(icon_name="edit-clear-symbolic")
        clear_btn.set_tooltip_text("Clear script")
        clear_btn.connect("clicked", lambda *_: self._clear_canvas())
        header.pack_end(clear_btn)

        # Prevent the default toolbar scroller: replace children with our split.
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_start(24)
        outer.set_margin_end(24)
        outer.set_margin_top(16)
        outer.set_margin_bottom(24)

        split = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        split.set_vexpand(True)
        split.append(self._build_palette())
        split.append(self._build_canvas())
        outer.append(split)

        tb.set_content(outer)
        return tb

    def _build_palette(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        frame.add_css_class("mm-canvas-frame")
        frame.set_valign(Gtk.Align.FILL)
        frame.set_size_request(300, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(14)

        title = Gtk.Label(label="Actions", xalign=0)
        title.add_css_class("mm-pane-title")
        box.append(title)

        sub = Gtk.Label(label="Drag a block onto the canvas", xalign=0)
        sub.add_css_class("dim-label")
        box.append(sub)

        search = Gtk.SearchEntry()
        search.set_placeholder_text("Filter actions…")
        search.add_css_class("mm-search-entry")
        search.connect("search-changed", self._on_palette_search)
        box.append(search)

        self._palette_search = search
        self._palette_boxes: dict[str, Gtk.ListBox] = {}

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        list_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for cat, title_text in CATEGORIES.items():
            sec = Gtk.Label(label=title_text, xalign=0)
            sec.add_css_class("mm-sidebar-section-label")
            list_container.append(sec)

            lbox = Gtk.ListBox()
            lbox.add_css_class("mm-palette-list")
            lbox.set_selection_mode(Gtk.SelectionMode.NONE)
            for entry in DISPATCHERS[cat]:
                lbox.append(self._make_palette_block(entry["cmd"], entry.get("desc", "")))
            self._palette_boxes[cat] = lbox
            list_container.append(lbox)

        scroller.set_child(list_container)
        box.append(scroller)

        frame.set_child(box)
        return frame

    def _make_palette_block(self, cmd: str, desc: str) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        block = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        block.add_css_class("mm-palette-block")
        block.add_css_class(dispatcher_css(cmd))

        icon = Gtk.Image.new_from_icon_name("open-menu-symbolic")
        icon.add_css_class("mm-block-handle")
        block.append(icon)

        lbl = Gtk.Label(label=cmd, xalign=0)
        lbl.add_css_class("mm-block-name")
        lbl.set_hexpand(True)
        block.append(lbl)

        if desc:
            block.set_tooltip_text(desc)

        # Drag source (copy)
        source = Gtk.DragSource()
        source.set_actions(Gdk.DragAction.COPY)

        def _prepare(s, x, y):
            value = GObject.Value()
            value.init(_TYPE_STRING)
            value.set_string(json.dumps({"cmd": cmd}))
            return Gdk.ContentProvider.new_for_value(value)

        source.connect("prepare", _prepare)
        row.add_controller(source)

        row.set_child(block)

        # Compat gate handle: the command this row adds.
        row._cmd = cmd
        # Click-to-add (guaranteed path; drag is the bonus).
        if hasattr(self, "add_block"):
            row.connect("activate", lambda *_: self.add_block(cmd))
        elif self._page is not None:  # falls back to page when row self is not the page
            row.connect("activate", lambda *_: self._page.add_block(cmd))

        return row

    def _build_canvas(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        frame.add_css_class("mm-canvas-frame")
        frame.set_vexpand(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(14)
        box.set_margin_end(14)
        box.set_margin_top(10)
        box.set_margin_bottom(14)

        title = Gtk.Label(label="Your Script", xalign=0)
        title.add_css_class("mm-pane-title")
        box.append(title)

        # --- Trigger editor ---
        self._build_trigger_editor(box)

        # --- Drop canvas ---
        canvas_frame = Gtk.Frame()
        canvas_frame.add_css_class("mm-drop-canvas")
        canvas_frame.set_vexpand(True)

        self.canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.canvas.set_margin_top(10)
        self.canvas.set_margin_bottom(10)
        self.canvas.set_margin_start(10)
        self.canvas.set_margin_end(10)

        placeholder = Gtk.Label(label="Drop action blocks here")
        placeholder.add_css_class("dim-label")
        self._placeholder = placeholder
        self.canvas.append(placeholder)

        canvas_frame.set_child(self.canvas)
        box.append(canvas_frame)

        self._canvas_drop_target = Gtk.DropTarget()
        self._canvas_drop_target.set_actions(Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
        self._canvas_drop_target.set_gtypes([_TYPE_STRING])
        self._canvas_drop_target.connect("drop", self._on_canvas_drop)
        canvas_frame.add_controller(self._canvas_drop_target)

        # --- Live preview ---
        prev_title = Gtk.Label(label="Live Preview", xalign=0)
        prev_title.add_css_class("mm-pane-title")
        box.append(prev_title)

        self._preview = Gtk.TextView()
        self._preview.set_editable(False)
        self._preview.set_cursor_visible(False)
        self._preview.set_wrap_mode(Gtk.WrapMode.WORD)
        self._preview.add_css_class("mm-preview")
        self._preview.set_size_request(-1, 96)
        buf = self._preview.get_buffer()
        buf.set_text("")
        box.append(self._preview)

        frame.set_child(box)
        return frame

    def _build_trigger_editor(self, box: Gtk.Box) -> None:
        trig_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        trig_box.add_css_class("mm-trigger-editor")

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        t_label = Gtk.Label(label="Trigger:", xalign=0)
        t_label.add_css_class("mm-param-label")
        t_label.set_size_request(110, -1)
        row1.append(t_label)

        types = Gtk.StringList.new([t["label"] for t in TRIGGER_TYPES])
        dd = Gtk.DropDown(model=types)
        dd.connect("notify::selected", self._on_trigger_type_changed)
        row1.append(dd)
        trig_box.append(row1)
        self._trigger_type_dd = dd

        self._trigger_mode = Gtk.Stack()
        self._trigger_mode.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        for t in TRIGGER_TYPES:
            self._trigger_mode.add_named(self._build_trigger_fields(t), t["id"])
        trig_box.append(self._trigger_mode)

        # keymode row (shared)
        km_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        km_label = Gtk.Label(label="Key Mode:", xalign=0)
        km_label.add_css_class("mm-param-label")
        km_label.set_size_request(110, -1)
        km_row.append(km_label)
        km_entry = Gtk.Entry()
        km_entry.set_text("default")
        km_entry.set_placeholder_text("default, common or custom")
        km_entry.set_hexpand(True)
        km_entry.connect("notify::text", lambda *_: self.on_block_change())
        km_row.append(km_entry)
        self._trigger_widgets["keymode"] = km_entry
        trig_box.append(km_row)

        hint = Gtk.Label(xalign=0)
        hint.add_css_class("dim-label")
        self._trigger_hint = hint
        trig_box.append(hint)

        box.append(trig_box)
        self._update_trigger_ui()

    def _build_trigger_fields(self, t: dict[str, Any]) -> Gtk.Widget:
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for f in t["fields"]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lbl = Gtk.Label(label=f["label"] + ":", xalign=0)
            lbl.add_css_class("mm-param-label")
            lbl.set_size_request(110, -1)
            row.append(lbl)

            ftype = f["type"]
            store = f"{t['id']}:{f['name']}"
            if ftype == "multi":
                # toggle chain
                toggles: dict[str, Gtk.ToggleButton] = {}
                for opt in f["options"]:
                    btn = Gtk.ToggleButton(label=opt)
                    if opt == "SUPER":
                        btn.set_active(True)
                    btn.connect("toggled", lambda *_: self.on_block_change())
                    toggles[opt] = btn
                    row.append(btn)
                self._trigger_widgets[f"multi:{store}"] = toggles
            elif ftype == "enum":
                dd = Gtk.DropDown(model=Gtk.StringList.new(f["options"]))
                dd.set_hexpand(True)
                dd.connect("notify::selected", lambda *_: self.on_block_change())
                row.append(dd)
                self._trigger_widgets[store] = dd
            else:
                e = Gtk.Entry()
                e.set_placeholder_text(f.get("hint", ""))
                e.set_hexpand(True)
                e.connect("notify::text", lambda *_: self.on_block_change())
                row.append(e)
                self._trigger_widgets[store] = e

            vbox.append(row)
        return vbox

    # ------------------------------------------------------------- Trigger --

    def _on_trigger_type_changed(self, *_):
        self._update_trigger_ui()

    def _update_trigger_ui(self) -> None:
        idx = self._trigger_type_dd.get_selected()
        t = TRIGGER_TYPES[idx]
        self._trigger_mode.set_visible_child_name(t["id"])
        self._trigger_hint.set_text(t["hint"])

    def _current_trigger(self) -> dict[str, Any]:
        idx = self._trigger_type_dd.get_selected()
        return TRIGGER_TYPES[idx]

    def _get_mods(self) -> str:
        store = f"multi:{self._current_trigger()['id']}:mods"
        toggles = self._trigger_widgets.get(store) or {}
        active = [m for m, b in toggles.items() if b.get_active()]
        return "+".join(active) if active else "NONE"

    def _get_value(self, name: str, default: str = "") -> str:
        store = f"{self._current_trigger()['id']}:{name}"
        w = self._trigger_widgets.get(store)
        if w is None:
            return default
        if isinstance(w, Gtk.DropDown):
            item = w.get_selected_item()
            return item.get_string() if item else default
        return w.get_text()

    # --------------------------------------------------------------- Blocks --

    def add_block(self, cmd: str, insert_after: _ActionBlock | None = None) -> None:
        block = _ActionBlock(self, cmd)
        self._blocks.append(block)
        self.canvas.append(block)
        self.on_block_change()

    def remove_block(self, block: _ActionBlock) -> None:
        if block in self._blocks:
            self._blocks.remove(block)
            self.canvas.remove(block)
            self.on_block_change()

    def move_block(self, uid: int, insert_before: _ActionBlock) -> None:
        src = next((b for b in self._blocks if b.uid == uid), None)
        if src is None or src is insert_before:
            return
        self.canvas.remove(src)
        self._blocks.remove(src)
        idx = self._blocks.index(insert_before)
        self._blocks.insert(idx, src)
        self.canvas.insert_child_after(src, insert_before)
        self.on_block_change()

    def _on_canvas_drop(self, target, value, x, y) -> bool:
        raw = value
        if hasattr(raw, "get_string"):
            raw = raw.get_string()
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return False
        if data.get("kind") == "move":
            return False
        if data.get("cmd"):
            self.add_block(data["cmd"])
            return True
        return False

    def _on_palette_search(self, entry: Gtk.SearchEntry) -> None:
        q = entry.get_text().strip().lower()
        for cat, lbox in self._palette_boxes.items():
            for child in lbox:
                row = child
                if isinstance(row, Gtk.ListBoxRow) and row.get_child() is not None:
                    label = self._find_label(row.get_child())
                    txt = (label or "").lower()
                    row.set_visible(not q or q in txt)
                elif isinstance(row, Gtk.Widget):
                    row.set_visible(True)

    @staticmethod
    def _find_label(widget: Gtk.Widget) -> str:
        if isinstance(widget, Gtk.Label):
            return widget.get_text()
        if isinstance(widget, Gtk.Box):
            child = widget.get_first_child()
            while child is not None:
                text = CommandBuilderPage._find_label(child)
                if text:
                    return text
                child = child.get_next_sibling()
        return ""

    def on_block_change(self, *_) -> None:
        placeholder = getattr(self, "_placeholder", None)
        if placeholder is not None:
            placeholder.set_visible(not bool(self._blocks))
        preview = getattr(self, "_preview", None)
        if preview is not None:
            self._update_preview()
        self._gate_palette()

    # ------------------------------------------------------------------ Gate --

    def _schema_categories(self) -> dict[str, list[str]]:
        """``{category: [cmd, ...]}`` in the exact shape mango_compat expects."""
        return {cat: [d["cmd"] for d in entries] for cat, entries in DISPATCHERS.items()}

    def _gate_palette(self) -> None:
        """Grey / disable palette rows whose dispatcher isn't available next,
        given the current trigger kind and the blocks already on the canvas.

        This is the honest rule: I don't guess tiny/maxi metadata that the
        schema never typed — compat only ever derives pointer-capability from
        real dispatcher categories, so a row is greyed *only* when it truly
        cannot interact with the chosen trigger.
        """
        if not getattr(self, "_palette_boxes", None):
            return
        kind = self._current_trigger().get("id", "")
        existing = [b.cmd for b in self._blocks]
        try:
            allowed = set(
                available_next(kind, existing, self._schema_categories())
            )
        except Exception:
            allowed = None  # never hard-block on engine hiccup
        for cat, lbox in self._palette_boxes.items():
            for row in lbox:
                cmd = getattr(row, "_cmd", None)
                if cmd is None:
                    continue
                ok = allowed is None or cmd in allowed
                row.set_sensitive(ok)
                row.get_child().remove_css_class("mm-palette-dim")
                if not ok:
                    row.get_child().add_css_class("mm-palette-dim")

    def _clear_canvas(self) -> None:
        for block in list(self._blocks):
            self.canvas.remove(block)
        self._blocks.clear()
        self.on_block_change()
        self.show_toast("Script cleared")

    # -------------------------------------------------------------- Preview --

    def _lines(self) -> list[str]:
        t = self._current_trigger()
        kw = t["kw"]
        mods = self._get_mods()
        lines: list[str] = []
        for block in self._blocks:
            cmd = format_dispatcher(block.cmd, block.get_values())
            tag = t["id"]
            if tag == "key":
                flags = ",".join(
                    m for m, b in (self._flag_toggles() or {}).items() if b.get_active()
                )
                btype = f"bind{flags}" if flags else "bind"
                lines.append(f"{btype}={mods},{self._get_value('key')},{cmd}")
            elif tag == "mouse":
                lines.append(f"{kw}={mods},{self._get_value('key')},{cmd}")
            elif tag == "axis":
                lines.append(f"{kw}={mods},{self._get_value('key')},{cmd}")
            elif tag == "gesture":
                lines.append(f"{kw}={mods},{self._get_value('key')},{self._get_value('fingers')},{cmd}")
            elif tag == "switch":
                lines.append(f"{kw}={self._get_value('key')},{cmd}")
        return lines

    def _flag_toggles(self) -> dict[str, Gtk.ToggleButton]:
        return self._trigger_widgets.get("multi:key:flags") or {}

    def _update_preview(self) -> None:
        buf = self._preview.get_buffer()
        km = self._get_value("keymode", "default").strip() or "default"
        out = [f"keymode={km}"]
        out.extend(self._lines())
        buf.set_text("\n".join(out) if out else "")

    # ----------------------------------------------------------------- Save --

    def _save_script(self) -> None:
        t = self._current_trigger()
        if not self._blocks:
            self.show_toast("Drop at least one action block onto the canvas")
            return
        tag = t["id"]
        km = self._get_value("keymode", "default").strip() or "default"
        mods = self._get_mods()

        count = 0
        for block in self._blocks:
            args = ",".join(v for v in block.get_values().values() if v.strip())
            if tag == "key":
                key = self._get_value("key").strip()
                if not key:
                    self.show_toast("Key cannot be empty")
                    return
                flags = ",".join(
                    m for m, b in self._flag_toggles().items() if b.get_active()
                )
                btype = f"bind{flags}" if flags else "bind"
                self._doc.add_binding(BindingEntry(bind_type=btype, modifiers=mods, key=key,
                                                   command=block.cmd, args=args, keymode=km))
            elif tag == "mouse":
                btn = self._get_value("key").strip()
                if not btn:
                    self.show_toast("Button cannot be empty")
                    return
                self._doc.add_mouse_binding(MouseBindingEntry(modifiers=mods, button=btn,
                                                              command=block.cmd, args=args, keymode=km))
            elif tag == "axis":
                direction = self._get_value("key").strip()
                if not direction:
                    self.show_toast("Direction cannot be empty")
                    return
                self._doc.add_axis_binding(AxisBindingEntry(modifiers=mods, direction=direction,
                                                            command=block.cmd, args=args, keymode=km))
            elif tag == "gesture":
                direction = self._get_value("key").strip()
                fingers = int(self._get_value("fingers", "3"))
                if not direction:
                    self.show_toast("Direction cannot be empty")
                    return
                self._doc.add_gesture_binding(GestureBindingEntry(modifiers=mods, direction=direction,
                                                                  fingers=fingers, command=block.cmd,
                                                                  args=args, keymode=km))
            elif tag == "switch":
                fold = self._get_value("key").strip()
                if not fold:
                    self.show_toast("Fold state cannot be empty")
                    return
                self._doc.add_switch_binding(SwitchBindingEntry(fold=fold, command=block.cmd,
                                                                args=args, keymode=km))
            count += 1

        self._commit("add command-builder script")
        self.show_toast(f"Added {count} binding(s) to config")
        self._clear_canvas()