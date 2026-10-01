import select
import threading
import time

from gi.repository import Gdk, GLib, Gtk

from nexus import devices, system
from nexus.common import Settings, out, root, run, xfconf_get, xfconf_list, xfconf_set
from nexus_settings.ui import Page, background, confirm, label, styled


class BluetoothPage(Page):
    def build(self):
        powered = system.bt_powered()
        self.switch("Bluetooth", "Controllers, keyboards, headphones", powered, self.set_power)
        if not powered:
            return
        self.button("Find devices", "Put your device in pairing mode first", "Scan", self.scan)
        self.section("Devices")
        found = system.bt_devices()
        if not found:
            self.note("No devices yet. Press Scan.")
        for device in found:
            state = "Connected" if device["connected"] else ("Paired" if device["paired"] else "Not paired")
            actions = []
            if not device["paired"]:
                actions.append(("Pair", lambda mac=device["mac"]: self.act(system.bt_pair, mac, "Paired")))
            elif device["connected"]:
                actions.append(("Disconnect", lambda mac=device["mac"]: self.act(system.bt_disconnect, mac, "Disconnected")))
            else:
                actions.append(("Connect", lambda mac=device["mac"]: self.act(system.bt_connect, mac, "Connected")))
            if device["paired"]:
                actions.append(("Forget", lambda mac=device["mac"]: self.act(system.bt_forget, mac, "Forgotten")))
            self.buttons(device["name"], f"{state}  ·  {device['mac']}", actions)

    def set_power(self, value):
        self.task(lambda: system.set_bt(value), lambda r, e: self.rebuild())

    def scan(self):
        self.task(lambda: system.bt_scan(10), lambda r, e: self.rebuild(), busy="Scanning for 10 seconds...")

    def act(self, func, mac, done_text):
        def done(result, error):
            ok = error is None and (result is True or getattr(result, "code", 1) == 0)
            self.window.toast(done_text if ok else "That didn't work. Is the device in pairing mode?")
            self.rebuild()

        self.task(lambda: func(mac), done)


class ControllerPage(Page):
    def build(self):
        settings = Settings()
        self.section("Pairing")
        self.button("Pair a controller", "Hold the controller's pair button, then scan", "Bluetooth",
                    lambda: self.window.open_page("bluetooth"))
        self.section("Mouse mode")
        self.switch("Use the controller as a mouse", "Or hold Select + Start. Turns itself off in games.",
                    system.mousemode_get(), system.mousemode_set)
        self.note("Left stick moves the pointer, A clicks, B right-clicks, right stick scrolls.")
        self.scale("Hold time for Select + Start (seconds)", 1, 4, 0.5, settings.get_float("PAD_HOLD", 2),
                   lambda value: Settings().set("PAD_HOLD", f"{value:.1f}"), digits=1)
        self.scale("Pointer speed", 4, 30, 1, settings.get_float("PAD_SPEED", 12),
                   lambda value: Settings().set("PAD_SPEED", int(value)))
        self.scale("Stick dead zone (%)", 5, 40, 1, settings.get_float("PAD_DEADZONE", 0.15) * 100,
                   lambda value: Settings().set("PAD_DEADZONE", f"{value / 100:.2f}"))
        self.section("Test buttons")
        self.test_label = label("Press Start test, then press buttons and move the sticks.", "nexus-value")
        self.button("Button test", "Runs for 15 seconds", "Start test", self.start_test)
        self.put(self.test_label)

    def start_test(self):
        def work():
            try:
                from evdev import InputDevice, ecodes, list_devices
            except ImportError:
                GLib.idle_add(self.test_label.set_text, "python3-evdev is not installed")
                return
            pads = []
            for path in list_devices():
                device = InputDevice(path)
                keys = device.capabilities().get(ecodes.EV_KEY, [])
                if ecodes.BTN_SOUTH in keys and device.name != "NEXUS controller mouse":
                    pads.append(device)
            if not pads:
                GLib.idle_add(self.test_label.set_text, "No controller found. Pair it first.")
                return
            GLib.idle_add(self.test_label.set_text, f"Listening to {pads[0].name}...")
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                ready, _, _ = select.select(pads, [], [], 0.2)
                for device in ready:
                    for event in device.read():
                        if event.type == ecodes.EV_KEY and event.value == 1:
                            name = ecodes.BTN.get(event.code, ecodes.KEY.get(event.code, event.code))
                            if isinstance(name, list):
                                name = name[0]
                            GLib.idle_add(self.test_label.set_text, f"Pressed {name}")
                        elif event.type == ecodes.EV_ABS and event.code in (ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_RX, ecodes.ABS_RY):
                            name = ecodes.ABS.get(event.code, event.code)
                            GLib.idle_add(self.test_label.set_text, f"Stick {name} = {event.value}")
            GLib.idle_add(self.test_label.set_text, "Test finished.")

        threading.Thread(target=work, daemon=True).start()


