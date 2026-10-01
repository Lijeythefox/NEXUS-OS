import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

MINECRAFT_VERSION = "1.21.1"
MODS = ["fabric-api", "sodium", "lithium", "ferrite-core", "immediatelyfast"]
OPTIONS = {
    "renderDistance": "6",
    "simulationDistance": "5",
    "graphicsMode": "0",
    "maxFps": "60",
    "enableVsync": "false",
    "entityShadows": "false",
    "particles": "2",
    "mipmapLevels": "0",
    "biomeBlendRadius": "0",
    "ao": "false",
    "guiScale": "2",
}


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "NEXUS-OS-build (github.com/Lijeythefox/NEXUS-OS)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download(url, target):
    request = urllib.request.Request(url, headers={"User-Agent": "NEXUS-OS-build"})
    with urllib.request.urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())


def latest_loader():
    for entry in get_json("https://meta.fabricmc.net/v2/versions/loader"):
        if entry.get("stable"):
            return entry["version"]
    raise RuntimeError("No stable Fabric loader found")


def mod_file(slug):
    query = urllib.parse.urlencode({
        "loaders": json.dumps(["fabric"]),
        "game_versions": json.dumps([MINECRAFT_VERSION]),
    })
    versions = get_json(f"https://api.modrinth.com/v2/project/{slug}/version?{query}")
    releases = [item for item in versions if item.get("version_type") == "release"] or versions
    if not releases:
        raise RuntimeError(f"No {slug} build for {MINECRAFT_VERSION}")
    files = releases[0]["files"]
    primary = next((item for item in files if item.get("primary")), files[0])
    return primary["filename"], primary["url"]


def main(argv):
    target = Path(argv[1])
    game = target / "minecraft"
    mods = game / "mods"
    mods.mkdir(parents=True, exist_ok=True)
    loader = latest_loader()
    (target / "instance.cfg").write_text(
        "\n".join([
            "InstanceType=OneSix",
            f"name=NEXUS Fabric {MINECRAFT_VERSION}",
            "iconKey=default",
            "notes=Tuned for the NEXUS deck: Fabric with Sodium, Lithium, FerriteCore and ImmediatelyFast.",
            "",
        ]),
        encoding="utf-8",
    )
    pack = {
        "components": [
            {"uid": "net.minecraft", "version": MINECRAFT_VERSION, "important": True},
            {"uid": "net.fabricmc.intermediary", "version": MINECRAFT_VERSION, "dependencyOnly": True},
            {"uid": "net.fabricmc.fabric-loader", "version": loader},
        ],
        "formatVersion": 1,
    }
    (target / "mmc-pack.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    (game / "options.txt").write_text("\n".join(f"{key}:{value}" for key, value in OPTIONS.items()) + "\n",
                                     encoding="utf-8")
    for slug in MODS:
        try:
            filename, url = mod_file(slug)
            download(url, mods / filename)
            print(f"[minecraft] {slug}: {filename}")
        except Exception as error:
            print(f"::warning::Skipped mod {slug}: {error}")
    print(f"[minecraft] Fabric loader {loader} for Minecraft {MINECRAFT_VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
