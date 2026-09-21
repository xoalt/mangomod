"""Environment variables configuration page (env=KEY,VALUE)."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod.pages.base import BasePage

COMMON_ENV_PRESETS = [
    ("QT_QPA_PLATFORM", "wayland;xcb", "Force Qt to use Wayland native backend"),
    ("GDK_BACKEND", "wayland,x11", "GTK backend preference"),
    ("SDL_VIDEODRIVER", "wayland", "SDL gaming Wayland driver"),
    ("CLUTTER_BACKEND", "wayland", "Clutter Wayland backend"),
    ("XDG_CURRENT_DESKTOP", "mango", "Desktop identity for portals"),
    ("XMODIFIERS", "@im=fcitx", "Fcitx input method framework"),
]


class EnvironmentPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("Environment Variables")
        self._content = content

        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Add Environment Variable")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", lambda *_: self._open_add_dialog())
        header.pack_end(add_btn)

        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        env_grp = Adw.PreferencesGroup(
            title="Session Environment (env=KEY,VALUE)",
            description="Environment variables set before compositor and child processes launch",
        )

        entries = doc.get_env_entries()
        if entries:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for e in entries:
                row = Adw.ActionRow(title=e.key, subtitle=e.value)
                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, k=e.key: self._delete_env(k))
                row.add_suffix(del_b)
                box.append(row)
            env_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No custom environment variables defined")
            no_lbl.add_css_class("dim-label")
            env_grp.add(no_lbl)

        content.append(env_grp)

    def _delete_env(self, key: str) -> None:
        if self._doc.remove_env(key):
            self._commit(f"remove env {key}")
            self.refresh()
            self.show_toast(f"Removed env {key}")

    def refresh(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()

    def _existing_keys(self) -> set[str]:
        try:
            return {e.key for e in self._doc.get_env_entries()}
        except Exception:
            return set()

    def _open_add_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="New Environment Variable", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()

        # KEY = select-with-custom, driven by the real COMMON_ENV_PRESETS.
        known = [k for k, _, _ in COMMON_ENV_PRESETS]
        model_items = known + ["Custom…"]
        slist = Gtk.StringList.new(model_items)
        key_dd = Gtk.DropDown(model=slist)
        key_dd.set_selected(0)
        key_dd.set_hexpand(True)
        custom_key = Gtk.Entry()
        custom_key.set_placeholder_text("Type variable name…")
        custom_key.set_hexpand(True)
        custom_key.set_visible(False)

        # Conflict guard: if the chosen key is ALREADY in the doc, say so up
        # front (set_env updates in place, so we never create a duplicate — but
        # the user must KNOW they're overwriting).
        conflict_lbl = Gtk.Label(xalign=0)
        conflict_lbl.add_css_class("dim-label")

        def _current_key() -> str:
            if custom_key.get_visible():
                return custom_key.get_text().strip()
            item = key_dd.get_selected_item()
            text = item.get_string() if item is not None else ""
            return "" if text == "Custom…" else text

        def _update_conflict_lbl(*_) -> None:
            k = _current_key()
            if k and k in self._existing_keys():
                conflict_lbl.set_text(f"'{k}' is already defined — saving will overwrite it.")
            else:
                conflict_lbl.set_text("")

        def _sync_key_slots(*_) -> None:
            item = key_dd.get_selected_item()
            is_custom = item is not None and item.get_string() == "Custom…"
            custom_key.set_visible(is_custom)
            if is_custom:
                custom_key.grab_focus()
            _update_conflict_lbl()

        key_dd.connect("notify::selected", _sync_key_slots)
        custom_key.connect("changed", _update_conflict_lbl)

        key_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        key_lbl = Gtk.Label(label="Key", xalign=0)
        key_lbl.set_size_request(110, -1)
        key_row.append(key_lbl)
        key_row.append(key_dd)
        key_row.append(custom_key)
        group.add(key_row)
        group.add(conflict_lbl)

        val_entry = Adw.EntryRow(title="Variable Value")
        group.add(val_entry)

        tpl_grp = Adw.PreferencesGroup(title="Common Presets")
        for k, v, desc in COMMON_ENV_PRESETS:
            row = Adw.ActionRow(title=k, subtitle=desc)
            btn = Gtk.Button(label="Use")
            btn.add_css_class("flat")

            def _on_use(*_, var_k=k, var_v=v):
                if var_k in known:
                    key_dd.set_selected(known.index(var_k))
                else:
                    key_dd.set_selected(len(known))
                    custom_key.set_text(var_k)
                val_entry.set_text(var_v)

            btn.connect("clicked", _on_use)
            row.add_suffix(btn)
            tpl_grp.add(row)

        page.add(group)
        page.add(tpl_grp)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add")
        save_btn.add_css_class("suggested-action")

        def _on_save(*_):
            k = _current_key()
            v = val_entry.get_text().strip()
            if not k:
                self.show_toast("Enter a variable name first")
                return
            self._doc.set_env(k, v)
            self._commit(f"set env {k}")
            dialog.close()
            self.refresh()
            self.show_toast(f"Set env {k}")

        save_btn.connect("clicked", _on_save)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        _update_conflict_lbl()
        dialog.present()
