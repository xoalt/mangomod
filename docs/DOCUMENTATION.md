# MangoMod — User Guide

This guide covers settings, shortcuts, themes, presets, and configuration recovery. For setup instructions and upstream credits, see the [README](../README.md).

## Installation options

Use these options with `./install.sh` from the source directory:

| Option | Effect |
| --- | --- |
| `--yes` | Use defaults without prompting |
| `--minimal` | Install the application and terminal launcher only |
| `--prefix DIR` | Use another installation root |
| `--config PATH` | Set the launcher's default config path |
| `--help` | Show installer help |

The installer copies the application without replacing your Mango config, presets, or MangoMod preferences. Minimal mode skips desktop integration; it does not uninstall a desktop entry already on the system.

To run directly from source without installing:

```sh
python3 -m mangomod
```

Python wheels contain the application and licenses. Install the system dependencies listed in the [README](../README.md#install) separately; wheels do not create a desktop menu entry.

## Selecting a configuration

The default is `~/.config/mango/config.conf`.

```sh
mangomod -c /path/to/config.conf
mangomod --version
```

Config selection follows this order:

1. The `-c` or `--config` command-line argument.
2. The `MANGOMOD_CONFIG` environment variable.
3. The config remembered in App Settings.
4. The launcher's `MANGOMOD_DEFAULT_CONFIG` value.
5. The default path.

Opening another path does not change which file the running compositor uses. For live editing, select the compositor's active config.

## Finding settings

Navigation groups settings for the workspace, interaction, and system. Use **Ctrl+K** to find a section. The overview shows the active file, compositor status, and pending edits. **All Settings** provides a searchable catalog and a place to edit additional options.

The app menu contains **App Settings**, **Presets**, **Backups**, shortcut help, and About. App Settings controls language, theme, config selection, and save behavior.

## Editing and saving

Graphical controls and the raw editor operate on the same editing session. Change a setting, inspect **Review changes**, then save. Undo and redo apply to configuration edits; switching to another config starts a new undo history.

The raw editor exposes the main config and included files. Validation runs after a brief pause in typing. While the window is visible, external file changes are checked periodically. Clean documents refresh automatically; unsaved edits are retained and a conflict is reported instead of silently replacing them.

Saving stages all changed documents and checks them before replacing files. Unknown options, comments, spacing, and line endings remain intact on untouched lines. Edited entries are serialized again. File modes and symlinks are preserved. Each file replacement is atomic, but a multi-file save is not a single atomic operation across a power failure.

Closing or replacing a config with unsaved edits offers save, discard, or cancel. If another program changes a file while you are editing it, review the conflict and reload it before retrying.

## Sources and effective values

MangoMod parses `source=` files recursively. For scalar settings, the last effective occurrence in source order supplies the value shown in the UI. Editing that value updates its owning file. Appearance colors and All Settings expose the source path in tooltips.

For example:

```ini
borderpx=2
source=./appearance.conf
```

If `appearance.conf` sets `borderpx=4`, the editor displays **4** and edits that occurrence.

Paths beginning with `./` resolve from the main config's directory, including nested sources. Bare relative paths follow the running Mango process's working directory, or MangoMod's working directory when Mango is not running. Files added through the UI use absolute paths. Missing sources are reported rather than silently discarded.

This scalar precedence rule does not mean every repeated directive is a scalar override: bindings, rules, and startup commands retain their own entries.

## Shortcuts and command builder

**Add shortcut** and **Edit Shortcut** open the same builder. It supports keyboard, mouse, scroll, gesture, and lid bindings.

Start with the trigger, then add action blocks. The sequence grows as you enter commands. Select a block to inspect its attributes in the side panel. Modifier buttons and flag controls avoid duplicate raw inputs for the same values. Existing shortcuts keep their source-file ownership when edited.

A command is described as having no attributes only when the bundled Mango documentation explicitly confirms that. Unconfirmed commands keep an editable arguments field. Familiar commands receive structured controls; native Mango validation remains the final compatibility check.

Unapplied drafts are stored separately for each main config under `~/.config/mangomod/drafts/`. **Recover draft** restores a draft without automatically applying commands. Applying a builder change still requires saving the configuration.

## Rules and animation previews

The **+** menu on Window & Layer Rules offers both rule types.

The animation editor previews Bézier curves and provides six distinct presets. Curves can target opening, closing, movement, tag switching, or an explicit All selection. Previews stop their timers when hidden. These are illustrative previews; the compositor controls actual window motion.

## Themes and languages

Choose System, English, or Arabic in App Settings. Arabic uses a right-to-left interface. Config syntax, command names, key symbols, and raw text retain their technical spelling and left-to-right presentation where needed.

The theme selector starts with exactly five built-in families:

- Mango
- Ripe Paper
- Niri Violet
- Oasis Teal
- Sahara Sand

Each family has separate light and dark palettes. The mode is selected separately, so variants do not double the number of entries in the theme selector. Built-in names, accents, and typography adapt to the selected language.

**Create theme** opens color pickers and a live sample. Saving adds your theme to the same selector. Create its dark and light variants separately. Selecting a variant that has not been created reports an error and keeps the current theme.

Right-click a custom theme, or use its options button, to manage its variants or delete it. Built-in themes cannot be deleted. Custom CSS is supported under `~/.config/mangomod/themes/`. Files named `Name.css` appear as dark variants; explicit variants use `Name.dark.css` and `Name.light.css`. Invalid CSS is rejected on selection. The creator's contrast indicator checks its sample text, not every possible custom CSS rule.

## Presets and backups

Use **Presets** to save a named setup or switch to one. Presets are stored beside the active config:

```text
~/.config/mango/
├── config.conf
└── presets/
    └── preset-name/
        ├── config.conf
        └── ...captured sources and path manifest
```

Switching copies the selected setup into the active `config.conf` and its captured sources. The compositor continues using its normal active config path. Presets can capture external source files; they are local snapshots, so inspect stored paths before moving them to another system.

**Backups** provides recovery snapshots. Live saves and preset activation always keep a recovery backup. Snapshots use a path manifest to record captured source files. A snapshot without a path manifest cannot reconstruct unrecorded external paths.

## Backward and forward compatibility

MangoMod works with your Mango configuration in place, including custom paths and source files. You can select its config through the command line, environment variables, or App Settings.

Unknown config options and commands are preserved. If the installed Mango accepts a setting that the app's catalog does not recognize, MangoMod reports a compatibility warning and allows the save. New names and values can be edited through **All Settings → Other config options** or the raw editor.

The native check uses `mango -c FILE -p`. A nonzero result or an explicit compositor error diagnostic blocks activation, even if the process also reports a successful exit. Familiarity to the editor alone is not a reason to reject an option accepted by Mango.

Live activation always validates. Offline save validation can be configured in App Settings. If Mango is unavailable, native support cannot be confirmed; the app reports that limitation rather than claiming the config was accepted by the compositor.

Preserving an option does not guarantee that every Mango version supports it. The bundled reference catalog is pinned to a documented upstream revision; newer settings may initially have raw controls instead of specialized UI.

## Recovery after rejection

A failed staged check leaves active files unchanged and retains the draft for correction. If a check or reload fails after writing, MangoMod restores the previous files, removes newly created files where appropriate, and attempts to reload the restored config. Recovery failures are reported explicitly.

Some Mango versions acknowledge receipt of a reload request without returning complete parser status. MangoMod also performs native validation, but cannot guarantee detection of every runtime failure from that acknowledgement alone. Backups remain useful even with validation enabled.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Application does not start | Required Python, GTK, libadwaita, PyGObject, and pycairo versions |
| Save is rejected | Native diagnostic, missing source files, permissions, or an external-edit conflict |
| An unfamiliar setting has a warning | Whether installed Mango accepts it; warnings alone do not mean invalid syntax |
| Changes do not affect the desktop | Selected config path, live reload setting, and running Mango session |
| A custom theme cannot switch modes | Create the missing light or dark variant |
| Rendering problems | Try `GSK_RENDERER=cairo mangomod`; explicit renderer overrides are respected |

MangoMod chooses an OpenGL renderer by default and uses libadwaita's style manager for light/dark appearance. It does not change the desktop's global GTK preferences.
