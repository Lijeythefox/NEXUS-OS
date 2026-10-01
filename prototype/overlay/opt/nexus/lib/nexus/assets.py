import argparse
import math
import os
import random
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape

from nexus.presets import (
    floats,
    hls,
    list_presets,
    load_preset,
    mix,
    tint_keep_lightness,
    with_lightness,
    from_hls,
)

FONT = "'Share Tech Mono', 'DejaVu Sans Mono', monospace"
WALL_W, WALL_H = 1536, 900
TITLE_HEIGHT = 32
BORDER = 3
GLYPH = 12

GTK_CSS = Template("""@import url("resource:///org/gtk/libgtk/theme/Adwaita/gtk-contained-dark.css");

@define-color theme_bg_color $bg;
@define-color theme_fg_color $text;
@define-color theme_base_color $surface;
@define-color theme_text_color $text;
@define-color theme_selected_bg_color $selection;
@define-color theme_selected_fg_color $text_hi;
@define-color insensitive_bg_color $bg;
@define-color insensitive_fg_color $dim;
@define-color insensitive_base_color $surface;
@define-color theme_unfocused_bg_color $bg;
@define-color theme_unfocused_fg_color $text;
@define-color theme_unfocused_base_color $surface;
@define-color theme_unfocused_text_color $text;
@define-color theme_unfocused_selected_bg_color $selection;
@define-color theme_unfocused_selected_fg_color $text_hi;
@define-color borders $border;
@define-color unfocused_borders $grid;
@define-color warning_color $alert;
@define-color error_color $alert;
@define-color success_color $secondary;
@define-color nexus_bg $bg;
@define-color nexus_primary $primary;
@define-color nexus_secondary $secondary;
@define-color nexus_grid $grid;
@define-color nexus_alert $alert;
@define-color nexus_text $text;
@define-color nexus_dim $dim;
@define-color nexus_surface $surface;

* {
  border-radius: 0;
  -gtk-outline-radius: 0;
  outline-color: alpha($primary, 0.5);
}

window, .background, dialog, messagedialog, messagedialog .dialog-action-box {
  background-color: $bg;
  color: $text;
}

label.dim-label, .dim-label {
  color: $dim;
}

headerbar, .titlebar, headerbar:backdrop, .titlebar:backdrop {
  background-image: none;
  background-color: $title_active;
  border-bottom: 2px solid $primary;
  box-shadow: none;
  color: $text_hi;
  min-height: 36px;
}

button {
  background-image: none;
  background-color: $surface_hi;
  border: 1px solid $border;
  color: $text;
  box-shadow: none;
  text-shadow: none;
  -gtk-icon-shadow: none;
  min-height: 30px;
  min-width: 30px;
}

button:hover {
  background-color: $hover;
  border-color: $primary;
  color: $text_hi;
}

button:active, button:checked {
  background-color: $primary;
  border-color: $primary;
  color: $on_primary;
}

button:disabled {
  background-color: $bg;
  border-color: $grid;
  color: $dim;
}

button.flat {
  background-color: transparent;
  border-color: transparent;
}

button.flat:hover {
  background-color: $hover;
  border-color: $border;
}

button.suggested-action {
  background-color: $primary;
  border-color: $primary;
  color: $on_primary;
}

button.suggested-action:hover {
  background-color: $text_hi;
}

button.destructive-action {
  background-color: $alert;
  border-color: $alert;
  color: $on_primary;
}

entry, spinbutton:not(.vertical) {
  background-image: none;
  background-color: $surface;
  border: 1px solid $border;
  color: $text;
  caret-color: $primary;
  box-shadow: none;
  min-height: 30px;
}

entry:focus, spinbutton:focus {
  border-color: $primary;
  box-shadow: inset 0 -2px $primary;
}

textview text, .view, iconview, treeview.view, list, row {
  background-color: $surface;
  color: $text;
}

row:hover, treeview.view:hover {
  background-color: $hover;
}

*:selected, *:selected:focus, .view:selected, treeview.view:selected, row:selected,
iconview:selected, entry selection, textview text selection, label selection, flowboxchild:selected {
  background-color: $selection;
  color: $text_hi;
}

menu, .menu, .context-menu, popover, popover.background, menubar {
  background-color: $surface;
  border: 1px solid $border;
  color: $text;
  box-shadow: none;
}

menu menuitem, .menu menuitem {
  min-height: 30px;
  padding: 4px 12px;
}

menu menuitem:hover, .menu menuitem:hover, menubar > menuitem:hover, popover modelbutton:hover {
  background-color: $selection;
  color: $text_hi;
}

notebook > header {
  background-color: $bg;
  border-color: $border;
}

notebook > header tab {
  min-height: 30px;
  padding: 4px 12px;
  color: $dim;
}

notebook > header tab:checked {
  color: $primary;
  box-shadow: inset 0 -2px $primary;
}

notebook > stack:not(:only-child) {
  background-color: $bg;
}

scrollbar {
  background-color: $bg;
  border-color: $grid;
}

scrollbar slider {
  background-color: $border;
  min-width: 8px;
  min-height: 8px;
  border: 2px solid transparent;
}

scrollbar slider:hover, scrollbar slider:active {
  background-color: $primary;
}

scale trough, progressbar trough, levelbar trough {
  background-image: none;
  background-color: $grid;
  border: none;
  min-height: 6px;
  min-width: 6px;
}

scale highlight, progressbar progress, levelbar block.filled {
  background-image: none;
  background-color: $primary;
  border: none;
}

scale slider {
  background-image: none;
  background-color: $primary;
  border: 2px solid $bg;
  box-shadow: none;
  min-width: 20px;
  min-height: 20px;
}

switch {
  background-image: none;
  background-color: $grid;
  border: 1px solid $border;
  color: $dim;
  min-width: 48px;
  min-height: 26px;
}

switch:checked {
  background-color: $primary;
  border-color: $primary;
  color: $on_primary;
}

switch slider {
  background-image: none;
  background-color: $text;
  border: none;
  box-shadow: none;
  min-width: 24px;
  min-height: 24px;
}

switch:checked slider {
  background-color: $bg;
}

check, radio {
  background-image: none;
  background-color: $surface;
  border: 1px solid $border;
  color: $on_primary;
  min-width: 18px;
  min-height: 18px;
}

check:checked, radio:checked, check:indeterminate {
  background-color: $primary;
  border-color: $primary;
}

radio {
  border-radius: 50%;
}

tooltip, tooltip.background {
  background-color: $surface;
  border: 1px solid $primary;
  color: $text;
}

tooltip * {
  color: $text;
}

separator {
  background-color: $grid;
  min-width: 1px;
  min-height: 1px;
}

frame > border, .frame {
  border-color: $border;
}

infobar {
  background-color: $surface_hi;
  border-bottom: 1px solid $primary;
}

.sidebar, placessidebar, placessidebar list, stacksidebar list {
  background-color: $surface;
  border-color: $grid;
}

placessidebar row:selected, stacksidebar row:selected {
  box-shadow: inset 3px 0 $primary;
}

treeview.view header button {
  background-color: $surface_hi;
  border-color: $grid;
  color: $dim;
}

calendar {
  color: $text;
  border-color: $border;
}

calendar:selected {
  background-color: $primary;
  color: $on_primary;
}

.xfce4-panel.background, .xfce4-panel {
  background-image: none;
  background-color: $bg;
  color: $text;
  border-top: 1px solid $border;
}

.xfce4-panel button {
  background-color: transparent;
  border: 1px solid transparent;
  color: $text;
  padding: 2px 6px;
  min-height: 0;
  min-width: 0;
}

.xfce4-panel button:hover {
  background-color: $hover;
  border-color: $border;
}

.xfce4-panel button:checked, .xfce4-panel button:active {
  background-color: $selection;
  border-color: transparent;
  box-shadow: inset 0 -2px $primary;
  color: $text_hi;
}

#whiskermenu-window {
  background-color: $bg;
  border: 1px solid $primary;
}

#whiskermenu-window entry {
  min-height: 36px;
}

#whiskermenu-window treeview.view, #whiskermenu-window iconview {
  background-color: $bg;
}

#XfceNotifyWindow {
  background-color: $surface;
  border: 1px solid $primary;
  color: $text;
}

#XfceNotifyWindow label#summary {
  color: $primary;
  font-weight: bold;
}

#XfceNotifyWindow progressbar progress {
  background-color: $primary;
}

#login_window, #restart_dialog, #shutdown_dialog {
  background-color: alpha($bg, 0.94);
  border: 1px solid $primary;
  box-shadow: 0 0 24px alpha($primary, 0.35);
  padding: 18px;
}

#login_window entry {
  background-color: $bg;
  border: 1px solid $border;
  color: $primary;
  min-height: 38px;
}

#login_window entry:focus {
  border-color: $primary;
}

#login_window button {
  min-height: 36px;
}

#panel_window {
  background-color: alpha($bg, 0.85);
  border-bottom: 1px solid $grid;
  color: $text;
}

#panel_window menubar, #panel_window menubar > menuitem {
  background-color: transparent;
  border: none;
  color: $text;
}

#content_frame {
  background-color: transparent;
  border-bottom: 1px solid $grid;
  padding-bottom: 14px;
}

#greeter_infobar {
  background-color: $surface;
  border-bottom: 1px solid $alert;
}
""")

