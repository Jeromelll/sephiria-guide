#!/usr/bin/env python3
"""Generate Sephiria Guide static site from verified research notes only."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

NAV = [
    ("Guides", "/guides/"),
    ("Beginner", "/beginner-guide/"),
    ("Builds", "/builds/"),
    ("Weapons", "/weapons/"),
    ("Destiny", "/destiny-inscription/"),
    ("Bosses", "/bosses/"),
    ("Co-op", "/multiplayer/"),
]

STEAM = "https://store.steampowered.com/app/2436940/Sephiria/"
STEAM_NEWS = "https://steamcommunity.com/app/2436940/allnews/"
STEAM_GUIDE = "https://steamcommunity.com/sharedfiles/filedetails/?id=3474238982"


def css_href(depth: int) -> str:
    return "../" * depth + "assets/styles.css"


def link(depth: int, path: str) -> str:
    if path == "/":
        return "../" * depth if depth else "./"
    return "../" * depth + path.strip("/") + "/"


def shell(
    *,
    title: str,
    description: str,
    depth: int,
    path: str,
    body: str,
    h1: str | None = None,
    kicker: str = "Sephiria 1.0 fan guide",
) -> str:
    nav_html = []
    for label, href in NAV:
        current = ' aria-current="page"' if href.rstrip("/") in path.rstrip("/") else ""
        nav_html.append(f'<a href="{link(depth, href)}"{current}>{label}</a>')
    page_h1 = h1 or title.split("—")[0].strip()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <meta name="keywords" content="sephiria, sephiria wiki, sephiria builds, sephiria weapons, destiny inscription" />
  <link rel="canonical" href="https://sephiria-guide.com{path}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{css_href(depth)}" />
  <script src="{css_href(depth).replace('styles.css', 'analytics.js')}" defer></script>
</head>
<body>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="brand" href="{link(depth, '/')}">Sephiria <span>Guide</span></a>
      <nav class="nav">{''.join(nav_html)}</nav>
    </div>
  </header>
  <main>
{body}
  </main>
  <footer class="site-footer">
    <div class="narrow">
      <p>Unofficial fan guides for <a href="{STEAM}">Sephiria</a> by Team Horay. Not affiliated with the developer.</p>
      <p>Facts checked against Steam, community guides, and cross-sourced videos. EA-era numbers are marked when used.</p>
      <p><a href="{link(depth, '/guides/')}">All guides</a> · Updated 2026-08-12</p>
    </div>
  </footer>
</body>
</html>
"""


def article(depth: int, crumbs: list[tuple[str, str]], title: str, meta: str, content: str, sources: list[tuple[str, str]]) -> str:
    crumb_html = ' / '.join(
        (f'<a href="{link(depth, href)}">{label}</a>' if href else label)
        for label, href in crumbs
    )
    src = "".join(f'<li><a href="{u}" rel="noopener">{n}</a></li>' for n, u in sources)
    return f"""
  <div class="narrow">
    <p class="breadcrumbs">{crumb_html}</p>
    <h1 class="page-title">{title}</h1>
    <p class="meta-line">{meta}</p>
    {content}
    <section class="sources">
      <h2>Sources</h2>
      <ul>{src}</ul>
    </section>
  </div>
"""


PAGES: dict[str, tuple[str, str, str, str]] = {}


