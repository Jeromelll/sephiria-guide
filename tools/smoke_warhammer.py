#!/usr/bin/env python3
"""Smoke the standalone Warhammer Survivors build and the Sephiria 301 contract.

The standalone site is warhammer-dist/. Sephiria no longer copies those pages;
build.py must still 301 every source index to https://warhammersurvivors.com/.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SRC = ROOT / "extra_sites" / "warhammer-survivors"
OUT = ROOT / "warhammer-dist"
APEX = "https://warhammersurvivors.com"
NAV = (
    "/",
    "/demo/",
    "/guide/",
    "/codex/",
    "/characters/",
    "/evolutions/",
    "/stages/",
    "/tier-list/",
    "/upcoming-warhammer-games/",
)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1: list[str] = []
        self.nav: list[str] = []
        self._h1: list[str] | None = None
        self._nav = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "nav":
            self._nav += 1
        if tag == "h1":
            self._h1 = []
        if tag == "a" and self._nav and data.get("href"):
            self.nav.append(data["href"].split("#", 1)[0])

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self._nav:
            self._nav -= 1
        if tag == "h1" and self._h1 is not None:
            self.h1.append("".join(self._h1).strip())
            self._h1 = None

    def handle_data(self, data: str) -> None:
        if self._h1 is not None:
            self._h1.append(data)


def parse(path: Path) -> tuple[str, Page]:
    text = path.read_text(encoding="utf-8")
    parser = Page()
    parser.feed(text)
    return text, parser


def source_rules() -> list[str]:
    rules: list[str] = []
    for index in sorted(SRC.rglob("index.html")):
        parts = [part for part in index.parent.relative_to(SRC).parts if part not in ("", ".")]
        tail = "/".join(parts) + "/" if parts else ""
        old = f"/warhammer-survivors/{tail}"
        new = f"{APEX}/{tail}"
        rules.append(f"{old} {new} 301")
        if not parts:
            rules.append(f"/warhammer-survivors {new} 301")
    return rules


def redirect_text() -> str:
    import build

    tmp = Path(tempfile.mkdtemp(prefix="wh-redirects-"))
    previous = build.OUTPUT_DIR
    build.OUTPUT_DIR = tmp
    try:
        build.write_redirects()
        return (tmp / "_redirects").read_text(encoding="utf-8")
    finally:
        build.OUTPUT_DIR = previous
        shutil.rmtree(tmp, ignore_errors=True)


def missing_redirects(text: str) -> list[str]:
    return [rule for rule in source_rules() if rule not in text.splitlines()]


def check(dist: Path) -> list[str]:
    fails: list[str] = []
    home_file = dist / "index.html"
    if not home_file.is_file():
        return [f"missing {home_file}"]
    home, home_page = parse(home_file)
    if home_page.h1 != ["Warhammer Survivors: What It Is, Platforms, Price Status & Release Date"]:
        fails.append(f"home h1 {home_page.h1!r}")
    if home_page.nav != list(NAV):
        fails.append(f"home nav {home_page.nav!r}")
    if 'href="/login.html"' in home:
        fails.append("standalone home still links at the Sephiria login page")
    for needle in ("10 November 2026", 'href="/guide/"', 'href="/characters/"'):
        if needle not in home:
            fails.append(f"home missing {needle}")

    guide_file = dist / "guide" / "index.html"
    if not guide_file.is_file():
        fails.append("guide page missing")
    else:
        guide, guide_page = parse(guide_file)
        if guide_page.h1 != ["Warhammer Survivors Beginner Guide"]:
            fails.append(f"guide h1 {guide_page.h1!r}")
        if "paint pots" not in guide:
            fails.append("guide page lost the paint pots explanation")
        if 'href="/"' not in guide:
            fails.append("guide page has no link back to the overview")

    codex = dist / "codex" / "characters" / "index.html"
    if not codex.is_file():
        fails.append("character codex missing")
    else:
        codex_html = codex.read_text(encoding="utf-8")
        if 'id="cx-q"' not in codex_html:
            fails.append("character codex has no search box")
        if codex_html.count('class="cx-card') < 2:
            fails.append("character codex has fewer than two entries")

    css = dist / "assets" / "wh.css"
    shot = dist / "assets" / "ss1.jpg"
    if not css.is_file() or "--gold:" not in css.read_text(encoding="utf-8"):
        fails.append("wh.css missing the theme token")
    if not shot.is_file() or not shot.read_bytes().startswith(b"\xff\xd8"):
        fails.append("ss1.jpg is not a JPEG")
    return fails


def check_redirects() -> list[str]:
    try:
        text = redirect_text()
    except Exception as exc:  # noqa: BLE001 — surface the build failure as a check
        return [f"could not render Sephiria redirects: {exc}"]
    return [f"Sephiria redirect missing: {rule}" for rule in missing_redirects(text)]


def self_test() -> int:
    page_fails = check(OUT)
    redirect_fails = check_redirects()
    if page_fails or redirect_fails:
        print("FAIL self-test setup; warhammer build is not clean:")
        for item in page_fails + redirect_fails:
            print(" ", item)
        return 1

    failed = 0
    tmp = Path(tempfile.mkdtemp(prefix="wh-smoke-"))
    try:
        for rel in (
            "index.html",
            "guide/index.html",
            "codex/characters/index.html",
            "assets/wh.css",
            "assets/ss1.jpg",
        ):
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(OUT / rel, target)
        (tmp / "guide" / "index.html").unlink()
        found = check(tmp)
        if not found:
            failed += 1
            print("FAIL counterexample passed: deleted guide page")
        else:
            print(f"PASS counterexample failed (deleted guide): {found[0]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    real = redirect_text()
    dropped = "\n".join(
        line for line in real.splitlines() if not line.startswith("/warhammer-survivors/guide/")
    )
    gone = missing_redirects(dropped)
    if not any("/warhammer-survivors/guide/" in rule for rule in gone):
        failed += 1
        print("FAIL counterexample passed: guide redirect removed")
    else:
        print("PASS counterexample failed (guide redirect removed)")
    if failed:
        return 1
    print("PASS warhammer smoke self-test")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    fails = check(OUT) + check_redirects()
    if fails:
        print(f"FAIL warhammer smoke ({len(fails)})")
        for item in fails:
            print(" ", item)
        return 1
    print("PASS warhammer smoke: nav, guide, codex search, assets, Sephiria 301s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
