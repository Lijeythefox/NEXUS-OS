import json
import re
import time
from pathlib import Path

from nexus.common import (
    Settings,
    ok,
    out,
    root,
    root_quick,
    run,
    runtime_dir,
    split_terse,
    spawn,
    xfconf_get,
    xfconf_set,
)


def wifi_enabled():
    return out(["nmcli", "radio", "wifi"]) == "enabled"


def set_wifi(enabled):
    return ok(["nmcli", "radio", "wifi", "on" if enabled else "off"])


def wifi_device():
    for line in out(["nmcli", "-t", "-f", "DEVICE,TYPE", "device"]).splitlines():
        fields = split_terse(line)
        if len(fields) >= 2 and fields[1] == "wifi":
            return fields[0]
    return ""


def wifi_scan(rescan=True):
    cmd = ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"]
    if rescan:
        cmd += ["--rescan", "yes"]
    networks = {}
    for line in out(cmd, timeout=40).splitlines():
        fields = split_terse(line)
        if len(fields) < 4 or not fields[1]:
            continue
        ssid = fields[1]
        signal = int(fields[2] or 0)
        entry = {"ssid": ssid, "signal": signal, "security": fields[3], "active": fields[0].strip() == "*"}
        if ssid not in networks or signal > networks[ssid]["signal"] or entry["active"]:
            networks[ssid] = entry
    return sorted(networks.values(), key=lambda item: (not item["active"], -item["signal"]))


def active_wifi():
    for line in out(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "device", "wifi"]).splitlines():
        fields = split_terse(line)
        if len(fields) >= 3 and fields[0] == "yes":
            return fields[1], int(fields[2] or 0)
    return None, 0


def wifi_saved():
    saved = []
    result = out(["nmcli", "-t", "-f", "NAME,UUID,TYPE,AUTOCONNECT,AUTOCONNECT-PRIORITY", "connection", "show"])
    for line in result.splitlines():
        fields = split_terse(line)
        if len(fields) >= 5 and fields[2] in ("802-11-wireless", "wifi"):
            saved.append({
                "name": fields[0],
                "uuid": fields[1],
                "autoconnect": fields[3] == "yes",
                "priority": int(fields[4] or 0),
            })
    return saved


def wifi_connect(ssid, password=None):
    for item in wifi_saved():
        if item["name"] == ssid:
            result = run(["nmcli", "connection", "up", "uuid", item["uuid"]], timeout=60)
            if result.code == 0 or password is None:
                return result
    cmd = ["nmcli", "device", "wifi", "connect", ssid]
    if password:
        cmd += ["password", password]
    return run(cmd, timeout=60)


def wifi_disconnect():
    device = wifi_device()
    return ok(["nmcli", "device", "disconnect", device]) if device else False


def wifi_forget(uuid):
    return ok(["nmcli", "connection", "delete", "uuid", uuid])


def set_hotspot_preference(name):
    for item in wifi_saved():
        priority = "20" if item["name"] == name else "0"
        run(["nmcli", "connection", "modify", "uuid", item["uuid"],
             "connection.autoconnect", "yes", "connection.autoconnect-priority", priority])


def hotspot_name():
    return Settings().get("HOTSPOT_SSID")


def hotspot_active():
    name = hotspot_name()
    ssid, _ = active_wifi()
    return bool(name) and ssid == name


def hotspot_toggle(enabled):
    name = hotspot_name()
    if not name:
        return False
    if enabled:
        return wifi_connect(name).code == 0
    return ok(["nmcli", "connection", "down", "id", name])


def bt_info(mac):
    info = {}
    for line in out(["bluetoothctl", "info", mac]).splitlines():
        line = line.strip()
        if ": " in line:
            key, value = line.split(": ", 1)
            info[key] = value
    return info


def bt_powered():
    return "Powered: yes" in out(["bluetoothctl", "show"])


def set_bt(enabled):
    if enabled:
        run(["rfkill", "unblock", "bluetooth"])
    return ok(["bluetoothctl", "power", "on" if enabled else "off"])


def bt_devices():
    devices = []
    for line in out(["bluetoothctl", "devices"]).splitlines():
        parts = line.split(" ", 2)
        if len(parts) < 3 or parts[0] != "Device":
            continue
        info = bt_info(parts[1])
        devices.append({
            "mac": parts[1],
            "name": info.get("Alias", parts[2]),
            "paired": info.get("Paired") == "yes",
            "connected": info.get("Connected") == "yes",
            "icon": info.get("Icon", "bluetooth"),
        })
    return sorted(devices, key=lambda item: (not item["connected"], not item["paired"], item["name"].lower()))


def bt_connected_count():
    return sum(1 for device in bt_devices() if device["connected"])


def bt_scan(seconds=10):
    run(["bluetoothctl", "--timeout", str(seconds), "scan", "on"], timeout=seconds + 10)


def bt_pair(mac):
    result = run(["bluetoothctl", "--timeout", "30", "pair", mac], timeout=45)
    run(["bluetoothctl", "trust", mac])
    connect = run(["bluetoothctl", "--timeout", "20", "connect", mac], timeout=30)
    return connect if connect.code == 0 else result


def bt_connect(mac):
    return run(["bluetoothctl", "--timeout", "20", "connect", mac], timeout=30)


def bt_disconnect(mac):
    return run(["bluetoothctl", "disconnect", mac])


def bt_forget(mac):
    return run(["bluetoothctl", "remove", mac])


def pactl_json(*args):
    result = run(["pactl", "--format=json", *args])
    if result.code != 0:
        return []
    try:
        return json.loads(result.out)
    except json.JSONDecodeError:
        return []


