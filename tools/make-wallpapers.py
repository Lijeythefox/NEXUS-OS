#!/usr/bin/python3
"""Makes a theme's wallpapers from its colours.

    python3 tools/make-wallpapers.py THEME.CONF OUTDIR

Writes 1.png, 2.png and 3.png (1920x1080) into OUTDIR. Needs rsvg-convert
(Debian package librsvg2-bin). No colour is typed here: all come from theme.conf.
"""
import subprocess
import sys
from pathlib import Path

W, H = 1920, 1080


def load(path):
    colours = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = (part.strip() for part in line.split("=", 1))
            colours[key] = value
    return colours


def glow(ident, cx, cy, r, colour, strength):
    return (f'<radialGradient id="{ident}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="{colour}" stop-opacity="{strength}"/>'
            f'<stop offset="1" stop-color="{colour}" stop-opacity="0"/></radialGradient>')


def designs(c):
    bg, a, b = c["bg"], c["accent"], c["accent2"]
    base = f'<rect width="{W}" height="{H}" fill="{bg}"/>'
    one = (f'<defs>{glow("g1", 230, 1210, 1150, b, 0.34)}{glow("g2", 1850, -130, 1050, a, 0.30)}</defs>'
           f'{base}<rect width="{W}" height="{H}" fill="url(#g1)"/><rect width="{W}" height="{H}" fill="url(#g2)"/>')
    two = (f'<defs><linearGradient id="l1" x1="0" y1="0" x2="1" y2="1">'
           f'<stop offset="0" stop-color="{a}" stop-opacity="0.22"/><stop offset="0.45" stop-color="{a}" stop-opacity="0"/>'
           f'<stop offset="0.55" stop-color="{b}" stop-opacity="0"/><stop offset="1" stop-color="{b}" stop-opacity="0.26"/>'
           f'</linearGradient></defs>{base}<rect width="{W}" height="{H}" fill="url(#l1)"/>')
    three = (f'<defs>{glow("g3", 1500, 370, 900, a, 0.10)}</defs>{base}'
             f'<rect width="{W}" height="{H}" fill="url(#g3)"/>'
             f'<circle cx="1500" cy="370" r="330" fill="{b}" fill-opacity="0.09"/>'
             f'<circle cx="1500" cy="370" r="180" fill="{a}" fill-opacity="0.16"/>'
             f'<circle cx="1500" cy="370" r="330" fill="none" stroke="{a}" stroke-opacity="0.18" stroke-width="2"/>')
    return [one, two, three]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    colours = load(sys.argv[1])
    for key in ("bg", "accent", "accent2"):
        if key not in colours:
            sys.exit(f"make-wallpapers: {sys.argv[1]} has no colour called '{key}'")
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for number, body in enumerate(designs(colours), 1):
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{body}</svg>'
        subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(out / f"{number}.png")],
                       input=svg.encode("utf-8"), check=True)
        print(f"wrote {out / f'{number}.png'}")


if __name__ == "__main__":
    main()
