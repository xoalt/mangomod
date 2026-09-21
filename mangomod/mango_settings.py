"""Docs-backed catalog of every scalar configuration option Mangowm documents.

Each setting records its type so the All Settings page can render a typed
widget and read/write the value straight from the parsed ConfigDocument:
  type:  bool | int | float | str | color | enum | curve | mask
"""

from __future__ import annotations

from typing import Any, Iterator

# ---------------------------------------------------------------------------
# Section keys used by the All Settings browser (suggested render order)
# ---------------------------------------------------------------------------

SECTIONS: list[str] = [
    "Keyboard & Typing",
    "Mouse",
    "Trackpad",
    "Touchscreen",
    "System & Hardware",
    "Focus & Input",
    "Multi-Monitor & Tags",
    "Window Behavior",
    "Theme: Dimensions",
    "Theme: Colors",
    "Theme: Overview Jump Labels",
    "Theme: Monocle Tab Bar",
    "Theme: Cursor",
    "Effects: Blur",
    "Effects: Shadows",
    "Effects: Opacity & Radius",
    "Effects: Dim Overlay",
    "Animations",
    "Layouts: Scroller",
    "Layouts: Master-Stack",
    "Layouts: Dwindle",
    "Monitor & Tearing",
]


def _b(key: str, label: str, cat: str, default: int, desc: str, restart: bool = False) -> dict:
    return {"key": key, "label": label, "cat": cat, "type": "bool",
            "default": str(default), "mini": 0, "maxi": 1, "desc": desc, "restart": restart}


def _i(key: str, label: str, cat: str, default: int, desc: str,
       mini: int | None = None, maxi: int | None = None, restart: bool = False) -> dict:
    return {"key": key, "label": label, "cat": cat, "type": "int", "default": str(default),
            "mini": mini, "maxi": maxi, "desc": desc, "restart": restart}


def _f(key: str, label: str, cat: str, default: float, desc: str,
       mini: float | None = None, maxi: float | None = None, restart: bool = False) -> dict:
    return {"key": key, "label": label, "cat": cat, "type": "float", "default": repr(default),
            "mini": mini, "maxi": maxi, "desc": desc, "restart": restart}


def _s(key: str, label: str, cat: str, default: str, desc: str, restart: bool = False) -> dict:
    return {"key": key, "label": label, "cat": cat, "type": "str", "default": default,
            "desc": desc, "restart": restart}


def _c(key: str, label: str, cat: str, default: str, desc: str) -> dict:
    return {"key": key, "label": label, "cat": cat, "type": "color", "default": default,
            "desc": desc, "restart": False}


def _e(key: str, label: str, cat: str, default: str, options: list[str], desc: str) -> dict:
    return {"key": key, "label": label, "cat": cat, "type": "enum", "default": default,
            "options": list(options), "desc": desc, "restart": False}


def _curve(key: str, cat: str, default: str, desc: str) -> dict:
    return {"key": key, "label": key, "cat": cat, "type": "curve", "default": default,
            "desc": desc, "restart": False}


# ---------------------------------------------------------------------------
# Full documented settings
# ---------------------------------------------------------------------------