PAPIRUS_COLOURS = (
    "adwaita|black|blue|bluegrey|breeze|brown|carmine|cyan|darkcyan|deeporange|green|grey|indigo|"
    "magenta|nordic|orange|palebrown|paleorange|pink|red|teal|violet|white|yaru|yellow"
)
SKIP_PLACE = re.compile(rf"^(folder|user)-({PAPIRUS_COLOURS})(-|\.)")
COLOUR_RE = re.compile(r"(?<![\w&])#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])")


def write(path, content, mode="w"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if "b" in mode:
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def render_png(svg, out, width, height):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(out)],
        input=svg.encode("utf-8"),
        check=True,
    )


def gtk_theme(preset, root):
    colors = preset.palette()
    base = Path(root) / "usr/share/themes" / preset.theme_name
    write(base / "gtk-3.0/gtk.css", GTK_CSS.substitute(colors))
    write(
        base / "index.theme",
        "\n".join([
            "[Desktop Entry]",
            "Type=X-GNOME-Metatheme",
            f"Name={preset.theme_name}",
            f"Comment=NEXUS OS {preset.name} preset",
            "Encoding=UTF-8",
            "",
            "[X-GNOME-Metatheme]",
            f"GtkTheme={preset.theme_name}",
            f"MetacityTheme={preset.theme_name}",
            f"IconTheme={preset.theme_name}",
            "ButtonLayout=:minimize,maximize,close",
            "",
        ]),
    )
    xfwm_theme(preset, base / "xfwm4")


def xpm(width, height, pixels, colors):
    keys = list(colors)
    lines = ["/* XPM */", "static char * nexus_xpm[] = {", f'"{width} {height} {len(keys)} 1",']
    lines += [f'"{key} c {colors[key]}",' for key in keys]
    lines += [f'"{"".join(row)}",' for row in pixels]
    lines[-1] = lines[-1][:-1]
    lines.append("};")
    return "\n".join(lines) + "\n"


def title_column(height):
    column = ["t"] * height
    column[0] = "b"
    column[-1] = "a"
    column[-2] = "a"
    return column


def glyph_pixels(name):
    pixels = set()
    last = GLYPH - 1
    if name == "close":
        for index in range(GLYPH):
            pixels |= {(index, index), (last - index, index)}
            pixels |= {(min(index + 1, last), index), (max(last - index - 1, 0), index)}
    elif name == "maximize":
        for index in range(GLYPH):
            pixels |= {(index, 0), (index, 1), (index, last), (0, index), (last, index)}
    elif name == "maximize-toggled":
        for index in range(3, GLYPH):
            pixels |= {(index, 0), (index, 1), (index, 8), (3, index - 3), (last, index - 3)}
        for index in range(0, 9):
            pixels |= {(index, 3), (index, 4), (index, last), (0, index + 3), (8, index + 3)}
        pixels -= {(x, y) for x in range(1, 8) for y in range(5, last)}
    elif name == "hide":
        pixels |= {(x, y) for x in range(GLYPH) for y in (last - 1, last)}
    elif name == "menu":
        pixels |= {(x, y) for x in range(GLYPH) for y in (1, 2, 5, 6, 9, 10)}
    elif name in ("shade", "shade-toggled"):
        for index in range(6):
            for offset in (0, 1):
                y = 3 + index + offset
                if name == "shade-toggled":
                    y = last - y
                pixels |= {(5 - index, y), (6 + index, y)}
    elif name == "stick":
        pixels |= {(x, y) for x in range(4, 8) for y in range(4, 8)}
    elif name == "stick-toggled":
        pixels |= {(x, y) for x in range(2, 10) for y in range(2, 10)}
    return pixels


