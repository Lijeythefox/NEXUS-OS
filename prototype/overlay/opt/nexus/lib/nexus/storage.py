import json
import re

from nexus.common import out

DRIVE_LABEL = "NEXUS-SD"
USB_DISK = re.compile(r"/dev/sd[a-z]+")
SYSTEM_PATHS = ("/", "/boot", "/boot/firmware")


def flag(value):
    return str(value).lower() in ("1", "true")


def block_devices(device=None):
    cmd = ["lsblk", "-J", "-o", "NAME,PATH,TYPE,SIZE,TRAN,RM,HOTPLUG,VENDOR,MODEL,LABEL,MOUNTPOINTS"]
    if device:
        cmd.append(device)
    try:
        return json.loads(out(cmd) or "{}").get("blockdevices", [])
    except json.JSONDecodeError:
        return []


def system_disks():
    disks = set()
    for path in SYSTEM_PATHS:
        source = out(["findmnt", "-n", "-o", "SOURCE", "--target", path]).split("[")[0]
        if not source.startswith("/dev/"):
            continue
        for line in out(["lsblk", "-nlso", "PATH,TYPE", source]).splitlines():
            fields = line.split()
            if len(fields) == 2 and fields[1] == "disk":
                disks.add(fields[0])
    return disks


def mountpoints(disk):
    points = [point for point in disk.get("mountpoints") or [] if point]
    for child in disk.get("children") or []:
        points += mountpoints(child)
    return points


def labels(disk):
    found = [disk["label"]] if disk.get("label") else []
    for child in disk.get("children") or []:
        found += labels(child)
    return found


def refusal(disk, protected):
    path = disk.get("path") or ""
    if "mmcblk" in path:
        return "Memory cards (mmcblk) are never formatted here. NEXUS runs from the microSD card."
    if disk.get("type") != "disk" or not USB_DISK.fullmatch(path):
        return f"{path or 'That'} is not a USB drive"
    if not protected:
        return "Couldn't work out which disk the system runs from, so nothing was erased"
    if path in protected:
        return "That disk holds the running system, so it can't be erased"
    if disk.get("tran") != "usb" or not (flag(disk.get("rm")) or flag(disk.get("hotplug"))):
        return f"{path} is not a removable USB drive"
    for point in mountpoints(disk):
        if point in ("/", "[SWAP]") or point.startswith("/boot"):
            return f"{path} is in use by the system ({point})"
    return None


def usb_drives():
    protected = system_disks()
    return [disk for disk in block_devices() if refusal(disk, protected) is None]


def describe(disk):
    parts = [(disk.get(key) or "").strip() for key in ("vendor", "model")]
    name = " ".join(part for part in parts if part) or "USB drive"
    return f"{name} ({disk.get('size') or '?'})"


def labelled_drive_present():
    return any(DRIVE_LABEL in labels(disk) for disk in block_devices())
