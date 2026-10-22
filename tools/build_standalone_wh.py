#!/usr/bin/env python3
"""Build the standalone Warhammer Survivors site from extra_sites/warhammer-survivors/.

Single source of truth stays extra_sites/warhammer-survivors/ (the sub-site that
also ships on sephiria-guide.com). This script rewrites domain + paths so the same
pages can serve from their own apex domain, and emits sitemap/robots/404.

    python3 tools/build_standalone_wh.py            # → warhammer-dist/
    python3 tools/build_standalone_wh.py --check    # verify no leftover sub-site paths
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "extra_sites" / "warhammer-survivors"
OUT = ROOT / "warhammer-dist"
OLD_DOMAIN = "https://sephiria-guide.com/warhammer-survivors/"
NEW_DOMAIN = "https://warhammersurvivors.com/"
PREFIX = "/warhammer-survivors/"


def rewrite(html: str) -> str:
    # canonical first (most specific), then internal links
    html = html.replace(f'href="{OLD_DOMAIN}"', f'href="{NEW_DOMAIN}"')
    html = html.replace(OLD_DOMAIN, NEW_DOMAIN)
    html = re.sub(rf'href="{re.escape(PREFIX)}([^"]*)"', lambda m: f'href="/{m.group(1)}"', html)
    html = re.sub(rf'href="{re.escape(PREFIX.rstrip())}"', 'href="/"', html)
    # standalone footer: drop the cross-site network line
    html = re.sub(
        r'Part of the guide network at <a href="/">sephiria-guide\.com</a>[^.]*\.\s*',
        "",
        html,
    )
    html = html.replace(
        'Unofficial fan guide for Warhammer Survivors.',
        'Unofficial fan guide for Warhammer Survivors.',
    )
    return html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify output has no sub-site paths")
    args = ap.parse_args()

    if args.check:
        if not OUT.is_dir():
            print("FAIL: warhammer-dist/ missing — run without --check first")
            return 1
        bad = []
        for p in OUT.rglob("*.html"):
            t = p.read_text(encoding="utf-8")
            if PREFIX in t:
                bad.append(str(p.relative_to(OUT)))
            if "sephiria-guide.com" in t:
                bad.append(f"{p.relative_to(OUT)} (sephiria ref)")
        if bad:
            print("FAIL leftover sub-site references:")
            for b in sorted(set(bad)):
                print(" ", b)
            return 1
        print("OK: no sub-site paths or sephiria references in warhammer-dist/")
        return 0

    if not SRC.is_dir():
        print(f"FAIL: source missing {SRC}")
        return 1
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    urls: list[str] = []
    for index in sorted(SRC.rglob("index.html")):
        rel_dir = index.parent.relative_to(SRC)
        parts = [p for p in rel_dir.parts if p not in ("", ".")]
        dest_dir = OUT.joinpath(*parts) if parts else OUT
        dest_dir.mkdir(parents=True, exist_ok=True)
        html = rewrite(index.read_text(encoding="utf-8"))
        (dest_dir / "index.html").write_text(html, encoding="utf-8")
        url = NEW_DOMAIN + ("/".join(parts) + "/" if parts else "")
        urls.append(url)
        print("wrote", (dest_dir / "index.html").relative_to(ROOT))

    day = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for i, u in enumerate(urls):
        pri = "1.0" if i == 0 else "0.8"
        sm.append(f"  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>{pri}</priority><lastmod>{day}</lastmod></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {NEW_DOMAIN}sitemap.xml\n", encoding="utf-8"
    )
    notfound = (OUT / "index.html").read_text(encoding="utf-8")
    (OUT / "404.html").write_text(
        notfound.replace(
            "<h1>Warhammer Survivors Guide — Characters, Weapons &amp; Evolutions</h1>",
            "<h1>Page not found</h1>",
        ),
        encoding="utf-8",
    )
    (OUT / "_redirects").write_text("/* /404.html 404\n", encoding="utf-8")
    print(f"wrote sitemap.xml ({len(urls)} urls), robots.txt, 404.html, _redirects")
    return 0


if __name__ == "__main__":
    sys.exit(main())
