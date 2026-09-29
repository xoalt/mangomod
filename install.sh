#!/usr/bin/env bash
# Per-user installation; does not modify compositor configuration.
set -euo pipefail

usage() {
    cat <<'HELP'
Usage: ./install.sh [--yes] [--minimal] [--prefix DIR] [--config PATH]

  --yes          Use defaults without prompting
  --minimal      Install only the terminal launcher and application
  --prefix DIR   Installation root (default: ~/.local)
  --config PATH  Default Mango config (default: ~/.config/mango/config.conf)
  --help         Show this help

Install system dependencies first: Python 3.12+, PyGObject, pycairo,
GTK 4.10+, and libadwaita 1.4+. Run without sudo.
HELP
}

INSTALL_PREFIX="$HOME/.local"
MANGO_CONFIG="${MANGOMOD_CONFIG:-$HOME/.config/mango/config.conf}"
ASSUME_YES=0
FULL_INSTALL=1
CONFIG_SET=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --yes) ASSUME_YES=1; shift ;;
        --minimal) FULL_INSTALL=0; shift ;;
        --prefix|--config)
            [ "$#" -ge 2 ] && [ -n "$2" ] || { echo "Missing value for $1" >&2; exit 2; }
            if [ "$1" = --prefix ]; then INSTALL_PREFIX="$2";
            else MANGO_CONFIG="$2"; CONFIG_SET=1; fi
            shift 2 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SRC_DIR/mangomod/__main__.py" ] || { echo 'Application package not found.' >&2; exit 1; }
python3 - <<'PY'
import sys
try:
    if sys.version_info < (3, 12):
        raise RuntimeError('Python 3.12 or newer is required')
    import gi
    import cairo
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw
    if (Gtk.get_major_version(), Gtk.get_minor_version()) < (4, 10):
        raise RuntimeError('GTK 4.10 or newer is required')
    if (Adw.get_major_version(), Adw.get_minor_version()) < (1, 4):
        raise RuntimeError('libadwaita 1.4 or newer is required')
except (ImportError, ValueError, RuntimeError) as error:
    sys.exit(f'Dependency check failed: {error}\nInstall PyGObject, pycairo, GTK4 and libadwaita using your distribution package manager.')
PY

if [ "$ASSUME_YES" -eq 0 ] && [ -t 0 ]; then
    if [ "$FULL_INSTALL" -eq 1 ]; then
        read -r -p 'Include app menu entry and icon? [Y/n] ' choice
        case "$choice" in n|N|no|No) FULL_INSTALL=0 ;; esac
    fi
    if [ "$CONFIG_SET" -eq 0 ]; then
        read -r -p "Mango config [$MANGO_CONFIG]: " choice
        MANGO_CONFIG="${choice:-$MANGO_CONFIG}"
    fi
