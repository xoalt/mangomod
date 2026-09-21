"""CSS theme definitions for MangoMod."""

CSS = """
/* --- MangoMod -- Warm Mango Dark Theme --- */
/* Identity: ripe-mango amber accent on warm charcoal, matching the app icon
   (mango gradient #ffb703 -> #fb8500 -> #d90429) and the "mango_amber"
   default in app_settings. */

/* --- Accent --- */
@define-color mm_accent        #ffb703;   /* ripe mango amber */
@define-color mm_accent_dark   #fb8500;
@define-color mm_accent_glow   #ffd166;
@define-color mm_accent_dim    rgba(255, 183, 3, 0.14);
@define-color mm_accent_hover  rgba(255, 183, 3, 0.22);
@define-color mm_accent_border rgba(255, 183, 3, 0.38);
@define-color mm_accent_glowx  rgba(255, 209, 102, 0.55);

/* --- Surfaces (warm charcoal) --- */
@define-color window_bg_color    #14110d;
@define-color window_fg_color    #f1ebe1;
@define-color view_bg_color      #1a1611;
@define-color view_fg_color      #f1ebe1;
@define-color headerbar_bg_color #14110d;
@define-color card_bg_color      #221c15;
@define-color card_fg_color      #f1ebe1;
@define-color popover_bg_color   #221c15;
@define-color popover_fg_color   #f1ebe1;
@define-color dialog_bg_color    #1a1611;
@define-color dialog_fg_color    #f1ebe1;

/* --- Borders --- */
@define-color mm_border         rgba(255, 214, 150, 0.10);
@define-color mm_border_strong  rgba(255, 214, 150, 0.18);

/* --- Base Window --- */
window {
    background-color: @window_bg_color;
    color: @window_fg_color;
}

/* --- Header Bars --- */
headerbar,
.mm-sidebar-bg {
    background-color: @window_bg_color;
    background-image: none;
    box-shadow: none;
    border-bottom: 1px solid @mm_border;
    color: @window_fg_color;
}

/* --- Sidebar --- */
.navigation-sidebar {
    background-color: transparent;
    border-right: 1px solid @mm_border;
}

.mm-sidebar-listbox {
    background: transparent;
    border: none;
}

.mm-sidebar-listbox row {
    border-radius: 10px;
    margin: 1px 6px;
    padding: 7px 12px;
    transition: background 120ms ease, color 120ms ease;
    color: @window_fg_color;
}

.mm-sidebar-listbox row:hover {
    background: rgba(255, 183, 3, 0.07);
}

.mm-sidebar-listbox row:selected {
    background: @mm_accent_dim;
    color: @mm_accent_glow;
    font-weight: 600;
    box-shadow: inset 2px 0 0 @mm_accent;
}

.mm-sidebar-listbox row:selected image,
.mm-sidebar-listbox row:selected label {
    color: @mm_accent_glow;
}

/* --- Section Labels --- */
.mm-sidebar-section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: rgba(255, 209, 150, 0.42);
    margin-left: 12px;
    margin-top: 14px;
    margin-bottom: 4px;
}

/* --- Entries --- */
entry,
.mm-search-entry {
    color: @window_fg_color;
    background-color: @card_bg_color;
    border: 1px solid @mm_border;
    border-radius: 10px;
}

entry:focus,
.mm-search-entry:focus-within {
    border-color: @mm_accent_border;
    box-shadow: 0 0 0 1px @mm_accent_dark;
    outline: none;
}

/* --- Buttons --- */
button.suggested-action {
    background: linear-gradient(180deg, @mm_accent, @mm_accent_dark);
    color: #1a1206;
    font-weight: 700;
    border-radius: 10px;
    border: none;
    padding: 6px 16px;
}

button.suggested-action:hover {
    box-shadow: 0 0 12px @mm_accent_hover;
}

button.destructive-action {
    border-radius: 10px;
}

/* --- Live preview pane --- */
.mm-preview {
    background-color: #0e0b08;
    border: 1px solid @mm_border;
    border-radius: 12px;
    padding: 8px 12px;
    font-family: monospace;
    font-size: 12px;
    color: rgba(255, 236, 210, 0.82);
    caret-color: @mm_accent_glow;
}

.mm-preview selection {
    background-color: @mm_accent_dim;
}

/* --- Compositor Status Banner --- */
.mm-banner-running {
    background-color: rgba(34, 197, 94, 0.12);
    border-bottom: 1px solid rgba(34, 197, 94, 0.25);
    color: #4ade80;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
}

.mm-banner-stopped {
    background-color: rgba(217, 4, 41, 0.12);
    border-bottom: 1px solid rgba(217, 4, 41, 0.28);
    color: #ff7285;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
}

/* --- Badges & Pills --- */
.mm-badge {
    background-color: @mm_accent_dim;
    color: @mm_accent_glow;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

.mm-key-badge {
    background-color: rgba(255, 214, 150, 0.10);
    border: 1px solid rgba(255, 214, 150, 0.16);
    border-radius: 6px;
    padding: 3px 7px;
    font-family: monospace;
    font-size: 11px;
    font-weight: 600;
    color: @mm_accent_glow;
}

/* --- Canvas Frame --- */
.mm-canvas-frame {
    background: #0e0b08;
    border: 1px solid @mm_border;
    border-radius: 14px;
    min-height: 220px;
}

/* --- Save button indicator --- */
.mm-dirty-dot {
    color: @mm_accent_glow;
    font-size: 16px;
    margin-right: 4px;
}

/* ================= Command Builder ================= */

/* --- Pane titles --- */
.mm-pane-title,
.mm-sidebar-section-label {
    color: rgba(255, 209, 150, 0.60);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}

/* --- Palette (action tray) --- */
.mm-palette-list {
    background: transparent;
    border: none;
}

.mm-palette-block {
    background: rgba(255, 183, 3, 0.05);
    border: 1px solid @mm_border;
    border-radius: 12px;
    margin: 2px 4px;
    padding: 8px 10px;
    transition: background 140ms ease, border-color 140ms ease, transform 120ms ease;
}

.mm-palette-block:hover {
    background: @mm_accent_dim;
    border-color: @mm_accent_border;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(251, 133, 0, 0.18);
}

.mm-palette-dim,
.mm-palette-block:disabled,
.mm-palette-block:disabled .mm-block-name {
    opacity: 0.38;
    filter: grayscale(1);
    box-shadow: none;
    transition: opacity 160ms ease;
}

.mm-palette-block:disabled {
    opacity: 0.38;
}

.mm-palette-block:disabled:hover {
    transform: none;
}

.mm-block-handle {
    opacity: 0.55;
    color: rgba(255, 214, 150, 0.60);
}

.mm-block-name {
    font-weight: 600;
    color: @window_fg_color;
}

/* --- Drop canvas --- */
.mm-drop-canvas {
    border: 2px dashed rgba(255, 183, 3, 0.22);
    border-radius: 12px;
    margin: 12px;
    transition: border-color 160ms ease, background 160ms ease;
}

.mm-drop-canvas.mm-drop-over {
    border-color: @mm_accent_glow;
    background: @mm_accent_dim;
    box-shadow: inset 0 0 24px rgba(255, 183, 3, 0.10);
}

/* --- Action block --- */
.mm-action-block {
    background: #201912;
    border: 1px solid @mm_border_strong;
    border-radius: 12px;
    margin: 4px 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.40);
}

.mm-block-head {
    background: rgba(255, 183, 3, 0.06);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid @mm_border;
}

.mm-block-delete {
    opacity: 0.4;
    margin: 2px;
}

.mm-block-delete:hover {
    opacity: 1;
    color: #ff7285;
}

/* --- Per-category accents (from dispatcher_css) --- */
.mm-badge-launch { background: rgba(255, 183, 3, 0.16); color: #ffd166; }
.mm-badge-window { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
.mm-badge-focus  { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.mm-badge-group  { background: rgba(129, 140, 248, 0.15); color: #818cf8; }
.mm-badge-tags   { background: rgba(251, 146, 60, 0.18); color: #fb923c; }
.mm-badge-monitor{ background: rgba(232, 121, 249, 0.15); color: #e879f9; }
.mm-badge-layout { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.mm-badge-system { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }
.mm-badge-mouse  { background: rgba(250, 204, 21, 0.13); color: #facc15; }

.mm-param-label {
    color: rgba(255, 226, 190, 0.65);
    font-size: 12px;
    font-weight: 500;
}

.mm-trigger-editor {
    background: rgba(255, 183, 3, 0.04);
    border: 1px solid @mm_border;
    border-radius: 12px;
    padding: 8px 10px;
}

.mm-param-hint {
    opacity: 0.5;
    font-size: 11px;
}

/* --- Cards / boxed lists --- */
.card,
boxed-list,
.boxed-list {
    background-color: @card_bg_color;
    border: 1px solid @mm_border;
    border-radius: 12px;
}

/* --- Dropdowns & popovers --- */
dropdown,
popover {
    border-radius: 10px;
}

popover contents {
    background-color: @popover_bg_color;
    border: 1px solid @mm_border_strong;
    border-radius: 10px;
}

/* --- Scrollbars --- */
scrollbar slider {
    background-color: rgba(255, 183, 3, 0.22);
    border-radius: 999px;
    min-width: 8px;
    min-height: 8px;
}

scrollbar slider:hover {
    background-color: rgba(255, 183, 3, 0.38);
}

"""

