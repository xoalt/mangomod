"""Read-only installed-Mango checks, including a staged copy of a real config."""
import argparse
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mangomod import app_settings, config_parser as cp, mango_ipc
from mangomod.state import AppState


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=Path.home()/'.config/mango/config.conf')
    args = parser.parse_args()
    version = subprocess.run(['mango', '-v'], capture_output=True, text=True, check=True).stdout.strip()
    report = {'mango': version, 'working_directory': str(mango_ipc.config_working_directory()), 'cases': {}}
    with TemporaryDirectory(prefix='mangomod-system-validation-') as temporary:
        path = Path(temporary)/'config.conf'
        cases = {
            'known_option': 'borderpx=3\n',
            'unknown_scalar': 'mangomod_future_review_option=1\n',
            'unknown_monitor_attribute': 'monitorrule=name:HEADLESS-1,width:1920,height:1080,future_review_option:1\n',
            'accepted_nonnumeric_value': 'borderpx=not-a-number\n',
            'missing_source': f'source={temporary}/does-not-exist.conf\n',
        }
        for name, text in cases.items():
            path.write_text(text)
            direct = subprocess.run(['mango', '-c', str(path), '-p'], capture_output=True, text=True,
                                    cwd=mango_ipc.config_working_directory(), timeout=5)
            raw = mango_ipc._strip_ansi(direct.stdout + direct.stderr)
            ok, message = cp.validate_documents([(cp.parse_config_text(text, path), path)])
            expected = direct.returncode == 0 and '[ERROR]' not in raw
            assert ok == expected, (name, direct.returncode, raw, message)
            report['cases'][name] = {'exit': direct.returncode, 'error_diagnostic': '[ERROR]' in raw,
                                     'mangomod_accepts': ok}
        with patch('mangomod.mango_settings.SETTINGS', []):
            ok, message = cp.validate_documents([(cp.parse_config_text('borderpx=3\n'), path)])
        assert ok and 'Compatibility warning' in message
        report['cases']['accepted_by_mango_unknown_to_catalog'] = {'mangomod_accepts': ok, 'warning_only': True}
        # ./ sources are rooted at the main config, including inside nested
        # sources. Exercise the installed parser and the staged checker.
        nested = Path(temporary)/'nested'
        nested.mkdir()
        (nested/'colors.conf').write_text('source=./colors.conf\n')
        (Path(temporary)/'colors.conf').write_text('bordercolor=0x778899ff\n')
        path.write_text('bordercolor=0x112233ff\nsource=./nested/colors.conf\n')
        direct = subprocess.run(['mango','-c',str(path),'-p'],capture_output=True,text=True,timeout=5)
        assert direct.returncode == 0 and '[ERROR]' not in direct.stderr
        doc, included = cp.load_config_multi(path)
        assert len(included) == 2
        assert cp.validate_documents([(doc,path),*included])[0]
        report['cases']['nested_dot_sources'] = {'exit':direct.returncode,'files_parsed':3,'mangomod_accepts':True}

    target = args.config.expanduser().resolve()
    if target.is_file():
        doc, includes = cp.load_config_multi(target)
        documents = [(doc, target), *includes]
        originals = {path: hashlib.sha256(path.read_bytes()).hexdigest() for _, path in documents if path.is_file()}
        ok, message = cp.validate_documents(documents)
        assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in originals.items())
        report['real_config'] = {'path': str(target), 'files': len(documents), 'accepted': ok,
                                 'unchanged': True, 'diagnostics': message}
        # Exercise the actual save/backup path on an isolated copy of the
        # user's entire tree, including options unknown to our catalog.
        with TemporaryDirectory(prefix='mangomod-real-save-') as temporary:
            root = Path(temporary)
            destinations = {path.resolve(): root/str(i)/'config.conf'
                            for i, (_, path) in enumerate(documents)}
            for document, path in documents:
                copied = deepcopy(document)
                for entry in copied.get_source_entries():
                    source = cp.resolve_include_path(path, entry.path, target)
                    entry.path = str(destinations.get(source.resolve(), source))
                destination = destinations[path.resolve()]
                destination.parent.mkdir(parents=True)
                destination.write_text(copied.serialize())
            with patch.object(cp, 'MANGO_CONFIG', destinations[target]), \
                 patch.object(cp, 'BACKUP_DIR', root/'backups'), \
                 patch.object(app_settings, '_cache', {'auto_backup':True, 'validate_on_save':True, 'hot_reload_on_save':False}):
                state = AppState()
                state.load()
                state.settings_view.set_setting('borderpx', state.settings_view.get_int('borderpx', 3) + 1)
                state.commit('isolated save verification')
                saved, notice = state.save()
                assert saved, notice
                assert not state.is_dirty
                assert cp.validate_documents(state.documents())[0]
                report['real_config']['copied_tree_save'] = notice
                report['real_config']['backup_created'] = any((root/'backups').iterdir())
        assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in originals.items())
    else:
        report['real_config'] = {'path': str(target), 'exists': False}
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
