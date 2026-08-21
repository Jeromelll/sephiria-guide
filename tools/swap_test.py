#!/usr/bin/env python3
"""关卡7 replacement test: swap config only, rebuild to a temp dir, report leftovers."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


def main() -> int:
    cfg = build.load_config()
    swapped = json.loads(json.dumps(cfg))
    swapped.update(
        {
            "game_name": "Gelum",
            "brand_name": "Gelum",
            "brand_suffix": "Guide",
            "site_name": "Gelum Guide",
            "domain": "https://gelum-guide.example",
            "kicker": "Gelum 1.0 fan guide",
            "seo_keywords": "gelum, gelum wiki, gelum builds",
        }
    )
    swapped["links"]["steam"] = "https://store.steampowered.com/app/0000000/Gelum/"
    swapped["theme"]["accent"] = "#0f766e"
    swapped["theme"]["accent_ink"] = "#115e59"

    tmp = Path(tempfile.mkdtemp(prefix="gelum-swap-"))
    try:
        (tmp / "config").mkdir()
        (tmp / "content").mkdir()
        (tmp / "assets").mkdir()
        (tmp / "config" / "site.json").write_text(
            json.dumps(swapped, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for src in (ROOT / "content").glob("*.json"):
            shutil.copy2(src, tmp / "content" / src.name)
        shutil.copy2(ROOT / "assets" / "styles.css", tmp / "assets" / "styles.css")
        shutil.copy2(ROOT / "assets" / "analytics.js", tmp / "assets" / "analytics.js")

        orig_root = build.ROOT
        build.ROOT = tmp
        try:
            pages = build.build(swapped, tmp / "content")
        finally:
            build.ROOT = orig_root

        home = (tmp / "index.html").read_text(encoding="utf-8")
        theme = (tmp / "assets" / "theme.css").read_text(encoding="utf-8")
        checks = {
            "brand Gelum": "Gelum <span>Guide</span>" in home,
            "canonical domain": "https://gelum-guide.example/" in home,
            "steam swapped": "app/0000000/Gelum" in home,
            "no old brand in chrome": "Sephiria <span>Guide</span>" not in home,
            "theme accent swapped": "--accent: #0f766e" in theme,
            "page count": len(pages) >= 16,
        }
        leftovers = []
        chrome_files = [tmp / "index.html", tmp / "guides" / "index.html"]
        for f in chrome_files:
            text = f.read_text(encoding="utf-8")
            header = text.split("</header>", 1)[0].split("<header", 1)[-1]
            footer = text.split('<footer class="site-footer">', 1)[-1]
            if "Sephiria" in header or "Sephiria" in footer:
                leftovers.append(f"{f.name}: Sephiria still in header/footer")

        print("swap test dir:", tmp)
        for k, ok in checks.items():
            print(("PASS" if ok else "FAIL"), k)
        if leftovers:
            print("LEFTOVER in framework chrome:")
            for line in leftovers:
                print(" ", line)
        else:
            print("PASS framework chrome has no leftover Sephiria")
        print(
            "NOTE content layer still says Sephiria — expected. "
            "A second game needs new content files / the 关卡8 prompt, not a code rewrite."
        )
        return 0 if all(checks.values()) and not leftovers else 1
    finally:
        # keep dir for inspection; comment shutil.rmtree if debugging
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