def audio_devices(kind="sinks"):
    default = out(["pactl", f"get-default-{kind[:-1]}"])
    devices = []
    for item in pactl_json("list", kind):
        name = item.get("name", "")
        if kind == "sources" and name.endswith(".monitor"):
            continue
        devices.append({"name": name, "description": item.get("description", name), "default": name == default})
    return devices


def set_default_audio(kind, name):
    return ok(["pactl", f"set-default-{kind[:-1]}", name])


def volume_get():
    text = out(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
    match = re.search(r"(\d+)%", text)
    muted = out(["pactl", "get-sink-mute", "@DEFAULT_SINK@"]).endswith("yes")
    return (int(match.group(1)) if match else 0), muted


def volume_set(percent):
    percent = max(0, min(150, int(percent)))
    return ok(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%"])


def mute_set(muted):
    return ok(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if muted else "0"])


def mic_get():
    text = out(["pactl", "get-source-volume", "@DEFAULT_SOURCE@"])
    match = re.search(r"(\d+)%", text)
    return int(match.group(1)) if match else 0


def mic_set(percent):
    return ok(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{max(0, min(150, int(percent)))}%"])


def brightness_available():
    return bool(list(Path("/sys/class/backlight").glob("*"))) and bool(out(["brightnessctl", "-l"]))


def brightness_get():
    current = out(["brightnessctl", "get"])
    maximum = out(["brightnessctl", "max"])
    try:
        return round(int(current) * 100 / max(int(maximum), 1))
    except ValueError:
        return 100


def brightness_set(percent):
    return ok(["brightnessctl", "set", f"{max(5, min(100, int(percent)))}%"])


def airplane_get():
    text = out(["rfkill", "list"])
    blocks = re.findall(r"Soft blocked: (yes|no)", text)
    return bool(blocks) and all(state == "yes" for state in blocks)


def airplane_set(enabled):
    if enabled:
        run(["nmcli", "radio", "all", "off"])
        run(["bluetoothctl", "power", "off"])
        return ok(["rfkill", "block", "all"])
    run(["rfkill", "unblock", "all"])
    run(["nmcli", "radio", "all", "on"])
    return ok(["bluetoothctl", "power", "on"])


def tailscale_status():
    result = run(["tailscale", "status", "--json"], timeout=10)
    if result.code != 0 and not result.out:
        return {"installed": result.code != 127, "state": "Stopped", "ips": [], "peers": [], "error": result.err.strip()}
    try:
        data = json.loads(result.out)
    except json.JSONDecodeError:
        return {"installed": True, "state": "Unknown", "ips": [], "peers": [], "error": result.err.strip()}
    peers = []
    for peer in (data.get("Peer") or {}).values():
        peers.append({
            "name": peer.get("HostName", "?"),
            "ip": (peer.get("TailscaleIPs") or ["?"])[0],
            "online": peer.get("Online", False),
            "os": peer.get("OS", ""),
        })
    self_info = data.get("Self") or {}
    return {
        "installed": True,
        "state": data.get("BackendState", "Unknown"),
        "ips": self_info.get("TailscaleIPs") or [],
        "peers": sorted(peers, key=lambda item: (not item["online"], item["name"].lower())),
        "auth_url": data.get("AuthURL", ""),
        "error": "",
    }


def tailscale_up():
    result = run(["tailscale", "up", "--timeout=8s"], timeout=20)
    text = result.out + result.err
    if "Access denied" in text or "permission" in text.lower():
        root("tailscale-operator")
        result = run(["tailscale", "up", "--timeout=8s"], timeout=20)
        text = result.out + result.err
    match = re.search(r"https://login\.tailscale\.com/\S+", text)
    if match:
        spawn(["xdg-open", match.group(0)])
        return "Finish signing in to Tailscale in the browser window that just opened."
    if result.code == 0:
        return ""
    return text.strip() or "Tailscale could not start."


def tailscale_down():
    result = run(["tailscale", "down"], timeout=20)
    if result.code != 0 and ("Access denied" in result.err or "permission" in result.err.lower()):
        root("tailscale-operator")
        result = run(["tailscale", "down"], timeout=20)
    return result.code == 0


def dnd_get():
    return xfconf_get("xfce4-notifyd", "/do-not-disturb") == "true"


def dnd_set(enabled):
    return xfconf_set("xfce4-notifyd", "/do-not-disturb", bool(enabled))


def onboard_running():
    return ok(["pgrep", "-x", "onboard"])


def osk_visible():
    if not onboard_running():
        return False
    text = out([
        "gdbus", "call", "--session", "--dest", "org.onboard.Onboard",
        "--object-path", "/org/onboard/Onboard/Keyboard",
        "--method", "org.freedesktop.DBus.Properties.Get", "org.onboard.Onboard.Keyboard", "Visible",
    ])
    return "true" in text


def osk_call(method):
    return ok([
        "gdbus", "call", "--session", "--dest", "org.onboard.Onboard",
        "--object-path", "/org/onboard/Onboard/Keyboard",
        "--method", f"org.onboard.Onboard.Keyboard.{method}",
    ])


def osk_set(visible):
    if visible and not onboard_running():
        spawn(["onboard"])
        for _ in range(30):
            time.sleep(0.2)
            if osk_call("Show"):
                return True
        return False
    return osk_call("Show" if visible else "Hide")


def mousemode_file():
    return runtime_dir() / "mousemode"


def mousemode_get():
    try:
        return mousemode_file().read_text().strip() == "1"
    except OSError:
        return False


def mousemode_set(enabled):
    mousemode_file().write_text("1\n" if enabled else "0\n")
    return True


def governor_apply(mode):
    return root_quick("governor", mode).code == 0


def ip_address():
    for address in out(["hostname", "-I"]).split():
        if "." in address and not address.startswith("100."):
            return address
    return ""