def xfwm_theme(preset, base):
    c = preset.palette()
    states = {
        "active": {"b": c["border"], "t": c["title_active"], "a": c["primary"], "f": c["frame"]},
        "inactive": {"b": c["grid"], "t": c["title_inactive"], "a": c["grid"], "f": c["title_inactive"]},
    }
    for state, colors in states.items():
        column = title_column(TITLE_HEIGHT)
        for index in range(1, 6):
            rows = [[column[y]] * 2 for y in range(TITLE_HEIGHT)]
            write(base / f"title-{index}-{state}.xpm", xpm(2, TITLE_HEIGHT, rows, colors))
        top_left = [["b"] + [column[y]] * (BORDER - 1) for y in range(TITLE_HEIGHT)]
        write(base / f"top-left-{state}.xpm", xpm(BORDER, TITLE_HEIGHT, top_left, colors))
        write(base / f"top-right-{state}.xpm", xpm(BORDER, TITLE_HEIGHT, [list(reversed(row)) for row in top_left], colors))
        write(base / f"left-{state}.xpm", xpm(BORDER, 1, [["b"] + ["f"] * (BORDER - 1)], colors))
        write(base / f"right-{state}.xpm", xpm(BORDER, 1, [["f"] * (BORDER - 1) + ["b"]], colors))
        bottom = [["f"] for _ in range(BORDER - 1)] + [["b"]]
        write(base / f"bottom-{state}.xpm", xpm(1, BORDER, bottom, colors))
        corner = [["b" if x == 0 or y == BORDER - 1 else "f" for x in range(BORDER)] for y in range(BORDER)]
        write(base / f"bottom-left-{state}.xpm", xpm(BORDER, BORDER, corner, colors))
        write(base / f"bottom-right-{state}.xpm", xpm(BORDER, BORDER, [list(reversed(row)) for row in corner], colors))

    glyphs = ["close", "maximize", "maximize-toggled", "hide", "menu", "shade", "shade-toggled", "stick", "stick-toggled"]
    offset_x = (TITLE_HEIGHT - GLYPH) // 2
    offset_y = (TITLE_HEIGHT - GLYPH) // 2
    for glyph in glyphs:
        shape = glyph_pixels(glyph)
        for state in ("active", "inactive", "prelight", "pressed"):
            frame = states["inactive" if state == "inactive" else "active"]
            fill = frame["t"]
            ink = c["primary"]
            if state == "inactive":
                ink = c["dim"]
            elif state == "prelight":
                fill = c["alert"] if glyph == "close" else c["hover"]
                ink = c["bg"] if glyph == "close" else c["text_hi"]
            elif state == "pressed":
                fill = c["primary"]
                ink = c["bg"]
            colors = {"b": frame["b"], "t": fill, "a": frame["a"], "g": ink}
            column = title_column(TITLE_HEIGHT)
            rows = [[column[y]] * TITLE_HEIGHT for y in range(TITLE_HEIGHT)]
            for x, y in shape:
                rows[offset_y + y][offset_x + x] = "g"
            write(base / f"{glyph}-{state}.xpm", xpm(TITLE_HEIGHT, TITLE_HEIGHT, rows, colors))

    write(
        base / "themerc",
        "\n".join([
            f"active_text_color={c['text_hi']}",
            f"inactive_text_color={c['dim']}",
            "button_offset=0",
            "button_spacing=0",
            "button_layout=|HMC",
            "title_alignment=left",
            "title_horizontal_offset=10",
            "title_vertical_offset_active=0",
            "title_vertical_offset_inactive=0",
            "full_width_title=true",
            "title_shadow_active=false",
            "title_shadow_inactive=false",
            "maximized_offset=0",
            "show_app_icon=false",
            "shadow_delta_height=0",
            "shadow_delta_width=0",
            "shadow_delta_x=0",
            "shadow_delta_y=0",
            "shadow_opacity=40",
            "",
        ]),
    )


def svg_doc(width, height, body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><defs>{defs}</defs>{body}</svg>'
    )


def glow_filter(name="glow", deviation=4):
    return (
        f'<filter id="{name}" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feGaussianBlur stdDeviation="{deviation}" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )


def vignette(c, width, height):
    defs = (
        '<radialGradient id="vignette" cx="50%" cy="50%" r="75%">'
        f'<stop offset="55%" stop-color="{c["bg"]}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="{c["bg"]}" stop-opacity="0.92"/></radialGradient>'
    )
    return defs, f'<rect width="{width}" height="{height}" fill="url(#vignette)"/>'


def grid_layer(c, width, height, minor=24, major=120, strength=1.0):
    minor_path = "".join(f"M{x + 0.5} 0V{height}" for x in range(0, width + 1, minor))
    minor_path += "".join(f"M0 {y + 0.5}H{width}" for y in range(0, height + 1, minor))
    major_path = "".join(f"M{x + 0.5} 0V{height}" for x in range(0, width + 1, major))
    major_path += "".join(f"M0 {y + 0.5}H{width}" for y in range(0, height + 1, major))
    return (
        f'<path d="{minor_path}" fill="none" stroke="{c["grid"]}" stroke-width="1" opacity="{0.6 * strength:.2f}"/>'
        f'<path d="{major_path}" fill="none" stroke="{c["border"]}" stroke-width="1" opacity="{0.55 * strength:.2f}"/>'
    )


def frame_marks(c, width, height, label):
    inset, length = 24, 46
    corners = [
        (inset, inset, 1, 1),
        (width - inset, inset, -1, 1),
        (inset, height - inset, 1, -1),
        (width - inset, height - inset, -1, -1),
    ]
    path = "".join(
        f"M{x} {y + dy * length}V{y}H{x + dx * length}" for x, y, dx, dy in corners
    )
    ticks = "".join(f"M{x} {inset + 10}v8" for x in range(inset + 60, width - inset - 40, 60))
    return (
        f'<path d="{path}" fill="none" stroke="{c["primary"]}" stroke-width="2" opacity="0.75"/>'
        f'<path d="{ticks}" fill="none" stroke="{c["primary"]}" stroke-width="1" opacity="0.4"/>'
        f'<text x="{inset + 14}" y="{inset + 42}" font-family="{FONT}" font-size="15" letter-spacing="3" '
        f'fill="{c["primary"]}" opacity="0.6">{escape(label)}</text>'
        f'<text x="{width - inset - 14}" y="{height - inset - 14}" text-anchor="end" font-family="{FONT}" '
        f'font-size="13" letter-spacing="2" fill="{c["secondary_text"]}" opacity="0.55">'
        f'GRID {width}x{height} // NEXUS OS</text>'
    )


def closed_path(points):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points) + "Z"


def style_topo(c, width, height, rng):
    body = []
    centers = [(width * 0.27, height * 0.4, 360), (width * 0.75, height * 0.68, 300), (width * 0.63, height * 0.16, 190)]
    for cx, cy, size in centers:
        phases = [rng.uniform(0, math.tau) for _ in range(3)]
        for ring in range(1, 11):
            radius = size * ring / 10
            points = []
            for step in range(96):
                angle = math.tau * step / 96
                wobble = 1 + 0.16 * math.sin(3 * angle + phases[0]) + 0.08 * math.sin(5 * angle + phases[1] + ring * 0.2)
                wobble += 0.04 * math.sin(9 * angle + phases[2])
                points.append((cx + radius * wobble * math.cos(angle), cy + radius * wobble * math.sin(angle) * 0.8))
            major = ring % 5 == 0
            body.append(
                f'<path d="{closed_path(points)}" fill="none" stroke="{c["primary"] if major else c["secondary"]}" '
                f'stroke-width="{1.5 if major else 1}" opacity="{0.6 if major else 0.45}"/>'
            )
        body.append(
            f'<path d="M{cx - 7} {cy}h14M{cx} {cy - 7}v14" stroke="{c["primary"]}" stroke-width="2"/>'
            f'<text x="{cx + 12}" y="{cy - 10}" font-family="{FONT}" font-size="14" fill="{c["primary"]}" '
            f'opacity="0.7">ELEV {rng.randint(180, 940)}</text>'
        )
    return "".join(body), ""


