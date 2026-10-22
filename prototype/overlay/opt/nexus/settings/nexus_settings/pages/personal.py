import configparser
from pathlib import Path

from gi.repository import Gdk, GdkPixbuf, Gtk

from nexus import hud, theme, tiler
from nexus.common import (
    LOGIN_IMAGE,
    PRESET_DIR,
    SHARE_DIR,
    Settings,
    read_kv,
    root_quick,
    run,
    spawn,
    xfconf_get,
    xfconf_set,
    xfconf_set_array,
)
from nexus.presets import Preset, active_key, active_preset, hex_to_rgb, list_presets, load_preset, luminance, rgb_to_hex
from nexus_settings.ui import Page, choose, label, load_css, pick_file, styled

CUSTOM_KEY = "custom"
CUSTOM_COLOURS = [
    ("BACKGROUND", "Background", "Behind everything. Keep it very dark."),
    ("PRIMARY", "Primary", "Text, lines and highlights"),
    ("SECONDARY", "Secondary", "Accents and section titles"),
    ("GRID", "Grid", "Thin grid lines and borders. A dim shade of the primary works well."),
    ("ALERT", "Alert", "Warnings and the low battery alarm"),
]
PATTERNS = [("topo", "Topographic lines"), ("radar", "Radar"), ("scope", "Scope sweep"), ("rings", "Glowing rings"),
            ("synth", "Synthwave grid")]
TILE_KEYS = [
    ("Switch Stack / Split", "Super + Space"),
    ("Stack: snap left or right, maximise, minimise", "Super + Arrows"),
    ("Split: jump to the window on that side", "Super + Arrows"),
    ("Split: swap with the window on that side", "Super + Shift + Arrows"),
    ("Split: make this the main window", "Super + Enter"),
    ("Split: float this window (press again to tile it)", "Super + F"),
    ("Close the window", "Super + W"),
]


def draw_preset(widget, cr, preset):
    c = preset.palette()
    width = widget.get_allocated_width()
    height = widget.get_allocated_height()
    cr.set_source_rgb(*hex_to_rgb(c["bg"]))
    cr.rectangle(0, 0, width, height)
    cr.fill()
    cr.set_source_rgb(*hex_to_rgb(c["grid"]))
    cr.set_line_width(1)
    for x in range(0, width, 12):
        cr.move_to(x + 0.5, 0)
        cr.line_to(x + 0.5, height)
    for y in range(0, height, 12):
        cr.move_to(0, y + 0.5)
        cr.line_to(width, y + 0.5)
    cr.stroke()
    cr.set_source_rgb(*hex_to_rgb(c["primary"]))
    cr.rectangle(0, height - 14, width, 14)
    cr.fill()
    cr.set_source_rgb(*hex_to_rgb(c["secondary"]))
    cr.rectangle(10, 12, width * 0.45, 22)
    cr.fill()
    cr.set_source_rgb(*hex_to_rgb(c["alert"]))
    cr.arc(width - 18, 22, 6, 0, 6.2832)
    cr.fill()
    cr.set_source_rgb(*hex_to_rgb(c["primary"]))
    cr.select_font_face("Share Tech Mono")
    cr.set_font_size(15)
    cr.move_to(10, height - 24)
    cr.show_text(preset.name.upper())
    return False


def apply_preset(window, key, done=None):
    def work():
        result = root_quick("preset", key)
        if result.code != 0:
            raise RuntimeError(result.err.strip() or "Couldn't change the preset")
        theme.apply(load_preset(key))
        return True

    def finished(result, error):
        window.busy(None)
        if error:
            window.toast(str(error))
            return
        load_css()
        window.toast(f"{load_preset(key).name} applied. The boot animation updates on the next restart.")
        if done:
            done()

    window.busy("Recolouring everything...")
    from nexus_settings.ui import background

    background(work, finished)


