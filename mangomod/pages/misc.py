"""Compositor behavior and miscellaneous options page."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod.pages.base import BasePage


class MiscPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Behavior & Miscellaneous")
        self._content = content
        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Focus Behavior ---
        focus_grp = Adw.PreferencesGroup(title="Focus Behavior", description="Pointer and window activation handling")

        sloppy = Adw.SwitchRow(title="Focus Follows Mouse (Sloppy Focus)", subtitle="Change focus when pointer hovers over a window")
        sloppy.set_active(doc.get_bool("sloppyfocus", True))
        sloppy.connect("notify::active", lambda r, _: self._on_bool_change("sloppyfocus", r.get_active()))
        focus_grp.add(sloppy)

        foa = Adw.SwitchRow(title="Focus on Activate", subtitle="Automatically focus windows requesting activation")
        foa.set_active(doc.get_bool("focus_on_activate", True))
        foa.connect("notify::active", lambda r, _: self._on_bool_change("focus_on_activate", r.get_active()))
        focus_grp.add(foa)

        cross_mon = Adw.SwitchRow(title="Cross-Monitor Focus Navigation", subtitle="Allow directional focus to jump across monitors")
        cross_mon.set_active(doc.get_bool("focus_cross_monitor", False))
        cross_mon.connect("notify::active", lambda r, _: self._on_bool_change("focus_cross_monitor", r.get_active()))
        focus_grp.add(cross_mon)

        cross_tag = Adw.SwitchRow(title="Cross-Tag Focus Navigation", subtitle="Allow directional focus to switch tags when at edge")
        cross_tag.set_active(doc.get_bool("focus_cross_tag", False))
        cross_tag.connect("notify::active", lambda r, _: self._on_bool_change("focus_cross_tag", r.get_active()))
        focus_grp.add(cross_tag)

        content.append(focus_grp)

        # --- Window Dragging & Snapping ---
        drag_grp = Adw.PreferencesGroup(title="Dragging and Snapping", description="Window drag-to-tile and edge magnetic snap")

        drag_tile = Adw.SwitchRow(title="Drag Tile-to-Tile", subtitle="Drag a tiled window over another to swap or reorder")
        drag_tile.set_active(doc.get_bool("drag_tile_to_tile", True))
        drag_tile.connect("notify::active", lambda r, _: self._on_bool_change("drag_tile_to_tile", r.get_active()))
        drag_grp.add(drag_tile)

        snap_on = Adw.SwitchRow(title="Floating Window Magnetic Snap", subtitle="Snap floating windows to screen and window edges")
        snap_on.set_active(doc.get_bool("enable_floating_snap", False))
        snap_on.connect("notify::active", lambda r, _: self._on_bool_change("enable_floating_snap", r.get_active()))
        drag_grp.add(snap_on)

        snap_dist_adj = Gtk.Adjustment(value=doc.get_int("snap_distance", 30), lower=5, upper=100, step_increment=5)
        snap_dist_row = Adw.SpinRow(title="Snap Distance (px)", adjustment=snap_dist_adj)
        snap_dist_row.connect("notify::value", lambda r, _: self._on_int_change("snap_distance", int(r.get_value())))
        drag_grp.add(snap_dist_row)

        content.append(drag_grp)

        # --- Power & Idle Inhibit ---
        power_grp = Adw.PreferencesGroup(title="Power and Idle Inhibit", description="Screen lock and sleep prevention")

        idle_full = Adw.SwitchRow(title="Inhibit Idle When Fullscreen", subtitle="Prevent screen sleep when watching fullscreen videos")
        idle_full.set_active(doc.get_bool("idleinhibit_when_fullscreen", False))
        idle_full.connect("notify::active", lambda r, _: self._on_bool_change("idleinhibit_when_fullscreen", r.get_active()))
        power_grp.add(idle_full)

        content.append(power_grp)

        # --- Rendering & Gaming ---
        render_grp = Adw.PreferencesGroup(title="Rendering and Tearing", description="Low-latency gaming options")

        tearing_row = Adw.SwitchRow(title="Allow Screen Tearing", subtitle="Allows unconstrained FPS in games")
        tearing_row.set_active(doc.get_bool("allow_tearing", False))
        tearing_row.connect("notify::active", lambda r, _: self._on_bool_change("allow_tearing", r.get_active()))
        render_grp.add(tearing_row)

        syncobj_row = Adw.SwitchRow(title="Enable Explicit Sync (syncobj)", subtitle="Explicit synchronization for modern GPUs / Wayland")
        syncobj_row.set_active(doc.get_bool("syncobj_enable", True))
        syncobj_row.connect("notify::active", lambda r, _: self._on_bool_change("syncobj_enable", r.get_active()))
        render_grp.add(syncobj_row)

        content.append(render_grp)

    def _on_int_change(self, key: str, value: int) -> None:
        self._doc.set_setting(key, value)
        self._commit(f"update {key}")

    def _on_bool_change(self, key: str, value: bool) -> None:
        self._doc.set_setting(key, 1 if value else 0)
        self._commit(f"update {key}")
