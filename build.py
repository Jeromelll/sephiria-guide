#!/usr/bin/env python3
"""Framework layer: read config + content files, write static HTML.

Add or delete a file in content/ and rebuild — nav hubs, home cards,
and sitemap follow automatically. Game-specific strings live in
config/site.json and content/*.json, not in this file.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "site.json"
CONTENT_DIR = ROOT / "content"
OUTPUT_DIR = ROOT / "dist"
EXTRA_SITES_DIR = ROOT / "extra_sites"
# Sub-sites that now live on their own apex domain. Keys are directory names under
# extra_sites/; values are the apex they moved to.
MOVED_SITES = {"warhammer-survivors": "warhammersurvivors.com"}


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
    if path.endswith(".html"):
        return "/" + path.lstrip("/")
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
  --shadow: {t.get("shadow", "rgba(26, 36, 51, 0.08)")};
  --shadow-accent: {t.get("shadow_accent", "rgba(232, 93, 4, 0.18)")};
  --max: 720px;
  --wide: 1040px;
}}
"""
    (OUTPUT_DIR / "assets" / "theme.css").write_text(css, encoding="utf-8")


def shell(cfg: dict, *, title: str, description: str, depth: int, path: str, body: str, jsonld: list | None = None) -> str:
    is_home = path == "/"
    home_style = ('\n  <link rel="stylesheet" href="assets/village.css?v=' +
                  hashlib.md5((ROOT / "assets" / "village.css").read_bytes()).hexdigest()[:8] + '" />') if is_home else ""
    ld_html = "".join(
        f'\n  <script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>' for obj in (jsonld or [])
    )
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
  <meta property="og:image" content="{cfg["domain"]}/assets/img/capsule.jpg" />
  <link rel="icon" href="{css_href(depth, "favicon.svg")}" type="image/svg+xml" />
  <link rel="icon" type="image/png" sizes="32x32" href="{css_href(depth, "favicon-32x32.png")}" />
  <link rel="icon" type="image/png" sizes="16x16" href="{css_href(depth, "favicon-16x16.png")}" />
  <link rel="apple-touch-icon" href="{css_href(depth, "apple-touch-icon.png")}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400..700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{css_href(depth, "theme.css")}?v={THEME_VERSION}" />
  <link rel="stylesheet" href="{css_href(depth, "styles.css")}?v={CSS_VERSION}" />
  <script src="{css_href(depth, "analytics.js")}" defer></script>{home_style}{ld_html}
</head>
<body{' class="village-home"' if is_home else ''}>
  <a class="skip-link" href="#content">Skip to content</a>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="brand" href="{link(depth, '/')}">{cfg["brand_name"]} <span>{cfg["brand_suffix"]}</span></a>
      <nav class="nav" aria-label="Primary">{''.join(nav_html)}</nav>
    </div>
  </header>
  <main id="content">
{body}
  </main>
  <footer class="site-footer">
    <div class="narrow">
      <p>{footer_line}</p>
      <p>{cfg["footer_facts"]}</p>
      <p><a href="{link(depth, '/guides/')}">All guides</a> · <a href="{link(depth, '/multiplayer/')}">Co-op</a> · <a href="{link(depth, '/bosses/')}">Bosses</a> · <a href="{link(depth, '/about/')}">About</a> · <a href="{link(depth, '/privacy/')}">Privacy</a> · <a href="{link(depth, '/contact/')}">Contact</a> · <a href="{link(depth, '/editorial-policy/')}">Editorial</a> · Updated {cfg["updated"]}</p>
      <p class="other-games">Other games we cover: <a href="{link(depth, '/phantom-blade-zero/')}">Phantom Blade Zero</a> · <a href="{link(depth, '/warhammer-survivors/')}">Warhammer Survivors</a> · <a href="{link(depth, '/fm27/')}">Football Manager 27</a></p>
    </div>
  </footer>
</body>
</html>
"""


def stuck_prompt(depth: int) -> str:
    """Light post-read ask — high-intent moment, same idea as Zigpoll's one question."""
    contact = link(depth, "/contact/")
    return f"""
    <p class="stuck-prompt">Still stuck? Tell us which step failed — Hard Mode tree / Scythe Drifa / Destiny sapphires — via <a href="{contact}">contact</a>.</p>"""


