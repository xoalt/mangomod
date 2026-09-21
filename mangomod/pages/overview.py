"""Overview dashboard — status-at-a-glance landing page for MangoMod."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod import backup, config_parser
from mangomod.pages.base import BasePage


class OverviewPage(BasePage):
    """Landing page: compositor status, config file, pending changes,
    backup count, and quick jumps. All values are live app state —
    nothing here is invented."""

    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Overview")
        self._content = content
        self._build_content()
        return tb

    def on_shown(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()

    def _build_content(self) -> None:
        state = self._win.app_state

        # --- Status card ---
        status_grp = Adw.PreferencesGroup(title="Compositor")
        if state.mango_running:
            status_row = Adw.ActionRow(
                title="Mango is running",
                subtitle=f"Version {state.mango_version}",
            )
        else:
            status_row = Adw.ActionRow(
                title="Mango is not running",
                subtitle="Changes will be saved to the config file",
            )
        reload_btn = Gtk.Button(label="Reload")
        reload_btn.add_css_class("flat")
        reload_btn.connect("clicked", lambda *_: self._win._reload_mango_compositor())
        status_row.add_suffix(reload_btn)
        status_grp.add(status_row)
        self._content.append(status_grp)

        # --- Config + changes + backups ---
        files_grp = Adw.PreferencesGroup(title="Configuration")
        n_files = len(state.source_files)
        cfg_row = Adw.ActionRow(
            title=str(config_parser.MANGO_CONFIG),
            subtitle=f"{n_files} file(s){' (multi-file setup)' if state.is_multi_file else ''}",
        )
        open_raw = Gtk.Button(label="Open Raw Editor")
        open_raw.add_css_class("flat")
        open_raw.connect("clicked", lambda *_: self._win._select_page("raw_config"))
        cfg_row.add_suffix(open_raw)
        files_grp.add(cfg_row)

        if state.is_dirty:
            ch_row = Adw.ActionRow(
                title="Unsaved changes",
                subtitle="Save to write them to disk",
            )
            save_btn = Gtk.Button(label="Save Now")
            save_btn.add_css_class("suggested-action")
            save_btn.connect("clicked", lambda *_: self._win.save_config_action())
            ch_row.add_suffix(save_btn)
        else:
            ch_row = Adw.ActionRow(
                title="All changes saved",
                subtitle="Working tree matches the file on disk",
            )
        files_grp.add(ch_row)

        try:
            n_backups = len(backup.list_backups())
        except Exception:
            n_backups = 0
        bak_row = Adw.ActionRow(
            title=f"{n_backups} snapshot(s)",
            subtitle="Automatic backups before every save",
        )
        view_bak = Gtk.Button(label="View")
        view_bak.add_css_class("flat")
        view_bak.connect("clicked", lambda *_: self._win._open_backups_dialog())
        bak_row.add_suffix(view_bak)
        files_grp.add(bak_row)
        self._content.append(files_grp)

        # --- Quick jumps ---
        quick_grp = Adw.PreferencesGroup(title="Quick Actions")
        jumps = [
            ("Key Bindings", "bindings"),
            ("Outputs &amp; Monitors", "outputs"),
            ("Command Builder", "command_builder"),
            ("All Settings", "all_settings"),
        ]
        for label_text, page_id in jumps:
            row = Adw.ActionRow(title=label_text)
            go_btn = Gtk.Button(label="Open")
            go_btn.add_css_class("flat")

            def _on_go(*_, pid=page_id):
                self._win._select_page(pid)

            go_btn.connect("clicked", _on_go)
            row.add_suffix(go_btn)
            quick_grp.add(row)
        self._content.append(quick_grp)
