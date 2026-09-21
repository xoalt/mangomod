#!/usr/bin/env bash
# MangoMod self-contained installer.
# Needs NOTHING besides this repo's `mangomod/` package directory:
# the .desktop entry and the icon are embedded below, so `data/` is
# never read. Run from the repo root:  ./install.sh
set -e

# --- Pretty output + arrow-key menus (all ANSI, all optional) ---
if command -v tput >/dev/null && [ -n "${TERM:-}" ]; then
    C_BOLD="$(tput bold 2>/dev/null || true)"; C_DIM="$(tput dim 2>/dev/null || true)"
    C_GREEN="$(tput setaf 2 2>/dev/null || true)"; C_AMBER="$(tput setaf 3 2>/dev/null || true)"
    C_CYAN="$(tput setaf 6 2>/dev/null || true)"; C_RESET="$(tput sgr0 2>/dev/null || true)"
else
    C_BOLD=""; C_DIM=""; C_GREEN=""; C_AMBER=""; C_CYAN=""; C_RESET=""
fi
STEP=0; STEPS=8
step() { STEP=$((STEP+1)); echo "${C_BOLD}${C_CYAN}[$STEP/$STEPS]${C_RESET} $1"; }
ok()   { echo "  ${C_GREEN}✓${C_RESET} $1"; }
note() { echo "  ${C_DIM}$1${C_RESET}"; }

_SPIN_PID=""
spin_start() {
    [ -t 1 ] || return 0
    local frames='|/-\' i=0
    { while :; do printf "\r  ${C_AMBER}%s${C_RESET} %s" "${frames:i++%4:1}" "$1"; sleep 0.08; done; } &
    _SPIN_PID=$!
}
spin_stop() {
    if [ -n "$_SPIN_PID" ]; then kill "$_SPIN_PID" 2>/dev/null || true; wait "$_SPIN_PID" 2>/dev/null || true; _SPIN_PID=""; fi
    [ -t 1 ] && printf "\r%*s\r" 60 "" || true
}
trap 'spin_stop; tput cnorm 2>/dev/null || true' EXIT

# Arrow-key menu. Usage: choose "Prompt" "opt1" "opt2" [...]
# Sets $CHOSEN (0-based). No TTY -> CHOSEN=0, no hang, no error.
CHOSEN=0
choose() {
    local prompt="$1"; shift
    local opts=("$@") sel=0 n=${#opts[@]} key rest i
    CHOSEN=0
    exec 3< /dev/tty 2>/dev/null || return 0
    tput civis 2>/dev/null || true
    while :; do
        echo "$prompt ${C_DIM}(↑/↓ + Enter)${C_RESET}"
        for ((i=0;i<n;i++)); do
            if [ "$i" -eq "$sel" ]; then echo "  ${C_GREEN}❯${C_RESET} ${C_BOLD}${opts[$i]}${C_RESET}";
            else echo "    ${opts[$i]}"; fi
        done
        IFS= read -rsn1 key <&3 2>/dev/null || { sel=0; break; }
        if [ "$key" = $'\e' ]; then
            IFS= read -rsn2 rest <&3 2>/dev/null || { break; }
            case "$rest" in
                "[A") sel=$(( (sel+n-1)%n )) ;;
                "[B") sel=$(( (sel+1)%n )) ;;
            esac
        elif [ -z "$key" ]; then
            break
        fi
        # redraw over the menu we just printed (prompt + n option lines)
        tput cuu $((n+1)) 2>/dev/null || true
        tput ed 2>/dev/null || true
    done
    exec 3<&-
    tput cnorm 2>/dev/null || true
    CHOSEN=$sel
    return 0
}

echo "${C_BOLD}${C_AMBER} __  __                       __  __           _ "
echo "|  \\/  | __ _ _ __   __ _  ___|  \\/  | ___   __| |"
echo "| |\\/| |/ _\` | '_ \\ / _\` |/ _ \\ |\\/| |/ _ \\ / _\` |"
echo "| |  | | (_| | | | | (_| | (_) | |  | | (_) | (_| |"
echo "|_|  |_|\\__,_|_| |_|\\__, |\\___/|_|  |_|\\___/ \\__,_|"
echo "                     |___/  ${C_RESET}${C_DIM}GTK4 configurator for the Mango compositor${C_RESET}"
echo ""

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$SRC_DIR/mangomod"
if [ ! -f "$PKG_DIR/__main__.py" ]; then
    echo "Error: $PKG_DIR/__main__.py not found." >&2
    echo "Run ./install.sh from the repository root." >&2
    exit 1
