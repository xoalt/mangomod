"""Illustrative workspace preview using the current appearance settings."""
import math
from gi.repository import Gtk


class WorkspacePreview(Gtk.DrawingArea):
    def __init__(self, document):
        super().__init__()
        self._document = document
        self.set_content_height(210)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)
        self.update_property([Gtk.AccessibleProperty.LABEL], ["Illustrative preview of window colors, borders, radius, and gaps"])

    def _draw(self, area, cr, width, height):
        from mangomod.pages.appearance import hex_to_rgba
        doc = self._document()

        def color(key, default):
            rgba = hex_to_rgba(doc.get_setting(key, default))
            cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

        def rect(x, y, w, h, radius):
            radius = min(max(0, radius), w / 2, h / 2)
            cr.new_sub_path()
            for cx, cy, a in [(x+w-radius,y+radius,-90), (x+w-radius,y+h-radius,0),
                              (x+radius,y+h-radius,90), (x+radius,y+radius,180)]:
                cr.arc(cx, cy, radius, math.radians(a), math.radians(a+90))
            cr.close_path()

        color("rootcolor", "#101419")
        rect(0, 0, width, height, 12)
        cr.fill()
        # Scale geometry for illustration; this is not a compositor screenshot.
        ox = min(48, max(12, doc.get_int("gappoh", 8)))
        oy = min(45, max(12, doc.get_int("gappov", 8)))
        gx = min(40, max(4, doc.get_int("gappih", 4)))
        gy = min(40, max(4, doc.get_int("gappiv", 4)))
        usable_w, usable_h = width - 2*ox, height - 2*oy
        master_w = (usable_w-gx)*0.58
        side_w = usable_w-master_w-gx
        for index, (x,y,w,h) in enumerate([
            (ox,oy,master_w,usable_h),
            (ox+master_w+gx,oy,side_w,(usable_h-gy)/2),
            (ox+master_w+gx,oy+(usable_h+gy)/2,side_w,(usable_h-gy)/2),
        ]):
            rect(x,y,w,h,doc.get_int("border_radius",4))
            cr.set_source_rgb(.14,.16,.19)
            cr.fill_preserve()
            border = max(0, doc.get_int("borderpx",3))
            color("focuscolor" if index == 0 else "bordercolor", "#f2a56b" if index == 0 else "#444444")
            cr.set_line_width(border)
            if border:
                cr.stroke()
            else:
                cr.new_path()
            cr.set_source_rgba(.85,.88,.92,.18)
            for line, fraction in enumerate([.35,.7,.55]):
                cr.rectangle(x+16,y+20+line*10,max(0,(w-32)*fraction),3)
                cr.fill()