LIGHT_CSS = """
/* --- MangoMod -- Ripe Paper Light Theme --- */

@define-color mm_accent        #d9480f;
@define-color mm_accent_dark   #a83708;
@define-color mm_accent_glow   #f76707;
@define-color mm_accent_dim    rgba(217, 72, 15, 0.12);
@define-color mm_accent_hover  rgba(217, 72, 15, 0.20);
@define-color mm_accent_border rgba(217, 72, 15, 0.45);
@define-color mm_accent_glowx  rgba(247, 103, 7, 0.35);

@define-color window_bg_color    #faf6ef;
@define-color window_fg_color    #2b2118;
@define-color view_bg_color      #fffdf8;
@define-color view_fg_color      #2b2118;
@define-color headerbar_bg_color #faf6ef;
@define-color card_bg_color      #ffffff;
@define-color card_fg_color      #2b2118;
@define-color popover_bg_color   #ffffff;
@define-color popover_fg_color   #2b2118;
@define-color dialog_bg_color    #fffdf8;
@define-color dialog_fg_color    #2b2118;

@define-color mm_border         rgba(120, 72, 20, 0.16);
@define-color mm_border_strong  rgba(120, 72, 20, 0.28);
@define-color mm_ink_soft       rgba(43, 33, 24, 0.62);
@define-color mm_ink_faint      rgba(43, 33, 24, 0.45);

window {
    background-color: @window_bg_color;
    color: @window_fg_color;
}

headerbar,
.mm-sidebar-bg {
    background-color: @headerbar_bg_color;
    background-image: none;
    box-shadow: none;
    border-bottom: 1px solid @mm_border;
    color: @window_fg_color;
}

.navigation-sidebar {
    background-color: #f3ecdf;
    border-right: 1px solid @mm_border;
}

.mm-sidebar-listbox {
    background: transparent;
    border: none;
}

.mm-sidebar-listbox row {
    border-radius: 10px;
    margin: 1px 6px;
    padding: 6px 10px;
    transition: background 120ms ease, color 120ms ease;
    color: @window_fg_color;
}

.mm-sidebar-listbox row:hover {
    background: rgba(217, 72, 15, 0.08);
}

.mm-sidebar-listbox row:selected {
    background: @mm_accent_dim;
    color: @mm_accent_dark;
    font-weight: 600;
}

.mm-sidebar-listbox row:selected image,
.mm-sidebar-listbox row:selected label {
    color: @mm_accent_dark;
}

.mm-sidebar-section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: @mm_ink_faint;
    margin-left: 12px;
    margin-top: 14px;
    margin-bottom: 4px;
}

entry,
.mm-search-entry {
    color: @window_fg_color;
    background-color: @card_bg_color;
    border: 1px solid @mm_border_strong;
    border-radius: 8px;
}

entry:focus,
.mm-search-entry:focus-within {
    border-color: @mm_accent_border;
    box-shadow: 0 0 0 1px @mm_accent_dark;
    outline: none;
}

.mm-preview {
    background-color: #2b2118;
    border: none;
    border-radius: 10px;
    padding: 8px 12px;
    font-family: monospace;
    font-size: 12px;
    color: #ffd8a8;
    caret-color: @mm_accent_glow;
}

.mm-preview selection {
    background-color: rgba(255, 183, 3, 0.30);
}

.mm-banner-running {
    background-color: rgba(47, 158, 68, 0.12);
    border-bottom: 1px solid rgba(47, 158, 68, 0.30);
    color: #2b8a3e;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
}

.mm-banner-stopped {
    background-color: rgba(217, 4, 41, 0.08);
    border-bottom: 1px solid rgba(217, 4, 41, 0.25);
    color: #c92a3a;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
}

.mm-badge {
    background-color: @mm_accent_dim;
    color: @mm_accent_dark;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
}

.mm-key-badge {
    font-family: monospace;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 7px;
    border-radius: 6px;
    background: #f3ecdf;
    border: 1px solid @mm_border_strong;
    color: @mm_accent_dark;
}

.mm-canvas-frame {
    background: #f3ecdf;
    border: 1px solid @mm_border;
    border-radius: 14px;
    min-height: 220px;
}

.mm-dirty-dot {
    color: @mm_accent_glow;
    font-size: 16px;
    margin-right: 4px;
}

.mm-pane-title,
.mm-sidebar-section-label {
    color: @mm_ink_faint;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}

.mm-palette-list {
    background: transparent;
    border: none;
}

.mm-palette-block {
    background: @card_bg_color;
    border: 1px solid @mm_border;
    border-radius: 10px;
    margin: 2px 4px;
    padding: 8px 10px;
    transition: background 140ms ease, border-color 140ms ease, transform 120ms ease;
}

.mm-palette-block:hover {
    background: @mm_accent_dim;
    border-color: @mm_accent_border;
    transform: translateY(-1px);
}

.mm-palette-dim,
.mm-palette-block:disabled,
.mm-palette-block:disabled .mm-block-name {
    opacity: 0.38;
    filter: grayscale(1);
    box-shadow: none;
    transition: opacity 160ms ease;
}

.mm-palette-block:disabled {
    opacity: 0.38;
}

.mm-palette-block:disabled:hover {
    transform: none;
}

.mm-block-handle {
    opacity: 0.55;
    color: @mm_ink_faint;
}

.mm-block-name {
    font-weight: 600;
    color: @window_fg_color;
}

.mm-drop-canvas {
    border: 2px dashed rgba(217, 72, 15, 0.35);
    border-radius: 12px;
    margin: 12px;
    transition: border-color 160ms ease, background 160ms ease;
}

.mm-drop-canvas.mm-drop-over {
    border-color: @mm_accent_glow;
    background: @mm_accent_dim;
}

.mm-action-block {
    background: #2b2118;
    border: none;
    border-radius: 12px;
    margin: 4px 4px;
    box-shadow: 0 2px 10px rgba(43, 33, 24, 0.30);
}

.mm-action-block .mm-block-name,
.mm-action-block .mm-param-label {
    color: #ffecd2;
}

.mm-block-head {
    background: rgba(255, 183, 3, 0.12);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid rgba(255, 183, 3, 0.20);
}

.mm-block-delete {
    opacity: 0.5;
    margin: 2px;
    color: #ffb59e;
}

.mm-block-delete:hover {
    opacity: 1;
    color: #ff8787;
}

.mm-badge-launch { background: rgba(217, 72, 15, 0.14); color: #a83708; }
.mm-badge-window { background: rgba(24, 100, 171, 0.12); color: #1864ab; }
.mm-badge-focus  { background: rgba(47, 158, 68, 0.14); color: #2b8a3e; }
.mm-badge-group  { background: rgba(92, 103, 178, 0.14); color: #5c67b2; }
.mm-badge-tags   { background: rgba(217, 72, 15, 0.16); color: #c24a08; }
.mm-badge-monitor{ background: rgba(166, 77, 199, 0.12); color: #a64dc7; }
.mm-badge-layout { background: rgba(47, 158, 68, 0.14); color: #2b8a3e; }
.mm-badge-system { background: rgba(90, 100, 110, 0.14); color: #5a646e; }
.mm-badge-mouse  { background: rgba(174, 124, 4, 0.16); color: #8a6400; }

.mm-param-label {
    color: @mm_ink_soft;
    font-size: 12px;
    font-weight: 500;
}

.mm-trigger-editor {
    background: rgba(217, 72, 15, 0.05);
    border: 1px solid @mm_border;
    border-radius: 10px;
    padding: 8px 10px;
}

.mm-param-hint {
    opacity: 0.5;
    font-size: 11px;
}

.card,
boxed-list,
.boxed-list {
    background-color: @card_bg_color;
    border: 1px solid @mm_border;
    border-radius: 12px;
}

dropdown,
popover {
    border-radius: 10px;
}

popover contents {
    background-color: @popover_bg_color;
    border: 1px solid @mm_border_strong;
    border-radius: 10px;
}

scrollbar slider {
    background-color: rgba(217, 72, 15, 0.30);
    border-radius: 999px;
    min-width: 8px;
    min-height: 8px;
}

scrollbar slider:hover {
    background-color: rgba(217, 72, 15, 0.50);
}

"""


