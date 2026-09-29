"""Main application window — sidebar + content NavigationSplitView."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from mangomod import app_settings, backup, config_parser, i18n, mango_ipc, profiles, snapshots
from mangomod.config_parser import SettingEntry
from mangomod import __version__
from mangomod.mango_schema import DISPATCHERS
from mangomod.mango_settings import SETTINGS
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
from mangomod.ui_compat import present_content_dialog, new_about_window

SIDEBAR_GROUPS = [
    ("Studio", [("overview", "view-grid-symbolic", "Overview")]),
    ("Workspace", [
        ("appearance", "preferences-desktop-appearance-symbolic", "Appearance"),
        ("window_effects", "view-reveal-symbolic", "Effects"),
        ("animations", "applications-multimedia-symbolic", "Motion"),
        ("outputs", "video-display-symbolic", "Displays"),
        ("layout", "view-grid-symbolic", "Layouts"),
        ("tags", "view-paged-symbolic", "Workspaces"),
    ]),
    ("Interaction", [
        ("bindings", "preferences-desktop-keyboard-shortcuts-symbolic", "Keyboard shortcuts"),
        ("input", "input-keyboard-symbolic", "Input devices"),
        ("mouse_gestures", "input-mouse-symbolic", "Mouse & gestures"),
        ("window_rules", "preferences-system-symbolic", "Window rules"),
        ("command_builder", "applications-graphics-symbolic", "Command builder"),
    ]),
    ("System", [
        ("startup", "system-run-symbolic", "Startup"),
        ("environment", "preferences-other-symbolic", "Environment"),
        ("misc", "preferences-desktop-apps-symbolic", "Behavior"),
        ("raw_config", "text-x-generic-symbolic", "Config editor"),
        ("all_settings", "preferences-system-symbolic", "All settings"),
    ]),
]

SIDEBAR_PAGES = [entry for _, group in SIDEBAR_GROUPS for entry in group]


class MangoModWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("MangoMod")
        self.set_default_size(1240, 860)
        self.add_css_class("mangomod")
        self._language = i18n.effective_language(app_settings.get("language", "system"))
        i18n.set_direction(self, self._language)

        self.app_state = AppState()
        self.app_state.load()

        self._current_page_id = ""
        self._pages: dict[str, Gtk.Widget] = {}
        self._page_instances: dict[str, Any] = {}
        self._sidebar_rows: dict[str, Gtk.ListBoxRow] = {}
        self._sidebar_listboxes: dict[str, Gtk.ListBox] = {}
        self._sidebar_expanders: dict[str, Gtk.Expander] = {}
        self._menu_buttons: list[Gtk.MenuButton] = []

        self._load_css()
        self._build_ui()
        i18n.localize_tree(self, self._language)
        self._setup_actions()
        self._setup_shortcuts()
        self.connect("close-request", self._on_close_request)
        self._watch_id = None
        self.connect('map', self._start_config_watch)
        self.connect('unmap', self._stop_config_watch)

        # Select first page
        if SIDEBAR_PAGES:
            self._select_page(SIDEBAR_PAGES[0][0])

    def _load_css(self) -> None:
        self._css_providers: list = []
        self._apply_theme(
            app_settings.get("theme", "mango-dark"),
            app_settings.get("color_scheme", "dark"),
        )

    def _start_config_watch(self, *_):
        if self._watch_id is None:
            self._watch_id = GLib.timeout_add(800, self._poll_config)

    def _stop_config_watch(self, *_):
        if self._watch_id is not None:
            GLib.source_remove(self._watch_id)
            self._watch_id = None

    def _poll_config(self):
        try:
            changes = self.app_state.disk_changes()
            if not changes:
                self._disk_notice.set_revealed(False)
                return True
            active_page = self._page_instances.get(self._current_page_id)
            pending_fields = getattr(active_page, 'has_unapplied_fields', lambda: False)()
            if self.app_state.is_dirty or pending_fields:
                self._disk_notice.set_title(self.tr('Files changed on disk. Your unsaved edits are kept; reload to review.'))
                self._disk_notice.set_revealed(True)
                return True
            # A missing main file may be between an editor's delete/rename.
            # Never replace the view with /etc defaults during that interval.
            if not config_parser.MANGO_CONFIG.is_file():
                return True
            raw = self._page_instances.get('raw_config')
            active_file = raw._active_file if raw else None
            self.app_state.load()
            self._refresh_current_page()
            raw = self._page_instances.get('raw_config')
            if raw and active_file:
                raw.select_file(active_file)
            self._disk_notice.set_revealed(False)
        except OSError as exc:
            self._disk_notice.set_title(self.tr('Could not read configuration files') + ': ' + str(exc))
            self._disk_notice.set_revealed(True)
        return True

    def _apply_theme(self, theme_id: str, scheme: str) -> bool:
        """Apply a theme only when its selected variant can be loaded."""
        from mangomod import theme as mm_theme

        style_mgr = Adw.StyleManager.get_default()
        effective_mode = scheme if scheme in ("light", "dark") else ("dark" if style_mgr.get_dark() else "light")
        base_id = theme_id if not theme_id.startswith("user:") else "mango-dark"
        css_text, error = mm_theme.load_theme_css(base_id, self._language, effective_mode)
        layers = [css_text] if css_text else []
        if theme_id.startswith("user:"):
            overlay, error = mm_theme.load_theme_css(theme_id, self._language, effective_mode)
            if overlay is not None:
                layers.append(overlay)
        if not error:
            error = mm_theme.check_css_parses('\n'.join(layers))
        if error:
            if hasattr(self, "_toast_overlay"):
                self.show_toast(error)
            if not self._css_providers:
                fallback = app_settings.get("builtin_theme", "mango-dark")
                if fallback not in mm_theme.BUILTIN_THEMES:
                    fallback = "mango-dark"
                app_settings.set("theme", fallback)
                self._apply_theme(fallback, effective_mode)
            return False

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
        return True

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

        # Runtime status lives in the overview; keep the banner for reload state.
        self._update_banner()

        self._disk_notice = Adw.Banner(button_label=self.tr('Reload files from disk'))
        self._disk_notice.connect('button-clicked', lambda *_: self.reload_from_disk())
        root_box.append(self._disk_notice)

        # Navigation Split View
        self._split_view = Adw.NavigationSplitView()
        self._split_view.set_vexpand(True)
        self._split_view.set_min_sidebar_width(240)
        self._split_view.set_max_sidebar_width(260)
        self._split_view.set_sidebar_width_fraction(0.21)
        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 760sp"))
        breakpoint.add_setter(self._split_view, "collapsed", True)
        self.add_breakpoint(breakpoint)
        root_box.append(self._split_view)

        self._split_view.set_sidebar(self._build_sidebar_nav())
        self._split_view.set_content(self._build_content_nav())
        root_box.append(self._build_save_bar())

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
        title_w = Adw.WindowTitle(title="MangoMod")
        title_w.add_css_class("mm-brand")
        header.set_title_widget(title_w)

        from mangomod.pages.base import main_menu
        app_menu = Gtk.MenuButton(icon_name='open-menu-symbolic', tooltip_text=self.tr('App menu'))
        app_menu.set_menu_model(main_menu(self._language))
        self._menu_buttons.append(app_menu)
        header.pack_end(app_menu)

        sidebar_box.append(header)

        # Search bar
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Find a section…")
        self._search_entry.set_tooltip_text("Find a section (Ctrl+K); Enter opens the first result")
        self._search_entry.add_css_class("mm-search-entry")
        self._search_entry.set_margin_start(10)
        self._search_entry.set_margin_end(10)
        self._search_entry.set_margin_top(8)
        self._search_entry.set_margin_bottom(6)
        self._search_entry.connect("search-changed", self._on_sidebar_search)
        self._search_entry.connect("activate", self._activate_search_result)
        sidebar_box.append(self._search_entry)

        self._search_results = Gtk.ListBox()
        self._search_results.add_css_class("mm-search-results")
        self._search_results.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._search_results.connect("row-activated", self._open_search_result)
        results_scroll = Gtk.ScrolledWindow(max_content_height=280, propagate_natural_height=True)
        results_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        results_scroll.set_child(self._search_results)
        self._search_revealer = Gtk.Revealer()
        self._search_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self._search_revealer.set_child(results_scroll)
        sidebar_box.append(self._search_revealer)

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
                row._search_text = f"{group_title} {label_text} {i18n.translate(group_title, 'ar')} {i18n.translate(label_text, 'ar')}".lower()

                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                icon = Gtk.Image.new_from_icon_name(icon_name)
                icon.set_pixel_size(16)
                icon.set_valign(Gtk.Align.CENTER)
                text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
                lbl = Gtk.Label(label=label_text, xalign=0)
                lbl.set_hexpand(True)
                sub = Gtk.Label(label=group_title, xalign=0)
                sub.add_css_class("dim-label")
                text_box.append(lbl)

                row_box.append(icon)
                row_box.append(text_box)
                row.set_child(row_box)

                listbox.append(row)
                self._sidebar_rows[page_id] = row

            expander.set_child(listbox)
            list_container.append(expander)

        self._search_empty = Gtk.Label(label="No matching sections", wrap=True)
        self._search_empty.add_css_class("dim-label")
        self._search_empty.set_margin_top(24)
        self._search_empty.set_visible(False)
        list_container.append(self._search_empty)
        scroller.set_child(list_container)
        sidebar_box.append(scroller)

        footer_hint = Gtk.Label(label="MANGO / WORKSPACE STUDIO", xalign=0)
        footer_hint.add_css_class("mm-sidebar-section-label")
        footer_hint.set_margin_bottom(18)
        sidebar_box.append(footer_hint)
        nav.set_child(sidebar_box)
        return nav

    def _build_save_bar(self):
        footer = Gtk.Box(spacing=12)
        footer.add_css_class("mm-save-bar")
        self._save_status = Gtk.Label(label="All changes saved", xalign=0, hexpand=True)
        self._save_status.add_css_class("mm-save-status")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3, hexpand=True)
        status_box.append(self._save_status)
        self._config_path_label = Gtk.Label(xalign=0, selectable=True)
        self._config_path_label.set_ellipsize(3)
        self._config_path_label.add_css_class('dim-label')
        status_box.append(self._config_path_label)
        footer.append(status_box)
        self._review_btn = Gtk.Button(label="Review changes")
        self._review_btn.add_css_class("flat")
        self._review_btn.connect("clicked", lambda *_: self._review_changes())
        footer.append(self._review_btn)
        # Bottom action bar: Save + Undo/Redo (previously header-only Save,
        # undo/redo had no visible buttons at all)
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_bar.set_margin_start(10)
        action_bar.set_margin_end(10)
        action_bar.set_margin_top(6)
        action_bar.set_margin_bottom(10)

        self._save_btn = Gtk.Button(label="Save changes")
        self._save_btn.add_css_class("suggested-action")
        self._save_btn.set_hexpand(False)
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

        footer.append(action_bar)

        self._refresh_action_buttons()
        return footer

    def _review_changes(self):
        import difflib
        current = self.app_state.snapshot()
        diff = ''.join(''.join(difflib.unified_diff(
            self.app_state.saved_files.get(path, '').splitlines(keepends=True),
            current.get(path, '').splitlines(keepends=True),
            fromfile=f'{path} (saved)', tofile=f'{path} (pending)',
        )) for path in sorted(self.app_state.saved_files.keys() | current.keys()))
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        view = Gtk.TextView(editable=False, monospace=True,
                            left_margin=20, right_margin=20, top_margin=20, bottom_margin=20)
        view.get_buffer().set_text(diff or "Your configuration has no pending changes.")
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(view)
        toolbar.set_content(scroll)
        return present_content_dialog(self, toolbar, "Review changes", 800, 520)

    def _refresh_action_buttons(self) -> None:
        if hasattr(self, '_config_path_label'):
            self._config_path_label.set_text(str(config_parser.MANGO_CONFIG))
            self._config_path_label.set_tooltip_text(str(config_parser.MANGO_CONFIG))
        if hasattr(self, "_save_status"):
            dirty = self.app_state.is_dirty
            self._save_status.set_label(self.tr("Unsaved changes · review before saving" if dirty else "All changes saved"))
            self._review_btn.set_sensitive(dirty)
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
            i18n.localize_tree(widget, self._language)
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
        self._split_view.set_show_content(True)

        # Notify page
        inst = self._page_instances.get(page_id)
        if inst and hasattr(inst, "on_shown"):
            inst.on_shown()
            i18n.localize_tree(self._pages[page_id], self._language)

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
        self._rebuild_search_results(query)
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

        self._search_empty.set_visible(first_match is None and not self._search_revealer.get_reveal_child())

    def _rebuild_search_results(self, query: str) -> None:
        while child := self._search_results.get_first_child():
            self._search_results.remove(child)
        if len(query) < 2:
            self._search_revealer.set_reveal_child(False)
            return
        matches = []
        for page_id, _icon, label in SIDEBAR_PAGES:
            haystack = f"{page_id} {label} {i18n.translate(label, 'ar')}".lower()
            if query in haystack:
                matches.append(("page", page_id, label, "Section"))
        for setting in SETTINGS:
            label, key = setting["label"], setting["key"]
            haystack = f"{key} {label} {setting['desc']} {i18n.translate(label, 'ar')}".lower()
            if query in haystack:
                matches.append(("setting", key, label, key))
        catalog_keys = {setting["key"] for setting in SETTINGS}
        for setting in self.app_state.doc.entries:
            if isinstance(setting, SettingEntry) and setting.key not in catalog_keys and query in setting.key.lower():
                matches.append(("setting", setting.key, setting.key, "Other config options"))
        for group in DISPATCHERS.values():
            for action in group:
                label, command = action["desc"], action["cmd"]
                if query in f"{command} {label}".lower():
                    matches.append(("action", command, label, command))
        for kind, identifier, title, subtitle in matches[:18]:
            row = Gtk.ListBoxRow()
            row._search_target = (kind, identifier)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_margin_start(12)
            box.set_margin_end(12)
            box.set_margin_top(7)
            box.set_margin_bottom(7)
            box.append(Gtk.Label(label=i18n.translate(title, self._language), xalign=0, wrap=True))
            detail = Gtk.Label(label=i18n.translate(subtitle, self._language), xalign=0)
            detail.add_css_class("dim-label")
            box.append(detail)
            row.set_child(box)
            self._search_results.append(row)
        first = self._search_results.get_row_at_index(0)
        if first:
            self._search_results.select_row(first)
        self._search_revealer.set_reveal_child(first is not None)

    def _open_search_result(self, _listbox, row) -> None:
        kind, identifier = row._search_target
        self._search_entry.set_text("")
        self._select_page(identifier if kind == "page" else "all_settings" if kind == "setting" else "command_builder")
        if kind == "setting":
            self._page_instances["all_settings"]._search.set_text(identifier)
        elif kind == "action":
            builder = self._page_instances["command_builder"]
            builder._show_library()
            builder._search.set_text(identifier)

    def _activate_search_result(self, entry):
        self._on_sidebar_search(entry)
        selected = self._search_results.get_selected_row()
        if self._search_revealer.get_reveal_child() and selected is not None:
            self._open_search_result(self._search_results, selected)
            return
        for page_id, row in self._sidebar_rows.items():
            if row.get_visible():
                self._select_page(page_id)
                break

    def show_toast(self, message: str, timeout: int = 3) -> None:
        # Adw.Toast parses its title as markup: a bare & (e.g. "saved &
        # reloaded") aborts the whole toast with a GTK warning. Escape once,
        # here, so no caller ever has to think about it.
        toast = Adw.Toast.new(i18n.translate(message, self._language).replace("&", "&amp;"))
        toast.set_timeout(timeout)
        self._toast_overlay.add_toast(toast)

    def tr(self, message: str) -> str:
        return i18n.translate(message, self._language)

    def _has_draft(self):
        builder = self._page_instances.get('command_builder')
        return builder is not None and builder.has_pending_draft()

    def _guard_unsaved(self, callback):
        if not self.app_state.is_dirty and not self._has_draft():
            callback()
            return
        dialog = Adw.MessageDialog.new(self, self.tr('Unsaved work'),
            self.tr('Save your config changes or discard them before continuing. Unapplied shortcut drafts are kept for recovery.'))
        for response, label in [('cancel', 'Keep editing'), ('discard', 'Discard changes'), ('save', 'Save and continue')]:
            dialog.add_response(response, self.tr(label))
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.set_response_appearance('discard', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_response_appearance('save', Adw.ResponseAppearance.SUGGESTED)
        def respond(_dialog, response):
            if response == 'cancel':
                return
            if response == 'save' and self.app_state.is_dirty and not self.save_config_action():
                return
            builder = self._page_instances.get('command_builder')
            if builder:
                builder.save_recovery()
            callback()
        dialog.connect('response', respond)
        dialog.present()
        self._unsaved_dialog = dialog

    def _on_close_request(self, *_):
        if getattr(self, '_allow_close', False):
            return False
        if not self.app_state.is_dirty and not self._has_draft():
            return False
        def close():
            self._allow_close = True
            self.close()
        self._guard_unsaved(close)
        return True

    def _set_language(self, setting: str) -> None:
        from mangomod.pages.base import main_menu
        app_settings.set("language", setting)
        self._language = i18n.effective_language(setting)
        i18n.set_direction(self, self._language)
        i18n.localize_tree(self, self._language)
        self._apply_theme(app_settings.get("theme", "mango-dark"), app_settings.get("color_scheme", "dark"))
        for menu_button in self._menu_buttons:
            menu_button.set_menu_model(main_menu(self._language))
            menu_button.set_tooltip_text(i18n.translate("App menu", self._language))

    def mark_dirty(self) -> None:
        self.app_state.mark_dirty()
        self._save_btn.set_label(self.tr("Save changes •"))
        self._refresh_action_buttons()

    def mark_clean(self) -> None:
        self.app_state.mark_clean()
        self._save_btn.set_label(self.tr("Save changes"))
        self._refresh_action_buttons()
        overview = self._page_instances.get("overview")
        if overview and self._current_page_id == "overview":
            overview.refresh()

    def push_undo(self, description: str, before: str, after: str) -> None:
        self.app_state.push_undo(description, before, after)
        self._invalidate_other_pages()
        if self.app_state.is_dirty:
            self.mark_dirty()
        else:
            self.mark_clean()

    def _remove_page(self, page_id):
        widget = self._pages.pop(page_id)
        self._page_instances.pop(page_id).dispose()
        self._menu_buttons = [button for button in self._menu_buttons if not button.is_ancestor(widget)]
        self._content_stack.remove(widget)

    def _invalidate_other_pages(self):
        builder = self._page_instances.get('command_builder')
        if builder:
            builder.rebind_source()
        for page_id in list(self._pages):
            if page_id not in (self._current_page_id, 'command_builder'):
                self._remove_page(page_id)

    def open_binding_editor(self, entry=None, kind='key'):
        self._select_page('command_builder')
        builder = self._page_instances['command_builder']
        def edit():
            if entry is not None:
                builder.load_binding(entry)
            else:
                builder._new_draft()
                builder.draft.trigger.kind = kind
                builder.draft.trigger.key = {'key':'Return','mouse':'btn_left','axis':'UP',
                                             'gesture':'left','switch':'fold'}[kind]
                builder._select_trigger()
                builder._baseline = builder._fingerprint()
        builder._confirm_replace(edit)

    def reload_from_disk(self):
        def reload():
            self.app_state.load()
            self._refresh_current_page(reset_builder=True)
        self._guard_unsaved(reload)

    def save_config_action(self) -> bool:
        ok, msg = self.app_state.save()
        if ok:
            self.mark_clean()
            self.show_toast(msg)
        elif msg.startswith("Validation error:"):
            self._offer_force_save(msg)
        else:
            dialog = Adw.MessageDialog.new(self, self.tr('Save Failed'), msg)
            dialog.add_response('close', self.tr('Close'))
            dialog.present()
        return ok

    def _offer_force_save(self, validation_msg: str) -> None:
        # Rejected edits stay in memory; the working files were never replaced.
        dialog = Adw.MessageDialog.new(self, self.tr('Validation Failed'),
            self.tr('The previous configuration is unchanged. Your edits remain available for correction.')
            + '\n\n' + validation_msg)
        dialog.add_response('cancel', self.tr('Keep editing'))
        dialog.set_close_response('cancel')
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
        if self.app_state.is_dirty or self._has_draft():
            def switch():
                self.app_state.mark_clean()
                builder = self._page_instances.get('command_builder')
                if builder:
                    builder._baseline = builder._fingerprint()
                self.switch_main_config(target)
            self._guard_unsaved(switch)
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
        self._refresh_current_page(reset_builder=True)
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

        if ctrl and keyval in (Gdk.KEY_k, Gdk.KEY_K):
            self._split_view.set_show_content(False)
            self._search_entry.grab_focus()
            return True
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
            self.app_state.restore_history(entry)
            self._refresh_current_page()
            self.show_toast(f"Undo: {entry.description}")
        self._refresh_action_buttons()

    def _action_redo(self) -> None:
        entry = self.app_state.undo.pop_redo()
        if entry:
            self.app_state.restore_history(entry, redo=True)
            self._refresh_current_page()
            self.show_toast(f"Redo: {entry.description}")
        self._refresh_action_buttons()

    def _refresh_current_page(self, reset_builder=False) -> None:
        # Document replacement invalidates every editor, including hidden pages.
        current = self._current_page_id
        for page_id, widget in list(self._pages.items()):
            if page_id == 'command_builder' and not reset_builder:
                self._page_instances[page_id].rebind_source()
                continue
            self._remove_page(page_id)
        if self.app_state.is_dirty:
            self.mark_dirty()
        else:
            self.mark_clean()
        self._select_page(current)

    def _restore_files(self, read_files, on_restored):
        try:
            files = read_files()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.show_toast(str(exc))
            return
        def apply():
            try:
                ok, message = self.app_state.apply_files(files)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                ok, message = False, str(exc)
            if ok:
                self._refresh_current_page(reset_builder=True)
                on_restored()
                self.show_toast(message, timeout=6)
            else:
                dialog = Adw.MessageDialog.new(self, self.tr('Could not activate configuration'), message)
                dialog.add_response('cancel', self.tr('Keep editing'))
                dialog.set_close_response('cancel')
                self._restore_dialog = dialog
                dialog.present()
        self._guard_unsaved(apply)

    def _open_profiles_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="Presets", transient_for=self, modal=True)
        dialog.set_default_size(440, 400)
        page = Adw.PreferencesPage()

        # Save profile row
        grp_save = Adw.PreferencesGroup(title="Save Current Setup as Preset", description=str(profiles.presets_dir()))
        name_entry = Adw.EntryRow(title="Preset Name")
        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")

        def _on_save_prof(*_):
            n = name_entry.get_text().strip()
            if n:
                try:
                    profiles.save_profile(n, self.app_state.source_files, self.app_state.snapshot())
                except (OSError, ValueError) as exc:
                    self.show_toast(str(exc))
                    return
                dialog.close()
                self.show_toast(f"Saved preset '{n}'")

        save_btn.connect("clicked", _on_save_prof)
        name_entry.add_suffix(save_btn)
        grp_save.add(name_entry)
        page.add(grp_save)

        # Saved profiles list
        grp_list = Adw.PreferencesGroup(title="Saved Presets", description="Switching a preset updates the active config.conf and its sources.")
        profs = profiles.list_profiles()
        if profs:
            box = Gtk.ListBox()
            box.add_css_class("boxed-list")
            for p_name in profs:
                row = Adw.ActionRow(title=p_name)
                load_b = Gtk.Button(label="Switch to preset")
                load_b.add_css_class("flat")

                def _on_load(*_, name=p_name):
                    self._restore_files(lambda: profiles.read_profile(name),
                        lambda: (dialog.close(), self.show_toast(f"Switched to preset '{name}'")))

                load_b.connect("clicked", _on_load)
                row.add_suffix(load_b)

                del_b = Gtk.Button(icon_name="user-trash-symbolic")
                del_b.add_css_class("flat")

                def _on_del(*_, name=p_name):
                    profiles.delete_profile(name)
                    dialog.close()
                    self.show_toast(f"Deleted preset '{name}'")

                del_b.connect("clicked", _on_del)
                row.add_suffix(del_b)
                box.append(row)
            grp_list.add(box)
        else:
            no_lbl = Gtk.Label(label="No saved presets found")
            no_lbl.add_css_class("dim-label")
            grp_list.add(no_lbl)

        page.add(grp_list)
        dialog.add(page)
        i18n.localize_tree(dialog, self._language)
        dialog.present()
        return dialog

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
                    self._restore_files(lambda: snapshots.contents(b_path),
                        lambda: (dialog.close(), self.show_toast(f"Restored snapshot {b_name}")))

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
        i18n.localize_tree(dialog, self._language)
        dialog.present()

    def _open_preferences_dialog(self) -> None:
        dialog = Adw.PreferencesWindow(title="App Settings", transient_for=self, modal=True)
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

        language_group = Adw.PreferencesGroup(title="Language")
        language_ids = ["system", "en", "ar"]
        language_names = ["Use system language", "English", "Arabic"]
        language_row = Adw.ComboRow(title="Language", model=Gtk.StringList.new(language_names))
        saved_language = app_settings.get("language", "system")
        language_row.set_selected(language_ids.index(saved_language) if saved_language in language_ids else 0)
        def change_language(row, _param):
            value = language_ids[row.get_selected()]
            self._set_language(value)
            i18n.set_direction(dialog, self._language)
            i18n.localize_tree(dialog, self._language)
            refresh_theme_choices()
            update_palette()
        language_row.connect("notify::selected", change_language)
        language_group.add(language_row)

        # --- Five built-ins followed by any themes created by the user. ---
        from mangomod import theme as mm_theme

        agrp = Adw.PreferencesGroup(
            title="Appearance",
            description="Choose a theme and its light or dark variant.",
        )

        theme_ids = [tid for tid, _ in mm_theme.available_themes(self._language)]
        theme_labels = [mm_theme.theme_name(tid, self._language) for tid in theme_ids]
        theme_dd = Gtk.DropDown(model=Gtk.StringList.new(theme_labels))
        cur_theme = app_settings.get("theme", "mango-dark")
        theme_dd.set_selected(theme_ids.index(cur_theme) if cur_theme in theme_ids else 0)
        theme_dd.set_valign(Gtk.Align.CENTER)
        theme_row = Adw.ActionRow(title="Theme", subtitle="Right-click a custom theme for options")
        theme_row.add_suffix(theme_dd)
        theme_options = Gtk.Button(icon_name='view-more-symbolic', valign=Gtk.Align.CENTER)
        theme_options.set_tooltip_text(self.tr('Theme options'))
        theme_row.add_suffix(theme_options)
        agrp.add(theme_row)

        schemes = [("light", "Light"), ("dark", "Dark")]
        scheme_ids = [sid for sid, _ in schemes]
        scheme_dd = Gtk.DropDown(model=Gtk.StringList.new([label for _, label in schemes]))
        cur_scheme = app_settings.get("color_scheme", "dark")
        if cur_scheme not in scheme_ids:
            cur_scheme = "dark" if Adw.StyleManager.get_default().get_dark() else "light"
        scheme_dd.set_selected(scheme_ids.index(cur_scheme))
        scheme_dd.set_valign(Gtk.Align.CENTER)
        scheme_row = Adw.ActionRow(title="Variant", subtitle="Created themes have only the variants you save")
        scheme_row.add_suffix(scheme_dd)
        agrp.add(scheme_row)

        palette_row = Adw.ActionRow(title="Palette preview")
        palette_box = Gtk.Box(spacing=7, valign=Gtk.Align.CENTER)
        palette_row.add_suffix(palette_box)
        agrp.add(palette_row)

        def update_palette(*_):
            selected_id = theme_ids[theme_dd.get_selected()]
            theme_options.set_sensitive(selected_id.startswith('user:'))
            variants = [self.tr(label) for mode, label in schemes
                        if mm_theme.load_theme_css(selected_id, self._language, mode)[1] is None]
            scheme_row.set_subtitle(self.tr('Available variants') + ': ' + ' / '.join(variants))
            while child := palette_box.get_first_child():
                palette_box.remove(child)
            swatches = mm_theme.theme_swatches(theme_ids[theme_dd.get_selected()], self._language, scheme_ids[scheme_dd.get_selected()])
            for color in swatches:
                rgba = Gdk.RGBA()
                rgba.parse(color)
                square = Gtk.DrawingArea(content_width=30, content_height=30)
                square.set_tooltip_text(color)
                def draw(_area, cr, width, height, sample=rgba):
                    cr.set_source_rgba(sample.red, sample.green, sample.blue, sample.alpha)
                    cr.rectangle(0, 0, width, height)
                    cr.fill()
                square.set_draw_func(draw)
                palette_box.append(square)
        update_palette()
        def refresh_theme_choices():
            current = app_settings.get("theme", "mango-dark")
            theme_ids[:] = [tid for tid, _ in mm_theme.available_themes(self._language)]
            labels = [mm_theme.theme_name(tid, self._language) for tid in theme_ids]
            model = theme_dd.get_model()
            self._appearance_guard = True
            try:
                model.splice(0, model.get_n_items(), labels)
                theme_dd.set_selected(theme_ids.index(current) if current in theme_ids else 0)
                current_scheme = app_settings.get("color_scheme", "dark")
                scheme_dd.set_selected(scheme_ids.index(current_scheme) if current_scheme in scheme_ids else 1)
            finally:
                self._appearance_guard = False
            # The generic translation pass must not restore labels from the old language.
            theme_dd._mm_choice_sources = (labels, labels)
            update_palette()

        def _on_appearance_changed(source, *_):
            if getattr(self, "_appearance_guard", False):
                return
            tid = theme_ids[theme_dd.get_selected()]
            sid = scheme_ids[scheme_dd.get_selected()]
            if tid == app_settings.get("theme", "mango-dark") and sid == app_settings.get("color_scheme", "dark"):
                return
            css, error = mm_theme.load_theme_css(tid, self._language, sid)
            bad = mm_theme.check_css_parses(css) if css is not None else None
            if error or bad:
                self.show_toast(error or bad)
                previous = app_settings.get("theme", "mango-dark")
                previous_scheme = app_settings.get("color_scheme", "dark")
                self._appearance_guard = True
                try:
                    theme_dd.set_selected(theme_ids.index(previous) if previous in theme_ids else 0)
                    scheme_dd.set_selected(scheme_ids.index(previous_scheme) if previous_scheme in scheme_ids else 1)
                finally:
                    self._appearance_guard = False
                return
            app_settings.set("theme", tid)
            app_settings.set("color_scheme", sid)
            if tid in mm_theme.BUILTIN_THEMES:
                app_settings.set("builtin_theme", tid)
            self._apply_theme(tid, sid)
            update_palette()
            self.show_toast(f"Theme: {mm_theme.theme_name(tid, self._language)}")

        theme_dd.connect("notify::selected", _on_appearance_changed)
        scheme_dd.connect("notify::selected", _on_appearance_changed)

        def delete_theme(theme_id: str):
            deleted, error = mm_theme.delete_custom_theme(theme_id)
            if not deleted:
                self.show_toast(error or "Theme not found.")
                return
            if app_settings.get("theme") == theme_id:
                fallback = app_settings.get("builtin_theme", "mango-dark")
                if fallback not in mm_theme.BUILTIN_THEMES:
                    fallback = "mango-dark"
                app_settings.set("theme", fallback)
                self._apply_theme(fallback, app_settings.get("color_scheme", "dark"))
            refresh_theme_choices()
            self.show_toast("Theme deleted")

        def confirm_delete(theme_id: str):
            name = mm_theme.theme_name(theme_id, self._language)
            confirm = Adw.MessageDialog.new(
                dialog,
                i18n.translate("Delete theme?", self._language),
                i18n.translate(f"Delete {name} and all its saved variants?", self._language),
            )
            confirm.add_response("cancel", i18n.translate("Cancel", self._language))
            confirm.add_response("delete", i18n.translate("Delete theme", self._language))
            confirm.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            confirm.set_default_response("cancel")
            confirm.set_close_response("cancel")
            confirm.connect("response", lambda _dlg, response: delete_theme(theme_id) if response == "delete" else None)
            i18n.localize_tree(confirm, self._language)
            confirm.present()

        def show_theme_menu(theme_id: str, anchor: Gtk.Widget):
            if not theme_id.startswith("user:"):
                return
            menu = Gtk.Popover(autohide=True)
            menu.set_parent(anchor)
            options = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            options.set_margin_top(6)
            options.set_margin_bottom(6)
            options.set_margin_start(6)
            options.set_margin_end(6)
            create_variant = Gtk.Button(label="Create variant…")
            create_variant.set_sensitive(any(mm_theme.load_theme_css(theme_id, self._language, mode)[1] for mode in ("light", "dark")))
            create_variant.connect("clicked", lambda *_: (menu.popdown(), self._open_custom_themes_dialog(refresh_theme_choices, theme_id)))
            options.append(create_variant)
            delete_button = Gtk.Button(label="Delete theme")
            delete_button.add_css_class("destructive-action")
            delete_button.connect("clicked", lambda *_: (menu.popdown(), confirm_delete(theme_id)))
            options.append(delete_button)
            menu.set_child(options)
            menu.connect("closed", lambda popover: popover.unparent())
            i18n.localize_tree(menu, self._language)
            menu.popup()
            return menu

        def theme_item_setup(_factory, item):
            label = Gtk.Label(xalign=0)
            label.set_hexpand(True)
            label.set_margin_start(6)
            label.set_margin_end(6)
            click = Gtk.GestureClick(button=3)
            click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            def on_secondary(gesture, _press_count, _x, _y):
                position = item.get_position()
                if position < len(theme_ids) and theme_ids[position].startswith("user:"):
                    gesture.set_state(Gtk.EventSequenceState.CLAIMED)
                    show_theme_menu(theme_ids[position], label)
            click.connect("pressed", on_secondary)
            label.add_controller(click)
            item.set_child(label)

        def theme_item_bind(_factory, item):
            item.get_child().set_text(item.get_item().get_string())

        theme_list_factory = Gtk.SignalListItemFactory()
        theme_list_factory.connect("setup", theme_item_setup)
        theme_list_factory.connect("bind", theme_item_bind)
        theme_dd.set_list_factory(theme_list_factory)
        selected_click = Gtk.GestureClick(button=3)
        selected_click.connect("pressed", lambda gesture, _count, _x, _y: show_theme_menu(theme_ids[theme_dd.get_selected()], theme_dd))
        theme_dd.add_controller(selected_click)
        theme_dd._mm_delete_theme = delete_theme
        theme_dd._mm_open_theme_menu = show_theme_menu
        theme_options.connect('clicked', lambda *_: show_theme_menu(theme_ids[theme_dd.get_selected()], theme_options))

        custom_row = Adw.ActionRow(title="Create theme", subtitle="Add a new theme or another variant")
        custom_button = Gtk.Button(label="Create…", valign=Gtk.Align.CENTER)
        custom_button.connect("clicked", lambda *_: self._open_custom_themes_dialog(refresh_theme_choices))
        custom_row.add_suffix(custom_button)
        agrp.add(custom_row)

        page.add(agrp)
        page.add(language_group)
        page.add(grp)
        dialog.add(page)
        i18n.localize_tree(dialog, self._language)
        dialog.present()
        return dialog

    def _open_custom_themes_dialog(self, on_change=None, theme_id: str | None = None):
        """Create one theme variant and add its name to the main picker."""
        from mangomod import theme as mm_theme

        dialog = Adw.PreferencesWindow(title="Create theme", transient_for=self, modal=True)
        dialog.set_default_size(540, 500)
        page = Adw.PreferencesPage()
        dialog.add(page)

        create_group = Adw.PreferencesGroup(title="Create theme", description="Choose a name, variant, and three colors.")
        name_row = Adw.EntryRow(title="Theme name")
        create_group.add(name_row)
        active_theme = theme_id or app_settings.get("theme", "mango-dark")
        if active_theme.startswith("user:"):
            name_row.set_text(active_theme[5:])
        mode_row = Adw.ComboRow(title="Variant", model=Gtk.StringList.new(["Light", "Dark"]))
        selected_mode = app_settings.get("color_scheme", "dark")
        if active_theme.startswith("user:"):
            other_mode = "light" if selected_mode == "dark" else "dark"
            if mm_theme.load_theme_css(active_theme, self._language, other_mode)[1]:
                selected_mode = other_mode
        mode_row.set_selected(0 if selected_mode == "light" else 1)
        create_group.add(mode_row)
        family = app_settings.get("builtin_theme", "mango-dark")
        if family not in mm_theme.BUILTIN_THEMES:
            family = "mango-dark"
        defaults = mm_theme.theme_swatches(family, self._language, "light" if mode_row.get_selected() == 0 else "dark")
        def hex_color(button: Gtk.ColorDialogButton) -> str:
            color = button.get_rgba()
            return "#{:02x}{:02x}{:02x}".format(*(round(channel * 255) for channel in (color.red, color.green, color.blue)))

        color_rows = []
        for title, value in zip(("Background color", "Card color", "Accent color"), defaults):
            row = Adw.ActionRow(title=title, subtitle=value)
            picker = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog(with_alpha=False))
            rgba = Gdk.RGBA()
            rgba.parse(value)
            picker.set_rgba(rgba)
            picker.set_valign(Gtk.Align.CENTER)
            picker.connect("notify::rgba", lambda button, _param, target=row: target.set_subtitle(hex_color(button)))
            row.add_suffix(picker)
            create_group.add(row)
            color_rows.append((row, picker))
        current_mode = ["light" if mode_row.get_selected() == 0 else "dark"]
        def change_mode(row, _param):
            next_mode = "light" if row.get_selected() == 0 else "dark"
            before = mm_theme.theme_swatches(family, self._language, current_mode[0])
            after = mm_theme.theme_swatches(family, self._language, next_mode)
            for (color_row, picker), old, new in zip(color_rows, before, after):
                if color_row.get_subtitle().lower() == old.lower():
                    rgba = Gdk.RGBA()
                    rgba.parse(new)
                    picker.set_rgba(rgba)
            current_mode[0] = next_mode
        mode_row.connect("notify::selected", change_mode)

        preview_group = Adw.PreferencesGroup(title='Live preview')
        preview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        import uuid
        preview_class = 'mm-preview-' + uuid.uuid4().hex
        preview.add_css_class(preview_class)
        sample_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sample_card.add_css_class('sample-card')
        sample_card.append(Gtk.Label(label=self.tr('Sample text'), xalign=0))
        sample_button = Gtk.Button(label=self.tr('Sample action'))
        sample_card.append(sample_button)
        preview.append(sample_card)
        preview_group.add(preview)
        contrast = Gtk.Label(xalign=0, wrap=True)
        preview_group.add(contrast)
        preview_provider = Gtk.CssProvider()
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(display, preview_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        dialog.connect('close-request', lambda *_: (Gtk.StyleContext.remove_provider_for_display(display, preview_provider), False)[1])
        def update_preview(*_):
            bg, card, accent = [hex_color(picker) for _, picker in color_rows]
            card_text, button_text = mm_theme.readable_text(card), mm_theme.readable_text(accent)
            preview_provider.load_from_data((
                f'.{preview_class} {{background: {bg}; padding: 16px; border-radius: 12px;}}'
                f'.{preview_class} .sample-card {{background: {card}; padding: 16px; border-radius: 8px;}}'
                f'.{preview_class} label {{color: {card_text};}}'
                f'.{preview_class} button {{background: {accent}; background-image: none;}}'
                f'.{preview_class} button label {{color: {button_text};}}'
            ).encode())
            ratio = min(mm_theme.contrast_ratio(card, card_text), mm_theme.contrast_ratio(accent, button_text))
            contrast.set_text(self.tr('Text contrast') + f': {ratio:.2f}:1 — ' + self.tr('Good contrast' if ratio >= 4.5 else 'Low contrast'))
            contrast.remove_css_class('warning')
            if ratio < 4.5:
                contrast.add_css_class('warning')
        for _, picker in color_rows:
            picker.connect('notify::rgba', update_preview)
        update_preview()

        save_button = Gtk.Button(label="Create and use theme")
        save_button.add_css_class("suggested-action")
        def save_theme(*_):
            mode = "light" if mode_row.get_selected() == 0 else "dark"
            theme_id, error = mm_theme.create_custom_theme(name_row.get_text(), mode, *(hex_color(picker) for _row, picker in color_rows))
            if error:
                self.show_toast(error)
                return
            app_settings.set("theme", theme_id)
            app_settings.set("color_scheme", mode)
            self._apply_theme(theme_id, mode)
            if on_change:
                on_change()
            self.show_toast("Custom theme created")
            dialog.close()
        save_button.connect("clicked", save_theme)
        create_group.add(save_button)
        page.add(create_group)
        page.add(preview_group)

        i18n.localize_tree(dialog, self._language)
        i18n.set_direction(dialog, self._language)
        dialog.present()
        return dialog

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
        i18n.localize_tree(dialog, self._language)
        dialog.present()

    def _open_about_dialog(self) -> None:
        about, present = new_about_window(self)
        about.set_application_name("MangoMod")
        about.set_developer_name("MangoMod Contributors")
        about.set_version(__version__)
        about.set_comments("A polished GTK4 / Libadwaita GUI configuration editor for the Mango Wayland compositor.")
        about.set_website("https://mangowm.github.io/docs")
        about.set_license_type(Gtk.License.MIT_X11)
        present()
