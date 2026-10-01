import threading
from string import Template

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

from nexus.presets import active_preset

APP_CSS = Template("""
.nexus-sidebar { background-color: $surface; border-right: 1px solid $grid; }
.nexus-sidebar list, .nexus-sidebar row { background-color: transparent; }
.nexus-sidebar row { padding: 10px 14px; min-height: 36px; border-left: 3px solid transparent; }
.nexus-sidebar row:selected { background-color: $selection; border-left: 3px solid $primary; color: $text_hi; }
.nexus-brand { color: $primary; font-size: 17pt; letter-spacing: 4px; }
.nexus-callsign { color: $dim; letter-spacing: 3px; }
.nexus-heading { color: $primary; font-size: 19pt; letter-spacing: 2px; }
.nexus-crumb { color: $dim; letter-spacing: 2px; font-size: 9pt; }
.nexus-section { color: $secondary_text; font-size: 9pt; letter-spacing: 3px; margin-top: 14px; }
.nexus-row { background-color: $surface; border: 1px solid $grid; border-radius: ${radius}px; padding: 10px 14px; }
.nexus-row:hover { border-color: $border; }
.nexus-nav { background-color: $surface; border: 1px solid $grid; border-radius: ${radius}px; padding: 12px 14px; }
.nexus-nav:hover { background-color: $hover; border-color: $primary; }
.nexus-subtitle { color: $dim; font-size: 9pt; }
.nexus-value { color: $primary; }
.nexus-alert { color: $alert; }
.nexus-tile { background-color: $surface_hi; border: 1px solid $border; border-radius: ${radius}px; min-height: 70px; padding: 6px; }
.nexus-tile:checked { background-color: $primary; border-color: $primary; color: $on_primary; }
.nexus-tile:checked label { color: $on_primary; }
.nexus-quick { background-color: $bg; border: 1px solid $primary; border-radius: ${radius}px; }
.nexus-toast { background-color: $surface_hi; border: 1px solid $primary; border-radius: ${radius}px; padding: 8px 16px; color: $text_hi; }
.nexus-preset { background-color: transparent; border: 2px solid $grid; border-radius: ${radius}px; padding: 4px; }
.nexus-preset.active { border-color: $primary; }
""")

_provider = None


def load_css():
    global _provider
    preset = active_preset()
    values = dict(preset.palette())
    values["radius"] = preset.radius
    provider = Gtk.CssProvider()
    provider.load_from_data(APP_CSS.substitute(values).encode("utf-8"))
    screen = Gdk.Screen.get_default()
    if _provider is not None:
        Gtk.StyleContext.remove_provider_for_screen(screen, _provider)
    Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    _provider = provider


def background(work, done=None):
    def finish(result, error):
        if done:
            done(result, error)
        return False

    def runner():
        try:
            result, error = work(), None
        except Exception as exc:
            result, error = None, exc
        GLib.idle_add(finish, result, error)

    threading.Thread(target=runner, daemon=True).start()


def debounce(func, delay=350):
    state = {"source": 0}

    def call(*args):
        if state["source"]:
            GLib.source_remove(state["source"])

        def fire():
            state["source"] = 0
            func(*args)
            return False

        state["source"] = GLib.timeout_add(delay, fire)

    return call


def styled(widget, *classes):
    context = widget.get_style_context()
    for name in classes:
        context.add_class(name)
    return widget


def label(text, *classes, xalign=0, wrap=True, selectable=False):
    widget = Gtk.Label(label=text, xalign=xalign, wrap=wrap, selectable=selectable)
    return styled(widget, *classes)


def set_quiet(widget, value):
    handler = getattr(widget, "nexus_handler", None)
    if handler:
        widget.handler_block(handler)
    if isinstance(widget, Gtk.Switch) or isinstance(widget, Gtk.ToggleButton):
        widget.set_active(bool(value))
    elif isinstance(widget, Gtk.Range):
        widget.set_value(value)
    if handler:
        widget.handler_unblock(handler)


def ask_text(parent, title, prompt, text="", password=False):
    dialog = Gtk.Dialog(title=title, transient_for=parent, modal=True)
    dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    box = dialog.get_content_area()
    box.set_spacing(10)
    box.set_border_width(16)
    box.add(label(prompt))
    entry = Gtk.Entry(text=text, visibility=not password, activates_default=True)
    box.add(entry)
    dialog.show_all()
    response = dialog.run()
    value = entry.get_text()
    dialog.destroy()
    return value if response == Gtk.ResponseType.OK else None


def ask_password_twice(parent, title):
    first = ask_text(parent, title, "New password", password=True)
    if first is None:
        return None
    second = ask_text(parent, title, "Type it again", password=True)
    if second is None:
        return None
    if first != second:
        message(parent, "The passwords didn't match. Nothing was changed.", error=True)
        return None
    return first


