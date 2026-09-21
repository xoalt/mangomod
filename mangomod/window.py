"""Main application window — sidebar + content NavigationSplitView."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from mangomod import app_settings, backup, config_parser, mango_ipc, profiles
from mangomod import __version__
from mangomod.pages.all_settings import AllSettingsPage
from mangomod.pages.animations import AnimationsPage
from mangomod.pages.appearance import AppearancePage
from mangomod.pages.bindings import BindingsPage
from mangomod.pages.command_builder import CommandBuilderPage
from mangomod.pages.environment import EnvironmentPage
from mangomod.pages.input_page import InputPage
from mangomod.pages.layout import LayoutPage
from mangomod.pages.misc import MiscPage
from mangomod.pages.mouse_gestures import MouseGesturesPage
from mangomod.pages.outputs import OutputsPage
from mangomod.pages.overview import OverviewPage
from mangomod.pages.raw_config import RawConfigPage
from mangomod.pages.startup import StartupPage
from mangomod.pages.tags import TagsPage
from mangomod.pages.window_effects import WindowEffectsPage
from mangomod.pages.window_rules import WindowRulesPage
from mangomod.state import AppState
from mangomod.theme import CSS

SIDEBAR_GROUPS = [
    (
        "Home",
        [
            ("overview", "go-home-symbolic", "Overview"),
        ],
    ),
    (
        "Input",
        [
            ("input", "input-keyboard-symbolic", "Input Devices"),
            ("bindings", "preferences-desktop-keyboard-shortcuts-symbolic", "Key Bindings"),
            ("mouse_gestures", "input-mouse-symbolic", "Mouse & Gestures"),
            ("command_builder", "applications-graphics-symbolic", "Command Builder"),
        ],
    ),
    (
        "Display",
        [
            ("outputs", "video-display-symbolic", "Outputs & Monitors"),
            ("appearance", "preferences-desktop-appearance-symbolic", "Appearance & Colors"),
            ("window_effects", "view-reveal-symbolic", "Window Effects"),
            ("animations", "applications-multimedia-symbolic", "Animations"),
        ],
    ),
    (
        "Workspace",
        [
            ("layout", "view-grid-symbolic", "Layout Settings"),
            ("tags", "view-paged-symbolic", "Tags & Workspaces"),
            ("window_rules", "preferences-system-symbolic", "Window Rules"),
        ],
    ),
    (
        "System",
        [
            ("startup", "system-run-symbolic", "Startup & Autostart"),
            ("environment", "preferences-other-symbolic", "Environment"),
            ("misc", "preferences-desktop-apps-symbolic", "Behavior & Misc"),
        ],
    ),
    (
        "Advanced",
        [
            ("raw_config", "text-x-generic-symbolic", "Raw Config"),
            ("all_settings", "preferences-system-symbolic", "All Settings"),
        ],
    ),
]

SIDEBAR_PAGES = [entry for _, group in SIDEBAR_GROUPS for entry in group]


class MangoModWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("MangoMod")
        self.set_default_size(1080, 750)

        self.app_state = AppState()
        self.app_state.load()

        self._current_page_id = ""
        self._pages: dict[str, Gtk.Widget] = {}
        self._page_instances: dict[str, Any] = {}
        self._sidebar_rows: dict[str, Gtk.ListBoxRow] = {}
        self._sidebar_listboxes: dict[str, Gtk.ListBox] = {}
        self._sidebar_expanders: dict[str, Gtk.Expander] = {}

        self._load_css()
        self._build_ui()
        self._setup_actions()
        self._setup_shortcuts()

        # Select first page
        if SIDEBAR_PAGES:
            self._select_page(SIDEBAR_PAGES[0][0])

    def _load_css(self) -> None:
        self._css_providers: list = []
        self._apply_theme(
            app_settings.get("theme", "mango-dark"),
            app_settings.get("color_scheme", "dark"),
        )

    def _apply_theme(self, theme_id: str, scheme: str) -> None:
        """Apply a color scheme + theme CSS. User themes layer over Mango Dark."""
        from mangomod import theme as mm_theme

        style_mgr = Adw.StyleManager.get_default()
        style_mgr.set_color_scheme(
            {
                "light": Adw.ColorScheme.FORCE_LIGHT,
                "dark": Adw.ColorScheme.FORCE_DARK,
            }.get(scheme, Adw.ColorScheme.DEFAULT)
        )

        display = Gdk.Display.get_default()
        for old in self._css_providers:
            if display is not None:
                Gtk.StyleContext.remove_provider_for_display(display, old)
        self._css_providers = []

        base_id = theme_id if not theme_id.startswith("user:") else "mango-dark"
        css_text, _err = mm_theme.load_theme_css(base_id)
        layers = [css_text] if css_text else []
        if theme_id.startswith("user:"):
            overlay, err = mm_theme.load_theme_css(theme_id)
            if overlay is not None:
                layers.append(overlay)
            elif hasattr(self, "_toast_overlay"):
                self.show_toast(f"Theme error: {err} — using Mango Dark")

        for layer in layers:
            provider = Gtk.CssProvider()
            provider.load_from_data(layer.encode("utf-8"))
            if display is not None:
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )
            self._css_providers.append(provider)

    def _build_ui(self) -> None:
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._toast_overlay.set_child(root_box)

        # Status Banner (proper Adw.Banner widget, not a hand-rolled box)
        self._banner = Adw.Banner()
        self._banner.set_button_label("Reload Mango")
        self._banner.connect("button-clicked", lambda *_: self._reload_mango_compositor())
        self._banner.set_revealed(True)

        root_box.append(self._banner)
        self._update_banner()

        # Navigation Split View
        self._split_view = Adw.NavigationSplitView()
        self._split_view.set_vexpand(True)
        root_box.append(self._split_view)

        self._split_view.set_sidebar(self._build_sidebar_nav())
        self._split_view.set_content(self._build_content_nav())

    def _update_banner(self) -> None:
        if self.app_state.mango_running:
            self._banner.remove_css_class("mm-banner-stopped")
            self._banner.add_css_class("mm-banner-running")
            self._banner.set_title(
                f"Mango Compositor: Running (version {self.app_state.mango_version})"
            )
            self._banner.set_button_label("Reload Mango")
        else:
            self._banner.remove_css_class("mm-banner-running")
            self._banner.add_css_class("mm-banner-stopped")
            self._banner.set_title(
                "Mango is not running — changes will be saved to config file"
            )
            self._banner.set_button_label("")

    def _build_sidebar_nav(self) -> Adw.NavigationPage:
        nav = Adw.NavigationPage(title="Navigation")
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.add_css_class("mm-sidebar-bg")

        header = Adw.HeaderBar()
        title_w = Adw.WindowTitle(title="MangoMod", subtitle="Mango WM Configurator")
        header.set_title_widget(title_w)

        sidebar_box.append(header)

        # Search bar
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search settings…")
        self._search_entry.add_css_class("mm-search-entry")
        self._search_entry.set_margin_start(10)
        self._search_entry.set_margin_end(10)
        self._search_entry.set_margin_top(8)
        self._search_entry.set_margin_bottom(6)
        self._search_entry.connect("search-changed", self._on_sidebar_search)
        sidebar_box.append(self._search_entry)

        # Scrolled content with collapsible groups
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)

        list_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        list_container.set_margin_bottom(12)

        for group_title, pages in SIDEBAR_GROUPS:
            expander = Gtk.Expander()
            expander.set_expanded(True)
            sec_lbl = Gtk.Label(label=group_title, xalign=0)
            sec_lbl.add_css_class("mm-sidebar-section-label")
            expander.set_label_widget(sec_lbl)
            self._sidebar_expanders[group_title] = expander

            listbox = Gtk.ListBox()
            listbox.add_css_class("mm-sidebar-listbox")
            listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
            listbox.connect("row-selected", self._on_sidebar_row_selected)
            self._sidebar_listboxes[group_title] = listbox

            for page_id, icon_name, label_text in pages:
                row = Gtk.ListBoxRow()
                row._page_id = page_id
                row._search_text = f"{group_title} {label_text}".lower()

                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                icon = Gtk.Image.new_from_icon_name(icon_name)
                icon.set_pixel_size(20)
                icon.set_valign(Gtk.Align.CENTER)
                text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
                lbl = Gtk.Label(label=label_text, xalign=0)
                lbl.set_hexpand(True)
                sub = Gtk.Label(label=group_title, xalign=0)
                sub.add_css_class("dim-label")
                text_box.append(lbl)
                text_box.append(sub)

                row_box.append(icon)
                row_box.append(text_box)
                row.set_child(row_box)

                listbox.append(row)
                self._sidebar_rows[page_id] = row

            expander.set_child(listbox)
            list_container.append(expander)

        scroller.set_child(list_container)
        sidebar_box.append(scroller)

        # Bottom action bar: Save + Undo/Redo (previously header-only Save,
        # undo/redo had no visible buttons at all)
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_bar.set_margin_start(10)
        action_bar.set_margin_end(10)
        action_bar.set_margin_top(6)
        action_bar.set_margin_bottom(10)

        self._save_btn = Gtk.Button(label="Save")
        self._save_btn.add_css_class("suggested-action")
        self._save_btn.set_hexpand(True)
        self._save_btn.connect("clicked", lambda *_: self.save_config_action())
        action_bar.append(self._save_btn)

        self._undo_btn = Gtk.Button(icon_name="edit-undo-symbolic")
        self._undo_btn.set_tooltip_text("Undo (Ctrl+Z)")
        self._undo_btn.add_css_class("flat")
        self._undo_btn.connect("clicked", lambda *_: self._action_undo())
        action_bar.append(self._undo_btn)

        self._redo_btn = Gtk.Button(icon_name="edit-redo-symbolic")
        self._redo_btn.set_tooltip_text("Redo (Ctrl+Shift+Z)")
        self._redo_btn.add_css_class("flat")
        self._redo_btn.connect("clicked", lambda *_: self._action_redo())
        action_bar.append(self._redo_btn)

        sidebar_box.append(action_bar)
        self._refresh_action_buttons()
        nav.set_child(sidebar_box)
        return nav

    def _refresh_action_buttons(self) -> None:
        undo = self.app_state.undo
        if hasattr(self, "_undo_btn"):
            self._undo_btn.set_sensitive(undo.can_undo())
            self._redo_btn.set_sensitive(undo.can_redo())

    def _build_content_nav(self) -> Adw.NavigationPage:
        self._content_nav = Adw.NavigationPage(title="Settings")
        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._content_stack.set_transition_duration(150)
        self._content_nav.set_child(self._content_stack)
        return self._content_nav

    def _get_or_create_page(self, page_id: str) -> Gtk.Widget:
        if page_id in self._pages:
            return self._pages[page_id]

        page_classes = {
            "overview": OverviewPage,
            "input": InputPage,
            "bindings": BindingsPage,
            "mouse_gestures": MouseGesturesPage,
            "command_builder": CommandBuilderPage,
            "outputs": OutputsPage,
            "appearance": AppearancePage,
            "window_effects": WindowEffectsPage,
            "animations": AnimationsPage,
            "layout": LayoutPage,
            "tags": TagsPage,
            "window_rules": WindowRulesPage,
            "startup": StartupPage,
            "environment": EnvironmentPage,
            "misc": MiscPage,
            "raw_config": RawConfigPage,
            "all_settings": AllSettingsPage,
        }

        cls = page_classes.get(page_id)
        if cls:
            instance = cls(self)
            self._page_instances[page_id] = instance
            widget = instance.build()
            self._pages[page_id] = widget
            self._content_stack.add_named(widget, page_id)
            return widget

        placeholder = Gtk.Label(label=f"Page {page_id} not implemented")
        self._pages[page_id] = placeholder
        self._content_stack.add_named(placeholder, page_id)
        return placeholder

    def _select_page(self, page_id: str) -> None:
        self._current_page_id = page_id
        self._get_or_create_page(page_id)
        self._content_stack.set_visible_child_name(page_id)

        # Notify page
        inst = self._page_instances.get(page_id)
        if inst and hasattr(inst, "on_shown"):
            inst.on_shown()

        # Update sidebar selection
        target_row = self._sidebar_rows.get(page_id)
        if target_row:
            for lb in self._sidebar_listboxes.values():
                if target_row.get_parent() == lb:
                    lb.select_row(target_row)
                else:
                    lb.unselect_all()

    def _on_sidebar_row_selected(self, listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if row and hasattr(row, "_page_id"):
            page_id = row._page_id
            if page_id != self._current_page_id:
                # Unselect other listboxes
                for lb in self._sidebar_listboxes.values():
                    if lb != listbox:
                        lb.unselect_all()
                self._select_page(page_id)

    def _on_sidebar_search(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text().strip().lower()
        first_match = None
        for page_id, row in self._sidebar_rows.items():
            matches = not query or (query in row._search_text) or (query in page_id)
            row.set_visible(matches)
            if matches and first_match is None:
                first_match = page_id

        # Collapse groups with zero matches; auto-expand groups with hits.
        for group_title, lb in self._sidebar_listboxes.items():
            any_visible = any(
                r.get_visible() for r in self._sidebar_rows.values()
                if r.get_parent() == lb
            )
            expander = self._sidebar_expanders.get(group_title)
            if expander is not None:
                expander.set_visible(any_visible or not query)
                if query and any_visible:
                    expander.set_expanded(True)

        if query and first_match:
            self._select_page(first_match)

    def show_toast(self, message: str, timeout: int = 3) -> None:
        # Adw.Toast parses its title as markup: a bare & (e.g. "saved &
        # reloaded") aborts the whole toast with a GTK warning. Escape once,
        # here, so no caller ever has to think about it.
        toast = Adw.Toast.new(message.replace("&", "&amp;"))
        toast.set_timeout(timeout)
        self._toast_overlay.add_toast(toast)

    def mark_dirty(self) -> None:
        self.app_state.mark_dirty()
        self._save_btn.set_label("● Save *")
        self._refresh_action_buttons()

    def mark_clean(self) -> None:
        self.app_state.mark_clean()
        self._save_btn.set_label("Save")
        self._refresh_action_buttons()

    def push_undo(self, description: str, before: str, after: str) -> None:
        self.app_state.push_undo(description, before, after)
        self.mark_dirty()

    def save_config_action(self) -> None:
        ok, msg = self.app_state.save()
        if ok:
            self.mark_clean()
            self.show_toast(msg)
        elif msg.startswith("Validation error:"):
            self._offer_force_save(msg)
        else:
            self.show_toast(f"Save Failed: {msg}", timeout=5)

    def _offer_force_save(self, validation_msg: str) -> None:
        """Validation failed but the file may still run (mango tolerates
        unknown keywords at startup while -p rejects them). Let the user
        read the plain-text error and choose — never silently force."""
        dialog = Adw.MessageDialog.new(
            self,
            "Validation Failed",
            f"{validation_msg}\n\nMango may still run this file. Save anyway?",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("force", "Save Anyway")
        dialog.set_response_appearance("force", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        def _on_response(_dlg, response: str) -> None:
            if response != "force":
                return
            fok, fmsg = self.app_state.save(skip_validation=True)
            if fok:
                self.mark_clean()
                self.show_toast(f"Saved without validation: {fmsg}")
            else:
                self.show_toast(f"Save Failed: {fmsg}", timeout=5)

        dialog.connect("response", _on_response)
        dialog.present()

    def switch_main_config(self, path) -> None:
        """Promote a file to the main config (runs it, and only it, when it
        has no includes). Refuses when unsaved changes exist — a disk reload
        would silently wipe them."""
        from pathlib import Path

        target = Path(path).expanduser()
        if self._resolve_same_file(target, config_parser.MANGO_CONFIG):
            self.show_toast("That is already the main file")
            return
        # Mango itself only loads a main file literally named config.conf —
        # anything else would silently never run.
        if target.name != "config.conf":
            self.show_toast("Main file must be named config.conf — mango won't load anything else")
            return
        if self.app_state.is_dirty:
            self.show_toast("Save or Revert first — switching reloads from disk")
            return
        if not target.is_file():
            self.show_toast("That file does not exist")
            return
        try:
            config_parser.set_paths(config_path=str(target))
        except OSError as exc:
            self.show_toast(f"Cannot switch config: {exc}")
            return
        app_settings.set("config_path", str(target))
        self.app_state.load()
        for inst in self._page_instances.values():
            if hasattr(inst, "refresh"):
                try:
                    inst.refresh()
                except Exception as exc:  # noqa: BLE001 — one bad page must not block the switch
                    self.show_toast(f"Refresh notice ({type(inst).__name__}): {exc}")
        self.show_toast(f"Main config is now {target.name}")

    @staticmethod
    def _resolve_same_file(a, b) -> bool:
        try:
            return Path(a).resolve() == Path(b).resolve()
        except OSError:
            return Path(a) == Path(b)

    def _reload_mango_compositor(self) -> None:
        ok, msg = mango_ipc.reload_config()
        if ok:
            self.show_toast("Mango compositor reloaded!")
        else:
            self.show_toast(f"Reload failed: {msg}")

    # --- Actions & Dialogs ---

    def _setup_actions(self) -> None:
        action_save = Gio.SimpleAction.new("save", None)
        action_save.connect("activate", lambda *_: self.save_config_action())
        self.add_action(action_save)

        action_undo = Gio.SimpleAction.new("undo", None)
        action_undo.connect("activate", lambda *_: self._action_undo())
        self.add_action(action_undo)

        action_redo = Gio.SimpleAction.new("redo", None)
        action_redo.connect("activate", lambda *_: self._action_redo())
        self.add_action(action_redo)

        action_profiles = Gio.SimpleAction.new("open_profiles", None)
        action_profiles.connect("activate", lambda *_: self._open_profiles_dialog())
        self.add_action(action_profiles)

        action_backups = Gio.SimpleAction.new("open_backups", None)
        action_backups.connect("activate", lambda *_: self._open_backups_dialog())
        self.add_action(action_backups)

        action_prefs = Gio.SimpleAction.new("open_preferences", None)
        action_prefs.connect("activate", lambda *_: self._open_preferences_dialog())
        self.add_action(action_prefs)

        action_shortcuts = Gio.SimpleAction.new("open_shortcuts", None)
        action_shortcuts.connect("activate", lambda *_: self._open_shortcuts_dialog())
        self.add_action(action_shortcuts)

        action_about = Gio.SimpleAction.new("open_about", None)
        action_about.connect("activate", lambda *_: self._open_about_dialog())
        self.add_action(action_about)

    def _setup_shortcuts(self) -> None:
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(controller)

    def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        if ctrl and keyval in (Gdk.KEY_s, Gdk.KEY_S):
            self.save_config_action()
            return True
        elif ctrl and not shift and keyval in (Gdk.KEY_z, Gdk.KEY_Z):
            self._action_undo()
            return True
        elif (ctrl and shift and keyval in (Gdk.KEY_z, Gdk.KEY_Z)) or (ctrl and keyval in (Gdk.KEY_y, Gdk.KEY_Y)):
            self._action_redo()
            return True
        elif ctrl and keyval in (Gdk.KEY_r, Gdk.KEY_R):
            self._reload_mango_compositor()
            return True
        elif ctrl and keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self._search_entry.grab_focus()
            return True
        return False

    def _action_undo(self) -> None:
        entry = self.app_state.undo.pop_undo()
        if entry:
            self.app_state.doc = config_parser.parse_config_text(entry.snapshot_before, config_parser.MANGO_CONFIG)
            self._refresh_current_page()
            self.show_toast(f"Undo: {entry.description}")
        self._refresh_action_buttons()

    def _action_redo(self) -> None:
        entry = self.app_state.undo.pop_redo()
        if entry:
            self.app_state.doc = config_parser.parse_config_text(entry.snapshot_after, config_parser.MANGO_CONFIG)
            self._refresh_current_page()
            self.show_toast(f"Redo: {entry.description}")
        self._refresh_action_buttons()

    def _refresh_current_page(self) -> None:
        inst = self._page_instances.get(self._current_page_id)
        if inst and hasattr(inst, "refresh"):
            inst.refresh()

    def _open_profiles_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Profiles", transient_for=self, modal=True)
        dialog.set_default_size(440, 400)
        page = Adw.PreferencesPage()

        # Save profile row
        grp_save = Adw.PreferencesGroup(title="Save Current Setup as Profile")
        name_entry = Adw.EntryRow(title="Profile Name")
        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")

        def _on_save_prof(*_):
            n = name_entry.get_text().strip()
            if n:
                profiles.save_profile(n, self.app_state.source_files)
                dialog.close()
                self.show_toast(f"Saved profile '{n}'")

        save_btn.connect("clicked", _on_save_prof)
        name_entry.add_suffix(save_btn)
        grp_save.add(name_entry)
        page.add(grp_save)

        # Saved profiles list
        grp_list = Adw.PreferencesGroup(title="Existing Profiles")
        profs = profiles.list_profiles()
        if profs:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for p_name in profs:
                row = Adw.ActionRow(title=p_name)
                load_b = Gtk.Button(label="Load")
                load_b.add_css_class("flat")

                def _on_load(*_, name=p_name):
                    if profiles.load_profile(name):
                        self.app_state.load()
                        self._refresh_current_page()
                        dialog.close()
                        self.show_toast(f"Loaded profile '{name}'")

                load_b.connect("clicked", _on_load)
                row.add_suffix(load_b)

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")

                def _on_del(*_, name=p_name):
                    profiles.delete_profile(name)
                    dialog.close()
                    self.show_toast(f"Deleted profile '{name}'")

                del_b.connect("clicked", _on_del)
                row.add_suffix(del_b)
                box.append(row)
            grp_list.add(box)
        else:
            no_lbl = Gtk.Label(label="No saved profiles found")
            no_lbl.add_css_class("dim-label")
            grp_list.add(no_lbl)

        page.add(grp_list)
        dialog.add(page)
        dialog.present()

    def _open_backups_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Backups &amp; Snapshots", transient_for=self, modal=True)
        dialog.set_default_size(480, 420)
        page = Adw.PreferencesPage()
        grp = Adw.PreferencesGroup(title="Automatic and Manual Snapshots")

        backups_list = backup.list_backups()
        if backups_list:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for b in backups_list:
                row = Adw.ActionRow(title=b["name"], subtitle=f"{b['file_count']} file(s)")
                restore_btn = Gtk.Button(label="Restore")
                restore_btn.add_css_class("suggested-action")

                def _on_restore(*_, b_path=b["path"], b_name=b["name"]):
                    if backup.restore_backup(b_path):
                        self.app_state.load()
                        self._refresh_current_page()
                        dialog.close()
                        self.show_toast(f"Restored snapshot {b_name}")

                restore_btn.connect("clicked", _on_restore)
                row.add_suffix(restore_btn)
                box.append(row)
            grp.add(box)
        else:
            no_lbl = Gtk.Label(label="No backups recorded yet")
            no_lbl.add_css_class("dim-label")
            grp.add(no_lbl)

        page.add(grp)
        dialog.add(page)
        dialog.present()

    def _open_preferences_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Preferences", transient_for=self, modal=True)
        page = Adw.PreferencesPage()
        grp = Adw.PreferencesGroup(title="MangoMod Options")

        auto_bak = Adw.SwitchRow(title="Automatic Backups", subtitle="Create timestamped snapshot on save")
        auto_bak.set_active(app_settings.get("auto_backup", True))
        auto_bak.connect("notify::active", lambda r, _: app_settings.set("auto_backup", r.get_active()))
        grp.add(auto_bak)

        bak_lim_adj = Gtk.Adjustment(value=app_settings.get("backup_limit", 10), lower=1, upper=50, step_increment=1)
        bak_lim = Adw.SpinRow(title="Backup Retention Limit", adjustment=bak_lim_adj)
        bak_lim.connect("notify::value", lambda r, _: app_settings.set("backup_limit", int(r.get_value())))
        grp.add(bak_lim)

        hot_reload = Adw.SwitchRow(title="Live Reload on Save", subtitle="Trigger compositor hot-reload immediately upon saving")
        hot_reload.set_active(app_settings.get("hot_reload_on_save", True))
        hot_reload.connect("notify::active", lambda r, _: app_settings.set("hot_reload_on_save", r.get_active()))
        grp.add(hot_reload)

        val_save = Adw.SwitchRow(title="Validate on Save", subtitle="Verify config syntax using mango -c -p before saving")
        val_save.set_active(app_settings.get("validate_on_save", True))
        val_save.connect("notify::active", lambda r, _: app_settings.set("validate_on_save", r.get_active()))
        grp.add(val_save)

        page.add(grp)

        # --- Appearance: user themes + light/dark mode ---
        from mangomod import theme as mm_theme

        agrp = Adw.PreferencesGroup(
            title="Appearance",
            description=f"Drop your own *.css files in {mm_theme.user_themes_dir()} — they appear below",
        )

        theme_items = mm_theme.available_themes()
        theme_ids = [tid for tid, _label in theme_items]
        theme_labels = [label for _tid, label in theme_items]
        theme_dd = Gtk.DropDown(model=Gtk.StringList.new(theme_labels))
        cur_theme = app_settings.get("theme", "mango-dark")
        theme_dd.set_selected(theme_ids.index(cur_theme) if cur_theme in theme_ids else 0)
        theme_dd.set_valign(Gtk.Align.CENTER)
        theme_row = Adw.ActionRow(title="Theme", subtitle="Built-in or your own CSS")
        theme_row.add_suffix(theme_dd)
        agrp.add(theme_row)

        schemes = [("system", "System"), ("light", "Light"), ("dark", "Dark")]
        scheme_ids = [sid for sid, _s in schemes]
        scheme_dd = Gtk.DropDown(
            model=Gtk.StringList.new([label for _sid, label in schemes])
        )
        cur_scheme = app_settings.get("color_scheme", "dark")
        scheme_dd.set_selected(scheme_ids.index(cur_scheme) if cur_scheme in scheme_ids else 2)
        scheme_dd.set_valign(Gtk.Align.CENTER)
        scheme_row = Adw.ActionRow(title="Mode", subtitle="Libadwaita light/dark/system")
        scheme_row.add_suffix(scheme_dd)
        agrp.add(scheme_row)

        def _on_appearance_changed(*_):
            if getattr(self, "_appearance_guard", False):
                return
            tid = theme_ids[theme_dd.get_selected()]
            sid = scheme_ids[scheme_dd.get_selected()]
            # Mode must visibly do something: our CSS paints every surface,
            # so pair the built-ins — Light pulls Ripe Paper, Dark pulls
            # Mango Dark. Custom user themes are left alone (scheme only).
            if sid == "light" and tid == "mango-dark":
                tid = "ripe-paper"
            elif sid == "dark" and tid == "ripe-paper":
                tid = "mango-dark"
            bad = mm_theme.check_css_parses(mm_theme.load_theme_css(tid)[0] or "")
            if bad is not None:
                self.show_toast(f"Theme {tid!r} has errors — kept current theme")
                return
            app_settings.set("theme", tid)
            app_settings.set("color_scheme", sid)
            self._appearance_guard = True
            try:
                if tid in theme_ids:
                    theme_dd.set_selected(theme_ids.index(tid))
            finally:
                self._appearance_guard = False
            self._apply_theme(tid, sid)
            self.show_toast(f"Theme: {dict(theme_items).get(tid, tid)}")

        theme_dd.connect("notify::selected", _on_appearance_changed)
        scheme_dd.connect("notify::selected", _on_appearance_changed)

        page.add(agrp)
        dialog.add(page)
        dialog.present()

    def _open_shortcuts_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Keyboard Shortcuts", transient_for=self, modal=True)
        dialog.set_default_size(420, 360)
        page = Adw.PreferencesPage()
        grp = Adw.PreferencesGroup(title="MangoMod Shortcuts")

        for keys, desc in [
            ("Ctrl+S", "Save configuration"),
            ("Ctrl+Z", "Undo last change"),
            ("Ctrl+Shift+Z  /  Ctrl+Y", "Redo change"),
            ("Ctrl+R", "Reload Mango compositor"),
            ("Ctrl+F", "Focus sidebar search"),
        ]:
            row = Adw.ActionRow(title=desc)
            badge = Gtk.Label(label=keys)
            badge.add_css_class("mm-key-badge")
            row.add_suffix(badge)
            grp.add(row)

        page.add(grp)
        dialog.add(page)
        dialog.present()

    def _open_about_dialog(self) -> None:
        about = Adw.AboutDialog()
        about.set_application_name("MangoMod")
        about.set_developer_name("MangoMod Contributors")
        about.set_version(__version__)
        about.set_comments("A polished GTK4 / Libadwaita GUI configuration editor for the Mango Wayland compositor.")
        about.set_website("https://mangowm.github.io/docs")
        about.set_license_type(Gtk.License.MIT_X11)
        about.present(self)