def style_radar(c, width, height, rng):
    cx, cy = width * 0.64, height * 0.5
    radius = min(width, height) * 0.42
    body = []
    for ring in range(1, 6):
        body.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius * ring / 5:.1f}" fill="none" stroke="{c["primary"]}" '
            f'stroke-width="1" opacity="0.4"/>'
        )
    for step in range(1, 6):
        body.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{radius * step / 6:.1f}" ry="{radius:.1f}" fill="none" '
            f'stroke="{c["secondary"]}" stroke-width="1" opacity="0.35"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{radius:.1f}" ry="{radius * step / 6:.1f}" fill="none" '
            f'stroke="{c["secondary"]}" stroke-width="1" opacity="0.35"/>'
        )
    ticks = []
    for degree in range(0, 360, 5):
        angle = math.radians(degree)
        inner = radius - (14 if degree % 30 == 0 else 6)
        ticks.append(
            f"M{cx + inner * math.cos(angle):.1f} {cy + inner * math.sin(angle):.1f}"
            f"L{cx + radius * math.cos(angle):.1f} {cy + radius * math.sin(angle):.1f}"
        )
        if degree % 30 == 0:
            body.append(
                f'<text x="{cx + (radius + 22) * math.cos(angle):.1f}" y="{cy + (radius + 22) * math.sin(angle) + 5:.1f}" '
                f'text-anchor="middle" font-family="{FONT}" font-size="13" fill="{c["primary"]}" opacity="0.6">'
                f'{(degree + 90) % 360:03d}</text>'
            )
    body.append(f'<path d="{"".join(ticks)}" stroke="{c["primary"]}" stroke-width="1" opacity="0.6"/>')
    body.append(
        f'<path d="M{cx - radius} {cy}H{cx + radius}M{cx} {cy - radius}V{cy + radius}" '
        f'stroke="{c["primary"]}" stroke-width="1" opacity="0.45"/>'
    )
    for _ in range(7):
        distance = rng.uniform(0.2, 0.9) * radius
        angle = rng.uniform(0, math.tau)
        body.append(
            f'<circle cx="{cx + distance * math.cos(angle):.1f}" cy="{cy + distance * math.sin(angle):.1f}" r="4" '
            f'fill="{c["primary"]}" filter="url(#glow)"/>'
        )
    return "".join(body), glow_filter()


def style_scope(c, width, height, rng):
    cx, cy = width * 0.5, height * 0.55
    radius = height * 0.42
    body = []
    for ring in range(1, 5):
        body.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius * ring / 4:.1f}" fill="none" stroke="{c["primary"]}" '
            f'stroke-width="{2 if ring == 4 else 1}" opacity="0.45"/>'
            f'<text x="{cx + 6}" y="{cy - radius * ring / 4 + 16:.1f}" font-family="{FONT}" font-size="12" '
            f'fill="{c["primary"]}" opacity="0.6">{ring * 25}KM</text>'
        )
    start, end = math.radians(-70), math.radians(-25)
    sweep = (
        f"M{cx} {cy}L{cx + radius * math.cos(start):.1f} {cy + radius * math.sin(start):.1f}"
        f"A{radius:.1f} {radius:.1f} 0 0 1 {cx + radius * math.cos(end):.1f} {cy + radius * math.sin(end):.1f}Z"
    )
    defs = glow_filter() + (
        '<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{c["primary"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{c["primary"]}" stop-opacity="0.45"/></linearGradient>'
    )
    body.append(f'<path d="{sweep}" fill="url(#sweep)"/>')
    body.append(
        f'<path d="M{cx} {cy}L{cx + radius * math.cos(end):.1f} {cy + radius * math.sin(end):.1f}" '
        f'stroke="{c["primary"]}" stroke-width="2" filter="url(#glow)"/>'
    )
    body.append(
        f'<path d="M{cx - radius} {cy}H{cx + radius}M{cx} {cy - radius}V{cy + radius}" '
        f'stroke="{c["secondary"]}" stroke-width="1" opacity="0.6"/>'
    )
    for _ in range(5):
        distance = rng.uniform(0.25, 0.92) * radius
        angle = rng.uniform(0, math.tau)
        x, y = cx + distance * math.cos(angle), cy + distance * math.sin(angle)
        body.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{c["alert"]}" filter="url(#glow)"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="none" stroke="{c["alert"]}" opacity="0.5"/>'
        )
    stripes = "".join(f"M{x} 0l24 18" for x in range(0, width + 40, 40))
    body.append(f'<path d="{stripes}" stroke="{c["secondary"]}" stroke-width="6" opacity="0.35"/>')
    return "".join(body), defs


def style_rings(c, width, height, rng):
    cx, cy = width * 0.5, height * 0.5
    defs = glow_filter() + (
        '<radialGradient id="core" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{c["secondary"]}" stop-opacity="0.35"/>'
        f'<stop offset="1" stop-color="{c["bg"]}" stop-opacity="0"/></radialGradient>'
    )
    body = [f'<circle cx="{cx}" cy="{cy}" r="{height * 0.5:.1f}" fill="url(#core)"/>']
    for index, radius in enumerate((70, 120, 180, 240, 305, 370)):
        dash = rng.choice(["none", "4 8", "60 20", "120 30 10 30", "2 6", "200 60"])
        rotation = rng.randint(0, 359)
        color = c["primary"] if index % 2 == 0 else c["secondary"]
        body.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" '
            f'stroke-width="{3 if index % 2 == 0 else 2}" stroke-dasharray="{dash}" opacity="0.7" '
            f'transform="rotate({rotation} {cx} {cy})" filter="url(#glow)"/>'
        )
    hexagon = [
        (cx + 46 * math.cos(math.radians(60 * step + 30)), cy + 46 * math.sin(math.radians(60 * step + 30)))
        for step in range(6)
    ]
    body.append(
        f'<path d="{closed_path(hexagon)}" fill="none" stroke="{c["primary"]}" stroke-width="2" filter="url(#glow)"/>'
    )
    return "".join(body), defs


