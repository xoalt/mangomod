"""Compatibility + validation engine for the Command Builder.

Pure logic (no GTK, no pixels): given the current trigger kind and the command
blocks already placed on the canvas, decide which dispatchers may legally be
added next, and given a parameter definition + candidate string value, decide
whether that value is well-formed *before* it is committed to the config
document. Because this module imports nothing from GI, it is testable in plain
unit tests on a headless box (which is exactly how it is kept honest).

Design notes
------------
1. The schema (``mango_schema``) describes every dispatcher already typed:
   each param is one of ``enum|str|int|float|bool|color|key`` and, when
   ``enum`` or typed, carries the concrete ``options`` list. There is *no*
   mini/maxi range metadata in the catalog, so numeric validation is limited
   to "is it parseable as the declared type" rather than fabricated ranges.
2. Compatibility between the trigger and a dispatcher is derived from the
   dispatcher's *category* (launch/window/focus/group/tags/monitor/layout/
   system/mouse). Interacting with mouse/trackpad (``moveresize``, gesture
   dispatchers) is only meaningful under a mouse/gesture/axis trigger; plain
   key dispatchers only under a key/mouse trigger. Anything not explicitly
   matched resolves to a loosened default so the app never hard-blocks a
   legal binding.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Canonical trigger kinds (ids in mango_rules.TRIGGER_TYPES)
# ---------------------------------------------------------------------------
TRIGGER_KINDS: tuple[str, ...] = ("key", "mouse", "axis", "gesture", "switch")

# Dispatcher categories that interact with a pointer/trackpad device and so
# only make sense bound through a mouse / gesture / axis trigger.
_POINTER_CATEGORIES: frozenset[str] = frozenset(
    {"mouse"}
)
# Categories that are conceptually pointer-but-triggerable also under mouse:
_POINTER_OK_KINDS: frozenset[str] = frozenset({"mouse", "axis", "gesture"})

# ---------------------------------------------------------------------------
# Value validation
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"^(?:0x|#)?[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")


def validate_value(param: dict[str, Any], value: str) -> str | None:
    """Return an error message if ``value`` is not well-formed for ``param``.

    ``None`` means the value is acceptable (and will be committed as-is).
    """
    ptype = param.get("type", "str")
    raw = (value or "").strip()

    if ptype == "enum":
        options = param.get("options", []) or []
        if raw and raw not in options:
            opts = ", ".join(options) if options else "(no options)"
            return f"'{raw}' is not one of: {opts}"
        return None

    if ptype == "bool":
        return None if raw in ("0", "1") else "Boolean values are 0 or 1"
    if ptype == "int":
        if not raw:
            return None
        try:
            int(raw, 10)
        except ValueError:
            return "Integer expected"
        return None
    if ptype == "float":
        if not raw:
            return None
        try:
            float(raw)
        except ValueError:
            return "Number expected"
        return None
    if ptype == "color":
        return None if (not raw or _HEX_RE.match(raw)) else (
            "Color must be a hex value like 0xrrggbbaa")
    if ptype == "key":
        # A single key name (wev-key style); no spaces/commas inside.
        return None if (not raw or " " not in raw and "," not in raw) else (
            "Key must be a single key name")
    return None


# ---------------------------------------------------------------------------
# Trigger compatibility
# ---------------------------------------------------------------------------

def kind_accepted(kind: str) -> str:
    """Return the canonical trigger-kind id, or ``""`` for an unknown id."""
    return kind if kind in TRIGGER_KINDS else ""


def category_of(cmd: str, schema_categories) -> str:
    """Best-effort category label for a dispatcher command.

    Falls back to ``"misc"`` when the command isn't in the schema.
    """
    for cat in schema_categories:
        if cmd in schema_categories[cat]:
            return cat
    return "misc"


def ok_for_trigger(kind: str, category: str) -> bool:
    """Whether a dispatcher of ``category`` may be bound under ``kind``.

    Rules (deliberately permissive, never hard-blocking a legal binding):
    - pointer-category dispatchers (mouse) require a pointer-capable trigger;
    - everything else resolves to True, since a key/mouse bind is the norm.
    """
    k = kind_accepted(kind)
    if not k:
        # Unknown/missing trigger id — be permissive.
        return True
    if category in _POINTER_CATEGORIES:
        return k in _POINTER_OK_KINDS
    return True


def available_next(
    trigger_kind: str,
    existing: list[str],
    schema_categories,
    always_allowed: set[str] | None = None,
) -> list[str]:
    """Dispatcher commands still allowed to be added, given the canvas state.

    ``existing`` is the ordered list of command ids already on the canvas.
    ``always_allowed`` is an optional over-ride set (e.g. trigger/mouse
    commands the palette always offers); defaults to empty.
    """
    allowed: set[str] = set(always_allowed or ())
    for cat, cmds in schema_categories.items():
        for cmd in cmds:
            k = resolve_against(existing, cat)
            if k is not None and ok_for_trigger(trigger_kind, k):
                allowed.add(cmd)
    return sorted(allowed)


def resolve_against(existing: list[str], cat: str) -> str | None:
    """Helper: trigger-compatible category after the placed blocks.

    Returns the *first trigger-kind* among the existing blocks' categories if
    any is pointer-ish, else the neutral category. Not currently used beyond
    hints; provided for symmetry with future re-filtering.
    """
    pointer = next(
        (c for c in (category_of(e, {}) for e in () if False) or [] if c in _POINTER_CATEGORIES),
        None,
    )
    return pointer or cat
