#!/usr/bin/env python3
"""One-shot: peel generated HTML into content/*.json. Safe to re-run."""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"

META = {
    "/guides/": {
        "layout": "hub",
        "hub": "guides",
        "h1": "Sephiria guide hub",
        "meta": "Maps to searches like sephiria wiki / sephiria guide.",
        "intro": "Looking for a Sephiria wiki-style hub? Use this index. Pages answer real search intents from Google Suggest / Trends / SimilarWeb research—not a dump of every noun in the game.",
        "crumbs": [["Home", "/"], ["Guides", ""]],
        "order": 10,
    },
    "/beginner-guide/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Beginner", ""]],
        "in_guides": True,
        "guides_label": "Beginner guide",
        "guides_em": "First run",
        "home_start": {"title": "Beginner Guide", "em": "First-run priorities and common traps."},
        "order": 20,
    },
    "/builds/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Builds", ""]],
        "in_guides": True,
        "guides_label": "Builds",
        "guides_em": "Combo focus",
        "home_start": {"title": "Builds", "em": "Commit to one or two combo tags."},
        "order": 30,
    },
    "/builds/companion/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Builds", "/builds/"], ["Companion", ""]],
        "in_guides": True,
        "guides_label": "Companion build",
        "guides_em": "Summoner route",
        "home_also": {"title": "Companion build", "em": "Summons / Ballista focus"},
        "order": 31,
    },
    "/weapons/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Weapons", ""]],
        "in_guides": True,
        "guides_label": "Weapons",
        "guides_em": "Six branches",
        "home_start": {"title": "Weapons", "em": "Six branches, beginner picks, unlock notes."},
        "order": 40,
    },
    "/destiny-inscription/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Destiny Inscription", ""]],
        "in_guides": True,
        "guides_label": "Destiny Inscription",
        "guides_em": "Permanent tree",
        "home_start": {"title": "Destiny Inscription", "em": "Permanent sapphire tree and talents."},
        "order": 50,
    },
    "/hard-mode/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Hard Mode", ""]],
        "in_guides": True,
        "guides_label": "Hard Mode",
        "guides_em": "Unlock Root’s Retreat",
        "home_also": {"title": "Hard Mode unlock", "em": "Root’s Retreat after Chapter 2"},
        "order": 55,
    },
    "/artifacts/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Artifacts", ""]],
        "in_guides": True,
        "guides_label": "Artifacts & Tablets",
        "guides_em": "Inventory grid",
        "order": 60,
    },
    "/bosses/": {
        "layout": "hub",
        "hub": "bosses",
        "child_prefix": "/bosses/",
        "h1": "Sephiria bosses",
        "meta": "Navigation page for boss intents.",
        "intro": "Boss pages will expand as we verify more pattern notes. Start with the high-search fights:",
        "crumbs": [["Home", "/"], ["Bosses", ""]],
        "in_guides": True,
        "guides_label": "Bosses",
        "guides_em": "Erma · Final",
        "order": 70,
    },
    "/bosses/erma/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Bosses", "/bosses/"], ["Erma", ""]],
        "hub_label": "Erma — Mad Scientist",
        "hub_em": "Floor 3 library line",
        "home_also": {"title": "Erma boss guide", "em": "Mad Scientist · Floor 3"},
        "order": 71,
    },
    "/bosses/final/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Bosses", "/bosses/"], ["Final boss", ""]],
        "hub_label": "Final boss (Qliphoth line)",
        "hub_em": "Chapter 6 / endgame",
        "order": 72,
    },
    "/multiplayer/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Multiplayer", ""]],
        "in_guides": True,
        "guides_label": "Multiplayer",
        "guides_em": "Co-op lobby",
        "home_also": {"title": "Multiplayer / co-op", "em": "Stone-wall lobby + invite notes"},
        "order": 80,
    },
    "/secret-rooms/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Secret rooms", ""]],
        "in_guides": True,
        "guides_label": "Secret rooms",
        "guides_em": "Cracks & lore rooms",
        "home_also": {"title": "Secret rooms", "em": "Cracked walls & post-Erma lore room"},
        "order": 90,
    },
    "/costumes/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Costumes", ""]],
        "in_guides": True,
        "guides_label": "Costumes",
        "guides_em": "Unlocks",
        "home_also": {"title": "Costumes", "em": "Starter skins & hidden unlocks"},
        "order": 100,
    },
    "/items/scythe/": {
        "layout": "article",
        "crumbs": [["Home", "/"], ["Weapons", "/weapons/"], ["Scythe", ""]],
        "in_guides": True,
        "guides_label": "Scythe",
        "guides_em": "Drifa / Blizzard Scythe",
        "home_also": {"title": "How to get the Scythe", "em": "Blizzard Scythe via Drifa—not a 6th weapon"},
        "order": 110,
    },
}


