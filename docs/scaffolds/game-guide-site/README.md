# Next-game guide site (JSON + `build.py`)

Docs only. Sephiria’s live pages stay under a content freeze: do not add `content/*.json` files or URLs from this folder. `build.py` reads `content/*.json` and ignores `docs/`.

These notes extract the item / mechanic pattern that already earns residual traffic, so the next guide site can be stood up without inventing a second framework.

## Warhammer is a different tree

Warhammer Survivors is the hand-authored static site in `extra_sites/warhammer-survivors`. `build.py` does not build it from JSON. The slug is in `MOVED_SITES`, so the Sephiria deploy 301s those paths to `warhammersurvivors.com`, where `tools/build_standalone_wh.py` is the publisher.

This scaffold is the other pattern: `config/site.json` + `content/*.json` + `build.py`. Use it for the next guide site. Leave the Warhammer tree on its own workstream.

## How a Sephiria page is driven

Three layers. The live site already documents them in the repo README; this is the contract to copy.

| Layer | Where | What it owns |
|---|---|---|
| Framework | `build.py`, `assets/styles.css` | HTML shell, article layout, ads, sitemap, canonical |
| Config | `config/site.json` | Game name, domain, nav, theme, Steam links, `updated` |
| Content | `content/*.json` | One URL per file |

`python3 build.py` loads every `content/*.json` whose name does not start with `_`, sorts by `order` then `path`, and writes `dist/<path>/index.html`. A missing `layout` means `article`. The sitemap, guides hub, and homepage “More to explore” list are derived from fields on those files.

```bash
python3 build.py
python3 tools/check_seo_consistency.py   # one H1, canonical, sitemap ↔ dist
```

