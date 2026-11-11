#!/usr/bin/env python3
"""Decide which product CI job has work in a diff.

Sephiria and Warhammer stay on separate path sets so a change to one
product does not run the other product's build. Shared probe/CI files
run both jobs. The GitHub jobs themselves always run and report a
status: a product with no matching paths exits green without building.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Directory prefixes end with "/". Anything else is an exact path.
SEPHIRIA = (
    "build.py",
    "ads.txt",
    "robots.txt",
    "favicon.ico",
    "login.html",
    "wrangler.jsonc",
    "131fc577a3d44393b0a07c68875a1462.txt",
    "config/",
    "content/",
    "assets/",
    "functions/",
    "extra_sites/phantom-blade-zero/",
    "extra_sites/shrek-2-remastered/",
    "tools/check_seo_consistency.py",
    "tools/check_village.py",
    "tools/check_guide_visuals.py",
    "tools/swap_test.py",
    "tools/smoke_sephiria.py",
    "tools/smoke_login.mjs",
    "tools/smoke_dom.mjs",
    "tools/probe_live.py",
    "tools/ci_paths.py",
    "tools/ci_sephiria.sh",
    "tools/make_favicon.py",
    "tools/make_svg_figures.py",
    "tools/export_content.py",
    ".github/workflows/ci.yml",
    ".github/workflows/deploy.yml",
)

WARHAMMER = (
    "extra_sites/warhammer-survivors/",
    "extra_sites/_root_files/",
    "tools/build_standalone_wh.py",
    "tools/build_wh_codex.py",
    "tools/make_favicon_wh.py",
    "tools/smoke_warhammer.py",
    "tools/smoke_codex.mjs",
    "tools/smoke_dom.mjs",
    "tools/probe_live.py",
    "tools/ci_paths.py",
    "tools/ci_warhammer.sh",
    ".github/workflows/ci.yml",
    ".github/workflows/deploy-warhammer.yml",
)

PRODUCTS = {"sephiria": SEPHIRIA, "warhammer": WARHAMMER}


def matches(path: str, prefixes: tuple[str, ...]) -> bool:
    rel = path.replace("\\", "/")
    if rel.startswith("./"):
        rel = rel[2:]
    for prefix in prefixes:
        if prefix.endswith("/"):
            if rel.startswith(prefix):
                return True
        elif rel == prefix:
            return True
    return False


def product_affected(paths: list[str], product: str) -> bool:
    prefixes = PRODUCTS[product]
    return any(matches(path, prefixes) for path in paths)


def changed_files(base: str, head: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def self_test() -> int:
    cases = [
        (["content/home.json"], "sephiria", True),
        (["content/home.json"], "warhammer", False),
        (["extra_sites/warhammer-survivors/guide/index.html"], "sephiria", False),
        (["extra_sites/warhammer-survivors/guide/index.html"], "warhammer", True),
        (["extra_sites/phantom-blade-zero/index.html"], "sephiria", True),
        (["extra_sites/phantom-blade-zero/index.html"], "warhammer", False),
        (["extra_sites/shrek-2-remastered/index.html"], "sephiria", True),
        (["docs/scaffolds/game-guide-site/README.md"], "sephiria", False),
        (["docs/scaffolds/game-guide-site/README.md"], "warhammer", False),
        ([".github/workflows/ci.yml"], "sephiria", True),
        ([".github/workflows/ci.yml"], "warhammer", True),
        ([".github/workflows/deploy.yml"], "sephiria", True),
        ([".github/workflows/deploy.yml"], "warhammer", False),
        ([".github/workflows/deploy-warhammer.yml"], "sephiria", False),
        ([".github/workflows/deploy-warhammer.yml"], "warhammer", True),
        (["tools/probe_live.py"], "sephiria", True),
        (["tools/probe_live.py"], "warhammer", True),
        (["tools/build_standalone_wh.py"], "sephiria", False),
        (["build.py"], "warhammer", False),
        (["build.py"], "sephiria", True),
        ([], "sephiria", False),
        ([], "warhammer", False),
    ]
    failed = 0
    for paths, product, expected in cases:
        got = product_affected(paths, product)
        if got != expected:
            failed += 1
            print(f"FAIL {product} {paths}: expected {expected} got {got}")
    # A near-name must not leak into the other product.
    if matches("tools/build_standalone_wh.py", SEPHIRIA):
        failed += 1
        print("FAIL sephiria matched the Warhammer build script")
    if matches("extra_sites/warhammer-survivors-notes/index.html", WARHAMMER):
        failed += 1
        print("FAIL warhammer prefix matched a sibling directory")
    if failed:
        print(f"FAIL ci_paths self-test ({failed})")
        return 1
    print(f"PASS ci_paths self-test ({len(cases)} cases, including cross-product counterexamples)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=sorted(PRODUCTS))
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.product or not args.base or not args.head:
        parser.error("--product, --base, and --head are required")
    try:
        files = changed_files(args.base, args.head)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or "git diff failed\n")
        return 1
    run = product_affected(files, args.product)
    # GitHub step output. Human detail goes to stderr so it is not a key.
    print(f"run={'true' if run else 'false'}")
    sys.stderr.write(
        f"{args.product}: {'run' if run else 'skip'} ({len(files)} changed files)\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
