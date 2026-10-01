import configparser
import os
import sys
from pathlib import Path

from nexus.common import DEFAULTS_DIR, config_dir, ok, run, spawn

WIDGETS = {
    "clock": {"title": "Clock, date and weather", "height": 150},
    "system": {"title": "CPU temperature and usage", "height": 150},
    "network": {"title": "Wi-Fi, Bluetooth and VPN", "height": 150},
    "battery": {"title": "Battery and charging", "height": 96},
}
POSITIONS = {
    "top_right": "Top right",
    "top_left": "Top left",
    "bottom_right": "Bottom right",
    "bottom_left": "Bottom left",
}
SIZES = {"small": 0.85, "medium": 1.0, "large": 1.25}
PANEL_HEIGHT = 48
EDGE_GAP = 16
STACK_GAP = 12
CONKY_PATTERN = r"conky -q -c .*/\.config/conky/"


def hud_file():
    return config_dir() / "hud.conf"


def load():
    parser = configparser.ConfigParser()
    parser.read([DEFAULTS_DIR / "hud.conf", hud_file()])
    if not parser.has_section("hud"):
        parser.add_section("hud")
    for name in WIDGETS:
        if not parser.has_section(name):
            parser.add_section(name)
    return parser


def save(parser):
    with open(hud_file(), "w", encoding="utf-8") as handle:
        parser.write(handle)


def visible():
    return load().getboolean("hud", "visible", fallback=True)


def set_visible(value):
    parser = load()
    parser.set("hud", "visible", "1" if value else "0")
    save(parser)
    if value:
        start()
    else:
        stop()


def widget(name):
    parser = load()
    return {
        "enabled": parser.getboolean(name, "enabled", fallback=True),
        "position": parser.get(name, "position", fallback="top_right"),
        "size": parser.get(name, "size", fallback="medium"),
        "ontop": parser.getboolean(name, "ontop", fallback=False),
    }


def set_widget(name, **values):
    parser = load()
    for key, value in values.items():
        if isinstance(value, bool):
            value = "1" if value else "0"
        parser.set(name, key, str(value))
    save(parser)
    if running() or visible():
        start()


def running():
    return ok(["pgrep", "-f", CONKY_PATTERN])


def stop():
    run(["pkill", "-f", CONKY_PATTERN])


def start():
    stop()
    stacks = {}
    for name in WIDGETS:
        config = widget(name)
        if config["enabled"]:
            stacks.setdefault(config["position"], []).append((name, config))
    conky_dir = Path.home() / ".config" / "conky"
    for position, items in stacks.items():
        offset = EDGE_GAP + (PANEL_HEIGHT if position.startswith("bottom") else 0)
        for name, config in items:
            scale = SIZES.get(config["size"], 1.0)
            env = {
                "NEXUS_HUD_ALIGN": position,
                "NEXUS_HUD_GAP_X": str(EDGE_GAP),
                "NEXUS_HUD_GAP_Y": str(offset),
                "NEXUS_HUD_SCALE": str(scale),
                "NEXUS_HUD_ONTOP": "1" if config["ontop"] else "0",
            }
            path = conky_dir / f"{name}.conf"
            if path.exists():
                spawn(["conky", "-q", "-c", str(path)], env=env)
            offset += int(WIDGETS[name]["height"] * scale) + STACK_GAP


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "toggle"
    if command == "start":
        set_visible(True)
    elif command == "stop":
        set_visible(False)
    elif command == "toggle":
        set_visible(not running())
    elif command == "restart":
        if running():
            start()
    elif command == "login":
        if visible():
            start()
    else:
        print("usage: nexus-hud [start|stop|toggle|restart|login]", file=sys.stderr)
        return 2
    return 0
