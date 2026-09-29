"""Base page class and toolbar helpers for MangoMod."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")

from gi.repository import Adw, Gio, Gtk
from mangomod.i18n import translate

if TYPE_CHECKING:
    from mangomod.config_parser import ConfigDocument
    from mangomod.window import MangoModWindow


def main_menu(language: str) -> Gio.Menu:
    label = lambda value: translate(value, language)
    menu = Gio.Menu()
    menu.append(label("Presets"), "win.open_profiles")
    menu.append(label("Backups & Snapshots"), "win.open_backups")
    menu.append(label("App Settings"), "win.open_preferences")
    menu.append(label("MangoMod Shortcuts"), "win.open_shortcuts")
    about_section = Gio.Menu()
    about_section.append(label("About MangoMod"), "win.open_about")
    menu.append_section(None, about_section)
    return menu


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

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    content.set_margin_start(32)
    content.set_margin_end(32)
    content.set_margin_top(20)
    content.set_margin_bottom(32)
    content.add_css_class("mm-page-content")
    wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    wrapper.append(content)
    clamp = Adw.Clamp(maximum_size=1080, tightening_threshold=800)
    clamp.set_child(wrapper)
    scroll.set_child(clamp)
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
        return getattr(self._win.app_state, 'settings_view', self._win.app_state.doc)

    def _commit(self, description: str = "change") -> None:
        app_state = self._win.app_state
        changed = app_state.commit(description)
        if changed:
            self._win._invalidate_other_pages()
        if app_state.is_dirty:
            self._win.mark_dirty()
        else:
            self._win.mark_clean()

    def build(self) -> Gtk.Widget:
        raise NotImplementedError

    def refresh(self) -> None:
        pass

    def dispose(self) -> None:
        """Release page-owned resources before replacing its widgets."""
        pass

    def on_shown(self) -> None:
        pass

    def show_toast(self, msg: str, timeout: int = 3) -> None:
        self._win.show_toast(msg, timeout)
