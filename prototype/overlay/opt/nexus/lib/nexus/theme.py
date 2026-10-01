import sys
from pathlib import Path

from nexus import hud
from nexus.common import (
    SHARE_DIR,
    Settings,
    config_dir,
    out,
    run,
    xfconf_list,
    xfconf_set,
)
from nexus.presets import active_preset, bare
from nexus.assets import ansi_palette


def wallpaper_path(preset, settings):
    choice = settings.get("WALLPAPER", "preset")
    if choice and choice != "preset" and Path(choice).is_file():
        return choice
    return str(SHARE_DIR / "wallpapers" / f"{preset.key}.png")


def monitors():
    names = []
    for line in out(["xrandr", "--listmonitors"]).splitlines()[1:]:
        parts = line.split()
        if parts:
            names.append(parts[-1])
    return names


def set_wallpaper(path):
    props = {prop for prop in xfconf_list("xfce4-desktop") if prop.endswith("/last-image")}
    for name in monitors() + ["0"]:
        props.add(f"/backdrop/screen0/monitor{name}/workspace0/last-image")
    for prop in props:
        xfconf_set("xfce4-desktop", prop, path)
        xfconf_set("xfce4-desktop", prop.replace("/last-image", "/image-style"), 5, "int")


def apply_terminal(preset, settings):
    c = preset.palette()
    size = settings.get_int("TEXT_SIZE", 11)
    xfconf_set("xfce4-terminal", "/color-use-theme", False)
    xfconf_set("xfce4-terminal", "/color-foreground", c["text"])
    xfconf_set("xfce4-terminal", "/color-background", c["bg"])
    xfconf_set("xfce4-terminal", "/color-cursor", c["primary"])
    xfconf_set("xfce4-terminal", "/color-cursor-use-default", False)
    xfconf_set("xfce4-terminal", "/color-selection", c["text_hi"])
    xfconf_set("xfce4-terminal", "/color-selection-background", c["selection"])
    xfconf_set("xfce4-terminal", "/color-selection-use-default", False)
    xfconf_set("xfce4-terminal", "/color-bold-use-default", True)
    xfconf_set("xfce4-terminal", "/color-palette", ";".join(ansi_palette(preset)))
    xfconf_set("xfce4-terminal", "/font-use-system", False)
    xfconf_set("xfce4-terminal", "/font-name", f"JetBrains Mono {size}")


def write_conky_colors(preset):
    c = preset.palette()
    lines = ["return {"]
    for key in ("bg", "primary", "secondary", "grid", "alert", "text", "dim", "surface", "border"):
        lines.append(f"  {key} = '{bare(c[key])}',")
    lines.append(f"  corners = '{preset.corners}',")
    lines.append("}")
    (config_dir() / "conky-colors.lua").write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_fonts(settings):
    size = settings.get_int("TEXT_SIZE", 11)
    xfconf_set("xsettings", "/Gtk/FontName", f"Share Tech Mono {size}")
    xfconf_set("xsettings", "/Gtk/MonospaceFontName", f"JetBrains Mono {max(size - 1, 8)}")
    xfconf_set("xfwm4", "/general/title_font", f"Share Tech Mono Bold {size}")


def apply_motion(settings):
    reduce = settings.get_bool("REDUCE_MOTION")
    xfconf_set("xsettings", "/Gtk/EnableAnimations", not reduce)
    xfconf_set("xfwm4", "/general/box_move", reduce)


def apply_onboard(preset):
    path = f"/usr/share/onboard/themes/{preset.theme_name}.theme"
    if Path(path).exists():
        run(["gsettings", "set", "org.onboard", "theme", path])


def apply(preset=None):
    preset = preset or active_preset()
    settings = Settings()
    name = preset.theme_name
    xfconf_set("xsettings", "/Net/ThemeName", name)
    xfconf_set("xsettings", "/Net/IconThemeName", name)
    xfconf_set("xfwm4", "/general/theme", name)
    xfconf_set("xfwm4", "/general/button_layout", "|HMC")
    apply_fonts(settings)
    apply_motion(settings)
    apply_terminal(preset, settings)
    set_wallpaper(wallpaper_path(preset, settings))
    write_conky_colors(preset)
    apply_onboard(preset)
    if hud.running():
        hud.start()
    return True


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "apply"
    if command == "apply":
        apply()
    elif command == "fonts":
        apply_fonts(Settings())
    elif command == "wallpaper":
        preset = active_preset()
        set_wallpaper(wallpaper_path(preset, Settings()))
    else:
        print("usage: nexus-theme [apply|fonts|wallpaper]", file=sys.stderr)
        return 2
    return 0
