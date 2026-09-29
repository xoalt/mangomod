"""All Settings — a docs-driven browser for every scalar option Mangowm offers.

Every option from the official docs (mangomod.mango_settings.SETTINGS) appears
here with a type-aware editor, grouped by documentation section and filterable
with a search box. Being generated from the catalog, anything documented is
always reachable from this page.
"""

from __future__ import annotations

import re
import math
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gdk, Gtk

from mangomod.config_parser import SettingEntry
from mangomod.mango_settings import SETTINGS, settings_by_section
from mangomod.pages.base import BasePage

_QUERY: str = ""


def _qr() -> str:
    return _QUERY


def _hex_to_rgba(hexstr: str) -> Gdk.RGBA:
    h = str(hexstr).strip()
    if h.startswith("#"):
        h = "0x" + h[1:]
    h = h.replace("0x", "").replace("0X", "")
    h = h.ljust(8, "f")
    if h.startswith("#"):
        h = h[1:]
    try:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        a = int(h[6:8], 16) / 255.0
        return Gdk.RGBA(r, g, b, a)
    except ValueError:
        return Gdk.RGBA(0.0, 0.0, 0.0, 1.0)


def _rgba_to_hex(rgba: Gdk.RGBA) -> str:
    r = int(max(0.0, min(1.0, rgba.red)) * 255)
    g = int(max(0.0, min(1.0, rgba.green)) * 255)
    b = int(max(0.0, min(1.0, rgba.blue)) * 255)
    a = int(max(0.0, min(1.0, rgba.alpha)) * 255)
    return f"0x{r:02x}{g:02x}{b:02x}{a:02x}"


