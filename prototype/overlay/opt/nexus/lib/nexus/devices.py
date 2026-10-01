import re
import sys

from nexus.common import Settings, out, run

ROTATIONS = {
    "normal": "1 0 0 0 1 0 0 0 1",
    "left": "0 -1 1 1 0 0 0 0 1",
    "right": "0 1 0 -1 0 1 0 0 1",
    "inverted": "-1 0 1 0 -1 1 0 0 1",
}


def outputs():
    found = []
    current = None
    for line in out(["xrandr", "--query"]).splitlines():
        match = re.match(r"^(\S+) connected( primary)?", line)
        if match:
            current = {"name": match.group(1), "modes": [], "current": "", "primary": bool(match.group(2))}
            found.append(current)
            continue
        if re.match(r"^\S", line):
            current = None
            continue
        if current is not None:
            mode = re.match(r"^\s+(\d+x\d+)\s+(.*)$", line)
            if mode:
                if mode.group(1) not in current["modes"]:
                    current["modes"].append(mode.group(1))
                if "*" in mode.group(2):
                    current["current"] = mode.group(1)
    return found


def primary_output():
    found = outputs()
    for item in found:
        if item["primary"]:
            return item
    return found[0] if found else None


def xinput_devices():
    ids = out(["xinput", "list", "--id-only"]).split()
    names = out(["xinput", "list", "--name-only"]).splitlines()
    return [(device_id, name.strip()) for device_id, name in zip(ids, names)]


def props(device_id):
    return out(["xinput", "list-props", device_id])


def has_prop(device_id, name):
    return name in props(device_id)


def touchscreen_ids():
    return [device_id for device_id, _ in xinput_devices() if has_prop(device_id, "Evdev Third Button Emulation")]


def pointer_ids():
    return [device_id for device_id, _ in xinput_devices() if has_prop(device_id, "libinput Accel Speed")]


def names_for(ids):
    lookup = dict(xinput_devices())
    return [lookup.get(device_id, device_id) for device_id in ids]


def touchscreens():
    return names_for(touchscreen_ids())


def pointers():
    return names_for(pointer_ids())


def set_prop(device_id, name, *values):
    return run(["xinput", "set-prop", device_id, name, *[str(value) for value in values]]).code == 0


def apply_display(settings=None):
    settings = settings or Settings()
    output = primary_output()
    if not output:
        return False
    cmd = ["xrandr", "--output", output["name"]]
    mode = settings.get("DISPLAY_MODE")
    if mode and mode in output["modes"]:
        cmd += ["--mode", mode]
    rotation = settings.get("DISPLAY_ROTATION", "normal")
    if rotation not in ROTATIONS:
        rotation = "normal"
    cmd += ["--rotate", rotation]
    if settings.get_bool("NIGHT_LIGHT"):
        strength = max(0.0, min(1.0, settings.get_float("NIGHT_LIGHT_STRENGTH", 0.5)))
        cmd += ["--gamma", f"1:{1 - 0.25 * strength:.2f}:{1 - 0.55 * strength:.2f}"]
    else:
        cmd += ["--gamma", "1:1:1"]
    run(cmd)
    matrix = ROTATIONS[rotation].split()
    for device_id in touchscreen_ids():
        set_prop(device_id, "Coordinate Transformation Matrix", *matrix)
    return True


def apply_input(settings=None):
    settings = settings or Settings()
    speed = max(-1.0, min(1.0, settings.get_float("POINTER_SPEED", 0.0)))
    for device_id in pointer_ids():
        set_prop(device_id, "libinput Accel Speed", f"{speed:.2f}")
        if has_prop(device_id, "libinput Tapping Enabled"):
            set_prop(device_id, "libinput Tapping Enabled", 1 if settings.get_bool("TAP_TO_CLICK") else 0)
        if has_prop(device_id, "libinput Natural Scrolling Enabled"):
            set_prop(device_id, "libinput Natural Scrolling Enabled", 1 if settings.get_bool("NATURAL_SCROLL") else 0)
    timeout = settings.get_int("LONG_PRESS_MS", 600)
    for device_id in touchscreen_ids():
        set_prop(device_id, "Evdev Third Button Emulation", 1)
        set_prop(device_id, "Evdev Third Button Emulation Timeout", timeout)
        set_prop(device_id, "Evdev Third Button Emulation Button", 3)
        set_prop(device_id, "Evdev Third Button Emulation Threshold", 30)
    return True


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "all"
    if command in ("display", "all"):
        apply_display()
    if command in ("input", "all"):
        apply_input()
    return 0
