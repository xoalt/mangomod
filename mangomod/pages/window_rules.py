"""Window and layer rules configuration page."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod.config_parser import RuleEntry
from mangomod.pages.base import BasePage


class WindowRulesPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("Window & Layer Rules")
        self._content = content

        add_win_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_win_btn.set_tooltip_text("Add Window Rule")
        add_win_btn.add_css_class("suggested-action")
        add_win_btn.connect("clicked", lambda *_: self._open_window_rule_dialog())
        header.pack_end(add_win_btn)

        add_layer_btn = Gtk.Button(label="+ Layer Rule")
        add_layer_btn.add_css_class("flat")
        add_layer_btn.connect("clicked", lambda *_: self._open_layer_rule_dialog())
        header.pack_end(add_layer_btn)

        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Window Rules ---
        win_grp = Adw.PreferencesGroup(
            title="Window Rules",
            description="Match windows by app-id or title to apply behavior and visual rules",
        )

        win_rules = doc.get_rules("windowrule") + doc.get_rules("windowrule-once")
        if win_rules:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for r in win_rules:
                row = Adw.ActionRow()

                is_once = r.rule_type == "windowrule-once"
                tag_badge = Gtk.Label()
                tag_badge.set_markup(f"<b>{'ONCE' if is_once else 'RULE'}</b>")
                tag_badge.add_css_class("mm-badge")
                row.add_prefix(tag_badge)

                appid = r.params.get("appid", "*")
                title = r.params.get("title", "*")
                row.set_title(f"App: {appid}  |  Title: {title}")

                # Subtitle listing other properties
                other_props = [f"{k}={v}" for k, v in r.params.items() if k not in ("appid", "title")]
                row.set_subtitle(", ".join(other_props) if other_props else "Default attributes")

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, rule=r: self._delete_rule(rule))
                row.add_suffix(del_b)
                box.append(row)
            win_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No window rules configured")
            no_lbl.add_css_class("dim-label")
            win_grp.add(no_lbl)

        content.append(win_grp)

        # --- Layer Shell Rules ---
        layer_grp = Adw.PreferencesGroup(
            title="Layer Shell Rules",
            description="Animation and effects rules for overlay shells (fuzzel, rofi, waybar, etc.)",
        )

        layer_rules = doc.get_rules("layerrule")
        if layer_rules:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for lr in layer_rules:
                row = Adw.ActionRow()
                layer_name = lr.params.get("layer_name", "unknown")
                row.set_title(f"Layer: {layer_name}")

                props = [f"{k}={v}" for k, v in lr.params.items() if k != "layer_name"]
                row.set_subtitle(", ".join(props) if props else "Default layer properties")

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, rule=lr: self._delete_rule(rule))
                row.add_suffix(del_b)
                box.append(row)
            layer_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No layer rules configured")
            no_lbl.add_css_class("dim-label")
            layer_grp.add(no_lbl)

        content.append(layer_grp)

    def _delete_rule(self, rule: RuleEntry) -> None:
        if self._doc.remove_rule(rule):
            self._commit("delete rule")
            self.refresh()
            self.show_toast("Deleted rule")

    def refresh(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()

    def _open_window_rule_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="New Window Rule", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Window Matching")

        appid_entry = Adw.EntryRow(title="Application ID (regex, e.g. firefox, foot)")
        group.add(appid_entry)

        title_entry = Adw.EntryRow(title="Window Title (regex, optional)")
        group.add(title_entry)

        once_sw = Adw.SwitchRow(title="Apply Once Only (windowrule-once)")
        group.add(once_sw)

        float_sw = Adw.SwitchRow(title="Force Floating State")
        group.add(float_sw)

        full_sw = Adw.SwitchRow(title="Force Fullscreen")
        group.add(full_sw)

        global_sw = Adw.SwitchRow(title="Sticky / Pinned Across Tags (isglobal)")
        group.add(global_sw)

        overlay_sw = Adw.SwitchRow(title="Always On Top (isoverlay)")
        group.add(overlay_sw)

        silent_sw = Adw.SwitchRow(title="Open Silently Without Stealing Focus")
        group.add(silent_sw)

        page.add(group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add Rule")
        save_btn.add_css_class("suggested-action")

        def _on_save(*_):
            aid = appid_entry.get_text().strip()
            tit = title_entry.get_text().strip()
            if not aid and not tit:
                self.show_toast("Provide an App ID or Window Title")
                return

            params = {}
            if aid:
                params["appid"] = aid
            if tit:
                params["title"] = tit

            if float_sw.get_active():
                params["isfloating"] = "1"
            if full_sw.get_active():
                params["isfullscreen"] = "1"
            if global_sw.get_active():
                params["isglobal"] = "1"
            if overlay_sw.get_active():
                params["isoverlay"] = "1"
            if silent_sw.get_active():
                params["isopensilent"] = "1"

            rtype = "windowrule-once" if once_sw.get_active() else "windowrule"
            rule = RuleEntry(rule_type=rtype, params=params)
            self._doc.add_rule(rule)
            self._commit("add window rule")
            dialog.close()
            self.refresh()
            self.show_toast(f"Added window rule for {aid or tit}")

        save_btn.connect("clicked", _on_save)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        dialog.present()

    def _open_layer_rule_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="New Layer Shell Rule", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Layer Properties")

        name_entry = Adw.EntryRow(title="Layer Name (e.g. rofi, fuzzel, waybar)")
        group.add(name_entry)

        open_anim_entry = Adw.EntryRow(title="Open Animation (e.g. zoom, slide)")
        open_anim_entry.set_text("zoom")
        group.add(open_anim_entry)

        close_anim_entry = Adw.EntryRow(title="Close Animation (e.g. zoom, slide)")
        close_anim_entry.set_text("zoom")
        group.add(close_anim_entry)

        page.add(group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add Layer Rule")
        save_btn.add_css_class("suggested-action")

        def _on_save(*_):
            name = name_entry.get_text().strip()
            if not name:
                return
            params = {"layer_name": name}
            if open_anim_entry.get_text().strip():
                params["animation_type_open"] = open_anim_entry.get_text().strip()
            if close_anim_entry.get_text().strip():
                params["animation_type_close"] = close_anim_entry.get_text().strip()

            rule = RuleEntry(rule_type="layerrule", params=params)
            self._doc.add_rule(rule)
            self._commit("add layer rule")
            dialog.close()
            self.refresh()
            self.show_toast(f"Added layer rule for {name}")

        save_btn.connect("clicked", _on_save)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        dialog.present()
