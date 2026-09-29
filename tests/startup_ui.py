"""Exercise the production entry point and renderer using isolated preferences."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mangomod import __main__ as entry, app_settings, config_parser as cp, mango_ipc
from gi.repository import Gio, GLib


def main():
    with TemporaryDirectory(prefix='mangomod-startup-') as directory:
        root = Path(directory)
        config = root/'config.conf'
        config.write_text('borderpx=3\n')
        ticks = []
        result = {}
        def exercise():
            app = Gio.Application.get_default()
            if app is None or app.window is None:
                return True
            window = app.window
            ticks.append(True)
            window.set_default_size(1000 + len(ticks)*20, 760 + len(ticks)*10)
            if len(ticks) == 2:
                window._select_page('raw_config')
            if len(ticks) < 5:
                return True
            result['renderer'] = type(window.get_renderer()).__name__
            result['config'] = str(cp.MANGO_CONFIG)
            for page in window._page_instances.values():
                page.dispose()
            window.destroy()
            app.quit()
            return False
        with patch.object(sys, 'argv', ['mangomod','-c',str(config)]), \
             patch.object(entry, '__app_id__', 'io.mangomod.StartupRegression'), \
             patch.object(app_settings, '_cache', {'theme':'mango-dark','color_scheme':'dark','language':'en'}), \
             patch.object(mango_ipc, 'is_mango_running', return_value=False), \
             patch.object(mango_ipc, 'has_touchpad', return_value=False):
            GLib.timeout_add(300, exercise)
            assert entry.main() == 0
        assert result['config'] == str(config), result
        assert 'GL' in result['renderer'], result
        print(result)


if __name__ == '__main__':
    main()
