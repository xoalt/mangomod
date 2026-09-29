"""Config preservation, snapshots and installed-Mango acceptance contracts."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import os
import shutil
import subprocess
import unittest

from mangomod import app_settings, backup, config_parser as cp, mango_ipc, profiles, snapshots, storage, theme
from mangomod.state import AppState
from mangomod.pages.outputs import OutputsPage


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(prefix='mangomod-regression-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.main = self.root / 'mango/config.conf'
        self.main.parent.mkdir()
        self.inc = self.main.parent / 'extra.conf'
        self.inc.write_text('borderpx=9\n')
        self.main.write_text(f'borderpx=3\nsource={self.inc}\n')
        for name, value in {'MANGO_CONFIG': self.main, 'BACKUP_DIR': self.root/'backups',
                            'PROFILES_DIR': self.root/'profiles'}.items():
            self.enterContext(patch.object(cp, name, value))
        self.enterContext(patch.object(app_settings, '_cache', {'auto_backup': False, 'validate_on_save': False, 'hot_reload_on_save': False}))
        self.enterContext(patch.object(mango_ipc, 'is_mango_running', return_value=False))
        self.enterContext(patch.object(mango_ipc, 'has_touchpad', return_value=False))
        self.state = AppState()
        self.state.load()

    def test_included_edit_save_undo_redo(self):
        self.state.include_docs[0][0].set_setting('borderpx', 12)
        self.state.commit('edit include')
        self.assertTrue(self.state.is_dirty)
        entry = self.state.undo.pop_undo()
        self.state.restore_history(entry)
        self.assertFalse(self.state.is_dirty)
        self.assertEqual(self.state.include_docs[0][0].get_int('borderpx'), 9)
        self.state.restore_history(self.state.undo.pop_redo(), redo=True)
        self.assertTrue(self.state.save()[0])
        self.assertEqual(self.inc.read_text(), 'borderpx=12\n')
        self.assertFalse(self.state.is_dirty)

    def test_effective_scalar_edits_its_source(self):
        self.assertEqual(self.state.settings_view.get_int('borderpx'), 9)
        self.state.settings_view.set_setting('borderpx', 11)
        self.assertEqual(self.state.doc.get_int('borderpx'), 3)
        self.assertEqual(self.state.setting_source('borderpx')[1], self.inc)
        self.assertEqual(self.state.include_docs[0][0].get_int('borderpx'), 11)

    def test_loading_clears_history(self):
        self.state.doc.set_setting('borderpx', 11)
        self.state.commit('edit')
        self.state.load()
        self.assertFalse(self.state.undo.can_undo())
        self.assertFalse(self.state.undo.can_redo())

    def test_external_change_blocks_without_overwrite(self):
        self.state.doc.set_setting('borderpx', 12)
        self.state.commit('edit')
        self.inc.write_text('future_external_option=keep\n')
        before = self.main.read_bytes()
        ok, message = self.state.save()
        self.assertFalse(ok)
        self.assertIn('outside MangoMod', message)
        self.assertEqual(self.main.read_bytes(), before)
        self.assertEqual(self.inc.read_text(), 'future_external_option=keep\n')
        self.assertTrue(self.state.is_dirty)

    def test_disk_watch_detects_include_creation_and_ignores_source_alias(self):
        alias = self.inc.with_name('alias.conf')
        alias.symlink_to(self.inc)
        missing = self.inc.with_name('later.conf')
        self.main.write_text(f'source={self.inc}\nsource={alias}\nsource-optional={missing}\n')
        self.state.load()
        self.assertEqual(self.state.disk_changes(), [])
        missing.write_text('border_radius=12\n')
        self.assertEqual(self.state.disk_changes(), [missing])
        self.state.load()
        self.assertEqual(self.state.settings_view.get_int('border_radius'), 12)
        self.assertEqual(self.state.disk_changes(), [])

    def test_monitor_edit_keeps_unknown_attributes_comments_and_order(self):
        text = '# displays\nmonitorrule=name:HDMI-A-1,width:1920,height:1080,future_option:keep # owner\nborderpx=3\n'
        doc = cp.parse_config_text(text)
        page = OutputsPage(SimpleNamespace(app_state=SimpleNamespace(doc=doc)))
        page._commit = lambda *_: None
        page._load_monitors_from_doc()
        page._update_cur('scale', 1.25)
        result = doc.serialize()
        self.assertIn('future_option:keep', result)
        self.assertIn('# owner', result)
        self.assertTrue(result.endswith('borderpx=3\n'))
        self.assertIn('scale:1.25', result)

    def test_unparsed_monitor_value_and_offline_rule_survive_edits(self):
        text = 'monitorrule=name:HDMI-A-1,width:future-size,height:1080,future_option:keep\nmonitorrule=name:OFFLINE,width:1920\n'
        doc = cp.parse_config_text(text)
        page = OutputsPage(SimpleNamespace(app_state=SimpleNamespace(doc=doc)))
        page._commit = lambda *_: None
        page._refresh_ui = lambda *_: None
        page.show_toast = lambda *_: None
        page._load_monitors_from_doc()
        page._update_cur('scale',1.25)
        self.assertIn('width:future-size',doc.serialize())
        with patch.object(mango_ipc,'get_all_monitors',return_value=[{'name':'HDMI-A-1','width':1920,'height':1080}]):
            page._detect_connected_displays()
        self.assertIn('monitorrule=name:OFFLINE,width:1920\n',doc.serialize())

    def test_backup_and_profile_restore_external_same_names(self):
        external = [self.root/'outside-a/keys.conf', self.root/'outside-b/keys.conf']
        for index, path in enumerate(external):
            path.parent.mkdir()
            path.write_text(f'original={index}\n')
        sources = {self.main, *external}
        generation = backup.backup_all_sources(sources)
        profiles.save_profile('External', sources)
        for restore in (lambda: backup.restore_backup(generation), lambda: profiles.load_profile('External')):
            for path in external:
                path.write_text('changed=1\n')
            self.assertTrue(restore())
            for index, path in enumerate(external):
                self.assertEqual(path.read_text(), f'original={index}\n')
            self.assertFalse((self.main.parent/'keys.conf').exists())
        self.assertGreater(len(backup.list_backups()), 1)

    def test_profile_rejects_path_names_and_saves_pending_text(self):
        for name in ('../escape', '/tmp/escape', '..', 'dir/name'):
            with self.assertRaises(ValueError):
                profiles.save_profile(name)
        self.state.doc.set_setting('borderpx', 14)
        profiles.save_profile('Draft', self.state.source_files, self.state.snapshot())
        self.assertEqual(profiles.read_profile('Draft')[self.main], self.state.doc.serialize().encode())
        self.assertTrue((self.main.parent/'presets/Draft/config.conf').is_file())
        self.assertEqual(cp.parse_config_text(self.main.read_text()).get_int('borderpx'), 3)

    def test_failed_multifile_write_rolls_back(self):
        original_main, original_inc = self.main.read_bytes(), self.inc.read_bytes()
        original_replace = os.replace
        count = [0]
        def fail_second(*args):
            count[0] += 1
            if count[0] == 2:
                raise OSError('simulated write failure')
            return original_replace(*args)
        with patch('mangomod.storage.os.replace', side_effect=fail_second):
            with self.assertRaises(OSError):
                storage.write_files({self.main: b'new main', self.inc: b'new include'})
        self.assertEqual(self.main.read_bytes(), original_main)
        self.assertEqual(self.inc.read_bytes(), original_inc)
        self.assertEqual(list(self.main.parent.glob('.mangomod-*')), [])

    def test_save_preserves_symlink_and_permissions(self):
        self.inc.chmod(0o640)
        link = self.root/'link.conf'
        link.symlink_to(self.inc)
        storage.write_files({link: b'changed=1\n'})
        self.assertTrue(link.is_symlink())
        self.assertEqual(self.inc.stat().st_mode & 0o777, 0o640)

    def test_nested_includes_and_cycles(self):
        last = self.main.parent/'last.conf'
        last.write_text(f'source={self.main}\nborder_radius=7\n')
        self.inc.write_text(f'source={last}\n')
        self.state.load()
        self.assertEqual(len(self.state.include_docs), 2)
        self.assertEqual(self.state.settings_view.get_int('border_radius'), 7)

    def test_raw_source_discovery_preserves_pending_includes(self):
        self.state.include_docs[0][0].set_setting('borderpx', 12)
        second = self.root/'second.conf'
        second.write_text('border_radius=9\n')
        self.state.doc.entries.append(cp.SourceEntry(path=str(second)))
        self.state.commit('add source')
        self.assertEqual(len(self.state.include_docs), 2)
        self.assertEqual(self.state.include_docs[0][0].get_int('borderpx'), 12)
        self.assertEqual(self.state.original_text(second), 'border_radius=9\n')
        self.state.restore_history(self.state.undo.pop_undo())
        second.write_text('external=1\n')
        self.assertTrue(self.state.save()[0])  # Unused, undone source is no longer a conflict.

    @unittest.skipUnless(shutil.which('mango'), 'Mango is not installed')
    def test_relative_source_matches_mango_and_missing_is_not_hidden(self):
        doc = cp.parse_config_text('source=extra.conf\n')
        with patch.object(mango_ipc, 'config_working_directory', return_value=self.root):
            self.assertEqual(cp.resolve_include_path(self.main, 'extra.conf'), self.root/'extra.conf')
            ok, message = cp.validate_documents([(doc, self.main)])
            self.assertFalse(ok, message)
            self.assertIn('Failed to open', message)
        with patch.object(mango_ipc, 'config_working_directory', return_value=self.main.parent):
            ok, message = cp.validate_documents([(doc, self.main), (cp.parse_config_text(self.inc.read_text()), self.inc)])
            self.assertTrue(ok, message)
        absolute = cp.parse_config_text(f'source={self.root}/absent.conf\n')
        ok, message = cp.validate_documents([(absolute, self.main)])
        self.assertFalse(ok, message)
        self.assertIn('Failed to open', message)

    def test_invalid_css_reports_parsing_errors(self):
        self.assertIsNotNone(theme.check_css_parses('button { color: not-a-color; }'))
        self.assertIsNone(theme.check_css_parses('button { color: #123456; }'))

    def test_checker_preserves_zero_exit_warning_and_recognizes_error_output(self):
        with patch('mangomod.mango_ipc.shutil.which', return_value='/usr/bin/mango'):
            for stderr, expected in [('warning: future option', True), ('[ERROR]: missing source', False), ('', True)]:
                result = subprocess.CompletedProcess([], 0, '', stderr)
                with patch('mangomod.mango_ipc.subprocess.run', return_value=result):
                    ok, message = mango_ipc.validate_config(str(self.main))
                self.assertEqual(ok, expected)
                if stderr:
                    self.assertIn(stderr, message)

    def test_dot_sources_nested_override_and_edit_owner(self):
        nested = self.main.parent/'nested/colors.conf'
        nested.parent.mkdir()
        self.main.write_text('bordercolor=0x111111ff\nsource=./nested/colors.conf\n')
        nested.write_text('bordercolor=0x222222ff\nsource=./extra.conf\n')
        self.inc.write_text('bordercolor=0x333333ff\n')
        self.state.load()
        self.assertEqual(self.state.settings_view.get_setting('bordercolor'),'0x333333ff')
        self.assertEqual(self.state.setting_source('bordercolor')[1],self.inc)
        self.state.settings_view.set_setting('bordercolor','0x444444ff')
        self.assertEqual(self.state.doc.get_setting('bordercolor'),'0x111111ff')
        self.assertEqual(self.state.include_docs[1][0].get_setting('bordercolor'),'0x444444ff')
        # A later main assignment wins; repeating the source then wins again.
        self.main.write_text(self.main.read_text()+'bordercolor=0x555555ff\n')
        self.state.load()
        self.assertEqual(self.state.settings_view.get_setting('bordercolor'),'0x555555ff')
        self.main.write_text(self.main.read_text()+'source=./extra.conf\n')
        self.state.load()
        self.assertEqual(self.state.settings_view.get_setting('bordercolor'),'0x333333ff')
        if shutil.which('mango'):
            self.assertTrue(cp.validate_documents(self.state.documents())[0])

    def test_failed_reload_restores_all_files_and_keeps_draft(self):
        originals = {p:p.read_bytes() for p in (self.main,self.inc)}
        self.state.doc.set_setting('borderpx',18)
        self.state.settings_view.set_setting('borderpx',21)
        self.state.commit('pending edit')
        self.state._runtime.mango_running = True
        with patch.object(app_settings,'_cache',{'auto_backup':False,'hot_reload_on_save':True}), \
             patch.object(mango_ipc,'reload_config',side_effect=[(False,'reload rejected'),(True,'ok')]) as reload:
            ok,message=self.state.save()
        self.assertFalse(ok)
        self.assertIn('Previous configuration restored',message)
        self.assertEqual(reload.call_count,2)
        self.assertTrue(self.state.is_dirty)
        self.assertEqual(self.state.settings_view.get_int('borderpx'),21)
        self.assertEqual({p:p.read_bytes() for p in originals}, originals)

    def test_rejected_validation_never_replaces_working_config(self):
        original=self.main.read_bytes()
        self.state.doc.set_setting('mangomod_invalid_option',1)
        self.state.commit('invalid draft')
        self.state._runtime.mango_running=True
        with patch.object(app_settings,'_cache',{'hot_reload_on_save':True}), \
             patch.object(cp, 'validate_documents', return_value=(False, 'rejected by compositor')), \
             patch.object(mango_ipc,'reload_config') as reload:
            ok,message=self.state.save(skip_validation=True)
        self.assertFalse(ok)
        self.assertIn('Validation error',message)
        reload.assert_not_called()
        self.assertEqual(self.main.read_bytes(),original)

    def test_preset_switch_uses_active_config_and_source_files(self):
        self.state.settings_view.set_setting('borderpx',24)
        profiles.save_profile('Work',self.state.source_files,self.state.snapshot())
        self.state.load()
        before_path=cp.MANGO_CONFIG
        ok,message=self.state.apply_files(profiles.read_profile('Work'))
        self.assertTrue(ok,message)
        self.assertEqual(cp.MANGO_CONFIG,before_path)
        self.assertEqual(self.state.settings_view.get_int('borderpx'),24)
        self.assertEqual(self.inc.read_text(),'borderpx=24\n')
        self.assertFalse(self.state.is_dirty)
        self.assertTrue(backup.list_backups())

    def test_failed_preset_activation_removes_created_source(self):
        new=self.main.parent/'new.conf'
        originals={p:p.read_bytes() for p in (self.main,self.inc)}
        files={self.main:f'borderpx=8\nsource={new}\n'.encode(), new:b'border_radius=12\n'}
        with patch.object(mango_ipc,'is_mango_running',return_value=True), \
             patch.object(mango_ipc,'get_version',return_value='test'), \
             patch.object(mango_ipc,'reload_config',side_effect=[(False,'rejected'),(True,'ok')]):
            ok,message=self.state.apply_files(files)
        self.assertFalse(ok)
        self.assertIn('restored',message)
        self.assertFalse(new.exists())
        self.assertEqual({p:p.read_bytes() for p in originals},originals)
        self.assertFalse(self.state.is_dirty)

    def test_ipc_error_responses_are_not_success(self):
        for response in ('{"error":"bad config"}', '{"success":false}', '[ERROR]: invalid', ''):
            with patch.object(mango_ipc,'_socket_request',return_value=response):
                self.assertFalse(mango_ipc.reload_config()[0])
        with patch.object(mango_ipc,'_socket_request',return_value='{"success":true}'):
            self.assertTrue(mango_ipc.reload_config()[0])

    @unittest.skipUnless(shutil.which('mango'), 'Mango is not installed')
    def test_installed_mango_decides_acceptance_even_with_older_catalog(self):
        # Model an older MangoMod catalog which has never seen borderpx.
        self.main.write_text('borderpx=3\n')
        with patch('mangomod.mango_settings.SETTINGS', []):
            ok, message = cp.validate_documents([(cp.parse_config_text(self.main.read_text()), self.main)])
        self.assertTrue(ok, message)
        self.assertIn('Compatibility warning', message)
        self.assertNotIn('Validation error', message)
        bad = cp.parse_config_text('mangomod_future_review_option=1\n')
        direct = mango_ipc.validate_config(str(self.main))
        self.assertTrue(direct[0], direct[1])
        ok, message = cp.validate_documents([(bad, self.main)])
        self.assertFalse(ok, message)

    @unittest.skipUnless(shutil.which('mango'), 'Mango is not installed')
    def test_real_validation_checks_pending_include_not_old_disk(self):
        self.state.include_docs[0][0].set_setting('mangomod_future_review_option', 1)
        with patch.object(app_settings, '_cache', {'auto_backup':False,'validate_on_save':True}):
            ok, message = self.state.save()
        self.assertFalse(ok, message)
        self.assertIn(str(self.inc), message)
        self.assertNotIn('mangomod_future', self.inc.read_text())


if __name__ == '__main__':
    unittest.main()