fi

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
LIB_DIR="$HOME/.local/share/mangomod"

# --- 1. Dependency check (fail fast with the exact fix) ---
step "Checking dependencies"
missing=0
python3 -c "import gi" 2>/dev/null || { echo "MISSING: PyGObject (python gi bindings)"; missing=1; }
python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw" 2>/dev/null || { echo "MISSING: GTK4 / libadwaita bindings"; missing=1; }
python3 -c "import cairo" 2>/dev/null || { echo "MISSING: pycairo"; missing=1; }
if [ "$missing" -ne 0 ]; then
    echo ""
    echo "Install the missing packages first, then re-run ./install.sh:"
    echo "  Arch:   sudo pacman -S python-gobject gtk4 libadwaita python-cairo"
    echo "  Fedora: sudo dnf install python3-gobject gtk4 libadwaita python3-cairo"
    echo "  Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cairo"
    exit 1
fi
echo "Dependencies OK (PyGObject, GTK4+libadwaita, pycairo)."
echo ""

step "Install mode"
choose "How should MangoMod integrate with your system?" \
    "Full — launcher, app menu entry, icons" \
    "Minimal — terminal launcher only"
FULL_INSTALL=$([ "$CHOSEN" -eq 0 ] && echo 1 || echo 0)
echo ""

step "Mango config file"
DEFAULT_CONFIG="$HOME/.config/mango/config.conf"
if [ -n "$MANGOMOD_CONFIG" ]; then
    DEFAULT_CONFIG="$MANGOMOD_CONFIG"
fi
DISPLAY_DEFAULT="${DEFAULT_CONFIG/#$HOME/\~}"
choose "Which mango config should MangoMod manage?" \
    "Use $DISPLAY_DEFAULT" \
    "Enter a custom path"
if [ "$CHOSEN" -eq 1 ]; then
    printf "Custom path [%s]: " "$DISPLAY_DEFAULT"
    read -r MANGO_CONFIG < /dev/tty || MANGO_CONFIG=""
    MANGO_CONFIG="${MANGO_CONFIG:-$DEFAULT_CONFIG}"
    # Tilde-expand a hand-typed ~/... path
    MANGO_CONFIG="${MANGO_CONFIG/#\~/$HOME}"
else
    MANGO_CONFIG="$DEFAULT_CONFIG"
fi
if [ ! -f "$MANGO_CONFIG" ]; then
    note "Note: '$MANGO_CONFIG' does not exist yet."
    note "MangoMod will use it anyway once mango creates it (or pass -c PATH later)."
else
    ok "Using mango config: $MANGO_CONFIG"
fi
echo ""

# --- 3. Install a private copy of the package (no repo needed afterwards) ---
step "Copying application files"
mkdir -p "$BIN_DIR" "$APP_DIR" "$ICON_DIR" "$LIB_DIR"
mkdir -p "$HOME/.config/mangomod/themes"
rm -rf "$LIB_DIR/mangomod"
spin_start "Copying package"
cp -r "$PKG_DIR" "$LIB_DIR/mangomod"
find "$LIB_DIR/mangomod" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
spin_stop
ok "Package installed to $LIB_DIR/mangomod"

# --- 4. Launcher wrapper (install-time choice baked in, still overridable) ---
step "Installing launcher"
cat > "$BIN_DIR/mangomod" << EOF
#!/usr/bin/env bash
# Generated by MangoMod install.sh — do not hand-edit; re-run ./install.sh.
export MANGOMOD_CONFIG="\${MANGOMOD_CONFIG:-$MANGO_CONFIG}"
PYTHONPATH="\$HOME/.local/share/mangomod:\$PYTHONPATH" exec python3 -m mangomod "\$@"
EOF
chmod +x "$BIN_DIR/mangomod"
ok "Launcher installed to $BIN_DIR/mangomod (config: $MANGO_CONFIG)"

if [ "$FULL_INSTALL" -eq 1 ]; then
step "Desktop integration"
# --- 5. Desktop entry (embedded — no data/ folder needed) ---
cat > "$APP_DIR/io.github.mangomod.desktop" << 'EOF'
[Desktop Entry]
Name=MangoMod
Comment=Configuration Editor for the Mango Wayland Compositor
Exec=mangomod
Icon=io.github.mangomod
Terminal=false
Type=Application
Categories=Settings;DesktopSettings;GTK;
Keywords=mango;wayland;compositor;settings;config;tiling;
StartupNotify=true
EOF

