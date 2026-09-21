"""Docs-backed catalog of Mangowm dispatchers, layouts and syntax helpers.

Every ``bind=MOD,KEY,COMMAND,PARAMS`` dispatcher from the official docs
(https://mangowm.github.io/docs) lives here with its parameter slots, so the
"add something new" flows and the Scratch-style Command Builder always offer
the complete set of possible options.
"""

from __future__ import annotations

from typing import Any, Iterator

# ---------------------------------------------------------------------------
# Category visual mapping
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, str] = {
    "launch": "Launch Programs",
    "window": "Window Management",
    "focus": "Focus & Movement",
    "group": "Window Groups",
    "tags": "Tags & Workspaces",
    "monitor": "Monitors & Displays",
    "layout": "Layouts",
    "system": "System",
    "mouse": "Mouse Actions",
}

BLOCK_CSS = {
    "launch": "mm-block-launch",
    "window": "mm-block-window",
    "focus": "mm-block-focus",
    "group": "mm-block-group",
    "tags": "mm-block-tags",
    "monitor": "mm-block-monitor",
    "layout": "mm-block-layout",
    "system": "mm-block-system",
    "mouse": "mm-block-mouse",
}

# ---------------------------------------------------------------------------
# Param factories
# ---------------------------------------------------------------------------


def _enum(name: str, options: list[str], label: str | None = None, default: str | None = None, hint: str = ""):
    return {
        "name": name,
        "label": label or name,
        "type": "enum",
        "options": list(options),
        "default": default if default is not None else (options[0] if options else ""),
        "hint": hint,
    }


def _str(name: str, label: str | None = None, default: str = "", hint: str = ""):
    return {"name": name, "label": label or name, "type": "str", "options": [], "default": default, "hint": hint}


def _int(name: str, label: str | None = None, default: str = "0", hint: str = ""):
    return {"name": name, "label": label or name, "type": "int", "options": [], "default": default, "hint": hint}


def _float(name: str, label: str | None = None, default: str = "0.0", hint: str = ""):
    return {"name": name, "label": label or name, "type": "float", "options": [], "default": default, "hint": hint}


_DIRS = ["left", "right", "up", "down"]
_LAYOUT_NAMES = [
    "tile", "scroller", "monocle", "grid", "deck",
    "center_tile", "vertical_tile", "right_tile",
    "vertical_scroller", "vertical_grid", "vertical_deck",
    "dwindle", "fair", "vertical_fair",
]

MODIFIERS = ["SUPER", "CTRL", "ALT", "SHIFT", "NONE"]
BIND_FLAGS = ["l", "s", "r", "p", "c"]

# ---------------------------------------------------------------------------
# Dispatchers catalog
# ---------------------------------------------------------------------------

