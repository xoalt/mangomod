"""Optional modern dialogs with libadwaita 1.4 window fallbacks."""
import gi

gi.require_version("Adw", "1")
from gi.repository import Adw


def set_form_content(dialog, header, page, language):
    """Use one owner and one header for ordinary form dialogs."""
    from mangomod.i18n import localize_tree
    parent = dialog.get_transient_for()
    if parent is not None:
        dialog.set_application(parent.get_application())
    dialog.set_default_size(560, 600)
    toolbar = Adw.ToolbarView()
    toolbar.add_top_bar(header)
    page.set_vexpand(True)
    toolbar.set_content(page)
    dialog.set_content(toolbar)
    localize_tree(dialog, language)


def present_content_dialog(parent, child, title, width, height):
    if hasattr(Adw, "Dialog"):
        dialog = Adw.Dialog(title=title, content_width=width, content_height=height)
        dialog.set_child(child)
        dialog.present(parent)
    else:
        dialog = Adw.Window(title=title, transient_for=parent, modal=True)
        dialog.set_default_size(width, height)
        dialog.set_content(child)
        dialog.present()
    return dialog


def new_about_window(parent):
    if hasattr(Adw, "AboutDialog"):
        about = Adw.AboutDialog()
        return about, lambda: about.present(parent)
    about = Adw.AboutWindow(transient_for=parent, modal=True)
    return about, about.present


def runtime_requirement_error(gtk_version, adw_version):
    """The minimum APIs used by the existing editors and navigation."""
    if tuple(gtk_version) < (4, 10, 0):
        return "MangoMod requires GTK 4.10 or newer."
    if tuple(adw_version) < (1, 4, 0):
        return "MangoMod requires libadwaita 1.4 or newer."
    return None
