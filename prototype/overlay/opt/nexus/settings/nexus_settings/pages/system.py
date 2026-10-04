import os
import shutil
from pathlib import Path

from gi.repository import Gtk

from nexus import battery, devices, storage, system
from nexus.common import (
    SD_MOUNT,
    VERSION_FILE,
    Settings,
    callsign,
    notify,
    out,
    read_kv,
    read_text,
    root,
    root_quick,
    run,
    spawn,
    xfconf_get,
    xfconf_set,
)
from nexus.presets import active_preset
from nexus_settings.ui import Page, ask_text, choose, confirm, label, message


class DisplayPage(Page):
    def build(self):
        settings = Settings()
        output = devices.primary_output()
        self.section("Screen")
        if output:
            current = settings.get("DISPLAY_MODE") or output["current"]
            self.combo("Resolution", [(mode, mode) for mode in output["modes"]], current, self.set_mode,
                       subtitle=f"Output {output['name']}")
        else:
            self.note("No screen was detected.")
        dpi = xfconf_get("xsettings", "/Xft/DPI") or "96"
        self.combo("Scale", [("96", "100%"), ("120", "125%"), ("144", "150%"), ("168", "175%")], dpi, self.set_scale,
                   subtitle="Makes text and apps bigger")
        self.combo(
            "Rotation",
            [("normal", "Normal"), ("left", "Rotate left"), ("right", "Rotate right"), ("inverted", "Upside down")],
            settings.get("DISPLAY_ROTATION", "normal"), self.set_rotation,
            subtitle="The touchscreen is rotated to match",
        )
        self.section("Brightness")
        if system.brightness_available():
            self.scale("Brightness", 5, 100, 5, system.brightness_get(), system.brightness_set)
        else:
            self.note("This screen sets its brightness with its own buttons, so there is no slider here.")
        self.section("Night light")
        self.switch("Night light", "Warmer colours that are easier on the eyes at night",
                    settings.get_bool("NIGHT_LIGHT"), lambda value: self.save("NIGHT_LIGHT", value))
        self.scale("Strength", 0, 100, 5, settings.get_float("NIGHT_LIGHT_STRENGTH", 0.5) * 100,
                   lambda value: self.save("NIGHT_LIGHT_STRENGTH", f"{value / 100:.2f}"))

    def save(self, key, value):
        Settings().set(key, value)
        devices.apply_display()

    def set_mode(self, mode):
        self.save("DISPLAY_MODE", mode)
        self.window.toast(f"Resolution set to {mode}")

    def set_scale(self, dpi):
        xfconf_set("xsettings", "/Xft/DPI", int(dpi), "int")
        self.window.toast("Scale changed. Some apps need restarting to follow it.")

    def set_rotation(self, rotation):
        self.save("DISPLAY_ROTATION", rotation)


class SoundPage(Page):
    def build(self):
        self.section("Output")
        sinks = system.audio_devices("sinks")
        if sinks:
            active = next((item["name"] for item in sinks if item["default"]), sinks[0]["name"])
            self.combo("Play sound through", [(item["name"], item["description"]) for item in sinks], active,
                       lambda name: system.set_default_audio("sinks", name))
        volume, muted = system.volume_get()
        self.scale("Volume", 0, 100, 5, volume, system.volume_set)
        self.switch("Mute", None, muted, system.mute_set)
        self.button("Test speakers", "Plays a short tone", "Play", lambda: spawn(["nexus-sound", "test"]))
        self.section("Input")
        sources = system.audio_devices("sources")
        if sources:
            active = next((item["name"] for item in sources if item["default"]), sources[0]["name"])
            self.combo("Microphone", [(item["name"], item["description"]) for item in sources], active,
                       lambda name: system.set_default_audio("sources", name))
            self.scale("Microphone level", 0, 100, 5, system.mic_get(), system.mic_set)
        else:
            self.note("No microphone found.")
        self.section("More")
        self.button("Volume mixer", "Per-app volume and advanced options", "Open", lambda: spawn(["pavucontrol"]))