def style_synth(c, width, height, rng):
    horizon = height * 0.58
    sky = mix(c["bg"], c["secondary"], 0.45)
    defs = glow_filter() + (
        f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{c["bg"]}"/><stop offset="1" stop-color="{sky}"/></linearGradient>'
        f'<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{c["primary"]}"/><stop offset="1" stop-color="{c["secondary"]}"/></linearGradient>'
        f'<clipPath id="sky-clip"><rect width="{width}" height="{horizon:.1f}"/></clipPath>'
        f'<mask id="sun-mask"><rect width="{width}" height="{height}" fill="white"/>'
    )
    sun_cy = horizon - 30
    for index in range(7):
        stripe_y = sun_cy - 10 + index * 22
        defs += f'<rect x="0" y="{stripe_y:.1f}" width="{width}" height="{2 + index * 2}" fill="black"/>'
    defs += "</mask>"
    body = [f'<rect width="{width}" height="{horizon:.1f}" fill="url(#sky)"/>']
    for _ in range(70):
        body.append(
            f'<circle cx="{rng.uniform(0, width):.1f}" cy="{rng.uniform(0, horizon - 60):.1f}" '
            f'r="{rng.uniform(0.6, 1.8):.1f}" fill="{c["primary"]}" opacity="{rng.uniform(0.2, 0.7):.2f}"/>'
        )
    body.append(
        f'<g clip-path="url(#sky-clip)"><circle cx="{width / 2}" cy="{sun_cy:.1f}" r="170" fill="url(#sun)" '
        f'mask="url(#sun-mask)" filter="url(#glow)"/></g>'
    )
    peaks = [(0, horizon)]
    x = 0
    while x < width:
        x += rng.uniform(40, 110)
        peaks.append((x, horizon - rng.uniform(10, 120) * (0.4 if abs(x - width / 2) < 220 else 1)))
    peaks.append((width, horizon))
    mountain = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in peaks) + "Z"
    body.append(f'<path d="{mountain}" fill="{c["bg"]}" stroke="{c["secondary"]}" stroke-width="1.5" opacity="0.9"/>')
    body.append(f'<rect y="{horizon:.1f}" width="{width}" height="{height - horizon:.1f}" fill="{c["bg"]}"/>')
    lines = []
    vanish_x = width / 2
    for index in range(-24, 25):
        lines.append(f"M{vanish_x} {horizon:.1f}L{vanish_x + index * 120:.1f} {height}")
    for index in range(1, 15):
        y = horizon + (height - horizon) * (index / 14) ** 2.2
        lines.append(f"M0 {y:.1f}H{width}")
    body.append(
        f'<path d="{"".join(lines)}" stroke="{c["primary"]}" stroke-width="1.5" opacity="0.65" filter="url(#glow)"/>'
    )
    body.append(f'<path d="M0 {horizon:.1f}H{width}" stroke="{c["primary"]}" stroke-width="2" filter="url(#glow)"/>')
    return "".join(body), defs


STYLES = {
    "topo": style_topo,
    "radar": style_radar,
    "scope": style_scope,
    "rings": style_rings,
    "synth": style_synth,
}


def wallpaper_svg(preset, width=WALL_W, height=WALL_H, overlay=""):
    c = preset.palette()
    rng = random.Random(preset.key)
    style = STYLES.get(preset.wallpaper)
    body = [f'<rect width="{width}" height="{height}" fill="{c["bg"]}"/>']
    defs = ""
    if preset.wallpaper != "synth":
        body.append(grid_layer(c, width, height))
    if style:
        art, extra = style(c, width, height, rng)
        body.append(art)
        defs += extra
    vignette_defs, vignette_rect = vignette(c, width, height)
    defs += vignette_defs
    if "id=\"glow\"" not in defs:
        defs += glow_filter()
    body.append(vignette_rect)
    body.append(frame_marks(c, width, height, f"NEXUS OS // {preset.name.upper()}"))
    body.append(overlay)
    return svg_doc(width, height, "".join(body), defs)


def login_svg(preset, sign, width=WALL_W, height=WALL_H):
    c = preset.palette()
    sign = escape(sign.upper())
    header_y = height * 0.2
    overlay = (
        f'<rect width="{width}" height="{height}" fill="{c["bg"]}" opacity="0.35"/>'
        f'<text x="{width / 2}" y="{header_y:.1f}" text-anchor="middle" font-family="{FONT}" font-size="72" '
        f'letter-spacing="12" fill="{c["primary"]}" filter="url(#glow)">{sign}</text>'
        f'<path d="M{width / 2 - 260} {header_y + 26:.1f}H{width / 2 + 260}" stroke="{c["primary"]}" '
        f'stroke-width="2" opacity="0.8"/>'
        f'<text x="{width / 2}" y="{header_y + 60:.1f}" text-anchor="middle" font-family="{FONT}" font-size="20" '
        f'letter-spacing="8" fill="{c["secondary_text"]}">SECURE ACCESS TERMINAL</text>'
        f'<text x="{width / 2}" y="{height - 40}" text-anchor="middle" font-family="{FONT}" font-size="14" '
        f'letter-spacing="4" fill="{c["dim"]}">AUTHORISED USE ONLY // NEXUS OS</text>'
    )
    return wallpaper_svg(preset, width, height, overlay)


def render_wallpaper(preset, root):
    render_png(wallpaper_svg(preset), Path(root) / f"usr/share/nexus/wallpapers/{preset.key}.png", WALL_W, WALL_H)


def render_login(preset, sign, out):
    render_png(login_svg(preset, sign), out, WALL_W, WALL_H)


PLYMOUTH_SCRIPT = Template("""W = Window.GetWidth();
H = Window.GetHeight();
Window.SetBackgroundTopColor($bg_r, $bg_g, $bg_b);
Window.SetBackgroundBottomColor($bg_r, $bg_g, $bg_b);

background_image = Image("bg.png");
background = Sprite(background_image.Scale(W, H));
background.SetZ(-100);

sweep_image = Image("sweep.png");
sweep = Sprite(sweep_image.Scale(W, sweep_image.GetHeight()));
sweep.SetZ(-50);

callsign_image = Image("callsign.png");
callsign = Sprite(callsign_image);
callsign.SetX(W / 2 - callsign_image.GetWidth() / 2);
callsign.SetY(H * 0.36 - callsign_image.GetHeight() / 2);
callsign.SetZ(10);
callsign.SetOpacity(0);

online_image = Image("online.png");
online = Sprite(online_image);
online.SetX(W / 2 - online_image.GetWidth() / 2);
online.SetY(H * 0.56);
online.SetZ(10);
online.SetOpacity(0);

frame_image = Image("bar-frame.png");
frame = Sprite(frame_image);
frame_x = W / 2 - frame_image.GetWidth() / 2;
frame_y = H * 0.56 + online_image.GetHeight() + 12;
frame.SetPosition(frame_x, frame_y, 10);
frame.SetOpacity(0);

fill_image = Image("bar-fill.png");
fill = Sprite();
fill.SetPosition(frame_x + 4, frame_y + 4, 11);
fill_width_max = frame_image.GetWidth() - 8;
fill_height = frame_image.GetHeight() - 8;

ticks = 0;

fun refresh_callback() {
  ticks = ticks + 1;
  sweep.SetY(Math.Int(ticks * 5) % (H + 60) - 60);
  fade = ticks / 60;
  if (fade > 1) {
    fade = 1;
  }
  callsign.SetOpacity(fade);
  late = (ticks - 30) / 40;
  if (late < 0) {
    late = 0;
  }
  if (late > 1) {
    late = 1;
  }
  online.SetOpacity(late);
  frame.SetOpacity(late);
  fill.SetOpacity(late);
}
Plymouth.SetRefreshFunction(refresh_callback);

fun progress_callback(duration, progress) {
  width = Math.Int(fill_width_max * progress);
  if (width < 1) {
    width = 1;
  }
  fill.SetImage(fill_image.Scale(width, fill_height));
}
Plymouth.SetBootProgressFunction(progress_callback);

message_sprite = Sprite();
message_sprite.SetPosition(24, H - 48, 20);

fun message_callback(text) {
  message_sprite.SetImage(Image.Text(text, $text_r, $text_g, $text_b));
}
Plymouth.SetMessageFunction(message_callback);

prompt_sprite = Sprite();
bullets_sprite = Sprite();

fun display_password_callback(prompt, bullets) {
  prompt_sprite.SetImage(Image.Text(prompt, $text_r, $text_g, $text_b));
  prompt_sprite.SetPosition(W / 2 - 160, H * 0.8, 30);
  prompt_sprite.SetOpacity(1);
  stars = "";
  count = 0;
  while (count < bullets) {
    stars = stars + "*";
    count = count + 1;
  }
  bullets_sprite.SetImage(Image.Text(stars + "_", $pri_r, $pri_g, $pri_b));
  bullets_sprite.SetPosition(W / 2 - 160, H * 0.8 + 28, 30);
  bullets_sprite.SetOpacity(1);
}
Plymouth.SetDisplayPasswordFunction(display_password_callback);

fun display_normal_callback() {
  prompt_sprite.SetOpacity(0);
  bullets_sprite.SetOpacity(0);
}
Plymouth.SetDisplayNormalFunction(display_normal_callback);
""")


