import colorsys
from dataclasses import dataclass, field

from nexus.common import PRESET_DIR, SYSTEM_PRESET_FILE, read_kv, read_text

DEFAULT_PRESET = "amber"


def hex_to_rgb(value):
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#" + "".join(f"{round(max(0.0, min(1.0, channel)) * 255):02X}" for channel in rgb)


def mix(color_a, color_b, amount):
    a = hex_to_rgb(color_a)
    b = hex_to_rgb(color_b)
    return rgb_to_hex(tuple(a[index] + (b[index] - a[index]) * amount for index in range(3)))


def hls(color):
    return colorsys.rgb_to_hls(*hex_to_rgb(color))


def from_hls(hue, lightness, saturation):
    return rgb_to_hex(colorsys.hls_to_rgb(hue % 1.0, max(0.0, min(1.0, lightness)), max(0.0, min(1.0, saturation))))


def with_lightness(color, lightness):
    hue, _, saturation = hls(color)
    return from_hls(hue, lightness, saturation)


def luminance(color):
    red, green, blue = hex_to_rgb(color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def rgba(color, alpha):
    red, green, blue = (round(channel * 255) for channel in hex_to_rgb(color))
    return f"rgba({red}, {green}, {blue}, {alpha})"


def floats(color):
    return tuple(round(channel, 4) for channel in hex_to_rgb(color))


def bare(color):
    return color.lstrip("#").upper()


def tint_keep_lightness(source, target):
    target_hue, _, target_saturation = hls(target)
    _, source_lightness, source_saturation = hls(source)
    saturation = target_saturation if source_saturation > 0.12 else target_saturation * 0.25
    return from_hls(target_hue, source_lightness, saturation)


@dataclass
class Preset:
    key: str
    name: str
    style: str
    order: int
    hidden: bool
    background: str
    primary: str
    secondary: str
    grid: str
    alert: str
    wallpaper: str
    sound_pack: str
    corners: str
    colors: dict = field(default_factory=dict)

    @property
    def theme_name(self):
        return "NEXUS-" + self.key.title()

    @property
    def radius(self):
        return 6 if self.corners == "rounded" else 0

    def palette(self):
        if self.colors:
            return self.colors
        bg = self.background
        primary = self.primary
        bright = with_lightness(primary, 0.9)
        text = mix(primary, bright, 0.55)
        colors = {
            "bg": bg,
            "primary": primary,
            "secondary": self.secondary,
            "grid": self.grid,
            "alert": self.alert,
            "text": text,
            "text_hi": bright,
            "dim": mix(text, bg, 0.45),
            "surface": mix(bg, primary, 0.06),
            "surface_hi": mix(bg, primary, 0.12),
            "hover": mix(bg, primary, 0.18),
            "selection": mix(bg, primary, 0.32),
            "border": mix(self.grid, primary, 0.35),
            "frame": mix(bg, primary, 0.22),
            "title_active": mix(bg, primary, 0.14),
            "title_inactive": mix(bg, self.grid, 0.6),
            "secondary_text": mix(self.secondary, bright, 0.35),
            "on_primary": bg,
        }
        self.colors = colors
        return colors


def load_preset(key):
    values = read_kv(PRESET_DIR / f"{key}.conf")
    if not values:
        if key != DEFAULT_PRESET:
            return load_preset(DEFAULT_PRESET)
        raise FileNotFoundError(f"Preset {key} not found in {PRESET_DIR}")
    return Preset(
        key=key,
        name=values.get("NAME", key.title()),
        style=values.get("STYLE", ""),
        order=int(values.get("ORDER", "50")),
        hidden=values.get("HIDDEN", "0") == "1",
        background=values["BACKGROUND"],
        primary=values["PRIMARY"],
        secondary=values["SECONDARY"],
        grid=values["GRID"],
        alert=values["ALERT"],
        wallpaper=values.get("WALLPAPER", "grid"),
        sound_pack=values.get("SOUND_PACK", "tactical"),
        corners=values.get("CORNERS", "sharp"),
    )


def list_presets(include_hidden=False):
    presets = []
    for path in sorted(PRESET_DIR.glob("*.conf")):
        preset = load_preset(path.stem)
        if include_hidden or not preset.hidden:
            presets.append(preset)
    return sorted(presets, key=lambda preset: preset.order)


def active_key():
    key = read_text(SYSTEM_PRESET_FILE, DEFAULT_PRESET) or DEFAULT_PRESET
    if not (PRESET_DIR / f"{key}.conf").exists():
        return DEFAULT_PRESET
    return key


def active_preset():
    return load_preset(active_key())