class PresetPage(Page):
    def build(self):
        current = active_key()
        self.note("Recolours the HUD, taskbar, start menu, windows, terminal, icons, wallpaper, login screen "
                  "and boot animation.")
        grid = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=3, column_spacing=12,
                           row_spacing=12, homogeneous=True)
        for preset in list_presets():
            button = Gtk.Button()
            styled(button, "nexus-preset")
            if preset.key == current:
                styled(button, "active")
            area = Gtk.DrawingArea()
            area.set_size_request(190, 112)
            area.connect("draw", draw_preset, preset)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.add(area)
            box.add(label(preset.style, "nexus-subtitle"))
            button.add(box)
            button.connect("clicked", lambda _, key=preset.key: apply_preset(self.window, key, self.rebuild))
            grid.add(button)
        self.put(grid)
        self.section("Your own")
        self.button("Make your own preset", "Pick your own five colours, pattern and sounds", "Open",
                    lambda: self.window.open_page("custompreset"))
        if (PRESET_DIR / f"{CUSTOM_KEY}.conf").exists() and current != CUSTOM_KEY:
            self.button("Remove your custom preset", None, "Remove", self.remove_custom)

    def remove_custom(self):
        self.root_task(lambda: root_quick("custom-preset-remove"), "Custom preset removed")


def rgba(colour):
    value = Gdk.RGBA()
    value.parse(colour)
    return value


