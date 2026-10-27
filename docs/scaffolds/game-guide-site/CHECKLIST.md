# Article checklist

Run this on every new `content/*.json` before `python3 build.py`. The three shapes in `templates/` already follow it. Sephiria itself is frozen: this list is for the next site, not a batch of new Sephiria URLs.

## TDH (title, description, H1)

- [ ] `title` is the `<title>`: the query a person types, plus a short differentiator (“Town Picker”, “Hidden Rooms”, “Summon Route”).
- [ ] `description` is the meta description: one or two sentences that answer the query. Unique to this URL.
- [ ] `h1` is the only H1. `body` has no `<h1>`. `tools/check_seo_consistency.py` fails a page that has any other count.
- [ ] `meta` is the status line under the H1 (who it is for, or “confirm in-game”), not a second title.
- [ ] Canonical is automatic: `{domain}{path}` from `config/site.json` and `path`. `path` starts and ends with `/` (`/` for home).

## One intent, one page

- [ ] The file answers one search question. A second question gets its own JSON and URL.
- [ ] The lead states the answer and, when a name collides, which object the page covers (town picker vs in-run fountain; one build family vs the builds overview).
- [ ] A parent hub stays an index. The long-tail steps live on the child URL (`/builds/summon/`, not a section pasted onto `/builds/` and `/`).
- [ ] Numbers that can change are marked community-reported or “verify in-game”. The `<div class="note">` carries the version or source limit.
- [ ] Facts come from sources you can cite in `sources`. The page does not invent item names, drop rates, or patch numbers.

## Related internal links

- [ ] The page links to the parent hub and to two or three sibling articles that share the same run (the build that uses the mechanic, the mechanic the build pre-loads).
- [ ] Links are relative to depth: `../sibling/` from `/town-picker/`, `../../sibling/` from `/builds/summon/`.
- [ ] The related block is either an `<h2>` whose text starts with `Related`, or a `<p>` whose text starts with `Related:`. `build.py` inserts the `before-related` ad immediately above that marker.
- [ ] Live `content/wishing-fountain.json` puts `Related:` mid-paragraph. Those links still work, and the second ad is appended after the body, because the marker has to start the heading or the paragraph. The templates open the related block at the start of a paragraph (`mechanic-picker.json`, `mechanic-hidden-find.json`) or with `<h2>Related guides</h2>` (`build-route.json`).
- [ ] `in_guides: true` plus `guides_label` and `guides_em` so the guides hub lists the page.
- [ ] `home_also` is set only for pages that belong on the short homepage “more” list.

## Ad slots

Ads are injected by `build.py`. Article JSON does not contain ad markup.

- [ ] `layout` is `article` or `hub` (both get ads). `legal` does not.
- [ ] The lead is a `<p>…</p>`. The `after-lead` unit is inserted after the first `</p>`.
- [ ] A Related heading or `Related:` paragraph is present so `before-related` sits above those links. With neither marker, that unit is appended at the end of `body`.
- [ ] Slots are in-flow (`data-ad-layout="in-article"`). The framework does not add a sticky unit, overlay, or popup.
- [ ] `ADSENSE_SLOTS` in `build.py` stays `""` until the new domain has numeric slot IDs in the AdSense console. An empty slot leaves the container and does not call `adsbygoogle.push`, so the gap collapses.
- [ ] The new domain gets its own `ADSENSE_CLIENT` and `ads.txt`. The Sephiria publisher id stays on the Sephiria site.

The Sephiria homepage also places `after-lead` under the intro and `before-related` above “More to explore”. A copied `home` layout inherits those two placements.

## Sitemap entry

- [ ] The file sits in `content/`, ends in `.json`, and does not start with `_`.
- [ ] `sitemap_exclude` is absent. Setting it drops the URL from `sitemap.xml` while leaving the HTML on disk.
- [ ] `robots.txt` points at `https://<new-domain>/sitemap.xml`.
- [ ] After build, the URL is in `dist/sitemap.xml` and `dist/<path>/index.html` exists. `tools/check_seo_consistency.py` checks that pair both ways.
- [ ] `lastmod` is the git date of the content file, otherwise `updated` in `config/site.json`.
- [ ] Long-tail articles stay indexable. `noindex` in this framework is the generated `404.html` and `login.html`, not a content-page switch. There is no bulk-noindex flag to flip later; residual URLs stay in the sitemap.

`layout: "legal"` is still listed in the sitemap at priority `0.3` and is left out of `llms.txt`.

## Homepage: no kitchen sink

- [ ] `home.json` is `layout: "home"` with a handful of `village` doors (the live site uses six), one CTA, and a short “what the game is”.
- [ ] Item tables, build routes, mechanic steps, and FAQs are article files. They are not pasted into `what_html` or the village intro.
- [ ] The full list is the guides hub (`layout: "hub"`, `hub: "guides"`), fed by `in_guides`.
- [ ] “More to explore” is the `home_also` set plus the hub link `build.py` appends. It is a directory, not a second copy of each article.

## After build

- [ ] The SEO checker exits 0. On a new domain, `ORIGIN` in `tools/check_seo_consistency.py` matches `config/site.json` `domain`, and the Sephiria-only login and privacy assertions are updated to that site.
- [ ] View source: one `<h1>`, canonical equals the public URL, description matches `description`.
- [ ] Click every related link and both breadcrumb parents.
- [ ] Sources render as a list under the body, from the `sources` array.
