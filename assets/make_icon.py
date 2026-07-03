#!/usr/bin/env python3
"""Draw NightBar's default app icon -> assets/NightBar.png (1024px).

Theme: a night sky (system awake overnight) with a crescent moon and stars,
and the screen off. Rendered at 3x then downsampled for smooth, anti-aliased
edges. Only needed to regenerate the artwork; the resulting PNG/.icns are
committed so a normal build needs no image libraries.

    pip install pillow && python assets/make_icon.py
"""
import os

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
SS = 3                      # supersample factor for smooth edges
S = SIZE * SS
RADIUS = int(0.2235 * S)    # macOS squircle-ish corner radius

TOP = (32, 48, 92)          # night sky, lighter at top
BOTTOM = (9, 15, 32)        # near-black navy at bottom
MOON = (246, 233, 197)      # warm cream
OUT = os.path.join(os.path.dirname(__file__), "NightBar.png")


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius, fill=255)
    return m


def vertical_gradient(size, top, bottom):
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        grad.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return grad.resize((size, size))


def crescent(size, cx, cy, r, color):
    """Crescent = big circle minus an offset circle, on its own alpha layer."""
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)             # full moon
    off = int(r * 0.42)
    d.ellipse([cx - r + off, cy - r - off, cx + r + off, cy + r - off], fill=0)  # bite
    layer = Image.new("RGBA", (size, size), color + (0,))
    layer.putalpha(mask)
    return layer


def main():
    img = Image.new("RGB", (S, S))
    img.paste(vertical_gradient(S, TOP, BOTTOM), (0, 0))

    draw = ImageDraw.Draw(img)
    # Stars: (x%, y%, radius px @1x)
    stars = [(0.18, 0.20, 5), (0.30, 0.35, 3), (0.22, 0.55, 4), (0.15, 0.78, 3),
             (0.38, 0.70, 5), (0.70, 0.18, 4), (0.82, 0.30, 3), (0.55, 0.22, 3),
             (0.78, 0.62, 4), (0.66, 0.80, 3)]
    for px, py, rr in stars:
        x, y, r = px * S, py * S, rr * SS
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255))

    cx, cy, r = int(0.62 * S), int(0.44 * S), int(0.24 * S)

    # Soft glow behind the moon.
    glow = crescent(S, cx, cy, int(r * 1.15), MOON).filter(ImageFilter.GaussianBlur(r * 0.18))
    glow.putalpha(glow.getchannel("A").point(lambda a: a * 0.5))
    img.paste(glow, (0, 0), glow)

    moon = crescent(S, cx, cy, r, MOON)
    img.paste(moon, (0, 0), moon)

    # Round the corners and downsample.
    img.putalpha(rounded_mask(S, RADIUS))
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
