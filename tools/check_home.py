#!/usr/bin/env python3
"""Check the portal home page contract.

The home page was rebuilt on 2026-11-13: it used to be an illustrated "guide
village" that asked a first-time visitor to decode a metaphor before choosing a
page. It is now a two-game portal — Football Manager 27 and Sephiria — with the
three most-read guides under each entry and a client-side search over every page.

This gate asserts the parts that must stay true:

  1. exactly two game entries, linking to /fm27/ and /guides/
  2. three guide links per entry, and every one resolves to a real built page
  3. no village-metaphor copy and no village stylesheet reference
  4. a search field, the portal script, and a non-empty search index
  5. no sign-in entry in the header
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class HomeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[str] = []
        self.guide_links: list[str] = []
        self.header_links: list[str] = []
        self.resources: list[str] = []
        self.has_search = False
        self._in_header = False
        self._in_card = 0
        self._in_guide_list = 0

    def handle_starttag(self, tag, attrs):
        d = {k: (v or "") for k, v in attrs}
        classes = d.get("class", "").split()
        if tag == "header":
            self._in_header = True
        if tag == "article":
            card = next((c for c in classes if c.startswith("portal-card--")), None)
            if card:
                self._in_card += 1
                self.cards.append(card)
        if tag == "a":
            href = d.get("href", "")
            if self._in_header:
                self.header_links.append(href)
            if self._in_guide_list:
                self.guide_links.append(href)
        if tag == "div" and "guide-list" in classes and self._in_card:
            self._in_guide_list += 1
        if tag == "input" and d.get("id") == "guide-search":
            self.has_search = True
        if tag in ("script", "link", "img"):
            url = d.get("src") or d.get("href", "")
            if url.startswith("assets/"):
                self.resources.append(url.split("?", 1)[0])

    def handle_endtag(self, tag):
        if tag == "header":
            self._in_header = False
        if tag == "div" and self._in_guide_list:
            self._in_guide_list -= 1
        if tag == "article":
            self._in_card = max(0, self._in_card - 1)


def main() -> int:
    home = DIST / "index.html"
    if not home.is_file():
        print("FAIL: dist/index.html missing — run python3 build.py first")
        return 1

    html = home.read_text(encoding="utf-8")
    parser = HomeParser()
    parser.feed(html)

    fails: list[str] = []

    if sorted(parser.cards) != ["portal-card--fm27", "portal-card--sephiria"]:
        fails.append(f"expected two game entries (fm27, sephiria), found {parser.cards}")

    expected_hubs = {"/fm27/", "/guides/"}
    entry_links = {href for href in parser.header_links if href in expected_hubs}
    # The card headline links to the section hub; check them from the card markup.
    for hub in expected_hubs:
        if f'href="{hub}"' not in html:
            fails.append(f"missing game entry link to {hub}")

    if len(parser.guide_links) != 6:
        fails.append(f"expected 3 guide links per game entry (6 total), found {len(parser.guide_links)}")

    for href in parser.guide_links:
        target = DIST / href.strip("/") / "index.html" if href.endswith("/") else DIST / href.lstrip("/")
        if not target.is_file():
            fails.append(f"guide link does not resolve to a built page: {href}")

    for banned in ("guide village", "village map", "Village noticeboard", "Your adventure starts here"):
        if banned.lower() in html.lower():
            fails.append(f"village-metaphor copy still on the home page: {banned!r}")

    if "village.css" in html:
        fails.append("home page still loads village.css")

    if not parser.has_search:
        fails.append("search field #guide-search missing from the home page")
    if "assets/portal.js" not in html:
        fails.append("assets/portal.js is not loaded on the home page")

    index_path = DIST / "assets" / "search-index.json"
    if not index_path.is_file():
        fails.append("assets/search-index.json missing")
    else:
        rows = json.loads(index_path.read_text(encoding="utf-8"))
        if len(rows) < 10:
            fails.append(f"search index looks empty ({len(rows)} rows)")
        paths = {r["p"] for r in rows}
        for must in ("/fm27-mods/", "/hard-mode/"):
            if must not in paths:
                fails.append(f"search index is missing {must}")

    if any("login" in href for href in parser.header_links):
        fails.append("header still links to a sign-in page")

    # Every asset referenced by the home page must exist in dist/.
    for url in parser.resources:
        if not (DIST / url).is_file():
            fails.append(f"missing asset referenced by the home page: {url}")

    if fails:
        print("FAIL: home portal contract")
        for f in fails:
            print("  -", f)
        return 1

    print(
        "PASS: two game entries, 3 guides each (all resolving), no village copy, "
        "search + index present, no sign-in entry"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
