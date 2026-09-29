"""Task-level section navigation for long preference editors."""
from gi.repository import Adw, Gtk


def organize_sections(content: Gtk.Box) -> None:
    """Turn long preference forms into named, keyboard-accessible sections."""
    groups = []
    child = content.get_first_child()
    while child:
        if isinstance(child, Adw.PreferencesGroup):
            groups.append(child)
        child = child.get_next_sibling()
    if len(groups) < 2:
        return
    nav = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                      max_children_per_line=4, min_children_per_line=1,
                      column_spacing=6, row_spacing=6, homogeneous=False)
    nav.add_css_class("mm-section-nav")
    stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
    stack.set_vhomogeneous(False)
    stack.set_hexpand(True)
    first = None
    for index, group in enumerate(groups):
        content.remove(group)
        title = group.get_title() or f"Section {index + 1}"
        button = Gtk.ToggleButton(label=title)
        button.add_css_class("mm-section-tab")
        if first is None:
            first = button
        else:
            button.set_group(first)
        stack.add_named(group, str(index))
        button.connect("toggled", lambda b, name=str(index): stack.set_visible_child_name(name) if b.get_active() else None)
        nav.insert(button, -1)
    first.set_active(True)
    content.append(nav)
    content.append(stack)