# --- Theme registry: built-ins + user themes ------------------------------
# Users make their own themes by dropping plain GTK4 CSS files into
#   ~/.config/mangomod/themes/*.css
# A custom file only needs the selectors it wants to override; the rest
# falls back to the active built-in theme (custom CSS loads on top).

BUILTIN_THEMES: dict[str, tuple[str, str]] = {
    "mango-dark": ("Mango Dark", CSS),
    "ripe-paper": ("Ripe Paper (light)", LIGHT_CSS),
}

USER_THEME_GLOB = "*.css"


def user_themes_dir():
    from pathlib import Path

    from mangomod import config_parser

    d = config_parser.APP_SETTINGS_DIR / "themes"
    return d


def available_themes() -> list[tuple[str, str]]:
    """Return [(theme_id, label)] — built-ins first, then user *.css files."""
    from mangomod import config_parser

    items = [(tid, label) for tid, (label, _css) in BUILTIN_THEMES.items()]
    d = config_parser.APP_SETTINGS_DIR / "themes"
    if d.is_dir():
        for f in sorted(d.glob(USER_THEME_GLOB)):
            if f.is_file():
                items.append((f"user:{f.stem}", f.stem))
    return items


def load_theme_css(theme_id: str) -> tuple[str | None, str | None]:
    """Return (css, error). css is None + error message on failure."""
    from mangomod import config_parser

    if theme_id in BUILTIN_THEMES:
        return BUILTIN_THEMES[theme_id][1], None
    if theme_id.startswith("user:"):
        stem = theme_id[len("user:"):]
        # Refuse path tricks — only a bare stem, file must live in themes dir.
        if not stem or "/" in stem or "\\" in stem or stem.startswith("."):
            return None, f"Invalid theme name: {stem!r}"
        path = config_parser.APP_SETTINGS_DIR / "themes" / f"{stem}.css"
        if not path.is_file():
            return None, f"Theme file not found: {path}"
        try:
            return path.read_text(encoding="utf-8"), None
        except OSError as exc:
            return None, f"Cannot read theme file: {exc}"
    return None, f"Unknown theme: {theme_id!r}"


def check_css_parses(css_text: str) -> str | None:
    """Return None if the CSS parses, else the parser error message."""
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk

    provider = Gtk.CssProvider()
    try:
        provider.load_from_data(css_text.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — surface any parser failure
        return str(exc)
    return None
