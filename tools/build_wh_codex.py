#!/usr/bin/env python3
"""Render the Warhammer Survivors codex pages from extra_sites/warhammer-survivors/data/*.json.

    python3 tools/build_wh_codex.py     # writes codex/, codex/characters/, weapons/, enemies/

Pages are plain static HTML (every entry is in the markup); assets/codex.js only
filters/searches client-side. Edit the JSON, re-run this script, then run
tools/build_standalone_wh.py as usual.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "extra_sites" / "warhammer-survivors"
P = "/warhammer-survivors/"
DOMAIN = "https://sephiria-guide.com/warhammer-survivors/"
PENDING = "Pending launch"
UPDATED = "2026-10-24"

FAC = {"40K": "Warhammer 40,000", "AoS": "Age of Sigmar", "Cross": "Cross-universe", "Unconfirmed": "Universe unconfirmed"}
FAC_SHORT = {"40K": "40K", "AoS": "AoS", "Cross": "Both", "Unconfirmed": "?"}
CONF = {"official": "Official", "press": "Press preview", "community": "Community · unconfirmed"}

NAV = [("", "Overview"), ("demo/", "Demo"), ("guide/", "Guide"), ("codex/", "Codex"),
       ("characters/", "Characters"), ("evolutions/", "Evolutions"), ("stages/", "Stages"), ("tier-list/", "Tier List")]

SOURCES = [
    ("https://store.steampowered.com/app/3669620/Warhammer_Survivors/", "Steam store page (app 3669620)"),
    ("https://steamcommunity.com/games/3669620/announcements", "Auroch Digital — Steam announcements (Nov 2025 – Oct 2026)"),
    ("https://news.xbox.com/en-us/2026/04/17/warhammer-survivors-reveals-mighty-ork-xbox-launch-2026", "Xbox Wire — Ork menace (Apr 17, 2026, by the lead designer)"),
    ("https://www.microsoft.com/en-us/store/apps/9MZZWGTF7V65", "Xbox / Microsoft Store page (9MZZWGTF7V65)"),
    ("https://blog.playstation.com/2026/10/06/warhammer-survivors-launches-november-10-new-characters-revealed/", "PlayStation.Blog — Auroch Digital developer post (Oct 6, 2026)"),
    ("https://www.warhammer-community.com/en-gb/articles/sxfxzwun/first-look-new-characters-and-enemies-for-warhammer-survivors/", "Warhammer Community — first look (Apr 9, 2026)"),
    ("https://www.ign.com/articles/warhammer-survivors-is-not-just-a-vampire-survivors-clone-it-aims-to-be-a-celebration-of-the-best-of-both-worlds-ign-preview", "IGN hands-on preview (Oct 6, 2026)"),
    ("https://www.pcgamer.com/games/roguelike/warhammer-survivors-is-more-than-just-a-vampire-survivors-spin-off/", "PC Gamer — 10 hours with the demo (Oct 6, 2026)"),
    ("https://whsurvivors.wiki/weapon-evolutions/", "whsurvivors.wiki — community evolution reports (unconfirmed)"),
]

e = html.escape


def load(name: str) -> list[dict]:
    return json.loads((SRC / "data" / f"{name}.json").read_text(encoding="utf-8"))["entries"]


def head(title: str, desc: str, path: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}"/>
<link rel="canonical" href="{DOMAIN}{path}"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/><link href="https://fonts.googleapis.com/css2?family=Alegreya+Sans:ital,wght@0,400;0,500;0,700;1,400&family=Cinzel:wght@700&family=Jacquarda+Bastarda+9&family=Pixelify+Sans:wght@500;600&display=swap" rel="stylesheet"/><link rel="stylesheet" href="{P}assets/wh.css"/><link rel="stylesheet" href="{P}assets/codex.css"/><meta name="theme-color" content="#0b0908"/><link rel="icon" href="{P}assets/favicon.svg" type="image/svg+xml"/><link rel="icon" href="{P}assets/favicon-32x32.png" sizes="32x32" type="image/png"/><link rel="icon" href="{P}assets/favicon-16x16.png" sizes="16x16" type="image/png"/><link rel="apple-touch-icon" href="{P}assets/apple-touch-icon.png"/>
</head>
<body>
{nav_html(path)}
"""