def text_png_svg(c, text, size, width, height, color_key="primary", spacing=6):
    return svg_doc(
        width,
        height,
        f'<text x="{width / 2}" y="{height / 2 + size * 0.35:.1f}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="{size}" letter-spacing="{spacing}" fill="{c[color_key]}" filter="url(#glow)">'
        f"{escape(text)}</text>",
        glow_filter(deviation=3),
    )


def plymouth_theme(preset, sign, root):
    c = preset.palette()
    name = f"nexus-{preset.key}"
    base = Path(root) / "usr/share/plymouth/themes" / name
    width, height = 1024, 600
    vignette_defs, vignette_rect = vignette(c, width, height)
    render_png(
        svg_doc(width, height, f'<rect width="{width}" height="{height}" fill="{c["bg"]}"/>'
                + grid_layer(c, width, height, strength=0.8) + vignette_rect, vignette_defs),
        base / "bg.png", width, height,
    )
    sweep_defs = (
        '<linearGradient id="band" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{c["primary"]}" stop-opacity="0"/>'
        f'<stop offset="0.9" stop-color="{c["primary"]}" stop-opacity="0.22"/>'
        f'<stop offset="1" stop-color="{c["primary"]}" stop-opacity="0.8"/></linearGradient>'
    )
    render_png(svg_doc(width, 60, f'<rect width="{width}" height="60" fill="url(#band)"/>', sweep_defs), base / "sweep.png", width, 60)
    sign = sign.upper()
    sign_width = max(240, len(sign) * 46 + 120)
    render_png(text_png_svg(c, sign, 64, sign_width, 110, spacing=10), base / "callsign.png", sign_width, 110)
    render_png(text_png_svg(c, "SYSTEM ONLINE", 24, 460, 44, "secondary_text"), base / "online.png", 460, 44)
    bar_ticks = "".join(f"M{x} 22v4" for x in range(10, 420, 41))
    render_png(
        svg_doc(420, 28, f'<rect x="1" y="1" width="418" height="18" fill="{c["bg"]}" stroke="{c["primary"]}" stroke-width="2"/>'
                f'<path d="{bar_ticks}" stroke="{c["primary"]}" stroke-width="1" opacity="0.6"/>'),
        base / "bar-frame.png", 420, 28,
    )
    render_png(svg_doc(16, 12, f'<rect width="16" height="12" fill="{c["primary"]}"/>'), base / "bar-fill.png", 16, 12)
    bg_r, bg_g, bg_b = floats(c["bg"])
    text_r, text_g, text_b = floats(c["text"])
    pri_r, pri_g, pri_b = floats(c["primary"])
    write(base / "nexus.script", PLYMOUTH_SCRIPT.substitute(
        bg_r=bg_r, bg_g=bg_g, bg_b=bg_b, text_r=text_r, text_g=text_g, text_b=text_b,
        pri_r=pri_r, pri_g=pri_g, pri_b=pri_b,
    ))
    write(
        base / f"{name}.plymouth",
        "\n".join([
            "[Plymouth Theme]",
            f"Name=NEXUS {preset.name}",
            "Description=NEXUS OS grid sweep boot animation",
            "ModuleName=script",
            "",
            "[script]",
            f"ImageDir=/usr/share/plymouth/themes/{name}",
            f"ScriptFile=/usr/share/plymouth/themes/{name}/nexus.script",
            "",
        ]),
    )


def recolour(text, mapper):
    return COLOUR_RE.sub(lambda match: mapper("#" + match.group(1)), text)


def panel_mapper(c):
    def mapper(color):
        hue, lightness, saturation = hls(color)
        if saturation > 0.5 and (hue < 0.06 or hue > 0.94):
            return c["alert"]
        return c["primary"] if lightness >= 0.45 else mix(c["bg"], c["primary"], 0.55)
    return mapper


