"""Install into temporary prefixes; never modify user configuration."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from mangomod import __version__

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_install_launch_and_update_with_literal_paths(self):
        with tempfile.TemporaryDirectory(prefix='mangomod-install-') as directory:
            root = Path(directory)
            prefix = root / 'app space $variable `touch injected` "quoted" %value'
            config = root / 'config $(touch injected) "quoted".conf'
            config.write_text('borderpx=3\n')
            arguments = ['bash', str(ROOT / 'install.sh'), '--yes', '--prefix', str(prefix), '--config', str(config)]
            result = subprocess.run(arguments, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            launcher = prefix / 'bin/mangomod'
            result = subprocess.run([str(launcher), '--version'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f'MangoMod {__version__}', result.stdout)
            desktop = prefix / 'share/applications/io.github.mangomod.desktop'
            self.assertTrue(desktop.is_file())
            self.assertTrue((prefix / 'share/mangomod/LICENSES/NiriMod-MIT.txt').is_file())
            if shutil.which('desktop-file-validate'):
                checked = subprocess.run(['desktop-file-validate', str(desktop)], capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            # Inspect what the launcher actually passes to Python without opening a GUI.
            fakebin = root / 'fakebin'
            fakebin.mkdir()
            fake_python = fakebin / 'python3'
            fake_python.write_text('#!/usr/bin/python3\nimport json, os, sys\nprint(json.dumps([os.environ["MANGOMOD_DEFAULT_CONFIG"], os.environ["PYTHONPATH"], sys.argv[1:]]))\n')
            fake_python.chmod(0o755)
            environment = dict(os.environ, PATH=str(fakebin) + os.pathsep + os.environ['PATH'])
            environment.pop('MANGOMOD_DEFAULT_CONFIG', None)
            result = subprocess.run([str(launcher), '--config', str(config)], env=environment, cwd=root, capture_output=True, text=True, check=True)
            default, library, args = json.loads(result.stdout)
            self.assertEqual(default, str(config))
            self.assertEqual(library.split(os.pathsep)[0], str(prefix / 'share/mangomod'))
            self.assertEqual(args, ['-m', 'mangomod', '--config', str(config)])
            self.assertFalse((root / 'injected').exists())
            self.assertEqual(config.read_text(), 'borderpx=3\n')
            # Reinstall through the minimal path without removing existing integration.
            subprocess.run(arguments + ['--minimal'], cwd=root, capture_output=True, text=True, check=True)
            self.assertTrue(desktop.is_file())
            self.assertEqual(list((prefix / 'share/mangomod').glob('.install-*')), [])

    def test_fresh_minimal_install(self):
        with tempfile.TemporaryDirectory(prefix='mangomod-minimal-') as directory:
            prefix = Path(directory) / 'install'
            subprocess.run(['bash', str(ROOT / 'install.sh'), '--yes', '--minimal', '--prefix', str(prefix)], capture_output=True, text=True, check=True)
            self.assertTrue((prefix / 'bin/mangomod').is_file())
            self.assertFalse((prefix / 'share/applications').exists())
            self.assertFalse((prefix / 'share/icons').exists())


if __name__ == '__main__':
    unittest.main()
