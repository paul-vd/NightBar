#!/usr/bin/env python3
"""Draw the installer-window background -> assets/dmg_bg.png.

A light backdrop with a curved arrow pointing from where NightBar sits to the
Applications shortcut, plus instructional text — the classic drag-to-install
look. Committed so `make dmg` needs no image libraries; only rerun to tweak.

    pip install pillow && python assets/make_dmg_bg.py

The icon positions here MUST match the `set position` lines in
scripts/dmg_style.applescript (window is W x H points; icons sit at y=ICON_Y).
"""
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 640, 400          # window content size, in points
SS = 3                   # supersample for smooth curves/text
ICON_Y = 200             # icon row (matches the AppleScript positions)
NB_X, APP_X = 150, 490   # NightBar icon x, Applications icon x

TOP = (240, 244, 250)    # very light blue-grey gradient
BOTTOM = (222, 230, 242)
INK = (74, 85, 104)      # arrow + text colour
OUT = os.path.join(os.path.dirname(__file__), "dmg_bg.png")

FONT_CANDIDATES = [
    "/System/Library/Fonts/SFNSRounded.ttf",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def bezier(p0, p1, p2, steps=60):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def main():
    img = Image.new("RGB", (W * SS, H * SS))
    # vertical gradient
    for y in range(H * SS):
        t = y / (H * SS - 1)
        img.paste(tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3)),
                  [0, y, W * SS, y + 1])

    d = ImageDraw.Draw(img)

    # Curved arrow from just right of NightBar, arcing over to Applications.
    p0 = ((NB_X + 70) * SS, (ICON_Y - 40) * SS)
    p1 = (320 * SS, (ICON_Y - 110) * SS)
    p2 = ((APP_X - 55) * SS, (ICON_Y - 45) * SS)
    pts = bezier(p0, p1, p2)
    d.line(pts, fill=INK, width=6 * SS, joint="curve")

    # Arrowhead at the end, aimed along the final tangent.
    ex, ey = pts[-1]
    px, py = pts[-4]
    import math
    ang = math.atan2(ey - py, ex - px)
    a = 26 * SS
    for da in (0.5, -0.5):
        d.line([(ex, ey),
                (ex - a * math.cos(ang - da), ey - a * math.sin(ang - da))],
               fill=INK, width=6 * SS)

    # Instructional text, centred above the icons.
    font = load_font(34 * SS)
    line = "Drag NightBar into Applications"
    tb = d.textbbox((0, 0), line, font=font)
    d.text(((W * SS - (tb[2] - tb[0])) / 2, 40 * SS), line, font=font, fill=INK)

    img.resize((W, H), Image.LANCZOS).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
