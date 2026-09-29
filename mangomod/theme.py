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


STUDIO_CSS = """
/* Workspace Studio: shared layout system, semantic colors for both modes. */
window.mangomod { font-family: "Inter", "Cantarell", sans-serif; font-size: 14px; }
.mm-sidebar-bg { background: @view_bg_color; border-right: 1px solid @mm_border; }
headerbar { min-height: 54px; border-bottom: 1px solid @mm_border; }
.mm-brand .title { font-size: 20px; font-weight: 800; letter-spacing: -0.6px; }
.mm-brand .subtitle { font-size: 9px; letter-spacing: 2px; color: @mm_accent; }
.mm-sidebar-listbox row { padding: 7px 10px; margin: 1px 10px; border-radius: 7px; }
.mm-sidebar-listbox row:selected { background: @mm_accent_dim; color: @mm_accent; box-shadow: inset 3px 0 @mm_accent; }
.mm-sidebar-listbox row:selected image, .mm-sidebar-listbox row:selected label { color: @mm_accent; }
.mm-sidebar-section-label { color: alpha(@window_fg_color, 0.45); font-size: 10px; letter-spacing: 1.2px; margin-top: 12px; }
.mm-search-entry { margin: 12px; padding: 5px; border-radius: 7px; background: @window_bg_color; }
.mm-search-results { margin: 0 10px 8px; background: @card_bg_color; border: 1px solid @mm_border; border-radius: 10px; }
.mm-search-results row { margin: 2px 4px; border-radius: 7px; }
.mm-search-results row:selected, .mm-search-results row:hover { background: @mm_accent_dim; }
.mm-page-title { font-size: 28px; font-weight: 800; letter-spacing: -0.8px; }
.mm-page-content { margin-top: 20px; }
.mm-hero { padding: 30px; border: 1px solid @mm_accent_border; border-radius: 16px; background: linear-gradient(120deg, @mm_accent_dim, @card_bg_color); }
.mm-eyebrow { font-size: 10px; font-weight: 700; letter-spacing: 1.5px; color: alpha(@window_fg_color, 0.55); }
.mm-hero .mm-eyebrow { color: @mm_accent; }
.mm-hero-title { font-size: 36px; font-weight: 800; letter-spacing: -1.2px; }
.mm-hero-description { font-size: 15px; color: alpha(@window_fg_color, 0.65); }
button.suggested-action { background: @mm_accent; color: @window_bg_color; border-radius: 8px; padding: 10px 16px; box-shadow: none; }
button.suggested-action:hover { background: @mm_accent_glow; box-shadow: none; }
.mm-session { padding: 14px 18px; border: 1px solid @mm_border; border-radius: 10px; }
.mm-online { color: #6ccca0; }
.mm-card-title { font-size: 15px; font-weight: 700; }
.mm-card-description { font-size: 12px; color: alpha(@window_fg_color, 0.58); }
flowboxchild { padding: 0; }
button.mm-destination { background: @card_bg_color; padding: 20px; border: 1px solid @mm_border; border-radius: 12px; box-shadow: none; }
button.mm-destination:hover { background: @mm_accent_dim; border-color: @mm_accent_border; }
.mm-tile-icon { color: @mm_accent; margin-bottom: 14px; }
.mm-tile-number { font-family: monospace; font-size: 11px; color: alpha(@window_fg_color, 0.3); }
.mm-config-card { padding: 20px; border: 1px solid @mm_border; border-radius: 12px; background: @card_bg_color; }
.mm-config-path { font-family: monospace; font-size: 12px; color: alpha(@window_fg_color, 0.55); }
.mm-badge { color: @mm_accent; background: @mm_accent_dim; padding: 4px 10px; }
.mm-section-nav { margin-bottom: 10px; }
button.mm-section-tab { background: transparent; border: 1px solid @mm_border; border-radius: 8px; padding: 10px 14px; box-shadow: none; color: alpha(@window_fg_color, 0.65); }
button.mm-section-tab:checked { color: @mm_accent; background: @mm_accent_dim; border-color: @mm_accent_border; }
.mm-save-bar { background: @view_bg_color; border-top: 1px solid @mm_border; padding: 12px 20px; }
.mm-save-status { font-size: 12px; color: alpha(@window_fg_color, 0.65); }
.mm-preview-caption { font-size: 11px; color: alpha(@window_fg_color, 0.5); }
.boxed-list { border-radius: 10px; background: @card_bg_color; }
.mm-preview { background: @view_bg_color; color: @window_fg_color; }
.mm-pane-title, .mm-param-label { color: alpha(@window_fg_color, 0.6); }
.mm-action-block { background: @card_bg_color; }
"""
CSS += """

@define-color mm_accent #f2a56b;
@define-color mm_accent_dark #d88750;
@define-color mm_accent_glow #ffc79e;
@define-color mm_accent_dim rgba(242,165,107,0.10);
@define-color mm_accent_hover rgba(242,165,107,0.18);
@define-color mm_accent_border rgba(242,165,107,0.28);
@define-color window_bg_color #17191d;
@define-color window_fg_color #eceef2;
@define-color view_bg_color #121417;
@define-color view_fg_color #eceef2;
@define-color headerbar_bg_color #17191d;
@define-color card_bg_color #1e2126;
@define-color card_fg_color #eceef2;
@define-color popover_bg_color #24272d;
@define-color popover_fg_color #eceef2;
@define-color dialog_bg_color #1e2126;
@define-color dialog_fg_color #eceef2;
@define-color mm_border rgba(235,239,245,0.08);
@define-color mm_border_strong rgba(235,239,245,0.16);
""" + STUDIO_CSS
LIGHT_CSS += STUDIO_CSS