def add(path: str, title: str, description: str, body: str):
    depth = 0 if path == "/" else path.strip("/").count("/") + 1
    # path /bosses/erma/ -> depth 2; / -> 0; /guides/ -> 1
    if path == "/":
        depth = 0
    else:
        depth = len([p for p in path.strip("/").split("/") if p])
    html = shell(title=title, description=description, depth=depth, path=path, body=body)
    out = ROOT / ("index.html" if path == "/" else Path(path.strip("/")) / "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out.relative_to(ROOT))


# --- Home ---
home_body = f"""
  <section class="hero">
    <div class="wrap">
      <p class="hero-kicker">Fan guides · Updated for Sephiria 1.0</p>
      <h1>Sephiria Guide</h1>
      <p class="lede">Builds, weapons, Destiny Inscription, bosses, and co-op notes distilled from Steam and cross-checked sources—not AI filler.</p>
      <div class="cta-row">
        <a class="btn btn-primary" href="{link(0, '/beginner-guide/')}">Start beginner guide</a>
        <a class="btn btn-ghost" href="{STEAM}" rel="noopener">Steam page</a>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>What Sephiria is</h2>
      <p>Sephiria is a top-down action roguelite from Team Horay (also known for Dungreed). You descend floors, upgrade weapons at anvils, and build power through an Artifact + Tablet inventory grid. Full release landed <strong>July 31, 2026</strong> after Early Access; Steam lists six chapters, six weapon lines, and online co-op for up to four players.</p>
      <div class="note">This site is English-first P0 coverage for sephiria-guide.com. Patch-sensitive tips note when they come from older Steam Community guides.</div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>Start here</h2>
      <div class="grid-4">
        <a class="start-link" href="/beginner-guide/"><strong>Beginner Guide</strong><span>First-run priorities and common traps.</span></a>
        <a class="start-link" href="/builds/"><strong>Builds</strong><span>Commit to one or two combo tags.</span></a>
        <a class="start-link" href="/weapons/"><strong>Weapons</strong><span>Six branches, beginner picks, unlock notes.</span></a>
        <a class="start-link" href="/destiny-inscription/"><strong>Destiny Inscription</strong><span>Permanent sapphire tree and talents.</span></a>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>Also covered</h2>
      <div class="guide-list">
        <a href="/bosses/erma/"><strong>Erma boss guide</strong><em>Mad Scientist · Floor 3</em></a>
        <a href="/multiplayer/"><strong>Multiplayer / co-op</strong><em>Stone-wall lobby + invite notes</em></a>
        <a href="/secret-rooms/"><strong>Secret rooms</strong><em>Cracked walls & post-Erma lore room</em></a>
        <a href="/costumes/"><strong>Costumes</strong><em>Starter skins & hidden unlocks</em></a>
        <a href="/items/scythe/"><strong>How to get the Scythe</strong><em>Blizzard Scythe via Drifa—not a 6th weapon</em></a>
        <a href="/guides/"><strong>Full guide index</strong><em>Wiki-style navigation</em></a>
      </div>
    </div>
  </section>
"""
add(
    "/",
    "Sephiria Guide — Builds, Weapons, Wiki Tips",
    "Fan guides for Sephiria: beginner tips, builds, weapons, Destiny Inscription, bosses, co-op, and secret rooms. Updated for the 1.0 release.",
    home_body,
)

# --- Guides index ---
guides_content = """
<p>Looking for a Sephiria wiki-style hub? Use this index. Pages answer real search intents from Google Suggest / Trends / SimilarWeb research—not a dump of every noun in the game.</p>
<div class="guide-list">
  <a href="../beginner-guide/"><strong>Beginner guide</strong><em>First run</em></a>
  <a href="../builds/"><strong>Builds</strong><em>Combo focus</em></a>
  <a href="../weapons/"><strong>Weapons</strong><em>Six branches</em></a>
  <a href="../destiny-inscription/"><strong>Destiny Inscription</strong><em>Permanent tree</em></a>
  <a href="../artifacts/"><strong>Artifacts & Tablets</strong><em>Inventory grid</em></a>
  <a href="../bosses/"><strong>Bosses</strong><em>Erma · Final</em></a>
  <a href="../multiplayer/"><strong>Multiplayer</strong><em>Co-op lobby</em></a>
  <a href="../secret-rooms/"><strong>Secret rooms</strong><em>Cracks & lore rooms</em></a>
  <a href="../costumes/"><strong>Costumes</strong><em>Unlocks</em></a>
  <a href="../items/scythe/"><strong>Scythe</strong><em>Drifa / Blizzard Scythe</em></a>
</div>
"""
add(
    "/guides/",
    "Sephiria Wiki / Guide Hub — Sephiria Guide",
    "Sephiria guide index: beginner tips, builds, weapons, Destiny Inscription, bosses, multiplayer, and secrets.",
    article(1, [("Home", "/"), ("Guides", "")], "Sephiria guide hub", "Maps to searches like sephiria wiki / sephiria guide.", guides_content, [
        ("Steam store", STEAM),
        ("Steam Basic Guide", STEAM_GUIDE),
    ]),
)

beginner = """
<p>Sephiria throws systems at you fast. Treat the first dozen runs as unlocking the Destiny tree and learning one build sentence—not chasing every shiny Artifact.</p>
<h2>Core loop</h2>
<ul>
  <li>Pick a costume and weapon, enter a floor, choose nodes (Anvil / Dice / combat / shops).</li>
  <li>Spend Sapphires after runs on the Destiny Inscription permanent tree.</li>
  <li>Open the Journal (Esc) to review unlocked weapons, Artifacts, Tablets, and Miracles before committing.</li>
</ul>
<h2>First-run priorities</h2>
<ul>
  <li><strong>Do New Events</strong> on the Destiny tree—they unlock systems (wishing fountain, costumes salon, weapons) that snowball later.</li>
  <li><strong>Prefer Anvil early</strong> so your weapon skill matches the build you are forcing.</li>
  <li><strong>Side Bag is not free power</strong>—items stored there are inactive (including Tablets).</li>
  <li><strong>Commit to 1–2 combo tags</strong> (Storm Cloud, Companion, Glacier, etc.). Diluting five tags starves Tablet payoffs.</li>
</ul>
<div class="note">Steam Community “Basic Guide” still helps for systems vocabulary, but prefer 1.0-era writeups for route advice after the July 31, 2026 full release.</div>
<h2>Combat habits that transfer</h2>
<ul>
  <li>Perfect Guard saves huge MP versus holding block.</li>
  <li>Reorganize inventory after bosses—adjacency and Tablet geometry matter more than raw rarity.</li>
  <li>Fruit Skewers bias which combo families appear; frozen fruit can suppress junk families.</li>
</ul>
"""
add(
    "/beginner-guide/",
    "Sephiria Beginner Guide — First Run Tips",
    "Sephiria beginner guide: first-run priorities, Side Bag rules, Destiny New Events, and combat habits for 1.0.",
    article(1, [("Home", "/"), ("Beginner", "")], "Sephiria beginner guide", "For searches like sephiria beginner guide / walkthrough.", beginner, [
        ("Steam Basic Guide", STEAM_GUIDE),
        ("9Puz 1.0 beginner", "https://9puz.com/3580-sephiria-first-run/"),
        ("YT: 10 Things the Game Doesn’t Tell You", "https://www.youtube.com/watch?v=BgYwuTVTEzE"),
        ("YT: 1.0 advanced tips", "https://www.youtube.com/watch?v=wXSOeKAbelM"),
    ]),
)

builds = """
<p>Strong Sephiria builds are boring on purpose: pick a theme, feed it, and let Tablets amplify the pieces that matter.</p>
<h2>Build rules that keep showing up</h2>
<ul>
  <li>Force <strong>one or two combo families</strong> (Storm Cloud, Companion, Ember/Solar, Glacier, Magitech…).</li>
  <li>Use Bond Artifacts to bridge two combos—you usually only need one side active to start seeing them.</li>
  <li>Stack levels into a few carry Artifacts instead of spreading upgrades evenly.</li>
  <li>After every new Tablet/Artifact, pause and rebuild adjacency.</li>
</ul>
<h2>Starter themes (community consensus)</h2>
<ul>
  <li><strong>Storm Cloud / Magitech</strong> — lightning cloud DPS while you focus bosses.</li>
  <li><strong>Companion</strong> — summons soak aggro; strong in co-op.</li>
  <li><strong>Sword &amp; Shield tank / reflect</strong> — learn patterns with Perfect Guard; Shield Bash is a beginner-friendly weapon skill path.</li>
  <li><strong>Frost / Ice Armament</strong> — dagger path can convert Blizzard Hammer into Blizzard Scythe via Drifa (see Scythe page).</li>
</ul>
<div class="note">Offer rates differ by weapon branch—Greatsword upgrades appear more often than Dagger in community 1.0 data—so “best” also means “completes more often.”</div>
"""
add(
    "/builds/",
    "Sephiria Builds — Best Themes for 1.0",
    "Sephiria builds guide: combo focus, Storm Cloud, Companion, shield tank, and frost themes for version 1.0.",
    article(1, [("Home", "/"), ("Builds", "")], "Sephiria builds", "Answers sephiria builds / companion / planet-style queries at a theme level.", builds, [
        ("9Puz first build", "https://9puz.com/3580-sephiria-first-run/"),
        ("SlashSkill weapons & builds", "https://www.slashskill.com/sephiria-best-weapons-and-builds-for-1-0-all-6-weapon-types-ranked/"),
        ("YT companion build", "https://www.youtube.com/watch?v=EftqxGiFgbM"),
    ]),
)

weapons = """
<p>Sephiria has <strong>six weapon branches</strong>, each with large upgrade trees. There is no separate “Scythe” starter weapon—see the dedicated Scythe page if that is what you searched.</p>
<h2>How community tier lists currently read (1.0)</h2>
<ul>
  <li><strong>Greatsword</strong> — high damage, generous upgrade offers; slower swings.</li>
  <li><strong>Sword &amp; Shield</strong> — best learner kit; block/reflect and Shield Bash paths.</li>
  <li><strong>Staff / Magic</strong> — versatile spells; Staff unlocks via Destiny weapon training after chapter progress.</li>
  <li><strong>Crossbow</strong> — safer ranged option with reload discipline.</li>
  <li><strong>Blade / Katana</strong> — aggressive melee, higher mastery curve.</li>
  <li><strong>Dagger</strong> — fastest hits / status; lower offer rate, higher commitment.</li>
</ul>
<h2>Unlock pattern (example: Staff)</h2>
<ol>
  <li>Progress the required chapter / patch.</li>
  <li>Buy the weapon training node on Destiny Inscription (Staff example: Graceful Weapon Training for Sapphires).</li>
  <li>Talk to Morrow, complete the short training ground, then the weapon appears on the village rack.</li>
</ol>
<div class="note">Exact sapphire costs and node names can shift with patches—verify in your client Journal / Destiny UI.</div>
"""
add(
    "/weapons/",
    "Sephiria Weapons Tier Notes — Six Branches",
    "Sephiria weapons guide: six branches, beginner Sword & Shield, Staff unlock path, and links to the Scythe clarification page.",
    article(1, [("Home", "/"), ("Weapons", "")], "Sephiria weapons", "Covers sephiria weapons / tier list / unlock dagger intent at branch level.", weapons, [
        ("Destructoid 1.0 weapons tier list", "https://www.destructoid.com/sephiria-1-0-weapons-tier-list/"),
        ("SlashSkill six weapon types", "https://www.slashskill.com/sephiria-best-weapons-and-builds-for-1-0-all-6-weapon-types-ranked/"),
        ("YT Shield Bash build", "https://www.youtube.com/watch?v=9DEtDVr4fqs"),
        ("YT Staff unlock", "https://www.youtube.com/watch?v=VqwdlBnFZ40"),
    ]),
)

destiny = """
<p>Destiny Inscription is Sephiria’s permanent meta tree. Sapphires come from dungeon depth and bosses defeated; spending them unlocks weapons, events, inventory, dice, and talent access.</p>
<h2>Early spends that matter</h2>
<ul>
  <li><strong>New Events / fruit skewers lines</strong> — unlock systems you will use every run.</li>
  <li><strong>Home Repairs</strong> — progresses village quests and opens Talents (talk to the relevant NPCs after unlocking).</li>
  <li><strong>Weapon training nodes</strong> — required before Morrow’s training grounds grant new weapons.</li>
  <li><strong>Hard Mode root unlock</strong> — appears after Chapter II progress and grants extra talent budget (per Steam guide).</li>
</ul>
<h2>Talents</h2>
<p>Once unlocked, talent points let you bias defense, MP regen, Willpower (luck-like outcomes), dash windows, and more. Guides agree you can respec—use that to match the weapon you are learning.</p>
"""
add(
    "/destiny-inscription/",
    "Sephiria Destiny Inscription — Sapphire Tree & Talents",
    "Sephiria Destiny Inscription guide: sapphire spends, New Events, Home Repairs, weapon unlocks, and talents.",
    article(1, [("Home", "/"), ("Destiny Inscription", "")], "Destiny Inscription", "For sephiria destiny inscription / best talents searches.", destiny, [
        ("Steam Basic Guide · Destiny", STEAM_GUIDE),
        ("Pro Game Guides talents section", "https://progameguides.com/sephiria/sephiria-beginners-guide-best-artifacts-talents-more/"),
    ]),
)

artifacts = """
<p>Artifacts and Tablets are the mid-run puzzle. Tablets buff geometry (lines, crosses, columns). An Artifact outside an active pattern wastes space.</p>
<ul>
  <li>Side Bag storage <strong>disables</strong> effects—use it as a bench, not a secret second board.</li>
  <li>Adjacency / edge / “no neighbors” constraints force full reshuffles after bosses.</li>
  <li>Mystic Pot can convert leftover Artifacts (same rarity, or feed two to climb a rarity)—handy for awkward drops.</li>
</ul>
"""
add(
    "/artifacts/",
    "Sephiria Artifacts & Tablets — Inventory Grid Tips",
    "Sephiria Artifact and Tablet guide: Side Bag rules, adjacency, and why tablet geometry beats raw rarity.",
    article(1, [("Home", "/"), ("Artifacts", "")], "Artifacts & Tablets", "Supports artifact / tablet searches; pairs with builds pages.", artifacts, [
        ("2UpSkill artifact grid", "https://2upskill.com/sephiria-1-0-artifact-placement-grid-guide-best-combos-and-inventory-layouts/"),
        ("9Puz first build", "https://9puz.com/3580-sephiria-first-run/"),
        ("YT 10 Things…", "https://www.youtube.com/watch?v=BgYwuTVTEzE"),
    ]),
)

bosses = """
<p>Boss pages will expand as we verify more pattern notes. Start with the high-search fights:</p>
<div class="guide-list">
  <a href="./erma/"><strong>Erma — Mad Scientist</strong><em>Floor 3 library line</em></a>
  <a href="./final/"><strong>Final boss (Qliphoth line)</strong><em>Chapter 6 / endgame</em></a>
</div>
"""
add(
    "/bosses/",
    "Sephiria Bosses — Guide Index",
    "Sephiria bosses hub linking to Erma and final boss notes for version 1.0.",
    article(1, [("Home", "/"), ("Bosses", "")], "Sephiria bosses", "Navigation page for boss intents.", bosses, [
        ("Steam news / patches", STEAM_NEWS),
        ("ProdigyGamers achievements", "https://prodigygamers.com/2026/08/06/sephiria-100-achievements-walkthrough-guide/"),
    ]),
)

erma = """
<p><strong>Erma, the Mad Scientist</strong>, is the Floor 3 / library-line boss (Steam achievement “This Is Not Stalking”). From Chapter 2 onward she can be replaced by Pantaxis, Guardian of the Library.</p>
<h2>Fight structure (NamuWiki cross-check)</h2>
<ul>
  <li>About <strong>three phases</strong> involving a golem Erma pilots.</li>
  <li>Golem head and hands have <strong>separate hitboxes</strong>—wide attacks that clip multiple parts deal more effective damage.</li>
  <li>When golem HP depletes, Erma becomes targetable; deplete her HP to advance phases.</li>
</ul>
<h2>Key pattern note — dual lasers</h2>
<p>Hands park top/bottom and scrape lasers across the arena while the head sprays. The clean dodge is to <strong>dash in the moment both lasers overlap and move the same direction</strong> (speeds are unequal). If tanky, sitting in the safer band and eating minimal chip can be better than panicking.</p>
<h2>Weaknesses</h2>
<ul>
  <li>AoE that hits multiple parts.</li>
  <li>Status effects applied to any part count for the whole (freeze on a hand freezes the head; burns scale hard).</li>
  <li>High-damage runs often just delete the head first when full AoE is awkward.</li>
</ul>
"""
add(
    "/bosses/erma/",
    "Sephiria Erma Guide — Mad Scientist Boss",
    "Sephiria Erma boss guide: phases, golem hitboxes, laser dodge timing, status weaknesses, and Pantaxis replacement note.",
    article(2, [("Home", "/"), ("Bosses", "/bosses/"), ("Erma", "")], "Erma (Mad Scientist)", "For sephiria erma searches.", erma, [
        ("NamuWiki Boss · Erma", "https://en.namu.wiki/w/%EC%84%B8%ED%94%BC%EB%A6%AC%EC%95%84/%EB%B3%B4%EC%8A%A4"),
        ("YT run with Erma fight", "https://www.youtube.com/watch?v=sQ_oYpLXZ4s"),
        ("YT All Bosses (EA) @ Erma", "https://www.youtube.com/watch?v=xC9ofSpci8U"),
        ("YT Library replacement boss short", "https://www.youtube.com/watch?v=iRqqwRa-bTk"),
    ]),
)

final = """
<p>The story climax sits in the late chapters around the <strong>Qliphoth</strong> fight line. Steam patches after 1.0 explicitly tuned final-boss readability (bullet density, warning indicators, Hard Mode clear flags).</p>
<ul>
  <li>Expect multi-phase pressure; community clear videos often melt phases with stacked burn/frost/scythe setups.</li>
  <li>Use official patch notes when something “feels wrong”—several patterns were hotfix-adjusted in mid-August patches.</li>
</ul>
<div class="note">We keep this page shorter until more pattern tables are dual-sourced beyond montage footage.</div>
"""
add(
    "/bosses/final/",
    "Sephiria Final Boss — Qliphoth Notes",
    "Sephiria final boss notes for the Qliphoth endgame fight, with Steam patch cross-checks.",
    article(2, [("Home", "/"), ("Bosses", "/bosses/"), ("Final boss", "")], "Final boss", "For sephiria final boss searches.", final, [
        ("grindnstrat bosses guide", "https://grindnstrat.com/sephiria-1-0-bosses-guide/"),
        ("Steam allnews / patches", STEAM_NEWS),
        ("YT final boss hard mode", "https://www.youtube.com/watch?v=R7rdy_owfbo"),
    ]),
)

multi = """
<p>Steam lists online co-op for up to <strong>four players</strong> with trading and revive support. Host disconnects can ruin the lobby—expect host-authoritative progress.</p>
<h2>How to open a lobby (quick)</h2>
<ul>
  <li>In the village / hub, find the large <strong>stone wall next to the dungeon entrance</strong>.</li>
  <li>Interact to create a lobby—you do not need to clear story gates first (per short tutorial footage).</li>
  <li>Invite via Steam; PixelNitro’s 1.0 writeup also describes the Mysterious Door / host flow.</li>
</ul>
"""
add(
    "/multiplayer/",
    "Sephiria Multiplayer — How to Invite Friends",
    "Sephiria multiplayer guide: 4-player co-op, stone-wall lobby creation, Steam invites, and host caveats.",
    article(1, [("Home", "/"), ("Multiplayer", "")], "Sephiria multiplayer", "For sephiria multiplayer / co-op / invite searches.", multi, [
        ("Steam Features", STEAM),
        ("PixelNitro multiplayer guide", "https://pixelnitro.com/sephiria-multiplayer-guide-how-to-invite-friends-for-online-co-op-version-1-0/"),
        ("YT how to create a lobby", "https://www.youtube.com/watch?v=3Eq4REN8wEQ"),
    ]),
)

secrets = """
<p>Secret rooms are an achievement (“Traveler”) and a real loot swing.</p>
<h2>Standard secret rooms</h2>
<ul>
  <li>Scan dungeon walls for <strong>subtle cracks near the top</strong>.</li>
  <li>Walk up and strike the crack. A notification confirms the find.</li>
  <li>The room appears on the map without a drawn passage. Rewards include leaves, Artifacts/Tablets, dice, or rare potions.</li>
</ul>
<h2>Special post-Erma room (community)</h2>
<p>After defeating Erma, cross the bridge; on the left side of the table in the next room you can <strong>walk under the wall</strong>—no crack. Players report it as mostly lore.</p>
<div class="note">Treat the crackless room as community experience; cracked-wall rooms are documented in the Steam Basic Guide with screenshots.</div>
"""
add(
    "/secret-rooms/",
    "Sephiria Secret Rooms — Cracked Walls Guide",
    "Sephiria secret rooms guide: how to spot cracked walls, Traveler achievement, and the post-Erma lore room.",
    article(1, [("Home", "/"), ("Secret rooms", "")], "Secret rooms", "For sephiria secret rooms / hidden room searches.", secrets, [
        ("Steam Basic Guide · Secret Room", STEAM_GUIDE),
        ("Steam discussion: secrets?", "https://steamcommunity.com/app/2436940/discussions/0/596280581879355354/"),
        ("ProdigyGamers Traveler achievement", "https://prodigygamers.com/2026/08/06/sephiria-100-achievements-walkthrough-guide/"),
    ]),
)

costumes = """
<p>Costumes change <strong>opening stats</strong>, not just looks. Align the skin with the weapon you plan to push.</p>
<h2>Unlock buckets (Steam Basic Guide)</h2>
<ul>
  <li>Several costumes unlocked by default.</li>
  <li>Task-based unlocks (e.g., grab many Tablets in one run for Red Fox).</li>
  <li>Secret costumes:
    <ul>
      <li><strong>Skeleton</strong> — take 333 cumulative damage in a single run.</li>
      <li><strong>Wingless Bat</strong> — complete Blood Donation (Manoc / iron maiden) five times across runs.</li>
      <li><strong>Adventurer</strong> — commonly tied to owning Dungreed; Steam guide author marks this as uncertain.</li>
    </ul>
  </li>
</ul>
"""
add(
    "/costumes/",
    "Sephiria Costumes — Unlocks & Hidden Skins",
    "Sephiria costumes guide: starter skins, Skeleton, Wingless Bat blood donation unlock, and Adventurer caveat.",
    article(1, [("Home", "/"), ("Costumes", "")], "Sephiria costumes", "For sephiria costumes searches.", costumes, [
        ("Steam Basic Guide · Costumes", STEAM_GUIDE),
        ("Treyex beginner · costumes", "https://www.treyexgaming.com/sephiria-beginner-guide/"),
        ("YT unlock Bat", "https://www.youtube.com/watch?v=BipTb4jrM8o"),
    ]),
)

scythe = """
<div class="note"><strong>Search intent check:</strong> “How to get the scythe in Sephiria” usually means the <em>Blizzard Scythe</em> weapon skill—not a seventh starter weapon. Official branch lists stop at six.</div>
<h2>Blizzard Scythe path (Dagger)</h2>
<ol>
  <li>Play <strong>Dagger</strong>.</li>
  <li>At the Anvil, take the frost enhancement line <strong>Dormant Frost</strong>.</li>
  <li>Second enhancement <strong>Drifa</strong> converts <strong>Blizzard Hammer</strong> into <strong>Blizzard Scythe</strong>.</li>
</ol>
<p>Korean clear videos build around Ice Armament + Precision, shop needles (Northbound Golden Needle), and Glacier support. Once Drifa lands, dash-fired scythes become the carry.</p>
<h2>Not the same item</h2>
<p><strong>Verut’s Scythe</strong> can drop as an Artifact tied to execution/crit fantasies. Do not confuse it with the Drifa weapon conversion.</p>
"""
add(
    "/items/scythe/",
    "How to Get the Scythe in Sephiria — Blizzard Scythe / Drifa",
    "How to get the scythe in Sephiria: Dagger → Dormant Frost → Drifa turns Blizzard Hammer into Blizzard Scythe. Not a sixth weapon branch.",
    article(2, [("Home", "/"), ("Weapons", "/weapons/"), ("Scythe", "")], "How to get the Scythe", "Clarifies the high-volume scythe query.", scythe, [
        ("YT Blizzard Scythe all-in", "https://www.youtube.com/watch?v=sQ_oYpLXZ4s"),
        ("YT same build description card", "https://www.youtube.com/watch?v=XMEXRKQZ8o4"),
        ("Destructoid weapons (no scythe branch)", "https://www.destructoid.com/sephiria-1-0-weapons-tier-list/"),
    ]),
)

print("done")
