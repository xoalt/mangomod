"""Docs-backed catalogs for rules, device rules and Command Builder triggers.

RULE_PARAMS feeds the rule add-dialogs (window rule, tag rule, layer rule,
monitor rule, device rule) so every documented parameter can be offered with a
typed editor.  TRIGGER_TYPES describes the five input-binding families used by
the Command Builder (key, mouse, axis, gesture, switch).
"""

from __future__ import annotations

from typing import Any

from .mango_schema import LAYOUTS, MODIFIERS

# Full layout list from the Layouts docs page.
LAYOUTS_ALL = [
    "tile", "scroller", "monocle", "grid", "deck",
    "center_tile", "vertical_tile", "right_tile",
    "vertical_scroller", "vertical_grid", "vertical_deck",
    "dwindle", "fair", "vertical_fair",
]

MONITOR_TRANSFORMS = ["0", "1", "2", "3", "4", "5", "6", "7"]
DEVICE_TYPES = ["keyboard", "pointer", "trackpad", "touch", "switch", "tablet", "pad"]
ANIM_TYPES = ["zoom", "slide", "fade", "none"]


def _r(name: str, label: str, ptype: str, default: str = "", options: list[str] | None = None,
       hint: str = "") -> dict[str, Any]:
    return {"name": name, "label": label, "type": ptype, "default": default,
            "options": list(options or []), "hint": hint}


def _rs(name: str, label: str, hint: str = "") -> dict[str, Any]:
    return _r(name, label, "str", "", None, hint)


# ---------------------------------------------------------------------------
# Rule catalogs (rule keyword -> (match params, option params))
# ---------------------------------------------------------------------------