BUILDER_CSS = """

/* The shortcut is a compact sequence; the side panel changes with selection. */
.mm-builder-workspace { background: @view_bg_color; border: 1px solid @mm_border; border-radius: 16px; padding: 20px; }
.mm-builder-sidebar { background: @card_bg_color; border: 1px solid @mm_border; border-radius: 16px; padding: 18px; }
.mm-builder-canvas { padding: 2px 0; }
.mm-builder-heading { font-size: 17px; font-weight: 700; }
.mm-builder-step { color: @mm_accent; font-size: 11px; font-weight: 700; letter-spacing: 0.06em; }
button.mm-builder-trigger { background: @mm_accent_dim; border: 1px solid @mm_accent_border; border-radius: 13px; padding: 16px; box-shadow: none; }
button.mm-builder-action { background: @card_bg_color; border: 1px solid @mm_border_strong; border-radius: 13px; padding: 15px; box-shadow: none; }
button.mm-builder-action.mm-builder-selected { background: @mm_accent_dim; border-color: @mm_accent; }
button.mm-builder-trigger:hover, button.mm-builder-action:hover { border-color: @mm_accent; }
.mm-builder-number { background: @mm_accent_dim; color: @mm_accent; border-radius: 8px; padding: 8px 11px; font-weight: 700; }
.mm-builder-connector { margin: 0 20px; background: @mm_accent_border; border-radius: 3px; }
button.mm-builder-palette { background: transparent; border: 1px solid @mm_border; border-radius: 10px; padding: 11px 12px; box-shadow: none; }
button.mm-builder-palette:hover { background: @mm_accent_dim; border-color: @mm_accent_border; }
.mm-builder-palette .mm-card-title { font-size: 13px; font-weight: 600; }
button.mm-builder-add { background: transparent; border: 1px dashed @mm_border_strong; border-radius: 10px; padding: 12px; margin-top: 8px; color: @mm_accent; }
.mm-builder-empty { background: @card_bg_color; border: 1px dashed @mm_border_strong; border-radius: 13px; padding: 22px; margin-top: 2px; }
.mm-builder-status { font-size: 12px; color: alpha(@window_fg_color, 0.72); }
.mm-builder-status.error { color: @error_color; }
.mm-builder-footer { background: @card_bg_color; border: 1px solid @mm_border; border-radius: 10px; padding: 9px 12px; }
"""
CSS += BUILDER_CSS
LIGHT_CSS += BUILDER_CSS

