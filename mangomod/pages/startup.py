"""Startup and autostart commands management page (exec-once and exec)."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from mangomod.config_parser import ExecEntry
from mangomod.pages.base import BasePage

COMMON_AUTOSTART_TEMPLATES = [
    ("Status Bar (Waybar)", "waybar"),
    ("Wallpaper (swaybg)", "swaybg -i ~/.config/mango/wallpaper.png"),
    ("Notification Daemon (dunst)", "dunst"),
    ("Polkit Agent (gnome)", "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1"),
    ("XDG Desktop Portal DBus Init", "dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP"),
    ("Clipboard Manager (wl-paste)", "wl-paste --watch cliphist store"),
]


class StartupPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("Startup & Autostart")
        self._content = content

        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Add Autostart Command")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", lambda *_: self._open_add_dialog())
        header.pack_end(add_btn)

        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Exec-Once ---
        once_grp = Adw.PreferencesGroup(
            title="Launch on Startup (exec-once)",
            description="Commands that run once when Mango compositor starts up",
        )

        entries = doc.get_exec_entries()
        once_entries = [e for e in entries if e.is_once]

        if once_entries:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for e in once_entries:
                row = Adw.ActionRow()
                tag = Gtk.Label()
                tag.set_markup("<b>ONCE</b>")
                tag.add_css_class("mm-badge")
                row.add_prefix(tag)

                row.set_title(GLib.markup_escape_text(e.command))
                if e.inline_comment:
                    row.set_subtitle(GLib.markup_escape_text(f"# {e.inline_comment}"))

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, item=e: self._delete_exec(item))
                row.add_suffix(del_b)
                box.append(row)
            once_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No startup commands configured")
            no_lbl.add_css_class("dim-label")
            once_grp.add(no_lbl)

        content.append(once_grp)

        # --- Exec (Every Reload) ---
        exec_grp = Adw.PreferencesGroup(
            title="Launch on Every Reload (exec)",
            description="Commands executed whenever configuration is reloaded",
        )

        reload_entries = [e for e in entries if not e.is_once]
        if reload_entries:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for e in reload_entries:
                row = Adw.ActionRow()
                tag = Gtk.Label()
                tag.set_markup("<b>RELOAD</b>")
                tag.add_css_class("mm-badge")
                row.add_prefix(tag)

                row.set_title(GLib.markup_escape_text(e.command))
                if e.inline_comment:
                    row.set_subtitle(GLib.markup_escape_text(f"# {e.inline_comment}"))

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, item=e: self._delete_exec(item))
                row.add_suffix(del_b)
                box.append(row)
            exec_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No reload commands configured")
            no_lbl.add_css_class("dim-label")
            exec_grp.add(no_lbl)

        content.append(exec_grp)

    def _delete_exec(self, entry: ExecEntry) -> None:
        if entry in self._doc.entries:
            self._doc.entries.remove(entry)
            self._commit("remove autostart command")
            self.refresh()
            self.show_toast("Removed autostart command")

    def refresh(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()

    def _open_add_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Add Autostart Command", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Command Setup")

        cmd_entry = Adw.EntryRow(title="Command to Execute")
        group.add(cmd_entry)

        once_sw = Adw.SwitchRow(title="Run Once at Startup (exec-once)")
        once_sw.set_active(True)
        group.add(once_sw)

        # Quick templates
        tpl_group = Adw.PreferencesGroup(title="Quick Templates")
        for title, cmd_tmpl in COMMON_AUTOSTART_TEMPLATES:
            row = Adw.ActionRow(title=title, subtitle=cmd_tmpl)
            use_btn = Gtk.Button(label="Use")
            use_btn.add_css_class("flat")

            def _on_use(*_, c=cmd_tmpl):
                cmd_entry.set_text(c)

            use_btn.connect("clicked", _on_use)
            row.add_suffix(use_btn)
            tpl_group.add(row)

        page.add(group)
        page.add(tpl_group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add")
        save_btn.add_css_class("suggested-action")

        def _on_add(*_):
            c = cmd_entry.get_text().strip()
            if not c:
                return
            is_once = once_sw.get_active()
            self._doc.add_exec(is_once=is_once, command=c)
            self._commit(f"add autostart {'exec-once' if is_once else 'exec'}")
            dialog.close()
            self.refresh()
            self.show_toast(f"Added {'exec-once' if is_once else 'exec'} command")

        save_btn.connect("clicked", _on_add)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        dialog.present()