def nav_html(path: str) -> str:
    links = []
    for href, label in NAV:
        on = href == path or (href == "codex/" and path in ("codex/characters/", "weapons/", "enemies/"))
        links.append(f'<a{" class=\"on\"" if on else ""} href="{P}{href}">{label}</a>')
    links.append('<a class="login" href="/login.html">Log in</a>')
    return ('<header><div class="wrap hd"><a class="brand" href="/warhammer-survivors/" aria-label="Warhammer Survivors Guide home">'
            '<span class="b1">Warhammer</span><span class="b2">Survivors Guide</span></a><nav>' + "".join(links) + "</nav></div></header>")


def codex_tabs(path: str) -> str:
    tabs = [("codex/", "Codex home"), ("codex/characters/", "Characters"), ("weapons/", "Weapons & Items"), ("enemies/", "Enemies")]
    out = "".join(f'<a{" class=\"on\" aria-current=\"page\"" if h == path else ""} href="{P}{h}">{l}</a>' for h, l in tabs)
    return f'<nav class="cx-tabs" aria-label="Codex sections">{out}</nav>'


def foot() -> str:
    return ('</main>\n<footer><div class="wrap"><span class="fm">Warhammer Survivors Guide</span><span>Unofficial fan guide for Warhammer Survivors. '
            'Not affiliated with Games Workshop or the game’s developer. Codex entries cite Auroch Digital’s Steam announcements and store pages, '
            'Warhammer Community, Xbox Wire, PlayStation.Blog, IGN and PC Gamer previews, and whsurvivors.wiki community reports; game names and art belong to their owners. '
            f'Part of the guide network at <a href="/">sephiria-guide.com</a> — also see <a href="/phantom-blade-zero/">Phantom Blade Zero</a> and <a href="/warhammer-survivors/">Warhammer Survivors</a>. Last updated October 24, 2026 · Demo build.</span></div></footer>\n'
            f'<script src="{P}assets/codex.js" defer></script>\n</body>\n</html>\n')


def sources_block() -> str:
    lis = "".join(f'<li><a href="{u}" rel="noopener">{e(t)}</a></li>' for u, t in SOURCES)
    return f'<div class="src"><h2>Sources</h2><ul>{lis}</ul></div>'


def val(v) -> str:
    if v is None or v == "" or v == PENDING:
        return f'<span class="pend">{PENDING}</span>'
    return e(v)


def tile(entry: dict) -> str:
    fac = entry["faction"]
    cls = {"40K": "40k", "AoS": "aos"}.get(fac, "x")
    if entry.get("image"):
        return (f'<img class="ico ico-{cls}" src="{P}assets/{entry["image"]}" alt="{e(entry["name"])} — official in-game pixel sprite" '
                'width="72" height="72" loading="lazy" decoding="async"/>')
    nm = entry["name"][4:] if entry["name"].startswith("The ") else entry["name"]
    letter = nm[:1].upper()
    return f'<span class="ico ph ph-{cls}" role="img" aria-label="{e(entry["name"])} — placeholder tile, no official icon published yet">{e(letter)}</span>'