def contrast(colour_a, colour_b):
    light, dark = sorted((luminance(colour_a), luminance(colour_b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class CustomPresetPage(Page):
    draft = None

    def build(self):
        if self.draft is None:
            exists = (PRESET_DIR / f"{CUSTOM_KEY}.conf").exists()
            self.draft = self.values_from(load_preset(CUSTOM_KEY) if exists else active_preset())
            if not exists:
                self.draft["NAME"] = "Custom"
        self.note("Saving builds your own preset and switches everything to it. It takes about a minute.")
        self.preview = Gtk.DrawingArea()
        self.preview.set_size_request(380, 190)
        self.preview.connect("draw", lambda widget, cr: draw_preset(widget, cr, self.preview_preset()))
        self.put(self.preview)
        self.warning = self.put(label("", "nexus-alert"))
        self.combo("Start from", [(preset.key, preset.name) for preset in list_presets()], "", self.start_from,
                   subtitle="Copies another preset's colours")
        name = Gtk.Entry(text=self.draft["NAME"], max_length=16)
        name.connect("changed", lambda entry: self.set_value("NAME", entry.get_text()))
        self.row("Name", "Shown on the preset tile", name)
        self.section("Colours")
        for key, title, hint in CUSTOM_COLOURS:
            button = Gtk.ColorButton(rgba=rgba(self.draft[key]), use_alpha=False, title=title)
            button.connect("color-set", lambda widget, item=key: self.set_colour(item, widget.get_rgba()))
            self.row(title, hint, button)
        self.section("Style")
        self.combo("Wallpaper pattern", PATTERNS, self.draft["WALLPAPER"], lambda value: self.set_value("WALLPAPER", value))
        self.combo("Corners", [("rounded", "Rounded HUD and tiles"), ("sharp", "Sharp")], self.draft["CORNERS"],
                   lambda value: self.set_value("CORNERS", value))
        self.combo("Sounds", [("tactical", "Tactical"), ("quiet", "Quiet")], self.draft["SOUND_PACK"],
                   lambda value: self.set_value("SOUND_PACK", value))
        self.button("Save and use it", None, "Save", self.save, style="nexus-primary")
        self.check()

    def values_from(self, preset):
        return {"NAME": preset.name, "BACKGROUND": preset.background, "PRIMARY": preset.primary,
                "SECONDARY": preset.secondary, "GRID": preset.grid, "ALERT": preset.alert,
                "WALLPAPER": preset.wallpaper, "CORNERS": preset.corners, "SOUND_PACK": preset.sound_pack}

    def preview_preset(self):
        d = self.draft
        return Preset(key=CUSTOM_KEY, name=d["NAME"] or "Custom", style="", order=90, hidden=False,
                      background=d["BACKGROUND"], primary=d["PRIMARY"], secondary=d["SECONDARY"], grid=d["GRID"],
                      alert=d["ALERT"], wallpaper=d["WALLPAPER"], sound_pack=d["SOUND_PACK"], corners=d["CORNERS"])

    def start_from(self, key):
        name = self.draft["NAME"]
        self.draft = self.values_from(load_preset(key))
        self.draft["NAME"] = name
        self.rebuild()

    def set_value(self, key, value):
        self.draft[key] = value
        self.preview.queue_draw()

    def set_colour(self, key, value):
        self.set_value(key, rgb_to_hex((value.red, value.green, value.blue)))
        self.check()

    def check(self):
        d = self.draft
        problems = []
        if contrast(d["PRIMARY"], d["BACKGROUND"]) < 4.5:
            problems.append("Primary is too close to the background, so text will be hard to read.")
        if luminance(d["BACKGROUND"]) > 0.25:
            problems.append("A light background makes the HUD and grid hard to see. Darker works best.")
        self.warning.set_text(" ".join(problems))

    def save(self):
        text = "\n".join(f"{key}={value}" for key, value in self.draft.items()) + "\n"

        def work():
            result = root_quick("custom-preset", input_text=text)
            if result.code != 0:
                raise RuntimeError(result.err.strip() or "Couldn't build the custom preset")
            theme.apply(load_preset(CUSTOM_KEY))
            return True

        def done(result, error):
            if error:
                self.window.toast(str(error))
                return
            load_css()
            self.window.toast("Your preset is on. The boot animation updates on the next restart.")
            self.rebuild()

        self.task(work, done, busy="Building your preset (about a minute)...")


def draw_layout(widget, cr, mode):
    c = active_preset().palette()
    width = widget.get_allocated_width()
    height = widget.get_allocated_height()
    cr.set_source_rgb(*hex_to_rgb(c["bg"]))
    cr.rectangle(0, 0, width, height)
    cr.fill()
    bar = 12
    cr.set_source_rgb(*hex_to_rgb(c["grid"]))
    cr.rectangle(0, height - bar, width, bar)
    cr.fill()
    if mode == "split":
        rects = tiler.split_rects(3, (0, 0, width, height - bar), 6, 0.55)
    else:
        rects = [(width * 0.08, height * 0.1, width * 0.55, height * 0.55),
                 (width * 0.36, height * 0.28, width * 0.55, height * 0.55)]
    for x, y, w, h in rects:
        cr.set_source_rgb(*hex_to_rgb(c["surface_hi"]))
        cr.rectangle(x, y, w, h)
        cr.fill()
        cr.set_source_rgb(*hex_to_rgb(c["title_active"]))
        cr.rectangle(x, y, w, 10)
        cr.fill()
        cr.set_source_rgb(*hex_to_rgb(c["primary"]))
        cr.set_line_width(1.5)
        cr.rectangle(x + 0.75, y + 0.75, w - 1.5, h - 1.5)
        cr.stroke()
    return False


class WindowLayoutPage(Page):
    def build(self):
        current = tiler.layout()
        self.note("How windows are arranged. Super + Space switches between the two at any time.")
        if not tiler.send("reload"):
            self.put(label("The window layout helper isn't running. Log out and back in to start it.", "nexus-alert"))
        choices = Gtk.Box(spacing=12, homogeneous=True)
        for mode, (title, text) in tiler.LAYOUTS.items():
            button = styled(Gtk.Button(), "nexus-preset")
            if mode == current:
                styled(button, "active")
            area = Gtk.DrawingArea()
            area.set_size_request(220, 130)
            area.connect("draw", draw_layout, mode)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.add(area)
            box.add(label(title.upper(), "nexus-value"))
            box.add(label(text, "nexus-subtitle"))
            button.add(box)
            button.connect("clicked", lambda _, value=mode: self.pick(value))
            choices.add(button)
        self.put(choices)
        settings = Settings()
        self.section("Split layout")
        self.scale("Main window width (%)", 40, 70, 5, settings.get_int("TILE_MAIN", 55),
                   lambda value: self.save("TILE_MAIN", int(value)))
        self.scale("Gap between windows (pixels)", 0, 16, 2, settings.get_int("TILE_GAP", 6),
                   lambda value: self.save("TILE_GAP", int(value)))
        self.section("Shortcuts")
        for action, keys in TILE_KEYS:
            self.info(action, keys)
        self.note("Change these in Settings > Bluetooth & devices > Keyboard.")

    def pick(self, mode):
        tiler.set_layout(mode)
        self.window.toast(f"Window layout: {tiler.LAYOUTS[mode][0]}")
        self.rebuild()

    def save(self, key, value):
        Settings().set(key, value)
        tiler.send("reload")


class WallpaperPage(Page):
    def build(self):
        settings = Settings()
        choice = settings.get("WALLPAPER", "preset")
        path = theme.wallpaper_path(load_preset(active_key()), settings)
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 420, 250, True)
            self.put(Gtk.Image.new_from_pixbuf(pixbuf))
        except Exception:
            pass
        self.combo("Wallpaper", [("preset", "Follow the colour preset"), ("custom", "My own picture")],
                   "preset" if choice == "preset" else "custom", self.set_mode)
        self.button("Choose a picture", "PNG or JPG", "Browse", self.pick)

    def set_mode(self, mode):
        if mode == "preset":
            Settings().set("WALLPAPER", "preset")
            theme.main(["wallpaper"])
            self.rebuild()
        else:
            self.pick()

    def pick(self):
        path = pick_file(self.window, "Choose a wallpaper", patterns=["*.png", "*.jpg", "*.jpeg", "*.webp"])
        if path:
            Settings().set("WALLPAPER", path)
            theme.main(["wallpaper"])
        self.rebuild()


class HudPage(Page):
    def build(self):
        self.switch("Show HUD", "Super + H also shows and hides it", hud.visible(), self.set_visible)
        for name, meta in hud.WIDGETS.items():
            config = hud.widget(name)
            self.section(meta["title"])
            self.switch("Show this widget", None, config["enabled"],
                        lambda value, widget=name: hud.set_widget(widget, enabled=value))
            self.combo("Position", list(hud.POSITIONS.items()), config["position"],
                       lambda value, widget=name: hud.set_widget(widget, position=value))
            self.combo("Size", [("small", "Small"), ("medium", "Medium"), ("large", "Large")], config["size"],
                       lambda value, widget=name: hud.set_widget(widget, size=value))
            self.switch("Always on top", "Stays above windows instead of on the desktop", config["ontop"],
                        lambda value, widget=name: hud.set_widget(widget, ontop=value))

    def set_visible(self, value):
        hud.set_visible(value)


def desktop_name(path):
    return Path(path).name


def app_choices():
    from gi.repository import Gio

    apps = [app for app in Gio.AppInfo.get_all() if app.should_show()]
    return sorted(((app.get_id(), app.get_display_name()) for app in apps), key=lambda item: item[1].lower())


def docklike_file():
    return Path.home() / ".config/xfce4/panel/docklike-2.rc"


def read_docklike():
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(docklike_file())
    pinned = parser.get("user", "pinned", fallback="")
    return [item for item in pinned.split(";") if item]


def write_docklike(paths):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(docklike_file())
    if not parser.has_section("user"):
        parser.add_section("user")
    parser.set("user", "pinned", ";".join(paths) + ";")
    docklike_file().parent.mkdir(parents=True, exist_ok=True)
    with open(docklike_file(), "w", encoding="utf-8") as handle:
        parser.write(handle)


def restart_panel():
    spawn(["xfce4-panel", "-r"])


class TaskbarPage(Page):
    def build(self):
        size = xfconf_get("xfce4-panel", "/panels/panel-1/size") or "48"
        self.combo("Taskbar size", [("40", "Small"), ("48", "Medium"), ("56", "Large")], size, self.set_size)
        autohide = (xfconf_get("xfce4-panel", "/panels/panel-1/autohide-behavior") or "0") != "0"
        self.switch("Auto-hide the taskbar", None, autohide,
                    lambda value: xfconf_set("xfce4-panel", "/panels/panel-1/autohide-behavior", 2 if value else 0, "uint"))
        self.section("Pinned apps")
        self.button("Pin an app", None, "Add", self.add)
        for path in read_docklike():
            self.button(desktop_name(path), path, "Unpin", lambda target=path: self.remove(target))

    def set_size(self, value):
        xfconf_set("xfce4-panel", "/panels/panel-1/size", int(value), "uint")
        xfconf_set("xfce4-panel", "/panels/panel-1/icon-size", int(value) - 16, "uint")

    def add(self):
        app_id = choose(self.window, "Pin an app", app_choices(), searchable=True)
        if not app_id:
            return
        path = next((str(base / app_id) for base in (Path("/usr/share/applications"), Path.home() / ".local/share/applications")
                     if (base / app_id).exists()), f"/usr/share/applications/{app_id}")
        pinned = read_docklike()
        if path not in pinned:
            write_docklike(pinned + [path])
            restart_panel()
        self.rebuild()

    def remove(self, path):
        write_docklike([item for item in read_docklike() if item != path])
        restart_panel()
        self.rebuild()


def whisker_file():
    return Path.home() / ".config/xfce4/panel/whiskermenu-1.rc"


def read_favorites():
    values = run(["xfconf-query", "-c", "xfce4-panel", "-p", "/plugins/plugin-1/favorites"]).out.splitlines()
    favorites = [line.strip() for line in values if line.strip().endswith(".desktop")]
    if favorites:
        return favorites
    return [item for item in read_kv(whisker_file()).get("favorites", "").split(",") if item]


def write_favorites(favorites):
    xfconf_set_array("xfce4-panel", "/plugins/plugin-1/favorites", favorites)
    path = whisker_file()
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("favorites=")]
        lines.insert(0, "favorites=" + ",".join(favorites))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    restart_panel()


class StartMenuPage(Page):
    def build(self):
        self.button("Pin an app to the start menu", None, "Add", self.add)
        for item in read_favorites():
            self.button(item, None, "Unpin", lambda target=item: self.remove(target))

    def add(self):
        app_id = choose(self.window, "Pin to start", app_choices(), searchable=True)
        if app_id:
            favorites = read_favorites()
            if app_id not in favorites:
                write_favorites(favorites + [app_id])
        self.rebuild()

    def remove(self, item):
        write_favorites([entry for entry in read_favorites() if entry != item])
        self.rebuild()


class LockPage(Page):
    def build(self):
        if LOGIN_IMAGE.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(LOGIN_IMAGE), 420, 250, True)
                self.put(Gtk.Image.new_from_pixbuf(pixbuf))
            except Exception:
                pass
        self.note("The lock and login screen follow the colour preset and show your callsign.")
        self.button("Redraw the login screen", "Use this after changing the callsign", "Redraw", self.redraw)
        self.button("Lock now", None, "Lock", lambda: spawn(["nexus-lock"]))

    def redraw(self):
        self.root_task(lambda: root_quick("preset", active_key()), "Login screen redrawn")