# --- 6. Icon (embedded — no data/ folder needed) ---
cat > "$ICON_DIR/io.github.mangomod.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <linearGradient id="mangoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffb703" />
      <stop offset="50%" stop-color="#fb8500" />
      <stop offset="100%" stop-color="#d90429" />
    </linearGradient>
    <linearGradient id="leafGrad" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#2d6a4f" />
      <stop offset="100%" stop-color="#52b788" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.35" />
    </filter>
  </defs>

  <!-- Mango fruit base -->
  <path d="M 64,18 C 96,18 116,46 112,80 C 108,110 82,120 54,120 C 30,120 16,102 16,74 C 16,40 38,18 64,18 Z"
        fill="url(#mangoGrad)" filter="url(#shadow)" />

  <!-- Leaf -->
  <path d="M 64,18 C 64,4 82,2 90,8 C 92,18 78,22 64,18 Z"
        fill="url(#leafGrad)" />

  <!-- Tiling Grid Windows Overlay -->
  <rect x="36" y="44" width="24" height="48" rx="4" fill="#ffffff" fill-opacity="0.25" stroke="#ffffff" stroke-width="2" stroke-opacity="0.7" />
  <rect x="66" y="44" width="30" height="22" rx="4" fill="#ffffff" fill-opacity="0.35" stroke="#ffffff" stroke-width="2" stroke-opacity="0.8" />
  <rect x="66" y="70" width="30" height="22" rx="4" fill="#ffffff" fill-opacity="0.25" stroke="#ffffff" stroke-width="2" stroke-opacity="0.7" />
</svg>
EOF
ok "Desktop entry installed to $APP_DIR/io.github.mangomod.desktop"
ok "Icon installed to $ICON_DIR/io.github.mangomod.svg"
fi

step "Fallback icons"

# --- 6b. Symbolic fallback icons (fixes missing icons on non-Adwaita themes) ---
# GTK only falls back to hicolor, never to Adwaita — so on themes like breeze
# several symbolic names have no match and render as "missing image".
# Copy them from the system Adwaita set (guaranteed present: libadwaita
# hard-depends on adwaita-icon-theme) into hicolor, which is always consulted.
FALLBACK_DIR="$HOME/.local/share/icons/hicolor/symbolic/apps"
mkdir -p "$FALLBACK_DIR"
for _icon in applications-graphics-symbolic applications-multimedia-symbolic \
    document-edit-symbolic document-save-symbolic edit-clear-symbolic \
    edit-redo-symbolic edit-undo-symbolic input-keyboard-symbolic \
    input-mouse-symbolic list-add-symbolic open-menu-symbolic \
    preferences-desktop-apps-symbolic preferences-desktop-appearance-symbolic \
    preferences-desktop-keyboard-shortcuts-symbolic preferences-desktop-symbolic \
    preferences-other-symbolic preferences-system-symbolic system-run-symbolic \
    text-x-generic-symbolic user-trash-symbolic video-display-symbolic \
    view-grid-symbolic view-list-symbolic view-paged-symbolic \
    view-refresh-symbolic view-reveal-symbolic; do
    _src=$(find /usr/share/icons/Adwaita/symbolic -name "$_icon.svg" 2>/dev/null | head -1)
    if [ -n "$_src" ]; then
        cp -f "$_src" "$FALLBACK_DIR/$_icon.svg"
    else
        note "System Adwaita lacks $_icon.svg — skipping."
    fi
done

# --- 7. Best-effort cache refresh (never fatal) ---
step "Finalizing"
command -v update-desktop-database >/dev/null && update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

echo ""
ok "Package installed to $LIB_DIR/mangomod"
ok "Launcher installed to $BIN_DIR/mangomod (config: $MANGO_CONFIG)"
if [ "$FULL_INSTALL" -eq 1 ]; then
    ok "Desktop entry + icon installed"
else
    note "Minimal mode: skipped app-menu entry and icon (terminal launcher only)"
fi
echo ""
echo "Run 'mangomod' from a terminal or your app launcher."
echo "Override the config for one run with:  MANGOMOD_CONFIG=/path/to/config.conf mangomod"
echo "or permanently with:                   mangomod -c /path/to/config.conf"