ANN = {"1816849002007457": "Steam: First Survivors (Nov 19, 2025)", "1817483467033907": "Steam: Enemies sighted (Nov 26, 2025)",
       "1825727806704618": "Steam: Zangrom-Thaz (Feb 25)", "1829528821307561": "Steam: new champions & weapons (Apr 9)",
       "1832700592786358": "Steam: Status Effects (May 13)", "1833334318569481": "Steam: demo & Skulls (May 21)",
       "1835236783557691": "Steam: Chaos detected (Jun 10)", "1835871199300397": "Steam: Hobby Table (Jun 17)",
       "1840310314339267": "Steam: Status Effects focus (Aug 5)", "1840944183773754": "Steam: concept art (Aug 12)",
       "1841579228662246": "Steam: Pick-ups (Aug 19)", "1842212951299753": "Steam: pixel art blog (Aug 27)",
       "1842846814442987": "Steam: Enemy Skills (Sep 3)", "1844115010491623": "Steam: Faction Traits (Sep 17)",
       "1845383656396506": "Steam: release date (Oct 6)", "1846651706690969": "Steam: Next Fest demo (Oct 19)",
       "1847286114029178": "Steam: Squad System (Oct 21)"}
HOSTS = {"store.steampowered.com": "Steam store", "blog.playstation.com": "PlayStation.Blog (dev post)", "news.xbox.com": "Xbox Wire (dev post)",
         "warhammer-community.com": "Warhammer Community", "ign.com": "IGN preview", "pcgamer.com": "PC Gamer", "whsurvivors.wiki": "whsurvivors.wiki (community)"}


def src_label(u: str) -> str:
    if "steam_community_announcements" in u:
        return ANN.get(u.rstrip("/").split("/")[-1], "Steam announcement")
    host = u.split("/")[2].replace("www.", "")
    return HOSTS.get(host, host)


def src_links(entry: dict) -> str:
    urls = [entry["source_url"]] + [u for u in entry.get("extra_sources", []) if u != entry["source_url"]]
    parts = [f'<a href="{u}" rel="noopener">{e(src_label(u))}</a>' for u in urls]
    return '<p class="cx-src">Source: ' + " · ".join(parts) + "</p>"


def card(entry: dict, badges: list[str], fields: list[tuple[str, str]], data: dict) -> str:
    conf = entry["confidence"]
    attrs = " ".join(f'data-{k}="{e(v)}"' for k, v in data.items())
    search = " ".join([entry["name"], entry["description"], entry.get("type", ""), entry.get("group", ""), FAC.get(entry["faction"], "")]
                      + [f for _, f in fields]).lower()
    b = "".join(badges) + f'<span class="cx-b cx-c-{conf}">{CONF[conf]}</span>'
    dl = "".join(f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in fields)
    import re
    search_txt = re.sub(r"<[^>]+>", " ", search)
    return (f'<article class="cx-card cx-{conf}" id="{entry["id"]}" {attrs} data-conf="{conf}" data-search="{e(search_txt)}">'
            f'<div class="cx-hd">{tile(entry)}<div class="cx-t"><h3>{e(entry["name"])}</h3><div class="cx-bs">{b}</div></div></div>'
            f'<p class="cx-d">{e(entry["description"])}</p>' + (f"<dl>{dl}</dl>" if dl else "") + src_links(entry) + "</article>")


def fbadge(f: str) -> str:
    return f'<span class="cx-b cx-f-{FAC_SHORT[f].lower().replace("?", "q")}">{e(FAC[f])}</span>'


def tools(selects: list[tuple[str, str, list[tuple[str, str]]]], placeholder: str) -> str:
    out = ['<form class="cx-tools" role="search" aria-label="Filter the codex">',
           f'<label class="cx-q"><span>Search</span><input type="search" id="cx-q" placeholder="{e(placeholder)}" autocomplete="off"/></label>']
    for key, label, opts in selects:
        o = "".join(f'<option value="{e(v)}">{e(t)}</option>' for v, t in opts)
        out.append(f'<label><span>{e(label)}</span><select data-filter="{key}"><option value="">All</option>{o}</select></label>')
    out.append('<button type="reset" id="cx-reset" class="btn ghost">Reset</button><output id="cx-count" aria-live="polite"></output></form>')
    out.append('<p id="cx-empty" class="note" hidden>No entries match. Try a shorter search or reset the filters.</p>')
    return "".join(out)


