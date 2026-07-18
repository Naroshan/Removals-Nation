# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

RemovalsNation — a pure static HTML/CSS site (no framework, no build tool, no `node_modules`) for a UK
removals company. It's a **Python static site generator**: scripts read a Python-literal locations
database and stamp out one page per location × service combination as plain HTML into `dist/`, plus a
handful of hand-authored top-level pages. `dist/` is committed (not gitignored) — Netlify deploys it
directly via `netlify.toml` (`publish = "dist"`, no build command), so the repo is deployable as-is
without Netlify needing to run Python.

- Hosting: Netlify, deploying `dist/` from this repo (see `netlify.toml`)
- Forms: Formspree (form ID `xkododjy`), POSTs from every booking/contact form, redirects to `/thank-you.html`
- Fonts: Syne (headings) + DM Sans (body), loaded from Google Fonts
- Domain: `removalsnation.com` (GoDaddy DNS → Netlify)

## Commands

```bash
# Full rebuild of dist/ from source (run all three, in order)
python scripts/locations_db.py       # regenerates data/locations.json from ALL_LOCATIONS
python scripts/build_pages.py        # generates dist/{service}/{location}/index.html + locations.html
python scripts/build_static_pages.py # generates dist/index.html, about, contact, privacy, thank-you,
                                      #   blog (+posts), partner-with-us, and dist/{service}/index.html
mkdir -p dist/assets && cp docs/assets/*.svg docs/assets/*.ico docs/assets/*.png docs/assets/*.webmanifest dist/assets/
                                      # ^ favicon/icon files — not copied by either script
python scripts/minify_css.py         # minifies docs/assets/shared.css into dist/assets/shared.css
python scripts/build_sitemap.py      # generates dist/sitemap.xml, robots.txt, llms.txt

python scripts/build_pages.py --force                # rebuild even existing location/service pages
python scripts/build_pages.py --service man-and-van   # build one service only
python scripts/build_pages.py --dist output           # custom output dir
python scripts/inject_mobile_menu.py                  # patch mobile-menu markup into HTML that lacks it
```

There is no test suite, linter, or build step beyond these scripts — "correctness" here means the
generated HTML in `dist/` is well-formed and the scripts run to completion. Verify changes by running
the relevant script and spot-checking output files (e.g. `dist/house-removals/camden/index.html`), or
serve `dist/` locally with `python -m http.server` and click through.

**After changing any script, always rerun the full pipeline above and re-commit `dist/`** — the committed
HTML is what Netlify actually serves; editing the generator alone does nothing to the live site.

## Architecture

**`scripts/locations_db.py`** — a single large `ALL_LOCATIONS` list of tuples:
`(display_name, region, county, postcode_prefix, url_slug)`, covering UK towns/boroughs/
neighbourhoods (Greater London boroughs and neighbourhoods, then counties/regions across England,
Scotland, Wales, Northern Ireland). `build_db()` dedupes by `slug` and writes `data/locations.json`
(1,253 unique locations after dedup — several `ALL_LOCATIONS` entries share a slug). This file is the
single source of truth for every location page that gets generated — adding a new location means
adding a tuple here and rerunning the full pipeline.

**`scripts/build_pages.py`** — the actual generator, driven by two config blocks at the top:
- `SERVICES`: list of `(slug, display_name, emoji)` tuples — the 8 services offered (house-removals,
  office-removals, man-and-van, storage, packing-services, same-day-removals,
  international-removals, piano-removals). Adding a service means adding a tuple here *and* a matching
  entry in `COST_TABLES`.
- `COST_TABLES`: dict keyed by service slug, list of `(label, price_range)` rows shown on every page
  for that service.

For every `(service, location)` pair it renders one self-contained HTML string (nav, mobile menu,
hero with booking form, stats bar, cost table, FAQ block generated per-location, footer, sticky mobile
CTA bar) and writes it to `dist/{service_slug}/{location_slug}/index.html`. All HTML fragments (`nav_html`,
`mobile_menu_html`, `footer_html`, `booking_form_html`, `faq_html`, `cost_table_html`,
`sidebar_services_html`) are plain f-string builders — there's no templating engine. Page-relative
asset paths are computed via a `root` string (`"../../"` for a two-level-deep location page, `"./"`
for a top-level page like `locations.html`) rather than absolute URLs, so the whole `dist/` tree is
directly droppable as static files.

Existing output files are skipped by default (`out_path.exists()` check) so re-running the script only
builds new location/service combinations — pass `--force` to regenerate everything (e.g. after editing
the HTML templates in this file).

`build_locations_page()` runs after all service pages and rebuilds `dist/locations.html`, grouping every
location by region using a hand-maintained `REGION_ORDER` list (regions not in the list are appended
alphabetically after).

**`scripts/inject_mobile_menu.py`** — a standalone patcher, independent of `build_pages.py`'s templates
(duplicates `SERVICES`, `mobile_menu_html`, and `MENU_JS` locally). Walks every `*.html` file under
`dist/` and, for any file that doesn't already contain `class="hamburger"`, inserts the hamburger
button, mobile menu overlay, and toggle JS via string replacement on known anchor points
(`</a>\n  <ul class="nav-links">`, `</nav>`, `</body>`). Use this after hand-editing static pages
(`index.html`, `about.html`, etc.) outside the generator, or after changing the mobile menu markup,
instead of a full `--force` rebuild.

**`scripts/build_static_pages.py`** — covers everything `build_pages.py` doesn't: the top-level pages
(`index.html`, `about.html`, `contact.html`, `privacy.html`, `thank-you.html`), the Knowledge Hub
(`blog/index.html` + two posts), `partner-with-us/index.html`, and — importantly — the 8 generic
`dist/{service_slug}/index.html` service landing pages that every nav bar and footer link to (these are
distinct from the per-location pages `build_pages.py` generates under the same directories). Imports
its shared fragments (`nav_html`, `footer_html`, `SERVICES`, `COST_TABLES`, etc.) directly from
`build_pages.py` rather than duplicating them, unlike `inject_mobile_menu.py`.

## Key config values

Both `build_pages.py` and `inject_mobile_menu.py` hardcode `PHONE`/`PHONE_HREF` and the `SERVICES` list
independently — keep them in sync when changing either. Other shared config (`FORMSPREE_ID`,
`SITE_NAME`, `SITE_URL`) lives only in `build_pages.py`.

Design tokens (colors) are defined once in `docs/assets/shared.css` (also mirrored as
`dist/assets/shared.css` in a built site) as CSS custom properties: `--navy`, `--navy-mid`,
`--navy-light`, `--orange`, `--orange-light`, `--text-muted`.

Favicon/icon files live in `docs/assets/` (`favicon.ico`, `favicon.svg`, `apple-touch-icon.png`,
`android-chrome-{192,512}x192.png`, `safari-pinned-tab.svg`, `site.webmanifest`) and are copied to
`dist/assets/` by the same command that copies `shared.css`. The `<link rel="icon">` etc. tags are
emitted by `favicon_html(root)` in `build_pages.py`, imported into `build_static_pages.py` — every
page template calls it, so a new page type just needs to include that fragment in its `<head>`.