class NotificationsPage(Page):
    def build(self):
        settings = Settings()
        self.switch("Do not disturb", "Hide pop-up notifications", system.dnd_get(), system.dnd_set)
        self.switch("Notification sound", "Beep when a notification arrives", settings.get_bool("NOTIFY_SOUND"),
                    lambda value: Settings().set("NOTIFY_SOUND", value))
        self.button("Test", "Send a test notification", "Send",
                    lambda: notify("NEXUS", "This is a test notification."))


SCREEN_OFF = [("1", "1 minute"), ("2", "2 minutes"), ("5", "5 minutes"), ("10", "10 minutes"),
              ("15", "15 minutes"), ("30", "30 minutes"), ("0", "Never")]


class PowerPage(Page):
    def build(self):
        settings = Settings()
        data = battery.read()
        self.section("Battery")
        if data.get("present"):
            self.info("Level", f"{data.get('percent', 0)}%")
            self.info("Status", "Charging" if data.get("charging") else "On battery")
            self.info("Voltage", f"{data.get('millivolts', 0) / 1000:.2f} V")
        elif data.get("paused"):
            self.note("The Pico sensor is paused so you can program it.")
        else:
            self.note("The battery level comes from the Pico hinge sensor. It isn't connected yet.")
        paused = data.get("paused", False)
        self.button("Pico sensor", "Pause it while you program the Pico in Thonny. The deck buttons stop while paused.",
                    "Resume" if paused else "Pause", lambda: self.toggle_pico(paused))
        self.section("Screen and sleep")
        current = str(int(xfconf_get("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-off") or 10))
        self.combo("Turn off the screen after", SCREEN_OFF, current, self.set_screen_off)
        self.combo("When the lid closes",
                   [("screen-off", "Screen off and lock (recommended)"), ("suspend", "Sleep"), ("nothing", "Do nothing")],
                   settings.get("LID_ACTION", "screen-off"), lambda value: Settings().set("LID_ACTION", value),
                   subtitle="Sleep is unreliable on this board, so screen off is the default")
        self.section("Performance")
        self.combo("Performance mode",
                   [("balanced", "Balanced"), ("performance", "Best performance"), ("powersave", "Battery saver")],
                   settings.get("PERF_MODE", "balanced"), self.set_mode)
        self.switch("Boost while gaming", "Best performance automatically while a game is running",
                    settings.get_bool("GAME_PERFORMANCE"), lambda value: Settings().set("GAME_PERFORMANCE", value))

    def toggle_pico(self, paused):
        run(["nexus-pico", "resume" if paused else "pause"])
        self.rebuild()

    def set_screen_off(self, minutes):
        minutes = int(minutes)
        for key in ("dpms-on-ac-off", "dpms-on-battery-off"):
            xfconf_set("xfce4-power-manager", f"/xfce4-power-manager/{key}", minutes, "uint")
        xfconf_set("xfce4-power-manager", "/xfce4-power-manager/dpms-enabled", minutes > 0)

    def set_mode(self, mode):
        Settings().set("PERF_MODE", mode)
        self.task(lambda: root_quick("governor-default", mode), lambda r, e: self.window.toast("Performance mode changed"))


def usage(path):
    try:
        total, used, free = shutil.disk_usage(path)
    except OSError:
        return None
    return total, used, free


def size(value):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


