"""Mouse, gestures, axis scrolling, and lid switch bindings page."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod.config_parser import (
    AxisBindingEntry,
    GestureBindingEntry,
    MouseBindingEntry,
    SwitchBindingEntry,
)
from mangomod.pages.base import BasePage
from mangomod.xkb_helper import format_modifiers


class MouseGesturesPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Mouse & Gestures")
        self._content = content
        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Mouse Button Bindings ---
        mouse_grp = Adw.PreferencesGroup(
            title="Mouse Button Bindings",
            description="Assign window movement and actions to mouse clicks",
        )
        add_mouse_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_mouse_btn.add_css_class("flat")
        add_mouse_btn.connect("clicked", lambda *_: self._open_add_mousebind_dialog())
        mouse_grp.set_header_suffix(add_mouse_btn)

        mouse_binds = doc.get_mouse_bindings()
        if mouse_binds:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for mb in mouse_binds:
                row = Adw.ActionRow()
                badge = Gtk.Label()
                mods = format_modifiers(mb.modifiers)
                combo = f"{mods} + {mb.button}" if mods else mb.button
                badge.set_markup(f"<b>{combo}</b>")
                badge.add_css_class("mm-key-badge")
                row.add_prefix(badge)

                row.set_title(f"{mb.command} {mb.args}".strip())

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, b=mb: self._delete_entry(b, "mouse binding"))
                row.add_suffix(del_b)
                box.append(row)
            mouse_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No custom mouse button bindings")
            no_lbl.add_css_class("dim-label")
            mouse_grp.add(no_lbl)

        content.append(mouse_grp)

        # --- Axis Bindings (Scroll Wheel) ---
        axis_grp = Adw.PreferencesGroup(
            title="Axis Bindings (Scroll Wheel)",
            description="Map scroll wheel movements with modifiers",
        )
        add_axis_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_axis_btn.add_css_class("flat")
        add_axis_btn.connect("clicked", lambda *_: self._open_add_axisbind_dialog())
        axis_grp.set_header_suffix(add_axis_btn)

        axis_binds = doc.get_axis_bindings()
        if axis_binds:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for ab in axis_binds:
                row = Adw.ActionRow()
                badge = Gtk.Label()
                mods = format_modifiers(ab.modifiers)
                combo = f"{mods} + Scroll {ab.direction}" if mods else f"Scroll {ab.direction}"
                badge.set_markup(f"<b>{combo}</b>")
                badge.add_css_class("mm-key-badge")
                row.add_prefix(badge)

                row.set_title(f"{ab.command} {ab.args}".strip())

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, b=ab: self._delete_entry(b, "axis binding"))
                row.add_suffix(del_b)
                box.append(row)
            axis_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No axis bindings configured")
            no_lbl.add_css_class("dim-label")
            axis_grp.add(no_lbl)

        content.append(axis_grp)

        # --- Touchpad Gestures ---
        gesture_grp = Adw.PreferencesGroup(
            title="Trackpad Gestures",
            description="Multi-finger swipe gestures for workspace and window navigation",
        )

        gesture_live_row = Adw.SwitchRow(
            title="Live Gesture Previews",
            subtitle="Show interactive animated transition while dragging gestures",
        )
        gesture_live_row.set_active(doc.get_bool("gesture_live", True))
        gesture_live_row.connect("notify::active", lambda r, _: self._on_live_gesture_changed(r.get_active()))
        gesture_grp.add(gesture_live_row)

        add_gest_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_gest_btn.add_css_class("flat")
        add_gest_btn.connect("clicked", lambda *_: self._open_add_gesture_dialog())
        gesture_grp.set_header_suffix(add_gest_btn)

        gest_binds = doc.get_gesture_bindings()
        if gest_binds:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for gb in gest_binds:
                row = Adw.ActionRow()
                badge = Gtk.Label()
                mods = format_modifiers(gb.modifiers)
                combo = f"{gb.fingers}-finger swipe {gb.direction}"
                if mods:
                    combo = f"{mods} + {combo}"
                badge.set_markup(f"<b>{combo}</b>")
                badge.add_css_class("mm-key-badge")
                row.add_prefix(badge)

                row.set_title(f"{gb.command} {gb.args}".strip())

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, b=gb: self._delete_entry(b, "gesture binding"))
                row.add_suffix(del_b)
                box.append(row)
            gesture_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No custom gestures configured")
            no_lbl.add_css_class("dim-label")
            gesture_grp.add(no_lbl)

        content.append(gesture_grp)

        # --- Switch Bindings (Laptop Lid) ---
        switch_grp = Adw.PreferencesGroup(
            title="Laptop Lid Switches",
            description="Actions triggered upon closing or opening laptop lid",
        )
        add_switch_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_switch_btn.add_css_class("flat")
        add_switch_btn.connect("clicked", lambda *_: self._open_add_switch_dialog())
        switch_grp.set_header_suffix(add_switch_btn)

        sw_binds = doc.get_switch_bindings()
        if sw_binds:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for sb in sw_binds:
                row = Adw.ActionRow()
                badge = Gtk.Label()
                lbl = "Lid Close (fold)" if sb.fold == "fold" else "Lid Open (unfold)"
                badge.set_markup(f"<b>{lbl}</b>")
                badge.add_css_class("mm-key-badge")
                row.add_prefix(badge)

                row.set_title(f"{sb.command} {sb.args}".strip())

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")
                del_b.connect("clicked", lambda *_, b=sb: self._delete_entry(b, "switch binding"))
                row.add_suffix(del_b)
                box.append(row)
            switch_grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No lid switch actions configured")
            no_lbl.add_css_class("dim-label")
            switch_grp.add(no_lbl)

        content.append(switch_grp)

    def _on_live_gesture_changed(self, active: bool) -> None:
        self._doc.set_setting("gesture_live", 1 if active else 0)
        self._commit("toggle gesture_live")

    def _delete_entry(self, entry, name: str) -> None:
        if entry in self._doc.entries:
            self._doc.entries.remove(entry)
            self._commit(f"delete {name}")
            self.refresh()
            self.show_toast(f"Removed {name}")

    def refresh(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()

    def _open_add_mousebind_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Add Mouse Binding", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()

        mod_entry = Adw.EntryRow(title="Modifier (SUPER, ALT, CTRL, NONE)")
        mod_entry.set_text("SUPER")
        group.add(mod_entry)

        btn_entry = Adw.EntryRow(title="Button (btn_left, btn_right, btn_middle, etc.)")
        btn_entry.set_text("btn_left")
        group.add(btn_entry)

        cmd_entry = Adw.EntryRow(title="Command (e.g. moveresize, killclient)")
        cmd_entry.set_text("moveresize")
        group.add(cmd_entry)

        arg_entry = Adw.EntryRow(title="Arguments (e.g. curmove, curresize)")
        arg_entry.set_text("curmove")
        group.add(arg_entry)

        page.add(group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add")
        save_btn.add_css_class("suggested-action")

        def _on_add(*_):
            m = mod_entry.get_text().strip() or "NONE"
            b = btn_entry.get_text().strip()
            c = cmd_entry.get_text().strip()
            a = arg_entry.get_text().strip()
            if not b or not c:
                return
            self._doc.entries.append(MouseBindingEntry(modifiers=m, button=b, command=c, args=a))
            self._commit("add mouse binding")
            dialog.close()
            self.refresh()

        save_btn.connect("clicked", _on_add)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        dialog.present()

    def _open_add_axisbind_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Add Axis Binding", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()

        mod_entry = Adw.EntryRow(title="Modifier (SUPER, ALT, CTRL, NONE)")
        mod_entry.set_text("SUPER")
        group.add(mod_entry)

        dir_entry = Adw.EntryRow(title="Direction (UP, DOWN, LEFT, RIGHT)")
        dir_entry.set_text("UP")
        group.add(dir_entry)

        cmd_entry = Adw.EntryRow(title="Command (e.g. viewtoleft_have_client)")
        cmd_entry.set_text("viewtoleft_have_client")
        group.add(cmd_entry)

        page.add(group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add")
        save_btn.add_css_class("suggested-action")

        def _on_add(*_):
            m = mod_entry.get_text().strip() or "NONE"
            d = dir_entry.get_text().strip().upper()
            c = cmd_entry.get_text().strip()
            if not d or not c:
                return
            self._doc.entries.append(AxisBindingEntry(modifiers=m, direction=d, command=c))
            self._commit("add axis binding")
            dialog.close()
            self.refresh()

        save_btn.connect("clicked", _on_add)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        dialog.present()

    def _open_add_gesture_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Add Gesture Binding", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()

        mod_entry = Adw.EntryRow(title="Modifier (none, super, alt, etc.)")
        mod_entry.set_text("none")
        group.add(mod_entry)

        dir_entry = Adw.EntryRow(title="Direction (left, right, up, down)")
        dir_entry.set_text("left")
        group.add(dir_entry)

        fingers_adj = Gtk.Adjustment(value=3, lower=3, upper=4, step_increment=1)
        fingers_row = Adw.SpinRow(title="Fingers Count (3 or 4)", adjustment=fingers_adj)
        group.add(fingers_row)

        cmd_entry = Adw.EntryRow(title="Command (e.g. focusdir, viewnext_have_client, toggleoverview)")
        cmd_entry.set_text("focusdir")
        group.add(cmd_entry)

        arg_entry = Adw.EntryRow(title="Arguments (e.g. left, right, up, down)")
        arg_entry.set_text("left")
        group.add(arg_entry)

        page.add(group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add")
        save_btn.add_css_class("suggested-action")

        def _on_add(*_):
            m = mod_entry.get_text().strip() or "none"
            d = dir_entry.get_text().strip()
            f = int(fingers_row.get_value())
            c = cmd_entry.get_text().strip()
            a = arg_entry.get_text().strip()
            if not d or not c:
                return
            self._doc.entries.append(GestureBindingEntry(modifiers=m, direction=d, fingers=f, command=c, args=a))
            self._commit("add gesture binding")
            dialog.close()
            self.refresh()

        save_btn.connect("clicked", _on_add)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        dialog.present()

    def _open_add_switch_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Add Lid Switch Action", transient_for=self._win, modal=True)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()

        fold_entry = Adw.EntryRow(title="State (fold or unfold)")
        fold_entry.set_text("fold")
        group.add(fold_entry)

        cmd_entry = Adw.EntryRow(title="Command (e.g. spawn)")
        cmd_entry.set_text("spawn")
        group.add(cmd_entry)

        arg_entry = Adw.EntryRow(title="Arguments / Shell Command")
        arg_entry.set_text("swaylock -f -c 000000")
        group.add(arg_entry)

        page.add(group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add")
        save_btn.add_css_class("suggested-action")

        def _on_add(*_):
            fl = fold_entry.get_text().strip()
            c = cmd_entry.get_text().strip()
            a = arg_entry.get_text().strip()
            if not fl or not c:
                return
            self._doc.entries.append(SwitchBindingEntry(fold=fl, command=c, args=a))
            self._commit("add switch binding")
            dialog.close()
            self.refresh()

        save_btn.connect("clicked", _on_add)
        header.pack_end(save_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(page)
        dialog.set_content(box)
        dialog.present()
