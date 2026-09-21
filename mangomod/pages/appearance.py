"""Appearance page — borders, corner radius, gaps, and window colors."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from mangomod.pages.base import BasePage


def hex_to_rgba(hex_str: str, default: tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)) -> Gdk.RGBA:
    """Parse 0xRRGGBBAA or #RRGGBB into Gdk.RGBA."""
    s = hex_str.strip().lower()
    if s.startswith("0x") and len(s) == 10:
        try:
            r = int(s[2:4], 16) / 255.0
            g = int(s[4:6], 16) / 255.0
            b = int(s[6:8], 16) / 255.0
            a = int(s[8:10], 16) / 255.0
            rgba = Gdk.RGBA()
            rgba.red, rgba.green, rgba.blue, rgba.alpha = r, g, b, a
            return rgba
        except ValueError:
            pass

    rgba = Gdk.RGBA()
    if not rgba.parse(hex_str):
        rgba.red, rgba.green, rgba.blue, rgba.alpha = default
    return rgba


def rgba_to_mango_hex(rgba: Gdk.RGBA) -> str:
    """Convert Gdk.RGBA to Mango 0xRRGGBBAA string format."""
    r = int(max(0.0, min(1.0, rgba.red)) * 255)
    g = int(max(0.0, min(1.0, rgba.green)) * 255)
    b = int(max(0.0, min(1.0, rgba.blue)) * 255)
    a = int(max(0.0, min(1.0, rgba.alpha)) * 255)
    return f"0x{r:02x}{g:02x}{b:02x}{a:02x}"


COLOR_SETTINGS = [
    ("focuscolor", "Focused Window Border", "0xc9b890ff"),
    ("bordercolor", "Unfocused Window Border", "0x444444ff"),
    ("rootcolor", "Root / Desktop Background", "0x201b14ff"),
    ("dropcolor", "Drag and Drop Target", "0x8FBA7C55"),
    ("splitcolor", "Dwindle Split Preview", "0xEB441EFF"),
    ("maximizescreencolor", "Maximized Window Border", "0x89aa61ff"),
    ("urgentcolor", "Urgent Alert Border", "0xad401fff"),
    ("scratchpadcolor", "Scratchpad Window Border", "0x516c93ff"),
    ("globalcolor", "Pinned Global Window Border", "0xb153a7ff"),
    ("overlaycolor", "Always-on-Top Overlay Border", "0x14a57cff"),
]


class AppearancePage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Appearance and Colors")
        self._content = content
        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Borders & Radius ---
        border_grp = Adw.PreferencesGroup(title="Borders and Geometry", description="Window border width and corner rounding")

        # Border width
        bpx_adj = Gtk.Adjustment(value=doc.get_int("borderpx", 3), lower=0, upper=32, step_increment=1)
        bpx_row = Adw.SpinRow(title="Border Width (px)", adjustment=bpx_adj)
        bpx_row.connect("notify::value", lambda r, _: self._on_int_change("borderpx", int(r.get_value())))
        border_grp.add(bpx_row)

        # Border radius
        rad_adj = Gtk.Adjustment(value=doc.get_int("border_radius", 4), lower=0, upper=64, step_increment=1)
        rad_row = Adw.SpinRow(title="Corner Radius (px)", adjustment=rad_adj)
        rad_row.connect("notify::value", lambda r, _: self._on_int_change("border_radius", int(r.get_value())))
        border_grp.add(rad_row)

        # No border when single
        single_b = Adw.SwitchRow(title="Hide Border When Single", subtitle="Disable border when only one window is visible on tag")
        single_b.set_active(doc.get_bool("no_border_when_single", False))
        single_b.connect("notify::active", lambda r, _: self._on_bool_change("no_border_when_single", r.get_active()))
        border_grp.add(single_b)

        # No radius when single
        single_r = Adw.SwitchRow(title="Square Corners When Single", subtitle="Disable corner radius when only one window is visible")
        single_r.set_active(doc.get_bool("no_radius_when_single", False))
        single_r.connect("notify::active", lambda r, _: self._on_bool_change("no_radius_when_single", r.get_active()))
        border_grp.add(single_r)

        content.append(border_grp)

        # --- Gaps ---
        gaps_grp = Adw.PreferencesGroup(title="Window Gaps", description="Spacing between windows and screen edges")

        gappih_adj = Gtk.Adjustment(value=doc.get_int("gappih", 4), lower=0, upper=100, step_increment=1)
        gappih_row = Adw.SpinRow(title="Inner Horizontal Gap (px)", adjustment=gappih_adj)
        gappih_row.connect("notify::value", lambda r, _: self._on_int_change("gappih", int(r.get_value())))
        gaps_grp.add(gappih_row)

        gappiv_adj = Gtk.Adjustment(value=doc.get_int("gappiv", 4), lower=0, upper=100, step_increment=1)
        gappiv_row = Adw.SpinRow(title="Inner Vertical Gap (px)", adjustment=gappiv_adj)
        gappiv_row.connect("notify::value", lambda r, _: self._on_int_change("gappiv", int(r.get_value())))
        gaps_grp.add(gappiv_row)

        gappoh_adj = Gtk.Adjustment(value=doc.get_int("gappoh", 8), lower=0, upper=100, step_increment=1)
        gappoh_row = Adw.SpinRow(title="Outer Horizontal Gap (px)", adjustment=gappoh_adj)
        gappoh_row.connect("notify::value", lambda r, _: self._on_int_change("gappoh", int(r.get_value())))
        gaps_grp.add(gappoh_row)

        gappov_adj = Gtk.Adjustment(value=doc.get_int("gappov", 8), lower=0, upper=100, step_increment=1)
        gappov_row = Adw.SpinRow(title="Outer Vertical Gap (px)", adjustment=gappov_adj)
        gappov_row.connect("notify::value", lambda r, _: self._on_int_change("gappov", int(r.get_value())))
        gaps_grp.add(gappov_row)

        smartgaps_row = Adw.SwitchRow(title="Smart Gaps", subtitle="Automatically disable gaps when only one window is tiled")
        smartgaps_row.set_active(doc.get_bool("smartgaps", False))
        smartgaps_row.connect("notify::active", lambda r, _: self._on_bool_change("smartgaps", r.get_active()))
        gaps_grp.add(smartgaps_row)

        content.append(gaps_grp)

        # --- Colors ---
        color_grp = Adw.PreferencesGroup(title="Window and Theme Colors", description="Color scheme for borders and indicators")

        for key, label, default_hex in COLOR_SETTINGS:
            cur_hex = doc.get_setting(key, default_hex)
            row = Adw.ActionRow(title=label, subtitle=cur_hex)

            # Color dialog button
            dialog = Gtk.ColorDialog(with_alpha=True)
            btn = Gtk.ColorDialogButton(dialog=dialog)
            btn.set_rgba(hex_to_rgba(cur_hex))

            def _on_color_set(button, _, k=key, r_ref=row):
                new_hex = rgba_to_mango_hex(button.get_rgba())
                self._doc.set_setting(k, new_hex)
                r_ref.set_subtitle(new_hex)
                self._commit(f"change {k}")

            btn.connect("notify::rgba", _on_color_set)
            row.add_suffix(btn)
            color_grp.add(row)

        content.append(color_grp)

    def _on_int_change(self, key: str, value: int) -> None:
        self._doc.set_setting(key, value)
        self._commit(f"update {key}")

    def _on_bool_change(self, key: str, value: bool) -> None:
        self._doc.set_setting(key, 1 if value else 0)
        self._commit(f"update {key}")