def confirm(parent, text, ok_label="Continue", danger=False):
    dialog = Gtk.MessageDialog(
        transient_for=parent, modal=True, message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE, text=text,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    button = dialog.add_button(ok_label, Gtk.ResponseType.OK)
    styled(button, "destructive-action" if danger else "suggested-action")
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def message(parent, text, error=False):
    dialog = Gtk.MessageDialog(
        transient_for=parent, modal=True,
        message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK, text=text,
    )
    dialog.run()
    dialog.destroy()


def choose(parent, title, options, searchable=False):
    dialog = Gtk.Dialog(title=title, transient_for=parent, modal=True)
    dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Choose", Gtk.ResponseType.OK)
    dialog.set_default_size(420, 460)
    box = dialog.get_content_area()
    box.set_spacing(8)
    box.set_border_width(12)
    listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
    for key, text in options:
        row = Gtk.ListBoxRow()
        row.nexus_key = key
        row.nexus_text = text.lower()
        row.add(label(text, xalign=0))
        listbox.add(row)
    if searchable:
        search = Gtk.SearchEntry(placeholder_text="Search")
        listbox.set_filter_func(lambda row: search.get_text().lower() in row.nexus_text)
        search.connect("search-changed", lambda entry: listbox.invalidate_filter())
        box.add(search)
    listbox.connect("row-activated", lambda lb, row: dialog.response(Gtk.ResponseType.OK))
    scroller = Gtk.ScrolledWindow(vexpand=True)
    scroller.add(listbox)
    box.add(scroller)
    dialog.show_all()
    response = dialog.run()
    selected = listbox.get_selected_row()
    dialog.destroy()
    if response == Gtk.ResponseType.OK and selected:
        return selected.nexus_key
    return None


def pick_file(parent, title, folder=False, patterns=None):
    action = Gtk.FileChooserAction.SELECT_FOLDER if folder else Gtk.FileChooserAction.OPEN
    dialog = Gtk.FileChooserDialog(title=title, transient_for=parent, action=action)
    dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Choose", Gtk.ResponseType.OK)
    if patterns:
        file_filter = Gtk.FileFilter()
        for pattern in patterns:
            file_filter.add_pattern(pattern)
        dialog.set_filter(file_filter)
    response = dialog.run()
    path = dialog.get_filename()
    dialog.destroy()
    return path if response == Gtk.ResponseType.OK else None


class Page(Gtk.ScrolledWindow):
    title = ""

    def __init__(self, window):
        super().__init__(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True, hexpand=True)
        self.window = window
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for side in ("start", "end", "top", "bottom"):
            getattr(self.box, f"set_margin_{side}")(20)
        self.add(self.box)
        self.build()
        self.show_all()

    def build(self):
        pass

    def rebuild(self):
        for child in self.box.get_children():
            child.destroy()
        self.build()
        self.show_all()

    def put(self, widget, parent=None):
        (parent or self.box).add(widget)
        return widget

    def section(self, text, parent=None):
        return self.put(label(text.upper(), "nexus-section"), parent)

    def note(self, text, parent=None):
        return self.put(label(text, "nexus-subtitle"), parent)

    def row(self, title, subtitle=None, widget=None, parent=None):
        row = styled(Gtk.Box(spacing=12), "nexus-row")
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True, valign=Gtk.Align.CENTER)
        texts.add(label(title))
        row.subtitle = None
        if subtitle:
            row.subtitle = label(subtitle, "nexus-subtitle")
            texts.add(row.subtitle)
        row.add(texts)
        if widget is not None:
            widget.set_valign(Gtk.Align.CENTER)
            row.add(widget)
        return self.put(row, parent)

    def switch(self, title, subtitle, active, on_change, parent=None):
        widget = Gtk.Switch(active=bool(active))
        widget.nexus_handler = widget.connect("notify::active", lambda w, _: on_change(w.get_active()))
        self.row(title, subtitle, widget, parent)
        return widget

    def scale(self, title, low, high, step, value, on_change, subtitle=None, digits=0, parent=None):
        widget = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, low, high, step)
        widget.set_value(value)
        widget.set_digits(digits)
        widget.set_size_request(240, -1)
        delayed = debounce(on_change)
        widget.nexus_handler = widget.connect("value-changed", lambda w: delayed(w.get_value()))
        self.row(title, subtitle, widget, parent)
        return widget

    def combo(self, title, options, active, on_change, subtitle=None, parent=None):
        widget = Gtk.ComboBoxText()
        for key, text in options:
            widget.append(str(key), text)
        widget.set_active_id(str(active))
        widget.nexus_handler = widget.connect(
            "changed", lambda w: w.get_active_id() is not None and on_change(w.get_active_id())
        )
        self.row(title, subtitle, widget, parent)
        return widget

    def button(self, title, subtitle, text, on_click, parent=None, style=None):
        widget = Gtk.Button(label=text)
        if style:
            styled(widget, style)
        widget.connect("clicked", lambda _: on_click())
        self.row(title, subtitle, widget, parent)
        return widget

    def buttons(self, title, subtitle, actions, parent=None):
        box = Gtk.Box(spacing=6)
        for text, callback in actions:
            widget = Gtk.Button(label=text)
            widget.connect("clicked", lambda _, cb=callback: cb())
            box.add(widget)
        self.row(title, subtitle, box, parent)
        return box

    def info(self, title, value, parent=None):
        widget = label(str(value), "nexus-value", xalign=1, wrap=False, selectable=True)
        self.row(title, None, widget, parent)
        return widget

    def task(self, work, done=None, busy="Working..."):
        self.window.busy(busy)

        def finished(result, error):
            self.window.busy(None)
            if done:
                done(result, error)
            elif error:
                self.window.toast(str(error))

        background(work, finished)

    def root_task(self, result_work, ok_text, refresh=True):
        def done(result, error):
            if error:
                self.window.toast(str(error))
            elif result is not None and getattr(result, "code", 0) not in (0,):
                text = (getattr(result, "err", "") or "").strip()
                if getattr(result, "code", 0) in (126, 127):
                    text = text or "Cancelled"
                self.window.toast(text or "That didn't work")
            else:
                self.window.toast(ok_text)
            if refresh:
                self.rebuild()

        self.task(result_work, done)
