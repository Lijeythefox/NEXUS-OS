import json
import sys
import time

from nexus.battery import percent_from_mv, write_state
from nexus.common import Settings, notify, root_quick, run, runtime_dir, sound

PICO_VENDOR_ID = 0x2E8A
HANDSHAKE_SECONDS = 4
SILENT_SECONDS = 5
LOW_LEVELS = (15, 5)
DECK_NAME = "NEXUS Deck Buttons"
DECK_VENDOR_ID = 0x2E8A
DECK_PRODUCT_ID = 0x4E58
DECK_VERSION = 0x0001
DECK_BUTTONS = ("up", "down", "left", "right", "a", "b", "x", "y")
FACE_BUTTONS = {"a": "BTN_SOUTH", "b": "BTN_EAST", "x": "BTN_WEST", "y": "BTN_NORTH"}


def pause_file():
    return runtime_dir() / "pico-paused"


def paused():
    return pause_file().exists()


class DeckButtons:
    def __init__(self):
        from evdev import AbsInfo, UInput, ecodes

        self.ecodes = ecodes
        self.codes = {name: getattr(ecodes, code) for name, code in FACE_BUTTONS.items()}
        hat = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)
        self.device = UInput(
            {
                ecodes.EV_KEY: list(self.codes.values()),
                ecodes.EV_ABS: [(ecodes.ABS_HAT0X, hat), (ecodes.ABS_HAT0Y, hat)],
            },
            name=DECK_NAME,
            vendor=DECK_VENDOR_ID,
            product=DECK_PRODUCT_ID,
            version=DECK_VERSION,
            bustype=ecodes.BUS_USB,
        )
        self.state = dict.fromkeys(DECK_BUTTONS, False)

    def update(self, buttons):
        state = {name: bool(buttons.get(name)) for name in DECK_BUTTONS}
        if state == self.state:
            return
        self.state = state
        ecodes = self.ecodes
        for name, code in self.codes.items():
            self.device.write(ecodes.EV_KEY, code, int(state[name]))
        self.device.write(ecodes.EV_ABS, ecodes.ABS_HAT0X, int(state["right"]) - int(state["left"]))
        self.device.write(ecodes.EV_ABS, ecodes.ABS_HAT0Y, int(state["down"]) - int(state["up"]))
        self.device.syn()

    def release_all(self):
        self.update({})


class LidSensor:
    def __init__(self):
        self.ignored = set()
        self.lid = "open"
        self.warned = set()
        self.samples = []
        self.deck = None
        self.last_seen = 0.0

    def candidate_ports(self):
        from serial.tools import list_ports

        ports = []
        for port in list_ports.comports():
            if port.vid == PICO_VENDOR_ID and port.device not in self.ignored:
                ports.append(port.device)
        present = {port.device for port in list_ports.comports()}
        self.ignored &= present
        return ports

    def open_sensor(self, device):
        import serial

        handle = serial.Serial(device, 115200, timeout=1)
        deadline = time.monotonic() + HANDSHAKE_SECONDS
        while time.monotonic() < deadline:
            data = self.parse(handle.readline())
            if data:
                self.ensure_deck()
                self.handle(data)
                return handle
        handle.close()
        self.ignored.add(device)
        return None

    def ensure_deck(self):
        if self.deck is not None:
            return
        try:
            self.deck = DeckButtons()
        except (ImportError, OSError) as error:
            print(f"nexus-pico: deck buttons unavailable: {error}", file=sys.stderr)

    def release_buttons(self):
        if self.deck is not None:
            self.deck.release_all()

    def parse(self, line):
        try:
            data = json.loads(line.decode("utf-8", "replace").strip() or "{}")
        except json.JSONDecodeError:
            return None
        return data if data.get("nexus") == "lid-sensor" else None

    def lid_changed(self, state):
        settings = Settings()
        action = settings.get("LID_ACTION", "screen-off")
        if state == "closed":
            if action == "nothing":
                return
            run(["light-locker-command", "-l"])
            if action == "suspend":
                run(["systemctl", "suspend"])
            else:
                run(["xset", "dpms", "force", "off"])
                root_quick("governor", "powersave")
        else:
            run(["xset", "dpms", "force", "on"])
            run(["xset", "s", "reset"])
            root_quick("governor", settings.get("PERF_MODE", "balanced"))

    def handle(self, data):
        self.last_seen = time.monotonic()
        buttons = data.get("buttons")
        if self.deck is not None and isinstance(buttons, dict):
            self.deck.update(buttons)
        lid = data.get("lid", "open")
        if lid != self.lid:
            self.lid = lid
            self.lid_changed(lid)
        if "mv" not in data:
            return
        millivolts = int(data.get("mv", 0))
        self.samples = (self.samples + [millivolts])[-5:]
        average = sum(self.samples) / len(self.samples)
        percent = percent_from_mv(average)
        charging = bool(data.get("charging"))
        write_state({
            "present": millivolts > 500,
            "percent": percent,
            "millivolts": round(average),
            "charging": charging,
            "lid": lid,
        })
        if charging or millivolts <= 500:
            self.warned.clear()
            return
        for level in LOW_LEVELS:
            if percent <= level and level not in self.warned:
                self.warned.add(level)
                sound("alert")
                notify(
                    "Battery low",
                    f"{percent}% left. Plug in the charger soon.",
                    icon="battery-caution",
                    urgency="critical",
                    timeout=10000,
                )

    def loop(self):
        while True:
            if paused():
                self.release_buttons()
                write_state({"present": False, "paused": True})
                time.sleep(2)
                continue
            handle = None
            for device in self.candidate_ports():
                try:
                    handle = self.open_sensor(device)
                except Exception:
                    handle = None
                if handle:
                    break
            if not handle:
                self.release_buttons()
                write_state({"present": False})
                time.sleep(5)
                continue
            try:
                while not paused():
                    data = self.parse(handle.readline())
                    if data:
                        self.handle(data)
                    elif time.monotonic() - self.last_seen > SILENT_SECONDS:
                        self.release_buttons()
            except Exception:
                pass
            finally:
                handle.close()
                self.release_buttons()
            time.sleep(1)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "run"
    if command == "pause":
        pause_file().write_text("1\n")
        print("Pico sensor paused (lid, battery and deck buttons). You can now program the Pico in Thonny.")
        return 0
    if command == "resume":
        pause_file().unlink(missing_ok=True)
        print("Pico sensor resumed.")
        return 0
    try:
        LidSensor().loop()
    except ImportError:
        print("python3-serial is missing", file=sys.stderr)
        return 1
    return 0