APP_ICONS = {
    "nexus-settings": lambda c: (
        f'<circle cx="32" cy="32" r="11" fill="none" stroke="{c["primary"]}" stroke-width="4"/>'
        + "".join(
            f'<rect x="29" y="11" width="6" height="9" fill="{c["primary"]}" transform="rotate({angle} 32 32)"/>'
            for angle in range(0, 360, 45)
        )
        + f'<circle cx="32" cy="32" r="4" fill="{c["secondary"]}"/>'
    ),
    "nexus-quick-settings": lambda c: (
        f'<rect x="14" y="14" width="16" height="16" fill="{c["primary"]}"/>'
        f'<rect x="34" y="14" width="16" height="16" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<rect x="14" y="34" width="16" height="16" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<rect x="34" y="34" width="16" height="16" fill="{c["secondary"]}"/>'
    ),
    "nexus-hud": lambda c: (
        f'<path d="M32 12L49 22V42L32 52L15 42V22Z" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<path d="M32 20V44M20 32H44" stroke="{c["secondary"]}" stroke-width="2"/>'
        f'<circle cx="32" cy="32" r="5" fill="none" stroke="{c["primary"]}" stroke-width="2"/>'
    ),
    "nexus-keyboard": lambda c: (
        f'<rect x="10" y="20" width="44" height="26" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        + "".join(
            f'<rect x="{15 + col * 7}" y="{25 + row * 7}" width="4" height="4" fill="{c["primary"]}"/>'
            for row in range(2) for col in range(5)
        )
        + f'<rect x="20" y="39" width="24" height="3" fill="{c["secondary"]}"/>'
    ),
    "nexus-gamepad": lambda c: (
        f'<path d="M14 24H50Q56 24 56 32L54 44Q52 50 46 46L40 40H24L18 46Q12 50 10 44L8 32Q8 24 14 24Z" '
        f'fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<path d="M20 28V36M16 32H24" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<circle cx="42" cy="30" r="2.5" fill="{c["secondary"]}"/><circle cx="47" cy="35" r="2.5" fill="{c["primary"]}"/>'
    ),
    "nexus-mousemode": lambda c: (
        f'<path d="M14 30H44Q50 30 50 37L48 46Q46 51 41 48L36 43H22L17 48Q12 51 10 46L8 37Q8 30 14 30Z" '
        f'fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<path d="M38 8L38 26L42 22L46 30L49 28L45 21L51 21Z" fill="{c["secondary"]}"/>'
    ),
    "nexus-ai": lambda c: (
        f'<rect x="18" y="18" width="28" height="28" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        + "".join(f'<path d="M{x} 10V18M{x} 46V54" stroke="{c["primary"]}" stroke-width="2"/>' for x in (24, 32, 40))
        + "".join(f'<path d="M10 {y}H18M46 {y}H54" stroke="{c["primary"]}" stroke-width="2"/>' for y in (24, 32, 40))
        + f'<circle cx="27" cy="29" r="3" fill="{c["secondary"]}"/><circle cx="37" cy="35" r="3" fill="{c["secondary"]}"/>'
        f'<path d="M27 29L37 35" stroke="{c["secondary"]}" stroke-width="2"/>'
    ),
    "nexus-games": lambda c: (
        f'<rect x="12" y="38" width="40" height="14" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<path d="M26 38V22" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<circle cx="26" cy="18" r="6" fill="{c["secondary"]}"/>'
        f'<circle cx="40" cy="45" r="3" fill="{c["primary"]}"/><circle cx="46" cy="45" r="3" fill="{c["alert"]}"/>'
    ),
    "nexus-minecraft": lambda c: (
        f'<path d="M32 10L52 21V43L32 54L12 43V21Z" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<path d="M12 21L32 32L52 21M32 32V54" fill="none" stroke="{c["primary"]}" stroke-width="2"/>'
        f'<path d="M32 10L52 21L32 32L12 21Z" fill="{c["secondary"]}" opacity="0.7"/>'
    ),
    "nexus-start": lambda c: (
        f'<path d="M32 8L56 32L32 56L8 32Z" fill="none" stroke="{c["primary"]}" stroke-width="3"/>'
        f'<circle cx="32" cy="32" r="9" fill="none" stroke="{c["primary"]}" stroke-width="2"/>'
        f'<path d="M32 18V26M32 38V46M18 32H26M38 32H46" stroke="{c["secondary"]}" stroke-width="2"/>'
    ),
}


def app_icon_svg(preset, name):
    c = preset.palette()
    radius = preset.radius * 1.5
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
        f'<rect x="3" y="3" width="58" height="58" rx="{radius}" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="2"/>'
        f"{APP_ICONS[name](c)}</svg>"
    )


def icon_theme(preset, root, icons_root):
    c = preset.palette()
    base = Path(root) / "usr/share/icons" / preset.theme_name
    directories = {"scalable/apps": ("64", "Applications", "Scalable")}
    for name in APP_ICONS:
        write(base / "scalable/apps" / f"{name}.svg", app_icon_svg(preset, name))
    papirus = Path(icons_root) / "Papirus"
    papirus_dark = Path(icons_root) / "Papirus-Dark"
    places_mapper = lambda color: tint_keep_lightness(color, c["primary"])
    if papirus.is_dir():
        for size_dir in sorted(papirus.iterdir()):
            if "@" in size_dir.name or "x" not in size_dir.name or not (size_dir / "places").is_dir():
                continue
            size = size_dir.name.split("x")[0]
            target = f"{size_dir.name}/places"
            count = 0
            for icon in sorted((size_dir / "places").iterdir()):
                if icon.suffix != ".svg" or SKIP_PLACE.match(icon.name):
                    continue
                try:
                    text = Path(os.path.realpath(icon)).read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                write(base / target / icon.name, recolour(text, places_mapper))
                count += 1
            if count:
                directories[target] = (size, "Places", "Fixed")
    if papirus_dark.is_dir():
        mapper = panel_mapper(c)
        for size_dir in sorted(papirus_dark.iterdir()):
            panel = size_dir / "panel"
            if "@" in size_dir.name or not panel.is_dir():
                continue
            size = size_dir.name.split("x")[0]
            target = f"{size_dir.name}/panel"
            count = 0
            for icon in sorted(panel.iterdir()):
                if icon.suffix != ".svg":
                    continue
                try:
                    text = Path(os.path.realpath(icon)).read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                write(base / target / icon.name, recolour(text, mapper))
                count += 1
            if count:
                directories[target] = (size, "Status", "Fixed")
    lines = [
        "[Icon Theme]",
        f"Name={preset.theme_name}",
        f"Comment=NEXUS OS {preset.name} icons",
        "Inherits=Papirus-Dark,Papirus,Adwaita,hicolor",
        "Directories=" + ",".join(directories),
        "",
    ]
    for directory, (size, context, kind) in directories.items():
        lines += [f"[{directory}]", f"Size={size}", f"Context={context}", f"Type={kind}"]
        if kind == "Scalable":
            lines += ["MinSize=16", "MaxSize=512"]
        lines.append("")
    write(base / "index.theme", "\n".join(lines))


def ansi_palette(preset):
    c = preset.palette()
    hues = [0.0, 0.33, 0.14, 0.6, 0.83, 0.5]
    normal = [mix(from_hls(hue, 0.55, 0.65), c["primary"], 0.3) for hue in hues]
    bright = [mix(from_hls(hue, 0.7, 0.75), c["primary"], 0.25) for hue in hues]
    black = mix(c["bg"], c["primary"], 0.15)
    return [black, *normal, c["text"], c["dim"], *bright, c["text_hi"]]


def terminal_scheme(preset, root):
    c = preset.palette()
    write(
        Path(root) / f"usr/share/xfce4/terminal/colorschemes/nexus-{preset.key}.theme",
        "\n".join([
            "[Scheme]",
            f"Name=NEXUS {preset.name}",
            f"ColorForeground={c['text']}",
            f"ColorBackground={c['bg']}",
            f"ColorCursor={c['primary']}",
            "ColorCursorUseDefault=FALSE",
            f"ColorSelection={c['text_hi']}",
            f"ColorSelectionBackground={c['selection']}",
            "ColorSelectionUseDefault=FALSE",
            "ColorBoldUseDefault=TRUE",
            f"TabActivityColor={c['alert']}",
            "ColorPalette=" + ";".join(ansi_palette(preset)),
            "",
        ]),
    )


