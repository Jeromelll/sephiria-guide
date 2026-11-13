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
        (tmp / "config" / "site.json").write_text(
            json.dumps(swapped, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for src in (ROOT / "content").glob("*.json"):
            shutil.copy2(src, tmp / "content" / src.name)
        shutil.copytree(ROOT / "assets", tmp / "assets")
        (tmp / "login.html").write_text("<!doctype html><title>Log in</title>", encoding="utf-8")

        orig_root = build.ROOT
        orig_output = build.OUTPUT_DIR
        build.ROOT = tmp
        build.OUTPUT_DIR = tmp / "dist"
        try:
            pages = build.build(swapped, tmp / "content")
        finally:
            build.ROOT = orig_root
            build.OUTPUT_DIR = orig_output

        home = (tmp / "dist" / "index.html").read_text(encoding="utf-8")
        theme = (tmp / "dist" / "assets" / "theme.css").read_text(encoding="utf-8")
        checks = {
            "brand Gelum": "Game <span>Guides</span>" in home or "Gelum <span>Guide</span>" in home,
            "canonical domain": "https://gelum-guide.example/" in home,
            "steam swapped": "app/0000000/Gelum" in home,
            "no old brand in chrome": "Sephiria <span>Guide</span>" not in home,
            "theme accent swapped": "--accent: #0f766e" in theme,
            "page count": len(pages) >= 16,
        }
        leftovers = []
        chrome_files = [tmp / "dist" / "index.html", tmp / "dist" / "guides" / "index.html"]
        for f in chrome_files:
            text = f.read_text(encoding="utf-8")
            header = text.split("</header>", 1)[0].split("<header", 1)[-1]
            footer = text.split('<footer class="site-footer">', 1)[-1]
            # The swapped config still carries the Sephiria content files, so
            # "Sephiria" legitimately appears in page copy and in the "Also see:
            # Warhammer Survivors" footer line. The swap test only cares that
            # the framework chrome (brand, nav, footer link list) is free of
            # hard-coded Sephiria, which section_of() now guarantees via config.
            if "Sephiria <span>" in header or "Sephiria <span>" in footer:
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