def legend() -> str:
    return ('<p class="cx-legend"><span class="cx-b cx-c-official">Official</span> developer / publisher / store text · '
            '<span class="cx-b cx-c-press">Press preview</span> hands-on reporting · '
            '<span class="cx-b cx-c-community">Community · unconfirmed</span> player reports, not verified. '
            f'<span class="pend">{PENDING}</span> = not published yet.</p>')


def upd() -> str:
    return (f'<div class="upd">🚧 <strong>Last updated {UPDATED} · Demo build.</strong> Warhammer Survivors launches <strong>November 10, 2026</strong>. '
            'Every entry cites its source; nothing here is datamined or guessed. Missing values are marked Pending launch.</div>')


def page(path, title, desc, crumb, h1, meta, body, banner="ss1.jpg"):
    return (head(title, desc, path) +
            f'<div class="banner" style="background-image:url({P}assets/{banner})" role="presentation"></div>\n<main class="wrap cx-wide">\n'
            f'<p class="bread"><a href="/">Home</a> / <a href="{P}">Warhammer Survivors Guide</a> / '
            + (f'<a href="{P}codex/">Codex</a> / ' if path != "codex/" else "") + f'{e(crumb)}</p>\n'
            f'<h1>{e(h1)}</h1>\n<p class="meta">{meta}</p>\n{upd()}\n{codex_tabs(path)}\n{body}\n{sources_block()}\n' + foot())


def write(path: str, text: str) -> None:
    d = SRC / path
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(text, encoding="utf-8")
    print("wrote", (d / "index.html").relative_to(ROOT))


def weapons_by_name(weapons):
    return sorted(weapons, key=lambda w: -len(w["name"]))


def link_weapon(text: str, weapons) -> str:
    if not text or text == PENDING:
        return val(text)
    for w in weapons_by_name(weapons):
        if text.startswith(w["name"]):
            return f'<a href="{P}weapons/#{w["id"]}">{e(w["name"])}</a>{e(text[len(w["name"]):])}'
    return e(text)


def build_characters(chars, weapons):
    cards = {"40K": [], "AoS": []}
    for c in chars:
        fields = [("Title", val(c.get("title"))), ("Starting weapon", link_weapon(c.get("starting_weapon"), weapons)),
                  ("Ability / passive", val(c.get("ability"))), ("Unlock", val(c.get("unlock"))),
                  ("Squad / keywords", val(c.get("squad"))), ("Demo status", val(c.get("demo")))]
        badges = [fbadge(c["faction"]), f'<span class="cx-b">{e(c["type"])}</span>']
        cards[c["faction"]].append(card(c, badges, fields, {"faction": c["faction"], "type": c["type"].lower()}))
    groups = "".join(f'<section class="cx-group" aria-labelledby="g-{k.lower()}"><h2 id="g-{k.lower()}">{FAC[k]} champions</h2><div class="cx-grid">{"".join(v)}</div></section>'
                     for k, v in cards.items())
    squad = ('<h2 id="squad-system">Squad &amp; keyword system</h2>'
             '<p>From Auroch Digital’s <a href="https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1847286114029178" rel="noopener">October 21 Feature Focus</a>: '
             'every character, weapon and some items carry one or more <strong>keywords</strong>. When your champion acquires a weapon their keywords do not allow, an ally who can use it joins as a <strong>follower</strong>. '
             'Followers attack on your behalf but <strong>cannot take damage or collect items</strong>, and several can squad up with one champion. Some champions are restricted to signature weapons (Marneus Calgar’s Gauntlets of Ultramar, Gotrek’s Zangrom-Thaz).</p>'
             '<p>The full launch roster is <strong>40+ characters</strong> (Steam page); the 18 below are the ones named in official or preview sources so far. Individual keyword lists are pending launch.</p>')
    tl = tools([("faction", "Universe", [("40K", "Warhammer 40,000"), ("AoS", "Age of Sigmar")]),
                ("type", "Type", [("champion", "Champion"), ("cameo", "Cameo")]),
                ("conf", "Source", [(k, v) for k, v in CONF.items()])], "Name, weapon, ability…")
    body = squad + tl + legend() + groups + (f'<p>Related: <a href="{P}characters/">demo roster guide</a> · <a href="{P}weapons/">weapons &amp; items codex</a> · '
                                             f'<a href="{P}weapon-evolutions/">evolution recipes</a> · <a href="{P}enemies/">enemies codex</a>.</p>')
    write("codex/characters/", page("codex/characters/", "Warhammer Survivors Character Codex — All Announced Champions",
          "Every announced Warhammer Survivors champion with universe, starting weapon, ability, unlock and squad notes — each entry sourced, demo-era.",
          "Character Codex", "Warhammer Survivors Character Codex",
          "All 18 champions named so far across Warhammer 40,000 and Age of Sigmar, with starting weapons, abilities, unlocks and squad combos.", body, "ss2.jpg"))
    return len(chars)


