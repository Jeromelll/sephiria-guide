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
# Bing IndexNow key for the apex. Filename and body must match; the file is
# published from extra_sites/_root_files/ (not the Sephiria dist).
INDEXNOW_KEY = "ad0db49bd5c248469506a7c12efd28c6"
INDEXNOW_FILE = f"{INDEXNOW_KEY}.txt"
# Nav says "Beginner" but the page has always been /guide/ on this apex.
# Guessed legacy URLs still 404 in Search Console; 301 them before the catch-all.
LEGACY_BEGINNER_PATHS = (
    "/beginner",
    "/beginner/",
    "/beginner-guide",
    "/beginner-guide/",
    "/Beginner",
    "/Beginner/",
    "/guides/beginner",
    "/guides/beginner/",
    "/guide/beginner",
    "/guide/beginner/",
)


def redirects_file() -> str:
    """Cloudflare Pages _redirects. Pages applies rules in order."""
    lines = [
        "/index.html / 301",
        "https://www.warhammersurvivors.com/* https://warhammersurvivors.com/:splat 301",
    ]
    lines.extend(f"{path} /guide/ 301" for path in LEGACY_BEGINNER_PATHS)
    # Catch-all last so the specific beginner rules and the www host redirect win.
    lines.append("/* /404.html 404")
    return "\n".join(lines) + "\n"


def rewrite(html: str) -> str:
    # This standalone build does not ship the parent site's login page or auth API.
    # Remove only its inherited navigation entry; leave the source site untouched.
    html = html.replace('<a class="login" href="/login.html">Log in</a>', "")
    # static assets (css/images) referenced by absolute sub-site path
    html = html.replace(f"{PREFIX}assets/", "/assets/")
    # canonical first (most specific), then internal links
    html = html.replace(f'href="{OLD_DOMAIN}"', f'href="{NEW_DOMAIN}"')
    html = html.replace(OLD_DOMAIN, NEW_DOMAIN)
    html = re.sub(rf'href="{re.escape(PREFIX)}([^"]*)"', lambda m: f'href="/{m.group(1)}"', html)
    html = re.sub(rf'href="{re.escape(PREFIX.rstrip())}"', 'href="/"', html)
    # login lives only on sephiria-guide.com; drop the nav entry on the standalone domain
    html = re.sub(r'<a class="login" href="/login\.html">[^<]*</a>', "", html)
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
            # External URLs can contain the same path segment (for example
            # capydb.com/warhammer-survivors/). Only a leftover internal prefix
            # means the rewrite missed a link.
            internal = re.sub(r"https?://[^\"'\s<]+", "", t)
            if PREFIX in internal:
                bad.append(str(p.relative_to(OUT)))
            if "sephiria-guide.com" in t:
                bad.append(f"{p.relative_to(OUT)} (sephiria ref)")
        # every internal href/src must resolve to a file in warhammer-dist/
        for p in OUT.rglob("*.html"):
            t = p.read_text(encoding="utf-8")
            base = "/" + "/".join(p.relative_to(OUT).parent.parts)
            for ref in re.findall(r'(?:href|src)="([^"#?]+)', t):
                if re.match(r"^(https?:|mailto:|data:|//)", ref):
                    if ref.startswith(NEW_DOMAIN):
                        ref = "/" + ref[len(NEW_DOMAIN):]
                    else:
                        continue
                path = ref if ref.startswith("/") else (base.rstrip("/") + "/" + ref)
                parts = []
                for seg in path.split("/"):
                    if seg in ("", "."):
                        continue
                    if seg == "..":
                        parts and parts.pop()
                    else:
                        parts.append(seg)
                target = OUT.joinpath(*parts) if parts else OUT
                if target.is_dir():
                    target = target / "index.html"
                if not target.is_file():
                    bad.append(f"{p.relative_to(OUT)} (broken link {ref})")
        key_path = OUT / INDEXNOW_FILE
        if not key_path.is_file():
            bad.append(f"missing /{INDEXNOW_FILE} (IndexNow key must ship at site root)")
        else:
            body = key_path.read_text(encoding="utf-8")
            if body not in (INDEXNOW_KEY, INDEXNOW_KEY + "\n"):
                bad.append(f"/{INDEXNOW_FILE} body is not the IndexNow key")
        headers = OUT / "_headers"
        if not headers.is_file():
            bad.append("missing _headers (IndexNow key needs text/plain)")
        else:
            header_text = headers.read_text(encoding="utf-8")
            if f"/{INDEXNOW_FILE}" not in header_text or "text/plain" not in header_text:
                bad.append(f"_headers does not pin text/plain for /{INDEXNOW_FILE}")
        redirects = OUT / "_redirects"
        expected_redirects = redirects_file()
        if not redirects.is_file() or redirects.read_text(encoding="utf-8") != expected_redirects:
            bad.append("_redirects missing legacy beginner 301s or existing rules changed")
        else:
            rules = expected_redirects.splitlines()
            catch_all = "/* /404.html 404"
            if not rules or rules[-1] != catch_all:
                bad.append("_redirects catch-all is not the last rule")
            else:
                catch_at = rules.index(catch_all)
                for path in LEGACY_BEGINNER_PATHS:
                    rule = f"{path} /guide/ 301"
                    if rule not in rules or rules.index(rule) > catch_at:
                        bad.append(f"_redirects missing {rule} before the 404 catch-all")
        if bad:
            print("FAIL:")
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

    # Extra root files (Search Console verification tokens, ads.txt, IndexNow
    # keys, …) ship as-is onto the Warhammer Pages root. Sephiria's build skips
    # this directory, so these files are not published to sephiria-guide.com.
    extras = ROOT / "extra_sites" / "_root_files"
    plain_text_roots: list[str] = []
    if extras.is_dir():
        for src in sorted(extras.rglob("*")):
            if not src.is_file():
                continue
            dest = OUT / src.relative_to(extras)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print("copied", dest.relative_to(ROOT))
            # Unknown paths are HTML (404.html). A real .txt at the root is
            # served as itself; pin text/plain so the catch-all cannot wrap it.
            if src.parent == extras and src.suffix == ".txt":
                plain_text_roots.append(src.name)
    if INDEXNOW_FILE not in plain_text_roots:
        print(f"FAIL: IndexNow key missing {extras / INDEXNOW_FILE}")
        return 1
    header_blocks = [
        f"/{name}\n  Content-Type: text/plain; charset=utf-8" for name in plain_text_roots
    ]
    (OUT / "_headers").write_text("\n\n".join(header_blocks) + "\n", encoding="utf-8")
    print("wrote _headers", len(plain_text_roots), "text/plain root files")

    # Theme assets (css, screenshots) ship as-is under /assets/.
    assets = SRC / "assets"
    if assets.is_dir():
        shutil.copytree(assets, OUT / "assets")
        print("copied assets/")
    if (SRC / "favicon.ico").is_file():
        shutil.copy2(SRC / "favicon.ico", OUT / "favicon.ico")

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
            "<h1>Warhammer Survivors: What It Is, Platforms, Price Status &amp; Release Date</h1>",
            "<h1>Page not found</h1>",
        ),
        encoding="utf-8",
    )
    # www → apex stays first so the 404 catch-all cannot swallow the host redirect.
    # Legacy beginner paths are inserted before that catch-all.
    (OUT / "_redirects").write_text(redirects_file(), encoding="utf-8")
    print(f"wrote sitemap.xml ({len(urls)} urls), robots.txt, 404.html, _redirects")
    return 0


if __name__ == "__main__":
    sys.exit(main())
