"""Base page class and toolbar helpers for MangoMod."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")

from gi.repository import Adw, Gio, Gtk

if TYPE_CHECKING:
    from mangomod.config_parser import ConfigDocument
    from mangomod.window import MangoModWindow


def make_toolbar_page(
    title: str,
    window: "MangoModWindow | None" = None,
) -> tuple[Adw.ToolbarView, Adw.HeaderBar, Gtk.ScrolledWindow, Gtk.Box]:
    """Create a standardized toolbar page with title, action menu, and scrollable content."""
    tb = Adw.ToolbarView()
    header = Adw.HeaderBar()
    title_widget = Adw.WindowTitle(title=title)
    header.set_title_widget(title_widget)
    tb.add_top_bar(header)

    if window is not None:
        menu = Gio.Menu()
        menu.append("Profiles", "win.open_profiles")
        menu.append("Backups & Snapshots", "win.open_backups")
        menu.append("Preferences", "win.open_preferences")
        menu.append("Keyboard Shortcuts", "win.open_shortcuts")

        about_section = Gio.Menu()
        about_section.append("About MangoMod", "win.open_about")
        menu.append_section(None, about_section)

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_btn.set_tooltip_text("Main Menu")
        menu_btn.add_css_class("flat")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    content.set_margin_start(32)
    content.set_margin_end(32)
    content.set_margin_top(20)
    content.set_margin_bottom(32)
    scroll.set_child(content)
    tb.set_content(scroll)

    return tb, header, scroll, content


class BasePage:
    def __init__(self, window: "MangoModWindow"):
        self._win = window

    def _make_toolbar_page(
        self, title: str
    ) -> tuple[Adw.ToolbarView, Adw.HeaderBar, Gtk.ScrolledWindow, Gtk.Box]:
        return make_toolbar_page(title, window=self._win)

    @property
    def _doc(self) -> "ConfigDocument":
        return self._win.app_state.doc

    def _commit(self, description: str = "change") -> None:
        app_state = self._win.app_state
        after = app_state.doc.serialize()
        before = app_state.undo.last_snapshot
        if before is None:
            before = app_state.saved_text

        if before != after:
            self._win.push_undo(description, before, after)

        if after == app_state.saved_text:
            self._win.mark_clean()
        else:
            self._win.mark_dirty()

    def build(self) -> Gtk.Widget:
        raise NotImplementedError

    def refresh(self) -> None:
        pass

    def on_shown(self) -> None:
        pass

    def show_toast(self, msg: str, timeout: int = 3) -> None:
        self._win.show_toast(msg, timeout)