_WINDOW_MATCH = [_rs("appid", "App ID", "regex, optional"), _rs("title", "Title", "regex, optional")]
_WINDOW_OPTIONS = [
    _r("isfloating", "Floating", "bool", "0", ["0", "1"], "Force floating state"),
    _r("isfullscreen", "Fullscreen", "bool", "0", ["0", "1"]),
    _r("isfakefullscreen", "Fake Fullscreen", "bool", "0", ["0", "1"], "Stay constrained"),
    _r("isglobal", "Global", "bool", "0", ["0", "1"], "Sticky across tags"),
    _r("isoverlay", "Overlay", "bool", "0", ["0", "1"], "Always in the top layer"),
    _r("isopensilent", "Open Silent", "bool", "0", ["0", "1"], "Open without focus"),
    _r("istagsilent", "Tag Silent", "bool", "0", ["0", "1"], "Don't focus if not on the current tag"),
    _r("force_fakemaximize", "Force Fake Maximize", "bool", "1", ["0", "1"]),
    _r("ignore_maximize", "Ignore Maximize", "bool", "1", ["0", "1"], "Don't handle client maximize"),
    _r("ignore_minimize", "Ignore Minimize", "bool", "1", ["0", "1"], "Don't handle client minimize"),
    _r("force_tiled_state", "Force Tiled State", "bool", "0", ["0", "1"], "Lies about tiling to clients"),
    _r("noopenmaximized", "No Open Maximized", "bool", "0", ["0", "1"]),
    _r("single_scratchpad", "Single Scratchpad", "bool", "1", ["0", "1"], "Only one scratchpad shown"),
    _r("allow_shortcuts_inhibit", "Allow Shortcuts Inhibit", "bool", "1", ["0", "1"]),
    _r("idleinhibit_when_focus", "Idle Inhibit When Focus", "bool", "0", ["0", "1"]),
    _r("vrr_only_fullscreen", "VRR Only Fullscreen", "bool", "0", ["0", "1"], "Need vrr:0 in monitor rule"),
    _r("shield_when_capture", "Shield When Captured", "bool", "0", ["0", "1"]),
    _r("force_render", "Force Render", "bool", "0", ["0", "1"]),
    _r("activation_bypass", "Activation Bypass", "bool", "0", ["0", "1"], "Skip xdg-activation auth"),
    _r("width", "Width", "float", "0", None, "px or % of screen if below 1"),
    _r("height", "Height", "float", "0", None, "px or % of screen if below 1"),
    _r("offsetx", "Offset X", "int", "0", None, "% from center (-999..999)"),
    _r("offsety", "Offset Y", "int", "0", None, "% from center (-999..999)"),
    _rs("monitor", "Monitor", "monitor spec"),
    _r("tags", "Tags", "mask", "0", None, "e.g. 9 or 1|3|5; 0 = special overlay"),
    _r("no_force_center", "No Force Center", "bool", "0", ["0", "1"]),
    _r("isnosizehint", "No Size Hints", "bool", "0", ["0", "1"], "Ignore min/max size hints"),
    _r("noblur", "No Blur", "bool", "0", ["0", "1"]),
    _r("isnoborder", "No Border", "bool", "0", ["0", "1"]),
    _r("isnoshadow", "No Shadow", "bool", "0", ["0", "1"]),
    _r("isnoradius", "No Radius", "bool", "0", ["0", "1"]),
    _r("isnoanimation", "No Animation", "bool", "0", ["0", "1"]),
    _r("focused_opacity", "Focused Opacity", "float", "1.0", None, "0.0-1.0"),
    _r("unfocused_opacity", "Unfocused Opacity", "float", "1.0", None, "0.0-1.0"),
    _r("allow_csd", "Allow CSD", "bool", "0", ["0", "1"], "Client side decoration"),
    _r("scroller_proportion", "Scroller Proportion", "float", "0.9", None, "0.1-1.0"),
    _r("scroller_proportion_single", "Scroller Single Proportion", "float", "1.0", None, "0.1-1.0"),
    _r("animation_type_open", "Open Animation", "enum", "none", ANIM_TYPES),
    _r("animation_type_close", "Close Animation", "enum", "none", ANIM_TYPES),
    _r("nofadein", "No Fade In", "bool", "0", ["0", "1"]),
    _r("nofadeout", "No Fade Out", "bool", "0", ["0", "1"]),
    _r("isterm", "Is Terminal", "bool", "0", ["0", "1"], "A new GUI window replaces it"),
    _r("noswallow", "No Swallow", "bool", "0", ["0", "1"]),
    _rs("globalkeybinding", "Global Keybinding", "[mod][-]key, Wayland apps only"),
    _r("isunglobal", "Unmanaged Global", "bool", "0", ["0", "1"], "Desktop pets / cameras"),
    _r("isnamedscratchpad", "Named Scratchpad", "bool", "1", ["0", "1"], "0 disable, 1 named scratchpad"),
    _r("force_tearing", "Force Tearing", "bool", "0", ["0", "1"]),
]

_TAG_MATCH = [
    _r("id", "Tag ID", "str", "*", None, "0-9 or * for all tags"),
    _rs("monitor_name", "Monitor Name"),
    _rs("monitor_make", "Monitor Make"),
    _rs("monitor_model", "Monitor Model"),
    _rs("monitor_serial", "Monitor Serial"),
]
_TAG_OPTIONS = [
    _r("layout_name", "Layout", "enum", "tile", list(LAYOUTS_ALL)),
    _r("no_render_border", "No Render Border", "bool", "0", ["0", "1"]),
    _r("open_as_floating", "Open Floating", "bool", "0", ["0", "1"]),
    _r("no_hide", "Persistent Tag", "bool", "0", ["0", "1"], "Not hidden when empty"),
    _r("nmaster", "Master Count", "int", "1", None, "0-99"),
    _r("mfact", "Master Factor", "float", "0.55", None, "0.1-0.9"),
    _r("scroller_default_proportion", "Scroller Proportion", "float", "0.9", None, "0.1-1.0"),
    _r("scroller_default_proportion_single", "Scroller Single Proportion", "float", "1.0", None, "0.1-1.0"),
    _r("scroller_ignore_proportion_single", "Ignore Single Proportion", "bool", "0", ["0", "1"]),
]

