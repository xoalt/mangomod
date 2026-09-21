"""MangoMod application entry point."""

from __future__ import annotations

import argparse
import os
import sys

try:
    import gi
except ModuleNotFoundError:
    print(
        "\033[31mError: Could not find Python GObject bindings (PyGObject).\033[0m",
        file=sys.stderr,
    )
    print(
        "This application requires system libraries to interface with GTK4 and Libadwaita.",
        file=sys.stderr,
    )
    print("\nPlease install the required packages for your distribution:", file=sys.stderr)
    print("  \033[1mArch:\033[0m   sudo pacman -S python-gobject gtk4 libadwaita python-cairo", file=sys.stderr)
    print("  \033[1mFedora:\033[0m sudo dnf install python3-gobject gtk4 libadwaita python3-cairo", file=sys.stderr)
    print("  \033[1mUbuntu:\033[0m sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cairo", file=sys.stderr)
    sys.exit(1)

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib

from mangomod import __app_id__, __version__, config_parser
from mangomod.window import MangoModWindow


class MangoModApp(Adw.Application):
    def __init__(self, config_override: str | None = None):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.config_override = config_override
        self.window: MangoModWindow | None = None

    def do_activate(self):
        if not self.window:
            # Precedence: -c flag > MANGOMOD_CONFIG env (installer choice) >
            # stored in-app choice ("Set as Main") > parser default.
            from mangomod import app_settings

            override = (
                self.config_override
                or os.environ.get("MANGOMOD_CONFIG")
                or app_settings.get("config_path")
            )
            if override:
                config_parser.set_paths(config_path=override)
            self.window = MangoModWindow(application=self)
        self.window.present()


def main():
    parser = argparse.ArgumentParser(
        prog="mangomod",
        description="A polished GTK4/Libadwaita GUI configurator for the Mango Wayland compositor.",
    )
    parser.add_argument(
        "-c", "--config",
        metavar="PATH",
        help="Path to custom config.conf file",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"MangoMod {__version__}",
    )

    args = parser.parse_args()

    app = MangoModApp(config_override=args.config)
    try:
        return app.run(None)
    except KeyboardInterrupt:
        # Meta+Q / Ctrl+C during shutdown: PyGObject's SIGINT fallback
        # raises KeyboardInterrupt inside app.run() teardown. The app is
        # already quitting — exit quietly instead of dumping a traceback.
        return 0


if __name__ == "__main__":
    sys.exit(main())
