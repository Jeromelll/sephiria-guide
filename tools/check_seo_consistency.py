#!/usr/bin/env python3
"""Deterministic SEO checks for sephiria-guide.com built HTML.

Checks (coach-style: script, not prompt):
  1. Exactly one <h1> per public HTML page
  2. Canonical present, same host, self-consistent with file path
  3. sitemap.xml ↔ disk: every sitemap loc has index.html;
     every public page is in the sitemap

Run from site/ after build:
  python3 tools/check_seo_consistency.py
  python3 tools/check_seo_consistency.py --json
Exit 0 = clean (WARN OK); 1 = any FAIL.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

SITE = Path(__file__).resolve().parents[1]
ORIGIN = "https://sephiria-guide.com"
SITEMAP = SITE / "sitemap.xml"

SKIP_DIR_NAMES = {"assets", "content", "config", "tools", "raw"}
SKIP_FILES = {"404.html"}


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.canonical: str | None = None
        self.title: str | None = None
        self.description: str | None = None
        self._in_title = False
        self._title_buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: (v or "") for k, v in attrs}
        if tag == "h1":
            self.h1_count += 1
        elif tag == "link" and "canonical" in d.get("rel", "").lower():
            self.canonical = d.get("href") or None
        elif tag == "meta" and d.get("name", "").lower() == "description":
            self.description = d.get("content") or ""
        elif tag == "title":
            self._in_title = True
            self._title_buf = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = self._title_buf.strip()

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buf += data


def iter_pages() -> list[Path]:
    pages: list[Path] = []
    for p in SITE.rglob("*.html"):
        rel = p.relative_to(SITE)
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if p.name in SKIP_FILES:
            continue
        # only pretty URLs: index.html at root or under a folder
        if p.name != "index.html":
            continue
        pages.append(p)
    return sorted(pages)


def file_to_url(path: Path) -> str:
    rel = path.relative_to(SITE).as_posix()
    if rel == "index.html":
        return ORIGIN + "/"
    if rel.endswith("/index.html"):
        return ORIGIN + "/" + rel[: -len("index.html")]
    raise ValueError(rel)


def url_to_file(url: str) -> Path | None:
    p = urlparse(url)
    origin = f"{p.scheme}://{p.netloc}"
    if origin != ORIGIN:
        return None
    path = p.path or "/"
    if path == "/":
        return SITE / "index.html"
    slug = path.strip("/")
    candidate = SITE / slug / "index.html"
    return candidate if candidate.is_file() else None


def parse_sitemap(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)


def norm_url(u: str) -> str:
    u = u.strip()
    if u == ORIGIN:
        return ORIGIN + "/"
    # Sephiria canonicals use trailing slash for non-home
    if not u.endswith("/") and urlparse(u).path not in ("", "/"):
        # accept either; normalize to trailing slash for compare when file is dir index
        pass
    return u


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    fails: list[dict] = []
    warns: list[dict] = []
    oks: list[dict] = []

    pages = iter_pages()
    page_urls = {file_to_url(p): p for p in pages}

    for path in pages:
        html = path.read_text(encoding="utf-8")
        parser = HeadParser()
        parser.feed(html)
        url = file_to_url(path)
        rel = path.relative_to(SITE).as_posix()

        if parser.h1_count != 1:
            fails.append(
                {
                    "check": "h1",
                    "file": rel,
                    "url": url,
                    "detail": f"expected exactly 1 <h1>, found {parser.h1_count}",
                }
            )
        else:
            oks.append({"check": "h1", "file": rel, "url": url})

        if not parser.canonical:
            fails.append(
                {
                    "check": "canonical_missing",
                    "file": rel,
                    "url": url,
                    "detail": "no <link rel=canonical>",
                }
            )
            continue

        can = parser.canonical.strip()
        # build.py writes domain+path; home is https://sephiria-guide.com/
        if can == ORIGIN:
            can = ORIGIN + "/"
        host = f"{urlparse(can).scheme}://{urlparse(can).netloc}"
        if host != ORIGIN:
            fails.append(
                {
                    "check": "canonical_host",
                    "file": rel,
                    "url": url,
                    "detail": f"canonical off-site: {can}",
                }
            )
            continue

        # Allow missing trailing slash mismatch as WARN only if same path
        can_n = can if can.endswith("/") or can == ORIGIN + "/" else can + "/"
        url_n = url
        if can_n == url_n or can == url:
            oks.append({"check": "canonical_self", "file": rel, "url": url})
        elif can_n in page_urls or can in page_urls:
            warns.append(
                {
                    "check": "canonical_consolidate",
                    "file": rel,
                    "url": url,
                    "detail": f"canonical points to {can}",
                }
            )
        else:
            fails.append(
                {
                    "check": "canonical_mismatch",
                    "file": rel,
                    "url": url,
                    "detail": f"canonical {can} != expected {url}",
                }
            )

        if not (parser.title or "").strip():
            warns.append({"check": "title_empty", "file": rel, "url": url, "detail": "empty <title>"})
        if not (parser.description or "").strip():
            warns.append(
                {
                    "check": "description_empty",
                    "file": rel,
                    "url": url,
                    "detail": "empty meta description",
                }
            )

    if not SITEMAP.is_file():
        fails.append({"check": "sitemap_missing", "file": "sitemap.xml", "detail": "file not found"})
        locs: list[str] = []
    else:
        locs = []
        for u in parse_sitemap(SITEMAP):
            u = u.strip()
            if u == ORIGIN:
                u = ORIGIN + "/"
            locs.append(u)

    loc_set = set(locs)
    # also accept without trailing slash variants when matching
    def in_sitemap(u: str) -> bool:
        if u in loc_set:
            return True
        if u.endswith("/") and u.rstrip("/") in loc_set:
            return True
        if not u.endswith("/") and (u + "/") in loc_set:
            return True
        return False

    for loc in locs:
        f = url_to_file(loc if loc.endswith("/") or loc == ORIGIN + "/" else loc + "/")
        if f is None:
            f = url_to_file(loc)
        if f is None or not f.is_file():
            fails.append(
                {
                    "check": "sitemap_phantom",
                    "url": loc,
                    "detail": "in sitemap but no matching index.html on disk",
                }
            )
        else:
            oks.append({"check": "sitemap_has_file", "url": loc, "file": f.relative_to(SITE).as_posix()})

    for url, path in page_urls.items():
        if not in_sitemap(url):
            fails.append(
                {
                    "check": "sitemap_missing_page",
                    "file": path.relative_to(SITE).as_posix(),
                    "url": url,
                    "detail": "public page on disk but not in sitemap.xml",
                }
            )

    report = {
        "site": ORIGIN,
        "pages": len(pages),
        "sitemap_locs": len(locs),
        "fail": fails,
        "warn": warns,
        "ok_n": len(oks),
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Sephiria SEO consistency — {ORIGIN}")
        print(f"pages={len(pages)} sitemap_locs={len(locs)} ok={len(oks)} warn={len(warns)} fail={len(fails)}")
        for item in fails:
            print(f"FAIL  [{item['check']}] {item.get('file') or item.get('url')}: {item.get('detail')}")
        for item in warns:
            print(f"WARN  [{item['check']}] {item.get('file') or item.get('url')}: {item.get('detail')}")
        if not fails and not warns:
            print("All checks passed.")
        elif not fails:
            print("No FAILs (WARN only).")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
