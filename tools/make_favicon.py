#!/usr/bin/env python3
"""Regenerate the site favicon set from one Destiny-Tree mark.

Outputs (all from this single script — edit here, rerun, commit):
  assets/favicon.svg            vector master (same geometry as the raster)
  assets/favicon-16x16.png
  assets/favicon-32x32.png
  assets/apple-touch-icon.png   full-bleed square (iOS applies its own mask)
  favicon.ico                   repo root, 16+32+48 (copied to dist by build.py)

Run from the repo root: python3 tools/make_favicon.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

# All geometry lives in a 512x512 space, drawn at SS× supersampling.
SS = 4
BASE = 512
RADIUS = 100
INK_TOP = (24, 17, 46)     # #181130 night violet
INK_BOT = (43, 35, 64)     # #2b2340 — matches config/site.json theme bg
BRANCH = "#f0a43e"         # site accent family (theme --accent #f2a83c)
DOT = "#ffd98f"
SAPPH = "#7fe3ff"          # Destiny-sapphire cyan on the two inner tips
EMBER = SAPPH

TRUNK_TOP = (256, 252)
TRUNK_BOT = (256, 402)
BRANCHES = [
    (TRUNK_BOT, TRUNK_TOP),
    (TRUNK_TOP, (172, 190)),
    ((172, 190), (120, 132)),
    ((172, 190), (208, 156)),
    (TRUNK_TOP, (340, 190)),
    ((340, 190), (392, 132)),
    ((340, 190), (304, 156)),
    ((256, 300), (256, 112)),
    (TRUNK_BOT, (218, 424)),
    (TRUNK_BOT, (294, 424)),
]
TIPS = [(120, 132), (208, 156), (256, 112), (304, 156), (392, 132)]
SAPPH_TIPS = {(208, 156), (304, 156)}
SPARKS = [(96, 238), (432, 210)]
STROKE = 26
DOT_R = 18

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#181130"/>
      <stop offset="1" stop-color="#2b2340"/>
    </linearGradient>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="14"/>
    </filter>
  </defs>
  <rect width="512" height="512" rx="100" fill="url(#sky)"/>
  <ellipse cx="256" cy="400" rx="120" ry="90" fill="#7b5cff" opacity="0.28" filter="url(#glow)"/>
  <g stroke="{branch}" stroke-width="{stroke}" stroke-linecap="round" fill="none" filter="url(#glow)" opacity="0.9">{glow_paths}
  </g>
  {glow_dots}
  <g stroke="{branch}" stroke-width="{stroke}" stroke-linecap="round" fill="none">{paths}
  </g>
  {dots}
  {sparks}
</svg>
"""


def s(v: float) -> int:
    return round(v * SS)


def tip_color(x: int, y: int) -> str:
    return SAPPH if (x, y) in SAPPH_TIPS else DOT


def draw_art(size: int, rounded: bool) -> Image.Image:
    """Render the mark at `size` px; rounded=False gives the full-bleed square."""
    img = Image.new("RGBA", (BASE * SS, BASE * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Night-sky gradient background.
    grad = Image.new("RGBA", (1, BASE * SS))
    for y in range(BASE * SS):
        t = y / (BASE * SS - 1)
        grad.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(INK_TOP, INK_BOT)) + (255,))
    mask = Image.new("L", (BASE * SS, BASE * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, BASE * SS - 1, BASE * SS - 1], radius=RADIUS * SS, fill=255)
    if rounded:
        img.paste(grad.resize((BASE * SS, BASE * SS)), (0, 0), mask)
    else:
        img.paste(grad.resize((BASE * SS, BASE * SS)), (0, 0))

    # Soft violet horizon behind the trunk, ember sparks.
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([s(136), s(310), s(376), s(500)], fill=(123, 92, 255, 70))
    halo = halo.filter(ImageFilter.GaussianBlur(60 * SS // 4))
    img.alpha_composite(halo)

    # Tree glow pass, then the sharp pass on top.
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for a, b in BRANCHES:
        gd.line([s(a[0]), s(a[1]), s(b[0]), s(b[1])], fill=BRANCH, width=s(STROKE))
    for x, y in TIPS:
        gd.ellipse([s(x - DOT_R), s(y - DOT_R), s(x + DOT_R), s(y + DOT_R)], fill=tip_color(x, y))
    glow = glow.filter(ImageFilter.GaussianBlur(14 * SS // 4))
    img.alpha_composite(glow)

    d = ImageDraw.Draw(img)
    for a, b in BRANCHES:
        d.line([s(a[0]), s(a[1]), s(b[0]), s(b[1])], fill=BRANCH, width=s(STROKE))
    for x, y in TIPS + [TRUNK_TOP, TRUNK_BOT]:
        d.ellipse([s(x - STROKE // 2), s(y - STROKE // 2), s(x + STROKE // 2), s(y + STROKE // 2)], fill=BRANCH)
    for x, y in TIPS:
        d.ellipse([s(x - DOT_R), s(y - DOT_R), s(x + DOT_R), s(y + DOT_R)], fill=tip_color(x, y))
    for x, y in SPARKS:
        d.ellipse([s(x - 6), s(y - 6), s(x + 6), s(y + 6)], fill=EMBER)

    img = img.resize((size, size), Image.LANCZOS)
    if rounded:
        small_mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(small_mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=round(RADIUS * size / BASE), fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(img, (0, 0), small_mask)
        return out
    return img


def svg_markup() -> str:
    def seg(a, b):
        return f'\n    <path d="M{a[0]} {a[1]}L{b[0]} {b[1]}"/>'

    paths = "".join(seg(a, b) for a, b in BRANCHES)
    glow_paths = paths
    dots = "".join(
        f'\n  <circle cx="{x}" cy="{y}" r="{DOT_R}" fill="{tip_color(x, y)}"/>' for x, y in TIPS
    )
    glow_dots = f'<g filter="url(#glow)" opacity="0.9">{dots}\n  </g>'
    sparks = "".join(
        f'\n  <circle cx="{x}" cy="{y}" r="6" fill="{EMBER}"/>' for x, y in SPARKS
    )
    return SVG.format(branch=BRANCH, stroke=STROKE, paths=paths, glow_paths=glow_paths,
                      dots=dots, glow_dots=glow_dots, sparks=sparks)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "favicon.svg").write_text(svg_markup(), encoding="utf-8")
    for size in (16, 32):
        draw_art(size, rounded=True).save(ASSETS / f"favicon-{size}x{size}.png")
    draw_art(180, rounded=False).save(ASSETS / "apple-touch-icon.png")
    draw_art(512, rounded=True).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # Preview strip for eyeballing at tab sizes.
    strip = Image.new("RGBA", (256 + 3 * 40, 256), (244, 241, 232, 255))
    strip.paste(draw_art(256, rounded=True), (0, 0))
    for i, px in enumerate((48, 32, 16)):
        icon = draw_art(px, rounded=True)
        strip.alpha_composite(icon, (260 + i * 40, 4))
    strip.save(ROOT / "tools" / "_favicon_preview.png")
    print("favicon assets written to assets/ and favicon.ico")


if __name__ == "__main__":
    main()
