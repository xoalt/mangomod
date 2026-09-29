"""Focused GTK regression tests. Uses only temporary configs/preferences."""
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from mangomod import app_settings, backup, config_parser as cp, i18n, mango_ipc, profiles, theme
from mangomod.window import MangoModWindow


def pump(seconds=.1):
    until = time.monotonic() + seconds
    context = GLib.MainContext.default()
    while time.monotonic() < until:
        while context.pending():
            context.iteration(False)
        time.sleep(.005)


def walk(widget):
    yield widget
    if isinstance(widget, Gtk.Expander) and widget.get_child():
        yield from walk(widget.get_child())
    child = widget.get_first_child()
    while child:
        yield from walk(child)
        child = child.get_next_sibling()


class ReviewUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Adw.Application(application_id='io.mangomod.ReviewRegression', flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)

    def setUp(self):
        temp = TemporaryDirectory(prefix='mangomod-review-ui-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.main, self.inc = self.root/'config.conf', self.root/'extra.conf'
        self.main.write_text(f'borderpx=3\nsource={self.inc}\nanimation_curve_open=0.18,0.85,0.28,1\nanimation_curve_close=0,0,1,1\nanimation_curve_move=0.42,0,1,1\nbind=SUPER,Return,spawn,foot\n')
        self.inc.write_text('border_radius=5\n')
        for name, value in {'MANGO_CONFIG':self.main,'BACKUP_DIR':self.root/'backups',
                            'PROFILES_DIR':self.root/'profiles','APP_SETTINGS_DIR':self.root/'settings'}.items():
            self.enterContext(patch.object(cp, name, value))
        self.enterContext(patch.object(app_settings, '_SETTINGS_FILE', self.root/'settings/settings.json'))
        self.enterContext(patch.object(app_settings, '_cache', {'theme':'mango-dark', 'color_scheme':'dark', 'language':'en', 'auto_backup':False, 'validate_on_save':False, 'hot_reload_on_save':False}))
        for function, value in [('is_mango_running',False),('has_touchpad',False),('get_all_tags',[]),('get_all_monitors',[])]:
            self.enterContext(patch.object(mango_ipc, function, return_value=value))
        self.win = MangoModWindow(application=self.app)
        self.win.show_toast = lambda *_args, **_kwargs: None
        self.win.present()
        pump()

    def tearDown(self):
        for page in self.win._page_instances.values():
            page.dispose()
        self.win._allow_close = True
        for window in self.app.get_windows():
            window.destroy()
        pump(.05)

    def page(self, name):
        self.win._select_page(name)
        return self.win._page_instances[name]

    def test_raw_file_switching_revert_and_save(self):
        raw = self.page('raw_config')
        raw._buffer.set_text(self.main.read_text().replace('borderpx=3','borderpx=7'))
        raw._file_dropdown.set_selected(1)
        raw._buffer.set_text('border_radius=11\n')
        raw._file_dropdown.set_selected(0)
        self.assertEqual(self.win.app_state.doc.get_int('borderpx'), 7)
        self.assertEqual(self.win.app_state.include_docs[0][0].get_int('border_radius'), 11)
        raw._file_dropdown.set_selected(1)
        raw._revert_text()
        self.assertTrue(self.win.app_state.is_dirty)
        self.assertEqual(self.win.app_state.include_docs[0][0].get_int('border_radius'), 5)
        self.win._action_undo()
        self.assertEqual(self.win.app_state.include_docs[0][0].get_int('border_radius'), 11)
        self.assertTrue(self.win.save_config_action())
        self.assertIn('borderpx=7',self.main.read_text())
        self.assertEqual(self.inc.read_text(),'border_radius=11\n')

    def test_language_does_not_edit_values_and_translates_hidden_controls(self):
        anim = self.page('animations')
        anim._preset_row.set_selected(1)
        self.win.app_state.doc.set_setting('animation_curve_open', '.42,0,1,1')
        self.win.app_state.commit('curve formatting')
        self.assertTrue(self.win.save_config_action())
        builder = self.page('command_builder')
        builder._select_trigger()
        before = self.win.app_state.snapshot()
        self.win._set_language('ar')
        self.assertEqual(self.win.app_state.snapshot(), before)
        self.assertFalse(self.win.app_state.is_dirty)
        expander = next(w for w in walk(builder._inspector) if isinstance(w,Gtk.Expander))
        expander.set_expanded(True)
        labels = [w.get_label() for w in walk(expander) if isinstance(w,(Gtk.Label,Gtk.CheckButton))]
        self.assertNotIn('Key mode', labels)
        self.assertNotIn('Works while locked', labels)
        self.win.mark_dirty()
        self.assertEqual(self.win._save_btn.get_label(),i18n.translate('Save changes •','ar'))
        self.win.mark_clean()
        self.assertEqual(self.win._save_btn.get_label(),i18n.translate('Save changes','ar'))
        self.win._set_language('en')
        self.assertEqual(self.win.app_state.snapshot(), before)
        self.assertEqual(anim._preset_row.get_selected(),1)

    def test_preview_timer_lifetime_and_independent_curves(self):
        anim = self.page('animations')
        sections = anim._content.get_last_child()
        sections.set_visible_child_name('1')
        pump(.3)
        old_id = anim._bezier_editor._anim_id
        self.assertIsNotNone(old_id)
        anim._preset_row.set_selected(4)
        self.assertEqual(self.win.app_state.doc.get_setting('animation_curve_open'),'0.00,0.00,1.00,1.00')
        self.assertEqual(self.win.app_state.doc.get_setting('animation_curve_move'),'0.42,0,1,1')
        anim._curve_target.set_selected(4)
        anim._preset_row.set_selected(2)
        values = [self.win.app_state.doc.get_setting('animation_curve_'+key) for key in ('open','close','move','tag')]
        self.assertEqual(len(set(values)),1)
        self.win._action_undo()
        self.assertIsNone(GLib.MainContext.default().find_source_by_id(old_id))
        self.page('overview')
        pump(.3)
        self.assertIsNone(self.win._page_instances['animations']._bezier_editor._anim_id)

    def test_builder_draft_survives_undo_and_recovers(self):
        appearance = self.page('appearance')
        appearance._on_int_change('borderpx',7)
        builder = self.page('command_builder')
        builder.add_action('focusid', {'id':'bad-number'})
        self.assertTrue(builder._parameter_widgets['id']._mm_error_label.get_visible())
        builder._edit_value('id','10')
        self.assertFalse(builder._parameter_widgets['id']._mm_error_label.get_visible())
        self.win._action_undo()
        self.assertIs(self.win._page_instances['command_builder'],builder)
        self.assertEqual(builder.draft.actions[0].values['id'],'10')
        builder.save_recovery()
        self.assertTrue(builder._recovery_path().exists())
        self.win._refresh_current_page(reset_builder=True)
        restored = self.win._page_instances['command_builder']
        self.assertTrue(restored._restore_button.get_visible())
        restored._restore_recovery()
        self.assertEqual(restored.draft.actions[0].values['id'],'10')

    def test_close_cancel_and_failed_save_keep_window(self):
        self.page('appearance')._on_int_change('borderpx',7)
        self.win.close()
        self.assertTrue(self.win.get_visible())
        self.win._unsaved_dialog.response('cancel')
        self.assertTrue(self.win.app_state.is_dirty)
        self.win.close()
        with patch.object(self.win.app_state,'save',return_value=(False,'simulated failure')):
            self.win._unsaved_dialog.response('save')
        self.assertTrue(self.win.get_visible())
        self.win.close()
        self.win._unsaved_dialog.response('discard')
        self.assertFalse(self.win.get_visible())

    def test_restore_guard_validation_and_recovery_snapshot(self):
        original = self.main.read_bytes()
        self.page('appearance')._on_int_change('borderpx',7)
        completed = []
        restore = lambda: self.win._restore_files(lambda: {self.main:b'borderpx=19\n'}, lambda: completed.append(True))
        restore()
        self.assertEqual(self.main.read_bytes(),original)
        self.win._unsaved_dialog.response('cancel')
        self.assertEqual(completed,[])
        with patch.object(app_settings,'_cache',{'validate_on_save':True}), patch('mangomod.mango_settings.SETTINGS',[]):
            restore()
            self.win._unsaved_dialog.response('discard')
        self.assertEqual(completed,[True])
        self.assertEqual(self.main.read_bytes(),b'borderpx=19\n')
        self.assertFalse(self.win.app_state.undo.can_undo())
        self.assertEqual(len(backup.list_backups()),1)
        with patch.object(app_settings,'_cache',{'validate_on_save':True}):
            self.win._restore_files(lambda: {self.main:b'mangomod_future_review_option=1\n'}, lambda: completed.append(True))
        self.assertEqual(self.main.read_bytes(),b'borderpx=19\n')
        self.win._restore_dialog.response('cancel')
        self.assertEqual(completed,[True])

    def test_included_scalar_commit_and_source_tooltip(self):
        settings = self.page('all_settings')
        row = next(row for row,key,_ in settings._rows if key=='border_radius')
        self.assertIn(str(self.inc),row.get_tooltip_text())
        row.set_value(13)
        self.assertTrue(self.win.app_state.is_dirty)
        self.assertEqual(self.win.app_state.include_docs[0][0].get_int('border_radius'),13)
        raw = self.page('raw_config')
        raw._file_dropdown.set_selected(1)
        self.assertIn('border_radius=13',raw._buffer.get_text(*raw._buffer.get_bounds(),True))
        raw._buffer.set_text('border_radius=17\n')
        settings = self.page('all_settings')
        row = next(row for row,key,_ in settings._rows if key=='border_radius')
        self.assertEqual(row.get_value(),17)

    def test_theme_options_variants_preview_and_invalid_css(self):
        theme_id,error = theme.create_custom_theme('Review','dark','#20252b','#323942','#77bbaa')
        self.assertIsNone(error)
        dialog = self.win._open_preferences_dialog()
        picker = next(w for w in walk(dialog) if isinstance(w,Gtk.DropDown) and w.get_model().get_n_items()==6)
        picker.set_selected(5)
        options = next(w for w in walk(dialog) if isinstance(w,Gtk.Button) and w.get_tooltip_text()=='Theme options')
        self.assertTrue(options.get_sensitive())
        variant = next(w for w in walk(dialog) if isinstance(w,Adw.ActionRow) and w.get_title()=='Variant')
        self.assertEqual(variant.get_subtitle(),'Available variants: Dark')
        options.emit('clicked')
        popup = next(w for w in walk(options) if isinstance(w,Gtk.Popover))
        self.assertTrue(any(isinstance(w,Gtk.Button) and w.get_label()=='Delete theme' for w in walk(popup)))
        popup.popdown()
        dialog.close()
        creator = self.win._open_custom_themes_dialog()
        colors = [w for w in walk(creator) if isinstance(w,Gtk.ColorDialogButton)]
        contrast = next(w for w in walk(creator) if isinstance(w,Gtk.Label) and w.get_text().startswith('Text contrast:'))
        previous = contrast.get_text()
        color = Gdk.RGBA()
        color.parse('#777777')
        colors[-1].set_rgba(color)
        self.assertNotEqual(contrast.get_text(),previous)
        creator.close()
        (theme.user_themes_dir()/'Broken.dark.css').write_text('button { color: definitely-invalid; }')
        providers = list(self.win._css_providers)
        self.assertFalse(self.win._apply_theme('user:Broken','dark'))
        self.assertEqual(self.win._css_providers,providers)

    def test_external_config_refreshes_controls_and_preserves_dirty_draft(self):
        settings = self.page('all_settings')
        self.inc.write_text('border_radius=27\nfuture_option=original\n')
        pump(1.0)
        settings = self.win._page_instances['all_settings']
        row = next(row for row,key,_ in settings._rows if key=='border_radius')
        self.assertEqual(row.get_value(), 27)
        self.assertEqual(settings._unknown_rows[0].get_title(), 'future_option')
        self.assertFalse(self.win.app_state.is_dirty)
        row.set_value(31)
        self.inc.write_text('border_radius=42\n')
        pump(1.0)
        self.assertEqual(self.win.app_state.settings_view.get_int('border_radius'),31)
        self.assertTrue(self.win._disk_notice.get_revealed())
        self.assertFalse(self.win.app_state.save()[0])
        self.assertEqual(self.inc.read_text(),'border_radius=42\n')

    def test_live_validation_uses_mango_and_warning_does_not_block_save(self):
        raw = self.page('raw_config')
        # A supported option omitted from an older catalog must stay advisory.
        with patch('mangomod.mango_settings.SETTINGS', []), patch.object(app_settings, '_cache',
                {'validate_on_save':True,'auto_backup':False,'hot_reload_on_save':False}):
            raw._buffer.set_text('borderpx=not-a-number\n')
            pump(1.1)
            self.assertIn('Configuration Valid', raw._diagnostics_label.get_text())
            self.assertTrue(raw._diagnostics_label.has_css_class('warning'))
            self.assertTrue(self.win.save_config_action())
        self.assertEqual(self.main.read_text(), 'borderpx=not-a-number\n')
        raw._buffer.set_text('mangomod_future_review_option=1\n')
        pump(1.1)
        self.assertTrue(raw._diagnostics_label.has_css_class('error'))

    def test_controls_keep_new_enum_values_and_out_of_catalog_numbers(self):
        self.win.app_state.doc.set_setting('animation_type_open','future-animation')
        self.win.app_state.doc.set_setting('borderpx','100005')
        settings = self.page('all_settings')
        enum = next(row for row,key,_ in settings._rows if key=='animation_type_open')
        self.assertEqual(enum.get_selected_item().get_string(), 'future-animation')
        number = next(row for row,key,_ in settings._rows if key=='borderpx')
        self.assertEqual(number.get_value(),100005)
        self.win.app_state.doc.set_setting('borderpx','future-width')
        self.win._refresh_current_page()
        settings = self.win._page_instances['all_settings']
        number = next(row for row,key,_ in settings._rows if key=='borderpx')
        self.assertTrue(any(isinstance(w,Gtk.Entry) and w.get_text()=='future-width' for w in walk(number)))

    def test_sourced_color_picker_and_preset_switch(self):
        self.main.write_text('bordercolor=0x112233ff\nsource=./extra.conf\n')
        self.inc.write_text('bordercolor=0x445566ff\n')
        self.win.app_state.load()
        appearance = self.page('appearance')
        row = next(w for w in walk(appearance._content) if isinstance(w,Adw.ActionRow)
                   and w.get_title()=='Unfocused Window Border')
        self.assertEqual(row.get_subtitle(),'0x445566ff')
        self.assertIn(str(self.inc),row.get_tooltip_text())
        picker = next(w for w in walk(row) if isinstance(w,Gtk.ColorDialogButton))
        color = Gdk.RGBA()
        color.parse('#778899')
        picker.set_rgba(color)
        self.assertEqual(self.win.app_state.doc.get_setting('bordercolor'),'0x112233ff')
        self.assertEqual(self.win.app_state.settings_view.get_setting('bordercolor'),'0x778899ff')
        self.assertTrue(self.win.save_config_action())
        profiles.save_profile('Colors',self.win.app_state.source_files,self.win.app_state.snapshot())
        self.inc.write_text('bordercolor=0xaaaaaaff\n')
        self.win.app_state.load()
        dialog = self.win._open_profiles_dialog()
        switch = next(w for w in walk(dialog) if isinstance(w,Gtk.Button) and w.get_label()=='Switch to preset')
        switch.emit('clicked')
        self.assertEqual(cp.MANGO_CONFIG,self.main)
        self.assertEqual(self.win.app_state.settings_view.get_setting('bordercolor'),'0x778899ff')
        self.assertEqual(self.inc.read_text(),'bordercolor=0x778899ff\n')
        self.assertTrue((self.main.parent/'presets/Colors/config.conf').is_file())

    def test_keyboard_add_edit_and_sourced_edit_use_shared_builder(self):
        shortcuts = self.page('bindings')
        original = self.win.app_state.doc.get_bindings()[0]
        shortcuts._open_edit_dialog(original)
        pump()
        builder = self.win._page_instances['command_builder']
        self.assertEqual(self.win._current_page_id,'command_builder')
        self.assertTrue(builder._parameter_widgets['command'].get_mapped())
        self.assertEqual(builder._parameter_widgets['command'].get_text(),'foot')
        builder._edit_value('command','kitty')
        builder._apply()
        self.assertEqual(self.win.app_state.doc.get_bindings()[0].args,'kitty')
        shortcuts = self.page('bindings')
        shortcuts._open_edit_dialog()
        builder = self.win._page_instances['command_builder']
        builder._edit_trigger('key','F12')
        builder._confirm_trigger()
        builder.add_action('spawn',{'command':'foot'})
        builder._apply()
        self.assertEqual(len(self.win.app_state.doc.get_bindings()),2)
        self.assertTrue(self.win.save_config_action())
        self.inc.write_text(self.inc.read_text()+'bind=SUPER,x,spawn,foot\n')
        self.win.app_state.load()
        self.win._refresh_current_page()
        shortcuts = self.page('bindings')
        entry = next(e for e in shortcuts._bindings() if e.key=='x')
        before = self.main.read_bytes()
        shortcuts._open_edit_dialog(entry)
        builder = self.win._page_instances['command_builder']
        builder._edit_value('command','alacritty')
        builder.save_recovery()
        self.win._refresh_current_page(reset_builder=True)
        builder = self.win._page_instances['command_builder']
        builder._restore_recovery()
        self.assertEqual(builder._source_path,self.inc)
        builder._apply()
        self.assertTrue(self.win.save_config_action())
        self.assertEqual(self.main.read_bytes(),before)
        self.assertIn('bind=SUPER,x,spawn,alacritty',self.inc.read_text())

    def test_rule_plus_opens_both_working_forms(self):
        rules = self.page('window_rules')
        for choice, title, field_title, value, save_label, rule_type in [
            ('Window Rule','New Window Rule','Application ID (regex, e.g. firefox, foot)','foot','Add Rule','windowrule'),
            ('Layer Rule','New Layer Shell Rule','Layer Name (e.g. rofi, fuzzel, waybar)','waybar','Add Layer Rule','layerrule')]:
            rules._add_rule_button.popup()
            button = next(w for w in walk(rules._add_rule_button.get_popover()) if isinstance(w,Gtk.Button) and w.get_label()==choice)
            button.emit('clicked')
            pump()
            dialog = next(w for w in self.app.get_windows() if w.get_title()==title)
            field = next(w for w in walk(dialog) if isinstance(w,Adw.EntryRow) and w.get_title()==field_title)
            self.assertTrue(field.get_mapped())
            field.set_text(value)
            next(w for w in walk(dialog) if isinstance(w,Gtk.Button) and w.get_label()==save_label).emit('clicked')
            self.assertEqual(len(self.win.app_state.doc.get_rules(rule_type)),1)

    def test_one_app_menu_and_documented_attribute_certainty(self):
        from mangomod.window import SIDEBAR_PAGES
        for name,_,_ in SIDEBAR_PAGES:
            self.page(name)
        self.assertEqual(len(self.win._menu_buttons),1)
        menu = self.win._menu_buttons[0].get_menu_model()
        labels = [menu.get_item_attribute_value(i,'label',None).get_string() for i in range(menu.get_n_items()-1)]
        self.assertIn('App Settings',labels)
        dialog = self.win._open_preferences_dialog()
        self.assertEqual(dialog.get_title(),'App Settings')
        dialog.close()
        builder = self.page('command_builder')
        builder.add_action('viewprev_have_client')
        self.assertIn('raw_args',builder._parameter_widgets)
        labels = [w.get_text() for w in walk(builder._inspector) if isinstance(w,Gtk.Label)]
        self.assertNotIn('This action has no attributes to configure.',labels)
        builder.add_action('togglefloating')
        labels = [w.get_text() for w in walk(builder._inspector) if isinstance(w,Gtk.Label)]
        self.assertIn('This action has no attributes to configure.',labels)
        self.win._remove_page('window_rules')
        self.win._set_language('ar')
        rules = self.page('window_rules')
        labels = [w.get_label() for w in walk(rules._add_rule_button.get_popover()) if isinstance(w,Gtk.Button)]
        self.assertIn(i18n.translate('Layer Rule','ar'),labels)
        dialog = rules._open_window_rule_dialog()
        self.assertEqual(dialog.get_title(),i18n.translate('New Window Rule','ar'))
        dialog.close()
        self.win._set_language('en')
        labels = [w.get_label() for w in walk(rules._add_rule_button.get_popover()) if isinstance(w,Gtk.Button)]
        self.assertIn('Layer Rule',labels)

    def test_remaining_form_dialogs_have_visible_contents(self):
        for page_id,method in [('startup','_open_add_dialog'),('environment','_open_add_dialog'),('raw_config','_open_add_file_dialog')]:
            page = self.page(page_id)
            dialog = getattr(page,method)()
            pump()
            fields = [w for w in walk(dialog) if isinstance(w,Adw.EntryRow)]
            self.assertTrue(fields, page_id)
            self.assertTrue(fields[0].get_mapped(),page_id)
            dialog.close()


if __name__ == '__main__':
    unittest.main(verbosity=2, warnings='ignore')
