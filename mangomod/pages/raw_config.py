"""Raw configuration text editor page with syntax validation and file selector."""

from __future__ import annotations

from pathlib import Path
from threading import Thread

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk, Pango

from mangomod import config_parser, mango_ipc
from mangomod.pages.base import BasePage
from mangomod.ui_compat import set_form_content


class RawConfigPage(BasePage):
    def __init__(self, window):
        super().__init__(window)
        self._text_view: Gtk.TextView | None = None
        self._buffer: Gtk.TextBuffer | None = None
        self._active_file: Path | None = None
        self._diagnostics_label: Gtk.Label | None = None
        self._file_dropdown: Gtk.DropDown | None = None
        self._loading_buffer = False
        self._user_action_depth = 0
        self._validation_timer = None
        self._validation_generation = 0
        self._validating = False
        self._disposed = False

    def build(self) -> Gtk.Widget:
        tb, header, _, content = self._make_toolbar_page("Raw Config Editor")
        self._content = content

        # Validation button
        val_btn = Gtk.Button(label="Validate")
        val_btn.add_css_class("flat")
        val_btn.connect("clicked", lambda *_: self._validate_current_text())
        header.pack_end(val_btn)

        # Revert button
        revert_btn = Gtk.Button(label="Revert")
        revert_btn.add_css_class("flat")
        revert_btn.connect("clicked", lambda *_: self._revert_text())
        header.pack_end(revert_btn)
        reload_btn = Gtk.Button(icon_name='view-refresh-symbolic')
        reload_btn.set_tooltip_text('Reload files from disk')
        reload_btn.connect('clicked', lambda *_: self._win.reload_from_disk())
        header.pack_end(reload_btn)

        # Add-file button: create a new .conf next to the main config and
        # wire it in with a real `source=` line so mango actually loads it.
        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Add Config File")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", lambda *_: self._open_add_file_dialog())
        header.pack_end(add_btn)

        self._build_content()
        self._queue_validation()
        return tb

    def refresh(self) -> None:
        while child := self._content.get_first_child():
            self._content.remove(child)
        self._build_content()

    def _build_content(self) -> None:
        content = self._content
        self._file_dropdown = None

        # File selector dropdown (if multi-file)
        self._active_file = config_parser.MANGO_CONFIG
        if self._win.app_state.is_multi_file:
            selector_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lbl = Gtk.Label(label="Editing File:")
            lbl.add_css_class("dim-label")
            selector_box.append(lbl)

            file_names = [str(config_parser.MANGO_CONFIG)] + [str(p) for _, p in self._win.app_state.include_docs]
            dropdown = Gtk.DropDown.new_from_strings(file_names)
            dropdown.connect("notify::selected", self._on_file_selected)
            self._file_dropdown = dropdown
            selector_box.append(dropdown)

            content.append(selector_box)

        # Diagnostics / Validation message bar
        self._diagnostics_label = Gtk.Label(label="", xalign=0)
        self._diagnostics_label.set_wrap(True)
        self._diagnostics_label.set_visible(False)
        content.append(self._diagnostics_label)

        # Text Editor Area
        editor_frame = Gtk.Frame()
        editor_frame.add_css_class("card")
        editor_frame.set_vexpand(True)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(480)

        self._text_view = Gtk.TextView()
        self._text_view.set_direction(Gtk.TextDirection.LTR)
        self._text_view.set_monospace(True)
        self._text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self._text_view.set_left_margin(12)
        self._text_view.set_right_margin(12)
        self._text_view.set_top_margin(12)
        self._text_view.set_bottom_margin(12)

        self._buffer = self._text_view.get_buffer()
        self._buffer.set_text(self._win.app_state.doc.serialize())
        self._buffer.connect("changed", self._on_buffer_changed)
        self._buffer.connect('begin-user-action', self._begin_edit)
        self._buffer.connect('end-user-action', self._end_edit)

        scroller.set_child(self._text_view)
        editor_frame.set_child(scroller)
        content.append(editor_frame)

    def _on_file_selected(self, dropdown, _):
        idx = dropdown.get_selected()
        if idx == 0:
            self._active_file = config_parser.MANGO_CONFIG
            self._set_buffer(self._win.app_state.doc.serialize())
        else:
            sub_doc, sub_path = self._win.app_state.include_docs[idx - 1]
            self._active_file = sub_path
            self._set_buffer(sub_doc.serialize())

    def _set_buffer(self, text):
        self._loading_buffer = True
        try:
            self._buffer.set_text(text)
        finally:
            self._loading_buffer = False

    def _on_buffer_changed(self, buffer: Gtk.TextBuffer) -> None:
        if self._loading_buffer:
            return
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        text = buffer.get_text(start, end, True)
        self._replace_active(text)
        self._queue_validation()
        if self._user_action_depth == 0:
            self._commit("raw config edit")

    def _begin_edit(self, *_):
        self._user_action_depth += 1

    def _end_edit(self, *_):
        self._user_action_depth = max(0, self._user_action_depth - 1)
        if self._user_action_depth == 0:
            self._commit('raw config edit')

    def _replace_active(self, text):
        if self._active_file == config_parser.MANGO_CONFIG:
            new_doc = config_parser.parse_config_text(text, self._active_file)
            self._win.app_state.doc = new_doc
        else:
            state = self._win.app_state
            state.include_docs = [(config_parser.parse_config_text(text, path) if path == self._active_file else doc, path)
                                  for doc, path in state.include_docs]

    def _validate_current_text(self) -> None:
        self._queue_validation(delay=1)

    def _queue_validation(self, delay=600):
        self._validation_generation += 1
        if self._validation_timer is not None:
            GLib.source_remove(self._validation_timer)
        self._diagnostics_label.set_visible(True)
        for css in ('error', 'warning', 'success'):
            self._diagnostics_label.remove_css_class(css)
        self._diagnostics_label.set_text(self._win.tr('Checking with Mango…'))
        self._validation_timer = GLib.timeout_add(delay, self._start_validation)

    def _start_validation(self):
        if self._validating:
            return True
        self._validation_timer = None
        self._validating = True
        generation = self._validation_generation
        documents = [(config_parser.parse_config_text(text, Path(path)), Path(path))
                     for path, text in self._win.app_state.snapshot().items()]
        def check():
            try:
                result = config_parser.validate_documents(documents)
            except Exception as exc:
                result = (False, str(exc))
            GLib.idle_add(self._show_validation, generation, result)
        Thread(target=check, daemon=True, name='mangomod-validator').start()
        return False

    def _show_validation(self, generation, result):
        self._validating = False
        if self._disposed or generation != self._validation_generation:
            return False
        ok, message = result
        title = self._win.tr('Configuration Valid' if ok else 'Validation Error')
        self._diagnostics_label.set_text(title + '\n' + message)
        for css in ('error', 'warning', 'success'):
            self._diagnostics_label.remove_css_class(css)
        self._diagnostics_label.add_css_class('error' if not ok else
                                             'success' if message == 'Config syntax OK' else 'warning')
        return False

    def select_file(self, path):
        if self._file_dropdown:
            paths = [p for _, p in self._win.app_state.documents()]
            if path in paths:
                self._file_dropdown.set_selected(paths.index(path))

    def dispose(self):
        self._disposed = True
        if self._validation_timer is not None:
            GLib.source_remove(self._validation_timer)
            self._validation_timer = None

    def _revert_text(self) -> None:
        if self._buffer:
            text = self._win.app_state.original_text(self._active_file)
            self._set_buffer(text)
            self._replace_active(text)
            self._commit('revert config file')
            self._queue_validation()
            self.show_toast("Reverted raw configuration")

    def _open_add_file_dialog(self) -> None:
        dialog = Adw.Window(title="New Config File", transient_for=self._win, modal=True)
        dialog.set_default_size(440, 360)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(
            title="File Details",
            description=f"Created next to {config_parser.MANGO_CONFIG.name}, or pick an existing file",
        )

        name_entry = Adw.EntryRow(title="File Name or Path")
        name_entry.set_text("custom.conf")
        group.add(name_entry)

        # Browse button: native file chooser for an existing .conf.
        picked: dict = {"file": None}

        def _use_picked(gfile) -> None:
            picked["file"] = gfile
            name_entry.set_text(gfile.get_path() or "")

        browse_row = Adw.ActionRow(
            use_markup=False,
            title="Browse for an existing file",
            subtitle="Or drop a file onto the name field above",
        )
        browse_btn = Gtk.Button(label="Browse…")
        browse_btn.add_css_class("flat")

        def _on_browse(*_):
            chooser = Gtk.FileChooserNative.new(
                "Choose Config File",
                dialog,
                Gtk.FileChooserAction.OPEN,
                "_Open",
                "_Cancel",
            )
            filt = Gtk.FileFilter()
            filt.set_name("Config files (*.conf)")
            filt.add_pattern("*.conf")
            chooser.add_filter(filt)
            any_filt = Gtk.FileFilter()
            any_filt.set_name("All files")
            any_filt.add_pattern("*")
            chooser.add_filter(any_filt)

            def _on_response(native, response: int) -> None:
                if response == Gtk.ResponseType.ACCEPT:
                    gfile = native.get_file()
                    if gfile is not None:
                        _use_picked(gfile)

            chooser.connect("response", _on_response)
            chooser.show()

        browse_btn.connect("clicked", _on_browse)
        browse_row.add_suffix(browse_btn)
        group.add(browse_row)

        # Drag & drop a file onto the name field.
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)

        def _on_drop(_target, value, _x, _y) -> bool:
            try:
                files = value.get_files()
            except Exception:
                return False
            if files:
                _use_picked(files[0])
                self.show_toast(f"Picked {files[0].get_basename()}")
                return True
            return False

        drop_target.connect("drop", _on_drop)
        name_entry.add_controller(drop_target)

        opt_row = Adw.SwitchRow(
            title="Optional Include",
            subtitle="Use source-optional= so mango starts even if the file is later removed",
        )
        group.add(opt_row)
        page.add(group)

        header = Adw.HeaderBar()
        save_btn = Gtk.Button(label="Add")
        save_btn.add_css_class("suggested-action")

        def _already_tracked(target: Path) -> bool:
            known = {config_parser.MANGO_CONFIG}
            known.update(p for _, p in self._win.app_state.include_docs)
            try:
                target = target.resolve()
            except OSError:
                pass
            return any(
                self._resolve_known(k) == target for k in known
            )

        def _on_save(*_):
            cfg_dir = config_parser.MANGO_CONFIG.parent
            gfile = picked["file"]
            if gfile is not None and gfile.get_path():
                # Explicitly browsed or dropped file — reference it as-is.
                target = Path(gfile.get_path())
                if not target.is_file():
                    self.show_toast("That file no longer exists")
                    return
            else:
                raw = name_entry.get_text().strip()
                # A typed absolute/existing path is referenced directly.
                typed = Path(raw).expanduser()
                if raw and (typed.is_absolute() or "/" in raw or "\\" in raw):
                    target = typed if typed.is_absolute() else (cfg_dir / raw)
                    if not target.is_file():
                        self.show_toast("No such file — give a plain name to create one")
                        return
                else:
                    # Plain name: sanitize and create next to the main config.
                    name = Path(raw).name.strip().strip(".")
                    if not name or name in (".", ".."):
                        self.show_toast("Enter a plain file name, e.g. custom.conf")
                        return
                    target = cfg_dir / name
                    if target.exists():
                        if _already_tracked(target):
                            self.show_toast(f"'{name}' is already in your config")
                            return
                        # Orphaned by the old disk-reload bug (file created,
                        # wiring lost): adopt it instead of dead-ending.
                        self._adopt_existing(target, opt_row.get_active(), dialog)
                        return
                    try:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(f"# {name} — managed by MangoMod\n", encoding="utf-8")
                    except OSError as exc:
                        self.show_toast(f"Cannot create file: {exc}")
                        return
            if self._resolve_known(config_parser.MANGO_CONFIG) == self._resolve_known(target):
                self.show_toast("That is the main config file itself")
                return
            if _already_tracked(target):
                self.show_toast("That file is already in your config")
                return
            self._finish_add(target, opt_row.get_active(), dialog)

        save_btn.connect("clicked", _on_save)
        header.pack_end(save_btn)

        set_form_content(dialog, header, page, self._win._language)
        dialog.present()
        return dialog

    def _adopt_existing(self, target: Path, optional: bool, dialog) -> None:
        """Wire an on-disk-but-unwired file (orphan of the old disk-reload
        bug) into the config instead of refusing it."""
        self._finish_add(target, optional, dialog, verb="Adopted")

    def _finish_add(self, target: Path, optional: bool, dialog, verb: str = "Added") -> None:
        """Shared tail: wire source= line, track in memory, rebuild, land."""
        # Mango resolves relative source= paths against its own working
        # directory — NOT the config dir — so bare names only load by luck.
        # Always write absolute paths (~ form under $HOME, matching the
        # convention mango ships with); proven against `mango -c -p`.
        try:
            target = target.resolve()
        except OSError:
            pass
        home = Path.home()
        try:
            rel = "~/" + str(target.relative_to(home))
        except ValueError:
            rel = str(target)
        # Wire it in with a real source= line so mango loads it.
        self._win.app_state.doc.entries.append(
            config_parser.SourceEntry(path=rel, optional=optional)
        )
        # In-memory only — a disk reload here would wipe the unsaved
        # source= line (Save still belongs to the user).
        self._win.app_state.register_include(target)
        self._commit(f"add config file {target.name}")
        dialog.close()
        self.refresh()
        # Land on the new file: it is the last entry in the selector.
        if self._file_dropdown is not None:
            self._file_dropdown.set_selected(len(self._win.app_state.include_docs))
        self.show_toast(f"{verb} {target.name}")

    @staticmethod
    def _resolve_known(path: Path) -> Path:
        try:
            return path.resolve()
        except OSError:
            return path

    def on_shown(self) -> None:
        count = len(self._win.app_state.documents())
        shown = self._file_dropdown.get_model().get_n_items() if self._file_dropdown else 1
        if count != shown:
            active = self._active_file
            self.refresh()
            paths = [path for _, path in self._win.app_state.documents()]
            if self._file_dropdown and active in paths:
                self._file_dropdown.set_selected(paths.index(active))
        if self._buffer:
            for doc, path in self._win.app_state.documents():
                if path == self._active_file:
                    self._set_buffer(doc.serialize())
                    break