SETTINGS: list[dict[str, Any]] = [
    # --- Keyboard & Typing ---
    _i("repeat_rate", "Repeat Rate", "Keyboard & Typing", 25, "Key repeats per second.", mini=1, maxi=100),
    _i("repeat_delay", "Repeat Delay", "Keyboard & Typing", 600, "Delay (ms) before a held key repeats.", mini=0),
    _b("numlockon", "NumLock on Startup", "Keyboard & Typing", 0, "Enable NumLock when mango starts."),
    _s("xkb_rules_rules", "XKB Rules File", "Keyboard & Typing", "evdev", "XKB rules file, e.g. evdev, base."),
    _s("xkb_rules_model", "XKB Model", "Keyboard & Typing", "pc104", "Keyboard model, e.g. pc104, macbook."),
    _s("xkb_rules_layout", "XKB Layout", "Keyboard & Typing", "us", "Layout code, e.g. us, de, us,de."),
    _s("xkb_rules_variant", "XKB Variant", "Keyboard & Typing", "", "Layout variant, e.g. dvorak, colemak, intl."),
    _s("xkb_rules_options", "XKB Options", "Keyboard & Typing", "", "E.g. caps:escape, ctrl:nocaps."),

    # --- Mouse ---
    _b("mouse_natural_scrolling", "Natural Scrolling", "Mouse", 0, "Invert the scroll direction."),
    _e("mouse_accel_profile", "Accel Profile", "Mouse", "2", ["0", "1", "2"],
       "0 none, 1 flat, 2 adaptive."),
    _f("mouse_accel_speed", "Accel Speed", "Mouse", 0.0, "Speed adjustment (-1.0 to 1.0).", mini=-1.0, maxi=1.0),
    _b("mouse_left_handed", "Left Handed", "Mouse", 0, "Swap left and right buttons."),
    _b("mouse_middle_button_emulation", "Middle Button Emulation", "Mouse", 0, "Emulate a middle button."),
    _e("mouse_scroll_method", "Scroll Method", "Mouse", "1", ["0", "1", "2", "4"],
       "0 none, 1 two-finger, 2 edge, 4 button."),
    _i("mouse_scroll_button", "Scroll Button", "Mouse", 274, "Button used for scroll mode (272-279).", 272, 279),
    _e("mouse_click_method", "Click Method", "Mouse", "1", ["0", "1", "2"],
       "0 none, 1 button areas, 2 clickfinger."),
    _e("mouse_send_events_mode", "Send Events", "Mouse", "0", ["0", "1", "2"],
       "0 enabled, 1 disabled, 2 disabled on external mouse."),
    _f("axis_scroll_factor", "Axis Scroll Factor", "Mouse", 1.0, "Scroll speed factor (0.1-10.0).", mini=0.1, maxi=10.0),

    # --- Trackpad ---
    _b("disable_trackpad", "Disable Trackpad", "Trackpad", 0, "Set to 1 to disable the trackpad entirely.", restart=True),
    _b("tap_to_click", "Tap to Click", "Trackpad", 1, "Tap to trigger a left click."),
    _b("tap_and_drag", "Tap and Drag", "Trackpad", 1, "Tap and hold to drag items."),
    _b("trackpad_natural_scrolling", "Natural Scrolling", "Trackpad", 0, "Natural (inverted) scrolling."),
    _e("trackpad_accel_profile", "Accel Profile", "Trackpad", "2", ["0", "1", "2"],
       "0 none, 1 flat, 2 adaptive."),
    _f("trackpad_accel_speed", "Accel Speed", "Trackpad", 0.0, "Speed adjustment (-1.0 to 1.0).", mini=-1.0, maxi=1.0),
    _i("trackpad_scroll_button", "Scroll Button", "Trackpad", 274, "Button used for scroll mode (272-279).", 272, 279),
    _e("trackpad_scroll_method", "Scroll Method", "Trackpad", "1", ["0", "1", "2", "4"],
       "0 none, 1 two-finger, 2 edge, 4 button."),
    _e("trackpad_click_method", "Click Method", "Trackpad", "1", ["0", "1", "2"],
       "0 none, 1 button areas, 2 clickfinger."),
    _e("trackpad_send_events_mode", "Send Events", "Trackpad", "0", ["0", "1", "2"],
       "0 enabled, 1 disabled, 2 disabled on external mouse."),
    _b("drag_lock", "Drag Lock", "Trackpad", 1, "Lock dragging after tapping."),
    _b("trackpad_disable_while_typing", "Disable While Typing", "Trackpad", 1, "Disable the trackpad while typing."),
    _b("trackpad_left_handed", "Left Handed", "Trackpad", 0, "Swap left and right buttons."),
    _b("trackpad_middle_button_emulation", "Middle Button Emulation", "Trackpad", 0, "Emulate a middle button."),
    _i("swipe_min_threshold", "Swipe Min Threshold", "Trackpad", 1, "Minimum swipe threshold when using gestures."),
    _b("gesture_live", "Gesture Live Preview", "Trackpad", 1,
       "Drive tag/focus/overview transitions while fingers move (1) or only on release (0)."),
    _i("gesture_swipe_distance", "Swipe Distance", "Trackpad", 300, "Finger travel (px) per full page transition."),
    _f("gesture_swipe_cancel_ratio", "Swipe Cancel Ratio", "Trackpad", 0.5, "Fraction past which a swipe commits."),
    _f("gesture_swipe_min_speed_to_force", "Min Force Speed", "Trackpad", 10.0, "Speed (px) that forces a commit."),
    _e("button_map", "Button Map", "Trackpad", "0", ["0", "1"],
       "0 left/right/middle, 1 left/middle/right."),
    _f("trackpad_scroll_factor", "Scroll Factor", "Trackpad", 1.0, "Scroll speed factor (0.1-10.0).", mini=0.1, maxi=10.0),

    # --- Touchscreen ---
    _b("touch_enable", "Touchscreen Enabled", "Touchscreen", 1, "Set to 0 to completely disable touch support."),
    _b("touch_enable_mouse_emulation", "Mouse Emulation", "Touchscreen", 0,
       "Emulate left-click for surfaces that do not accept touch."),

    # --- System & Hardware ---
    _b("xwayland_persistence", "XWayland Persistence", "System & Hardware", 1,
       "Keep XWayland running even with no X11 apps open."),
    _b("xwayland_ignore_scale", "XWayland Ignore Scale", "System & Hardware", 0,
       "Disable global scale for XWayland."),
    _b("syncobj_enable", "Syncobj", "System & Hardware", 1,
       "Enable drm_syncobj support (helps with gaming stutter). Requires restart.", restart=True),
    _b("allow_lock_transparent", "Transparent Lock", "System & Hardware", 0, "Allow the lock screen to be transparent."),
    _b("allow_shortcuts_inhibit", "Allow Shortcuts Inhibit", "System & Hardware", 1,
       "Allow shortcuts to be inhibited by clients."),

    # --- Focus & Input ---
    _b("focus_on_activate", "Focus on Activate", "Focus & Input", 1,
       "Auto-focus windows when they request activation."),
    _b("sloppyfocus", "Sloppy Focus", "Focus & Input", 1, "Focus follows the mouse cursor."),
    _b("warpcursor", "Warp Cursor", "Focus & Input", 1,
       "Warp cursor to window center when focus changes via keyboard."),
    _i("cursor_hide_timeout", "Cursor Hide Timeout", "Focus & Input", 0,
       "Hide cursor after N seconds of inactivity (0 disables)."),
    _b("cursor_hide_on_keypress", "Hide Cursor on Keypress", "Focus & Input", 0, "Hide the cursor on keypress."),
    _b("drag_tile_to_tile", "Drag Tile to Tile", "Focus & Input", 0,
       "Allow dragging a tiled window onto another to swap them."),
    _b("drag_tile_small", "Drag Tile Small", "Focus & Input", 1,
       "Allow dragging a tiled window temporarily to small size."),
    _e("drag_corner", "Drag Corner", "Focus & Input", "3", ["0", "1", "2", "3", "4"],
       "0 none, 1-3 corners, 4 auto-detect."),
    _b("drag_warp_cursor", "Drag Warp Cursor", "Focus & Input", 1, "Warp cursor when dragging windows to tile."),
    _i("axis_bind_apply_timeout", "Axis Bind Timeout", "Focus & Input", 100,
       "Timeout (ms) detecting consecutive scroll events for axis binds."),

    # --- Multi-Monitor & Tags ---
    _b("focus_cross_monitor", "Focus Cross Monitor", "Multi-Monitor & Tags", 0,
       "Allow directional focus to cross monitor boundaries."),
    _b("focusdir_only_zone_overlap", "Focus Zone Overlap", "Multi-Monitor & Tags", 1,
       "Directional focus only picks windows overlapping on the perpendicular axis."),
    _b("exchange_cross_monitor", "Exchange Cross Monitor", "Multi-Monitor & Tags", 0,
       "Allow exchange_client / move_client to cross monitors."),
    _b("focus_cross_tag", "Focus Cross Tag", "Multi-Monitor & Tags", 0,
       "Allow directional focus to cross into other tags."),
    _b("view_current_to_back", "View Current to Back", "Multi-Monitor & Tags", 0,
       "Toggling the current tag switches back to the previously viewed tag."),
    _b("scratchpad_cross_monitor", "Scratchpad Cross Monitor", "Multi-Monitor & Tags", 0,
       "Share the scratchpad pool across all monitors."),
    _b("single_scratchpad", "Single Scratchpad", "Multi-Monitor & Tags", 1,
       "Only one scratchpad visible at a time."),
    _i("tag_num", "Number of Tags", "Multi-Monitor & Tags", 9, "Number of tags/workspaces (1-31).", 1, 31),
    _b("tag_gather", "Tag Gather", "Multi-Monitor & Tags", 0,
       "Compact occupied tags to consecutive tags starting at 1."),

    # --- Window Behavior ---
    _b("enable_floating_snap", "Floating Snap", "Window Behavior", 0,
       "Snap floating windows to edges or other windows."),
    _i("snap_distance", "Snap Distance", "Window Behavior", 30, "Max distance (px) to trigger floating snap."),
    _b("float_full_to_top", "Float Full to Top", "Window Behavior", 0,
       "Let fullscreen, floating and layer-shell top windows share one layer."),
    _b("no_border_when_single", "No Border When Single", "Window Behavior", 0,
       "Remove borders when only one window is on the tag."),
    _b("smartgaps", "Smart Gaps", "Window Behavior", 0, "Disable gaps when only one window is present."),
    _b("idleinhibit_ignore_visible", "Idle Inhibit Invisible", "Window Behavior", 0,
       "Allow invisible clients to inhibit idle."),
    _b("idleinhibit_when_fullscreen", "Idle Inhibit Fullscreen", "Window Behavior", 0,
       "Keep idle inhibited while a fullscreen window is focused."),
    _b("tag_carousel", "Tag Carousel", "Window Behavior", 0, "Enable cycling through tags."),
    _f("drag_tile_refresh_interval", "Tile Drag Refresh", "Window Behavior", 8.0,
       "Refresh interval (1-16) for tiled window resize.", mini=1.0, maxi=16.0),
    _f("drag_floating_refresh_interval", "Floating Drag Refresh", "Window Behavior", 8.0,
       "Refresh interval (1-16) for floating window resize.", mini=1.0, maxi=16.0),

    # --- Theme: Dimensions ---
    _i("borderpx", "Border Width", "Theme: Dimensions", 4, "Window border width in pixels."),
    _i("gappih", "Inner Gap H", "Theme: Dimensions", 5, "Horizontal inner gap (between windows)."),
    _i("gappiv", "Inner Gap V", "Theme: Dimensions", 5, "Vertical inner gap."),
    _i("gappoh", "Outer Gap H", "Theme: Dimensions", 10, "Horizontal outer gap (windows <-> screen edges)."),
    _i("gappov", "Outer Gap V", "Theme: Dimensions", 10, "Vertical outer gap."),

    # --- Theme: Colors ---
    _c("rootcolor", "Root Color", "Theme: Colors", "0x323232ff", "Background color of the root window."),
    _c("bordercolor", "Border Color", "Theme: Colors", "0x444444ff", "Inactive window border."),
    _c("dropcolor", "Drop Color", "Theme: Colors", "0x8FBA7C55", "Drop shadow when dragging windows."),
    _c("splitcolor", "Split Color", "Theme: Colors", "0xEB441EFF", "Split border in manual dwindle layout."),
    _c("focuscolor", "Focus Color", "Theme: Colors", "0xc66b25ff", "Active window border."),
    _c("urgentcolor", "Urgent Color", "Theme: Colors", "0xad401fff", "Urgent window border (alerts)."),
    _c("maximizescreencolor", "Maximized Color", "Theme: Colors", "0x89aa61ff", "Maximized window border."),
    _c("scratchpadcolor", "Scratchpad Color", "Theme: Colors", "0x516c93ff", "Scratchpad window border."),
    _c("globalcolor", "Global Color", "Theme: Colors", "0xb153a7ff", "Global (sticky) window border."),
    _c("overlaycolor", "Overlay Color", "Theme: Colors", "0x14a57cff", "Overlay window border."),

    # --- Theme: Overview Jump Labels ---
    _c("jump_label_decorate_fg_color", "Jump Label FG", "Theme: Overview Jump Labels", "0xc4939dff", "Label text color."),
    _c("jump_label_decorate_bg_color", "Jump Label BG", "Theme: Overview Jump Labels", "0x201b14ff", "Label background."),
    _c("jump_label_decorate_focus_fg_color", "Jump Focus FG", "Theme: Overview Jump Labels", "0x201b14ff", "Focused label text."),
    _c("jump_label_decorate_focus_bg_color", "Jump Focus BG", "Theme: Overview Jump Labels", "0xc4939dff", "Focused label background."),
    _c("jump_label_decorate_border_color", "Jump Border", "Theme: Overview Jump Labels", "0x8BAA9Bff", "Label border color."),
    _i("jump_label_decorate_border_width", "Jump Border Width", "Theme: Overview Jump Labels", 4, "Label border width."),
    _i("jump_label_decorate_corner_radius", "Jump Radius", "Theme: Overview Jump Labels", 5, "Label corner radius."),
    _i("jump_label_decorate_padding_x", "Jump Padding X", "Theme: Overview Jump Labels", 10, "Label horizontal padding."),
    _i("jump_label_decorate_padding_y", "Jump Padding Y", "Theme: Overview Jump Labels", 10, "Label vertical padding."),
    _s("jump_label_decorate_font_desc", "Jump Font", "Theme: Overview Jump Labels", "monospace Bold 16", "Label font description."),

    # --- Theme: Monocle Tab Bar ---
    _i("group_bar_height", "Tab Bar Height", "Theme: Monocle Tab Bar", 50, "Height of the monocle tab bar."),
    _c("group_bar_decorate_fg_color", "Tab FG", "Theme: Monocle Tab Bar", "0xc4939dff", "Tab text color."),
    _c("group_bar_decorate_bg_color", "Tab BG", "Theme: Monocle Tab Bar", "0x201b14ff", "Tab background."),
    _c("group_bar_decorate_focus_fg_color", "Tab Focus FG", "Theme: Monocle Tab Bar", "0x201b14ff", "Active tab text."),
    _c("group_bar_decorate_focus_bg_color", "Tab Focus BG", "Theme: Monocle Tab Bar", "0xc4939dff", "Active tab background."),
    _c("group_bar_decorate_border_color", "Tab Border", "Theme: Monocle Tab Bar", "0x8BAA9Bff", "Tab border color."),
    _i("group_bar_decorate_border_width", "Tab Border Width", "Theme: Monocle Tab Bar", 4, "Tab border width."),
    _i("group_bar_decorate_corner_radius", "Tab Radius", "Theme: Monocle Tab Bar", 5, "Tab corner radius."),
    _i("group_bar_decorate_padding_x", "Tab Padding X", "Theme: Monocle Tab Bar", 0, "Tab horizontal padding."),
    _i("group_bar_decorate_padding_y", "Tab Padding Y", "Theme: Monocle Tab Bar", 0, "Tab vertical padding."),
    _s("group_bar_decorate_font_desc", "Tab Font", "Theme: Monocle Tab Bar", "monospace Bold 16", "Tab font description."),

    # --- Theme: Cursor ---
    _i("cursor_size", "Cursor Size", "Theme: Cursor", 24, "Mouse cursor size."),
    _s("cursor_theme", "Cursor Theme", "Theme: Cursor", "Adwaita", "Mouse cursor theme."),

    # --- Effects: Blur ---
    _b("blur", "Blur Windows", "Effects: Blur", 0, "Enable blur for windows."),
    _b("blur_layer", "Blur Layer Surfaces", "Effects: Blur", 0, "Enable blur for layer surfaces."),
    _b("blur_optimized", "Blur Optimized", "Effects: Blur", 1,
       "Cache wallpaper/blur background to cut GPU usage."),
    _i("blur_params_radius", "Blur Radius", "Effects: Blur", 5, "Blur strength."),
    _i("blur_params_num_passes", "Blur Passes", "Effects: Blur", 1, "Number of blur passes."),
    _f("blur_params_noise", "Blur Noise", "Effects: Blur", 0.02, "Blur noise level."),
    _f("blur_params_brightness", "Blur Brightness", "Effects: Blur", 0.9, "Blur brightness adjustment."),
    _f("blur_params_contrast", "Blur Contrast", "Effects: Blur", 0.9, "Blur contrast adjustment."),
    _f("blur_params_saturation", "Blur Saturation", "Effects: Blur", 1.2, "Blur saturation adjustment."),

    # --- Effects: Shadows ---
    _b("shadows", "Shadows", "Effects: Shadows", 0, "Enable window shadows."),
    _b("layer_shadows", "Layer Shadows", "Effects: Shadows", 0, "Enable shadows for layer surfaces."),
    _b("shadow_only_floating", "Shadow Only Floating", "Effects: Shadows", 1,
       "Only draw shadows for floating windows."),
    _i("shadows_size", "Shadow Size", "Effects: Shadows", 10, "Shadow size."),
    _i("shadows_blur", "Shadow Blur", "Effects: Shadows", 15, "Shadow blur amount."),
    _i("shadows_position_x", "Shadow X", "Effects: Shadows", 0, "Shadow X offset."),
    _i("shadows_position_y", "Shadow Y", "Effects: Shadows", 0, "Shadow Y offset."),
    _c("shadowscolor", "Shadow Color", "Effects: Shadows", "0x000000ff", "Color of the shadow."),

    # --- Effects: Opacity & Radius ---
    _i("border_radius", "Window Radius", "Effects: Opacity & Radius", 0, "Window corner radius in pixels."),
    _e("border_radius_location_default", "Radius Location", "Effects: Opacity & Radius", "0",
       ["0", "1", "2", "3", "4", "5"], "0 all, 1 top-left, 2 top-right, 3 bottom-left, 4 bottom-right, 5 closest."),
    _b("no_radius_when_single", "No Radius When Single", "Effects: Opacity & Radius", 0,
       "Disable radius if only one window is visible."),
    _f("focused_opacity", "Focused Opacity", "Effects: Opacity & Radius", 1.0,
       "Opacity of the active window (0-1).", 0.0, 1.0),
    _f("unfocused_opacity", "Unfocused Opacity", "Effects: Opacity & Radius", 1.0,
       "Opacity of inactive windows (0-1).", 0.0, 1.0),

    # --- Effects: Dim Overlay ---
    _b("dim_enable", "Dim Overlay", "Effects: Dim Overlay", 0,
       "Draw a translucent shade over window content."),
    _c("dim_focused_color", "Dim Focused Color", "Effects: Dim Overlay", "0x00000000",
       "Dim color of the focused window."),
    _c("dim_unfocused_color", "Dim Unfocused Color", "Effects: Dim Overlay", "0x00000055",
       "Dim color of unfocused windows."),

    # --- Animations ---
    _b("animations", "Window Animations", "Animations", 0, "Enable animations for windows."),
    _b("layer_animations", "Layer Animations", "Animations", 0, "Enable animations for layer surfaces."),
    _e("animation_type_open", "Open Type", "Animations", "zoom", ["zoom", "slide", "fade", "none"],
       "Window open animation."),
    _e("animation_type_close", "Close Type", "Animations", "slide", ["zoom", "slide", "fade", "none"],
       "Window close animation."),
    _e("layer_animation_type_open", "Layer Open Type", "Animations", "zoom",
       ["zoom", "slide", "fade", "none"], "Layer open animation."),
    _e("layer_animation_type_close", "Layer Close Type", "Animations", "zoom",
       ["zoom", "slide", "fade", "none"], "Layer close animation."),
    _b("animation_fade_in", "Fade In", "Animations", 1, "Enable fade-in effect."),
    _b("animation_fade_out", "Fade Out", "Animations", 1, "Enable fade-out effect."),
    _f("fadein_begin_opacity", "Fade-in Start", "Animations", 0.5, "Starting opacity of fade-in (0-1).", 0.0, 1.0),
    _f("fadeout_begin_opacity", "Fade-out Start", "Animations", 0.5, "Starting opacity of fade-out (0-1).", 0.0, 1.0),
    _f("zoom_initial_ratio", "Zoom Initial", "Animations", 0.4, "Initial zoom ratio."),
    _f("zoom_end_ratio", "Zoom End", "Animations", 0.8, "End zoom ratio."),
    _i("animation_duration_move", "Move Duration", "Animations", 500, "Move animation duration (ms)."),
    _i("animation_duration_open", "Open Duration", "Animations", 400, "Open animation duration (ms)."),
    _i("animation_duration_tag", "Tag Duration", "Animations", 300, "Tag animation duration (ms)."),
    _i("animation_duration_close", "Close Duration", "Animations", 300, "Close animation duration (ms)."),
    _i("animation_duration_focus", "Focus Duration", "Animations", 0, "Focus change duration (ms)."),
    _curve("animation_curve_open", "Animations", "0.46,1.0,0.29,0.99", "Open bezier curve (x1,y1,x2,y2)."),
    _curve("animation_curve_move", "Animations", "0.46,1.0,0.29,0.99", "Move bezier curve."),
    _curve("animation_curve_tag", "Animations", "0.46,1.0,0.29,0.99", "Tag animation bezier curve."),
    _curve("animation_curve_close", "Animations", "0.46,1.0,0.29,0.99", "Close bezier curve."),
    _curve("animation_curve_focus", "Animations", "0.46,1.0,0.29,0.99", "Focus bezier curve."),
    _curve("animation_curve_opafadein", "Animations", "0.46,1.0,0.29,0.99", "Open opacity bezier curve."),
    _curve("animation_curve_opafadeout", "Animations", "0.5,0.5,0.5,0.5", "Close opacity bezier curve."),
    _b("tag_animation_direction", "Tag Direction", "Animations", 1, "1 horizontal, 0 vertical."),

    # --- Layouts: Scroller ---
    _i("scroller_structs", "Scroller Structs", "Layouts: Scroller", 20, "Width reserved on sides when ratio is 1."),
    _f("scroller_default_proportion", "Default Proportion", "Layouts: Scroller", 0.9,
       "Default width proportion for new windows."),
    _b("scroller_focus_center", "Focus Center", "Layouts: Scroller", 0, "Always center the focused window."),
    _b("scroller_prefer_center", "Prefer Center", "Layouts: Scroller", 0,
       "Center focused window only if it was outside the view."),
    _b("scroller_prefer_overspread", "Prefer Overspread", "Layouts: Scroller", 1,
       "Allow windows to overspread with extra space."),
    _b("edge_scroller_pointer_focus", "Edge Pointer Focus", "Layouts: Scroller", 1,
       "Focus windows even if partially off-screen."),
    _f("edge_scroller_focus_allow_speed", "Edge Focus Speed", "Layouts: Scroller", 0.0,
       "Allow pointer focus if pointer moves faster than this."),
    _s("scroller_proportion_preset", "Proportion Preset", "Layouts: Scroller", "0.5,0.8,1.0",
       "Presets for cycling window widths."),
    _b("scroller_ignore_proportion_single", "Ignore Single Proportion", "Layouts: Scroller", 1,
       "Ignore proportion adjustments for single windows."),
    _f("scroller_default_proportion_single", "Single Proportion", "Layouts: Scroller", 1.0,
       "Default proportion for single windows (needs ignore=0)."),

    # --- Layouts: Master-Stack ---
    _b("new_is_master", "New Is Master", "Layouts: Master-Stack", 1, "New windows become the master window."),
    _f("default_mfact", "Master Factor", "Layouts: Master-Stack", 0.55, "Split ratio between master and stack."),
    _i("default_nmaster", "Master Count", "Layouts: Master-Stack", 1, "Number of master windows."),
    _b("center_master_overspread", "Master Overspread", "Layouts: Master-Stack", 0,
       "Center Tile: master spreads across the screen if no stack."),
    _b("center_when_single_stack", "Center Single Stack", "Layouts: Master-Stack", 1,
       "Center Tile: center master with one stack window."),

    # --- Layouts: Dwindle ---
    _f("dwindle_split_ratio", "Split Ratio", "Layouts: Dwindle", 0.5, "Ratio for new splits (0.05-0.95)."),
    _b("dwindle_smart_split", "Smart Split", "Layouts: Dwindle", 0,
       "Pick the split axis from the cursor's position."),
    _e("dwindle_hsplit", "HSplit", "Layouts: Dwindle", "1", ["0", "1", "2"],
       "0 follow cursor, 1 right, 2 left."),
    _e("dwindle_vsplit", "VSplit", "Layouts: Dwindle", "1", ["0", "1", "2"],
       "0 follow cursor, 1 below, 2 above."),
    _b("dwindle_preserve_split", "Preserve Split", "Layouts: Dwindle", 0,
       "Keep the sibling's split orientation on close."),
    _b("dwindle_smart_resize", "Smart Resize", "Layouts: Dwindle", 0,
       "Move the split toward the cursor when dragging."),
    _b("dwindle_drop_simple_split", "Simple Drop Split", "Layouts: Dwindle", 1,
       "1 two-zone preview, 0 four-quadrant preview."),
    _b("dwindle_manual_split", "Manual Split", "Layouts: Dwindle", 0, "Manually split windows mode."),
    _s("circle_layout", "Circle Layout", "Layouts: Dwindle", "",
       "Comma-separated layouts switch_layout cycles (e.g. tile,scroller)."),

    # --- Monitor & Tearing ---
    _e("allow_tearing", "Allow Tearing", "Monitor & Tearing", "0", ["0", "1", "2"],
       "0 disabled, 1 enabled, 2 fullscreen only."),
    _e("hdr_depth", "HDR Depth", "Monitor & Tearing", "2", ["0", "1", "2"],
       "0 default, 1 HDR8, 2 HDR10 (requires vulkan renderer)."),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def iter_settings() -> Iterator[tuple[str, dict[str, Any], str]]:
    """Yield (key, entry, section) for every documented setting."""
    for entry in SETTINGS:
        yield entry["key"], entry, entry["cat"]


def get_setting(key: str) -> dict[str, Any] | None:
    for k, entry, _ in iter_settings():
        if k == key:
            return entry
    return None


def settings_by_section() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {s: [] for s in SECTIONS}
    for key, entry, cat in iter_settings():
        out.setdefault(cat, []).append(entry)
    return out