# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo layout note

The actual site source lives zipped up at `removalsnation-repo.zip` (the working tree only otherwise
contains this file and `.git`). Unzip it before working:

```bash
unzip -o removalsnation-repo.zip -d /tmp/rn && cd /tmp/rn/removalsnation-repo
```

Do your work inside the extracted copy, then re-zip and replace `removalsnation-repo.zip` at the repo
root before committing (or ask the user how they want the extracted layout committed, since the
current repo intentionally keeps the source zipped rather than checked out flat).

## What this project is

RemovalsNation — a pure static HTML/CSS site (no framework, no build tool, no `node_modules`) for a UK
removals company. It's a **Python static site generator**: two scripts read a Python-literal locations
database and stamp out ~13,600 location × service landing pages as plain HTML into `dist/`, which is
then drag-and-drop deployed to Netlify. `dist/` is gitignored — it's a build artifact, not source.

- Hosting: Netlify (drag-and-drop deploy of `dist/`)
- Forms: Formspree (form ID `xaqzerzk`), POSTs from every booking form, redirects to `/thank-you.html`
- Fonts: Syne (headings) + DM Sans (body), loaded from Google Fonts
- Domain: `removalsnation.com` (GoDaddy DNS → Netlify)

## Commands

```bash
# 1. Regenerate data/locations.json from the ALL_LOCATIONS list in locations_db.py
python scripts/locations_db.py

# 2. Generate all location x service pages into dist/ (skips pages that already exist)
python scripts/build_pages.py
python scripts/build_pages.py --force                # rebuild even existing pages
python scripts/build_pages.py --service man-and-van   # build one service only
python scripts/build_pages.py --dist output           # custom output dir
python scripts/build_pages.py --data path/to.json     # custom locations file

# 3. Patch hamburger menu / mobile nav into any HTML files missing it (idempotent, skips files
#    that already have `class="hamburger"`)
python scripts/inject_mobile_menu.py
python scripts/inject_mobile_menu.py --dist dist
```

There is no test suite, linter, or build step beyond these scripts — "correctness" here means the
generated HTML in `dist/` is well-formed and the scripts run to completion. Verify changes by running
the relevant script and spot-checking output files (e.g. `dist/house-removals/camden/index.html`).

## Architecture

**`scripts/locations_db.py`** — a single large `ALL_LOCATIONS` list of tuples:
`(display_name, region, county, postcode_prefix, url_slug)`, covering ~1,700+ UK towns/boroughs/
neighbourhoods (Greater London boroughs and neighbourhoods, then counties/regions across England,
Scotland, Wales, Northern Ireland). `build_db()` dedupes by `slug` and writes `data/locations.json`.
This file is the single source of truth for every location page that gets generated — adding a new
location means adding a tuple here and rerunning both scripts.

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

## Key config values

Both `build_pages.py` and `inject_mobile_menu.py` hardcode `PHONE`/`PHONE_HREF` and the `SERVICES` list
independently — keep them in sync when changing either. Other shared config (`FORMSPREE_ID`,
`SITE_NAME`, `SITE_URL`) lives only in `build_pages.py`.

Design tokens (colors) are defined once in `docs/assets/shared.css` (also mirrored as
`dist/assets/shared.css` in a built site) as CSS custom properties: `--navy`, `--navy-mid`,
`--navy-light`, `--orange`, `--orange-light`, `--text-muted`.
