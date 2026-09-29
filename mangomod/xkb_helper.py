"""XKB and Key Mapping Helper for MangoMod."""

from __future__ import annotations

import ctypes
import ctypes.util
import os
from typing import Any

# Standard key symbol to readable label map
KEY_DISPLAY_NAMES: dict[str, str] = {
    "return": "Enter ↵",
    "enter": "Enter ↵",
    "space": "Space ␣",
    "backspace": "Backspace ⌫",
    "tab": "Tab ⇥",
    "escape": "Esc",
    "capslock": "Caps Lock",
    "print": "Print Screen",
    "delete": "Del",
    "insert": "Ins",
    "home": "Home",
    "end": "End",
    "prior": "Page Up",
    "next": "Page Down",
    "page_up": "Page Up",
    "page_down": "Page Down",
    "left": "Left ←",
    "right": "Right →",
    "up": "Up ↑",
    "down": "Down ↓",
    "minus": "-",
    "equal": "=",
    "bracketleft": "[",
    "bracketright": "]",
    "backslash": "\\",
    "semicolon": ";",
    "apostrophe": "'",
    "quote": "'",
    "grave": "`",
    "comma": ",",
    "period": ".",
    "slash": "/",
}


class XkbHelper:
    def __init__(self):
        self.lib = None
        self.ctx = None
        self.keymap = None
        self.state = None

        path = ctypes.util.find_library("xkbcommon")
        if not path:
            candidates = [
                "/usr/lib/libxkbcommon.so.0",
                "/usr/lib64/libxkbcommon.so.0",
                "/lib/x86_64-linux-gnu/libxkbcommon.so.0",
                "/usr/lib/x86_64-linux-gnu/libxkbcommon.so.0",
                "/usr/lib/libxkbcommon.so",
                "/usr/lib64/libxkbcommon.so",
            ]
            for p in candidates:
                if os.path.exists(p):
                    path = p
                    break

        if not path:
            return

        try:
            self.lib = ctypes.CDLL(path)
            self.lib.xkb_context_new.restype = ctypes.c_void_p
            self.lib.xkb_keymap_new_from_names.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_int,
            ]
            self.lib.xkb_keymap_new_from_names.restype = ctypes.c_void_p
            self.lib.xkb_state_new.argtypes = [ctypes.c_void_p]
            self.lib.xkb_state_new.restype = ctypes.c_void_p
            self.lib.xkb_state_key_get_one_sym.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint32,
            ]
            self.lib.xkb_state_key_get_one_sym.restype = ctypes.c_uint32
            self.lib.xkb_keysym_get_name.argtypes = [
                ctypes.c_uint32,
                ctypes.c_char_p,
                ctypes.c_size_t,
            ]
            self.lib.xkb_keysym_get_name.restype = ctypes.c_int
            self.lib.xkb_keymap_unref.argtypes = [ctypes.c_void_p]
            self.lib.xkb_keymap_unref.restype = None
            self.lib.xkb_state_unref.argtypes = [ctypes.c_void_p]
            self.lib.xkb_state_unref.restype = None

            self.ctx = self.lib.xkb_context_new(0)
        except Exception:
            self.lib = None

    def format_key_label(self, key_name: str) -> str:
        k_lower = key_name.lower().strip()
        if k_lower.startswith("code:"):
            return f"Keycode {k_lower[5:]}"
        return KEY_DISPLAY_NAMES.get(k_lower, key_name.upper() if len(key_name) <= 2 else key_name.capitalize())


def format_modifiers(mods: str) -> str:
    """Format modifier string cleanly (e.g. SUPER+SHIFT -> Super + Shift)."""
    if not mods or mods.upper() == "NONE":
        return ""
    parts = mods.replace("+", " ").replace("-", " ").split()
    clean_parts = []
    for p in parts:
        p_up = p.upper()
        if p_up == "SUPER" or p_up == "MOD4":
            clean_parts.append("Super ❖")
        elif p_up == "CTRL" or p_up == "CONTROL":
            clean_parts.append("Ctrl")
        elif p_up == "ALT" or p_up == "MOD1":
            clean_parts.append("Alt")
        elif p_up == "SHIFT":
            clean_parts.append("Shift ⇧")
        else:
            clean_parts.append(p.capitalize())
    return " + ".join(clean_parts)