def slug(path: str) -> str:
    if path == "/":
        return "home"
    return path.strip("/").replace("/", "-")


def parse_article(html: str) -> dict:
    title = unescape(re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip())
    desc = unescape(re.search(r'name="description" content="(.*?)"', html).group(1))
    can = re.search(r'rel="canonical" href="https://sephiria-guide.com([^"]*)"', html).group(1)
    h1 = unescape(re.search(r'<h1 class="page-title">(.*?)</h1>', html).group(1).strip())
    meta = unescape(re.search(r'<p class="meta-line">(.*?)</p>', html).group(1).strip())
    body_m = re.search(
        r'<p class="meta-line">.*?</p>\s*(.*?)\s*<section class="sources">',
        html,
        re.S,
    )
    body = body_m.group(1).strip() if body_m else ""
    src_sec = re.search(r'<section class="sources">.*?</section>', html, re.S)
    sources = []
    if src_sec:
        sources = [
            [unescape(re.sub(r"<[^>]+>", "", name).strip()), href]
            for href, name in re.findall(
                r'<li><a href="([^"]+)"[^>]*>(.*?)</a></li>', src_sec.group(0)
            )
        ]
    return {
        "path": can if can.endswith("/") or can == "/" else can + "/",
        "title": title,
        "description": desc,
        "h1": h1,
        "meta": meta,
        "body": body,
        "sources": sources,
    }


def main() -> None:
    CONTENT.mkdir(parents=True, exist_ok=True)
    home = {
        "path": "/",
        "layout": "home",
        "title": "Sephiria Guide — Builds, Weapons, Wiki Tips",
        "description": "Fan guides for Sephiria: beginner tips, builds, weapons, Destiny Inscription, bosses, co-op, and secret rooms. Updated for the 1.0 release.",
        "hero_kicker": "Fan guides · Updated for Sephiria 1.0",
        "hero_h1": "Sephiria Guide",
        "lede": "Builds, weapons, Destiny Inscription, bosses, and co-op notes distilled from Steam and cross-checked sources—not AI filler.",
        "cta_label": "Start beginner guide",
        "cta_path": "/beginner-guide/",
        "what_h2": "What Sephiria is",
        "what_html": "<p>Sephiria is a top-down action roguelite from Team Horay (also known for Dungreed). You descend floors, upgrade weapons at anvils, and build power through an Artifact + Tablet inventory grid. Full release landed <strong>July 31, 2026</strong> after Early Access; Steam lists six chapters, six weapon lines, and online co-op for up to four players.</p>\n      <div class=\"note\">This site is English-first P0 coverage for sephiria-guide.com. Patch-sensitive tips note when they come from older Steam Community guides.</div>",
        "order": 0,
    }
    (CONTENT / "home.json").write_text(json.dumps(home, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for path, extra in META.items():
        html_path = ROOT / ("index.html" if path == "/" else Path(path.strip("/")) / "index.html")
        if not html_path.exists():
            raise SystemExit(f"missing {html_path}")
        parsed = parse_article(html_path.read_text(encoding="utf-8"))
        if extra.get("layout") == "hub":
            page = {
                "path": parsed["path"],
                "layout": "hub",
                "hub": extra["hub"],
                "title": parsed["title"],
                "description": parsed["description"],
                "h1": extra.get("h1") or parsed["h1"],
                "meta": extra.get("meta") or parsed["meta"],
                "intro": extra["intro"],
                "crumbs": extra["crumbs"],
                "sources": parsed["sources"],
                "order": extra["order"],
            }
            if extra.get("child_prefix"):
                page["child_prefix"] = extra["child_prefix"]
            for k in ("in_guides", "guides_label", "guides_em"):
                if k in extra:
                    page[k] = extra[k]
        else:
            page = {**parsed, **extra}
        out = CONTENT / f"{slug(path)}.json"
        out.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