_LAYER_MATCH = [_rs("layer_name", "Layer Name", "regex, optional")]
_LAYER_OPTIONS = [
    _r("animation_type_open", "Open Animation", "enum", "zoom", ANIM_TYPES),
    _r("animation_type_close", "Close Animation", "enum", "zoom", ANIM_TYPES),
    _r("noblur", "No Blur", "bool", "0", ["0", "1"]),
    _r("noanim", "No Animation", "bool", "0", ["0", "1"]),
    _r("noshadow", "No Shadow", "bool", "0", ["0", "1"]),
    _r("shield_when_capture", "Shield When Captured", "bool", "0", ["0", "1"]),
]

_MONITOR_MATCH = [
    _rs("name", "Name", "regex, optional (^name$)"),
    _rs("make", "Make"),
    _rs("model", "Model"),
    _rs("serial", "Serial"),
]
_MONITOR_OPTIONS = [
    _r("width", "Width", "int", "0", None, "0-9999"),
    _r("height", "Height", "int", "0", None, "0-9999"),
    _r("refresh", "Refresh (Hz)", "float", "60", None, "0.001-9999"),
    _r("x", "X Position", "int", "0", None),
    _r("y", "Y Position", "int", "0", None),
    _r("scale", "Scale", "float", "1.0", None, "0.01-100"),
    _r("vrr", "VRR", "bool", "0", ["0", "1"], "Variable refresh rate"),
    _r("hdr", "HDR", "bool", "0", ["0", "1"]),
    _r("hdr_min_lum", "HDR Min Luminance", "float", "0", None, "cd/m2 (0 = unset)"),
    _r("hdr_max_lum", "HDR Max Luminance", "float", "0", None, "cd/m2 (0 = unset)"),
    _r("hdr_max_avg_lum", "HDR Max Avg Luminance", "float", "0", None, "cd/m2 (0 = unset)"),
    _r("hdr_force", "HDR Force", "bool", "0", ["0", "1"], "Skip EDID capability checks"),
    _rs("icc", "ICC Profile", "path, mutually exclusive with hdr"),
    _r("rr", "Transform", "enum", "0", list(MONITOR_TRANSFORMS), "rotation / flip"),
    _r("custom", "Custom Mode", "bool", "0", ["0", "1"], "may cause black screen"),
    _r("disable", "Disable", "bool", "0", ["0", "1"]),
]

_DEVICE_MATCH = [
    _rs("name", "Device Name", "match exactly, else a type: rule matches all devices of a type"),
    _r("type", "Device Type", "enum", "keyboard", list(DEVICE_TYPES)),
]
_DEVICE_OPTIONS = [
    _rs("kb_layout", "KB Layout"),
    _rs("kb_variant", "KB Variant"),
    _rs("kb_options", "KB Options"),
    _rs("kb_rules", "KB Rules"),
    _rs("kb_model", "KB Model"),
    _r("repeat_rate", "Repeat Rate", "int", "25", None, "per second"),
    _r("repeat_delay", "Repeat Delay", "int", "600", None, "ms"),
    _r("accel_speed", "Accel Speed", "float", "0.0", None, "-1.0 to 1.0"),
    _r("accel_profile", "Accel Profile", "enum", "2", ["0", "1", "2"], "0 none, 1 flat, 2 adaptive"),
    _r("natural_scrolling", "Natural Scrolling", "bool", "0", ["0", "1"]),
    _r("left_handed", "Left Handed", "bool", "0", ["0", "1"]),
    _r("tap_to_click", "Tap to Click", "bool", "0", ["0", "1"]),
    _r("tap_and_drag", "Tap and Drag", "bool", "0", ["0", "1"]),
    _r("scroll_method", "Scroll Method", "enum", "1", ["1", "2", "4"], "1 two-finger, 2 edge, 4 button"),
    _r("disable_while_typing", "Disable While Typing", "bool", "0", ["0", "1"]),
    _r("middle_button_emulation", "Middle Button Emulation", "bool", "0", ["0", "1"]),
    _r("send_events_mode", "Send Events", "enum", "0", ["0", "1", "2"],
       "0 enabled, 1 disabled, 2 disabled with external mouse"),
    _r("scroll_button", "Scroll Button", "int", "274", None, "272-279"),
    _r("click_method", "Click Method", "enum", "1", ["1", "2"], "1 button areas, 2 clickfinger"),
    _r("drag_lock", "Drag Lock", "bool", "0", ["0", "1"]),
    _r("button_map", "Button Map", "enum", "0", ["0", "1"], "0 L/R/M, 1 L/M/R"),
    _rs("monitor", "Monitor", "pin touch/tablet to an output"),
]

