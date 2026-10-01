import glob
import sys
from xml.sax.saxutils import escape

from nexus import battery, system
from nexus.common import out, read_text
from nexus.presets import active_preset


def cpu_temp():
    temps = []
    for path in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            temps.append(int(read_text(path, "0")) / 1000)
        except ValueError:
            continue
    return f"{max(temps):.0f}" if temps else "--"


def wifi_line():
    if not system.wifi_enabled():
        return "WIFI OFF"
    ssid, signal = system.active_wifi()
    return f"{ssid[:16]}  {signal}%" if ssid else "NOT CONNECTED"


def bluetooth_line():
    if not system.bt_powered():
        return "BT OFF"
    count = system.bt_connected_count()
    return f"BT ON  {count} LINKED"


def vpn_line():
    status = system.tailscale_status()
    if status["state"] == "Running":
        return f"VPN UP  {(status['ips'] or ['?'])[0]}"
    return "VPN DOWN"


def battery_percent():
    data = battery.read()
    return str(data.get("percent", 0)) if data.get("present") else "0"


def battery_label():
    data = battery.read()
    if data.get("paused"):
        return "SENSOR PAUSED"
    if not data.get("present"):
        return "NO SENSOR"
    return "CHARGING" if data.get("charging") else "ON BATTERY"


def battery_detail():
    data = battery.read()
    if not data.get("present"):
        return "Connect the Pico sensor"
    return f"{data.get('millivolts', 0) / 1000:.2f} V   LID {data.get('lid', 'open').upper()}"


def status_bar():
    c = active_preset().palette()
    ssid, signal = system.active_wifi()
    ssid = escape(ssid) if ssid else ssid
    wifi = f"WIFI {signal}" if ssid else "WIFI --"
    volume, muted = system.volume_get()
    vol = "VOL MUTE" if muted else f"VOL {volume}"
    bat = f"BAT {battery.summary()}"
    pad = f"<span foreground='{c['alert']}'>PAD</span>  " if system.mousemode_get() else ""
    text = f"{pad}<span foreground='{c['primary']}'>{wifi}</span>  {vol}  {bat}"
    tooltip = f"Wi-Fi: {ssid or 'not connected'}\nVolume: {volume}%\nBattery: {battery.summary()}\nClick for Quick Settings"
    return (
        f"<txt> {text} </txt>"
        "<txtclick>nexus-quick-settings</txtclick>"
        f"<tool>{tooltip}</tool>"
    )


COMMANDS = {
    "cpu-temp": cpu_temp,
    "wifi": wifi_line,
    "bluetooth": bluetooth_line,
    "vpn": vpn_line,
    "battery-percent": battery_percent,
    "battery-label": battery_label,
    "battery-detail": battery_detail,
    "iface": lambda: system.wifi_device() or "wlan0",
    "ip": lambda: system.ip_address() or "NO IP",
    "status-bar": status_bar,
    "battery": battery.summary,
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else ""
    func = COMMANDS.get(command)
    if not func:
        print("usage: nexus-info [" + "|".join(COMMANDS) + "]", file=sys.stderr)
        return 2
    try:
        print(func())
    except Exception:
        print("--")
    return 0
