"""Outputs / Monitors configuration page with interactive 2D canvas."""

from __future__ import annotations

import math
from typing import Any

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from mangomod import mango_ipc
from mangomod.config_parser import RuleEntry
from mangomod.pages.base import BasePage

ROTATION_NAMES = ["0° (Normal)", "90° (Counter-clockwise)", "180° (Upside down)", "270° (Clockwise)"]


class OutputsPage(BasePage):
    def __init__(self, window):
        super().__init__(window)
        self._monitors: list[dict[str, Any]] = []
        self._selected_idx: int = 0
        self._canvas: Gtk.DrawingArea | None = None
        self._drag_idx: int | None = None
        self._drag_start_pos: tuple[float, float] = (0, 0)
        self._monitor_rects: list[tuple[float, float, float, float]] = []

    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("Outputs & Displays")
        self._content = content

        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Add Display Output")
        add_btn.add_css_class("flat")
        add_btn.connect("clicked", lambda *_: self._add_monitor())
        header.pack_end(add_btn)

        reload_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        reload_btn.set_tooltip_text("Detect Connected Displays (IPC)")
        reload_btn.add_css_class("flat")
        reload_btn.connect("clicked", lambda *_: self._detect_connected_displays())
        header.pack_end(reload_btn)

        # 2D Interactive Canvas Frame
        canvas_frame = Gtk.Frame()
        canvas_frame.add_css_class("mm-canvas-frame")
        canvas_frame.set_margin_bottom(12)

        self._canvas = Gtk.DrawingArea()
        self._canvas.set_content_height(280)
        self._canvas.set_draw_func(self._draw_canvas)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        drag.connect("drag-end", self._on_drag_end)
        self._canvas.add_controller(drag)

        click = Gtk.GestureClick()
        click.connect("pressed", self._on_canvas_click)
        self._canvas.add_controller(click)

        canvas_frame.set_child(self._canvas)
        content.append(canvas_frame)

        # Settings below canvas
        self._settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.append(self._settings_box)

        self._load_monitors_from_doc()
        self._build_monitor_controls()
        return tb

    def _load_monitors_from_doc(self) -> None:
        self._monitors.clear()
        rules = self._doc.get_rules("monitorrule")
        for r in rules:
            p = r.params
            name = p.get("name", "HDMI-A-1")
            width = int(p.get("width", 1920))
            height = int(p.get("height", 1080))
            refresh = float(p.get("refresh", 60.0))
            x = int(p.get("x", 0))
            y = int(p.get("y", 0))
            scale = float(p.get("scale", 1.0))
            vrr = int(p.get("vrr", 0))
            hdr = int(p.get("hdr", 0))
            rr = int(p.get("rr", 0))
            disable = int(p.get("disable", 0))
            icc = p.get("icc", "")

            self._monitors.append({
                "rule": r,
                "name": name,
                "width": width,
                "height": height,
                "refresh": refresh,
                "x": x,
                "y": y,
                "scale": scale,
                "vrr": vrr,
                "hdr": hdr,
                "rr": rr,
                "disable": disable,
                "icc": icc,
            })

        if not self._monitors:
            # Fallback to detecting from IPC or default
            self._detect_connected_displays(commit=False)

        if not self._monitors:
            self._monitors.append({
                "rule": None,
                "name": "HDMI-A-1",
                "width": 2560,
                "height": 1080,
                "refresh": 60.0,
                "x": 0,
                "y": 0,
                "scale": 1.0,
                "vrr": 0,
                "hdr": 0,
                "rr": 0,
                "disable": 0,
                "icc": "",
            })

    def _detect_connected_displays(self, commit: bool = True) -> None:
        live = mango_ipc.get_all_monitors()
        if not live:
            if commit:
                self.show_toast("No monitors reported by IPC (is Mango running?)")
            return

        new_monitors = []
        for m in live:
            name = m.get("name", "Unknown")
            w = m.get("width", 1920)
            h = m.get("height", 1080)
            x = m.get("x", 0)
            y = m.get("y", 0)
            scale = m.get("scale", 1.0)
            vrr = 1 if m.get("is_vrr", False) else 0
            hdr = 1 if m.get("is_hdr", False) else 0

            # Find matching rule in doc
            matched_rule = None
            for r in self._doc.get_rules("monitorrule"):
                if r.params.get("name") == name:
                    matched_rule = r
                    break

            new_monitors.append({
                "rule": matched_rule,
                "name": name,
                "width": w,
                "height": h,
                "refresh": 60.0,
                "x": x,
                "y": y,
                "scale": scale,
                "vrr": vrr,
                "hdr": hdr,
                "rr": 0,
                "disable": 0,
                "icc": "",
            })

        self._monitors = new_monitors
        self._selected_idx = 0
        if commit:
            self._sync_monitors_to_doc()
            self.show_toast(f"Detected {len(new_monitors)} display output(s)")
        self._refresh_ui()

    def _sync_monitors_to_doc(self) -> None:
        # Remove old monitorrule entries
        for r in self._doc.get_rules("monitorrule"):
            self._doc.remove_rule(r)

        for m in self._monitors:
            params = {
                "name": m["name"],
                "width": str(m["width"]),
                "height": str(m["height"]),
                "refresh": f"{m['refresh']:.1f}",
                "x": str(m["x"]),
                "y": str(m["y"]),
                "scale": str(m["scale"]),
            }
            if m["vrr"]:
                params["vrr"] = "1"
            if m["hdr"]:
                params["hdr"] = "1"
            if m["rr"]:
                params["rr"] = str(m["rr"])
            if m["disable"]:
                params["disable"] = "1"
            if m["icc"]:
                params["icc"] = m["icc"]

            rule = RuleEntry(rule_type="monitorrule", params=params)
            m["rule"] = rule
            self._doc.add_rule(rule)

        self._commit("update monitors")

    def _draw_canvas(self, area, cr: cairo.Context, width: int, height: int) -> None:
        # Background
        cr.set_source_rgb(0.06, 0.07, 0.09)
        cr.paint()

        if not self._monitors:
            return

        # Calculate bounding box of all monitors
        min_x = min(m["x"] for m in self._monitors)
        min_y = min(m["y"] for m in self._monitors)
        max_x = max(m["x"] + m["width"] for m in self._monitors)
        max_y = max(m["y"] + m["height"] for m in self._monitors)

        span_w = max(1, max_x - min_x)
        span_h = max(1, max_y - min_y)

        pad = 32.0
        avail_w = width - pad * 2
        avail_h = height - pad * 2

        scale_factor = min(avail_w / span_w, avail_h / span_h) * 0.85
        scale_factor = max(0.04, min(scale_factor, 0.25))

        center_offset_x = (width - (span_w * scale_factor)) / 2.0 - (min_x * scale_factor)
        center_offset_y = (height - (span_h * scale_factor)) / 2.0 - (min_y * scale_factor)

        self._monitor_rects = []

        for idx, m in enumerate(self._monitors):
            mw = m["width"] * scale_factor
            mh = m["height"] * scale_factor
            mx = center_offset_x + (m["x"] * scale_factor)
            my = center_offset_y + (m["y"] * scale_factor)

            self._monitor_rects.append((mx, my, mw, mh))

            is_sel = (idx == self._selected_idx)
            is_dis = bool(m.get("disable", 0))

            # Rounded rect
            rad = 6.0
            cr.new_sub_path()
            cr.arc(mx + mw - rad, my + rad, rad, -math.pi / 2, 0)
            cr.arc(mx + mw - rad, my + mh - rad, rad, 0, math.pi / 2)
            cr.arc(mx + rad, my + mh - rad, rad, math.pi / 2, math.pi)
            cr.arc(mx + rad, my + rad, rad, math.pi, 3 * math.pi / 2)
            cr.close_path()

            if is_dis:
                cr.set_source_rgba(0.12, 0.13, 0.16, 0.7)
            elif is_sel:
                cr.set_source_rgba(0.96, 0.62, 0.07, 0.22)
            else:
                cr.set_source_rgba(0.16, 0.18, 0.23, 0.9)
            cr.fill_preserve()

            # Border
            if is_sel:
                cr.set_source_rgba(0.98, 0.75, 0.14, 1.0)
                cr.set_line_width(2.0)
            else:
                cr.set_source_rgba(0.35, 0.38, 0.46, 0.7)
                cr.set_line_width(1.0)
            cr.stroke()

            # Text
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_sel else cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(12.0)
            title = m["name"]
            res = f"{m['width']}x{m['height']} @ {m['refresh']:.0f}Hz"
            pos = f"({m['x']}, {m['y']})"

            cr.set_source_rgb(1.0, 0.95, 0.85) if is_sel else cr.set_source_rgb(0.75, 0.78, 0.85)

            ext_t = cr.text_extents(title)
            cr.move_to(mx + (mw - ext_t.width) / 2.0, my + mh / 2.0 - 6.0)
            cr.show_text(title)

            cr.set_font_size(9.5)
            ext_r = cr.text_extents(res)
            cr.move_to(mx + (mw - ext_r.width) / 2.0, my + mh / 2.0 + 10.0)
            cr.show_text(res)

            cr.set_font_size(8.5)
            cr.set_source_rgba(0.6, 0.63, 0.7, 0.8)
            ext_p = cr.text_extents(pos)
            cr.move_to(mx + (mw - ext_p.width) / 2.0, my + mh / 2.0 + 24.0)
            cr.show_text(pos)

    def _on_canvas_click(self, gesture, n_press: int, x: float, y: float) -> None:
        for idx, (rx, ry, rw, rh) in enumerate(self._monitor_rects):
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self._selected_idx = idx
                self._refresh_ui()
                return

    def _on_drag_begin(self, gesture, start_x: float, start_y: float) -> None:
        self._drag_idx = None
        for idx, (rx, ry, rw, rh) in enumerate(self._monitor_rects):
            if rx <= start_x <= rx + rw and ry <= start_y <= ry + rh:
                self._drag_idx = idx
                self._selected_idx = idx
                self._drag_start_pos = (self._monitors[idx]["x"], self._monitors[idx]["y"])
                self._refresh_ui()
                return

    def _on_drag_update(self, gesture, offset_x: float, offset_y: float) -> None:
        if self._drag_idx is None:
            return
        m = self._monitors[self._drag_idx]
        # approx scale inverse
        m["x"] = int(self._drag_start_pos[0] + offset_x * 8)
        m["y"] = int(self._drag_start_pos[1] + offset_y * 8)
        if self._canvas:
            self._canvas.queue_draw()

    def _on_drag_end(self, gesture, offset_x: float, offset_y: float) -> None:
        if self._drag_idx is not None:
            self._sync_monitors_to_doc()
            self._drag_idx = None
            self._refresh_ui()

    def _build_monitor_controls(self) -> None:
        while child := self._settings_box.get_first_child():
            self._settings_box.remove(child)

        if not self._monitors:
            return

        idx = min(self._selected_idx, len(self._monitors) - 1)
        cur = self._monitors[idx]

        grp = Adw.PreferencesGroup(title=f"Monitor: {cur['name']}")

        # Resolution & Position
        name_entry = Adw.EntryRow(title="Display Output Name")
        name_entry.set_text(cur["name"])
        name_entry.connect("notify::text", lambda r, _: self._update_cur("name", r.get_text()))
        grp.add(name_entry)

        w_adj = Gtk.Adjustment(value=cur["width"], lower=640, upper=7680, step_increment=100)
        w_row = Adw.SpinRow(title="Resolution Width (px)", adjustment=w_adj)
        w_row.connect("notify::value", lambda r, _: self._update_cur("width", int(r.get_value())))
        grp.add(w_row)

        h_adj = Gtk.Adjustment(value=cur["height"], lower=480, upper=4320, step_increment=100)
        h_row = Adw.SpinRow(title="Resolution Height (px)", adjustment=h_adj)
        h_row.connect("notify::value", lambda r, _: self._update_cur("height", int(r.get_value())))
        grp.add(h_row)

        hz_adj = Gtk.Adjustment(value=cur["refresh"], lower=24.0, upper=360.0, step_increment=1.0)
        hz_row = Adw.SpinRow(title="Refresh Rate (Hz)", adjustment=hz_adj, digits=1)
        hz_row.connect("notify::value", lambda r, _: self._update_cur("refresh", float(r.get_value())))
        grp.add(hz_row)

        x_adj = Gtk.Adjustment(value=cur["x"], lower=-10000, upper=100000, step_increment=50)
        x_row = Adw.SpinRow(title="Position X (px)", adjustment=x_adj)
        x_row.connect("notify::value", lambda r, _: self._update_cur("x", int(r.get_value())))
        grp.add(x_row)

        y_adj = Gtk.Adjustment(value=cur["y"], lower=-10000, upper=100000, step_increment=50)
        y_row = Adw.SpinRow(title="Position Y (px)", adjustment=y_adj)
        y_row.connect("notify::value", lambda r, _: self._update_cur("y", int(r.get_value())))
        grp.add(y_row)

        scale_adj = Gtk.Adjustment(value=cur["scale"], lower=0.5, upper=4.0, step_increment=0.1)
        scale_row = Adw.SpinRow(title="Scale Factor", adjustment=scale_adj, digits=2)
        scale_row.connect("notify::value", lambda r, _: self._update_cur("scale", float(r.get_value())))
        grp.add(scale_row)

        # VRR & HDR
        vrr_row = Adw.SwitchRow(title="Variable Refresh Rate (VRR / G-Sync)")
        vrr_row.set_active(bool(cur["vrr"]))
        vrr_row.connect("notify::active", lambda r, _: self._update_cur("vrr", 1 if r.get_active() else 0))
        grp.add(vrr_row)

        hdr_row = Adw.SwitchRow(title="HDR Support")
        hdr_row.set_active(bool(cur["hdr"]))
        hdr_row.connect("notify::active", lambda r, _: self._update_cur("hdr", 1 if r.get_active() else 0))
        grp.add(hdr_row)

        dis_row = Adw.SwitchRow(title="Disable Display")
        dis_row.set_active(bool(cur["disable"]))
        dis_row.connect("notify::active", lambda r, _: self._update_cur("disable", 1 if r.get_active() else 0))
        grp.add(dis_row)

        # Delete Display
        del_btn = Gtk.Button(label="Remove Display Configuration")
        del_btn.add_css_class("destructive-action")
        del_btn.set_margin_top(8)
        del_btn.connect("clicked", lambda *_: self._delete_current_monitor())
        grp.add(del_btn)

        self._settings_box.append(grp)

    def _update_cur(self, key: str, val: Any) -> None:
        idx = min(self._selected_idx, len(self._monitors) - 1)
        self._monitors[idx][key] = val
        self._sync_monitors_to_doc()
        if self._canvas:
            self._canvas.queue_draw()

    def _delete_current_monitor(self) -> None:
        if len(self._monitors) <= 1:
            self.show_toast("Cannot remove the only display")
            return
        self._monitors.pop(self._selected_idx)
        self._selected_idx = max(0, self._selected_idx - 1)
        self._sync_monitors_to_doc()
        self._refresh_ui()

    def _add_monitor(self) -> None:
        next_id = len(self._monitors) + 1
        new_m = {
            "rule": None,
            "name": f"DP-{next_id}",
            "width": 1920,
            "height": 1080,
            "refresh": 60.0,
            "x": self._monitors[-1]["x"] + self._monitors[-1]["width"] if self._monitors else 0,
            "y": 0,
            "scale": 1.0,
            "vrr": 0,
            "hdr": 0,
            "rr": 0,
            "disable": 0,
            "icc": "",
        }
        self._monitors.append(new_m)
        self._selected_idx = len(self._monitors) - 1
        self._sync_monitors_to_doc()
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        if self._canvas:
            self._canvas.queue_draw()
        self._build_monitor_controls()
