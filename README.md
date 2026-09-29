# MangoMod

<img src="data/mangomod.svg" width="96" height="96" alt="MangoMod logo">

**A graphical configuration editor for the Mango Wayland compositor, ported from [NiriMod](https://github.com/srinivasr/nirimod).**

Edit Mango settings visually while keeping your text configuration intact. Built with Python, GTK4, and libadwaita; NiriMod is not required to run it.

## Features

- Visual settings for monitors, layouts, input, effects, startup commands, and window and layer rules.
- A block-based shortcut builder with the selected command's attributes on the side.
- Live animation previews, editable Bézier curves, and six curve presets.
- English and Arabic layouts, five light/dark theme families, and custom themes with color pickers.
- Source-aware config editing, change review, undo, backups, and presets using one active `config.conf`.
- Validation through the installed Mango, preserving unfamiliar options and warning when accepted options are outside the editor's catalog.

## Install

You need Linux with Python **3.12+**, GTK **4.10+**, libadwaita **1.4+**, PyGObject, and pycairo. Install [Mango](https://github.com/mangowm/mango) separately for native config validation and live reload.

### 1. Install the dependencies

Open a terminal and run the commands for **your distribution only**:

<details>
<summary>Arch Linux</summary>

```sh
sudo pacman -S --needed git python python-gobject python-cairo gtk4 libadwaita
```

</details>

<details>
<summary>Fedora</summary>

```sh
sudo dnf install git python3 python3-gobject python3-cairo gtk4 libadwaita
```

</details>

<details>
<summary>Ubuntu 24.04 or newer</summary>

```sh
sudo apt update
sudo apt install git python3 python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

</details>

For another distribution, install equivalent packages meeting the minimum versions above. The installer checks these before copying files. See the [PyGObject installation guide](https://pygobject.gnome.org/getting_started.html) for distribution-specific GTK bindings.

### 2. Download MangoMod

Run these commands in the folder where you want to keep the source:

```sh
git clone https://github.com/xoalt/mangomod.git
cd mangomod
```

`git clone` downloads the project; `cd mangomod` enters its folder. You do not need a GitHub account.

### 3. Install MangoMod

```sh
./install.sh
```

Follow the prompts to select your config and whether to add an application menu entry. Run this command as your normal user, **without sudo**. The app installs under `~/.local`; your Mango configuration is not replaced.

### 4. Open MangoMod

Launch **MangoMod** from your application menu, or run:

```sh
~/.local/bin/mangomod
```

If `~/.local/bin` is on your `PATH`, you can simply type `mangomod`.

The default configuration is `~/.config/mango/config.conf`. To open another file:

```sh
~/.local/bin/mangomod -c /path/to/config.conf
```

You can also remember a config path in **App Settings**.

Prefer downloading in your browser? Choose **Code → Download ZIP** on this repository's GitHub page, extract it, open a terminal in that folder, and run `bash install.sh` after installing the dependencies above.

For a minimal install, a custom installation folder, or running from source, see [installation options](docs/DOCUMENTATION.md#installation-options).

## Getting started

Open a settings page, make your changes, then use **Review changes** before saving. The app menu provides **App Settings**, **Presets**, and **Backups**. Add or edit a shortcut to open the command builder; selecting a block displays its attributes.

## Documentation

- [User guide](docs/DOCUMENTATION.md) — settings, shortcuts, themes, presets, compatibility, and recovery.
- [Development and testing](tests/README.md) — automated checks and building packages.

## Credits and license

Application code is under the [MIT license](LICENSE).

**NiriMod** provided the UI reference at revision `e851734`. It is MIT licensed, copyright © 2026 srinivasr. Its original notice is preserved in [LICENSES/NiriMod-MIT.txt](LICENSES/NiriMod-MIT.txt).

**Mango reference documentation** in `docs/upstream-mango/` comes from commit `f014971000ea1e6124c6bb120b8aa4062460d2e4` and supports the catalog and documentation checks. See its [origin note](docs/upstream-mango/README.mangomod.md) and [upstream GPL-3.0-or-later license notice](docs/upstream-mango/LICENSE). The application's MIT license does not replace those terms.

**GTK, libadwaita, PyGObject, and pycairo** are installed separately and retain their respective licenses. Icons copied from the system's Adwaita theme remain upstream assets.
