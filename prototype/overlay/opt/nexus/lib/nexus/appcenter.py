import configparser
import re
from dataclasses import dataclass, field
from pathlib import Path

from nexus.common import SHARE_DIR, run

CATALOGUE = SHARE_DIR / "appcenter.conf"
LIBRETRO_DIR = Path("/usr/lib/aarch64-linux-gnu/libretro")
CORE_URL = "https://buildbot.libretro.com/nightly/linux/aarch64/latest/{core}_libretro.so.zip"
KINDS = ("builtin", "apt", "core")
NAME_RE = re.compile(r"[a-z0-9][a-z0-9_+.-]*")


@dataclass
class Entry:
    key: str
    name: str
    category: str
    kind: str
    description: str = ""
    launch: str = ""
    browser: bool = False
    packages: list = field(default_factory=list)
    cores: list = field(default_factory=list)
    systems: list = field(default_factory=list)


def load(path=CATALOGUE):
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error:
        return []
    entries = []
    for key in parser.sections():
        section = parser[key]
        kind = section.get("kind", "apt")
        words = {name: [word for word in section.get(name, "").split() if NAME_RE.fullmatch(word)]
                 for name in ("packages", "cores", "systems")}
        if kind not in KINDS or (kind == "apt" and not words["packages"]) or (kind == "core" and not words["cores"]):
            continue
        entries.append(Entry(
            key=key,
            name=section.get("name", key),
            category=section.get("category", "Other"),
            kind=kind,
            description=section.get("description", ""),
            launch=section.get("launch", ""),
            browser=section.get("browser", "0") == "1",
            **words,
        ))
    return entries


def get(key):
    for entry in load():
        if entry.key == key:
            return entry
    raise RuntimeError(f"{key} is not in the App Center")


def categories(entries):
    seen = []
    for entry in entries:
        if entry.category not in seen:
            seen.append(entry.category)
    return seen


def package_installed(package):
    result = run(["dpkg-query", "-W", "-f=${db:Status-Abbrev}", package])
    return result.code == 0 and result.out.startswith("ii")


def core_path(core):
    return LIBRETRO_DIR / f"{core}_libretro.so"


def installed(entry):
    if entry.kind == "builtin":
        return True
    if entry.kind == "apt":
        return all(package_installed(package) for package in entry.packages)
    return all(core_path(core).exists() for core in entry.cores)


def installed_map(entries):
    packages = sorted({package for entry in entries if entry.kind == "apt" for package in entry.packages})
    present = set()
    if packages:
        listing = run(["dpkg-query", "-W", "-f=${Package} ${db:Status-Abbrev}\n", *packages]).out
        present = {line.split()[0] for line in listing.splitlines() if line.split()[1:2] == ["ii"]}
    states = {}
    for entry in entries:
        if entry.kind == "apt":
            states[entry.key] = all(package in present for package in entry.packages)
        else:
            states[entry.key] = installed(entry)
    return states


def launch_id(entry):
    if entry.launch:
        return entry.launch
    for package in entry.packages[:1]:
        for line in run(["dpkg-query", "-L", package]).out.splitlines():
            if line.startswith("/usr/share/applications/") and line.endswith(".desktop"):
                return line.rsplit("/", 1)[1]
    return ""


def installed_systems():
    systems = []
    for entry in load():
        if entry.kind == "core" and installed(entry):
            systems += entry.systems
    return systems
