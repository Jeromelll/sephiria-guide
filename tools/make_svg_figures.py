#!/usr/bin/env python3
"""Generate the site's self-made figures as SVG.

No screenshots from the games: these are diagrams built from data the pages
already publish (branch table, release dates, platform list), so every figure
can be traced back to a cited row.

    python3 tools/make_svg_figures.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEPH = ROOT / "assets" / "img"
WH = ROOT / "extra_sites" / "warhammer-survivors" / "assets"

INK = "#1c1b19"
MUTED = "#6b6560"
LINE = "#d8d2c8"
BG = "#faf7f2"
ACCENT = "#7a4b2a"

FONT = "'Alegreya Sans', 'Helvetica Neue', Arial, sans-serif"


def esc(text: str) -> str:
    """XML-escape text nodes: an ampersand in a label breaks the SVG parser."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _svg(w: int, h: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">\n'
        f'  <rect width="{w}" height="{h}" fill="{BG}"/>\n{body}\n</svg>\n'
    )


def weapon_branches() -> str:
    rows = [
        ("Sword & Shield", "Defensive close melee", "First runs, pattern learning", "Short reach"),
        ("Greatsword", "Heavy, wide melee", "Creating space, clearing groups", "Long commitment per swing"),
        ("Dagger", "Fast reaction melee", "Precise counters, bosses", "Extremely short reach"),
        ("Crossbow", "Ranged positioning", "Kiting, safe damage", "Reload discipline"),
        ("Katana", "Aggressive melee", "High ceiling once parry timing lands", "Steeper mastery curve"),
        ("Staff / Quarterstaff", "Versatile caster", "Flexible damage at most ranges", "Needs upgrade support to scale"),
    ]
    w, h = 1000, 520
    cols = 3
    cw, ch = 310, 200
    gap = 20
    x0, y0 = 20, 80
    out = [f'  <text x="20" y="44" font-size="26" font-weight="700" fill="{INK}">Six weapon branches, one tradeoff each</text>',
           f'  <text x="20" y="66" font-size="15" fill="{MUTED}">Sephiria 1.0 · every branch has its own upgrade pool</text>']
    for i, (name, ident, fit, trade) in enumerate(rows):
        r, c = divmod(i, cols)
        x = x0 + c * (cw + gap)
        y = y0 + r * (ch + gap)
        out += [
            f'  <rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10" fill="#ffffff" stroke="{LINE}"/>',
            f'  <text x="{x+18}" y="{y+34}" font-size="19" font-weight="700" fill="{INK}">{esc(name)}</text>',
            f'  <text x="{x+18}" y="{y+60}" font-size="14" fill="{ACCENT}">{esc(ident)}</text>',
            f'  <line x1="{x+18}" y1="{y+76}" x2="{x+cw-18}" y2="{y+76}" stroke="{LINE}"/>',
            f'  <text x="{x+18}" y="{y+102}" font-size="12" fill="{MUTED}">BEST FIT</text>',
            f'  <text x="{x+18}" y="{y+122}" font-size="14" fill="{INK}">{esc(fit)}</text>',
            f'  <text x="{x+18}" y="{y+152}" font-size="12" fill="{MUTED}">TRADEOFF</text>',
            f'  <text x="{x+18}" y="{y+172}" font-size="14" fill="{INK}">{esc(trade)}</text>',
        ]
    return _svg(w, h, "\n".join(out))