def article(
    depth: int,
    crumbs: list,
    title: str,
    meta: str,
    content: str,
    sources: list,
    *,
    show_stuck_prompt: bool = False,
    media: dict | None = None,
) -> str:
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
    prompt_html = stuck_prompt(depth) if show_stuck_prompt else ""
    if media:
        cover, figure = media["cover"], media["illustration"]
        figure_url = "../" * depth + figure["src"]
        figure_width, figure_height = (1000, 500) if figure["src"].endswith(".svg") else (1920, 1080)
        figure_html = f'''<figure class="article-figure">
      <a href="{escape(figure_url, quote=True)}"><img src="{escape(figure_url, quote=True)}" alt="{escape(figure['alt'], quote=True)}" width="{figure_width}" height="{figure_height}" loading="lazy" decoding="async" /></a>
      <figcaption>{escape(figure['caption'])}</figcaption>
    </figure>'''
        marker = figure.get("after")
        if marker and marker in content:
            content = content.replace(marker, marker + figure_html, 1)
        else:
            content = content.replace("</p>", "</p>" + figure_html, 1)
        return f'''
  <article class="guide-article">
    <header class="article-hero">
      <img src="{escape('../' * depth + cover['src'], quote=True)}" alt="{escape(cover['alt'], quote=True)}" width="1920" height="1080" fetchpriority="high" />
      <div class="article-hero-copy">
        <p class="breadcrumbs">{crumb_html}</p>
        <h1 class="page-title">{title}</h1>
      </div>
    </header>
    <p class="article-credit"><a href="{escape(cover['source'], quote=True)}">{escape(cover['caption'])}</a></p>
    <div class="narrow article-body">
      <p class="meta-line">{meta}</p>
      {content}{prompt_html}{sources_html}
    </div>
  </article>'''
    return f"""
  <div class="narrow">
    <p class="breadcrumbs">{crumb_html}</p>
    <h1 class="page-title">{title}</h1>
    <p class="meta-line">{meta}</p>
    {content}{prompt_html}{sources_html}
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
        for i, p in enumerate(rows):
            card = p["home_start"]
            featured = ' start-link--featured' if i == 0 else ""
            items.append(
                f'<a class="start-link{featured}" href="{p["path"]}"><strong>{card["title"]}</strong><span>{card["em"]}</span></a>'
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
    also = guide_list(pages, kind="home_also")
    destinations = "\n".join(
        f'''<a class="destination destination--{place['id']}" href="{place['path']}">
          <span class="destination-art" aria-hidden="true"></span>
          <span class="village-plaque"><strong>{place['title']}</strong><span>{place['description']}</span></span>
          <span class="enter-hint" aria-hidden="true">Enter guide ↗</span>
        </a>''' for place in home["village"]
    )
    return f"""
  <section class="village-intro">
    <div>
      <p class="village-kicker">{home["hero_kicker"]}</p>
      <h1>{home["hero_h1"]}</h1>
      <p>{home["village_intro"]}</p>
    </div>
    <a class="village-party" href="/characters/">
      <img src="assets/img/capsule.jpg" width="616" height="353" alt="The three animal characters together in official Sephiria artwork" />
      <span>Meet the characters ↗</span>
    </a>
  </section>
  <nav class="village-map" aria-label="Village guide destinations" id="village">
    <img class="village-background" src="assets/img/village.png" width="1536" height="1024" alt="" fetchpriority="high" />
    {destinations}
    <div class="village-notice" role="group" aria-label="Village noticeboard">
    <span class="notice-title">Village noticeboard</span>
    <a href="/bosses/">Boss guides</a>
    <a href="/multiplayer/">Co-op</a>
    <a href="/secret-rooms/">Secret rooms</a>
    </div>
  </nav>
  <aside class="village-welcome">
    <img src="assets/img/capsule.jpg" width="616" height="353" alt="Official Sephiria artwork featuring all three characters" />
    <div><strong>First time in the village?</strong><span>Pick a weapon, find a build, and make your first descent.</span></div>
    <a href="{link(0, home["cta_path"])}">{home["cta_label"]} <span aria-hidden="true">↗</span></a>
  </aside>
  <section class="village-reading">
    <div class="village-about">
      <h2>{home["what_h2"]}</h2>
      {home["what_html"]}
      <a href="{cfg["links"]["steam"]}" rel="noopener">View the game on Steam</a>
    </div>
    <div>
      <h2>More to explore</h2>
      <div class="guide-list">
        {also}
      </div>
    </div>
  </section>
"""


def git_lastmod(rel: str) -> str | None:
    """Last commit date (YYYY-MM-DD) of a source file; None if git unavailable."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT,
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return out or None
    except Exception:
        return None


def page_lastmod(cfg: dict, page: dict) -> str:
    return git_lastmod(f"content/{page.get('_file', '')}") or cfg["updated"]


