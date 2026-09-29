"""Compatibility contracts for pre-redesign user data; all writes are isolated."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mangomod import app_settings, backup, config_parser as parser, profiles, theme
from mangomod.config_parser import BindingEntry, SettingEntry
from mangomod.state import AppState


LEGACY = (
    '# Existing desktop — keep my formatting\r\n'
    '  borderpx = 2   # thin borders\r\n'
    'borderpx=5\r\n'
    'focuscolor = 0xc9b890ff\r\n'
    'bindl = SUPER, Return, spawn, foot --title=old\r\n'
    'keymode=resize\r\n'
    'bind=NONE,h,resizewin,-10,0\r\n'
    'keymode=default\r\n'
    'mousebind=SUPER,btn_left,moveresize,curmove\r\n'
    'axisbind=SUPER,UP,viewtoleft\r\n'
    'gesturebind=none,left,3,viewtoright\r\n'
    'switchbind=fold,spawn,old-command\r\n'
    'windowrule=appid:old-app,unknown_property:keep\r\n'
    'exec-once = sh -c "echo hello # world"\r\n'
    'env=LEGACY_VALUE,keep,this,too\r\n'
    'source = extras.conf\r\n'
    'source-optional=missing.conf\r\n'
    'old_vendor_option = untouched-value\r\n'
    'opaque legacy syntax without equals\r\n'
    '# final comment without newline'
)


class IsolatedData(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'mango' / 'config.conf'
        self.config.parent.mkdir()
        self.config.write_bytes(LEGACY.encode())
        self.extra = self.config.parent / 'extras.conf'
        self.extra.write_bytes(b'# sourced legacy file\r\nold_option = 1\r\n')
        # These legacy relative includes assume Mango was started here.
        self.enterContext(patch('mangomod.mango_ipc.config_working_directory', return_value=self.config.parent))
        for name, value in {
            'MANGO_CONFIG': self.config,
            'DEFAULT_CONFIG_DIR': self.config.parent,
            'PROFILES_DIR': self.config.parent / 'profiles',
            'BACKUP_DIR': self.root / 'backups',
            'APP_SETTINGS_DIR': self.root / 'settings',
        }.items():
            self.enterContext(patch.object(parser, name, value))
        self.enterContext(patch.object(app_settings, '_cache', None))
        self.enterContext(patch.object(app_settings, '_SETTINGS_FILE', self.root / 'settings' / 'settings.json'))

    def test_legacy_document_round_trips_exactly(self):
        self.assertEqual(parser.parse_config_text(LEGACY).serialize(), LEGACY)

    def test_last_duplicate_setting_remains_effective(self):
        doc = parser.parse_config_text(LEGACY)
        self.assertEqual(doc.get_int('borderpx'), 5)
        doc.set_setting('borderpx', 7)
        self.assertEqual(doc.get_int('borderpx'), 7)
        self.assertEqual(doc.serialize(), LEGACY.replace('borderpx=5\r\n', 'borderpx=7\n'))

    def test_reverted_edit_recovers_original_format(self):
        doc = parser.parse_config_text('  borderpx = 2  # old\r\n')
        doc.set_setting('borderpx', 3)
        doc.set_setting('borderpx', 2)
        self.assertEqual(doc.serialize(), '  borderpx = 2  # old\r\n')

    def test_append_after_unterminated_line(self):
        doc = parser.parse_config_text('old_option=keep')
        doc.set_setting('borderpx', 4)
        self.assertEqual(doc.serialize(), 'old_option=keep\nborderpx=4\n')

    def test_legacy_binding_modes_and_commands(self):
        doc = parser.parse_config_text(LEGACY)
        binds = doc.get_bindings()
        self.assertEqual([(b.bind_type, b.keymode) for b in binds], [('bindl', 'default'), ('bind', 'resize')])
        binds[0].args = 'terminal-new'
        self.assertIn('bindl=SUPER,Return,spawn,terminal-new\n', doc.serialize())
        self.assertIn('switchbind=fold,spawn,old-command\r\n', doc.serialize())
        self.assertIn('old_vendor_option = untouched-value\r\n', doc.serialize())

    def test_quoted_hash_survives_editing_a_command(self):
        doc = parser.parse_config_text('bind=SUPER,H,spawn,sh -c "echo # old" # launcher\n')
        binding = doc.get_bindings()[0]
        self.assertEqual(binding.args, 'sh -c "echo # old"')
        self.assertEqual(binding.inline_comment, 'launcher')
        binding.args = 'sh -c "echo # new"'
        self.assertEqual(doc.serialize(), 'bind=SUPER,H,spawn,sh -c "echo # new" # launcher\n')

    def test_future_bind_prefixed_scalar_remains_editable(self):
        doc = parser.parse_config_text('binding_pref=2\nbindx=SUPER,K,future_action,arg\n')
        self.assertIsInstance(doc.entries[0], SettingEntry)
        self.assertIsInstance(doc.entries[1], BindingEntry)
        doc.set_setting('binding_pref', 3)
        self.assertEqual(doc.serialize(), 'binding_pref=3\nbindx=SUPER,K,future_action,arg\n')

    def test_multifile_load_and_save_keep_untouched_bytes(self):
        doc, includes = parser.load_config_multi()
        self.assertEqual(len(includes), 1)
        self.assertEqual(doc.serialize(), LEGACY)
        ok, _ = parser.save_config(doc, validate=False)
        self.assertTrue(ok)
        self.assertEqual(self.config.read_bytes(), LEGACY.encode())
        self.assertEqual(self.extra.read_bytes(), b'# sourced legacy file\r\nold_option = 1\r\n')

    def test_failed_validation_does_not_replace_existing_config(self):
        doc = parser.parse_config_text('borderpx=99\n', self.config)
        with patch('mangomod.mango_ipc.validate_config', return_value=(False, 'unsupported option')):
            ok, message = parser.save_config(doc)
        self.assertFalse(ok)
        self.assertIn('Validation error', message)
        self.assertEqual(self.config.read_bytes(), LEGACY.encode())
        self.assertEqual(list(self.config.parent.glob('.mangomod_tmp_*')), [])

    def test_old_preferences_and_unknown_keys_survive_updates(self):
        settings = app_settings._SETTINGS_FILE
        settings.parent.mkdir()
        old = {'theme': 'user:nord', 'color_scheme': 'system', 'config_path': '/custom/config.conf', 'legacy_plugin_key': {'a': 1}}
        settings.write_text(json.dumps(old))
        self.assertEqual(app_settings.get('theme'), 'user:nord')
        self.assertTrue(app_settings.get('auto_backup'))
        app_settings.set('backup_limit', 20)
        saved = json.loads(settings.read_text())
        for key, value in old.items():
            self.assertEqual(saved[key], value)

    def test_existing_theme_ids_and_custom_theme_files(self):
        for theme_id in ['mango-dark', 'ripe-paper']:
            css, error = theme.load_theme_css(theme_id)
            self.assertTrue(css)
            self.assertIsNone(error)
        directory = parser.APP_SETTINGS_DIR / 'themes'
        directory.mkdir(parents=True)
        css = '@define-color mm_accent #88c0d0;\n.mm-sidebar-listbox row { padding: 8px; }'
        (directory / 'nord.css').write_text(css)
        self.assertEqual(theme.load_theme_css('user:nord'), (css, None))
        self.assertEqual(theme.theme_swatches('user:nord')[-1], '#88c0d0')
        self.assertIn(('user:nord', 'nord'), theme.available_themes())
        self.assertEqual((directory / 'nord.css').read_text(), css)

    def test_five_theme_families_have_both_modes_without_hiding_custom_css(self):
        self.assertEqual(len(theme.BUILTIN_THEMES), 5)
        for theme_id in theme.BUILTIN_THEMES:
            light, light_error = theme.load_theme_css(theme_id, 'ar', 'light')
            dark, dark_error = theme.load_theme_css(theme_id, 'ar', 'dark')
            self.assertIsNone(light_error)
            self.assertIsNone(dark_error)
            self.assertNotEqual(light, dark)
            self.assertIsNone(theme.check_css_parses(light))
            self.assertIsNone(theme.check_css_parses(dark))
        theme_id, error = theme.create_custom_theme('سمة شخصية', 'light', '#faf8f3', '#ffffff', '#876543')
        self.assertIsNone(error)
        self.assertEqual(theme_id, 'user:سمة شخصية')
        self.assertTrue((parser.APP_SETTINGS_DIR / 'themes' / 'سمة شخصية.light.css').is_file())
        self.assertEqual(theme.load_theme_css(theme_id, mode='dark')[1], 'This theme has no Dark variant. Create it first.')
        self.assertEqual(theme.create_custom_theme('سمة شخصية', 'light', '#faf8f3', '#ffffff', '#876543')[0], None)

    def test_old_single_file_profile_loads_without_migration(self):
        parser.PROFILES_DIR.mkdir()
        (parser.PROFILES_DIR / 'old-desktop.conf').write_bytes(LEGACY.encode())
        self.config.write_text('borderpx=1\n')
        self.assertIn('old-desktop', profiles.list_profiles())
        # This format fixture includes vendor options. Simulate its supporting
        # compositor so this test covers storage compatibility, not schema age.
        with patch.object(parser, 'validate_documents', return_value=(True,'Config syntax OK')), \
             patch('mangomod.mango_ipc.is_mango_running', return_value=False):
            self.assertTrue(profiles.load_profile('old-desktop'))
        self.assertEqual(self.config.read_bytes(), LEGACY.encode())

    def test_old_directory_profile_loads(self):
        directory = parser.PROFILES_DIR / 'multi'
        directory.mkdir(parents=True)
        (directory / 'config.conf').write_text('source=extras.conf\n')
        (directory / 'extras.conf').write_text('old_option=7\n')
        with patch.object(parser, 'validate_documents', return_value=(True,'Config syntax OK')), \
             patch('mangomod.mango_ipc.is_mango_running', return_value=False):
            self.assertTrue(profiles.load_profile('multi'))
        self.assertEqual(self.extra.read_text(), 'old_option=7\n')

    def test_old_backup_generation_names_restore(self):
        for name in ['v1-old', 'gen2-old', '(Gen3)2025-01-01_00-00-00']:
            directory = parser.BACKUP_DIR / name
            directory.mkdir(parents=True)
            (directory / 'config.conf').write_bytes(LEGACY.encode())
        self.assertEqual(len(backup.list_backups()), 3)
        self.config.write_text('changed=1\n')
        self.assertTrue(backup.restore_backup(parser.BACKUP_DIR / 'v1-old'))
        self.assertEqual(self.config.read_bytes(), LEGACY.encode())

    def test_state_open_does_not_mark_legacy_config_dirty(self):
        with patch('mangomod.mango_ipc.is_mango_running', return_value=False), patch('mangomod.mango_ipc.has_touchpad', return_value=False):
            state = AppState()
            state.load()
        self.assertFalse(state.is_dirty)
        self.assertEqual(state.saved_text, LEGACY)
        self.assertEqual(state.doc.serialize(), LEGACY)
        self.assertIn(self.extra, state.source_files)

    def test_config_override_precedence_is_unchanged(self):
        with patch.dict(os.environ, {'MANGOMOD_CONFIG': '/env/config.conf'}), patch.object(app_settings, '_cache', {'config_path': '/saved/config.conf'}):
            self.assertEqual(app_settings.resolve_config_override('/cli/config.conf'), '/cli/config.conf')
            self.assertEqual(app_settings.resolve_config_override(), '/env/config.conf')
            with patch.dict(os.environ, {'MANGOMOD_CONFIG': ''}):
                self.assertEqual(app_settings.resolve_config_override(), '/saved/config.conf')
                app_settings._cache = {}
                self.assertIsNone(app_settings.resolve_config_override())

    def test_legacy_cli_help_and_version_flags(self):
        root = Path(__file__).resolve().parents[1]
        for option in ['-h', '--help', '-v', '--version']:
            result = subprocess.run([sys.executable, '-m', 'mangomod', option], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            if option in ['-h', '--help']:
                self.assertIn('--config', result.stdout)
            else:
                self.assertIn('MangoMod', result.stdout)

    def test_runtime_floor_allows_pre_dialog_libadwaita(self):
        from mangomod.ui_compat import runtime_requirement_error
        self.assertIsNone(runtime_requirement_error((4, 10, 0), (1, 4, 0)))
        self.assertIsNone(runtime_requirement_error((4, 22, 0), (1, 9, 0)))
        self.assertIn('GTK 4.10', runtime_requirement_error((4, 8, 0), (1, 4, 0)))
        self.assertIn('libadwaita 1.4', runtime_requirement_error((4, 10, 0), (1, 3, 0)))


if __name__ == '__main__':
    unittest.main()
