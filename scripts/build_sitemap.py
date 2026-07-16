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

from build_pages import SERVICES, SITE_URL


def static_paths():
    paths = ["", "about.html", "contact.html", "privacy.html", "locations.html",
             "blog/", "blog/how-much-do-removals-cost/", "blog/moving-house-checklist/",
             "partner-with-us/"]
    paths += [f"{slug}/" for slug, _, _ in SERVICES]
    return paths


def build_sitemap(locations, dist_dir):
    today = date.today().isoformat()
    urls = []
    for path in static_paths():
        priority = "1.0" if path == "" else "0.7"
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
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /thank-you.html\n\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )
    (Path(dist_dir) / "robots.txt").write_text(robots, encoding="utf-8")
    print("✅  robots.txt written")


def main():
    parser = argparse.ArgumentParser(description="Build sitemap.xml and robots.txt")
    parser.add_argument("--dist", default="dist", help="Output directory (default: dist)")
    parser.add_argument("--data", default="data/locations.json", help="Path to locations JSON")
    args = parser.parse_args()

    with open(args.data) as f:
        locations = json.load(f)

    build_sitemap(locations, args.dist)
    build_robots(args.dist)


if __name__ == "__main__":
    main()