# --- Theme registry: built-ins + user themes ------------------------------
# User themes live in ~/.config/mangomod/themes/. Variant files use
# Name.light.css or Name.dark.css; legacy Name.css files act as dark variants.
# Custom CSS overrides the matching Mango base palette.

def _palette_css(base: str, colors: dict[str, str]) -> str:
    """Derive a complete Studio palette while retaining legacy CSS selectors."""
    import re

    for name, color in colors.items():
        pattern = rf"(@define-color\s+{re.escape(name)}\s+)[^;]+;"
        base, count = re.subn(pattern, lambda match: match.group(1) + color + ";", base)
        if not count:
            raise ValueError(f"Unknown theme token: {name}")
    return base


THEME_SWATCHES = {
    "mango-dark": ("#17191d", "#1e2126", "#f2a56b"),
    "ripe-paper": ("#f2f2ef", "#f8f8f5", "#a84320"),
    "niri-violet": ("#11131d", "#1d2030", "#aa8cff"),
    "oasis-teal": ("#101c20", "#19292d", "#57d7c1"),
    "sahara-sand": ("#f4efe6", "#faf6ef", "#8c4b29"),
}

VIOLET_CSS = _palette_css(CSS, {
    "mm_accent": "#aa8cff", "mm_accent_dark": "#8a68d9", "mm_accent_glow": "#c7b7ff",
    "mm_accent_dim": "rgba(170,140,255,0.12)", "mm_accent_hover": "rgba(170,140,255,0.20)",
    "mm_accent_border": "rgba(170,140,255,0.34)",
    "window_bg_color": "#11131d", "view_bg_color": "#151826",
    "card_bg_color": "#1d2030", "popover_bg_color": "#24283a", "dialog_bg_color": "#1d2030",
})
TEAL_CSS = _palette_css(CSS, {
    "mm_accent": "#57d7c1", "mm_accent_dark": "#33bda6", "mm_accent_glow": "#92ebdc",
    "mm_accent_dim": "rgba(87,215,193,0.12)", "mm_accent_hover": "rgba(87,215,193,0.20)",
    "mm_accent_border": "rgba(87,215,193,0.34)",
    "window_bg_color": "#101c20", "view_bg_color": "#122125",
    "card_bg_color": "#19292d", "popover_bg_color": "#223438", "dialog_bg_color": "#19292d",
})
SAND_CSS = _palette_css(LIGHT_CSS, {
    "mm_accent": "#a45b33", "mm_accent_dark": "#804223", "mm_accent_glow": "#cf9877",
    "mm_accent_dim": "rgba(164,91,51,0.10)", "mm_accent_hover": "rgba(164,91,51,0.18)",
    "mm_accent_border": "rgba(164,91,51,0.30)",
    "window_bg_color": "#f4ede1", "view_bg_color": "#eee5d7",
    "card_bg_color": "#fffaf1", "popover_bg_color": "#fffaf1", "dialog_bg_color": "#fffaf1",
})

BUILTIN_THEMES: dict[str, tuple[str, str]] = {
    "mango-dark": ("Mango", CSS),
    "ripe-paper": ("Ripe Paper", LIGHT_CSS),
    "niri-violet": ("Niri Violet", VIOLET_CSS),
    "oasis-teal": ("Oasis Teal", TEAL_CSS),
    "sahara-sand": ("Sahara Sand", SAND_CSS),
}

ARABIC_THEME_NAMES = {
    "mango-dark": "مانجو",
    "ripe-paper": "ورق مانجو",
    "niri-violet": "بنفسجي نيري",
    "oasis-teal": "واحة فيروزية",
    "sahara-sand": "رمال الصحراء",
}

