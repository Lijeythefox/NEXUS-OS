import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk

from nexus.common import Settings, callsign
from nexus_settings.pages import access, accounts, apps, devices, gaming, network, personal, privacy, system, timelang, update
from nexus_settings.ui import label, load_css, styled

CATEGORIES = [
    ("system", "System", "computer-symbolic", system.PAGES),
    ("devices", "Bluetooth & devices", "bluetooth-active-symbolic", devices.PAGES),
    ("network", "Network & internet", "network-wireless-symbolic", network.PAGES),
    ("personal", "Personalization", "applications-graphics-symbolic", personal.PAGES),
    ("apps", "Apps", "view-app-grid-symbolic", apps.PAGES),
    ("accounts", "Accounts", "avatar-default-symbolic", accounts.PAGES),
    ("time", "Time & language", "preferences-system-time-symbolic", timelang.PAGES),
    ("gaming", "Gaming", "input-gaming-symbolic", gaming.PAGES),
    ("access", "Accessibility", "preferences-desktop-accessibility-symbolic", access.PAGES),
    ("privacy", "Privacy & security", "security-high-symbolic", privacy.PAGES),
    ("update", "Update & backup", "software-update-available-symbolic", update.PAGES),
]

PAGE_INDEX = {}
for category_id, category_title, _, pages in CATEGORIES:
    for page_id, title, subtitle, keywords, page_class in pages:
        PAGE_INDEX[page_id] = {
            "category": category_id,
            "category_title": category_title,
            "title": title,
            "subtitle": subtitle,
            "keywords": f"{title} {subtitle} {keywords} {category_title}".lower(),
            "class": page_class,
        }


class SettingsWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Settings")
        self.set_default_size(1024, 600)
        self.set_icon_name("nexus-settings")
        self.current = None
        self.history = []

        overlay = Gtk.Overlay()
        self.add(overlay)
        root_box = Gtk.Box()
        overlay.add(root_box)

        sidebar = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6), "nexus-sidebar")
        sidebar.set_size_request(250, -1)
        brand = label("NEXUS // SETTINGS", "nexus-brand")
        brand.set_margin_start(14)
        brand.set_margin_top(14)
        sidebar.add(brand)
        sign = label(callsign(), "nexus-callsign")
        sign.set_margin_start(14)
        sidebar.add(sign)
        self.search = Gtk.SearchEntry(placeholder_text="Find a setting")
        for side in ("start", "end", "top", "bottom"):
            getattr(self.search, f"set_margin_{side}")(10)
        self.search.connect("search-changed", self.on_search)
        sidebar.add(self.search)
        self.categories = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        for category_id, title, icon, _ in CATEGORIES:
            row = Gtk.ListBoxRow()
            row.category_id = category_id
            box = Gtk.Box(spacing=12)
            box.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.LARGE_TOOLBAR))
            box.add(label(title, wrap=False))
            row.add(box)
            self.categories.add(row)
        self.categories.connect("row-selected", self.on_category)
        scroller = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.add(self.categories)
        sidebar.add(scroller)
        root_box.add(sidebar)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        header = Gtk.Box(spacing=10)
        for side in ("start", "end", "top"):
            getattr(header, f"set_margin_{side}")(18)
        self.back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.back_button.connect("clicked", lambda _: self.back())
        header.add(self.back_button)
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.crumb = label("", "nexus-crumb")
        self.heading = label("", "nexus-heading")
        titles.add(self.crumb)
        titles.add(self.heading)
        header.add(titles)
        self.spinner = Gtk.Spinner()
        self.busy_label = label("", "nexus-subtitle", xalign=1)
        header.pack_end(self.spinner, False, False, 0)
        header.pack_end(self.busy_label, False, False, 0)
        content.add(header)
        reduce = Settings().get_bool("REDUCE_MOTION")
        self.stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.NONE if reduce else Gtk.StackTransitionType.CROSSFADE,
            vexpand=True, hexpand=True,
        )
        content.add(self.stack)
        root_box.add(content)

        self.toast_label = styled(Gtk.Label(), "nexus-toast")
        self.toast_revealer = Gtk.Revealer(halign=Gtk.Align.CENTER, valign=Gtk.Align.END)
        self.toast_revealer.set_margin_bottom(18)
        self.toast_revealer.add(self.toast_label)
        overlay.add_overlay(self.toast_revealer)
        self.toast_source = 0

    def toast(self, text):
        self.toast_label.set_text(text)
        self.toast_revealer.set_reveal_child(True)
        if self.toast_source:
            GLib.source_remove(self.toast_source)

        def hide():
            self.toast_revealer.set_reveal_child(False)
            self.toast_source = 0
            return False

        self.toast_source = GLib.timeout_add(3500, hide)

    def busy(self, text):
        if text:
            self.busy_label.set_text(text)
            self.spinner.start()
        else:
            self.busy_label.set_text("")
            self.spinner.stop()

    def show_widget(self, name, widget, crumb, heading, remember=True):
        if remember and self.current and self.current != name and self.current != "search":
            self.history.append(self.current)
        old = self.stack.get_child_by_name(name)
        if old is not None:
            old.destroy()
        self.stack.add_named(widget, name)
        widget.show_all()
        self.stack.set_visible_child_name(name)
        for child in self.stack.get_children():
            if child is not widget:
                child.destroy()
        self.current = name
        self.crumb.set_text(crumb.upper())
        self.heading.set_text(heading)
        self.back_button.set_sensitive(bool(self.history))

    def nav_row(self, page_id, box):
        meta = PAGE_INDEX[page_id]
        button = styled(Gtk.Button(), "nexus-nav")
        inner = Gtk.Box(spacing=12)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        texts.add(label(meta["title"]))
        texts.add(label(meta["subtitle"], "nexus-subtitle"))
        inner.add(texts)
        inner.add(Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON))
        button.add(inner)
        button.connect("clicked", lambda _: self.open_page(page_id))
        box.add(button)

    def category_view(self, category_id, remember=True):
        title, pages = next((t, p) for c, t, _, p in CATEGORIES if c == category_id)
        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(20)
        for page_id, *_ in pages:
            self.nav_row(page_id, box)
        scroller.add(box)
        self.show_widget(f"category:{category_id}", scroller, "Settings", title, remember)

    def open_page(self, page_id, remember=True):
        meta = PAGE_INDEX.get(page_id)
        if not meta:
            return
        page = meta["class"](self)
        self.show_widget(f"page:{page_id}", page, meta["category_title"], meta["title"], remember)

    def back(self):
        if not self.history:
            return
        target = self.history.pop()
        kind, _, key = target.partition(":")
        if kind == "category":
            self.category_view(key, remember=False)
        elif kind == "page":
            self.open_page(key, remember=False)
        self.back_button.set_sensitive(bool(self.history))

    def on_category(self, listbox, row):
        if row is not None:
            self.category_view(row.category_id)

    def on_search(self, entry):
        text = entry.get_text().strip().lower()
        if not text:
            row = self.categories.get_selected_row()
            if row:
                self.category_view(row.category_id)
            return
        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(20)
        matches = [page_id for page_id, meta in PAGE_INDEX.items() if all(word in meta["keywords"] for word in text.split())]
        for page_id in matches:
            self.nav_row(page_id, box)
        if not matches:
            box.add(label("Nothing matches that. Try another word.", "nexus-subtitle"))
        scroller.add(box)
        self.show_widget("search", scroller, "Search", f"Results for “{entry.get_text().strip()}”", remember=False)

    def start(self, page_id=None):
        first = self.categories.get_row_at_index(0)
        if page_id and page_id in PAGE_INDEX:
            category = PAGE_INDEX[page_id]["category"]
            for row in self.categories.get_children():
                if row.category_id == category:
                    self.categories.select_row(row)
                    break
            self.open_page(page_id)
        else:
            self.categories.select_row(first)


class SettingsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.nexus.Settings", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        page_id = args[0] if args else None
        if self.window is None:
            load_css()
            self.window = SettingsWindow(self)
            self.window.show_all()
            self.window.start(page_id)
        else:
            if page_id:
                self.window.open_page(page_id)
            self.window.present()
        return 0


def main(argv=None):
    app = SettingsApp()
    return app.run(argv or sys.argv)