fi
# Expand a literal ~/ supplied through the prompt or a quoted argument.
INSTALL_PREFIX="${INSTALL_PREFIX/#\~\//$HOME/}"
MANGO_CONFIG="${MANGO_CONFIG/#\~\//$HOME/}"
case "$MANGO_CONFIG" in /*) ;; *) MANGO_CONFIG="$PWD/$MANGO_CONFIG" ;; esac
mkdir -p "$INSTALL_PREFIX"
INSTALL_PREFIX="$(cd "$INSTALL_PREFIX" && pwd)"
BIN_DIR="$INSTALL_PREFIX/bin"
LIB_DIR="$INSTALL_PREFIX/share/mangomod"
APP_DIR="$INSTALL_PREFIX/share/applications"
ICON_DIR="$INSTALL_PREFIX/share/icons/hicolor/scalable/apps"

mkdir -p "$BIN_DIR" "$LIB_DIR"
# Stage the package before replacing the installed copy.
STAGING_DIR="$(mktemp -d "$LIB_DIR/.install-XXXXXXXX")"
trap 'rm -rf -- "$STAGING_DIR"' EXIT
cp -R "$SRC_DIR/mangomod" "$STAGING_DIR/mangomod"
find "$STAGING_DIR/mangomod" -type d -name __pycache__ -exec rm -rf -- {} +
if [ -d "$LIB_DIR/mangomod" ]; then mv "$LIB_DIR/mangomod" "$STAGING_DIR/previous"; fi
if ! mv "$STAGING_DIR/mangomod" "$LIB_DIR/mangomod"; then
    [ ! -d "$STAGING_DIR/previous" ] || mv "$STAGING_DIR/previous" "$LIB_DIR/mangomod"
    exit 1
fi
cp "$SRC_DIR/LICENSE" "$LIB_DIR/LICENSE"
cp -R "$SRC_DIR/LICENSES" "$LIB_DIR/"

# Quote install-time values as shell literals, including spaces and metacharacters.
{
    printf '#!/usr/bin/env bash\n'
    printf 'default_config=%q\n' "$MANGO_CONFIG"
    printf 'library_path=%q\n' "$LIB_DIR"
    printf '%s\n' 'export MANGOMOD_DEFAULT_CONFIG="${MANGOMOD_DEFAULT_CONFIG:-$default_config}"'
    printf '%s\n' 'export PYTHONPATH="$library_path${PYTHONPATH:+:$PYTHONPATH}"'
    printf '%s\n' 'exec python3 -m mangomod "$@"'
} > "$BIN_DIR/mangomod"
chmod +x "$BIN_DIR/mangomod"

if [ "$FULL_INSTALL" -eq 1 ]; then
    mkdir -p "$APP_DIR" "$ICON_DIR"
    # Desktop Exec uses its own quoting rules, not shell quoting.
    python3 - "$BIN_DIR/mangomod" "$APP_DIR/io.github.mangomod.desktop" <<'PY'
from pathlib import Path
import sys
executable = sys.argv[1]
for char, escaped in [('\\', '\\\\\\\\'), ('"', '\\\\"'), ('`', '\\\\`'), ('$', '\\\\$'), ('%', '%%')]:
    executable = executable.replace(char, escaped)
executable = executable.replace('\n', '\\n').replace('\r', '\\r')
Path(sys.argv[2]).write_text(f'''[Desktop Entry]
Name=MangoMod
Comment=Configuration editor for the Mango Wayland compositor
Exec="{executable}"
Icon=io.github.mangomod
Terminal=false
Type=Application
Categories=Settings;DesktopSettings;GTK;
Keywords=mango;wayland;compositor;settings;config;tiling;
StartupNotify=true
''')
PY
    cp "$SRC_DIR/data/mangomod.svg" "$ICON_DIR/io.github.mangomod.svg"
    # Supply symbolic fallbacks for desktops using non-Adwaita icon themes.
    FALLBACK_DIR="$INSTALL_PREFIX/share/icons/hicolor/symbolic/apps"
    mkdir -p "$FALLBACK_DIR"
    for icon in applications-graphics-symbolic applications-multimedia-symbolic \
        document-edit-symbolic document-save-symbolic edit-clear-symbolic \
        edit-redo-symbolic edit-undo-symbolic input-keyboard-symbolic \
        input-mouse-symbolic list-add-symbolic open-menu-symbolic \
        preferences-desktop-apps-symbolic preferences-desktop-appearance-symbolic \
        preferences-desktop-keyboard-shortcuts-symbolic preferences-desktop-symbolic \
        preferences-other-symbolic preferences-system-symbolic system-run-symbolic \
        text-x-generic-symbolic user-trash-symbolic video-display-symbolic \
        view-grid-symbolic view-list-symbolic view-paged-symbolic \
        view-refresh-symbolic view-reveal-symbolic; do
        icon_source="$(find /usr/share/icons/Adwaita/symbolic -name "$icon.svg" -print -quit 2>/dev/null || true)"
        [ -z "$icon_source" ] || cp "$icon_source" "$FALLBACK_DIR/$icon.svg"
    done
    if command -v update-desktop-database >/dev/null; then
        update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
    fi
    if command -v gtk-update-icon-cache >/dev/null; then
        gtk-update-icon-cache -f -t "$INSTALL_PREFIX/share/icons/hicolor" >/dev/null 2>&1 || true
    fi
fi
printf 'Installed MangoMod to %s\n' "$LIB_DIR"
printf 'Run: %s\n' "$BIN_DIR/mangomod"
printf 'Default config: %s\n' "$MANGO_CONFIG"
printf '%s\n' 'Use mangomod -c PATH for a one-time override, or App Settings to remember a different config.'
