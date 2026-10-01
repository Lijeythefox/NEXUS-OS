import json
import os
import shutil
from pathlib import Path

from gi.repository import Gtk

from nexus import battery, devices, system
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
from nexus_settings.ui import Page, ask_text, confirm, label, message


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
        self.button("Pico sensor", "Pause it while you program the Pico in Thonny",
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


def find_card():
    root_source = out(["findmnt", "-n", "-o", "SOURCE", "/"])
    root_disk = out(["lsblk", "-no", "PKNAME", root_source])
    try:
        data = json.loads(out(["lsblk", "-J", "-o", "NAME,TYPE,SIZE,TRAN,RM,MODEL"]))
    except json.JSONDecodeError:
        return None
    for disk in data.get("blockdevices", []):
        name = disk.get("name", "")
        if disk.get("type") == "disk" and name.startswith("mmcblk") and name != root_disk and "boot" not in name:
            return f"/dev/{name}", disk.get("size", "?")
    return None


class StoragePage(Page):
    def build(self):
        self.section("Internal storage (eMMC)")
        self.usage_row("System and apps", "/")
        self.section("Micro SD card")
        if os.path.ismount(SD_MOUNT):
            self.usage_row("Games and personal files", str(SD_MOUNT))
            self.buttons("Card folders", "ROMs, Files, Minecraft and Snapshots",
                         [("Open", lambda: spawn(["thunar", str(SD_MOUNT)])), ("Set up folders", self.setup)])
        else:
            card = find_card()
            if card:
                self.note(f"A card was found ({card[1]}) but it isn't set up for NEXUS yet.")
                self.button("Prepare card", "Formats the card for NEXUS. This erases everything on it.",
                            "Prepare", lambda: self.prepare(card[0]), style="destructive-action")
            else:
                self.note("No micro SD card found. Games, files and snapshots are stored on the card.")
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
        self.root_task(lambda: root("sd-setup"), "Card folders are ready")

    def prepare(self, device):
        answer = ask_text(self.window, "Prepare card",
                          f"Everything on {device} will be erased. Type ERASE to continue.")
        if answer != "ERASE":
            return
        self.root_task(lambda: root("sd-format", device), "The card is ready")

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
    ("storage", "Storage", "eMMC and micro SD usage, clean up", "disk space sd card format clean", StoragePage),
    ("about", "About", "Callsign, board, OS version", "version info board system", AboutPage),
]
