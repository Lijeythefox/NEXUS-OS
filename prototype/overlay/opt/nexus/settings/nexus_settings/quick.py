import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk

from nexus import battery, hud, system
from nexus.common import Settings, callsign, spawn
from nexus.presets import active_key, list_presets
from nexus_settings.pages.personal import apply_preset, draw_preset
from nexus_settings.ui import background, debounce, label, load_css, set_quiet, styled


def tailscale_running():
    return system.tailscale_status()["state"] == "Running"


def tailscale_set(value):
    return system.tailscale_up() if value else system.tailscale_down()


TILES = [
    ("wifi", "Wi-Fi", "network-wireless-symbolic", system.wifi_enabled, system.set_wifi),
    ("bluetooth", "Bluetooth", "bluetooth-active-symbolic", system.bt_powered, system.set_bt),
    ("hotspot", "Hotspot", "network-cellular-symbolic", system.hotspot_active, system.hotspot_toggle),
    ("vpn", "VPN", "network-vpn-symbolic", tailscale_running, tailscale_set),
    ("osk", "Keyboard", "input-keyboard-symbolic", system.osk_visible, system.osk_set),
    ("mouse", "Mouse mode", "input-gaming-symbolic", system.mousemode_get, system.mousemode_set),
    ("hud", "HUD", "view-grid-symbolic", hud.running, hud.set_visible),
    ("airplane", "Airplane", "airplane-mode-symbolic", system.airplane_get, system.airplane_set),
    ("dnd", "Do not disturb", "notifications-disabled-symbolic", system.dnd_get, system.dnd_set),
]


class QuickWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Quick Settings")
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_default_size(400, -1)
        self.positioned = False
        self.connect("key-press-event", self.on_key)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("size-allocate", self.place)

        frame = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12), "nexus-quick")
        for side in ("start", "end", "top", "bottom"):
            getattr(frame, f"set_margin_{side}")(0)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for side in ("start", "end", "top", "bottom"):
            getattr(inner, f"set_margin_{side}")(14)
        frame.add(inner)
        self.add(frame)

        header = Gtk.Box(spacing=8)
        header.add(label(f"// {callsign()}", "nexus-value", wrap=False))
        self.battery_label = label("", "nexus-subtitle", wrap=False, xalign=1)
        header.pack_start(self.battery_label, True, True, 0)
        for icon, tooltip, action in (
            ("emblem-system-symbolic", "Settings", lambda: self.launch(["nexus-settings"])),
            ("system-lock-screen-symbolic", "Lock", lambda: self.launch(["nexus-lock"])),
            ("system-shutdown-symbolic", "Power", lambda: self.launch(["xfce4-session-logout"])),
        ):
            button = Gtk.Button.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
            button.set_tooltip_text(tooltip)
            button.connect("clicked", lambda _, act=action: act())
            header.add(button)
        inner.add(header)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)
        self.tiles = {}
        for index, (key, title, icon, getter, setter) in enumerate(TILES):
            tile = styled(Gtk.ToggleButton(), "nexus-tile")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.LARGE_TOOLBAR))
            box.add(label(title, xalign=0.5, wrap=False))
            tile.add(box)
            tile.nexus_handler = tile.connect("toggled", self.on_tile, key, setter)
            self.tiles[key] = (tile, getter)
            grid.attach(tile, index % 3, index // 3, 1, 1)
        inner.add(grid)

        volume, muted = system.volume_get()
        self.volume = self.slider(inner, "audio-volume-high-symbolic", volume, system.volume_set)
        if system.brightness_available():
            self.slider(inner, "display-brightness-symbolic", system.brightness_get(), system.brightness_set)

        presets = Gtk.Box(spacing=6, homogeneous=True)
        current = active_key()
        for preset in list_presets():
            button = styled(Gtk.Button(), "nexus-preset")
            if preset.key == current:
                styled(button, "active")
            area = Gtk.DrawingArea()
            area.set_size_request(56, 34)
            area.connect("draw", self.draw_swatch, preset)
            button.add(area)
            button.set_tooltip_text(preset.name)
            button.connect("clicked", lambda _, key=preset.key: self.pick_preset(key))
            presets.add(button)
        inner.add(presets)
        self.status = label("", "nexus-subtitle", wrap=False)
        inner.add(self.status)

        self.refresh()
        GLib.timeout_add_seconds(3, self.refresh)

    def draw_swatch(self, widget, cr, preset):
        from nexus.presets import hex_to_rgb

        c = preset.palette()
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        cr.set_source_rgb(*hex_to_rgb(c["bg"]))
        cr.rectangle(0, 0, width, height)
        cr.fill()
        cr.set_source_rgb(*hex_to_rgb(c["primary"]))
        cr.rectangle(0, height - 10, width, 10)
        cr.fill()
        cr.set_source_rgb(*hex_to_rgb(c["secondary"]))
        cr.rectangle(6, 6, width / 2, 10)
        cr.fill()
        return False

    def slider(self, parent, icon, value, setter):
        row = Gtk.Box(spacing=10)
        row.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.LARGE_TOOLBAR))
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        scale.set_value(value)
        scale.set_hexpand(True)
        scale.set_draw_value(False)
        delayed = debounce(setter, 150)
        scale.nexus_handler = scale.connect("value-changed", lambda w: delayed(w.get_value()))
        row.add(scale)
        parent.add(row)
        return scale

    def place(self, widget, allocation):
        if self.positioned:
            return
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        area = monitor.get_workarea()
        width, height = self.get_size()
        self.move(area.x + area.width - width - 10, area.y + area.height - height - 10)
        self.positioned = True

    def refresh(self):
        def work():
            states = {key: getter() for key, (_, getter) in self.tiles.items()}
            return states, battery.summary(), system.active_wifi()

        def done(result, error):
            if not result:
                return
            states, battery_text, (ssid, _) = result
            for key, value in states.items():
                set_quiet(self.tiles[key][0], value)
            self.battery_label.set_text(f"BAT {battery_text}")
            self.status.set_text(f"WIFI {ssid}" if ssid else "WIFI not connected")
            self.tiles["hotspot"][0].set_sensitive(bool(Settings().get("HOTSPOT_SSID")))

        background(work, done)
        return True

    def on_tile(self, tile, key, setter):
        value = tile.get_active()
        self.status.set_text("Working...")

        def done(result, error):
            if isinstance(result, str) and result:
                self.status.set_text(result)
            self.refresh()

        background(lambda: setter(value), done)

    def pick_preset(self, key):
        self.status.set_text("Recolouring everything...")
        apply_preset(self, key, self.close)

    def busy(self, text):
        if text:
            self.status.set_text(text)

    def toast(self, text):
        self.status.set_text(text)

    def launch(self, cmd):
        spawn(cmd)
        self.close()

    def on_focus_out(self, widget, event):
        GLib.timeout_add(150, self.close_if_unfocused)
        return False

    def close_if_unfocused(self):
        if not self.is_active():
            self.close()
        return False

    def on_key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


class QuickApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.nexus.QuickSettings")
        self.window = None

    def do_activate(self):
        if self.window is not None:
            self.window.close()
            self.window = None
            return
        load_css()
        spawn(["nexus-sound", "menu-click"])
        self.window = QuickWindow(self)
        self.window.connect("destroy", lambda *_: setattr(self, "window", None))
        self.window.show_all()
        self.window.present()


def main(argv=None):
    return QuickApp().run(None)
