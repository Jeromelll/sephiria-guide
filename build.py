#!/usr/bin/env python3
"""Framework layer: read config + content files, write static HTML.

Add or delete a file in content/ and rebuild — nav hubs, home cards,
and sitemap follow automatically. Game-specific strings live in
config/site.json and content/*.json, not in this file.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "site.json"
CONTENT_DIR = ROOT / "content"


def load_config(path: Path = CONFIG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pages(content_dir: Path = CONTENT_DIR) -> list[dict]:
    pages = []
    for p in sorted(content_dir.glob("*.json")):
        if p.name.startswith("_"):
            continue
        page = json.loads(p.read_text(encoding="utf-8"))
        page["_file"] = p.name
        pages.append(page)
    pages.sort(key=lambda x: (x.get("order", 500), x.get("path", "")))
    return pages


def depth_of(path: str) -> int:
    if path == "/":
        return 0
    return len([p for p in path.strip("/").split("/") if p])


def css_href(depth: int, name: str) -> str:
    return "../" * depth + f"assets/{name}"


def link(depth: int, path: str) -> str:
    if path == "/":
        return "../" * depth if depth else "./"
    return "../" * depth + path.strip("/") + "/"


def write_theme(cfg: dict) -> None:
    t = cfg["theme"]
    css = f"""/* Generated from config/site.json — do not edit by hand. */
:root {{
  --bg: {t["bg"]};
  --bg-deep: {t["bg_deep"]};
  --ink: {t["ink"]};
  --muted: {t["muted"]};
  --line: {t["line"]};
  --accent: {t["accent"]};
  --accent-ink: {t["accent_ink"]};
  --panel: {t["panel"]};
  --max: 720px;
  --wide: 1040px;
}}
"""
    (ROOT / "assets" / "theme.css").write_text(css, encoding="utf-8")


def shell(cfg: dict, *, title: str, description: str, depth: int, path: str, body: str) -> str:
    nav_html = []
    for label, href in cfg["nav"]:
        current = ' aria-current="page"' if href.rstrip("/") == path.rstrip("/") else ""
        nav_html.append(f'<a href="{link(depth, href)}"{current}>{label}</a>')
    game_link = f'<a href="{cfg["links"]["steam"]}">{cfg["game_name"]}</a>'
    footer_line = (
        cfg["footer_line"]
        .replace("{game_link}", game_link)
        .replace("{developer}", cfg["developer"])
    )
    return f"""<!DOCTYPE html>
<html lang="{cfg["lang"]}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <meta name="keywords" content="{cfg["seo_keywords"]}" />
  <link rel="canonical" href="{cfg["domain"]}{path}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{css_href(depth, "theme.css")}" />
  <link rel="stylesheet" href="{css_href(depth, "styles.css")}" />
  <script src="{css_href(depth, "analytics.js")}" defer></script>
</head>
<body>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="brand" href="{link(depth, '/')}">{cfg["brand_name"]} <span>{cfg["brand_suffix"]}</span></a>
      <nav class="nav">{''.join(nav_html)}</nav>
    </div>
  </header>
  <main>
{body}
  </main>
  <footer class="site-footer">
    <div class="narrow">
      <p>{footer_line}</p>
      <p>{cfg["footer_facts"]}</p>
      <p><a href="{link(depth, '/guides/')}">All guides</a> · <a href="{link(depth, '/about/')}">About</a> · <a href="{link(depth, '/privacy/')}">Privacy</a> · Updated {cfg["updated"]}</p>
    </div>
  </footer>
</body>
</html>
"""


def article(depth: int, crumbs: list, title: str, meta: str, content: str, sources: list) -> str:
    crumb_html = " / ".join(
        (f'<a href="{link(depth, href)}">{label}</a>' if href else label) for label, href in crumbs
    )
    sources_html = ""
    if sources:
        src = "".join(f'<li><a href="{u}" rel="noopener">{n}</a></li>' for n, u in sources)
        sources_html = f"""
    <section class="sources">
      <h2>Sources</h2>
      <ul>{src}</ul>
    </section>"""
    return f"""
  <div class="narrow">
    <p class="breadcrumbs">{crumb_html}</p>
    <h1 class="page-title">{title}</h1>
    <p class="meta-line">{meta}</p>
    {content}{sources_html}
  </div>
