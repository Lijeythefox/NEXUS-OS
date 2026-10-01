import os
import subprocess
from collections import namedtuple
from pathlib import Path

SHARE_DIR = Path(os.environ.get("NEXUS_SHARE_DIR", "/usr/share/nexus"))
PRESET_DIR = Path(os.environ.get("NEXUS_PRESET_DIR", str(SHARE_DIR / "presets")))
DEFAULTS_DIR = SHARE_DIR / "defaults"
ETC_DIR = Path("/etc/nexus")
SYSTEM_PRESET_FILE = ETC_DIR / "preset"
CALLSIGN_FILE = ETC_DIR / "callsign"
VERSION_FILE = ETC_DIR / "version"
STATE_DIR = Path("/var/lib/nexus")
LOGIN_IMAGE = STATE_DIR / "login.png"
SD_MOUNT = Path("/mnt/sdcard")
APPS_DIR = Path("/opt/nexus/apps")

Result = namedtuple("Result", "code out err")


def config_dir():
    path = Path.home() / ".config" / "nexus"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_dir():
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    path = Path(base) / "nexus"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(cmd, input_text=None, timeout=30, env=None):
    full_env = None
    if env:
        full_env = dict(os.environ)
        full_env.update(env)
    try:
        done = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=timeout,
            env=full_env,
        )
    except FileNotFoundError:
        return Result(127, "", f"{cmd[0]} is not installed")
    except subprocess.TimeoutExpired:
        return Result(124, "", f"{cmd[0]} took too long")
    return Result(done.returncode, done.stdout, done.stderr)


def out(cmd, timeout=30):
    result = run(cmd, timeout=timeout)
    return result.out.strip() if result.code == 0 else ""


def ok(cmd, timeout=30):
    return run(cmd, timeout=timeout).code == 0


def spawn(cmd, env=None):
    full_env = None
    if env:
        full_env = dict(os.environ)
        full_env.update(env)
    try:
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=full_env,
        )
        return True
    except FileNotFoundError:
        return False


def read_kv(path):
    values = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_kv(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in values.items()]
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_text(path, default=""):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return default


class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path else config_dir() / "settings.conf"
        self.defaults = read_kv(DEFAULTS_DIR / "settings.conf")
        self.values = {}
        self.load()

    def load(self):
        self.values = dict(self.defaults)
        self.values.update(read_kv(self.path))

    def get(self, key, default=""):
        return self.values.get(key, default)

    def get_bool(self, key):
        return self.values.get(key, "0").lower() in ("1", "true", "yes", "on")

    def get_int(self, key, default=0):
        try:
            return int(float(self.values.get(key, default)))
        except ValueError:
            return default

    def get_float(self, key, default=0.0):
        try:
            return float(self.values.get(key, default))
        except ValueError:
            return default

    def set(self, key, value):
        if isinstance(value, bool):
            value = "1" if value else "0"
        self.load()
        self.values[key] = str(value)
        write_kv(self.path, self.values)


def callsign():
    return read_text(CALLSIGN_FILE, "NEXUS") or "NEXUS"


def notify(title, body="", icon="nexus-settings", urgency="normal", timeout=3000):
    spawn(["notify-send", "-a", "NEXUS", "-i", icon, "-u", urgency, "-t", str(timeout), title, body])


def sound(event):
    spawn(["nexus-sound", event])


def root_quick(*args):
    return run(["pkexec", "/usr/local/sbin/nexus-root-quick", *args], timeout=600)


def root(*args, input_text=None, timeout=3600):
    return run(["pkexec", "/usr/local/sbin/nexus-root", *args], input_text=input_text, timeout=timeout)


def xfconf_get(channel, prop):
    result = run(["xfconf-query", "-c", channel, "-p", prop])
    return result.out.strip() if result.code == 0 else None


def xfconf_set(channel, prop, value, kind="string"):
    if isinstance(value, bool):
        value = "true" if value else "false"
        kind = "bool"
    return ok(["xfconf-query", "-c", channel, "-p", prop, "-n", "-t", kind, "-s", str(value)])


def xfconf_set_array(channel, prop, values, kind="string"):
    cmd = ["xfconf-query", "-c", channel, "-p", prop, "-n", "-a"]
    for value in values:
        cmd += ["-t", kind, "-s", str(value)]
    if not values:
        return ok(["xfconf-query", "-c", channel, "-p", prop, "-r"])
    return ok(cmd)


def xfconf_list(channel):
    result = run(["xfconf-query", "-c", channel, "-l"])
    return result.out.split() if result.code == 0 else []


def split_terse(line):
    fields = []
    current = []
    escaped = False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    fields.append("".join(current))
    return fields