RULE_PARAMS: dict[str, dict[str, Any]] = {
    "windowrule": {"label": "Window Rule", "match": _WINDOW_MATCH, "options": _WINDOW_OPTIONS},
    "windowrule-once": {"label": "Window Rule (once)", "match": _WINDOW_MATCH, "options": _WINDOW_OPTIONS},
    "tagrule": {"label": "Tag Rule", "match": _TAG_MATCH, "options": _TAG_OPTIONS},
    "layerrule": {"label": "Layer Rule", "match": _LAYER_MATCH, "options": _LAYER_OPTIONS},
    "monitorrule": {"label": "Monitor Rule", "match": _MONITOR_MATCH, "options": _MONITOR_OPTIONS},
    "devicerule": {"label": "Device Rule", "match": _DEVICE_MATCH, "options": _DEVICE_OPTIONS},
}

# ---------------------------------------------------------------------------
# Command Builder trigger types
# ---------------------------------------------------------------------------

TRIGGER_TYPES: list[dict[str, Any]] = [
    {
        "id": "key", "kw": "bind", "label": "Key Binding",
        "fields": [
            {"name": "mods", "label": "Modifiers", "type": "multi", "options": list(MODIFIERS)},
            {"name": "key", "label": "Key", "type": "key"},
            {"name": "flags", "label": "Flags", "type": "multi", "options": ["l", "s", "r", "p", "c"]},
        ],
        "hint": "bind[flags]=MOD,KEY,COMMAND,PARAMS  (key names from wev)",
    },
    {
        "id": "mouse", "kw": "mousebind", "label": "Mouse Button",
        "fields": [
            {"name": "mods", "label": "Modifiers", "type": "multi", "options": list(MODIFIERS)},
            {"name": "key", "label": "Button", "type": "enum",
             "options": ["btn_left", "btn_right", "btn_middle", "btn_side", "btn_extra",
                         "btn_forward", "btn_back", "btn_task", "code:272", "code:273",
                         "code:274", "code:275", "code:276", "code:277", "code:278", "code:279"]},
        ],
        "hint": "mousebind=MOD,BUTTON,COMMAND,PARAMS",
    },
    {
        "id": "axis", "kw": "axisbind", "label": "Scroll Wheel (axis)",
        "fields": [
            {"name": "mods", "label": "Modifiers", "type": "multi", "options": list(MODIFIERS)},
            {"name": "key", "label": "Direction", "type": "enum",
             "options": ["UP", "DOWN", "LEFT", "RIGHT"]},
        ],
        "hint": "axisbind=MOD,DIRECTION,COMMAND,PARAMS",
    },
    {
        "id": "gesture", "kw": "gesturebind", "label": "Trackpad Gesture",
        "fields": [
            {"name": "mods", "label": "Modifiers", "type": "multi", "options": list(MODIFIERS)},
            {"name": "key", "label": "Direction", "type": "enum",
             "options": ["up", "down", "left", "right"]},
            {"name": "fingers", "label": "Fingers", "type": "enum", "options": ["3", "4"]},
        ],
        "hint": "gesturebind=MOD,DIRECTION,3|4,COMMAND,PARAMS  (needs gesture_live for previews)",
    },
    {
        "id": "switch", "kw": "switchbind", "label": "Lid Switch",
        "fields": [
            {"name": "key", "label": "Fold State", "type": "enum",
             "options": ["fold", "unfold"]},
        ],
        "hint": "switchbind=FOLD_STATE,COMMAND,PARAMS  (lid open/close)",
    },
]