#!/usr/bin/env python3
"""Check that the built village links reach the intended real guide pages."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VillageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.destinations = []
        self.resources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "destination" in attrs.get("class", "").split():
            self.destinations.append(attrs["href"])
        if tag in ("img", "script", "link"):
            url = attrs.get("src") or attrs.get("href", "")
            if url.startswith("assets/"):
                self.resources.append(url.split("?", 1)[0])


if __name__ == "__main__":
    parser = VillageLinks()
    parser.feed((ROOT / "dist/index.html").read_text())
    expected = {"/beginner-guide/", "/destiny-inscription/", "/weapons/",
                "/builds/", "/wishing-fountain/", "/hard-mode/"}
    assert len(parser.destinations) == 6 and set(parser.destinations) == expected
    for url in parser.destinations:
        page = ROOT / "dist" / url.strip("/") / "index.html"
        assert page.is_file(), f"Missing guide: {url}"
        assert "village.css" not in page.read_text(), f"Home styling leaked into {url}"
    assert "assets/img/village.png" in parser.resources
    for url in parser.resources:
        assert (ROOT / "dist" / url).is_file(), f"Missing resource: {url}"
    print("PASS: six distinct guide destinations, local resources, isolated home styling")
