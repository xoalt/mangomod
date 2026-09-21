"""Animations page with interactive cubic Bézier curve editor and live preview."""

from __future__ import annotations

import math
from typing import Callable

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from mangomod.pages.base import BasePage

PRESET_CURVES = {
    "Mango Default": (0.46, 1.0, 0.29, 1.0),
    "Ease": (0.25, 0.1, 0.25, 1.0),
    "Ease-In": (0.42, 0.0, 1.0, 1.0),
    "Ease-Out": (0.0, 0.0, 0.58, 1.0),
    "Ease-In-Out": (0.42, 0.0, 0.58, 1.0),
    "Linear": (0.0, 0.0, 1.0, 1.0),
    "Spring / Bounce": (0.17, 0.67, 0.83, 1.2),
}


class BezierEditor(Gtk.DrawingArea):
    """Interactive cubic Bézier curve editor with animated preview ball."""

    def __init__(self, on_changed: Callable[[float, float, float, float], None] | None = None):
        super().__init__()
        self._cp = [0.46, 1.0, 0.29, 1.0]  # x1, y1, x2, y2
        self._on_changed = on_changed
        self._dragging: int | None = None  # 0=P1, 1=P2
        self._ball_t = 0.0
        self._ball_dir = 1.0
        self._anim_id: int | None = None

        self.set_content_height(180)
        self.set_content_width(280)
        self.set_draw_func(self._draw)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        self.add_controller(motion)

        click = Gtk.GestureClick()
        click.connect("pressed", self._on_pressed)
        click.connect("released", self._on_released)
        self.add_controller(click)

        self._start_animation()

    def set_curve(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self._cp = [x1, y1, x2, y2]
        self.queue_draw()

    def get_curve(self) -> tuple[float, float, float, float]:
        return (self._cp[0], self._cp[1], self._cp[2], self._cp[3])

    def _start_animation(self) -> None:
        if self._anim_id is None:
            self._anim_id = GLib.timeout_add(16, self._on_tick)

    def _on_tick(self) -> bool:
        self._ball_t += 0.015 * self._ball_dir
        if self._ball_t >= 1.0:
            self._ball_t = 1.0
            self._ball_dir = -1.0
        elif self._ball_t <= 0.0:
            self._ball_t = 0.0
            self._ball_dir = 1.0
        self.queue_draw()
        return True

    def _eval_bezier_y(self, t: float) -> float:
        # standard 1D cubic bezier from 0 to 1
        y1, y2 = self._cp[1], self._cp[3]
        u = 1.0 - t
        return 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t

    def _draw(self, area, cr: cairo.Context, width: int, height: int) -> None:
        # Background
        cr.set_source_rgb(0.09, 0.10, 0.13)
        cr.paint()

        pad = 28.0
        grid_w = width - pad * 2
        grid_h = height - pad * 2

        # Coordinate transform: (0,0) is bottom-left, (1,1) is top-right
        def to_screen(x: float, y: float) -> tuple[float, float]:
            sx = pad + x * grid_w
            sy = height - pad - (y * grid_h)
            return sx, sy

        # Grid lines
        cr.set_source_rgba(0.25, 0.28, 0.35, 0.4)
        cr.set_line_width(1.0)
        cr.rectangle(pad, pad, grid_w, grid_h)
        cr.stroke()

        # Diagonal reference
        cr.set_source_rgba(0.3, 0.35, 0.45, 0.25)
        cr.move_to(*to_screen(0, 0))
        cr.line_to(*to_screen(1, 1))
        cr.stroke()

        p0 = to_screen(0, 0)
        p1 = to_screen(self._cp[0], self._cp[1])
        p2 = to_screen(self._cp[2], self._cp[3])
        p3 = to_screen(1, 1)

        # Control arms
        cr.set_source_rgba(0.96, 0.62, 0.07, 0.45)
        cr.set_line_width(1.2)
        cr.move_to(*p0)
        cr.line_to(*p1)
        cr.stroke()

        cr.move_to(*p3)
        cr.line_to(*p2)
        cr.stroke()

        # Bézier curve
        cr.set_source_rgba(0.98, 0.75, 0.14, 1.0)
        cr.set_line_width(2.5)
        cr.move_to(*p0)
        cr.curve_to(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
        cr.stroke()

        # Control points handles
        for pt, is_drag in [(p1, self._dragging == 0), (p2, self._dragging == 1)]:
            cr.arc(pt[0], pt[1], 6.0, 0, 2 * math.pi)
            if is_drag:
                cr.set_source_rgb(1.0, 1.0, 1.0)
            else:
                cr.set_source_rgb(0.96, 0.62, 0.07)
            cr.fill_preserve()
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.set_line_width(1.5)
            cr.stroke()

        # Preview animated ball
        by = self._eval_bezier_y(self._ball_t)
        bx, by_s = to_screen(self._ball_t, by)
        cr.arc(bx, by_s, 5.0, 0, 2 * math.pi)
        cr.set_source_rgba(0.29, 0.79, 0.98, 0.95)
        cr.fill()

    def _on_pressed(self, gesture, n_press: int, x: float, y: float) -> None:
        pad = 28.0
        grid_w = self.get_width() - pad * 2
        grid_h = self.get_height() - pad * 2

        p1_s = (pad + self._cp[0] * grid_w, self.get_height() - pad - (self._cp[1] * grid_h))
        p2_s = (pad + self._cp[2] * grid_w, self.get_height() - pad - (self._cp[3] * grid_h))

        d1 = math.hypot(x - p1_s[0], y - p1_s[1])
        d2 = math.hypot(x - p2_s[0], y - p2_s[1])

        if d1 < 16.0:
            self._dragging = 0
        elif d2 < 16.0:
            self._dragging = 1

    def _on_released(self, gesture, n_press: int, x: float, y: float) -> None:
        self._dragging = None

    def _on_motion(self, controller, x: float, y: float) -> None:
        if self._dragging is None:
            return

        pad = 28.0
        grid_w = self.get_width() - pad * 2
        grid_h = self.get_height() - pad * 2

        nx = max(0.0, min(1.0, (x - pad) / grid_w))
        ny = (self.get_height() - pad - y) / grid_h

        if self._dragging == 0:
            self._cp[0] = round(nx, 2)
            self._cp[1] = round(ny, 2)
        else:
            self._cp[2] = round(nx, 2)
            self._cp[3] = round(ny, 2)

        self.queue_draw()
        if self._on_changed:
            self._on_changed(self._cp[0], self._cp[1], self._cp[2], self._cp[3])


class AnimationsPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Animations")
        self._content = content
        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- General Toggles ---
        gen_grp = Adw.PreferencesGroup(title="Animation Configuration", description="Compositor animation state")

        anim_on = Adw.SwitchRow(title="Enable Window Animations")
        anim_on.set_active(doc.get_bool("animations", True))
        anim_on.connect("notify::active", lambda r, _: self._on_bool_change("animations", r.get_active()))
        gen_grp.add(anim_on)

        layer_anim_on = Adw.SwitchRow(title="Enable Layer Animations", subtitle="Animate rofi, fuzzel, bars, notifications")
        layer_anim_on.set_active(doc.get_bool("layer_animations", True))
        layer_anim_on.connect("notify::active", lambda r, _: self._on_bool_change("layer_animations", r.get_active()))
        gen_grp.add(layer_anim_on)

        fade_in = Adw.SwitchRow(title="Fade-In on Open")
        fade_in.set_active(doc.get_bool("animation_fade_in", True))
        fade_in.connect("notify::active", lambda r, _: self._on_bool_change("animation_fade_in", r.get_active()))
        gen_grp.add(fade_in)

        fade_out = Adw.SwitchRow(title="Fade-Out on Close")
        fade_out.set_active(doc.get_bool("animation_fade_out", True))
        fade_out.connect("notify::active", lambda r, _: self._on_bool_change("animation_fade_out", r.get_active()))
        gen_grp.add(fade_out)

        content.append(gen_grp)

        # --- Interactive Bézier Curve Editor ---
        curve_grp = Adw.PreferencesGroup(title="Cubic-Bézier Curve Editor", description="Visual timing curve with live bouncing particle")

        # Preset curves combo
        preset_row = Adw.ComboRow(title="Preset Curve")
        preset_model = Gtk.StringList.new(list(PRESET_CURVES.keys()))
        preset_row.set_model(preset_model)

        def _parse_curve_str(s: str) -> tuple[float, float, float, float]:
            parts = [float(p.strip()) for p in s.split(",") if p.strip()]
            if len(parts) == 4:
                return (parts[0], parts[1], parts[2], parts[3])
            return (0.46, 1.0, 0.29, 1.0)

        cur_curve_str = doc.get_setting("animation_curve_open", "0.46,1.0,0.29,1.0")
        c_vals = _parse_curve_str(cur_curve_str)

        editor_frame = Gtk.Frame()
        editor_frame.add_css_class("mm-canvas-frame")
        editor_frame.set_margin_top(6)
        editor_frame.set_margin_bottom(6)

        def _on_curve_modified(x1, y1, x2, y2):
            s = f"{x1:.2f},{y1:.2f},{x2:.2f},{y2:.2f}"
            self._doc.set_setting("animation_curve_open", s)
            self._doc.set_setting("animation_curve_move", s)
            self._doc.set_setting("animation_curve_tag", s)
            self._doc.set_setting("animation_curve_close", s)
            self._commit("update animation curve")

        self._bezier_editor = BezierEditor(on_changed=_on_curve_modified)
        self._bezier_editor.set_curve(*c_vals)
        editor_frame.set_child(self._bezier_editor)

        def _on_preset_selected(row, _):
            idx = row.get_selected()
            names = list(PRESET_CURVES.keys())
            if 0 <= idx < len(names):
                preset_tuple = PRESET_CURVES[names[idx]]
                self._bezier_editor.set_curve(*preset_tuple)
                _on_curve_modified(*preset_tuple)

        preset_row.connect("notify::selected", _on_preset_selected)
        curve_grp.add(preset_row)

        c_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        c_box.append(editor_frame)
        curve_grp.add(c_box)

        content.append(curve_grp)

        # --- Durations ---
        dur_grp = Adw.PreferencesGroup(title="Transition Durations (ms)", description="Fine-tune animation speeds")

        durations = [
            ("animation_duration_open", "Window Open Duration", 400),
            ("animation_duration_close", "Window Close Duration", 400),
            ("animation_duration_move", "Window Move / Tiling Duration", 500),
            ("animation_duration_tag", "Tag / Workspace Switch Duration", 350),
            ("animation_duration_focus", "Focus Switch Duration", 0),
        ]

        for key, lbl, default_ms in durations:
            adj = Gtk.Adjustment(value=doc.get_int(key, default_ms), lower=0, upper=2000, step_increment=50)
            row = Adw.SpinRow(title=lbl, adjustment=adj)
            row.connect("notify::value", lambda r, _, k=key: self._on_int_change(k, int(r.get_value())))
            dur_grp.add(row)

        content.append(dur_grp)

    def _on_int_change(self, key: str, value: int) -> None:
        self._doc.set_setting(key, value)
        self._commit(f"update {key}")

    def _on_bool_change(self, key: str, value: bool) -> None:
        self._doc.set_setting(key, 1 if value else 0)
        self._commit(f"update {key}")
