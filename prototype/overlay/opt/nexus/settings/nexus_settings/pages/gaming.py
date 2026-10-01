import re
from pathlib import Path

from nexus.common import Settings, spawn
from nexus_settings.ui import Page, pick_file

ES_SETTINGS = Path.home() / "ES-DE/settings/es_settings.xml"
PRISM_CFG = Path.home() / ".local/share/PrismLauncher/prismlauncher.cfg"
EMULATORS = [
    ("NES", "Mesen"), ("SNES", "Snes9x"), ("Game Boy / Color", "Gambatte"), ("Game Boy Advance", "mGBA"),
    ("Mega Drive", "Genesis Plus GX"), ("Arcade / MAME", "MAME 2003-Plus"), ("Neo Geo", "FinalBurn Neo"),
    ("PlayStation", "PCSX ReARMed"), ("Nintendo 64", "ParaLLEl N64"), ("PSP", "PPSSPP"), ("Dreamcast", "Flycast"),
]


def rom_directory():
    try:
        match = re.search(r'name="ROMDirectory" value="([^"]*)"', ES_SETTINGS.read_text(encoding="utf-8"))
        return match.group(1) if match else "/mnt/sdcard/ROMs"
    except OSError:
        return "/mnt/sdcard/ROMs"


def set_rom_directory(path):
    ES_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    text = ES_SETTINGS.read_text(encoding="utf-8") if ES_SETTINGS.exists() else '<?xml version="1.0"?>\n'
    line = f'<string name="ROMDirectory" value="{path}" />'
    if 'name="ROMDirectory"' in text:
        text = re.sub(r'<string name="ROMDirectory" value="[^"]*" />', line, text)
    else:
        text += line + "\n"
    ES_SETTINGS.write_text(text, encoding="utf-8")


def prism_value(key, default):
    try:
        for line in PRISM_CFG.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1]
    except OSError:
        pass
    return default


def set_prism_value(key, value):
    PRISM_CFG.parent.mkdir(parents=True, exist_ok=True)
    lines = PRISM_CFG.read_text(encoding="utf-8").splitlines() if PRISM_CFG.exists() else ["[General]"]
    lines = [line for line in lines if not line.startswith(f"{key}=")]
    index = lines.index("[General]") + 1 if "[General]" in lines else 0
    lines.insert(index, f"{key}={value}")
    PRISM_CFG.write_text("\n".join(lines) + "\n", encoding="utf-8")


class LauncherPage(Page):
    def build(self):
        self.info("Game folder", rom_directory())
        self.note("One folder per system, for example ROMs/snes or ROMs/psx. Put BIOS files in ROMs/bios.")
        self.buttons("Games", None, [("Change folder", self.change), ("Open ES-DE", lambda: spawn(["nexus-games"]))])

    def change(self):
        path = pick_file(self.window, "Game folder", folder=True)
        if path:
            set_rom_directory(path)
            self.rebuild()


class PerformancePage(Page):
    def build(self):
        self.switch("Emulator performance mode", "Runs the CPU at full speed while a game is open",
                    Settings().get_bool("GAME_PERFORMANCE"), lambda value: Settings().set("GAME_PERFORMANCE", value))
        self.note("Mouse mode always switches off while a game is running.")


class ControlsPage(Page):
    def build(self):
        self.note("Controllers are set up automatically. To change buttons for one system, start a game, "
                  "press Select + Start to open the RetroArch menu, then Controls > Manage Remap Files > "
                  "Save Core Remap File.")
        self.button("RetroArch", "Advanced controller and video options", "Open", lambda: spawn(["retroarch"]))
        self.section("Emulator per system")
        for system_name, core in EMULATORS:
            self.info(system_name, core)


class MinecraftPage(Page):
    def build(self):
        memory = int(prism_value("MaxMemAlloc", "3072"))
        self.scale("Memory limit (MB)", 1024, 6144, 512, memory,
                   lambda value: set_prism_value("MaxMemAlloc", int(value)))
        self.note("A ready-made Fabric instance with Sodium is copied to the micro SD card the first time you log "
                  "in with the card inserted.")
        self.button("Minecraft", "Prism Launcher", "Open", lambda: spawn(["nexus-prism"]))


PAGES = [
    ("games", "Game launcher", "Game folder for ES-DE", "es-de emulationstation roms games folder", LauncherPage),
    ("emuperf", "Emulator performance", "Full speed while gaming", "performance emulator speed", PerformancePage),
    ("controls", "Controller layouts", "Per-system controls in RetroArch", "controls remap retroarch buttons", ControlsPage),
    ("minecraft", "Minecraft", "Memory limit", "minecraft prism java memory ram", MinecraftPage),
]
