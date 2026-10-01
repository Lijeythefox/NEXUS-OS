import os
import select
import sys
import time

from nexus.common import Settings, notify, out, root_quick, sound
from nexus.system import mousemode_file, mousemode_get, mousemode_set

GAME_PROCESSES = {"es-de", "retroarch", "ppsspp", "flycast", "ppssppsdl"}
TICK = 0.01
RESCAN_SECONDS = 3
GAME_CHECK_SECONDS = 2
SETTINGS_SECONDS = 2


def game_running():
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/comm", encoding="utf-8") as handle:
                name = handle.read().strip().lower()
        except OSError:
            continue
        if name in GAME_PROCESSES:
            return True
        if name == "java":
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as handle:
                    if b"minecraft" in handle.read().lower():
                        return True
            except OSError:
                continue
    return False


class PadDaemon:
    def __init__(self):
        from evdev import UInput, ecodes

        self.ecodes = ecodes
        self.devices = {}
        self.ranges = {}
        self.axes = {}
        self.pressed = set()
        self.combo_since = None
        self.combo_fired = False
        self.game = False
        self.boosted = False
        self.motion = [0.0, 0.0, 0.0]
        self.settings = Settings()
        self.state_mtime = 0
        self.mouse_mode = mousemode_get()
        self.mouse = UInput(
            {
                ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE],
                ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL],
            },
            name="NEXUS controller mouse",
        )
        self.button_map = {
            ecodes.BTN_SOUTH: ecodes.BTN_LEFT,
            ecodes.BTN_EAST: ecodes.BTN_RIGHT,
            ecodes.BTN_THUMBL: ecodes.BTN_MIDDLE,
        }

    def is_gamepad(self, device):
        capabilities = device.capabilities()
        keys = capabilities.get(self.ecodes.EV_KEY, [])
        return self.ecodes.BTN_SOUTH in keys and self.ecodes.EV_ABS in capabilities

    def rescan(self):
        from evdev import InputDevice, list_devices

        for path in list_devices():
            if path in self.devices:
                continue
            try:
                device = InputDevice(path)
            except OSError:
                continue
            if device.name == "NEXUS controller mouse" or not self.is_gamepad(device):
                device.close()
                continue
            self.devices[path] = device
            for code, info in device.capabilities().get(self.ecodes.EV_ABS, []):
                self.ranges[(path, code)] = (info.min, info.max)

    def drop(self, path):
        device = self.devices.pop(path, None)
        if device:
            try:
                device.close()
            except OSError:
                pass
        for key in [key for key in self.axes if key[0] == path]:
            self.axes.pop(key, None)

    def axis(self, code):
        deadzone = self.settings.get_float("PAD_DEADZONE", 0.15)
        value = 0.0
        for (path, axis_code), raw in self.axes.items():
            if axis_code == code and abs(raw) > abs(value):
                value = raw
        if abs(value) < deadzone:
            return 0.0
        sign = 1 if value > 0 else -1
        scaled = (abs(value) - deadzone) / (1 - deadzone)
        return sign * scaled * scaled

    def emit_button(self, code, value):
        self.mouse.write(self.ecodes.EV_KEY, code, value)
        self.mouse.syn()

    def release_all(self):
        for code in self.button_map.values():
            self.emit_button(code, 0)

    def set_mode(self, enabled, announce=True):
        self.mouse_mode = enabled
        mousemode_set(enabled)
        self.state_mtime = mousemode_file().stat().st_mtime
        if not enabled:
            self.release_all()
        if announce:
            notify("Controller", "Mouse mode on" if enabled else "Mouse mode off", icon="nexus-mousemode", timeout=1500)
            sound("device-added" if enabled else "device-removed")

    def handle(self, path, event):
        ecodes = self.ecodes
        if event.type == ecodes.EV_KEY:
            if event.value == 1:
                self.pressed.add(event.code)
            elif event.value == 0:
                self.pressed.discard(event.code)
            if self.mouse_mode and not self.game and event.code in self.button_map and event.value in (0, 1):
                self.emit_button(self.button_map[event.code], event.value)
        elif event.type == ecodes.EV_ABS:
            low, high = self.ranges.get((path, event.code), (-32768, 32767))
            centre = (low + high) / 2
            half = max((high - low) / 2, 1)
            self.axes[(path, event.code)] = max(-1.0, min(1.0, (event.value - centre) / half))

    def check_combo(self, now):
        ecodes = self.ecodes
        combo = {ecodes.BTN_SELECT, ecodes.BTN_START}
        if combo <= self.pressed and not self.game:
            if self.combo_since is None:
                self.combo_since = now
            elif not self.combo_fired and now - self.combo_since >= self.settings.get_float("PAD_HOLD", 2.0):
                self.combo_fired = True
                self.set_mode(not self.mouse_mode)
        else:
            self.combo_since = None
            self.combo_fired = False

    def move(self):
        ecodes = self.ecodes
        if not self.mouse_mode or self.game:
            return
        speed = self.settings.get_float("PAD_SPEED", 12)
        self.motion[0] += self.axis(ecodes.ABS_X) * speed
        self.motion[1] += self.axis(ecodes.ABS_Y) * speed
        self.motion[2] -= self.axis(ecodes.ABS_RY) * 0.2
        dx, dy, wheel = int(self.motion[0]), int(self.motion[1]), int(self.motion[2])
        self.motion = [self.motion[0] - dx, self.motion[1] - dy, self.motion[2] - wheel]
        if dx or dy or wheel:
            if dx:
                self.mouse.write(ecodes.EV_REL, ecodes.REL_X, dx)
            if dy:
                self.mouse.write(ecodes.EV_REL, ecodes.REL_Y, dy)
            if wheel:
                self.mouse.write(ecodes.EV_REL, ecodes.REL_WHEEL, wheel)
            self.mouse.syn()

    def update_game(self):
        game = game_running()
        if game == self.game:
            return
        self.game = game
        if game:
            self.release_all()
        if self.settings.get_bool("GAME_PERFORMANCE"):
            if game and not self.boosted:
                root_quick("governor", "performance")
                self.boosted = True
            elif not game and self.boosted:
                root_quick("governor", self.settings.get("PERF_MODE", "balanced"))
                self.boosted = False

    def watch_state(self):
        try:
            mtime = mousemode_file().stat().st_mtime
        except OSError:
            return
        if mtime != self.state_mtime:
            self.state_mtime = mtime
            wanted = mousemode_get()
            if wanted != self.mouse_mode:
                self.mouse_mode = wanted
                if not wanted:
                    self.release_all()

    def loop(self):
        last_scan = last_game = last_settings = 0.0
        while True:
            now = time.monotonic()
            if now - last_scan > RESCAN_SECONDS:
                self.rescan()
                last_scan = now
            if now - last_game > GAME_CHECK_SECONDS:
                self.update_game()
                last_game = now
            if now - last_settings > SETTINGS_SECONDS:
                self.settings.load()
                self.watch_state()
                last_settings = now
            fds = {device.fd: path for path, device in self.devices.items()}
            if fds:
                readable, _, _ = select.select(list(fds), [], [], TICK)
            else:
                time.sleep(0.25)
                readable = []
            for fd in readable:
                path = fds[fd]
                device = self.devices.get(path)
                if not device:
                    continue
                try:
                    for event in device.read():
                        self.handle(path, event)
                except OSError:
                    self.drop(path)
            self.check_combo(time.monotonic())
            self.move()


def main(argv=None):
    while True:
        try:
            PadDaemon().loop()
        except ImportError:
            print("python3-evdev is missing", file=sys.stderr)
            return 1
        except OSError as error:
            print(f"nexus-pad: {error}; retrying", file=sys.stderr)
            time.sleep(10)


def mousemode_main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "toggle"
    current = mousemode_get()
    if command == "status":
        print("on" if current else "off")
        return 0
    wanted = {"on": True, "off": False, "toggle": not current}.get(command)
    if wanted is None:
        print("usage: nexus-mousemode [on|off|toggle|status]", file=sys.stderr)
        return 2
    mousemode_set(wanted)
    notify("Controller", "Mouse mode on" if wanted else "Mouse mode off", icon="nexus-mousemode", timeout=1500)
    return 0