def onboard_theme(preset, root):
    c = preset.palette()
    base = Path(root) / "usr/share/onboard/themes"
    name = preset.theme_name
    write(
        base / f"{name}.theme",
        "\n".join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<theme format="1.3" name="{escape(name)}">',
            f"  <color_scheme>{name}</color_scheme>",
            "  <key_style>flat</key_style>",
            f"  <roundrect_radius>{preset.radius * 3}</roundrect_radius>",
            "  <key_size>94</key_size>",
            "  <key_stroke_width>100</key_stroke_width>",
            "  <key_fill_gradient>0</key_fill_gradient>",
            "  <key_stroke_gradient>0</key_stroke_gradient>",
            "  <key_gradient_direction>0</key_gradient_direction>",
            "  <key_label_font>Share Tech Mono</key_label_font>",
            "  <key_label_overrides></key_label_overrides>",
            "  <key_shadow_strength>0</key_shadow_strength>",
            "  <key_shadow_size>0</key_shadow_size>",
            "</theme>",
            "",
        ]),
    )
    write(
        base / f"{name}.colors",
        "\n".join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<color_scheme name="{escape(name)}" format="2.1">',
            '  <window type="keyboard">',
            f'    <color element="background" rgb="{c["bg"]}" opacity="0.96"/>',
            "  </window>",
            '  <layer index="0">',
            f'    <color element="background" rgb="{c["bg"]}" opacity="1.0"/>',
            "  </layer>",
            '  <key_group default="true">',
            f'    <color element="fill" rgb="{c["surface_hi"]}" opacity="1.0"/>',
            f'    <color element="stroke" rgb="{c["border"]}" opacity="1.0"/>',
            f'    <color element="label" rgb="{c["primary"]}" opacity="1.0"/>',
            f'    <color element="fill" state="prelight" rgb="{c["hover"]}" opacity="1.0"/>',
            f'    <color element="fill" state="pressed" rgb="{c["primary"]}" opacity="1.0"/>',
            f'    <color element="label" state="pressed" rgb="{c["bg"]}" opacity="1.0"/>',
            f'    <color element="fill" state="active" rgb="{c["secondary"]}" opacity="1.0"/>',
            f'    <color element="fill" state="locked" rgb="{c["alert"]}" opacity="1.0"/>',
            "  </key_group>",
            "</color_scheme>",
            "",
        ]),
    )


SOUND_RATE = 44100

SOUND_EVENTS = {
    "menu-click": [("noise", 0, 0, 0.004, 0.5), ("sine", 2600, 2200, 0.02, 0.6)],
    "notify": [("sine", 1400, 1400, 0.07, 0.7), ("rest", 0, 0, 0.05, 0), ("sine", 1800, 1800, 0.07, 0.7)],
    "alert": [
        ("square", 880, 880, 0.12, 0.55), ("rest", 0, 0, 0.04, 0), ("square", 587, 587, 0.12, 0.55),
        ("rest", 0, 0, 0.04, 0), ("square", 880, 880, 0.12, 0.55), ("rest", 0, 0, 0.04, 0),
        ("square", 587, 587, 0.12, 0.55),
    ],
    "startup": [
        ("sine", 500, 1600, 0.18, 0.6), ("rest", 0, 0, 0.03, 0), ("sine", 1800, 1800, 0.06, 0.6),
        ("rest", 0, 0, 0.02, 0), ("sine", 2400, 2400, 0.05, 0.5),
    ],
    "device-added": [("sine", 900, 1500, 0.08, 0.6)],
    "device-removed": [("sine", 1500, 900, 0.08, 0.6)],
    "screenshot": [("noise", 0, 0, 0.03, 0.45), ("sine", 3000, 2500, 0.03, 0.4)],
    "test": [("sine", 700, 700, 0.12, 0.6), ("rest", 0, 0, 0.05, 0), ("sine", 1400, 1400, 0.12, 0.6)],
}

SOUND_PACKS = {
    "tactical": {"volume": 0.8, "pitch": 1.0, "soft": False},
    "quiet": {"volume": 0.3, "pitch": 0.8, "soft": True},
}


def synth(parts, volume, pitch, soft):
    rng = random.Random(1)
    samples = []
    for kind, start, end, duration, gain in parts:
        count = int(SOUND_RATE * duration)
        phase = 0.0
        for index in range(count):
            progress = index / max(count - 1, 1)
            attack = min(1.0, index / (SOUND_RATE * 0.003))
            release = min(1.0, (count - index) / (SOUND_RATE * 0.015))
            envelope = attack * release * gain * volume
            if kind == "rest":
                value = 0.0
            elif kind == "noise":
                value = rng.uniform(-1, 1) * (1 - progress) ** 2
            else:
                frequency = (start + (end - start) * progress) * pitch
                phase += math.tau * frequency / SOUND_RATE
                value = math.sin(phase)
                if kind == "square" and not soft:
                    value += math.sin(3 * phase) / 3 + math.sin(5 * phase) / 5
                    value *= 0.75
            samples.append(max(-1.0, min(1.0, value * envelope)))
    return samples


def write_wav(path, samples):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SOUND_RATE)
        handle.writeframes(b"".join(struct.pack("<h", int(sample * 32000)) for sample in samples))


def sound_packs(root):
    for pack, options in SOUND_PACKS.items():
        base = Path(root) / f"usr/share/sounds/nexus-{pack}"
        for event, parts in SOUND_EVENTS.items():
            write_wav(base / "stereo" / f"{event}.wav", synth(parts, options["volume"], options["pitch"], options["soft"]))
        write(
            base / "index.theme",
            "\n".join([
                "[Sound Theme]",
                f"Name=NEXUS {pack.title()}",
                "Comment=NEXUS OS sound pack",
                "Directories=stereo",
                "",
                "[stereo]",
                "OutputProfile=stereo",
                "",
            ]),
        )


def build_all(root, icons_root, sign, default_key):
    presets = list_presets(include_hidden=True)
    for preset in presets:
        print(f"[nexus-assets] {preset.name}", flush=True)
        gtk_theme(preset, root)
        icon_theme(preset, root, icons_root)
        render_wallpaper(preset, root)
        plymouth_theme(preset, sign, root)
        terminal_scheme(preset, root)
        onboard_theme(preset, root)
    sound_packs(root)
    render_login(load_preset(default_key), sign, Path(root) / "var/lib/nexus/login.png")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="nexus-assets")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--root", required=True)
    build.add_argument("--icons", default="/usr/share/icons")
    build.add_argument("--callsign", default="NEXUS")
    build.add_argument("--default", default="amber")
    login = sub.add_parser("login")
    login.add_argument("--preset", required=True)
    login.add_argument("--callsign", required=True)
    login.add_argument("--out", required=True)
    plymouth = sub.add_parser("plymouth")
    plymouth.add_argument("--callsign", required=True)
    plymouth.add_argument("--root", default="/")
    args = parser.parse_args(argv)
    if args.command == "build":
        build_all(args.root, args.icons, args.callsign, args.default)
    elif args.command == "login":
        render_login(load_preset(args.preset), args.callsign, args.out)
    elif args.command == "plymouth":
        for preset in list_presets(include_hidden=True):
            plymouth_theme(preset, args.callsign, args.root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