def page_jsonld(cfg: dict, page: dict) -> list:
    """Structured data built only from fields already on the page (no invented facts)."""
    domain = cfg["domain"]
    org = {"@type": "Organization", "name": cfg["site_name"], "url": domain + "/"}
    url = domain + page["path"]
    layout = page.get("layout", "article")
    if layout == "home":
        return [
            {"@context": "https://schema.org", "@type": "WebSite", "name": cfg["site_name"],
             "url": domain + "/", "description": page["description"], "inLanguage": cfg["lang"], "publisher": org},
            {"@context": "https://schema.org", **org},
        ]
    items = []
    for i, (label, href) in enumerate(page.get("crumbs") or [("Home", "/"), (page.get("h1", ""), "")], start=1):
        item = {"@type": "ListItem", "position": i, "name": label}
        item["item"] = domain + href if href else url
        items.append(item)
    out = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}]
    if layout not in ("legal", "hub"):
        out.insert(0, {
            "@context": "https://schema.org", "@type": "Article",
            "headline": page.get("h1") or page["title"], "description": page["description"],
            "url": url, "mainEntityOfPage": url, "inLanguage": cfg["lang"],
            "dateModified": page_lastmod(cfg, page),
            "author": org, "publisher": org,
            "about": {"@type": "VideoGame", "name": cfg["game_name"], "url": cfg["links"]["steam"]},
        })
    return out