RECIPE_CARDS = {"whirlwind-axes", "eviscerator-chainsword", "meltagun", "mordant-earth"}


def build_weapons(weapons, chars):
    byid = {w["id"]: w for w in weapons}
    order = ["Weapon", "Evolution", "Passive", "Pick-up"]
    titles = {"Weapon": "Weapons", "Evolution": "Evolved weapons", "Passive": "Passives (evolution companions)", "Pick-up": "Pick-ups"}
    groups = {k: [] for k in order}

    def ref(i, conf=None):
        if not i or i == PENDING:
            return val(i)
        w = byid[i]
        tag = ' <span class="cx-b cx-c-community">unconfirmed</span>' if (conf or w["confidence"]) == "community" else ""
        return f'<a href="#{i}">{e(w["name"])}</a>{tag}'

    for w in weapons:
        f = []
        if w["type"] == "Weapon":
            f = [("Wielder", val(w.get("wielder"))), ("Evolves into", ref(w.get("evolves_to")) if w.get("evolves_to") else val(None))]
            req = next((x for x in weapons if x.get("evolves_from") == w["id"]), None)
            if req:
                rc = req.get("requires_conf", req["confidence"])
                f.append(("Evolution companion", ref(req.get("requires"), rc)))
        elif w["type"] == "Evolution":
            rc = w.get("requires_conf", w["confidence"])
            f = [("Base weapon", ref(w.get("evolves_from"))), ("Required passive", ref(w.get("requires"), rc)),
                 ("Level / trigger", f'<span class="pend">{PENDING}</span>')]
            if w["id"] in RECIPE_CARDS:
                f.append(("Recipe card", f'<a href="{P}weapon-evolutions/">Weapon evolutions page</a>'))
        elif w["type"] == "Passive":
            f = [("Pairs with", ", ".join(ref(i) for i in w.get("pairs_with", []))), ("Stat effect", val(None if w["confidence"] == "community" else "See description"))]
        else:
            f = [("Duration / values", f'<span class="pend">{PENDING}</span>')]
        badges = [fbadge(w["faction"]), f'<span class="cx-b">{e(w["type"])}</span>']
        groups[w["type"]].append(card(w, badges, f, {"faction": w["faction"], "type": w["type"].lower()}))
    sec = "".join(f'<section class="cx-group" aria-labelledby="g-{k.lower()}"><h2 id="g-{k.lower()}">{titles[k]}</h2><div class="cx-grid">{"".join(groups[k])}</div></section>' for k in order)
    intro = ('<p>The Steam page promises an arsenal of <strong>75+ weapons</strong> plus passives and power-ups; weapons combine with a specific passive to evolve. '
             'Some weapons are cross-universe (Nuln Oil, D6 Dice). Pick-ups are temporary on-field items that differ per universe. '
             f'Recipe cards with art live on the <a href="{P}weapon-evolutions/">weapon evolutions</a> page.</p>')
    tl = tools([("faction", "Universe", [("40K", "Warhammer 40,000"), ("AoS", "Age of Sigmar"), ("Cross", "Cross-universe"), ("Unconfirmed", "Unconfirmed")]),
                ("type", "Type", [(k.lower(), k) for k in order]),
                ("conf", "Source", [(k, v) for k, v in CONF.items()])], "Weapon, passive, effect…")
    body = intro + tl + legend() + sec + (f'<p>Related: <a href="{P}weapon-evolutions/">evolution recipes</a> · <a href="{P}codex/characters/">character codex</a> · '
                                          f'<a href="{P}power-ups/">power-ups guide</a> · <a href="{P}enemies/">enemies codex</a>.</p>')
    write("weapons/", page("weapons/", "Warhammer Survivors Weapons & Items Codex — Weapons, Evolutions, Passives",
          "Warhammer Survivors weapons, evolved weapons, passives and pick-ups announced so far, cross-linked to evolution recipes, with every entry sourced.",
          "Weapons & Items Codex", "Warhammer Survivors Weapons & Items Codex",
          "Announced weapons, their evolutions and companion passives, plus pick-ups — official, press and community-reported entries kept apart.", body, "ss3.jpg"))
    return len(weapons)