# Each built-in has a distinct Arabic palette alongside right-to-left spacing.
ARABIC_ACCENTS = {
    "mango-dark": ("#ffc28e", "#e89a65"),
    "ripe-paper": ("#eea47d", "#d8835c"),
    "niri-violet": ("#c4a6ff", "#9876de"),
    "oasis-teal": ("#79e5cd", "#42bea9"),
    "sahara-sand": ("#e5ad7f", "#bf855b"),
}
ARABIC_LIGHT_ACCENTS = {
    "mango-dark": ("#914318", "#743713"),
    "ripe-paper": ("#923a1b", "#753017"),
    "niri-violet": ("#603a9d", "#4c2e7d"),
    "oasis-teal": ("#075c53", "#064b44"),
    "sahara-sand": ("#7d4225", "#65351e"),
}

# Five theme families, each with a real light and dark palette. The legacy IDs
# and mode-less CSS above remain available to older installations and callers.
THEME_PALETTES = {
    "mango-dark": {
        "dark": ("#17191d", "#121417", "#1e2126", "#24272d", "#f2a56b"),
        "light": ("#f6f0e6", "#efe7db", "#fbf7f0", "#fdf9f3", "#99501c"),
    },
    "ripe-paper": {
        "dark": ("#24201d", "#1d1a18", "#302a25", "#39312b", "#ee9b6b"),
        "light": ("#f2f2ef", "#e9eae7", "#f8f8f5", "#fbfbf9", "#a84320"),
    },
    "niri-violet": {
        "dark": ("#11131d", "#151826", "#1d2030", "#24283a", "#aa8cff"),
        "light": ("#f3f1f8", "#e9e6f1", "#f8f6fc", "#fbfafe", "#6741a5"),
    },
    "oasis-teal": {
        "dark": ("#101c20", "#122125", "#19292d", "#223438", "#57d7c1"),
        "light": ("#eef4f1", "#e3ece7", "#f6f9f6", "#fafcfa", "#08695d"),
    },
    "sahara-sand": {
        "dark": ("#201b18", "#191512", "#2b241e", "#362c24", "#e6aa75"),
        "light": ("#f4efe6", "#eae2d5", "#faf6ef", "#fdf9f2", "#8c4b29"),
    },
}


LIGHT_TEXT = {
    "mango-dark": ("#342b22", "#595044"),
    "ripe-paper": ("#292d31", "#555d62"),
    "niri-violet": ("#302b3b", "#555061"),
    "oasis-teal": ("#26332e", "#4c5d55"),
    "sahara-sand": ("#332c24", "#5b5145"),
}

LIGHT_STYLE_CSS = {
    # Warm stationery with soft, inset groupings.
    "mango-dark": """
.mm-hero, .mm-builder-workspace { border-radius: 18px; }
.mm-config-card, .mm-builder-sidebar { box-shadow: inset 0 1px rgba(255,255,255,0.55); }
.mm-sidebar-listbox row:selected { box-shadow: inset 3px 0 @mm_accent; }
""",
    # Editorial paper: flatter surfaces, sharper separators and tighter cards.
    "ripe-paper": """
.mm-hero, .mm-builder-workspace, .mm-builder-sidebar, .mm-config-card { border-radius: 7px; box-shadow: none; }
.mm-sidebar-listbox row { border-radius: 5px; }
.mm-save-bar { border-top: 2px solid @mm_border_strong; }
""",
    # Lavender glass: rounded cards with a restrained tinted hover surface.
    "niri-violet": """
.mm-hero, .mm-builder-workspace, .mm-builder-sidebar, .mm-config-card { border-radius: 18px; }
.mm-search-results, .boxed-list { box-shadow: 0 2px 6px rgba(54,42,79,0.07); }
.mm-sidebar-listbox row:hover { background: rgba(103,65,165,0.08); }
""",
    # Mint workspace: clean outlines and minimal elevation.
    "oasis-teal": """
.mm-hero, .mm-builder-workspace, .mm-builder-sidebar, .mm-config-card { border-radius: 10px; box-shadow: none; }
.mm-sidebar-listbox row:selected { box-shadow: inset 3px 0 @mm_accent; }
.mm-search-results { border-color: rgba(8,105,93,0.18); }
""",
    # Sand and clay: gently rounded panels with warm, quiet separators.
    "sahara-sand": """
.mm-hero, .mm-builder-workspace, .mm-builder-sidebar, .mm-config-card { border-radius: 12px; }
.mm-sidebar-listbox row:hover { background: rgba(140,75,41,0.07); }
.mm-search-results, .boxed-list { box-shadow: 0 1px 4px rgba(70,49,31,0.06); }
""",
}

