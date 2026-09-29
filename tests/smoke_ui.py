"""Run with PYTHONPATH=. python tests/smoke_ui.py on a graphical session.
Uses a temporary config; never saves to or reloads the user's compositor.
"""
from pathlib import Path
import tempfile
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk, GLib, Gio
from mangomod import config_parser, app_settings
from mangomod.window import MangoModWindow, SIDEBAR_PAGES

sandbox = tempfile.TemporaryDirectory(prefix='mangomod-ui-')
config = Path(sandbox.name) / 'config.conf'
config.write_text('borderpx=3\nborder_radius=8\ngappih=10\nfocuscolor=0xf2a56bff\nfuture_mango_option=alpha\nbind=SUPER,Return,spawn,foot\n')
config_parser.set_paths(config_path=config, backup_path=Path(sandbox.name)/'backups')
config_parser.APP_SETTINGS_DIR = Path(sandbox.name) / 'settings'
app_settings._SETTINGS_FILE = config_parser.APP_SETTINGS_DIR / 'settings.json'
app_settings._cache = {'theme': 'mango-dark', 'color_scheme': 'dark'}
app = Adw.Application(application_id='io.mangomod.DesignSmoke', flags=Gio.ApplicationFlags.NON_UNIQUE)
errors = []


def activate(app):
    try:
        window = MangoModWindow(application=app)
        import os
        if os.environ.get('MANGOMOD_WIDTH'):
            window.set_default_size(int(os.environ['MANGOMOD_WIDTH']), 860)
        window.present()
        window.show_toast = lambda *args, **kwargs: None
        for page_id, _, _ in SIDEBAR_PAGES:
            window._select_page(page_id)
        from mangomod.pages.animations import BezierEditor
        assert isinstance(window._page_instances['animations']._bezier_editor, BezierEditor)
        # Hidden previews must not keep a timer running.
        assert window._page_instances['animations']._bezier_editor._anim_id is None
        assert window.app_state.doc.serialize() == config.read_text()
        assert not window.app_state.is_dirty
        window._set_language('ar')
        assert window.get_direction() == Gtk.TextDirection.RTL
        assert window._sidebar_rows['appearance'].get_child().get_last_child().get_first_child().get_text() == 'المظهر'
        import os
        if os.environ.get('MANGOMOD_AUDIT_ARABIC'):
            import re
            labels = set()
            def audit(widget):
                values = []
                if isinstance(widget, Gtk.Label):
                    values.append(widget.get_label())
                elif isinstance(widget, Gtk.Button) and widget.get_label():
                    values.append(widget.get_label())
                elif isinstance(widget, (Adw.PreferencesRow, Adw.PreferencesGroup)):
                    values.append(widget.get_title())
                    if hasattr(widget, 'get_subtitle'):
                        values.append(widget.get_subtitle())
                if isinstance(widget, Gtk.Entry):
                    values.append(widget.get_placeholder_text())
                labels.update(v for v in values if v and re.search('[A-Za-z]{3}', v))
                child = widget.get_first_child()
                while child:
                    audit(child)
                    child = child.get_next_sibling()
            audit(window)
            print('ARABIC AUDIT:', *sorted(labels), sep='\n', flush=True)
        window._set_language('en')
        assert window.get_direction() == Gtk.TextDirection.LTR
        assert window._sidebar_rows['appearance'].get_child().get_last_child().get_first_child().get_text() == 'Appearance'
        preferences = window._open_preferences_dialog()
        def find_language_row(widget):
            if isinstance(widget, Adw.ComboRow) and widget.get_title() == 'Language':
                return widget
            child = widget.get_first_child()
            while child:
                found = find_language_row(child)
                if found:
                    return found
                child = child.get_next_sibling()
            return None
        language_row = find_language_row(preferences)
        assert language_row is not None
        def find_theme_dropdown(widget):
            if isinstance(widget, Gtk.DropDown) and widget.get_model().get_n_items() >= 5:
                return widget
            child = widget.get_first_child()
            while child:
                found = find_theme_dropdown(child)
                if found:
                    return found
                child = child.get_next_sibling()
            return None
        theme_dropdown = find_theme_dropdown(preferences)
        assert theme_dropdown is not None
        def find_variant_dropdown(widget):
            if isinstance(widget, Gtk.DropDown) and widget.get_model().get_n_items() == 2:
                return widget
            child = widget.get_first_child()
            while child:
                found = find_variant_dropdown(child)
                if found:
                    return found
                child = child.get_next_sibling()
            return None
        variant_dropdown = find_variant_dropdown(preferences)
        assert variant_dropdown is not None
        language_row.set_selected(2)
        assert window.get_direction() == Gtk.TextDirection.RTL
        assert theme_dropdown.get_model().get_n_items() == 5
        assert theme_dropdown.get_model().get_string(0) == 'مانجو'
        assert theme_dropdown.get_model().get_string(4) == 'رمال الصحراء'
        assert app_settings.get('theme') == 'mango-dark'
        language_row.set_selected(1)
        assert window.get_direction() == Gtk.TextDirection.LTR
        assert theme_dropdown.get_model().get_string(0) == 'Mango'
        assert app_settings.get('theme') == 'mango-dark'
        variant_dropdown.set_selected(0)
        assert app_settings.get('theme') == 'mango-dark'
        assert app_settings.get('color_scheme') == 'light'
        variant_dropdown.set_selected(1)
        assert app_settings.get('color_scheme') == 'dark'
        theme_dropdown.set_selected(2)
        assert app_settings.get('theme') == 'niri-violet'
        assert app_settings.get('color_scheme') == 'dark'
        theme_dropdown.set_selected(0)
        preferences.close()
        window._select_page('appearance')
        page = window._page_instances['appearance']
        page._on_int_change('borderpx', 7)
        assert window.app_state.is_dirty
        assert window._review_btn.get_sensitive()
        window._action_undo()
        assert window.app_state.doc.get_int('borderpx') == 3
        assert not window.app_state.is_dirty
        assert not window._review_btn.get_sensitive()
        window._action_redo()
        assert window.app_state.doc.get_int('borderpx') == 7
        window._search_entry.set_text('motion')
        window._on_sidebar_search(window._search_entry)
        window._activate_search_result(window._search_entry)
        assert window._current_page_id == 'animations'
        window._search_entry.set_text('map_focus_monitor')
        window._activate_search_result(window._search_entry)
        assert window._current_page_id == 'all_settings'
        assert window._page_instances['all_settings']._search.get_text() == 'map_focus_monitor'
        window._page_instances['all_settings']._search.set_text('')
        window._search_entry.set_text('no-section-matches-this')
        window._on_sidebar_search(window._search_entry)
        assert window._search_empty.get_visible()
        window._search_entry.set_text('')
        window._on_sidebar_search(window._search_entry)
        window._select_page('appearance')
        content = window._page_instances['appearance']._content
        sections = content.get_last_child()
        assert isinstance(sections, Gtk.Stack)
        sections.set_visible_child_name('1')
        assert sections.get_visible_child().get_title() == 'Window Gaps'
        window._select_page('all_settings')
        all_settings = window._page_instances['all_settings']
        assert any(row.get_title() == 'future_mango_option' for row in all_settings._unknown_rows)
        all_settings._new_key.set_text('another_future_option')
        all_settings._new_value.set_text('enabled')
        all_settings._add_unknown()
        assert window.app_state.doc.get_setting('another_future_option') == 'enabled'
        window._action_undo()
        assert window.app_state.doc.get_setting('another_future_option') is None
        row = next(row for row, key, _ in all_settings._rows if key == 'borderpx')
        row.set_value(5)
        assert window.app_state.doc.get_int('borderpx') == 5
        window._action_undo()
        assert window.app_state.doc.get_int('borderpx') == 7
        window._select_page('command_builder')
        builder = window._page_instances['command_builder']
        assert not builder._trigger_ready
        assert builder._side_stack.get_visible_child_name() == 'intro'
        assert builder.canvas.get_last_child() is builder._trigger_button
        builder._select_trigger()
        def trigger_labels(widget):
            labels = []
            if isinstance(widget, Gtk.Label):
                labels.append(widget.get_label())
            elif isinstance(widget, Gtk.CheckButton):
                labels.append(widget.get_label())
            if isinstance(widget, Gtk.Expander) and widget.get_child():
                labels.extend(trigger_labels(widget.get_child()))
            child = widget.get_first_child()
            while child:
                labels.extend(trigger_labels(child))
                child = child.get_next_sibling()
            return labels
        inspector_labels = trigger_labels(builder._inspector)
        assert 'Modifiers' in inspector_labels
        assert 'Works while locked' in inspector_labels, inspector_labels
        assert 'Modifiers (raw)' not in inspector_labels
        assert 'Flags (raw)' not in inspector_labels
        builder._confirm_trigger()
        assert builder._trigger_ready
        assert builder._side_stack.get_visible_child_name() == 'library'
        action = builder.add_action('spawn', {'command': 'kitty'})
        assert builder._selected is action
        assert builder._side_stack.get_visible_child_name() == 'attributes'
        assert not builder._apply_btn.get_sensitive()
        assert 'overlaps' in builder._status.get_text()
        builder._conflict_ack.set_active(True)
        assert builder._apply_btn.get_sensitive()
        preview = builder._preview.get_buffer()
        start, end = preview.get_bounds()
        preview_text = preview.get_text(start, end, False)
        assert '+bindc=SUPER,Return,spawn,kitty' in preview_text
        dialog = builder._review_diff()
        assert dialog is not None
        dialog.close()
        builder._apply()
        serialized = window.app_state.doc.serialize()
        assert 'bindc=SUPER,Return,spawn,foot\n' in serialized
        assert 'bindc=SUPER,Return,spawn,kitty\n' in serialized
        window._action_undo()
        serialized = window.app_state.doc.serialize()
        assert 'bind=SUPER,Return,spawn,foot\n' in serialized
        assert 'spawn,kitty' not in serialized
        builder.draft.trigger.modifiers = 'SUPER+code:64'
        builder.draft.trigger.flags = 'lz'
        builder._select_trigger()
        builder._toggle_modifier('CTRL', True)
        builder._toggle_flag('r', True)
        assert builder.draft.trigger.modifiers == 'SUPER+code:64+CTRL'
        assert builder.draft.trigger.flags == 'lzr'
        builder._new_draft()
        dialog = window._review_changes()
        assert dialog is not None
        dialog.close()
        # Exercise the libadwaita 1.4 fallback using real window widgets.
        from types import SimpleNamespace
        from unittest.mock import patch
        from mangomod import ui_compat
        legacy_adw = SimpleNamespace(Window=Adw.Window, AboutWindow=Adw.AboutWindow)
        with patch.object(ui_compat, 'Adw', legacy_adw):
            fallback = window._review_changes()
            assert isinstance(fallback, Adw.Window)
            fallback.close()
            about, present = ui_compat.new_about_window(window)
            present()
            about.close()
        # Legacy custom CSS loads over the redesigned base without migration.
        from mangomod import theme as themes
        theme_dir = Path(sandbox.name) / 'settings' / 'themes'
        theme_dir.mkdir(parents=True)
        with patch.object(config_parser, 'APP_SETTINGS_DIR', theme_dir.parent):
            for source in (Path(__file__).resolve().parents[1] / 'examples').glob('*.css'):
                (theme_dir / source.name).write_text(source.read_text())
                css, error = themes.load_theme_css('user:' + source.stem)
                assert error is None
                assert themes.check_css_parses(css) is None
                window._apply_theme('user:' + source.stem, 'dark')
                import re
                from gi.repository import Gdk
                expected = Gdk.RGBA()
                expected.parse(re.search(r'@define-color\s+mm_accent\s+(#[0-9a-fA-F]+)', css).group(1))
                found, actual = window.get_style_context().lookup_color('mm_accent')
                assert found and actual.equal(expected), source.name
            for source in (Path(__file__).resolve().parents[1] / 'examples').glob('*.css'):
                (theme_dir / source.name).unlink()
        assert len(themes.BUILTIN_THEMES) == 5
        for theme in themes.BUILTIN_THEMES:
            for mode in ('light', 'dark'):
                window._apply_theme(theme, mode)
                english, error = themes.load_theme_css(theme, 'en', mode)
                arabic, arabic_error = themes.load_theme_css(theme, 'ar', mode)
                assert error is None and arabic_error is None and english != arabic
                assert themes.check_css_parses(arabic) is None
                assert themes.check_css_parses(english) is None
                assert themes.theme_name(theme, 'ar') != themes.theme_name(theme, 'en')
        custom_id, error = themes.create_custom_theme('My Test Theme', 'dark', '#20252b', '#323942', '#77bbaa')
        assert error is None and custom_id == 'user:My Test Theme'
        assert (theme_dir / 'My Test Theme.dark.css').is_file()
        assert themes.load_theme_css(custom_id)[1] is None
        after_custom = window._open_preferences_dialog()
        assert find_theme_dropdown(after_custom).get_model().get_n_items() == 6
        theme_picker = find_theme_dropdown(after_custom)
        assert theme_picker.get_list_factory() is not None
        assert theme_picker._mm_open_theme_menu('mango-dark', theme_picker) is None
        context_menu = theme_picker._mm_open_theme_menu(custom_id, theme_picker)
        assert isinstance(context_menu, Gtk.Popover)
        context_buttons = []
        child = context_menu.get_child().get_first_child()
        while child:
            context_buttons.append(child.get_label())
            child = child.get_next_sibling()
        assert context_buttons == ['Create variant…', 'Delete theme']
        context_menu.popdown()
        variant_picker = find_variant_dropdown(after_custom)
        theme_picker.set_selected(5)
        assert app_settings.get('theme') == custom_id
        theme_errors = []
        window.show_toast = lambda message, **kwargs: theme_errors.append(message)
        variant_picker.set_selected(0)
        assert theme_errors == ['This theme has no Light variant. Create it first.'], theme_errors
        window.show_toast = lambda *args, **kwargs: None
        assert app_settings.get('theme') == custom_id
        assert app_settings.get('color_scheme') == 'dark'
        assert variant_picker.get_selected() == 1
        after_custom.close()
        custom_dialog = window._open_custom_themes_dialog()
        def find_widget(widget, wanted):
            if wanted(widget):
                return widget
            child = widget.get_first_child()
            while child:
                found = find_widget(child, wanted)
                if found:
                    return found
                child = child.get_next_sibling()
            return None
        name_entry = find_widget(custom_dialog, lambda w: isinstance(w, Adw.EntryRow) and w.get_title() == 'Theme name')
        create_button = find_widget(custom_dialog, lambda w: isinstance(w, Gtk.Button) and w.get_label() == 'Create and use theme')
        assert name_entry is not None and create_button is not None
        def find_color_pickers(widget):
            found = [widget] if isinstance(widget, Gtk.ColorDialogButton) else []
            child = widget.get_first_child()
            while child:
                found.extend(find_color_pickers(child))
                child = child.get_next_sibling()
            return found
        pickers = find_color_pickers(custom_dialog)
        assert len(pickers) == 3
        selected_color = Gdk.RGBA()
        assert selected_color.parse('#467a9b')
        pickers[2].set_rgba(selected_color)
        name_entry.set_text('From UI')
        create_button.emit('clicked')
        assert app_settings.get('theme') == 'user:From UI'
        assert (theme_dir / 'From UI.light.css').is_file()
        assert '@define-color mm_accent #467a9b;' in (theme_dir / 'From UI.light.css').read_text()
        final_preferences = window._open_preferences_dialog()
        final_picker = find_theme_dropdown(final_preferences)
        assert final_picker.get_model().get_n_items() == 7
        final_picker._mm_delete_theme('user:From UI')
        assert final_picker.get_model().get_n_items() == 6
        assert app_settings.get('theme') in themes.BUILTIN_THEMES
        assert not (theme_dir / 'From UI.light.css').exists()
        final_preferences.close()
        from mangomod.pages.animations import PRESET_CURVES
        window._select_page('animations')
        animations = window._page_instances['animations']
        preset_names = list(PRESET_CURVES)
        assert len(preset_names) == 6
        assert animations._preset_row.get_model().get_n_items() == 7
        assert animations._preset_row.get_selected() == 0
        animations._bezier_editor.set_curve(*PRESET_CURVES['Ease-In'])
        assert animations._bezier_editor._eval_bezier_y(0.5) < 0.5
        animations._bezier_editor.set_curve(*PRESET_CURVES['Ease-Out'])
        assert animations._bezier_editor._eval_bezier_y(0.5) > 0.5
        spring_index = preset_names.index('Spring / Bounce')
        animations._preset_row.set_selected(spring_index)
        assert animations._bezier_editor.get_curve() == PRESET_CURVES['Spring / Bounce']
        assert window.app_state.doc.get_setting('animation_curve_open') == '0.17,0.67,0.83,1.20'
        # A removed preset stays intact when it was already saved in a config.
        retired_curve = (0.18, 0.85, 0.28, 1.00)
        animations._bezier_editor.set_curve(*retired_curve)
        animations._bezier_editor._on_changed(*retired_curve)
        assert animations._preset_row.get_selected() == len(preset_names)
        assert animations._preset_row.get_model().get_string(len(preset_names)) == 'Custom curve'
        assert window.app_state.doc.get_setting('animation_curve_open') == '0.18,0.85,0.28,1.00'
        window._set_language('ar')
        assert animations._preset_row.get_model().get_string(spring_index) == 'نابض وارتداد'
        window._set_language('en')
        import os
        window._select_page(os.environ.get('MANGOMOD_PAGE', 'overview'))
        if os.environ.get('MANGOMOD_DEMO_ACTION'):
            window._select_page('command_builder')
            window._page_instances['command_builder'].add_action('spawn', {'command': 'foot'})
        elif os.environ.get('MANGOMOD_DEMO_TRIGGER'):
            window._select_page('command_builder')
            window._page_instances['command_builder']._select_trigger()
        if os.environ.get('MANGOMOD_LANGUAGE') == 'ar':
            window._set_language('ar')
        screenshot_target = window
        if os.environ.get('MANGOMOD_SCREENSHOT_PREFERENCES'):
            screenshot_target = window._open_preferences_dialog()
        elif os.environ.get('MANGOMOD_SCREENSHOT_CUSTOM_THEMES'):
            screenshot_target = window._open_custom_themes_dialog()
        assert config.read_text().startswith('borderpx=3\n')
        print(f'PASS: {len(SIDEBAR_PAGES)} pages, edit/undo/redo, search, Arabic layout, progressive builder, forward options, review dialogs, custom theme creator, five bilingual theme families with light/dark variants; disk unchanged', flush=True)
        def capture():
            import os
            if os.environ.get("MANGOMOD_SCREENSHOT"):
                try:
                    paintable = Gtk.WidgetPaintable.new(screenshot_target)
                    snapshot = Gtk.Snapshot.new()
                    paintable.snapshot(snapshot, screenshot_target.get_width(), screenshot_target.get_height())
                    node = snapshot.to_node()
                    texture = screenshot_target.get_renderer().render_texture(node, None)
                    texture.save_to_png(os.environ["MANGOMOD_SCREENSHOT"])
                except Exception:
                    import traceback
                    traceback.print_exc()
                    errors.append(RuntimeError("Screenshot failed"))
            app.quit()
            return False
        GLib.timeout_add(4000, capture)
    except Exception as error:
        import traceback
        traceback.print_exc()
        errors.append(error)
        app.quit()


app.connect('activate', activate)
app.run(None)
if errors:
    raise SystemExit(1)
