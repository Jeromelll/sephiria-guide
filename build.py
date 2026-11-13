#!/usr/bin/env python3
"""Framework layer: read config + content files, write static HTML.

Add or delete a file in content/ and rebuild — nav hubs, home cards,
and sitemap follow automatically. Game-specific strings live in
config/site.json and content/*.json, not in this file.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "site.json"
CONTENT_DIR = ROOT / "content"
OUTPUT_DIR = ROOT / "dist"
# AdSense account for sephiria-guide.com. Manual in-article units need
# numeric slot IDs from the AdSense console (created after the site is added).
# Leave a slot blank to keep the container in the layout without calling
# adsbygoogle.push — an unfilled unit then takes no space and throws no error.
ADSENSE_CLIENT = "ca-pub-8359621843582672"
ADSENSE_SLOTS = {
    "after-lead": "",
    "before-related": "",
}
_RELATED_SPLIT = re.compile(r"(<h2>\s*Related\b|<p>\s*Related\s*:)", re.IGNORECASE)
EXTRA_SITES_DIR = ROOT / "extra_sites"
# Sub-sites that now live on their own apex domain. Keys are directory names under
# extra_sites/; values are the apex they moved to.
MOVED_SITES = {"warhammer-survivors": "warhammersurvivors.com"}

# Legacy sub-sites kept reachable for old links but hidden from search and the
# sitemap: they belong to other games and dilute this domain's topic signal.
EXTRA_SITES_NOINDEX = {"phantom-blade-zero", "shrek-2-remastered"}


def _inject_noindex(path: Path) -> None:
    """Add a robots noindex meta to a copied static page, once."""
    if not path.is_file():
        return
    html = path.read_text(encoding="utf-8")
    if 'content="noindex' in html:
        return
    tag = '<meta name="robots" content="noindex,follow" />'
    if "</head>" in html:
        html = html.replace("</head>", f"  {tag}\n</head>", 1)
    else:
        html = tag + html
    path.write_text(html, encoding="utf-8")


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


def section_of(cfg: dict, path: str) -> dict:
    """Which game chrome a page belongs to.

    "/" is the shared portal; /fm27/* is the Football Manager 27 section; every
    other page is Sephiria. Each section carries its own brand, nav and footer
    so an FM27 reader never has to pass through Sephiria wording.
    """
    sections = cfg.get("sections") or {}
    root = sections.get("root") or {}
    if path == "/":
        return {**root, "key": "root"}
    if path.startswith("/fm27"):
        sec = sections.get("fm27") or {}
        return {**sec, "key": "fm27"}
    sec = sections.get("sephiria") or {}
    return {**sec, "key": "sephiria"}


def shell(cfg: dict, *, title: str, description: str, depth: int, path: str, body: str, jsonld: list | None = None, noindex: bool = False) -> str:
    is_home = path == "/"
    ld_html = "".join(
        f'\n  <script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>' for obj in (jsonld or [])
    )
    sec = section_of(cfg, path)
    nav_html = []
    for label, href in sec.get("nav") or cfg["nav"]:
        current = ' aria-current="page"' if href.rstrip("/") == path.rstrip("/") else ""
        nav_html.append(f'<a href="{link(depth, href)}"{current}>{label}</a>')
    brand_name, brand_suffix = sec.get("brand") or [cfg["brand_name"], cfg["brand_suffix"]]
    game_name = sec.get("game_name") or cfg["game_name"]
    developer = sec.get("developer") or cfg["developer"]
    steam = sec.get("steam") or cfg["links"]["steam"]
    game_link = f'<a href="{steam}">{game_name}</a>'
    footer_line = cfg["footer_line"].replace("{game_link}", game_link).replace("{developer}", developer)
    footer_nav = " · ".join(
        f'<a href="{link(depth, href)}">{label}</a>' for label, href in (sec.get("footer_links") or [])
    )
    robots_meta = '\n  <meta name="robots" content="noindex,follow" />' if noindex else ""
    portal_script = '\n  <script src="assets/portal.js" defer></script>' if is_home else ""
    return f"""<!DOCTYPE html>
<html lang="{cfg["lang"]}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{description}" />{robots_meta}
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
  <script src="{css_href(depth, "analytics.js")}" defer></script>{portal_script}{ld_html}
  <!-- AdSense head snippet (inserted by adsense_prep) -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>
</head>
<body{' class="home-portal"' if is_home else ''}>
  <a class="skip-link" href="#content">Skip to content</a>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="brand" href="{link(depth, '/')}">{brand_name} <span>{brand_suffix}</span></a>
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
      <p>{footer_nav} · Updated {cfg["updated"]}</p>
      <p class="other-games">Also see: <a href="https://warhammersurvivors.com/">Warhammer Survivors guide</a></p>
    </div>
  </footer>
  <script>
  (function () {{
    var nodes = document.querySelectorAll("ins.adsbygoogle[data-ad-slot]");
    for (var i = 0; i < nodes.length; i++) {{
      (adsbygoogle = window.adsbygoogle || []).push({{}});
    }}
  }})();
  </script>
</body>
</html>
"""


def ad_slot_html(placement: str) -> str:
    """In-flow in-article unit. Not sticky, not an overlay, not a popup."""
    slot = ADSENSE_SLOTS.get(placement, "")
    slot_attr = f'\n       data-ad-slot="{escape(slot, quote=True)}"' if slot else ""
    return f'''<div class="ad-slot" data-ad-placement="{escape(placement, quote=True)}">
  <ins class="adsbygoogle"
       style="display:block;text-align:center;"
       data-ad-client="{ADSENSE_CLIENT}"
       data-ad-layout="in-article"
       data-ad-format="fluid"
       data-full-width-responsive="true"{slot_attr}></ins>
</div>'''


def insert_ad_slots(content: str) -> str:
    """One unit after the opening paragraph, one before the Related block."""
    lead = ad_slot_html("after-lead")
    tail = ad_slot_html("before-related")
    close = content.find("</p>")
    if close == -1:
        content = lead + content
    else:
        cut = close + len("</p>")
        content = content[:cut] + "\n" + lead + content[cut:]
    match = _RELATED_SPLIT.search(content)
    if match:
        content = content[: match.start()] + tail + "\n" + content[match.start() :]
    else:
        content = content + "\n" + tail
    return content


def stuck_prompt(depth: int, section: dict | None = None) -> str:
    """Light post-read ask — high-intent moment, same idea as Zigpoll's one question.

    The wording is section-aware: an FM27 reader is asked about FM27 steps, not
    about Hard Mode or Destiny sapphires.
    """
    contact = link(depth, "/contact/")
    topic = (section or {}).get("stuck_topic") or "the step that failed"
    return f"""
    <p class="stuck-prompt">Still stuck? Tell us {topic} via <a href="{contact}">contact</a>.</p>"""


def article(
    depth: int,
    crumbs: list,
    title: str,
    meta: str,
    content: str,
    sources: list,
    *,
    show_stuck_prompt: bool = False,
    show_ads: bool = False,
    media: dict | None = None,
    section: dict | None = None,
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
    prompt_html = stuck_prompt(depth, section) if show_stuck_prompt else ""
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
    if show_ads:
        content = insert_ad_slots(content)
    if media:
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
    """Portal home: two game entries, three most-read guides each, plus a search box.

    Replaces the old illustrated "village" landing page. The village map asked a
    first-time visitor to decode a metaphor before choosing a page; this asks the
    only question they can answer — which game are you here for — and then offers
    the three pages each game actually gets read most.
    """
    cards = []
    for game in home["games"]:
        links = "\n".join(
            f'<a href="{g["path"]}"><strong>{g["title"]}</strong><em>{g["em"]}</em></a>'
            for g in game["top"]
        )
        cards.append(f'''
      <article class="portal-card portal-card--{game["id"]}">
        <p class="portal-card-kicker">{game["kicker"]}</p>
        <h2><a href="{game["path"]}">{game["name"]}</a></h2>
        <p class="portal-card-lede">{game["lede"]}</p>
        <div class="guide-list">
          {links}
        </div>
        <p class="portal-card-all"><a href="{game["path"]}">{game["all_label"]} <span aria-hidden="true">↗</span></a></p>
      </article>''')
    return f"""
  <section class="portal-hero">
    <div class="wrap">
      <p class="hero-kicker">{home["hero_kicker"]}</p>
      <h1>{home["hero_h1"]}</h1>
      <p class="lede">{home["lede"]}</p>
      <div class="portal-search">
        <label for="guide-search">Find a page</label>
        <input id="guide-search" type="search" placeholder="{home["search_placeholder"]}" autocomplete="off" spellcheck="false" />
        <ul id="guide-search-results" class="guide-list search-results" hidden></ul>
        <p id="guide-search-empty" class="search-empty" hidden>No page matches that yet. Try a shorter word, or browse one of the two game entries below.</p>
      </div>
    </div>
  </section>
  <section class="portal-games" aria-label="Choose a game">
    <div class="wrap portal-grid">{''.join(cards)}
    </div>
  </section>
  <section class="wrap portal-about">
    <h2>{home["what_h2"]}</h2>
    {home["what_html"]}
  </section>
"""


def write_search_index(pages: list[dict], cfg: dict) -> None:
    """Client-side guide search data. Title + description + path, nothing more."""
    rows = []
    for p in pages:
        if p.get("layout") in ("legal", "home") or p.get("noindex"):
            continue
        rows.append({
            "t": p.get("h1") or p.get("title", ""),
            "d": p.get("description", ""),
            "p": p["path"],
        })
    rows.sort(key=lambda r: r["t"].lower())
    (OUTPUT_DIR / "assets" / "search-index.json").write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print("wrote assets/search-index.json", len(rows), "entries")


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
    sec = section_of(cfg, page["path"])
    game_name = sec.get("game_name") or cfg["game_name"]
    steam = sec.get("steam") or cfg["links"]["steam"]
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
            "about": {"@type": "VideoGame", "name": game_name, "url": steam},
        })
    return out


def write_llms_txt(cfg: dict, pages: list[dict]) -> None:
    lines = [f"# {cfg['site_name']}", "",
             f"> Unofficial fan guides for {cfg['game_name']} by {cfg['developer']} "
             f"({cfg['links']['steam']}), plus a separate Football Manager 27 section. "
             "Not affiliated with either developer.", "", "## Guides"]
    for p in pages:
        if p.get("sitemap_exclude") or p.get("layout") == "legal":
            continue
        lines.append(f"- [{p.get('h1') or p['title']}]({cfg['domain']}{p['path']}): {p['description']}")
    (OUTPUT_DIR / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote llms.txt")


def write_page(cfg: dict, path: str, title: str, description: str, body: str, jsonld: list | None = None, noindex: bool = False) -> None:
    depth = depth_of(path)
    html = shell(cfg, title=title, description=description, depth=depth, path=path, body=body, jsonld=jsonld, noindex=noindex)
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
        noindex = slug in EXTRA_SITES_NOINDEX
        for index in sorted(slug_dir.rglob("index.html")):
            parts = [p for p in index.parent.relative_to(slug_dir).parts if p not in ("", ".")]
            path = "/" + "/".join([slug, *parts]) + "/"
            if noindex:
                _inject_noindex(OUTPUT_DIR / slug / index.relative_to(slug_dir))
                continue
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


ADS_TXT = (
    "# sephiria-guide.com — AdSense (ca-pub-8359621843582672)\n"
    "google.com, pub-8359621843582672, DIRECT, f08c47fec0942fa0\n"
)


def write_ads_txt() -> None:
    # Publish the repo-root ads.txt when it is present. The swap-test rebuild
    # points ROOT at a temp tree that has no ads.txt, so fall back to the
    # publisher line. Plain text so the SPA fallback cannot serve HTML here.
    source = ROOT / "ads.txt"
    if source.is_file():
        text = source.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
    else:
        text = ADS_TXT
    (OUTPUT_DIR / "ads.txt").write_text(text, encoding="utf-8")
    print("wrote ads.txt")


def write_redirects() -> None:
    # The Warhammer Survivors sub-site moved to its own apex (warhammersurvivors.com);
    # redirect the old sub-paths so existing links and indexed URLs pass their ranking
    # signal on. Only sub-sites with a registered apex are redirected — others still live
    # here. Rules must precede the SPA 404 catch-all below, since Pages applies
    # _redirects in order.
    lines = []
    # Same-site pages that were merged into another page (old path -> new anchor).
    # Keeps indexed URLs and inbound links flowing to the surviving page.
    for old, new in {
        "/roots-retreat/": "/hard-mode/",
        "/roots-retreat": "/hard-mode/",
        "/wiki/": "/guides/",
        "/wiki": "/guides/",
        "/bosses/erma/": "/bosses/#erma",
        "/bosses/erma": "/bosses/#erma",
        "/bosses/final/": "/bosses/#final",
        "/bosses/final": "/bosses/#final",
        # /items/ was never a page; the scythe explainer lives at /items/scythe/.
        # Point the bare directory at the weapons hub so old links stop 404ing.
        "/items/": "/weapons/",
        "/items": "/weapons/",
    }.items():
        lines.append(f"{old} {new} 301")
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
    # Pages deleted from a sub-site before it moved to its own apex are gone from
    # disk, so the rglob above cannot see them. Keep their inbound links flowing
    # to the surviving page instead of letting Google re-crawl a 404.
    for old, new in {
        "/warhammer-survivors/evolutions/weapon-evolutions": "https://warhammersurvivors.com/weapon-evolutions/",
        "/warhammer-survivors/guide/tier-list": "https://warhammersurvivors.com/tier-list/",
        "/warhammer-survivors/weapon-evolutions/tier-list": "https://warhammersurvivors.com/tier-list/",
        "/warhammer-survivors/demo/tier-list": "https://warhammersurvivors.com/tier-list/",
        "/warhammer-survivors/characters/tier-list": "https://warhammersurvivors.com/tier-list/",
        "/warhammer-survivors/characters/tier-list/hard-mode": "https://warhammersurvivors.com/tier-list/",
        "/warhammer-survivors/beginner-guide": "https://warhammersurvivors.com/guide/",
        "/warhammer-survivors/bosses": "https://warhammersurvivors.com/characters/",
        "/warhammer-survivors/walkthrough": "https://warhammersurvivors.com/guide/",
    }.items():
        lines.append(f"{old}/ {new} 301")
        lines.append(f"{old} {new} 301")
    # Static assets and root files that used to live under the sub-site path.
    # A splat keeps every one of them working without listing each file.
    lines.append("/warhammer-survivors/assets/* https://warhammersurvivors.com/assets/:splat 301")
    lines.append("/warhammer-survivors/assets/ https://warhammersurvivors.com/assets/ 301")
    lines.append("/warhammer-survivors/sitemap.xml https://warhammersurvivors.com/sitemap.xml 301")
    lines.append("/warhammer-survivors/robots.txt https://warhammersurvivors.com/robots.txt 301")
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
    # dist/ is a build artifact: wipe it so a page that was deleted from content/
    # cannot linger and get deployed (login.html did exactly that on 2026-11-13).
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", OUTPUT_DIR / "assets", dirs_exist_ok=True)
    # Copied as-is, including the IndexNow key. It must land in dist/ so
    # Pages serves /131fc577a3d44393b0a07c68875a1462.txt as text/plain.
    for filename in (
        "robots.txt",
        "favicon.ico",
        "131fc577a3d44393b0a07c68875a1462.txt",
    ):
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
            write_page(cfg, page["path"], page["title"], page["description"], home_body(page, pages, cfg), page_jsonld(cfg, page), noindex=bool(page.get("noindex")))
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
                show_ads=True,
                media=visuals.get(page["path"]),
                section=section_of(cfg, page["path"]),
            )
            write_page(cfg, page["path"], page["title"], page["description"], body, page_jsonld(cfg, page), noindex=bool(page.get("noindex")))
        else:
            body = article(
                depth_of(page["path"]),
                page.get("crumbs") or [("Home", "/"), (page.get("h1", ""), "")],
                page["h1"],
                page["meta"],
                page.get("body") or "",
                page.get("sources") or [],
                show_stuck_prompt=(layout != "legal"),
                show_ads=(layout != "legal"),
                media=visuals.get(page["path"]),
                section=section_of(cfg, page["path"]),
            )
            write_page(cfg, page["path"], page["title"], page["description"], body, page_jsonld(cfg, page), noindex=bool(page.get("noindex")))

    extra = write_extra_sites(cfg)
    write_sitemap(cfg, pages, extra)
    write_404(cfg)
    write_ads_txt()
    write_llms_txt(cfg, pages)
    write_search_index(pages, cfg)
    write_redirects()
    return pages


if __name__ == "__main__":
    build()
    print("done")