`tools/swap_test.py` checks that header, footer, canonical, and theme follow `config/site.json`. Body copy that is still written in `build.py` is listed under [Spin-up](#spin-up).

## Page types that worked

Ship **one search intent per article**. The three files below are the pattern to copy. Names in `templates/` are placeholders (`Example Game`, Town Picker, Hidden Rooms, Summon Route), stripped from the live pages.

| Proven page | Source file | Template | Why it worked |
|---|---|---|---|
| Item / town mechanic | `content/wishing-fountain.json` | `templates/mechanic-picker.json` | Names the object in the first sentence, separates it from the same-named in-run object, then covers unlock and capacity with “verify in-game”. |
| Find / hidden mechanic | `content/secret-rooms.json` | `templates/mechanic-hidden-find.json` | A single procedure (spot, confirm, map), a failure-mode list, and an FAQ that admits what the source does not prove. |
| One build route | `content/builds-companion.json` | `templates/build-route.json` | One family only. Checklist, run habits, mistakes, short FAQ, link back to the parent hub. The overview stays on its own URL. |

Shared shape of those articles:

1. Lead paragraph: the query phrase in `<strong>`, then the one-sentence answer.
2. A few `<h2>` sections that do that job only (what it is, how, checklist, mistakes or FAQ).
3. One `<div class="note">` for a version caveat or a name collision.
4. A related-links block `build.py` can see (see [CHECKLIST](CHECKLIST.md)).
5. `sources`: `[label, url]` pairs. The Sources heading is rendered by `build.py`, not typed into `body`.
6. `in_guides`, `guides_label`, and `guides_em` so `/guides/` lists the page.
7. `home_also` only when the page deserves a tile under “More to explore”.
8. `crumbs`: last pair has an empty href (current page).
9. `order`: integer. Lower sorts earlier. Homepage is `0`.

Body links are relative to the page depth. `/town-picker/` links with `../other/`. `/builds/summon/` links with `../../other/` and `../` for the parent hub. The body must not contain an `<h1>`; the template prints the only one from `h1`.

Hubs (`layout: "hub"`, `content/guides.json`) are indexes: an `intro` plus a list of every page with `in_guides: true`. Boss hubs filter `path` starting with `/bosses/` and `layout: "article"`.

The homepage (`layout: "home"`, `content/home.json`) is a short door list. Sephiria’s home renders `village` (six destinations), one CTA, a short “what the game is”, and `home_also` as “More to explore”. `home_start` is stored on some live pages; the current home template reads `village` instead.

## Field map (article)

The files in `templates/` validate against `schema/article-page.schema.json`.

| Field | Role |
|---|---|
| `path` | Canonical path, trailing slash, e.g. `/town-picker/` or `/builds/summon/`. This is the URL, not the filename. |
| `title` | `<title>`. Query plus a differentiator. |
| `description` | Meta description. The answer, unique to this URL. |
| `h1` | The only visible H1. |
| `meta` | The line under the H1 (status, who the page is for). |
| `body` | HTML. Lead must be a `<p>` so the first ad can sit after it. |
| `layout` | `article` for this pattern. Also used: `home`, `hub`, `legal`. |
| `crumbs` | `[[label, href], …]`. Last href is `""`. |
| `sources` | `[[label, url], …]`. |
| `in_guides` | `true` to appear on the guides hub. |
| `guides_label` / `guides_em` | Hub row title and italic subtitle. |
| `home_also` | `{ "title", "em" }` for the homepage “more” list. Omit it to stay off that list. |
| `order` | Sort key. Sitemap priority uses this order (home `1.0`, the next four pages `0.9`, the rest `0.8`; `legal` is forced to `0.3`). |
| `sitemap_exclude` | Omit the URL from `sitemap.xml` when `true`. Leave it off for pages you want indexed. |

`config/guide-visuals.json` can attach a cover keyed by `path`. Articles render without it. `build.py` treats a missing file as no media. On a new site, omit Sephiria’s visuals map until you have art.

Filename and URL may differ: `content/builds-companion.json` serves `/builds/companion/`. A file named `_draft.json` is skipped, which is the local way to hold a page back.

## Spin-up

1. New repository (or a new site config). Do not add pages under this repo’s `content/`.
2. Copy `build.py`, `assets/`, `tools/check_seo_consistency.py`, `robots.txt`, and `config/site.json`. Start `content/` from the three templates plus a home page and a guides hub.
3. Edit `config/site.json`: `game_name`, `brand_name`, `brand_suffix`, `site_name`, `domain`, `developer`, `seo_keywords`, `footer_line`, `footer_facts`, `theme`, `nav`, `links`, `updated`. Keep `nav` short. The copied SEO checker looks for the literal nav markup `href="/login.html">Log in</a>`; keep that item until you change the checker.
4. Edit the Sephiria sentences that `swap_test.py` does not touch, all in `build.py`:
   - `home_body` image alts, and the village noticeboard links
   - `stuck_prompt` (the “still stuck?” line)
   - footer guide links and the “Other games we cover” line
   - `write_404` copy
   - `ADSENSE_CLIENT`, `ADSENSE_SLOTS`, and repo-root `ads.txt` (see the checklist)
5. Replace `assets/img` village and capsule art when the game changes. The article layout does not use them. The home layout does, and village door `id`s are CSS hooks (`destination--{id}`).
6. Point the `Sitemap:` line in `robots.txt` at the new domain.
7. `python3 build.py`, then the SEO checker. `tools/check_seo_consistency.py` is pinned to `https://sephiria-guide.com` (`ORIGIN`) and also requires the login assets plus the privacy sentence `Optional account sign-in`. On the next site, point `ORIGIN` at the new domain and keep the portable checks: one `<h1>`, canonical host equals that domain, sitemap URL has a matching `dist` file and every public page is in the sitemap. Read three articles in `dist/`: the lead answers the query, there is one H1, related links resolve, Sources rendered from `sources`.

Homepage shell, kept small on purpose:

```json
{
  "path": "/",
  "layout": "home",
  "title": "Example Game Guide — First Unlock, One Build",
  "description": "Just bought Example Game? Open the first unlock, then one build route. Short pages with sources.",
  "hero_kicker": "Fan guides",
  "hero_h1": "Your adventure starts here.",
  "village_intro": "Choose a building to find your next guide.",
  "cta_label": "Start the beginner guide",
  "cta_path": "/getting-started/",
  "what_h2": "What Example Game is",
  "what_html": "<p>One sentence on genre, developer, and the loop. Link out to the articles.</p>",
  "order": 0,
  "village": [
    { "id": "inn", "path": "/getting-started/", "title": "Getting started", "description": "First run" }
  ]
}
```

Guides hub shell:

```json
{
  "path": "/guides/",
  "layout": "hub",
  "hub": "guides",
  "title": "Example Game Guide Index",
  "description": "Every guide on the site.",
  "h1": "Example Game guides",
  "meta": "Index of one-intent pages.",
  "intro": "Every guide on the site. New players start with the beginner page.",
  "crumbs": [["Home", "/"], ["Guides", ""]],
  "order": 10
}
```

Run the [checklist](CHECKLIST.md) on each article before the build.
