"""Cairo-drawn interactive keyboard visualizer and shortcut heat map."""

from __future__ import annotations

import math
from typing import Callable

import cairo
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk

from mangomod.xkb_helper import KEY_DISPLAY_NAMES


def normalize_key_id(key: str) -> str:
    """Normalize a key string for layout matching."""
    k = key.lower().strip()
    # strip modifiers if combined
    if "+" in k:
        k = k.split("+")[-1].strip()
    alias = {
        "return": "return",
        "enter": "return",
        "space": "space",
        "backspace": "backspace",
        "tab": "tab",
        "esc": "escape",
        "escape": "escape",
        "left": "left",
        "right": "right",
        "up": "up",
        "down": "down",
    }
    return alias.get(k, k)


# ANSI 60%/TKL row definitions: (key_id, width_units)
# 4 units = standard 1u key
KEYBOARD_LAYOUT_ANSI: list[list[tuple[str, int]]] = [
    # Function row
    [
        ("escape", 4),
        ("", 2),
        ("f1", 4),
        ("f2", 4),
        ("f3", 4),
        ("f4", 4),
        ("", 2),
        ("f5", 4),
        ("f6", 4),
        ("f7", 4),
        ("f8", 4),
        ("", 2),
        ("f9", 4),
        ("f10", 4),
        ("f11", 4),
        ("f12", 4),
        ("", 2),
        ("print", 4),
        ("delete", 4),
    ],
    # Row 1 (Numbers)
    [
        ("grave", 4),
        ("1", 4),
        ("2", 4),
        ("3", 4),
        ("4", 4),
        ("5", 4),
        ("6", 4),
        ("7", 4),
        ("8", 4),
        ("9", 4),
        ("0", 4),
        ("minus", 4),
        ("equal", 4),
        ("backspace", 8),
    ],
    # Row 2 (QWERTY)
    [
        ("tab", 6),
        ("q", 4),
        ("w", 4),
        ("e", 4),
        ("r", 4),
        ("t", 4),
        ("y", 4),
        ("u", 4),
        ("i", 4),
        ("o", 4),
        ("p", 4),
        ("bracketleft", 4),
        ("bracketright", 4),
        ("backslash", 6),
    ],
    # Row 3 (Home row)
    [
        ("capslock", 7),
        ("a", 4),
        ("s", 4),
        ("d", 4),
        ("f", 4),
        ("g", 4),
        ("h", 4),
        ("j", 4),
        ("k", 4),
        ("l", 4),
        ("semicolon", 4),
        ("quote", 4),
        ("return", 9),
    ],
    # Row 4 (Shift row)
    [
        ("shiftleft", 9),
        ("z", 4),
        ("x", 4),
        ("c", 4),
        ("v", 4),
        ("b", 4),
        ("n", 4),
        ("m", 4),
        ("comma", 4),
        ("period", 4),
        ("slash", 4),
        ("shiftright", 7),
        ("up", 4),
    ],
    # Row 5 (Bottom)
    [
        ("ctrlleft", 6),
        ("superleft", 5),
        ("altleft", 5),
        ("space", 25),
        ("altright", 5),
        ("ctrlright", 6),
        ("left", 4),
        ("down", 4),
        ("right", 4),
    ],
]