def release_timeline() -> str:
    # x axis: 2026-08 .. 2027-06 (11 months)
    months = ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    events = [
        ("Boltgun II", 2.0, "released 14 Oct 2026"),
        ("Warhammer Survivors", 3.0, "10 Nov 2026"),
        ("Dawn of War IV", 4.0, "3 Dec 2026"),
        ("Total War: WH40k", 5.0, "2027 window"),
        ("Space Marine 3", None, "no date"),
    ]
    w, h = 1000, 400
    left, right, top = 210, 40, 130
    span = w - left - right
    step = span / (len(months) - 1)
    out = [f'  <text x="20" y="40" font-size="24" font-weight="700" fill="{INK}">Announced Warhammer releases</text>',
           f'  <text x="20" y="62" font-size="14" fill="{MUTED}">Checked 9 November 2026 · only officially dated titles are placed on the axis</text>']
    for i, m in enumerate(months):
        x = left + i * step
        out.append(f'  <line x1="{x:.0f}" y1="{top-10}" x2="{x:.0f}" y2="{top+165}" stroke="{LINE}"/>')
        out.append(f'  <text x="{x:.0f}" y="{top-18}" font-size="12" fill="{MUTED}" text-anchor="middle">{esc(m)}</text>')
    for idx, (name, pos, note) in enumerate(events):
        y = top + 10 + idx * 30
        out.append(f'  <text x="200" y="{y+5}" font-size="14" fill="{INK}" text-anchor="end">{esc(name)}</text>')
        if pos is None:
            out.append(f'  <text x="{left+6}" y="{y+5}" font-size="13" fill="{MUTED}">—  {esc(note)}</text>')
            continue
        x = left + pos * step
        out.append(f'  <circle cx="{x:.0f}" cy="{y}" r="7" fill="{ACCENT}"/>')
        tx = x + 12
        out.append(f'  <text x="{tx:.0f}" y="{y+5}" font-size="13" fill="{MUTED}">{esc(note)}</text>')
    return _svg(w, h, "\n".join(out))


def platform_matrix() -> str:
    games = ["Warhammer Survivors", "Boltgun II", "Dawn of War IV", "Total War: WH40k", "Space Marine 3"]
    platforms = ["PC", "PS5", "Xbox", "Switch", "Mobile"]
    # 2 = confirmed, 1 = to follow/partial, 0 = not announced, None = unknown (no platforms named)
    grid = [
        [2, 2, 2, 2, 2],
        [2, 2, 2, 1, None],
        [2, 0, 0, 0, 0],
        [2, 0, 0, 0, 0],
        [None, None, None, None, None],
    ]
    w, h = 1000, 380
    left, top = 260, 100
    cw, ch = 118, 44
    out = [f'  <text x="20" y="40" font-size="24" font-weight="700" fill="{INK}">Platform coverage</text>',
           f'  <text x="20" y="62" font-size="14" fill="{MUTED}">Filled = confirmed by the developer or store page · half = announced to follow · blank = not announced</text>']
    for j, p in enumerate(platforms):
        x = left + j * cw
        out.append(f'  <text x="{x+cw/2}" y="{top-12}" font-size="12" fill="{MUTED}" text-anchor="middle">{esc(p)}</text>')
    for i, g in enumerate(games):
        y = top + i * ch
        out.append(f'  <text x="20" y="{y+28}" font-size="14" fill="{INK}">{esc(g)}</text>')
        for j, v in enumerate(grid[i]):
            x = left + j * cw
            if v is None:
                out.append(f'  <rect x="{x+16}" y="{y+8}" width="{cw-32}" height="{ch-16}" rx="6" fill="none" stroke="{LINE}" stroke-dasharray="4 3"/>')
                out.append(f'  <text x="{x+cw/2}" y="{y+28}" font-size="12" fill="{MUTED}" text-anchor="middle">TBA</text>')
            elif v == 2:
                out.append(f'  <rect x="{x+16}" y="{y+8}" width="{cw-32}" height="{ch-16}" rx="6" fill="{ACCENT}"/>')
            elif v == 1:
                out.append(f'  <rect x="{x+16}" y="{y+8}" width="{cw-32}" height="{ch-16}" rx="6" fill="none" stroke="{ACCENT}"/>')
                out.append(f'  <text x="{x+cw/2}" y="{y+28}" font-size="12" fill="{ACCENT}" text-anchor="middle">to follow</text>')
            else:
                out.append(f'  <rect x="{x+16}" y="{y+8}" width="{cw-32}" height="{ch-16}" rx="6" fill="none" stroke="{LINE}"/>')
    return _svg(w, h, "\n".join(out))


def main() -> int:
    SEPH.mkdir(parents=True, exist_ok=True)
    WH.mkdir(parents=True, exist_ok=True)
    (SEPH / "fig-weapon-branches.svg").write_text(weapon_branches(), encoding="utf-8")
    (WH / "fig-release-timeline.svg").write_text(release_timeline(), encoding="utf-8")
    (WH / "fig-platform-matrix.svg").write_text(platform_matrix(), encoding="utf-8")
    print("wrote fig-weapon-branches.svg, fig-release-timeline.svg, fig-platform-matrix.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
