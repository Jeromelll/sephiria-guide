#!/usr/bin/env python3
"""Check guide coverage, built images, and safe local SVG illustrations."""
import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))


if __name__ == "__main__":
    pages = [json.loads(p.read_text()) for p in (ROOT / "content").glob("*.json")]
    expected = {p["path"] for p in pages if p.get("layout") in ("article", "hub")
                and not p["path"].startswith("/fm27")}
    visuals = json.loads((ROOT / "config/guide-visuals.json").read_text())
    assert set(visuals) == expected, "Visual coverage does not match Sephiria guides"
    for route, media in visuals.items():
        page = next(p for p in pages if p["path"] == route)
        marker = media["illustration"].get("after")
        assert not marker or marker in page.get("body", ""), (route, marker)
        html = (ROOT / "dist" / route.strip("/") / "index.html").read_text()
        parser = Images()
        parser.feed(html)
        assert len(parser.images) >= 2, f"Missing cover/body image: {route}"
        for kind in ("cover", "illustration"):
            data = media[kind]
            assert data["alt"] and data["caption"]
            assert any(urljoin(route, i["src"]) == "/" + data["src"] for i in parser.images)
            file = ROOT / "dist" / data["src"]
            assert file.is_file(), file
            if file.suffix == ".svg":
                root = ET.parse(file).getroot()
                assert root.find("{http://www.w3.org/2000/svg}title") is not None
                for node in root.iter():
                    assert node.tag.split("}")[-1] not in ("script", "foreignObject")
                    assert not any(k.startswith("on") or "href" in k for k in node.attrib)
    home = (ROOT / "dist/index.html").read_text()
    assert 'class="village-party"' in home and 'src="assets/img/capsule.jpg"' in home
    print(f"PASS: {len(expected)} illustrated guides, local images, SVG safety, official trio on home")
