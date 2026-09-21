"""Window visual effects page (Blur, Shadows, Opacity, Dimming)."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from mangomod.pages.appearance import hex_to_rgba, rgba_to_mango_hex
from mangomod.pages.base import BasePage


class WindowEffectsPage(BasePage):
    def build(self) -> Gtk.Widget:
        tb, _, _, content = self._make_toolbar_page("Window Effects")
        self._content = content
        self._build_content()
        return tb

    def _build_content(self) -> None:
        content = self._content
        doc = self._doc

        # --- Blur Settings ---
        blur_grp = Adw.PreferencesGroup(
            title="Blur Effects",
            description="Background blur behind translucent surfaces (scenefx)",
        )

        blur_on = Adw.SwitchRow(title="Enable Window Blur")
        blur_on.set_active(doc.get_bool("blur", False))
        blur_on.connect("notify::active", lambda r, _: self._on_bool_change("blur", r.get_active()))
        blur_grp.add(blur_on)

        blur_layer_on = Adw.SwitchRow(title="Blur Layer Shells", subtitle="Apply blur to bars, launchers, and lockscreen")
        blur_layer_on.set_active(doc.get_bool("blur_layer", False))
        blur_layer_on.connect("notify::active", lambda r, _: self._on_bool_change("blur_layer", r.get_active()))
        blur_grp.add(blur_layer_on)

        blur_opt = Adw.SwitchRow(title="Optimized Blur", subtitle="Fast dual-Kawase rendering pass")
        blur_opt.set_active(doc.get_bool("blur_optimized", True))
        blur_opt.connect("notify::active", lambda r, _: self._on_bool_change("blur_optimized", r.get_active()))
        blur_grp.add(blur_opt)

        passes_adj = Gtk.Adjustment(value=doc.get_int("blur_params_num_passes", 2), lower=1, upper=8, step_increment=1)
        passes_row = Adw.SpinRow(title="Blur Passes", adjustment=passes_adj)
        passes_row.connect("notify::value", lambda r, _: self._on_int_change("blur_params_num_passes", int(r.get_value())))
        blur_grp.add(passes_row)

        rad_adj = Gtk.Adjustment(value=doc.get_int("blur_params_radius", 5), lower=1, upper=30, step_increment=1)
        rad_row = Adw.SpinRow(title="Blur Radius", adjustment=rad_adj)
        rad_row.connect("notify::value", lambda r, _: self._on_int_change("blur_params_radius", int(r.get_value())))
        blur_grp.add(rad_row)

        bright_adj = Gtk.Adjustment(value=doc.get_float("blur_params_brightness", 0.9), lower=0.1, upper=2.0, step_increment=0.05)
        bright_row = Adw.SpinRow(title="Blur Brightness", adjustment=bright_adj, digits=2)
        bright_row.connect("notify::value", lambda r, _: self._on_float_change("blur_params_brightness", float(r.get_value())))
        blur_grp.add(bright_row)

        noise_adj = Gtk.Adjustment(value=doc.get_float("blur_params_noise", 0.02), lower=0.0, upper=0.5, step_increment=0.01)
        noise_row = Adw.SpinRow(title="Noise Texture", subtitle="Add grain to eliminate banding", adjustment=noise_adj, digits=2)
        noise_row.connect("notify::value", lambda r, _: self._on_float_change("blur_params_noise", float(r.get_value())))
        blur_grp.add(noise_row)

        content.append(blur_grp)

        # --- Shadows ---
        shadow_grp = Adw.PreferencesGroup(
            title="Drop Shadows",
            description="Window and layer shadow effects",
        )

        shadow_on = Adw.SwitchRow(title="Enable Window Shadows")
        shadow_on.set_active(doc.get_bool("shadows", False))
        shadow_on.connect("notify::active", lambda r, _: self._on_bool_change("shadows", r.get_active()))
        shadow_grp.add(shadow_on)

        shadow_layer_on = Adw.SwitchRow(title="Shadows on Layer Shells")
        shadow_layer_on.set_active(doc.get_bool("layer_shadows", False))
        shadow_layer_on.connect("notify::active", lambda r, _: self._on_bool_change("layer_shadows", r.get_active()))
        shadow_grp.add(shadow_layer_on)

        shadow_only_float = Adw.SwitchRow(title="Shadows Only on Floating Windows")
        shadow_only_float.set_active(doc.get_bool("shadow_only_floating", True))
        shadow_only_float.connect("notify::active", lambda r, _: self._on_bool_change("shadow_only_floating", r.get_active()))
        shadow_grp.add(shadow_only_float)

        s_size_adj = Gtk.Adjustment(value=doc.get_int("shadows_size", 10), lower=0, upper=60, step_increment=2)
        s_size_row = Adw.SpinRow(title="Shadow Size (px)", adjustment=s_size_adj)
        s_size_row.connect("notify::value", lambda r, _: self._on_int_change("shadows_size", int(r.get_value())))
        shadow_grp.add(s_size_row)

        s_blur_adj = Gtk.Adjustment(value=doc.get_int("shadows_blur", 15), lower=0, upper=60, step_increment=2)
        s_blur_row = Adw.SpinRow(title="Shadow Softness / Blur (px)", adjustment=s_blur_adj)
        s_blur_row.connect("notify::value", lambda r, _: self._on_int_change("shadows_blur", int(r.get_value())))
        shadow_grp.add(s_blur_row)

        cur_scolor = doc.get_setting("shadowscolor", "0x000000ff")
        scolor_row = Adw.ActionRow(title="Shadow Color", subtitle=cur_scolor)
        s_dialog = Gtk.ColorDialog(with_alpha=True)
        s_btn = Gtk.ColorDialogButton(dialog=s_dialog)
        s_btn.set_rgba(hex_to_rgba(cur_scolor))

        def _on_scolor_set(button, _):
            new_hex = rgba_to_mango_hex(button.get_rgba())
            self._doc.set_setting("shadowscolor", new_hex)
            scolor_row.set_subtitle(new_hex)
            self._commit("change shadowscolor")

        s_btn.connect("notify::rgba", _on_scolor_set)
        scolor_row.add_suffix(s_btn)
        shadow_grp.add(scolor_row)

        content.append(shadow_grp)

        # --- Opacity & Dimming ---
        opa_grp = Adw.PreferencesGroup(title="Opacity and Dimming", description="Translucency and inactive window dimming")

        f_opa_adj = Gtk.Adjustment(value=doc.get_float("focused_opacity", 1.0), lower=0.1, upper=1.0, step_increment=0.05)
        f_opa_row = Adw.SpinRow(title="Focused Window Opacity", adjustment=f_opa_adj, digits=2)
        f_opa_row.connect("notify::value", lambda r, _: self._on_float_change("focused_opacity", float(r.get_value())))
        opa_grp.add(f_opa_row)

        uf_opa_adj = Gtk.Adjustment(value=doc.get_float("unfocused_opacity", 1.0), lower=0.1, upper=1.0, step_increment=0.05)
        uf_opa_row = Adw.SpinRow(title="Unfocused Window Opacity", adjustment=uf_opa_adj, digits=2)
        uf_opa_row.connect("notify::value", lambda r, _: self._on_float_change("unfocused_opacity", float(r.get_value())))
        opa_grp.add(uf_opa_row)

        dim_on = Adw.SwitchRow(title="Enable Inactive Window Dimming")
        dim_on.set_active(doc.get_bool("dim_enable", False))
        dim_on.connect("notify::active", lambda r, _: self._on_bool_change("dim_enable", r.get_active()))
        opa_grp.add(dim_on)

        content.append(opa_grp)

    def _on_int_change(self, key: str, value: int) -> None:
        self._doc.set_setting(key, value)
        self._commit(f"update {key}")

    def _on_float_change(self, key: str, value: float) -> None:
        self._doc.set_setting(key, f"{value:.2f}")
        self._commit(f"update {key}")

    def _on_bool_change(self, key: str, value: bool) -> None:
        self._doc.set_setting(key, 1 if value else 0)
        self._commit(f"update {key}")