LAYOUTS = [
    ("us", "English (US)"), ("gb", "English (UK)"), ("de", "German"), ("fr", "French"), ("es", "Spanish"),
    ("it", "Italian"), ("pt", "Portuguese"), ("se", "Swedish"), ("no", "Norwegian"), ("dk", "Danish"),
    ("fi", "Finnish"), ("nl", "Dutch"), ("pl", "Polish"), ("jp", "Japanese"),
]

SHORTCUTS = [
    ("Open start menu (Super)", "nexus-menu"),
    ("Settings", "nexus-settings"),
    ("Quick Settings", "nexus-quick-settings"),
    ("Show or hide HUD", "nexus-hud toggle"),
    ("Game launcher", "nexus-games"),
    ("Terminal", "xfce4-terminal"),
    ("On-screen keyboard", "nexus-osk"),
    ("Lock", "nexus-lock"),
    ("Files", "thunar"),
    ("Screenshot", "nexus-screenshot full"),
    ("Area screenshot", "nexus-screenshot area"),
    ("Task manager", "xfce4-taskmanager"),
]


def current_binding(command):
    for prop in xfconf_list("xfce4-keyboard-shortcuts"):
        if prop.startswith("/commands/custom/") and xfconf_get("xfce4-keyboard-shortcuts", prop) == command:
            return prop[len("/commands/custom/"):]
    return ""


class KeyboardPage(Page):
    def build(self):
        layout = xfconf_get("keyboard-layout", "/Default/XkbLayout") or "us"
        self.section("Layout")
        self.combo("Keyboard layout", LAYOUTS, layout.split(",")[0], self.set_layout)
        self.section("Typing")
        delay = int(xfconf_get("keyboards", "/Default/KeyRepeat/Delay") or 500)
        rate = int(xfconf_get("keyboards", "/Default/KeyRepeat/Rate") or 20)
        self.scale("Repeat delay (ms)", 150, 1000, 50, delay,
                   lambda value: xfconf_set("keyboards", "/Default/KeyRepeat/Delay", int(value), "int"))
        self.scale("Repeat speed", 5, 60, 1, rate,
                   lambda value: xfconf_set("keyboards", "/Default/KeyRepeat/Rate", int(value), "int"))
        self.section("Shortcuts")
        for title, command in SHORTCUTS:
            binding = current_binding(command)
            self.button(title, binding or "Not set", "Change", lambda cmd=command, old=binding: self.change(cmd, old))

    def set_layout(self, layout):
        xfconf_set("keyboard-layout", "/Default/XkbDisable", False)
        xfconf_set("keyboard-layout", "/Default/XkbLayout", layout)
        run(["setxkbmap", layout])

    def change(self, command, old):
        dialog = Gtk.Dialog(title="New shortcut", transient_for=self.window, modal=True)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Remove", Gtk.ResponseType.REJECT)
        box = dialog.get_content_area()
        box.set_border_width(20)
        box.add(label("Press the new key combination now."))
        result = {"accel": None}

        def on_key(widget, event):
            modifiers = event.state & Gtk.accelerator_get_default_mod_mask()
            keyval = Gdk.keyval_to_lower(event.keyval)
            name = Gdk.keyval_name(keyval) or ""
            if name.startswith(("Shift", "Control", "Alt", "Super", "Meta", "ISO_Level")):
                return True
            result["accel"] = Gtk.accelerator_name(keyval, modifiers)
            dialog.response(Gtk.ResponseType.OK)
            return True

        dialog.connect("key-press-event", on_key)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.REJECT and old:
            run(["xfconf-query", "-c", "xfce4-keyboard-shortcuts", "-p", f"/commands/custom/{old}", "-r"])
        elif response == Gtk.ResponseType.OK and result["accel"]:
            if old:
                run(["xfconf-query", "-c", "xfce4-keyboard-shortcuts", "-p", f"/commands/custom/{old}", "-r"])
            xfconf_set("xfce4-keyboard-shortcuts", f"/commands/custom/{result['accel']}", command)
            self.window.toast(f"Shortcut set to {result['accel']}")
        self.rebuild()