class AllSettingsPage(BasePage):
    def __init__(self, window):
        super().__init__(window)
        self._rows: list[tuple[Gtk.Widget, str, str]] = []  # (row, key, label)

    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("All Settings")

        search_group = Adw.PreferencesGroup(
            title="Complete Mangowm settings catalog",
            description="Every documented option rendered from the docs catalog "
                        f"({len(SETTINGS)} settings). Results update live as you type.",
        )
        self._search = Gtk.SearchEntry()
        self._search.set_placeholder_text("Search all settings…")
        self._search.add_css_class("mm-search-entry")
        self._search.connect("search-changed", self._on_search_changed)
        search_group.add(self._search)
        content.append(search_group)

        self._page = Adw.PreferencesPage()
        self._catalog_keys = {item["key"] for item in SETTINGS}
        self._unknown_rows: list[Gtk.Widget] = []
        self._unknown_group = Adw.PreferencesGroup(
            title="Other config options",
            description="Options absent from this version's catalog stay intact. Edit or add one here if your Mango version supports it.",
        )
        self._page.add(self._unknown_group)
        self._new_key = Adw.EntryRow(title="Option name")
        self._new_value = Adw.EntryRow(title="Value")
        self._unknown_group.add(self._new_key)
        self._unknown_group.add(self._new_value)
        add_button = Gtk.Button(label="Add option")
        add_button.add_css_class("suggested-action")
        add_button.set_halign(Gtk.Align.END)
        add_button.connect("clicked", self._add_unknown)
        self._unknown_group.add(add_button)
        for section, entries in settings_by_section().items():
            group = Adw.PreferencesGroup(title=GLib.markup_escape_text(section))
            for entry in entries:
                row = self._build_row(entry)
                group.add(row)
                self._rows.append((row, entry["key"], entry.get("label", entry["key"])))
                source = self._win.app_state.setting_source(entry['key'])
                row.set_tooltip_text(self._win.tr('Source file') + ': ' +
                                     (str(source[1]) if source else self._win.tr('Default value')))
            self._page.add(group)

        content.append(self._page)
        self._refresh_unknown()
        return tb

    def _valid_unknown(self, key: str, value: str) -> bool:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.:-]*", key) or "\n" in value or "\r" in value or "\x00" in value:
            self.show_toast("Use a single-line value and a config option name without spaces.")
            return False
        return True

    def _add_unknown(self, *_):
        key, value = self._new_key.get_text().strip(), self._new_value.get_text()
        if not self._valid_unknown(key, value):
            return
        if key in self._catalog_keys:
            self.show_toast("That option is already in the settings catalog.")
            return
        if self._doc.get_setting(key) is not None:
            self.show_toast("That option already exists below; edit its value there.")
            return
        self._write(key, value, "text")
        self._new_key.set_text("")
        self._new_value.set_text("")
        self._refresh_unknown()

    def _refresh_unknown(self):
        for row in self._unknown_rows:
            self._unknown_group.remove(row)
        self._unknown_rows.clear()
        self._unknown_fields = []
        seen = set()
        entries = [entry for doc, _ in self._win.app_state.documents() for entry in doc.entries]
        for entry in reversed(entries):
            if not isinstance(entry, SettingEntry) or entry.key in self._catalog_keys or entry.key in seen:
                continue
            if self._win.app_state.setting_source(entry.key) is None:
                continue
            seen.add(entry.key)
            row = Adw.ActionRow(title=entry.key, subtitle="Custom or newer Mango option")
            field = Gtk.Entry(text=self._doc.get_setting(entry.key, entry.value), hexpand=True)
            self._unknown_fields.append((entry.key, field))
            source = self._win.app_state.setting_source(entry.key)
            if source:
                row.set_tooltip_text(self._win.tr('Source file') + ': ' + str(source[1]))
            field.set_width_chars(18)
            apply = Gtk.Button(label="Apply")
            def save(_button, key=entry.key, editor=field):
                value = editor.get_text()
                if self._valid_unknown(key, value):
                    self._write(key, value, "text")
            apply.connect("clicked", save)
            row.add_suffix(field)
            row.add_suffix(apply)
            self._unknown_group.add(row)
            self._unknown_rows.append(row)

    def on_shown(self):
        if hasattr(self, "_unknown_group"):
            self._refresh_unknown()

    def has_unapplied_fields(self):
        return bool(self._new_key.get_text() or self._new_value.get_text() or
                    any(field.get_text() != self._doc.get_setting(key, '')
                        for key, field in self._unknown_fields))

    # ------------------------------------------------------------- row build --

    def _build_row(self, entry: dict[str, Any]) -> Gtk.Widget:
        key = entry["key"]
        label = GLib.markup_escape_text(entry.get("label", key))
        desc = GLib.markup_escape_text(entry.get("desc", ""))
        ptype = entry.get("type", "str")
        default = str(entry.get("default", ""))

        current = self._doc.get_setting(key)
        if current is None:
            current = default

        # The catalog describes a version, not every value a newer Mango can
        # accept. Keep unfamiliar values visible and editable verbatim.
        if ptype == 'bool' and str(current).lower() not in ('0', '1', 'true', 'false', 'yes', 'no', 'on', 'off'):
            ptype = 'str'
        if ptype in ('int', 'float'):
            try:
                value = float(current)
                if not math.isfinite(value) or (ptype == 'int' and not value.is_integer()):
                    ptype = 'str'
            except ValueError:
                ptype = 'str'

        if ptype == "bool":
            row = Adw.SwitchRow(title=label, subtitle=desc)
            row.set_active(str(current).lower() in ("1", "true", "yes", "on"))
            row.connect("notify::active", lambda r, _, k=key: self._on_bool(k, r.get_active()))
            return row

        if ptype in ("int", "float"):
            lower = entry.get("mini")
            upper = entry.get("maxi")
            if lower is None:
                lower = -100000.0 if ptype == "float" else -100000
            if upper is None:
                upper = 100000.0 if ptype == "float" else 100000
            try:
                value = float(current)
            except ValueError:
                value = float(default)
            adj = Gtk.Adjustment(value=value, lower=min(lower, value), upper=max(upper, value), step_increment=1)
            if ptype == "float":
                row = Adw.SpinRow(title=label, subtitle=desc, adjustment=adj, digits=2)
                row.connect("notify::value", lambda r, _, k=key: self._on_float(k, float(r.get_value())))
            else:
                row = Adw.SpinRow(title=label, subtitle=desc, adjustment=adj)
                row.connect("notify::value", lambda r, _, k=key: self._on_int(k, int(r.get_value())))
            return row

        if ptype == "enum":
            options = list(entry.get("options", []))
            if str(current) not in options:
                options.append(str(current))
            row = Adw.ComboRow(title=label, subtitle=desc, model=Gtk.StringList.new(options))
            try:
                row.set_selected(max(0, options.index(str(current))))
            except ValueError:
                row.set_selected(0)
            row.connect("notify::selected", lambda r, _, k=key, o=options: self._on_enum(k, o, r.get_selected()))
            return row

        if ptype == "color":
            row = Adw.ActionRow(title=label, subtitle=desc)
            hex_label = Gtk.Label(label=str(current))
            hex_label.add_css_class("mm-param-label")
            btn = Gtk.ColorButton()
            btn.set_rgba(_hex_to_rgba(str(current)))
            color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            color_box.append(hex_label)
            color_box.append(btn)
            row.add_suffix(color_box)
            btn.connect("color-set", lambda b, k=key, l=hex_label: self._on_color(k, l, b))
            return row

        # str / curve / mask / fallback
        row = Adw.ActionRow(title=label, subtitle=desc)
        entry = Gtk.Entry()
        entry.set_text(str(current))
        entry.set_hexpand(True)
        entry.connect("notify::text", lambda e, _, k=key: self._on_text(k, e.get_text()))
        row.add_suffix(entry)
        return row

    # ----------------------------------------------------------- write ops --

    def _write(self, key: str, value: Any, what: str) -> None:
        before = self._win.app_state.snapshot()
        self._doc.set_setting(key, value)
        if before != self._win.app_state.snapshot():
            self._commit(f"update {key}")

    def _on_bool(self, key: str, active: bool) -> None:
        self._write(key, 1 if active else 0, "bool")

    def _on_int(self, key: str, value: int) -> None:
        self._write(key, value, "int")

    def _on_float(self, key: str, value: float) -> None:
        self._write(key, repr(value), "float")

    def _on_text(self, key: str, value: str) -> None:
        self._write(key, value, "text")

    def _on_enum(self, key: str, options: list[str], index: int) -> None:
        if 0 <= index < len(options):
            self._write(key, options[index], "enum")

    def _on_color(self, key: str, hex_label: Gtk.Label, btn: Gtk.ColorButton) -> None:
        hexs = _rgba_to_hex(btn.get_rgba())
        hex_label.set_text(hexs)
        self._write(key, hexs, "color")

    # ------------------------------------------------------------- filtering --

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        global _QUERY
        _QUERY = entry.get_text().strip().lower()
        for row, key, label in self._rows:
            haystack = f"{key} {label}".lower()
            row.set_visible(not _QUERY or _QUERY in haystack)
