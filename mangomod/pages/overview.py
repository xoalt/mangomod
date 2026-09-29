"""Workspace dashboard backed by the current configuration and runtime."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Pango

from mangomod import backup, config_parser
from mangomod.pages.base import BasePage


def label(text, css, wrap=False):
    widget = Gtk.Label(label=text, xalign=0, wrap=wrap)
    widget.add_css_class(css)
    return widget


class OverviewPage(BasePage):
    def build(self):
        tb, _, _, self._content = self._make_toolbar_page("Overview")
        self._build_content()
        return tb

    def on_shown(self):
        self.refresh()

    def refresh(self):
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()

    def _button(self, title, callback, css="flat"):
        button = Gtk.Button(label=title)
        button.add_css_class(css)
        button.connect("clicked", lambda *_: callback())
        return button

    def _build_content(self):
        state = self._win.app_state
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        hero.add_css_class("mm-hero")
        eyebrow = Gtk.Box(spacing=10)
        eyebrow.append(label("YOUR WORKSPACE, YOUR RULES", "mm-eyebrow"))
        hero.append(eyebrow)
        hero.append(label("Make room for your flow.", "mm-hero-title", True))
        hero.append(label("Shape how your desktop looks, moves, and feels.", "mm-hero-description", True))
        actions = Gtk.Box(spacing=10)
        actions.set_margin_top(8)
        actions.append(self._button("Customize appearance  →", lambda: self._win._select_page("appearance"), "suggested-action"))
        actions.append(self._button("Edit configuration", lambda: self._win._select_page("raw_config")))
        hero.append(actions)
        self._content.append(hero)

        status = Gtk.Box(spacing=12)
        status.add_css_class("mm-session")
        status.append(label("●", "mm-online" if state.mango_running else "dim-label"))
        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3, hexpand=True)
        details.append(label("Mango is running" if state.mango_running else "Offline editing", "mm-card-title"))
        details.append(label(f"Version {state.mango_version}" if state.mango_running else "Your changes can still be saved to the configuration.", "dim-label", True))
        status.append(details)
        if state.mango_running:
            status.append(self._button("Reload", self._win._reload_mango_compositor))
        self._content.append(status)

        self._content.append(label("THE CONTROL ROOM", "mm-eyebrow"))
        grid = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                           column_spacing=12, row_spacing=12,
                           min_children_per_line=1, max_children_per_line=3)
        destinations = [
            ("preferences-desktop-appearance-symbolic", "Look & feel", "Colors, borders, blur, and shadows", "appearance", "01"),
            ("input-keyboard-symbolic", "Keys & actions", "Shortcuts that work the way you do", "bindings", "02"),
            ("video-display-symbolic", "Your displays", "Resolution, scaling, and arrangement", "outputs", "03"),
            ("view-grid-symbolic", "Window layouts", "Give every window its own place", "layout", "04"),
            ("applications-multimedia-symbolic", "Motion", "Transitions, timing, and curves", "animations", "05"),
            ("system-run-symbolic", "Startup", "Everything ready when you arrive", "startup", "06"),
        ]
        for icon, title, description, page, number in destinations:
            button = Gtk.Button()
            button.add_css_class("mm-destination")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            top = Gtk.Box(spacing=10)
            image = Gtk.Image.new_from_icon_name(icon)
            image.set_pixel_size(22)
            image.add_css_class("mm-tile-icon")
            top.append(image)
            num = label(number, "mm-tile-number")
            num.set_hexpand(True)
            num.set_xalign(1)
            top.append(num)
            box.append(top)
            box.append(label(title + "  ↗", "mm-card-title"))
            box.append(label(description, "mm-card-description", True))
            button.set_child(box)
            button.connect("clicked", lambda *_, pid=page: self._win._select_page(pid))
            grid.insert(button, -1)
        self._content.append(grid)

        self._content.append(label("CONFIGURATION", "mm-eyebrow"))
        config = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        config.add_css_class("mm-config-card")
        top = Gtk.Box(spacing=12)
        name = label(config_parser.MANGO_CONFIG.name, "mm-card-title")
        name.set_hexpand(True)
        top.append(name)
        top.append(label("Unsaved changes" if state.is_dirty else "All changes saved", "mm-badge"))
        config.append(top)
        path = label(str(config_parser.MANGO_CONFIG), "mm-config-path")
        path.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        path.set_selectable(True)
        path.set_tooltip_text(str(config_parser.MANGO_CONFIG))
        config.append(path)
        bottom = Gtk.Box(spacing=12)
        try:
            count = len(backup.list_backups())
        except OSError:
            count = 0
        summary = label(f"{len(state.source_files)} source files  ·  {count} snapshots", "dim-label")
        summary.set_hexpand(True)
        bottom.append(summary)
        bottom.append(self._button("Snapshots", self._win._open_backups_dialog))
        bottom.append(self._button("Open editor  →", lambda: self._win._select_page("raw_config")))
        config.append(bottom)
        self._content.append(config)
