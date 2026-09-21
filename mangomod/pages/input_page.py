"""Input devices configuration page (Keyboard, Trackpad, Mouse, Cursor)."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod.pages.base import BasePage


class InputPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Input Devices")
        self._content = content
        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Keyboard ---
        kb_group = Adw.PreferencesGroup(title="Keyboard", description="Layout and key repeat settings")

        # XKB Layout
        layout_entry = Adw.EntryRow(title="Layouts (e.g. us, ara)")
        layout_entry.set_text(doc.get_setting("xkb_rules_layout", "us"))
        layout_entry.connect("notify::text", lambda r, _: self._on_text_change("xkb_rules_layout", r.get_text()))
        kb_group.add(layout_entry)

        # XKB Variant
        variant_entry = Adw.EntryRow(title="Variant (optional)")
        variant_entry.set_text(doc.get_setting("xkb_rules_variant", ""))
        variant_entry.connect("notify::text", lambda r, _: self._on_text_change("xkb_rules_variant", r.get_text()))
        kb_group.add(variant_entry)

        # XKB Options
        options_entry = Adw.EntryRow(title="Options (e.g. grp:alt_shift_toggle, caps:swapescape)")
        options_entry.set_text(doc.get_setting("xkb_rules_options", ""))
        options_entry.connect("notify::text", lambda r, _: self._on_text_change("xkb_rules_options", r.get_text()))
        kb_group.add(options_entry)

        # Repeat Rate
        repeat_rate_adj = Gtk.Adjustment(value=doc.get_int("repeat_rate", 25), lower=1, upper=100, step_increment=1)
        repeat_rate_row = Adw.SpinRow(title="Repeat Rate", subtitle="Keys repeated per second", adjustment=repeat_rate_adj)
        repeat_rate_row.connect("notify::value", lambda r, _: self._on_int_change("repeat_rate", int(r.get_value())))
        kb_group.add(repeat_rate_row)

        # Repeat Delay
        repeat_delay_adj = Gtk.Adjustment(value=doc.get_int("repeat_delay", 600), lower=100, upper=2000, step_increment=50)
        repeat_delay_row = Adw.SpinRow(title="Repeat Delay (ms)", subtitle="Delay before key begins repeating", adjustment=repeat_delay_adj)
        repeat_delay_row.connect("notify::value", lambda r, _: self._on_int_change("repeat_delay", int(r.get_value())))
        kb_group.add(repeat_delay_row)

        # Numlock on startup
        numlock_row = Adw.SwitchRow(title="Enable NumLock on Startup")
        numlock_row.set_active(doc.get_bool("numlockon", False))
        numlock_row.connect("notify::active", lambda r, _: self._on_bool_change("numlockon", r.get_active()))
        kb_group.add(numlock_row)

        content.append(kb_group)

        # --- Trackpad ---
        tp_group = Adw.PreferencesGroup(title="Trackpad", description="Touchpad gestures and clicking")

        # Disable trackpad
        disable_tp = Adw.SwitchRow(title="Disable Trackpad Completely")
        disable_tp.set_active(doc.get_bool("disable_trackpad", False))
        disable_tp.connect("notify::active", lambda r, _: self._on_bool_change("disable_trackpad", r.get_active()))
        tp_group.add(disable_tp)

        # Tap to click
        tap_click = Adw.SwitchRow(title="Tap to Click")
        tap_click.set_active(doc.get_bool("tap_to_click", True))
        tap_click.connect("notify::active", lambda r, _: self._on_bool_change("tap_to_click", r.get_active()))
        tp_group.add(tap_click)

        # Tap and drag
        tap_drag = Adw.SwitchRow(title="Tap and Drag")
        tap_drag.set_active(doc.get_bool("tap_and_drag", True))
        tap_drag.connect("notify::active", lambda r, _: self._on_bool_change("tap_and_drag", r.get_active()))
        tp_group.add(tap_drag)

        # Natural scrolling
        tp_nat_scroll = Adw.SwitchRow(title="Natural Scrolling")
        tp_nat_scroll.set_active(doc.get_bool("trackpad_natural_scrolling", False))
        tp_nat_scroll.connect("notify::active", lambda r, _: self._on_bool_change("trackpad_natural_scrolling", r.get_active()))
        tp_group.add(tp_nat_scroll)

        # Disable while typing
        dwt_row = Adw.SwitchRow(title="Disable While Typing")
        dwt_row.set_active(doc.get_bool("trackpad_disable_while_typing", True))
        dwt_row.connect("notify::active", lambda r, _: self._on_bool_change("trackpad_disable_while_typing", r.get_active()))
        tp_group.add(dwt_row)

        # Left-handed mode
        tp_left = Adw.SwitchRow(title="Left-Handed Mode")
        tp_left.set_active(doc.get_bool("trackpad_left_handed", False))
        tp_left.connect("notify::active", lambda r, _: self._on_bool_change("trackpad_left_handed", r.get_active()))
        tp_group.add(tp_left)

        # Middle button emulation
        tp_mid = Adw.SwitchRow(title="Middle Button Emulation", subtitle="Click left and right buttons simultaneously")
        tp_mid.set_active(doc.get_bool("trackpad_middle_button_emulation", False))
        tp_mid.connect("notify::active", lambda r, _: self._on_bool_change("trackpad_middle_button_emulation", r.get_active()))
        tp_group.add(tp_mid)

        content.append(tp_group)

        # --- Mouse ---
        mouse_group = Adw.PreferencesGroup(title="Mouse", description="Pointing device settings")

        mouse_nat_scroll = Adw.SwitchRow(title="Natural Scrolling")
        mouse_nat_scroll.set_active(doc.get_bool("mouse_natural_scrolling", False))
        mouse_nat_scroll.connect("notify::active", lambda r, _: self._on_bool_change("mouse_natural_scrolling", r.get_active()))
        mouse_group.add(mouse_nat_scroll)

        mouse_left = Adw.SwitchRow(title="Left-Handed Mode")
        mouse_left.set_active(doc.get_bool("mouse_left_handed", False))
        mouse_left.connect("notify::active", lambda r, _: self._on_bool_change("mouse_left_handed", r.get_active()))
        mouse_group.add(mouse_left)

        mouse_mid = Adw.SwitchRow(title="Middle Button Emulation")
        mouse_mid.set_active(doc.get_bool("mouse_middle_button_emulation", False))
        mouse_mid.connect("notify::active", lambda r, _: self._on_bool_change("mouse_middle_button_emulation", r.get_active()))
        mouse_group.add(mouse_mid)

        content.append(mouse_group)

        # --- Cursor & Pointer ---
        cursor_group = Adw.PreferencesGroup(title="Cursor and Pointer", description="Cursor appearance and behavior")

        cursor_size_adj = Gtk.Adjustment(value=doc.get_int("cursor_size", 24), lower=12, upper=96, step_increment=4)
        cursor_size_row = Adw.SpinRow(title="Cursor Size", adjustment=cursor_size_adj)
        cursor_size_row.connect("notify::value", lambda r, _: self._on_int_change("cursor_size", int(r.get_value())))
        cursor_group.add(cursor_size_row)

        cursor_theme_row = Adw.EntryRow(title="Cursor Theme")
        cursor_theme_row.set_text(doc.get_setting("cursor_theme", "default"))
        cursor_theme_row.connect("notify::text", lambda r, _: self._on_text_change("cursor_theme", r.get_text()))
        cursor_group.add(cursor_theme_row)

        warp_row = Adw.SwitchRow(title="Warp Cursor", subtitle="Warp cursor to newly focused window")
        warp_row.set_active(doc.get_bool("warpcursor", True))
        warp_row.connect("notify::active", lambda r, _: self._on_bool_change("warpcursor", r.get_active()))
        cursor_group.add(warp_row)

        hide_row = Adw.SwitchRow(title="Hide Cursor on Keypress")
        hide_row.set_active(doc.get_bool("cursor_hide_on_keypress", False))
        hide_row.connect("notify::active", lambda r, _: self._on_bool_change("cursor_hide_on_keypress", r.get_active()))
        cursor_group.add(hide_row)

        content.append(cursor_group)

    def _on_text_change(self, key: str, value: str) -> None:
        self._doc.set_setting(key, value.strip())
        self._commit(f"update {key}")

    def _on_int_change(self, key: str, value: int) -> None:
        self._doc.set_setting(key, value)
        self._commit(f"update {key}")

    def _on_bool_change(self, key: str, value: bool) -> None:
        self._doc.set_setting(key, 1 if value else 0)
        self._commit(f"update {key}")