def build_enemies(enemies):
    order = []
    for x in enemies:
        if x["group"] not in order:
            order.append(x["group"])
    tiers = ["Normal", "Elite", "Boss"]
    out = []
    for g in order:
        mem = [x for x in enemies if x["group"] == g]
        mem.sort(key=lambda x: tiers.index(x["tier"]) if x["tier"] in tiers else 3)
        uni = mem[0]["faction"]
        stage = mem[0].get("stage")
        cards = []
        for x in mem:
            t = x["tier"]
            tk = t.lower() if t in tiers else "pending"
            badges = [fbadge(x["faction"]), f'<span class="cx-b cx-t-{tk}">{e(t if t in tiers else "Tier pending")}</span>']
            f = [("Faction", e(x["group"])), ("Stage", val(x.get("stage"))), ("HP / damage", f'<span class="pend">{PENDING}</span>')]
            cards.append(card(x, badges, f, {"faction": x["faction"], "tier": tk, "group": x["group"].lower()}))
        sub = f'<p class="cx-sub">{e(FAC[uni])} · stage: {val(stage)}</p>'
        gid = "g-" + g.lower().replace(" ", "-")
        out.append(f'<section class="cx-group" aria-labelledby="{gid}"><h2 id="{gid}">{e(g)}</h2>{sub}<div class="cx-grid">{"".join(cards)}</div></section>')
    intro = ('<p>Each stage has its own enemy faction (Steam page), each faction has its own <strong>Extremis Boss</strong> (April 9 announcement), and factions carry tabletop-inspired '
             '<strong>Faction Traits</strong> such as the Tyranid Synapse and the Ork Waaagh!. The Hobby Table stage mixes several factions from the same universe.</p>'
             '<div class="note"><strong>How tiers are assigned here:</strong> <em>Boss</em> = described as a boss or Extremis Boss; <em>Elite</em> = given a developer-described special skill or role; '
             '<em>Normal</em> = named as rank-and-file. The game’s own classification is pending launch.</div>')
    tl = tools([("faction", "Universe", [("40K", "Warhammer 40,000"), ("AoS", "Age of Sigmar"), ("Unconfirmed", "Unconfirmed")]),
                ("group", "Faction", [(g.lower(), g) for g in order]),
                ("tier", "Tier", [("normal", "Normal"), ("elite", "Elite"), ("boss", "Boss"), ("pending", "Tier pending")]),
                ("conf", "Source", [(k, v) for k, v in CONF.items() if k != "community"])], "Enemy, skill, faction…")
    body = intro + tl + legend() + "".join(out) + (f'<p>Related: <a href="{P}stages/">stages</a> · <a href="{P}codex/characters/">character codex</a> · <a href="{P}weapons/">weapons &amp; items</a>.</p>'
                                                   '<p class="credit">Enemy sprites: official in-game pixel art from Auroch Digital’s '
                                                   '<a href="https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1835236783557691" rel="noopener">Chaos detected</a> Steam post (each image sits directly above its unit’s heading) and the '
                                                   '<a href="https://news.xbox.com/en-us/2026/04/17/warhammer-survivors-reveals-mighty-ork-xbox-launch-2026" rel="noopener">Xbox Wire Ork reveal</a> (file names name the unit). Lettered tiles are placeholders.</p>')
    write("enemies/", page("enemies/", "Warhammer Survivors Enemies Codex — Factions, Elites & Extremis Bosses",
          "Warhammer Survivors enemies by faction: Tyranids, Orks, Death Guard, Skaven, Blades of Khorne and Gloomspite Gitz, with skills, stages and bosses — each entry sourced.",
          "Enemies Codex", "Warhammer Survivors Enemies Codex",
          "Every enemy named so far, grouped by faction, with developer-described skills, stage and tier.", body, "ss4.jpg"))
    return len(enemies)


