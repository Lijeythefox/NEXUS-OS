import json
import sys
import time

from nexus.battery import percent_from_mv, write_state
from nexus.common import Settings, notify, root_quick, run, runtime_dir, sound

PICO_VENDOR_ID = 0x2E8A
HANDSHAKE_SECONDS = 4
LOW_LEVELS = (15, 5)


def pause_file():
    return runtime_dir() / "pico-paused"


def paused():
    return pause_file().exists()


class LidSensor:
    def __init__(self):
        self.ignored = set()
        self.lid = "open"
        self.warned = set()
        self.samples = []

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
                self.handle(data)
                return handle
        handle.close()
        self.ignored.add(device)
        return None

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
        lid = data.get("lid", "open")
        if lid != self.lid:
            self.lid = lid
            self.lid_changed(lid)
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
                write_state({"present": False})
                time.sleep(5)
                continue
            try:
                while not paused():
                    data = self.parse(handle.readline())
                    if data:
                        self.handle(data)
            except Exception:
                pass
            finally:
                handle.close()
            time.sleep(1)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "run"
    if command == "pause":
        pause_file().write_text("1\n")
        print("Lid sensor paused. You can now program the Pico in Thonny.")
        return 0
    if command == "resume":
        pause_file().unlink(missing_ok=True)
        print("Lid sensor resumed.")
        return 0
    try:
        LidSensor().loop()
    except ImportError:
        print("python3-serial is missing", file=sys.stderr)
        return 1
    return 0
