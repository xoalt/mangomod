# MangoMod

<div align="center">
  <img src="data/mangomod.svg" width="128" height="128" alt="MangoMod Logo" />
  <h1>MangoMod</h1>

  **GTK4 / Libadwaita configuration editor for the [Mango](https://mangowm.github.io/docs) Wayland compositor — a port of the nirimod project.**

  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://python.org)
  [![GTK4](https://img.shields.io/badge/GTK-4%20%2B%20libadwaita-4A90D9?logo=gnome&logoColor=white)](https://gtk.org)
</div>

<br>

Mango uses an INI-style `config.conf`. MangoMod edits it graphically — monitors,
key bindings, appearance, blur and shadows, animations, layouts, tags, window
rules, autostart, environment — while preserving your comments, formatting, and
custom edits. Writes are staged, validated with `mango -c -p`, backed up, and
hot-reloaded into the running compositor.

---

## Install

Requirements: Python 3.12+, GTK4 + libadwaita, PyGObject, pycairo.

```bash
# Arch
sudo pacman -S python-gobject gtk4 libadwaita python-cairo
# Fedora
sudo dnf install python3-gobject gtk4 libadwaita python3-cairo
# Ubuntu / Debian
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cairo
```

```bash
git clone https://github.com/xoalt/mangomod.git
cd mangomod
./install.sh
```

The installer is self-contained (needs nothing besides the `mangomod/`
folder) and will:

1. Check dependencies, with the exact fix command if anything is missing.
2. Ask which mango config to manage (arrow keys; defaults to
   `~/.config/mango/config.conf`, custom paths welcome).
3. Let you pick Full (launcher + app menu + icons) or Minimal
   (terminal launcher only) installation.
4. Install fallback icons so the UI renders fully on non-Adwaita themes
   (e.g. breeze).

Run with `mangomod`. Config resolution order: `-c PATH` flag →
`MANGOMOD_CONFIG` env → in-app choice → default.

```text
Usage: mangomod [-h] [-c PATH] [-v]

Options:
  -c PATH, --config PATH  Path to custom config.conf file
  -v, --version           Show program's version number and exit
```

---

## Features

- **Overview dashboard** — compositor status, config file, unsaved changes,
  snapshots, and quick jumps. Undo/redo with visible buttons and shortcuts.
- **Outputs & monitors** — layout canvas, resolution, refresh rate, scaling,
  VRR, HDR, rotation, live IPC discovery.
- **Key bindings** — searchable shortcut table with conflict detection, plus
  mouse, wheel, gesture, and switch bindings.
- **Command builder** — visual action blocks with trigger-aware palette and
  per-parameter validation.
- **Appearance & effects** — borders, gaps, full color palette, blur,
  shadows, opacity, animations with Bézier editor.
- **Layouts, tags, rules** — master-stack, scroller, dwindle, per-tag
  layouts, `windowrule`, `layerrule`.
- **System** — autostart manager, environment variables, focus and
  pointer options.
- **Raw editor** — full-text editing with validation, multi-file
  `source=` support, add-file dialog with file picker and drag & drop.
- **Safety** — atomic staged writes, `mango -c -p` validation (with
  save-anyway choice), timestamped backups, profiles, hot-reload.

---

## Custom Themes

Preferences → Appearance ships *Mango Dark* and *Ripe Paper (light)* plus a
System/Light/Dark mode switch, applied live. Make your own: drop any `*.css`
into `~/.config/mangomod/themes/` and select it — see `examples/` for full
ready-made themes (Dracula, Gruvbox, Nord, Catppuccin Mocha, Tokyo Night and
more). Custom files only override what they define; broken files are rejected
with a message instead of breaking the UI.

---

## License

[MIT License](LICENSE).