class StoragePage(Page):
    def build(self):
        self.section("Boot microSD card")
        self.usage_row("System and apps", "/")
        self.note("NEXUS runs from this card. Reflashing replaces it but never touches the storage drive.")
        self.section(f"Storage drive ({storage.DRIVE_LABEL})")
        if os.path.ismount(SD_MOUNT):
            self.usage_row("Games and personal files", str(SD_MOUNT))
            self.buttons("Drive folders", "ROMs, Files, Minecraft and Snapshots",
                         [("Open", lambda: spawn(["thunar", str(SD_MOUNT)])), ("Set up folders", self.setup)])
        elif storage.labelled_drive_present():
            self.note(f"The {storage.DRIVE_LABEL} drive is plugged in but not mounted yet.")
            self.button("Use the drive", "Mounts it and checks its folders", "Mount", self.setup)
        else:
            self.note(f"No {storage.DRIVE_LABEL} drive found. Games, files, Minecraft and snapshots are stored on a "
                      "USB drive plugged into the deck's internal USB hub.")
            self.button("Prepare storage drive", "Formats a USB drive for NEXUS. This erases everything on it.",
                        "Prepare", self.prepare, style="destructive-action")
        self.section("Clean up")
        self.button("Free up space", "Removes download caches, old logs, thumbnails and the trash", "Clean up",
                    self.cleanup)

    def usage_row(self, title, path):
        data = usage(path)
        if not data:
            return
        total, used, free = data
        bar = Gtk.LevelBar(min_value=0, max_value=1, value=used / total if total else 0)
        bar.set_size_request(220, 10)
        self.row(title, f"{size(used)} used of {size(total)}  ({size(free)} free)", bar)

    def setup(self):
        self.root_task(lambda: root("storage-setup"), "Drive folders are ready")

    def prepare(self):
        drives = storage.usb_drives()
        if not drives:
            message(self.window, "No USB drive found. Plug one into the deck's USB hub and try again. "
                                 "The microSD card NEXUS runs from is never listed.")
            return
        options = []
        for disk in drives:
            text = f"{storage.describe(disk)}  ·  {disk['path']}"
            names = storage.labels(disk)
            if names:
                text += f"  ·  now named {', '.join(names)}"
            options.append((disk["path"], text))
        device = choose(self.window, "Pick the USB drive to prepare", options)
        if not device:
            return
        disk = next(item for item in drives if item["path"] == device)
        answer = ask_text(self.window, "Prepare storage drive",
                          f"{storage.describe(disk)} at {device} will be ERASED and renamed {storage.DRIVE_LABEL}. "
                          "Everything on it will be lost.\n\nType ERASE to continue.")
        if answer != "ERASE":
            return
        self.root_task(lambda: root("storage-format", device),
                       "The storage drive is ready. Log out and back in to use it.")

    def cleanup(self):
        def work():
            for folder in (Path.home() / ".cache/thumbnails",):
                shutil.rmtree(folder, ignore_errors=True)
            run(["gio", "trash", "--empty"])
            return root("cleanup")

        self.root_task(work, "Cleaned up")


class AboutPage(Page):
    def build(self):
        version = read_kv(VERSION_FILE)
        model = read_text("/proc/device-tree/model", "Unknown").replace("\x00", "")
        memory = "?"
        for line in read_text("/proc/meminfo").splitlines():
            if line.startswith("MemTotal:"):
                memory = size(int(line.split()[1]) * 1024)
        self.put(label(callsign(), "nexus-heading"))
        self.note("Callsign. Change it in Accounts.")
        self.section("This deck")
        self.info("Board", model)
        self.info("Memory", memory)
        self.info("Processor cores", os.cpu_count() or "?")
        self.info("Name on the network", out(["hostname"]))
        self.info("IP address", system.ip_address() or "Not connected")
        self.section("Software")
        self.info("NEXUS OS", version.get("NEXUS_VERSION", "unknown"))
        self.info("Debian", read_text("/etc/debian_version", "?"))
        self.info("Kernel", out(["uname", "-r"]))
        self.info("Colour preset", active_preset().name)


PAGES = [
    ("display", "Display", "Resolution, scale, rotation, brightness, night light",
     "screen monitor resolution scale rotate brightness night light", DisplayPage),
    ("sound", "Sound", "Output, input, volume, test speakers", "audio speaker headphones volume microphone", SoundPage),
    ("notifications", "Notifications", "Do not disturb, notification sound", "alerts dnd popups", NotificationsPage),
    ("power", "Power & battery", "Battery level, screen timeout, lid, performance",
     "battery sleep lid performance cpu screen off pico", PowerPage),
    ("storage", "Storage", "Boot microSD and storage drive usage, clean up",
     "disk space sd card usb drive nexus-sd format prepare clean", StoragePage),
    ("about", "About", "Callsign, board, OS version", "version info board system", AboutPage),
]
