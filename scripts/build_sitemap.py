"""
build_sitemap.py
-----------------
Generates dist/sitemap.xml (every URL on the site) and dist/robots.txt.

Usage:
    python scripts/build_sitemap.py
    python scripts/build_sitemap.py --dist output
"""

import argparse
import json
from datetime import date
from pathlib import Path

from build_pages import SERVICES, SITE_URL, SITE_NAME, PHONE, PHONE_HREF, COST_TABLES_BASE
from build_static_pages import BLOG_POSTS


def static_paths():
    paths = ["", "about.html", "contact.html", "privacy.html", "terms.html", "locations.html",
             "removals-within-the-m25/",
             "blog/",
             "partner-with-us/"]
    paths += [f"blog/{slug}/" for slug, _, _, _ in BLOG_POSTS]
    paths += [f"{slug}/" for slug, _, _ in SERVICES]
    return paths


def build_sitemap(locations, dist_dir):
    today = date.today().isoformat()
    urls = []
    for path in static_paths():
        if path == "":
            priority = "1.0"
        elif path == "removals-within-the-m25/":
            priority = "0.9"
        else:
            priority = "0.7"
        urls.append((f"{SITE_URL}/{path}", priority))
    for loc in locations:
        slug = loc[4]
        for svc_slug, _, _ in SERVICES:
            urls.append((f"{SITE_URL}/{svc_slug}/{slug}/", "0.6"))

    body = "\n".join(
        f"  <url><loc>{url}</loc><lastmod>{today}</lastmod><priority>{priority}</priority></url>"
        for url, priority in urls
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )
    (Path(dist_dir) / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"✅  sitemap.xml written ({len(urls)} URLs)")


def build_robots(dist_dir):
    # The blanket "User-agent: *" block already allows every crawler, AI bots
    # included — these explicit entries don't change behavior, they document
    # intent and guard against someone later adding a narrower "*" rule that
    # would accidentally block citation-relevant AI crawlers (GPTBot/
    # ChatGPT-User for ChatGPT, PerplexityBot, ClaudeBot/anthropic-ai for
    # Claude, Google-Extended for Gemini/AI Overviews, Bingbot for Copilot).
    ai_bots = [
        "GPTBot", "ChatGPT-User", "OAI-SearchBot",
        "PerplexityBot", "Perplexity-User",
        "ClaudeBot", "anthropic-ai", "Claude-Web",
        "Google-Extended", "Bingbot",
    ]
    ai_bot_rules = "\n".join(f"User-agent: {bot}\nAllow: /\n" for bot in ai_bots)
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /thank-you.html\n\n"
        f"{ai_bot_rules}\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )
    (Path(dist_dir) / "robots.txt").write_text(robots, encoding="utf-8")
    print("✅  robots.txt written")


def build_llms_txt(dist_dir, total_locations):
    today = date.today().isoformat()
    llms = f"""# {SITE_NAME}

> {SITE_NAME} is a UK removals company offering house removals, office removals,
> man and van hire, storage, packing services, same-day removals, international
> removals, and piano removals, with fully insured teams covering {total_locations}+
> towns and cities across England, Scotland, Wales and Northern Ireland. Every
> job is fully insured (public liability and goods-in-transit) with no hidden
> fees; quotes are confirmed online in about 60 seconds or by phone on {PHONE}.

Last updated: {today}

## Services
- [House Removals]({SITE_URL}/house-removals/index.html) — full house moves, priced by property size
- [Office Removals]({SITE_URL}/office-removals/index.html) — business relocations, IT equipment moves
- [Man & Van]({SITE_URL}/man-and-van/index.html) — hourly-rate hire for smaller loads, same-day available
- [Storage]({SITE_URL}/storage/index.html) — short- or long-term unit storage, flexible billing
- [Packing Services]({SITE_URL}/packing-services/index.html) — full or partial professional packing
- [Same Day Removals]({SITE_URL}/same-day-removals/index.html) — urgent/short-notice removals
- [International Removals]({SITE_URL}/international-removals/index.html) — moving abroad, sea and air freight
- [Piano Removals]({SITE_URL}/piano-removals/index.html) — specialist upright and grand piano moving

## Pricing
- [Pricing overview (machine-readable)]({SITE_URL}/pricing.md) — nationwide base price ranges per service
- Exact prices vary by property size, distance and UK region — get an instant quote on any service page

## Coverage
- [All UK Locations]({SITE_URL}/locations.html) — {total_locations}+ towns and cities, England/Scotland/Wales/Northern Ireland
- [Removals Within the M25]({SITE_URL}/removals-within-the-m25/index.html) — London, Surrey, Hertfordshire, Essex, Kent

## Company
- [About]({SITE_URL}/about.html)
- [Contact]({SITE_URL}/contact.html) — phone: {PHONE}
- [Knowledge Hub (blog)]({SITE_URL}/blog/index.html) — moving cost guides, checklists, how-to articles
- [Partner With Us]({SITE_URL}/partner-with-us/index.html) — referral and corporate partnerships for agents

## Sitemap
- [XML sitemap]({SITE_URL}/sitemap.xml)
"""
    (Path(dist_dir) / "llms.txt").write_text(llms, encoding="utf-8")
    print("✅  llms.txt written")


def build_pricing_md(dist_dir):
    """Machine-readable pricing overview at the site root for AI agents/answer
    engines evaluating cost — sourced directly from COST_TABLES_BASE, the
    same data that generates every on-page cost table, so this can never
    drift out of sync with what's actually shown to users."""
    today = date.today().isoformat()
    service_names = {slug: name for slug, name, _ in SERVICES}
    lines = [
        f"# {SITE_NAME} — UK Removals Pricing",
        "",
        f"Last updated: {today}",
        "",
        "Nationwide base price ranges (GBP). Exact prices depend on property "
        "size, distance and UK region — London and the South East run "
        "roughly 10-35% above these base figures; the North, Scotland, "
        "Wales and Northern Ireland typically run at or below them. Get an "
        f"exact, instant quote at {SITE_URL}/ or call {PHONE}.",
        "",
    ]
    for slug, rows in COST_TABLES_BASE.items():
        name = service_names.get(slug, slug)
        lines.append(f"## {name}")
        for row in rows:
            if len(row) == 2:
                label, price = row
                lines.append(f"- {label}: {price}")
            else:
                label, lo, hi, suffix = row
                if suffix == "add":
                    lines.append(f"- {label}: add £{lo}–£{hi}")
                else:
                    lines.append(f"- {label}: £{lo}–£{hi}{suffix}")
        lines.append(f"- Details: {SITE_URL}/{slug}/index.html")
        lines.append("")
    lines.append("## Notes")
    lines.append("- All prices include full insurance (public liability and goods-in-transit) at no extra cost.")
    lines.append("- No hidden fees — the confirmed price is the price.")
    lines.append(f"- Full location-by-location pricing: {SITE_URL}/locations.html")
    text = "\n".join(lines) + "\n"
    (Path(dist_dir) / "pricing.md").write_text(text, encoding="utf-8")
    print("✅  pricing.md written")


def main():
    parser = argparse.ArgumentParser(description="Build sitemap.xml and robots.txt")
    parser.add_argument("--dist", default="dist", help="Output directory (default: dist)")
    parser.add_argument("--data", default="data/locations.json", help="Path to locations JSON")
    args = parser.parse_args()

    with open(args.data) as f:
        locations = json.load(f)

    build_sitemap(locations, args.dist)
    build_robots(args.dist)
    build_llms_txt(args.dist, len(locations))
    build_pricing_md(args.dist)


if __name__ == "__main__":
    main()