def write_llms_txt(cfg: dict, pages: list[dict]) -> None:
    lines = [f"# {cfg['site_name']}", "",
             f"> Unofficial fan guides for {cfg['game_name']} by {cfg['developer']} ({cfg['links']['steam']}). "
             "Not affiliated with the developer.", "", "## Guides"]
    for p in pages:
        if p.get("sitemap_exclude") or p.get("layout") == "legal":
            continue
        lines.append(f"- [{p.get('h1') or p['title']}]({cfg['domain']}{p['path']}): {p['description']}")
    (OUTPUT_DIR / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote llms.txt")


def write_page(cfg: dict, path: str, title: str, description: str, body: str, jsonld: list | None = None) -> None:
    depth = depth_of(path)
    html = shell(cfg, title=title, description=description, depth=depth, path=path, body=body, jsonld=jsonld)
    out = OUTPUT_DIR / ("index.html" if path == "/" else Path(path.strip("/")) / "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out.relative_to(OUTPUT_DIR))


def write_extra_sites(cfg: dict) -> list[dict]:
    """Copy hand-authored game sub-sites (extra_sites/<slug>/) into dist.

    These live outside content/ on purpose: each game keeps its own header and
    footer (not the Sephiria nav or home cards) while sharing this domain and
    canonical host. Returns sitemap entries for every index.html found.

    Sub-sites in MOVED_SITES live on their own apex now, so they are not copied
    at all: write_redirects() emits 301s for their old sub-paths and the moved
    domain serves the pages itself.
    """
    extra: list[dict] = []
    if not EXTRA_SITES_DIR.is_dir():
        return extra
    for slug_dir in sorted(p for p in EXTRA_SITES_DIR.iterdir() if p.is_dir()):
        slug = slug_dir.name
        if slug.startswith("_"):
            continue  # shared scratch dirs (e.g. _root_files), not a sub-site
        if slug in MOVED_SITES:
            print(f"extra site {slug}: moved to {MOVED_SITES[slug]}, not copied")
            continue
        shutil.copytree(slug_dir, OUTPUT_DIR / slug, dirs_exist_ok=True)
        for index in sorted(slug_dir.rglob("index.html")):
            parts = [p for p in index.parent.relative_to(slug_dir).parts if p not in ("", ".")]
            path = "/" + "/".join([slug, *parts]) + "/"
            extra.append({"path": path, "lastmod": cfg.get("updated", "")})
    print("extra sites:", len(extra), "pages")
    return extra


def write_sitemap(cfg: dict, pages: list[dict], extra: list[dict] | None = None) -> None:
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
            f'  <url><loc>{cfg["domain"]}{page["path"]}</loc><lastmod>{page_lastmod(cfg, page)}</lastmod><changefreq>weekly</changefreq><priority>{pri}</priority></url>'
        )
    for page in extra or []:
        lastmod = f"<lastmod>{page['lastmod']}</lastmod>" if page.get("lastmod") else ""
        lines.append(
            f'  <url><loc>{cfg["domain"]}{page["path"]}</loc><changefreq>weekly</changefreq><priority>0.7</priority>{lastmod}</url>'
        )
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote sitemap.xml", len(listed) + len(extra or []), "urls")


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
    (OUTPUT_DIR / "404.html").write_text(html, encoding="utf-8")
    print("wrote 404.html")


def write_ads_txt() -> None:
    # Plain text so SPA fallback cannot serve homepage HTML here.
    text = (
        "# sephiria-guide.com — no ad network authorized yet.\n"
        "# When ads go live, publisher lines will be listed below.\n"
    )
    (OUTPUT_DIR / "ads.txt").write_text(text, encoding="utf-8")
    print("wrote ads.txt")


def write_redirects() -> None:
    # The Warhammer Survivors sub-site moved to its own domain (warhammersurvivors.com);
    # redirect the old sub-paths so existing links and indexed URLs pass their ranking
    # signal on. Only sub-sites with a registered apex are redirected — others still live
    # here. Rules must precede the SPA 404 catch-all below, since Pages applies
    # _redirects in order.
    lines = []
    if EXTRA_SITES_DIR.is_dir():
        for slug_dir in sorted(p for p in EXTRA_SITES_DIR.iterdir() if p.is_dir()):
            apex = MOVED_SITES.get(slug_dir.name)
            if not apex:
                continue
            for index in sorted(slug_dir.rglob("index.html")):
                parts = [p for p in index.parent.relative_to(slug_dir).parts if p not in ("", ".")]
                old = "/" + "/".join([slug_dir.name, *parts]) + "/"
                new = f"https://{apex}/" + "/".join(parts) + ("/" if parts else "")
                lines.append(f"{old} {new} 301")
                if parts:
                    # The old domain no longer serves these files, so Pages will not add the
                    # trailing slash itself; map the bare form straight to the new URL (one hop).
                    lines.append(f"{old.rstrip('/')} {new} 301")
                if not parts:
                    # Pages normalises a bare sub-site path to its trailing-slash form
                    # before matching, so the root needs both variants.
                    lines.append(f"/{slug_dir.name} {new} 301")
    text = "\n".join(lines) + ("\n" if lines else "")
    # Override Cloudflare Pages SPA soft-404 (/* → index.html 200).
    (OUTPUT_DIR / "_redirects").write_text(text + "/* /404.html 404\n", encoding="utf-8")
    print("wrote _redirects", len(lines), "moved-page redirects")


CSS_VERSION = ""
THEME_VERSION = ""


def compute_css_version() -> str:
    """Content hash of styles.css — cache-bust key for stylesheet URLs."""
    return hashlib.md5((ROOT / "assets" / "styles.css").read_bytes()).hexdigest()[:8]


def compute_theme_version(cfg: dict) -> str:
    """Content hash of the generated theme.css (config-driven colors)."""
    return hashlib.md5(json.dumps(cfg["theme"], sort_keys=True).encode()).hexdigest()[:8]


def build(cfg: dict | None = None, content_dir: Path = CONTENT_DIR) -> list[dict]:
    global CSS_VERSION, THEME_VERSION
    cfg = cfg or load_config()
    CSS_VERSION = compute_css_version()
    THEME_VERSION = compute_theme_version(cfg)
    pages = load_pages(content_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", OUTPUT_DIR / "assets", dirs_exist_ok=True)
    for filename in ("login.html", "robots.txt", "favicon.ico"):
        source = ROOT / filename
        if source.is_file():
            shutil.copy2(source, OUTPUT_DIR / filename)
    write_theme(cfg)
    by_path = {p["path"]: p for p in pages}
    visuals_path = ROOT / "config" / "guide-visuals.json"
    visuals = json.loads(visuals_path.read_text(encoding="utf-8")) if visuals_path.exists() else {}

    for page in pages:
        layout = page.get("layout", "article")
        if layout == "home":
            write_page(cfg, page["path"], page["title"], page["description"], home_body(page, pages, cfg), page_jsonld(cfg, page))
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
                show_stuck_prompt=True,
                media=visuals.get(page["path"]),
            )
            write_page(cfg, page["path"], page["title"], page["description"], body, page_jsonld(cfg, page))
        else:
            body = article(
                depth_of(page["path"]),
                page.get("crumbs") or [("Home", "/"), (page.get("h1", ""), "")],
                page["h1"],
                page["meta"],
                page.get("body") or "",
                page.get("sources") or [],
                show_stuck_prompt=(layout != "legal"),
                media=visuals.get(page["path"]),
            )
            write_page(cfg, page["path"], page["title"], page["description"], body, page_jsonld(cfg, page))

    extra = write_extra_sites(cfg)
    write_sitemap(cfg, pages, extra)
    write_404(cfg)
    write_ads_txt()
    write_llms_txt(cfg, pages)
    write_redirects()
    return pages


if __name__ == "__main__":
    build()
    print("done")