def bootlogo_on():
    return read_kv("/boot/armbianEnv.txt").get("bootlogo", "true") == "true"


class BootPage(Page):
    def build(self):
        self.switch("Boot animation", "Grid sweep, callsign and SYSTEM ONLINE while starting up", bootlogo_on(),
                    self.toggle)

    def toggle(self, value):
        self.root_task(lambda: root_quick("bootlogo", "on" if value else "off"),
                       "Saved. It takes effect on the next restart.", refresh=False)


class SoundThemePage(Page):
    def build(self):
        current = Settings().get("SOUND_THEME", "preset")
        self.combo("Sound theme",
                   [("preset", "Follow the colour preset"), ("tactical", "Tactical"), ("quiet", "Quiet"), ("off", "Off")],
                   current, lambda value: Settings().set("SOUND_THEME", value))
        self.buttons("Preview", None, [
            ("Click", lambda: spawn(["nexus-sound", "menu-click"])),
            ("Beep", lambda: spawn(["nexus-sound", "notify"])),
            ("Alert", lambda: spawn(["nexus-sound", "alert"])),
            ("Startup", lambda: spawn(["nexus-sound", "startup"])),
        ])


class FontsPage(Page):
    def build(self):
        size = str(Settings().get_int("TEXT_SIZE", 11))
        self.combo("Text size", [("10", "Small"), ("11", "Normal"), ("13", "Large"), ("15", "Larger")], size,
                   self.set_size)
        self.note("Interface font: Share Tech Mono. Terminal font: JetBrains Mono.")

    def set_size(self, value):
        Settings().set("TEXT_SIZE", value)
        theme.apply_fonts(Settings())
        theme.apply_terminal(load_preset(active_key()), Settings())