class KeyboardVisualizer(Gtk.DrawingArea):
    """Cairo drawing area rendering an interactive keyboard visualizer."""

    def __init__(self, on_key_clicked: Callable[[str], None] | None = None):
        super().__init__()
        self._on_key_clicked = on_key_clicked
        self._hover_key: str | None = None
        self._selected_key: str | None = None
        self._key_rects: dict[str, tuple[float, float, float, float]] = {}

        # active modifiers for heatmap filtering
        self.active_mods: set[str] = {"SUPER"}

        # map normalized key -> list of binding summaries
        self.bindings_by_key: dict[str, list[dict]] = {}
        # map normalized key -> count of conflicts
        self.conflicts_by_key: dict[str, int] = {}

        self.set_content_height(240)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)

        # Motion & Click controllers
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        motion.connect("leave", self._on_leave)
        self.add_controller(motion)

        click = Gtk.GestureClick()
        click.connect("pressed", self._on_pressed)
        self.add_controller(click)

    def set_bindings_data(self, bindings: list[dict], conflicts: set[str] | None = None) -> None:
        """Update active bindings and conflict data for visualization."""
        self.bindings_by_key.clear()
        self.conflicts_by_key.clear()
        conflicts = conflicts or set()

        for b in bindings:
            k = normalize_key_id(b.get("key", ""))
            if not k:
                continue
            if k not in self.bindings_by_key:
                self.bindings_by_key[k] = []
            self.bindings_by_key[k].append(b)

            if k in conflicts or b.get("is_conflict", False):
                self.conflicts_by_key[k] = self.conflicts_by_key.get(k, 0) + 1

        self.queue_draw()

    def set_active_mods(self, mods: set[str]) -> None:
        """Filter visualizer by currently checked modifiers."""
        self.active_mods = set(m.upper() for m in mods)
        self.queue_draw()

    def select_key(self, key_name: str | None) -> None:
        self._selected_key = normalize_key_id(key_name) if key_name else None
        self.queue_draw()

    def _matches_active_mods(self, bind_mods_str: str) -> bool:
        """Check if binding modifiers match the currently selected filter."""
        bm_set = set(bind_mods_str.replace("+", " ").replace("-", " ").upper().split())
        if not bm_set or bm_set == {"NONE"}:
            return not self.active_mods or self.active_mods == {"NONE"}
        return bm_set == self.active_mods

    def _draw(self, area, cr: cairo.Context, width: int, height: int) -> None:
        # Background
        cr.set_source_rgba(0.08, 0.09, 0.11, 1.0)
        cr.paint()

        padding = 12.0
        avail_w = width - padding * 2
        avail_h = height - padding * 2
        if avail_w <= 0 or avail_h <= 0:
            return

        layout = KEYBOARD_LAYOUT_ANSI
        num_rows = len(layout)
        gap = 4.0

        # Calculate max units in any row (Row 1 has 60 units)
        max_row_units = 60.0
        unit_w = (avail_w - (15 * gap)) / max_row_units
        unit_w = max(4.0, min(unit_w, 14.0))

        row_h = (avail_h - (num_rows * gap)) / num_rows
        row_h = max(20.0, min(row_h, 36.0))

        self._key_rects.clear()

        y = padding
        for row in layout:
            x = padding
            for key_id, units in row:
                if not key_id:  # Spacer
                    x += units * unit_w + gap
                    continue

                w = units * unit_w
                h = row_h

                self._key_rects[key_id] = (x, y, w, h)
                self._draw_key(cr, key_id, x, y, w, h)

                x += w + gap
            y += row_h + gap

    def _draw_key(self, cr: cairo.Context, key_id: str, x: float, y: float, w: float, h: float) -> None:
        radius = 4.0
        # Determine status
        binds = self.bindings_by_key.get(key_id, [])
        matching_binds = [b for b in binds if self._matches_active_mods(b.get("modifiers", ""))]
        is_bound = len(matching_binds) > 0
        has_conflict = self.conflicts_by_key.get(key_id, 0) > 0
        is_hover = (self._hover_key == key_id)
        is_selected = (self._selected_key == key_id)

        # Rounded rectangle path
        cr.new_sub_path()
        cr.arc(x + w - radius, y + radius, radius, -math.pi / 2, 0)
        cr.arc(x + w - radius, y + h - radius, radius, 0, math.pi / 2)
        cr.arc(x + radius, y + h - radius, radius, math.pi / 2, math.pi)
        cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        cr.close_path()

        # Key Base Fill Color
        if is_selected:
            cr.set_source_rgba(0.96, 0.62, 0.07, 0.40)  # Golden accent
        elif has_conflict:
            cr.set_source_rgba(0.94, 0.27, 0.27, 0.35)  # Danger / conflict
        elif is_bound:
            cr.set_source_rgba(0.96, 0.62, 0.07, 0.25)  # Mango bound highlight
        elif is_hover:
            cr.set_source_rgba(0.22, 0.24, 0.30, 1.0)
        else:
            cr.set_source_rgba(0.14, 0.15, 0.19, 1.0)
        cr.fill_preserve()

        # Border
        if is_selected:
            cr.set_source_rgba(0.98, 0.75, 0.14, 1.0)
            cr.set_line_width(1.8)
        elif has_conflict:
            cr.set_source_rgba(0.94, 0.27, 0.27, 0.9)
            cr.set_line_width(1.5)
        elif is_bound:
            cr.set_source_rgba(0.96, 0.62, 0.07, 0.8)
            cr.set_line_width(1.2)
        elif is_hover:
            cr.set_source_rgba(0.40, 0.44, 0.52, 1.0)
            cr.set_line_width(1.0)
        else:
            cr.set_source_rgba(0.24, 0.26, 0.32, 0.6)
            cr.set_line_width(0.8)
        cr.stroke()

        # Key Text Label
        label = KEY_DISPLAY_NAMES.get(key_id, key_id.upper() if len(key_id) <= 2 else key_id.capitalize())
        if len(label) > 8:
            label = label[:7] + "."

        font_size = 9.0 if len(label) > 3 or w < 30 else 11.0
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_bound else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(font_size)

        extents = cr.text_extents(label)
        tx = x + (w - extents.width) / 2.0 - extents.x_bearing
        ty = y + (h - extents.height) / 2.0 - extents.y_bearing

        if is_bound or is_selected:
            cr.set_source_rgba(1.0, 0.95, 0.85, 1.0)
        elif is_hover:
            cr.set_source_rgba(0.95, 0.95, 0.95, 1.0)
        else:
            cr.set_source_rgba(0.65, 0.68, 0.75, 1.0)
        cr.move_to(tx, ty)
        cr.show_text(label)

        # Draw a little dot if bound
        if is_bound and not has_conflict:
            cr.arc(x + w - 5.0, y + 5.0, 2.0, 0, 2 * math.pi)
            cr.set_source_rgba(0.96, 0.62, 0.07, 1.0)
            cr.fill()

    def _key_at_point(self, px: float, py: float) -> str | None:
        for k_id, (kx, ky, kw, kh) in self._key_rects.items():
            if kx <= px <= kx + kw and ky <= py <= ky + kh:
                return k_id
        return None

    def _on_motion(self, controller, x: float, y: float) -> None:
        key = self._key_at_point(x, y)
        if key != self._hover_key:
            self._hover_key = key
            self.queue_draw()

    def _on_leave(self, controller) -> None:
        if self._hover_key is not None:
            self._hover_key = None
            self.queue_draw()

    def _on_pressed(self, gesture, n_press: int, x: float, y: float) -> None:
        key = self._key_at_point(x, y)
        if key:
            self._selected_key = key
            self.queue_draw()
            if self._on_key_clicked:
                self._on_key_clicked(key)
