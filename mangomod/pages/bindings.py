"""Key bindings configuration page with searchable list and interactive keyboard visualizer."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Pango

from mangomod.config_parser import BindingEntry
from mangomod.pages.base import BasePage
from mangomod.widgets import KeyboardVisualizer, normalize_key_id
from mangomod.xkb_helper import format_modifiers

MANGO_DISPATCH_COMMANDS = [
    # Window management
    ("killclient", "Close focused window"),
    ("togglefloating", "Toggle floating state"),
    ("togglefullscreen", "Toggle fullscreen"),
    ("togglefakefullscreen", "Toggle fake fullscreen"),
    ("togglemaximizescreen", "Maximize window screen"),
    ("toggleglobal", "Pin window across all tags"),
    ("minimized", "Minimize window to scratchpad"),
    ("restore_minimized", "Restore minimized window"),
    ("centerwin", "Center floating window"),
    ("toggle_scratchpad", "Toggle scratchpad"),
    ("toggle_special_tag", "Toggle special scratchpad workspace"),
    ("tag_special_tag", "Move window to special tag"),
    # Focus & Navigation
    ("focusdir", "Focus window in direction (left, right, up, down)"),
    ("focusstack", "Cycle focus in window stack (next, prev)"),
    ("focuslast", "Focus previously active window"),
    ("exchange_client", "Swap window with neighbor (left, right, up, down)"),
    ("zoom", "Swap focused window with Master"),
    ("resizewin", "Resize window (+W, +H)"),
    ("movewin", "Move window (+X, +Y)"),
    # Tags & Monitors
    ("view", "Switch to tag number (e.g. 1, 2, ...)"),
    ("tag", "Move window to tag (and focus it)"),
    ("tagsilent", "Move window to tag (silently)"),
    ("viewtoleft", "Switch to previous tag"),
    ("viewtoright", "Switch to next tag"),
    ("viewtoleft_have_client", "Switch to left tag with active client"),
    ("viewtoright_have_client", "Switch to right tag with active client"),
    ("focusmon", "Focus monitor (left, right, or name)"),
    ("tagmon", "Move window to monitor (left, right, or name)"),
    # Layout & Compositor
    ("switch_layout", "Cycle layout mode"),
    ("set_proportion", "Set scroller layout proportion (e.g. 1.0)"),
    ("switch_proportion_preset", "Switch scroller proportion preset"),
    ("incgaps", "Increase/decrease gaps (+1, -1)"),
    ("togglegaps", "Toggle gaps on/off"),
    ("reload_config", "Hot-reload configuration"),
    ("quit", "Exit Mango compositor"),
    # Launching
    ("spawn", "Execute shell command or program"),
    ("spawn_shell", "Execute shell script"),
    ("switch_keyboard_layout", "Switch keyboard layout"),
    ("setkeymode", "Switch keymode / submap"),
]


class BindingsPage(BasePage):
    def __init__(self, window):
        super().__init__(window)
        self._filter_text = ""
        self._filter_mod = "ALL"
        self._visualizer: KeyboardVisualizer | None = None
        self._bindings_list_box: Gtk.ListBox | None = None
        self._conflict_keys: set[str] = set()

    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("Key Bindings")
        self._content = content

        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Add Key Binding")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", lambda *_: self._open_edit_dialog())
        header.pack_end(add_btn)

        # Keyboard visualizer card
        vis_frame = Gtk.Frame()
        vis_frame.add_css_class("mm-canvas-frame")
        vis_frame.set_margin_bottom(12)

        vis_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vis_box.set_margin_top(8)
        vis_box.set_margin_bottom(8)
        vis_box.set_margin_start(8)
        vis_box.set_margin_end(8)

        # Modifiers toggle buttons row for visualizer
        mod_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mod_label = Gtk.Label(label="Visualizer Filter:")
        mod_label.add_css_class("dim-label")
        mod_bar.append(mod_label)

        self._mod_btns: dict[str, Gtk.ToggleButton] = {}
        for m in ["SUPER", "CTRL", "ALT", "SHIFT"]:
            btn = Gtk.ToggleButton(label=m)
            if m == "SUPER":
                btn.set_active(True)
            btn.connect("toggled", lambda *_: self._update_visualizer_mods())
            self._mod_btns[m] = btn
            mod_bar.append(btn)

        vis_box.append(mod_bar)

        self._visualizer = KeyboardVisualizer(on_key_clicked=self._on_visualizer_key_clicked)
        vis_box.append(self._visualizer)
        vis_frame.set_child(vis_box)
        content.append(vis_frame)

        # Search and filter bar
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        search_entry = Gtk.SearchEntry()
        search_entry.set_hexpand(True)
        search_entry.set_placeholder_text("Search shortcuts or commands…")
        search_entry.connect("search-changed", self._on_search_changed)
        filter_box.append(search_entry)

        content.append(filter_box)

        # Bindings List Group
        self._list_group = Adw.PreferencesGroup(title="Shortcuts")
        self._bindings_list_box = Gtk.ListBox()
        self._bindings_list_box.add_css_class("boxed-list")
        self._list_group.add(self._bindings_list_box)
        content.append(self._list_group)

        self._refresh_bindings_data()
        return tb

    def _update_visualizer_mods(self) -> None:
        if not self._visualizer:
            return
        active = {m for m, btn in self._mod_btns.items() if btn.get_active()}
        self._visualizer.set_active_mods(active)

    def _on_visualizer_key_clicked(self, key: str) -> None:
        self._filter_text = key
        self._rebuild_list()

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._filter_text = entry.get_text().strip().lower()
        self._rebuild_list()

    def _refresh_bindings_data(self) -> None:
        # Detect conflicts: same (keymode, modifiers, key) without 'c' flag
        counts: dict[tuple[str, str, str], int] = {}
        self._conflict_keys.clear()

        doc_binds = self._doc.get_bindings()
        for b in doc_binds:
            norm_mods = " ".join(sorted(b.modifiers.replace("+", " ").upper().split()))
            norm_k = normalize_key_id(b.key)
            sig = (b.keymode, norm_mods, norm_k)
            counts[sig] = counts.get(sig, 0) + 1

        vis_data = []
        for b in doc_binds:
            norm_mods = " ".join(sorted(b.modifiers.replace("+", " ").upper().split()))
            norm_k = normalize_key_id(b.key)
            sig = (b.keymode, norm_mods, norm_k)
            has_conflict = counts.get(sig, 0) > 1 and "c" not in b.bind_type
            if has_conflict:
                self._conflict_keys.add(norm_k)
            vis_data.append({
                "modifiers": b.modifiers,
                "key": b.key,
                "command": b.command,
                "is_conflict": has_conflict,
            })

        if self._visualizer:
            self._visualizer.set_bindings_data(vis_data, self._conflict_keys)

        self._rebuild_list()

    def _rebuild_list(self) -> None:
        if not self._bindings_list_box:
            return

        # Clear existing rows
        while child := self._bindings_list_box.get_first_child():
            self._bindings_list_box.remove(child)

        bindings = self._doc.get_bindings()

        shown = 0
        for bind in bindings:
            # Filter
            norm_k = normalize_key_id(bind.key)
            cmd_full = f"{bind.command} {bind.args}".strip()
            mods_str = format_modifiers(bind.modifiers)

            if self._filter_text:
                q = self._filter_text
                if q not in norm_k and q not in bind.key.lower() and q not in cmd_full.lower() and q not in bind.modifiers.lower():
                    continue

            row = self._create_binding_row(bind)
            self._bindings_list_box.append(row)
            shown += 1

        self._list_group.set_description(f"{shown} active shortcuts" if shown == len(bindings) else f"Showing {shown} of {len(bindings)} shortcuts")

    def _create_binding_row(self, bind: BindingEntry) -> Adw.ActionRow:
        row = Adw.ActionRow()

        # Key badge representation
        key_label = Gtk.Label()
        mods_display = format_modifiers(bind.modifiers)
        combo_str = f"{mods_display} + {bind.key.upper()}" if mods_display else bind.key.upper()
        key_label.set_markup(f"<b>{combo_str}</b>")
        key_label.add_css_class("mm-key-badge")
        row.add_prefix(key_label)

        # Title: Command and args
        cmd_text = f"{bind.command} {bind.args}".strip()
        row.set_title(cmd_text)

        # Subtitle: flags and keymode
        subs = []
        if bind.keymode and bind.keymode != "default":
            subs.append(f"mode: {bind.keymode}")
        if bind.bind_type != "bind":
            flags = bind.bind_type.replace("bind", "")
            subs.append(f"flags: [{flags}]")
        if bind.inline_comment:
            subs.append(f"# {bind.inline_comment}")

        norm_k = normalize_key_id(bind.key)
        if norm_k in self._conflict_keys and "c" not in bind.bind_type:
            subs.append("⚠️ CONFLICT")
            row.add_css_class("error")

        if subs:
            row.set_subtitle(" • ".join(subs))

        # Edit and Delete buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
        edit_btn.add_css_class("flat")
        edit_btn.set_tooltip_text("Edit Shortcut")
        edit_btn.connect("clicked", lambda *_: self._open_edit_dialog(bind))
        btn_box.append(edit_btn)

        del_btn = Gtk.Button(icon_name="user-trash-symbolic")
        del_btn.add_css_class("flat")
        del_btn.set_tooltip_text("Delete Shortcut")
        del_btn.connect("clicked", lambda *_: self._delete_binding(bind))
        btn_box.append(del_btn)

        row.add_suffix(btn_box)
        return row

    def _delete_binding(self, bind: BindingEntry) -> None:
        if self._doc.remove_binding(bind):
            self._commit(f"delete keybind {bind.key}")
            self._refresh_bindings_data()
            self.show_toast(f"Deleted shortcut {bind.key}")

    def _open_edit_dialog(self, bind: BindingEntry | None = None) -> None:
        dialog = Adw.PreferencesWindow()
        dialog.set_title("Edit Shortcut" if bind else "Add Key Shortcut")
        dialog.set_default_size(480, 480)
        dialog.set_transient_for(self._win)
        dialog.set_modal(True)

        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Shortcut Details")

        # Modifiers Checkboxes
        cur_mods = set(bind.modifiers.replace("+", " ").upper().split()) if bind else {"SUPER"}
        mod_switches: dict[str, Adw.SwitchRow] = {}
        for m in ["SUPER", "CTRL", "ALT", "SHIFT"]:
            sw = Adw.SwitchRow(title=f"Modifier {m}")
            sw.set_active(m in cur_mods)
            group.add(sw)
            mod_switches[m] = sw

        # Key Entry
        key_entry = Adw.EntryRow(title="Key (e.g. Return, q, left, F1)")
        key_entry.set_text(bind.key if bind else "")
        group.add(key_entry)

        # Action Command Dropdown / Entry
        cmd_entry = Adw.EntryRow(title="Command Dispatcher")
        cmd_entry.set_text(bind.command if bind else "spawn")
        group.add(cmd_entry)

        args_entry = Adw.EntryRow(title="Arguments (optional)")
        args_entry.set_text(bind.args if bind else "")
        group.add(args_entry)

        # Flags entry
        flags_entry = Adw.EntryRow(title="Flags (e.g. l for locked, r for release, c for conflict)")
        cur_flags = bind.bind_type.replace("bind", "") if bind else ""
        flags_entry.set_text(cur_flags)
        group.add(flags_entry)

        # Keymode
        mode_entry = Adw.EntryRow(title="Key Mode (default, common, or custom)")
        mode_entry.set_text(bind.keymode if bind else "default")
        group.add(mode_entry)

        page.add(group)
        dialog.add(page)

        # Save Button in Header
        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")

        def _on_save(*_):
            k = key_entry.get_text().strip()
            if not k:
                self.show_toast("Key cannot be empty")
                return

            active_mods = [m for m, sw in mod_switches.items() if sw.get_active()]
            mod_str = "+".join(active_mods) if active_mods else "NONE"
            cmd_str = cmd_entry.get_text().strip()
            args_str = args_entry.get_text().strip()
            fl = flags_entry.get_text().strip()
            bind_type = f"bind{fl}" if fl else "bind"
            km = mode_entry.get_text().strip() or "default"

            if bind:
                bind.modifiers = mod_str
                bind.key = k
                bind.command = cmd_str
                bind.args = args_str
                bind.bind_type = bind_type
                bind.keymode = km
            else:
                new_b = BindingEntry(
                    bind_type=bind_type,
                    modifiers=mod_str,
                    key=k,
                    command=cmd_str,
                    args=args_str,
                    keymode=km,
                )
                self._doc.add_binding(new_b)

            self._commit("update keybindings")
            self._refresh_bindings_data()
            dialog.close()
            self.show_toast(f"Saved shortcut {k}")

        save_btn.connect("clicked", _on_save)
        header.pack_end(save_btn)

        # Put header on top
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)

        dialog.present()