LIGHT_COMPONENT_CSS = """
/* Calm daylight surfaces, legible muted text, and clear focus states. */
.navigation-sidebar { background-color: @view_bg_color; }
.mm-hero { background: @card_bg_color; }
.mm-preview { background: @card_bg_color; color: @window_fg_color; border: 1px solid @mm_border; }
.dim-label, .mm-card-description, .mm-config-path, .mm-save-status,
.mm-preview-caption, .mm-pane-title, .mm-param-label, .mm-builder-status,
.mm-sidebar-section-label, .mm-eyebrow, .mm-tile-number { color: @mm_text_muted; }
button.suggested-action { background: @mm_accent; color: @mm_accent_text; border: 1px solid @mm_accent_dark; box-shadow: 0 1px 3px rgba(35,30,24,0.12); }
button.suggested-action:hover { background: @mm_accent_glow; box-shadow: 0 2px 5px rgba(35,30,24,0.16); }
button:focus, entry:focus, dropdown:focus, .mm-search-entry:focus-within { outline: 2px solid @mm_accent; outline-offset: 1px; }
button:disabled { opacity: 0.66; }
button.mm-destination, button.mm-builder-action, button.mm-builder-palette { box-shadow: 0 1px 2px rgba(35,30,24,0.06); }
button.mm-destination:hover, button.mm-builder-action:hover, button.mm-builder-palette:hover { box-shadow: 0 2px 5px rgba(35,30,24,0.10); }
"""


def _mode_css(theme_id: str, mode: str) -> str:
    background, view, card, popover, accent = THEME_PALETTES[theme_id][mode]
    red, green, blue = (int(accent[i:i + 2], 16) for i in (1, 3, 5))
    colors = {
        "mm_accent": accent,
        "mm_accent_dark": accent,
        "mm_accent_glow": accent,
        "mm_accent_dim": f"rgba({red},{green},{blue},0.11)",
        "mm_accent_hover": f"rgba({red},{green},{blue},0.19)",
        "mm_accent_border": f"rgba({red},{green},{blue},0.32)",
        "window_bg_color": background,
        "view_bg_color": view,
        "card_bg_color": card,
        "popover_bg_color": popover,
        "dialog_bg_color": card,
        "headerbar_bg_color": background,
    }
    if mode == "light":
        text_color, muted = LIGHT_TEXT[theme_id]
        border = {
            "mango-dark": "rgba(93,65,36,0.15)",
            "ripe-paper": "rgba(66,74,80,0.16)",
            "niri-violet": "rgba(83,66,115,0.16)",
            "oasis-teal": "rgba(51,91,78,0.16)",
            "sahara-sand": "rgba(93,67,43,0.16)",
        }[theme_id]
        colors.update({
            "window_fg_color": text_color,
            "view_fg_color": text_color,
            "card_fg_color": text_color,
            "popover_fg_color": text_color,
            "dialog_fg_color": text_color,
            "mm_border": border,
            "mm_border_strong": border.replace("0.16", "0.27"),
        })
    css = _palette_css(LIGHT_CSS if mode == "light" else CSS, colors)
    if mode == "light":
        text_color, muted = LIGHT_TEXT[theme_id]
        css += f"\n@define-color mm_text_muted {muted};\n@define-color mm_accent_text #ffffff;\n"
        css += LIGHT_COMPONENT_CSS + LIGHT_STYLE_CSS[theme_id]
    return css