def build_hub(n_c, n_w, n_e, counts):
    def cardlink(h, t, d, img):
        return (f'<a class="card" href="{P}{h}"><div class="thumb" style="background-image:url({P}assets/{img})"></div>'
                f'<div class="ct"><b>{t}</b><span>{d}</span></div></a>')
    rows = "".join(f"<tr><td>{e(n)}</td><td>{c['official']}</td><td>{c['press']}</td><td>{c['community']}</td><td>{sum(c.values())}</td></tr>" for n, c in counts)
    body = (f'<p>Three searchable reference lists built only from published sources. Each card shows where it came from and how firm it is; unknown values stay marked '
            f'<span class="pend">{PENDING}</span> until the November 10 release.</p>'
            '<div class="grid">' + cardlink("codex/characters/", "Character Codex", f"{n_c} champions · weapons, abilities, unlocks, squad combos", "ss2.jpg")
            + cardlink("weapons/", "Weapons & Items", f"{n_w} weapons, evolutions, passives, pick-ups", "ss3.jpg")
            + cardlink("enemies/", "Enemies", f"{n_e} enemies · 7 groups · elites and Extremis Bosses", "ss4.jpg") + "</div>"
            '<h2>Entries by source</h2><div class="cx-scroll"><table><tr><th>Codex</th><th>Official</th><th>Press</th><th>Community</th><th>Total</th></tr>' + rows + '</table></div>'
            + legend() +
            '<h2>Biggest gaps before launch</h2><ul><li>Unlock conditions for almost every champion outside the demo.</li>'
            '<li>Numeric stats: weapon damage, cooldowns, passive values, enemy HP.</li><li>Evolution level thresholds and triggers (community reports only).</li>'
            '<li>Character keyword lists and which weapons each can wield.</li><li>The full 40+ roster and 75+ weapon list.</li></ul>')
    write("codex/", page("codex/", "Warhammer Survivors Codex — Characters, Weapons & Enemies",
          "Searchable Warhammer Survivors codex: characters, weapons & items, and enemies, every entry tagged official, press or community.",
          "Codex", "Warhammer Survivors Codex", "Characters, weapons &amp; items, and enemies — sourced, filterable, demo-era.", body, "ss1.jpg"))


def main() -> int:
    from collections import Counter
    chars, weapons, enemies = load("characters"), load("weapons"), load("enemies")
    n_c = build_characters(chars, weapons)
    n_w = build_weapons(weapons, chars)
    n_e = build_enemies(enemies)
    counts = []
    for n, d in [("Characters", chars), ("Weapons & items", weapons), ("Enemies", enemies)]:
        c = Counter(x["confidence"] for x in d)
        counts.append((n, {k: c.get(k, 0) for k in ("official", "press", "community")}))
    build_hub(n_c, n_w, n_e, counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