"""


def guide_list(pages: list[dict], *, kind: str) -> str:
    items = []
    if kind == "guides":
        rows = [p for p in pages if p.get("in_guides")]
        for p in rows:
            items.append(
                f'<a href="{p["path"]}"><strong>{p.get("guides_label") or p.get("h1")}</strong><em>{p.get("guides_em", "")}</em></a>'
            )
    elif kind == "bosses":
        rows = [p for p in pages if p.get("path", "").startswith("/bosses/") and p.get("layout") == "article"]
        for p in rows:
            rel = "./" + p["path"].strip("/").split("/")[-1] + "/"
            items.append(
                f'<a href="{rel}"><strong>{p.get("hub_label") or p.get("h1")}</strong><em>{p.get("hub_em", "")}</em></a>'
            )
    elif kind == "home_start":
        rows = [p for p in pages if p.get("home_start")]
        for p in rows:
            card = p["home_start"]
            items.append(
                f'<a class="start-link" href="{p["path"]}"><strong>{card["title"]}</strong><span>{card["em"]}</span></a>'
            )
        return "\n        ".join(items)
    elif kind == "home_also":
        rows = [p for p in pages if p.get("home_also")]
        for p in rows:
            card = p["home_also"]
            items.append(
                f'<a href="{p["path"]}"><strong>{card["title"]}</strong><em>{card["em"]}</em></a>'
            )
        items.append('<a href="/guides/"><strong>Full guide index</strong><em>Wiki-style navigation</em></a>')
    return "\n  ".join(items)


def home_body(home: dict, pages: list[dict], cfg: dict) -> str:
    start = guide_list(pages, kind="home_start")
    also = guide_list(pages, kind="home_also")
    return f"""
  <section class="hero">
    <div class="wrap">
      <p class="hero-kicker">{home["hero_kicker"]}</p>
      <h1>{home["hero_h1"]}</h1>
      <p class="lede">{home["lede"]}</p>
      <div class="cta-row">
        <a class="btn btn-primary" href="{link(0, home["cta_path"])}">{home["cta_label"]}</a>
        <a class="btn btn-ghost" href="{cfg["links"]["steam"]}" rel="noopener">Steam page</a>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>{home["what_h2"]}</h2>
      {home["what_html"]}
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>Start here</h2>
      <div class="grid-4">
        {start}
      </div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>Also covered</h2>
      <div class="guide-list">
        {also}
      </div>
    </div>
  </section>
"""


def write_page(cfg: dict, path: str, title: str, description: str, body: str) -> None:
    depth = depth_of(path)
    html = shell(cfg, title=title, description=description, depth=depth, path=path, body=body)
    out = ROOT / ("index.html" if path == "/" else Path(path.strip("/")) / "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out.relative_to(ROOT))


def write_sitemap(cfg: dict, pages: list[dict]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    listed = [p for p in pages if not p.get("sitemap_exclude")]
    for i, page in enumerate(listed):
        pri = "1.0" if page["path"] == "/" else ("0.9" if i < 5 else "0.8")
        if page.get("layout") == "legal":
            pri = "0.3"
        lines.append(
            f'  <url><loc>{cfg["domain"]}{page["path"]}</loc><changefreq>weekly</changefreq><priority>{pri}</priority></url>'
        )
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote sitemap.xml", len(listed), "urls")


def write_404(cfg: dict) -> None:
    body = """
  <div class="narrow">
    <h1 class="page-title">Page not found</h1>
    <p class="meta-line">That URL is not a guide on this site.</p>
    <p><a href="/">Back to the Sephiria 1.0 guide</a> · <a href="/guides/">All guides</a></p>
  </div>
"""
    html = shell(
        cfg,
        title="404 — Page not found | Sephiria Guide",
        description="This URL is not a page on sephiria-guide.com.",
        depth=0,
        path="/404.html",
        body=body,
    )
    # Avoid claiming a fake canonical for a missing URL.
    html = html.replace(
        f'<link rel="canonical" href="{cfg["domain"]}/404.html" />',
        f'<meta name="robots" content="noindex" />',
    )
    (ROOT / "404.html").write_text(html, encoding="utf-8")
    print("wrote 404.html")


def write_ads_txt() -> None:
    # Plain text so SPA fallback cannot serve homepage HTML here.
    text = (
        "# sephiria-guide.com — no ad network authorized yet.\n"
        "# When ads go live, publisher lines will be listed below.\n"
    )
    (ROOT / "ads.txt").write_text(text, encoding="utf-8")
    print("wrote ads.txt")


def write_redirects() -> None:
    # Override Cloudflare Pages SPA soft-404 (/* → index.html 200).
    text = "/* /404.html 404\n"
    (ROOT / "_redirects").write_text(text, encoding="utf-8")
    print("wrote _redirects")


def build(cfg: dict | None = None, content_dir: Path = CONTENT_DIR) -> list[dict]:
    cfg = cfg or load_config()
    pages = load_pages(content_dir)
    write_theme(cfg)
    by_path = {p["path"]: p for p in pages}

    for page in pages:
        layout = page.get("layout", "article")
        if layout == "home":
            write_page(cfg, page["path"], page["title"], page["description"], home_body(page, pages, cfg))
        elif layout == "hub":
            kind = page.get("hub", "guides")
            listing = f'<div class="guide-list">\n  {guide_list(pages, kind=kind)}\n</div>'
            body = article(
                depth_of(page["path"]),
                page.get("crumbs") or [("Home", "/"), (page.get("h1", "Guides"), "")],
                page["h1"],
                page["meta"],
                f'<p>{page["intro"]}</p>\n{listing}',
                page.get("sources") or [],
            )
            write_page(cfg, page["path"], page["title"], page["description"], body)
        else:
            body = article(
                depth_of(page["path"]),
                page.get("crumbs") or [("Home", "/"), (page.get("h1", ""), "")],
                page["h1"],
                page["meta"],
                page.get("body") or "",
                page.get("sources") or [],
            )
            write_page(cfg, page["path"], page["title"], page["description"], body)

    write_sitemap(cfg, pages)
    write_404(cfg)
    write_ads_txt()
    write_redirects()
    return pages


if __name__ == "__main__":
    build()
    print("done")