def theme_name(theme_id: str, language: str = "en") -> str:
    if theme_id in BUILTIN_THEMES:
        return ARABIC_THEME_NAMES[theme_id] if language == "ar" else BUILTIN_THEMES[theme_id][0]
    if theme_id.startswith("user:"):
        return theme_id[5:]
    return theme_id


def theme_swatches(theme_id: str, language: str = "en", mode: str | None = None) -> tuple[str, str, str]:
    """Return background, card and accent colors for the Preferences preview."""
    if theme_id in THEME_SWATCHES:
        colors = THEME_SWATCHES[theme_id] if mode not in ("light", "dark") else (
            THEME_PALETTES[theme_id][mode][0], THEME_PALETTES[theme_id][mode][2], THEME_PALETTES[theme_id][mode][4]
        )
        if language == "ar":
            accent = (ARABIC_LIGHT_ACCENTS if mode == "light" else ARABIC_ACCENTS)[theme_id][0]
            return (*colors[:2], accent)
        return colors
    import re

    css, _error = load_theme_css(theme_id, language, mode)
    colors = list(THEME_SWATCHES["mango-dark"])
    if css:
        for index, token in enumerate(("window_bg_color", "card_bg_color", "mm_accent")):
            values = re.findall(rf"@define-color\s+{token}\s+(#[0-9a-fA-F]{{6,8}})\s*;", css)
            if values:
                colors[index] = values[-1]
    return tuple(colors)

USER_THEME_GLOB = "*.css"


def user_themes_dir():
    from pathlib import Path

    from mangomod import config_parser

    d = config_parser.APP_SETTINGS_DIR / "themes"
    return d


def contrast_ratio(first: str, second: str) -> float:
    def luminance(color):
        values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    low, high = sorted((luminance(first), luminance(second)))
    return (high + .05) / (low + .05)


def readable_text(background: str) -> str:
    return max(('#20252b', '#f4f6f8'), key=lambda text: contrast_ratio(background, text))


def create_custom_theme(name: str, mode: str, background: str, card: str, accent: str) -> tuple[str | None, str | None]:
    """Add one light or dark variant without replacing an existing variant."""
    import re

    name = name.strip()
    if not name or len(name) > 48 or name.startswith(".") or any(c in name for c in "/\\\n\r\0"):
        return None, "Choose a theme name without path characters."
    if mode not in ("light", "dark"):
        return None, "Choose Light or Dark."
    if not all(re.fullmatch(r"#[0-9a-fA-F]{6}", value) for value in (background, card, accent)):
        return None, "Use six-digit hex colors such as #4b7f71."
    red, green, blue = (int(accent[i:i + 2], 16) for i in (1, 3, 5))
    css = "\n".join((
        f"@define-color window_bg_color {background};",
        f"@define-color headerbar_bg_color {background};",
        f"@define-color view_bg_color {background};",
        f"@define-color card_bg_color {card};",
        f"@define-color popover_bg_color {card};",
        f"@define-color dialog_bg_color {card};",
        f"@define-color window_fg_color {readable_text(background)};",
        f"@define-color view_fg_color {readable_text(background)};",
        f"@define-color card_fg_color {readable_text(card)};",
        f"@define-color popover_fg_color {readable_text(card)};",
        f"@define-color dialog_fg_color {readable_text(card)};",
        f"@define-color mm_accent_text {readable_text(accent)};",
        f"@define-color mm_accent {accent};",
        f"@define-color mm_accent_dark {accent};",
        f"@define-color mm_accent_glow {accent};",
        f"@define-color mm_accent_dim rgba({red},{green},{blue},0.11);",
        f"@define-color mm_accent_hover rgba({red},{green},{blue},0.19);",
        f"@define-color mm_accent_border rgba({red},{green},{blue},0.32);",
        "",
    ))
    error = check_css_parses(css)
    if error:
        return None, error
    directory = user_themes_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        if mode == "dark" and (directory / f"{name}.css").exists():
            return None, "This theme already has a Dark variant."
        with (directory / f"{name}.{mode}.css").open("x", encoding="utf-8") as stream:
            stream.write(css)
    except FileExistsError:
        return None, f"This theme already has a {mode.title()} variant."
    except OSError as exc:
        return None, str(exc)
    return f"user:{name}", None