PAGES = [
    ("preset", "Colour preset", "Amber, Green, Red, Blue, Pink / Purple", "theme colour color preset amber green red blue pink",
     PresetPage),
    ("custompreset", "Custom colour preset", "Make your own preset", "custom colour color own make create preset",
     CustomPresetPage),
    ("windows", "Window layout", "Stack (Windows style) or Split (Omarchy style)",
     "window layout tiling tile split stack omarchy snap arrange", WindowLayoutPage),
    ("wallpaper", "Wallpaper", "Preset grid or your own picture", "background wallpaper picture", WallpaperPage),
    ("hud", "HUD widgets", "Which widgets show, position, size, always on top", "conky widgets hud overlay", HudPage),
    ("taskbar", "Taskbar", "Size, pinned apps, auto-hide", "panel taskbar dock pinned", TaskbarPage),
    ("startmenu", "Start menu", "Pinned apps", "start menu whisker favourites", StartMenuPage),
    ("lock", "Lock screen and login", "Login look and callsign", "lock login lightdm greeter", LockPage),
    ("boot", "Boot animation", "On or off", "plymouth boot splash animation", BootPage),
    ("soundtheme", "Sound theme", "Tactical, quiet or off", "sounds beep click theme", SoundThemePage),
    ("fonts", "Fonts and text size", "Make text bigger or smaller", "font text size bigger", FontsPage),
]