class MousePage(Page):
    def build(self):
        settings = Settings()
        self.scale("Pointer speed", -1, 1, 0.1, settings.get_float("POINTER_SPEED", 0), self.speed, digits=1)
        self.switch("Tap to click", "Tap the trackpad instead of pressing it", settings.get_bool("TAP_TO_CLICK"),
                    lambda value: self.save("TAP_TO_CLICK", value))
        self.switch("Natural scrolling", "Content follows your fingers, like a phone",
                    settings.get_bool("NATURAL_SCROLL"), lambda value: self.save("NATURAL_SCROLL", value))
        found = devices.pointers()
        self.note("Devices: " + (", ".join(found) if found else "none found"))

    def speed(self, value):
        self.save("POINTER_SPEED", f"{value:.1f}")

    def save(self, key, value):
        Settings().set(key, value)
        devices.apply_input()


class TouchPage(Page):
    def build(self):
        settings = Settings()
        self.button("Calibrate", "Tap the targets that appear on screen", "Start", self.calibrate)
        self.scale("Long-press time for right-click (ms)", 300, 1500, 50, settings.get_int("LONG_PRESS_MS", 600),
                   self.long_press)
        found = devices.touchscreens()
        self.note("Touchscreens: " + (", ".join(found) if found else "none found"))

    def long_press(self, value):
        Settings().set("LONG_PRESS_MS", int(value))
        devices.apply_input()

    def calibrate(self):
        def work():
            result = run(["xinput_calibrator", "--output-type", "xorg.conf.d"], timeout=180)
            text = result.out
            start = text.find('Section "InputClass"')
            end = text.find("EndSection", start)
            if start < 0 or end < 0:
                raise RuntimeError("Calibration was cancelled")
            return root("calibration", input_text=text[start:end + len("EndSection")] + "\n")

        self.root_task(work, "Calibration saved. It applies fully after a restart.", refresh=False)


PAGES = [
    ("bluetooth", "Bluetooth", "Pair, connect, forget", "bluetooth pair headphones controller keyboard", BluetoothPage),
    ("controller", "Controller", "Pair, test buttons, mouse mode, stick speed",
     "gamepad 8bitdo joystick mouse mode select start", ControllerPage),
    ("keyboard", "Keyboard", "Layout, repeat speed, shortcuts", "keyboard layout shortcut keys repeat", KeyboardPage),
    ("mouse", "Mouse & trackpad", "Speed, tap to click, scrolling", "mouse trackpad touchpad tap scroll", MousePage),
    ("touch", "Touchscreen", "Calibrate, long-press time", "touch screen calibrate long press right click", TouchPage),
]