def available_themes(language: str = "en") -> list[tuple[str, str]]:
    """Return built-ins and one entry per user theme, regardless of variants."""
    items = [(tid, theme_name(tid, language)) for tid in BUILTIN_THEMES]
    d = user_themes_dir()
    if d.is_dir():
        names = set()
        for f in sorted(d.glob(USER_THEME_GLOB)):
            if f.is_file():
                stem = f.stem
                if stem.endswith((".light", ".dark")):
                    stem = stem.rsplit(".", 1)[0]
                names.add(stem)
        items.extend((f"user:{name}", theme_name(f"user:{name}", language)) for name in sorted(names))
    return items


def delete_custom_theme(theme_id: str) -> tuple[bool, str | None]:
    """Delete every saved variant of a user theme, including legacy CSS."""
    if not theme_id.startswith("user:"):
        return False, "Built-in themes cannot be deleted."
    stem = theme_id[5:]
    if not stem or stem.startswith(".") or any(char in stem for char in "/\\\n\r\0"):
        return False, "Choose a theme name without path characters."
    directory = user_themes_dir()
    paths = [directory / f"{stem}{suffix}.css" for suffix in ("", ".light", ".dark")]
    existing = [path for path in paths if path.is_file() or path.is_symlink()]
    if not existing:
        return False, "Theme not found."
    try:
        for path in existing:
            path.unlink()
    except OSError as exc:
        return False, str(exc)
    return True, None


def load_theme_css(theme_id: str, language: str = "en", mode: str | None = None) -> tuple[str | None, str | None]:
    """Return (css, error). css is None + error message on failure."""
    if theme_id in BUILTIN_THEMES:
        css = _mode_css(theme_id, mode) if mode in ("light", "dark") else BUILTIN_THEMES[theme_id][1]
        if language == "ar":
            accent, dark = (ARABIC_LIGHT_ACCENTS if mode == "light" else ARABIC_ACCENTS)[theme_id]
            css = _palette_css(css, {"mm_accent": accent, "mm_accent_dark": dark})
            css += "\n.mangomod { font-family: 'Noto Sans Arabic', 'DejaVu Sans', sans-serif; }\n"
            css += ".mm-builder-action { border-right: 3px solid @mm_accent; }\n"
        return css, None
    if theme_id.startswith("user:"):
        stem = theme_id[len("user:"):]
        # Refuse path tricks — only a bare stem, file must live in themes dir.
        if not stem or "/" in stem or "\\" in stem or stem.startswith("."):
            return None, f"Invalid theme name: {stem!r}"
        directory = user_themes_dir()
        legacy = directory / f"{stem}.css"
        if mode in ("light", "dark"):
            path = directory / f"{stem}.{mode}.css"
            if mode == "dark" and not path.is_file() and legacy.is_file():
                path = legacy
        else:
            path = legacy if legacy.is_file() else next(
                (candidate for candidate in (directory / f"{stem}.dark.css", directory / f"{stem}.light.css") if candidate.is_file()),
                directory / f"{stem}.dark.css",
            )
        if not path.is_file():
            if mode in ("light", "dark"):
                return None, f"This theme has no {mode.title()} variant. Create it first."
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
    errors = []
    provider.connect('parsing-error', lambda _provider, _section, error:
                     errors.append(str(error)) if error.domain != 'gtk-css-parser-warning-quark' else None)
    try:
        provider.load_from_data(css_text.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — surface any parser failure
        return str(exc)
    return '\n'.join(errors) if errors else None
