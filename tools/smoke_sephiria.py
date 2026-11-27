#!/usr/bin/env python3
"""Smoke the built Sephiria guide: navigation, page content, login shell, assets.

Reads dist/ produced by build.py. Expectations come from config/site.json and
content/*.json. --self-test copies that dist, breaks one contract at a time,
and requires each broken copy to fail.
"""
from __future__ import annotations

import json
import posixpath
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ASSETS = (
    "assets/styles.css",
    "assets/theme.css",
    "assets/img/village.png",
    "assets/img/capsule.jpg",
    "assets/login.js",
    "assets/login.css",
)


class Extract(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1: list[str] = []
        self.hrefs: list[str] = []
        self.ids: set[str] = set()
        self.scripts: list[str] = []
        self._h1: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "h1":
            self._h1 = []
        if tag == "a" and "href" in data:
            self.hrefs.append(data["href"])
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "script" and data.get("src"):
            self.scripts.append(data["src"].split("?", 1)[0])

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self._h1 is not None:
            self.h1.append("".join(self._h1).strip())
            self._h1 = None

    def handle_data(self, data: str) -> None:
        if self._h1 is not None:
            self._h1.append(data)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def journey_paths() -> list[str]:
    cfg = load_json(ROOT / "config" / "site.json")
    home = load_json(ROOT / "content" / "home.json")
    paths = ["/", "/guides/", "/login.html", "/characters/"]
    for _label, href in cfg["nav"]:
        paths.append(href if href.endswith("/") or href.endswith(".html") else href + "/")
    for place in home["village"]:
        paths.append(place["path"])
    for extra in ("/bosses/", "/multiplayer/", "/secret-rooms/"):
        paths.append(extra)
    ordered: list[str] = []
    for path in paths:
        if path not in ordered:
            ordered.append(path)
    return ordered


def file_for(dist: Path, url_path: str) -> Path:
    if url_path == "/":
        return dist / "index.html"
    if url_path.endswith(".html"):
        return dist / url_path.lstrip("/")
    return dist / url_path.strip("/") / "index.html"


def resolve(page: str, href: str) -> str | None:
    raw = href.split("#", 1)[0].split("?", 1)[0]
    if not raw or raw.startswith(("http://", "https://", "mailto:", "tel:", "//", "#")):
        return None
    if raw.startswith("/"):
        path = raw
    else:
        base = page if page.endswith("/") else page.rsplit("/", 1)[0] + "/"
        joined = posixpath.normpath(posixpath.join(base, raw))
        path = joined if joined.startswith("/") else "/" + joined
        if raw.endswith("/"):
            path = path.rstrip("/") + "/"
    if path != "/" and not path.endswith("/") and not path.endswith(".html"):
        path += "/"
    return path


def read_page(dist: Path, url_path: str) -> tuple[Path, str, Extract]:
    path = file_for(dist, url_path)
    text = path.read_text(encoding="utf-8")
    parser = Extract()
    parser.feed(text)
    return path, text, parser


def expected_h1(url_path: str) -> str | None:
    if url_path == "/":
        return load_json(ROOT / "content" / "home.json")["hero_h1"]
    if url_path == "/login.html":
        return "Log in"
    for page in (ROOT / "content").glob("*.json"):
        data = load_json(page)
        if data.get("path") == url_path and data.get("h1"):
            return data["h1"]
    return None


def check(dist: Path) -> list[str]:
    fails: list[str] = []
    if not (dist / "index.html").is_file():
        return [f"missing built home: {dist / 'index.html'}"]

    cfg = load_json(ROOT / "config" / "site.json")
    home = load_json(ROOT / "content" / "home.json")
    home_path, home_html, home_parsed = read_page(dist, "/")
    if home_parsed.h1 != [home["hero_h1"]]:
        fails.append(f"home h1 {home_parsed.h1!r} != {home['hero_h1']!r}")
    if "What Sephiria is" not in home_html:
        fails.append("home is missing the 'What Sephiria is' section")
    if "app/2436940" not in home_html:
        fails.append("home is missing the Sephiria Steam app link")

    resolved = {resolve("/", href) for href in home_parsed.hrefs}
    for label, href in cfg["nav"]:
        target = href if href.endswith("/") or href.endswith(".html") else href + "/"
        if target not in resolved:
            fails.append(f"primary nav missing {label} -> {target}")
    cta = resolve("/", home["cta_path"])
    if cta not in resolved or "Start beginner guide" not in home_html:
        fails.append("home welcome link does not open the beginner guide")

    for place in home["village"]:
        marker = f'destination destination--{place["id"]}'
        if marker not in home_html or place["path"] not in home_parsed.hrefs:
            fails.append(f"village door missing: {place['id']} {place['path']}")

    for url_path in journey_paths():
        page = file_for(dist, url_path)
        if not page.is_file():
            fails.append(f"journey page missing: {url_path}")
            continue
        _path, text, parsed = read_page(dist, url_path)
        want = expected_h1(url_path)
        if want is not None and parsed.h1 != [want]:
            fails.append(f"{url_path} h1 {parsed.h1!r} != {want!r}")
        if url_path != "/login.html" and len(parsed.h1) != 1:
            fails.append(f"{url_path} has {len(parsed.h1)} h1 headings")

    beginner = file_for(dist, "/beginner-guide/")
    if beginner.is_file():
        text = beginner.read_text(encoding="utf-8")
        parsed = Extract()
        parsed.feed(text)
        onward = {resolve("/beginner-guide/", href) for href in parsed.hrefs}
        if "Side Bag" not in text:
            fails.append("beginner guide lost the Side Bag rule")
        for nxt in ("/destiny-inscription/", "/builds/", "/hard-mode/"):
            if nxt not in onward:
                fails.append(f"beginner guide does not link onward to {nxt}")

    guides = file_for(dist, "/guides/")
    if guides.is_file():
        text = guides.read_text(encoding="utf-8")
        if "/beginner-guide/" not in text:
            fails.append("guides hub does not link to the beginner guide")

    login = file_for(dist, "/login.html")
    if login.is_file():
        text = login.read_text(encoding="utf-8")
        parsed = Extract()
        parsed.feed(text)
        if parsed.h1 != ["Log in"]:
            fails.append(f"login h1 {parsed.h1!r}")
        for node_id in ("notice", "account", "providers"):
            if node_id not in parsed.ids:
                fails.append(f"login page missing #{node_id}")
        if "/assets/login.js" not in parsed.scripts:
            fails.append("login page is not wired to /assets/login.js")
        if 'href="/"' not in text:
            fails.append("login page has no way back home")

    styles = dist / "assets" / "styles.css"
    theme = dist / "assets" / "theme.css"
    village = dist / "assets" / "img" / "village.png"
    capsule = dist / "assets" / "img" / "capsule.jpg"
    login_js = dist / "assets" / "login.js"
    if not styles.is_file() or "box-sizing" not in styles.read_text(encoding="utf-8"):
        fails.append("styles.css missing or not the site stylesheet")
    if not theme.is_file() or "--accent:" not in theme.read_text(encoding="utf-8"):
        fails.append("theme.css missing the accent token")
    if not village.is_file() or not village.read_bytes().startswith(b"\x89PNG"):
        fails.append("village.png is not a PNG")
    if not capsule.is_file() or not capsule.read_bytes().startswith(b"\xff\xd8"):
        fails.append("capsule.jpg is not a JPEG")
    if not login_js.is_file() or "/api/auth/start?provider=" not in login_js.read_text(encoding="utf-8"):
        fails.append("login.js is missing the provider start URL")
    if not (dist / "assets" / "login.css").is_file():
        fails.append("login.css missing")
    return fails


def snapshot(dest: Path) -> None:
    for url_path in journey_paths():
        src = file_for(DIST, url_path)
        target = file_for(dest, url_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    for rel in ASSETS:
        src = DIST / rel
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)


def self_test() -> int:
    base = check(DIST)
    if base:
        print("FAIL self-test setup; built dist is not clean:")
        for item in base:
            print(" ", item)
        return 1
    mutations = {
        "home h1": lambda root: _replace(
            file_for(root, "/"),
            load_json(ROOT / "content" / "home.json")["hero_h1"],
            "Broken heading",
        ),
        "side bag": lambda root: _replace(
            file_for(root, "/beginner-guide/"), "Side Bag", "Side Pouch"
        ),
        "login script": lambda root: _replace(
            file_for(root, "/login.html"),
            'src="/assets/login.js"',
            'src="/assets/missing.js"',
        ),
        "village png": lambda root: (root / "assets" / "img" / "village.png").write_bytes(b"GIF89a"),
    }
    failed = 0
    for name, mutate in mutations.items():
        tmp = Path(tempfile.mkdtemp(prefix="sephiria-smoke-"))
        try:
            snapshot(tmp)
            mutate(tmp)
            found = check(tmp)
            if not found:
                failed += 1
                print(f"FAIL counterexample passed: {name}")
            else:
                print(f"PASS counterexample failed ({name}): {found[0]}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if failed:
        return 1
    print("PASS sephiria smoke self-test")
    return 0


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"self-test could not find {old!r} in {path}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    fails = check(DIST)
    if fails:
        print(f"FAIL sephiria smoke ({len(fails)})")
        for item in fails:
            print(" ", item)
        return 1
    print(
        "PASS sephiria smoke: nav, village doors, beginner onward links, "
        "login shell, and key assets"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