DISPATCHERS: dict[str, list[dict[str, Any]]] = {
    "launch": [
        {"cmd": "spawn", "desc": "Execute a program or shell command",
         "params": [_str("command", "Command", "foot")]},
        {"cmd": "spawn_shell", "desc": "Run a shell command (supports pipes)",
         "params": [_str("command", "Shell command", "")]},
        {"cmd": "spawn_on_empty", "desc": "Launch an app on an empty tag",
         "params": [_str("command", "Command", ""), _str("tags", "Tag mask", "0", "e.g. 2 or 1|3")]},
        {"cmd": "load_config_file", "desc": "Load a configuration file from a path",
         "params": [_str("path", "File path", "")]},
    ],
    "window": [
        {"cmd": "killclient", "desc": "Close the focused window",
         "params": [_enum("mode", ["", "force"], "Mode")]},
        {"cmd": "togglefloating", "desc": "Toggle floating state", "params": []},
        {"cmd": "toggle_all_floating", "desc": "Float every visible window", "params": []},
        {"cmd": "togglefullscreen", "desc": "Toggle fullscreen", "params": []},
        {"cmd": "togglefakefullscreen", "desc": "Toggle constrained 'fake' fullscreen", "params": []},
        {"cmd": "togglemaximizescreen", "desc": "Maximize keeping the bar", "params": []},
        {"cmd": "toggleglobal", "desc": "Pin window across all tags", "params": []},
        {"cmd": "toggle_render_border", "desc": "Toggle window border rendering", "params": []},
        {"cmd": "centerwin", "desc": "Center the floating window", "params": []},
        {"cmd": "minimized", "desc": "Minimize window to scratchpad", "params": []},
        {"cmd": "restore_minimized", "desc": "Restore minimized window", "params": []},
        {"cmd": "toggle_scratchpad", "desc": "Toggle the standard scratchpad", "params": []},
        {"cmd": "toggle_named_scratchpad", "desc": "Toggle a named scratchpad app",
         "params": [_str("appid", "App ID", ""), _str("title", "Title", ""), _str("cmd", "Launch command", "")]},
        {"cmd": "toggle_special_tag", "desc": "Toggle the special overlay workspace", "params": []},
        {"cmd": "tag_special_tag", "desc": "Move window to/from the overlay", "params": []},
        {"cmd": "tag_special_silent", "desc": "Silently move window to/from overlay", "params": []},
        {"cmd": "toggleoverlay", "desc": "Toggle overlay state of focused window", "params": []},
        {"cmd": "toggleoverview", "desc": "Toggle the overview grid", "params": [_enum("scope", ["", "1"], "Scope")]},
        {"cmd": "enteroverview", "desc": "Enter overview mode", "params": []},
        {"cmd": "leaveoverview", "desc": "Leave overview mode", "params": []},
        {"cmd": "togglejump", "desc": "Toggle overview jump mode", "params": []},
    ],
    "focus": [
        {"cmd": "focusid", "desc": "Focus a window by client id", "params": [_int("id", "Client ID")]},
        {"cmd": "focusdir", "desc": "Focus window in a direction", "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "focus_window_or_workspace", "desc": "Focus window, else adjacent tag",
         "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "focusstack", "desc": "Cycle focus within the stack",
         "params": [_enum("dir", ["next", "prev"], "Direction")]},
        {"cmd": "overcircle", "desc": "Open overview / cycle next window",
         "params": [_enum("mode", ["next", "prev", "current_next", "current_prev"], "Mode")]},
        {"cmd": "focuslast", "desc": "Focus the previously active window", "params": []},
        {"cmd": "switcher", "desc": "Open or cycle the thumbnail switcher",
         "params": [_enum("scope", ["next", "prev", "all_tag_next", "all_tag_prev", "all_next", "all_prev"], "Scope")]},
        {"cmd": "exchange_client", "desc": "Swap the focused window with a neighbor",
         "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "exchange_stack_client", "desc": "Swap positions within the stack",
         "params": [_enum("dir", ["next", "prev"], "Direction")]},
        {"cmd": "move_client", "desc": "Move the window one step in a direction",
         "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "zoom", "desc": "Swap focused window with Master", "params": []},
        {"cmd": "smartmovewin", "desc": "Move floating window by the snap distance",
         "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "smartresizewin", "desc": "Resize floating window by the snap distance",
         "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "movewin", "desc": "Move floating window by pixels",
         "params": [_str("x", "X", "+0"), _str("y", "Y", "+0")]},
        {"cmd": "resizewin", "desc": "Resize window by pixels",
         "params": [_str("w", "Width", "+10"), _str("h", "Height", "+0")]},
    ],
    "group": [
        {"cmd": "groupjoin", "desc": "Join a group by direction", "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "groupfocus", "desc": "Focus a group member",
         "params": [_enum("dir", ["prev", "next"], "Direction")]},
        {"cmd": "groupleave", "desc": "Leave the current group", "params": []},
    ],
    "tags": [
        {"cmd": "view", "desc": "View tag(s) by mask",
         "params": [_str("mask", "Tag mask", "1", "e.g. 1, 1|3, 0 = all"),
                   _enum("synctag", ["", "0", "1"], "Sync to all monitors")]},
        {"cmd": "viewtoleft", "desc": "View previous tag", "params": [_enum("synctag", ["", "0", "1"], "Sync")]},
        {"cmd": "viewtoright", "desc": "View next tag", "params": [_enum("synctag", ["", "0", "1"], "Sync")]},
        {"cmd": "view_insert", "desc": "View or insert an adjacent empty tag",
         "params": [_enum("dir", ["prev", "next"], "Direction")]},
        {"cmd": "viewtoleft_have_client", "desc": "View left tag and focus a client",
         "params": [_enum("synctag", ["", "0", "1"], "Sync")]},
        {"cmd": "viewtoright_have_client", "desc": "View right tag and focus a client",
         "params": [_enum("synctag", ["", "0", "1"], "Sync")]},
        {"cmd": "viewprev_have_client", "desc": "View previous tag with client", "params": []},
        {"cmd": "viewnext_have_client", "desc": "View next tag with client", "params": []},
        {"cmd": "viewcrossmon", "desc": "View tag(s) on a specific monitor",
         "params": [_str("mask", "Tag mask", "1"), _str("monitor", "Monitor spec", "")]},
        {"cmd": "tag", "desc": "Move window to tag(s)",
         "params": [_str("mask", "Tag mask", "1"), _enum("synctag", ["", "0", "1"], "Sync")]},
        {"cmd": "tagsilent", "desc": "Move window to tag(s) without focusing",
         "params": [_str("mask", "Tag mask", "1")]},
        {"cmd": "tagtoleft", "desc": "Move window to left tag", "params": [_enum("synctag", ["", "0", "1"], "Sync")]},
        {"cmd": "tagtoright", "desc": "Move window to right tag", "params": [_enum("synctag", ["", "0", "1"], "Sync")]},
        {"cmd": "tagcrossmon", "desc": "Move window to tag(s) on a monitor",
         "params": [_str("mask", "Tag mask", "1"), _str("monitor", "Monitor spec", "")]},
        {"cmd": "toggletag", "desc": "Toggle tag(s) on the window", "params": [_str("mask", "Tag mask", "0")]},
        {"cmd": "toggleview", "desc": "Toggle view of tag(s)", "params": [_str("mask", "Tag mask", "1")]},
        {"cmd": "comboview", "desc": "View multiple tags simultaneously", "params": [_str("mask", "Tag mask", "1")]},
    ],
    "monitor": [
        {"cmd": "focusmon", "desc": "Focus a monitor by direction or spec",
         "params": [_str("target", "Direction / monitor spec", "next")]},
        {"cmd": "tagmon", "desc": "Move window to a monitor",
         "params": [_str("target", "Direction / monitor spec", "next"),
                   _enum("keeptag", ["", "0", "1"], "Keep tag")]},
        {"cmd": "sleep_monitor", "desc": "Turn a monitor's power off",
         "params": [_str("monitor", "Monitor spec", "")]},
        {"cmd": "wakeup_monitor", "desc": "Turn a monitor's power on",
         "params": [_str("monitor", "Monitor spec", "")]},
        {"cmd": "sleep_toggle_monitor", "desc": "Toggle a monitor's power",
         "params": [_str("monitor", "Monitor spec", "")]},
        {"cmd": "disable_monitor", "desc": "Remove a monitor", "params": [_str("monitor", "Monitor spec", "")]},
        {"cmd": "enable_monitor", "desc": "Add a monitor", "params": [_str("monitor", "Monitor spec", "")]},
        {"cmd": "toggle_monitor", "desc": "Toggle monitor add/remove", "params": [_str("monitor", "Monitor spec", "")]},
        {"cmd": "togglehdr", "desc": "Toggle HDR on the focused output",
         "params": [_enum("mode", ["", "on", "off", "toggle"], "Mode"),
                   _str("monitor", "Monitor name / all", "")]},
        {"cmd": "create_virtual_output", "desc": "Create a headless monitor", "params": []},
        {"cmd": "destroy_all_virtual_output", "desc": "Destroy all virtual monitors", "params": []},
    ],
    "layout": [
        {"cmd": "setlayout", "desc": "Switch to a layout",
         "params": [_enum("layout", _LAYOUT_NAMES, "Layout")]},
        {"cmd": "switch_layout", "desc": "Cycle through layouts", "params": []},
        {"cmd": "incnmaster", "desc": "Increase / decrease master count",
         "params": [_enum("delta", ["+1", "-1"], "Delta")]},
        {"cmd": "setmfact", "desc": "Adjust the master area factor",
         "params": [_str("delta", "Delta", "+0.05")]},
        {"cmd": "set_proportion", "desc": "Set scroller proportion",
         "params": [_float("proportion", "Proportion", "1.0", "0.0-1.0")]},
        {"cmd": "switch_proportion_preset", "desc": "Cycle scroller width presets", "params": []},
        {"cmd": "scroller_stack", "desc": "Move window in/out of the scroller stack",
         "params": [_enum("dir", _DIRS, "Direction")]},
        {"cmd": "incgaps", "desc": "Adjust the gap size", "params": [_str("delta", "Delta", "+5")]},
        {"cmd": "togglegaps", "desc": "Toggle gaps", "params": []},
        {"cmd": "dwindle_toggle_split_direction", "desc": "Toggle dwindle split direction", "params": []},
        {"cmd": "dwindle_split_horizontal", "desc": "Set dwindle split horizontal", "params": []},
        {"cmd": "dwindle_split_vertical", "desc": "Set dwindle split vertical", "params": []},
        {"cmd": "dwindle_toggle_current_split", "desc": "Toggle current window split direction", "params": []},
    ],
    "system": [
        {"cmd": "reload_config", "desc": "Hot-reload the configuration", "params": []},
        {"cmd": "quit", "desc": "Exit mango", "params": []},
        {"cmd": "setkeymode", "desc": "Switch key mode / submap",
         "params": [_str("mode", "Mode name", "default")]},
        {"cmd": "switch_keyboard_layout", "desc": "Cycle or set a keyboard layout",
         "params": [_str("index", "Layout index (optional)", "")]},
        {"cmd": "setoption", "desc": "Temporarily set a config option",
         "params": [_str("key", "Option key", ""), _str("value", "Value", "")]},
        {"cmd": "toggle_trackpad_enable", "desc": "Toggle enabling the trackpad", "params": []},
    ],
    "mouse": [
        {"cmd": "moveresize", "desc": "Move or resize a window while dragging (mouse)",
         "params": [_enum("mode", ["curmove", "curresize"], "Mode")]},
    ],
}

LAYOUTS = list(_LAYOUT_NAMES)

MOUSE_BUTTONS = [
    "btn_left", "btn_right", "btn_middle", "btn_side", "btn_extra",
    "btn_forward", "btn_back", "btn_task",
]

KEYMODES_FLAGS_LIST = ["default", "common"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def iter_dispatchers() -> Iterator[tuple[str, dict[str, Any], str]]:
    """Yield (cmd, entry, category) for every dispatcher."""
    for cat, entries in DISPATCHERS.items():
        for entry in entries:
            yield entry["cmd"], entry, cat


def get_dispatcher(cmd: str) -> dict[str, Any] | None:
    for _, entry, _ in iter_dispatchers():
        if entry["cmd"] == cmd.lower():
            return entry
    return None


def dispatcher_css(cmd: str) -> str:
    for _, entry, cat in iter_dispatchers():
        if entry["cmd"] == cmd.lower():
            return BLOCK_CSS.get(cat, "mm-block-launch")
    return "mm-block-launch"


def dispatcher_category(cmd: str) -> str:
    for _, entry, cat in iter_dispatchers():
        if entry["cmd"] == cmd.lower():
            return cat
    return "launch"


def dispatcher_has_params(cmd: str) -> bool:
    entry = get_dispatcher(cmd)
    return bool(entry and entry.get("params"))


def format_dispatcher(cmd: str, params: dict[str, str]) -> str:
    """Serialise a dispatcher + parameters into ``cmd,param,param`` text."""
    parts = [cmd.lower()]
    for p in params.values():
        p = (p or "").strip()
        if p:
            parts.append(p)
    return ",".join(parts)