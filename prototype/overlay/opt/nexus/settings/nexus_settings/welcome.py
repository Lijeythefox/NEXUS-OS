import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gio, Gtk

from nexus import appcenter, tiler
from nexus.common import callsign, config_dir, root
from nexus.presets import active_key, list_presets
from nexus_settings.pages.apps import DEFAULT_TYPES, default_browser_id, set_default_app
from nexus_settings.pages.personal import apply_preset, draw_layout, draw_preset
from nexus_settings.ui import background, label, load_css, styled

DONE_FILE = ".welcome-done"
GAME_CATEGORIES = ("Games", "Casual games", "Emulators")
TIPS = [
    ("Start menu", "Super"),
    ("Settings", "Super + I"),
    ("Quick Settings", "Super + A"),
    ("Switch Stack / Split windows", "Super + Space"),
    ("Game launcher", "Super + G"),
    ("On-screen keyboard", "Super + K"),
    ("Controller as a mouse", "Hold Select + Start"),
    ("Add more apps and games", "Settings > Apps > App Center"),
]


def mark_done():
    (config_dir() / DONE_FILE).touch()


class WelcomeWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Welcome to NEXUS OS")
        self.set_default_size(960, 560)
        self.set_icon_name("nexus-settings")
        self.connect("delete-event", self.on_close)
        self.entries = appcenter.load()
        self.browser = default_browser_id() or "chromium.desktop"
        self.games = set()
        self.installing = False
        self.steps = [
            ("Welcome", self.step_welcome),
            ("Colours", self.step_colours),
            ("Windows", self.step_windows),
            ("Browser", self.step_browser),
            ("Games", self.step_games),
            ("Ready", self.step_ready),
        ]
        self.index = 0

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("start", "end", "top", "bottom"):
            getattr(outer, f"set_margin_{side}")(18)
        self.add(outer)
        header = Gtk.Box(spacing=12)
        header.add(label("NEXUS // WELCOME", "nexus-brand", wrap=False))
        self.step_label = label("", "nexus-crumb", xalign=1, wrap=False)
        header.pack_end(self.step_label, False, False, 0)
        outer.add(header)
        self.heading = label("", "nexus-heading")
        outer.add(self.heading)
        self.scroller = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        outer.add(self.scroller)

        footer = Gtk.Box(spacing=8)
        self.skip_button = Gtk.Button(label="Skip setup")
        self.skip_button.connect("clicked", lambda _: self.finish())
        footer.add(self.skip_button)
        self.status = label("", "nexus-subtitle", xalign=0.5)
        footer.pack_start(self.status, True, True, 0)
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: self.go(self.index - 1))
        footer.add(self.back_button)
        self.next_button = styled(Gtk.Button(label="Next"), "nexus-primary")
        self.next_button.set_size_request(140, 44)
        self.next_button.connect("clicked", lambda _: self.next())
        footer.add(self.next_button)
        outer.add(footer)
        self.go(0)

    def busy(self, text):
        self.status.set_text(text or "")

    def toast(self, text):
        self.status.set_text(text)

    def go(self, index):
        self.index = max(0, min(index, len(self.steps) - 1))
        title, builder = self.steps[self.index]
        child = self.scroller.get_child()
        if child is not None:
            child.destroy()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(6)
        builder(box)
        self.scroller.add(box)
        self.scroller.show_all()
        self.step_label.set_text(f"STEP {self.index + 1} / {len(self.steps)}  ·  {title.upper()}")
        last = self.index == len(self.steps) - 1
        self.back_button.set_sensitive(self.index > 0 and not self.installing)
        self.skip_button.set_visible(not last)
        self.next_button.set_label("Finish" if last else "Next")
        self.next_button.set_sensitive(not self.installing)

    def refresh(self):
        self.go(self.index)

    def next(self):
        if self.index == len(self.steps) - 1:
            self.finish()
            return
        self.go(self.index + 1)
        if self.index == len(self.steps) - 1:
            self.install_choices()

    def finish(self):
        if self.installing:
            self.status.set_text("Still installing. Finish unlocks when it's done.")
            return
        mark_done()
        self.destroy()

    def on_close(self, *_):
        if self.installing:
            self.status.set_text("Still installing. Please wait a moment.")
            return True
        mark_done()
        return False

    def big_choice(self, parent, active, body, on_click):
        button = styled(Gtk.Button(), "nexus-preset")
        if active:
            styled(button, "active")
        button.add(body)
        button.connect("clicked", lambda _: on_click())
        parent.add(button)
        return button

    def step_welcome(self, box):
        self.heading.set_text(f"Welcome, {callsign()}")
        box.add(label("Let's set up a few things: your colours, how windows behave, your web browser and extra "
                      "game systems. It takes a minute."))
        box.add(label("Everything here can be changed later in Settings (Super + I). Tap Next to start, "
                      "or Skip setup to keep the defaults.", "nexus-subtitle"))

    def step_colours(self, box):
        self.heading.set_text("Pick your colours")
        box.add(label("This recolours everything: HUD, taskbar, windows, terminal, login screen and boot animation. "
                      "You can also make your own later in Settings > Personalization.", "nexus-subtitle"))
        grid = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=3, column_spacing=12,
                           row_spacing=12, homogeneous=True)
        current = active_key()
        for preset in list_presets():
            area = Gtk.DrawingArea()
            area.set_size_request(200, 110)
            area.connect("draw", draw_preset, preset)
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            inner.add(area)
            inner.add(label(preset.style, "nexus-subtitle"))
            self.big_choice(grid, preset.key == current, inner,
                            lambda key=preset.key: apply_preset(self, key, self.on_preset))
        box.add(grid)

    def on_preset(self):
        load_css()
        self.refresh()

    def step_windows(self, box):
        self.heading.set_text("How should windows behave?")
        choices = Gtk.Box(spacing=12, homogeneous=True)
        current = tiler.layout()
        for mode, (title, text) in tiler.LAYOUTS.items():
            area = Gtk.DrawingArea()
            area.set_size_request(240, 140)
            area.connect("draw", draw_layout, mode)
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            inner.add(area)
            inner.add(label(title.upper(), "nexus-value"))
            inner.add(label(text, "nexus-subtitle"))
            self.big_choice(choices, mode == current, inner, lambda value=mode: self.pick_layout(value))
        box.add(choices)
        box.add(label("Super + Space switches between them at any time.", "nexus-subtitle"))

    def pick_layout(self, mode):
        tiler.set_layout(mode)
        self.refresh()

    def step_browser(self, box):
        self.heading.set_text("Your web browser")
        box.add(label("Links, web apps and the AI Assistant open in this browser.", "nexus-subtitle"))
        for entry in (item for item in self.entries if item.browser):
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            inner.set_margin_start(8)
            inner.set_margin_end(8)
            note = "" if appcenter.installed(entry) else "  (installs at the end, needs internet)"
            inner.add(label(entry.name + note, "nexus-value"))
            inner.add(label(entry.description, "nexus-subtitle"))
            self.big_choice(box, entry.launch == self.browser, inner, lambda item=entry: self.pick_browser(item))

    def pick_browser(self, entry):
        self.browser = entry.launch
        if appcenter.installed(entry):
            set_default_app(entry.launch, DEFAULT_TYPES[0][1])
        self.refresh()

    def step_games(self, box):
        self.heading.set_text("Extra games")
        box.add(label("NES, SNES, Game Boy, Mega Drive, arcade, PS1, N64, PSP, Dreamcast and Minecraft are already "
                      "built in. Tick anything else you want. It installs at the end and needs internet.",
                      "nexus-subtitle"))
        states = appcenter.installed_map(self.entries)
        for category in GAME_CATEGORIES:
            entries = [item for item in self.entries if item.category == category]
            if entries:
                box.add(label(category.upper(), "nexus-section"))
            for entry in entries:
                if states[entry.key]:
                    box.add(label(f"{entry.name}: already installed", "nexus-subtitle"))
                    continue
                check = Gtk.CheckButton(label=entry.name, active=entry.key in self.games)
                check.connect("toggled", lambda widget, key=entry.key: self.pick_game(key, widget.get_active()))
                row = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2), "nexus-row")
                row.add(check)
                row.add(label(entry.description, "nexus-subtitle"))
                box.add(row)

    def pick_game(self, key, value):
        if value:
            self.games.add(key)
        else:
            self.games.discard(key)

    def step_ready(self, box):
        self.heading.set_text("All set")
        box.add(label("A few shortcuts worth knowing:", "nexus-subtitle"))
        grid = Gtk.Grid(column_spacing=24, row_spacing=6)
        for row, (action, keys) in enumerate(TIPS):
            grid.attach(label(keys, "nexus-value", wrap=False), 0, row, 1, 1)
            grid.attach(label(action), 1, row, 1, 1)
        box.add(grid)

    def install_choices(self):
        keys = sorted(self.games)
        browser = next((entry for entry in self.entries if entry.browser and entry.launch == self.browser), None)
        if browser and not appcenter.installed(browser):
            keys.insert(0, browser.key)
        if not keys:
            return
        names = ", ".join(entry.name for entry in self.entries if entry.key in keys)
        self.installing = True
        self.refresh()
        self.status.set_text(f"Installing {names}...")

        def done(result, error):
            self.installing = False
            failed = error or (result is not None and result.code != 0)
            if failed:
                text = str(error) if error else (result.err.strip() or "Install failed")
                self.status.set_text(f"{text[-160:]}  You can try again in Settings > Apps > App Center.")
            else:
                if browser and browser.key in keys:
                    set_default_app(browser.launch, DEFAULT_TYPES[0][1])
                self.games.clear()
                self.status.set_text("Everything is installed.")
            self.go(self.index)

        background(lambda: root("app-install", *keys), done)


class WelcomeApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.nexus.Welcome", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None

    def do_activate(self):
        if self.window is None:
            load_css()
            self.window = WelcomeWindow(self)
            self.window.show_all()
            self.window.go(0)
        self.window.present()


def main(argv=None):
    return WelcomeApp().run(None)


if __name__ == "__main__":
    sys.exit(main())
