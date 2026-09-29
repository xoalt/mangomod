"""Tags and Workspaces configuration page."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod import mango_ipc
from mangomod.config_parser import RuleEntry
from mangomod.pages.base import BasePage

AVAILABLE_LAYOUTS = [
    "tile",
    "scroller",
    "grid",
    "deck",
    "monocle",
    "center_tile",
    "vertical_tile",
    "vertical_scroller",
    "dwindle",
]


class TagsPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("Tags & Workspaces")
        self._content = content

        sync_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        sync_btn.set_tooltip_text("Refresh Live Tags from IPC")
        sync_btn.add_css_class("flat")
        sync_btn.connect("clicked", lambda *_: self.refresh())
        header.pack_end(sync_btn)

        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- General Tag Settings ---
        gen_grp = Adw.PreferencesGroup(title="Tag Configuration", description="dwm-style tagging system")

        tag_num_adj = Gtk.Adjustment(value=doc.get_int("tag_num", 9), lower=1, upper=32, step_increment=1)
        tag_num_row = Adw.SpinRow(title="Number of Tags", subtitle="Total tags available per monitor", adjustment=tag_num_adj)
        tag_num_row.connect("notify::value", lambda r, _: self._on_tag_num_changed(int(r.get_value())))
        gen_grp.add(tag_num_row)

        carousel_row = Adw.SwitchRow(title="Tag Carousel Loop", subtitle="Wrap around when navigating past first or last tag")
        carousel_row.set_active(doc.get_bool("tag_carousel", False))
        carousel_row.connect("notify::active", lambda r, _: self._on_bool_change("tag_carousel", r.get_active()))
        gen_grp.add(carousel_row)

        gather_row = Adw.SwitchRow(title="Tag Gather", subtitle="Gather windows when switching multi-tag views")
        gather_row.set_active(doc.get_bool("tag_gather", False))
        gather_row.connect("notify::active", lambda r, _: self._on_bool_change("tag_gather", r.get_active()))
        gen_grp.add(gather_row)

        content.append(gen_grp)

        # --- Live Tag Status (if running) ---
        live_tags = mango_ipc.get_all_tags()
        if live_tags:
            live_grp = Adw.PreferencesGroup(title="Active Monitor Tags (Live IPC)")
            for mon_tags in live_tags:
                mon_name = mon_tags.get("monitor", "Monitor")
                flow = Gtk.FlowBox()
                flow.set_valign(Gtk.Align.START)
                flow.set_max_children_per_line(9)
                flow.set_selection_mode(Gtk.SelectionMode.NONE)

                for t in mon_tags.get("tags", []):
                    idx = t.get("index", 1)
                    act = t.get("is_active", False)
                    cnt = t.get("client_count", 0)
                    lay = t.get("layout", "T")

                    pill = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                    pill.set_margin_start(4)
                    pill.set_margin_end(4)
                    pill.set_margin_top(4)
                    pill.set_margin_bottom(4)

                    btn = Gtk.Button(label=f"Tag {idx} [{lay}] ({cnt})")
                    if act:
                        btn.add_css_class("suggested-action")
                    else:
                        btn.add_css_class("flat")

                    pill.append(btn)
                    flow.append(pill)

                row = Adw.ActionRow(title=f"Monitor: {mon_name}")
                row.add_suffix(flow)
                live_grp.add(row)

            content.append(live_grp)

        # --- Per-Tag Default Layouts ---
        rules_grp = Adw.PreferencesGroup(title="Per-Tag Default Layouts", description="Set initial layout algorithm for each tag")

        tag_rules = {r.params.get("id"): r for r in doc.get_rules("tagrule")}
        tag_count = doc.get_int("tag_num", 9)

        for i in range(1, tag_count + 1):
            tag_id_str = str(i)
            rule = tag_rules.get(tag_id_str)
            cur_layout = rule.params.get("layout_name", "tile") if rule else "tile"

            row = Adw.ComboRow(title=f"Tag {i} Default Layout")
            model = Gtk.StringList.new(AVAILABLE_LAYOUTS)
            row.set_model(model)

            # Select current layout
            if cur_layout in AVAILABLE_LAYOUTS:
                row.set_selected(AVAILABLE_LAYOUTS.index(cur_layout))

            def _on_layout_selected(r, _, tid=tag_id_str):
                sel_idx = r.get_selected()
                chosen = AVAILABLE_LAYOUTS[sel_idx]
                self._update_tag_rule(tid, chosen)

            row.connect("notify::selected", _on_layout_selected)
            rules_grp.add(row)

        content.append(rules_grp)

    def _on_tag_num_changed(self, value: int) -> None:
        self._doc.set_setting("tag_num", value)
        self._commit("change tag_num")
        self.refresh()

    def _on_bool_change(self, key: str, value: bool) -> None:
        self._doc.set_setting(key, 1 if value else 0)
        self._commit(f"update {key}")

    def _update_tag_rule(self, tag_id: str, layout_name: str) -> None:
        for r in self._doc.get_rules("tagrule"):
            if r.params.get("id") == tag_id:
                r.params["layout_name"] = layout_name
                self._commit(f"update tag {tag_id} layout")
                return

        new_rule = RuleEntry(
            rule_type="tagrule",
            params={"id": tag_id, "layout_name": layout_name},
        )
        self._doc.add_rule(new_rule)
        self._commit(f"set tag {tag_id} layout")

    def refresh(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()
