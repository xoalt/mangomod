"""Layout configuration page (Master-Stack, Scroller, Dwindle, Overview, Scratchpad)."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod.pages.base import BasePage


class LayoutPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Layout Settings")
        self._content = content
        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Master-Stack Layout ---
        ms_grp = Adw.PreferencesGroup(title="Master-Stack Layout", description="Classic dwm-style master and slave stack")

        new_master = Adw.SwitchRow(title="New Window as Master", subtitle="Spawn newly opened windows in the master area")
        new_master.set_active(doc.get_bool("new_is_master", True))
        new_master.connect("notify::active", lambda r, _: self._on_bool_change("new_is_master", r.get_active()))
        ms_grp.add(new_master)

        mfact_adj = Gtk.Adjustment(value=doc.get_float("default_mfact", 0.55), lower=0.1, upper=0.9, step_increment=0.05)
        mfact_row = Adw.SpinRow(title="Master Factor (mfact)", subtitle="Proportion of screen occupied by master window", adjustment=mfact_adj, digits=2)
        mfact_row.connect("notify::value", lambda r, _: self._on_float_change("default_mfact", float(r.get_value())))
        ms_grp.add(mfact_row)

        nmaster_adj = Gtk.Adjustment(value=doc.get_int("default_nmaster", 1), lower=1, upper=10, step_increment=1)
        nmaster_row = Adw.SpinRow(title="Number of Masters (nmaster)", adjustment=nmaster_adj)
        nmaster_row.connect("notify::value", lambda r, _: self._on_int_change("default_nmaster", int(r.get_value())))
        ms_grp.add(nmaster_row)

        content.append(ms_grp)

        # --- Scroller Layout ---
        scroller_grp = Adw.PreferencesGroup(title="Scroller Layout", description="Horizontal scrolling column layout")

        s_prop_adj = Gtk.Adjustment(value=doc.get_float("scroller_default_proportion", 0.8), lower=0.2, upper=1.0, step_increment=0.05)
        s_prop_row = Adw.SpinRow(title="Default Column Proportion", subtitle="Width ratio of newly opened column", adjustment=s_prop_adj, digits=2)
        s_prop_row.connect("notify::value", lambda r, _: self._on_float_change("scroller_default_proportion", float(r.get_value())))
        scroller_grp.add(s_prop_row)

        s_single_adj = Gtk.Adjustment(value=doc.get_float("scroller_default_proportion_single", 1.0), lower=0.5, upper=1.0, step_increment=0.05)
        s_single_row = Adw.SpinRow(title="Proportion When Single", subtitle="Width ratio when only one window exists", adjustment=s_single_adj, digits=2)
        s_single_row.connect("notify::value", lambda r, _: self._on_float_change("scroller_default_proportion_single", float(r.get_value())))
        scroller_grp.add(s_single_row)

        s_center = Adw.SwitchRow(title="Keep Focused Window Centered")
        s_center.set_active(doc.get_bool("scroller_focus_center", False))
        s_center.connect("notify::active", lambda r, _: self._on_bool_change("scroller_focus_center", r.get_active()))
        scroller_grp.add(s_center)

        s_presets_entry = Adw.EntryRow(title="Width Presets (comma-separated)")
        s_presets_entry.set_text(doc.get_setting("scroller_proportion_preset", "0.5,0.8,1.0"))
        s_presets_entry.connect("notify::text", lambda r, _: self._on_text_change("scroller_proportion_preset", r.get_text()))
        scroller_grp.add(s_presets_entry)

        content.append(scroller_grp)

        # --- Dwindle Layout ---
        dwindle_grp = Adw.PreferencesGroup(title="Dwindle Layout", description="Binary tree recursive splitting")

        dw_smart = Adw.SwitchRow(title="Smart Split", subtitle="Automatically choose split direction by window geometry")
        dw_smart.set_active(doc.get_bool("dwindle_smart_split", False))
        dw_smart.connect("notify::active", lambda r, _: self._on_bool_change("dwindle_smart_split", r.get_active()))
        dwindle_grp.add(dw_smart)

        dw_manual = Adw.SwitchRow(title="Manual Split Mode")
        dw_manual.set_active(doc.get_bool("dwindle_manual_split", False))
        dw_manual.connect("notify::active", lambda r, _: self._on_bool_change("dwindle_manual_split", r.get_active()))
        dwindle_grp.add(dw_manual)

        dw_preserve = Adw.SwitchRow(title="Preserve Split", subtitle="Retain split proportion when closing neighbors")
        dw_preserve.set_active(doc.get_bool("dwindle_preserve_split", False))
        dw_preserve.connect("notify::active", lambda r, _: self._on_bool_change("dwindle_preserve_split", r.get_active()))
        dwindle_grp.add(dw_preserve)

        content.append(dwindle_grp)

        # --- Overview & Scratchpad ---
        over_grp = Adw.PreferencesGroup(title="Overview and Scratchpad", description="Window overview grid and quick scratchpad")

        hotarea_on = Adw.SwitchRow(title="Enable Screen Corner Hotarea", subtitle="Trigger overview by moving pointer to corner")
        hotarea_on.set_active(doc.get_bool("enable_hotarea", False))
        hotarea_on.connect("notify::active", lambda r, _: self._on_bool_change("enable_hotarea", r.get_active()))
        over_grp.add(hotarea_on)

        sp_w_adj = Gtk.Adjustment(value=doc.get_float("scratchpad_width_ratio", 0.8), lower=0.2, upper=1.0, step_increment=0.05)
        sp_w_row = Adw.SpinRow(title="Scratchpad Width Ratio", adjustment=sp_w_adj, digits=2)
        sp_w_row.connect("notify::value", lambda r, _: self._on_float_change("scratchpad_width_ratio", float(r.get_value())))
        over_grp.add(sp_w_row)

        sp_h_adj = Gtk.Adjustment(value=doc.get_float("scratchpad_height_ratio", 0.9), lower=0.2, upper=1.0, step_increment=0.05)
        sp_h_row = Adw.SpinRow(title="Scratchpad Height Ratio", adjustment=sp_h_adj, digits=2)
        sp_h_row.connect("notify::value", lambda r, _: self._on_float_change("scratchpad_height_ratio", float(r.get_value())))
        over_grp.add(sp_h_row)

        content.append(over_grp)

    def _on_text_change(self, key: str, value: str) -> None:
        self._doc.set_setting(key, value.strip())
        self._commit(f"update {key}")

    def _on_int_change(self, key: str, value: int) -> None:
        self._doc.set_setting(key, value)
        self._commit(f"update {key}")

    def _on_float_change(self, key: str, value: float) -> None:
        self._doc.set_setting(key, f"{value:.2f}")
        self._commit(f"update {key}")

    def _on_bool_change(self, key: str, value: bool) -> None:
        self._doc.set_setting(key, 1 if value else 0)
        self._commit(f"update {key}")
