"""
inject_mobile_menu.py
---------------------
Patches the hamburger button, mobile menu overlay, and JS into every
HTML file in the dist/ folder that doesn't already have one.

Useful when you've edited shared.css or the menu markup and need to
push changes to all existing pages without a full rebuild.

Usage:
    python scripts/inject_mobile_menu.py
    python scripts/inject_mobile_menu.py --dist dist
"""

import os
import argparse
from pathlib import Path

PHONE_HREF = "tel:08001234567"
PHONE      = "0800 123 4567"

SERVICES = [
    ("house-removals",         "House Removals",         "🏠"),
    ("office-removals",        "Office Removals",        "🏢"),
    ("man-and-van",            "Man & Van",              "🚐"),
    ("storage",                "Storage",                "📦"),
    ("packing-services",       "Packing Services",       "📋"),
    ("same-day-removals",      "Same Day Removals",      "⚡"),
    ("international-removals", "International Removals", "✈️"),
    ("piano-removals",         "Piano Removals",         "🎹"),
]

HAMBURGER = (
    '<button class="hamburger" id="hamburger" '
    'aria-label="Open menu" aria-expanded="false">'
    "<span></span><span></span><span></span>"
    "</button>"
)

MENU_JS = """<script>
(function(){
  var btn  = document.getElementById('hamburger');
  var menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;
  btn.addEventListener('click', function() {
    var open = menu.classList.toggle('open');
    btn.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open);
    document.body.classList.toggle('menu-open', open);
  });
  menu.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', function() {
      menu.classList.remove('open');
      btn.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('menu-open');
    });
  });
})();
</script>"""


def mobile_menu_html(root):
    svc_links = "\n    ".join(
        f'<a href="{root}{slug}/index.html" class="mobile-nav-svc">'
        f'<span class="svc-icon">{icon}</span>{name}</a>'
        for slug, name, icon in SERVICES
    )
    return f"""<div class="mobile-menu" id="mobile-menu" role="dialog" aria-label="Navigation menu">
  <div class="mobile-menu-inner">
    <div class="mobile-menu-label">Navigation</div>
    <a href="{root}index.html" class="mobile-nav-link">Home <span class="arrow">›</span></a>
    <a href="{root}locations.html" class="mobile-nav-link">All Locations <span class="arrow">›</span></a>
    <a href="{root}blog/index.html" class="mobile-nav-link">Knowledge Hub <span class="arrow">›</span></a>
    <a href="{root}partner-with-us/index.html" class="mobile-nav-link">For Businesses <span class="arrow">›</span></a>
    <div class="mobile-menu-label">Our Services</div>
    {svc_links}
    <a href="{root}index.html#quote" class="mobile-menu-cta">📦 Book My Removal Now</a>
    <a href="{PHONE_HREF}" class="mobile-menu-tel">📞 {PHONE}</a>
  </div>
</div>"""


def get_root(filepath: Path, dist_dir: Path) -> str:
    """Return the relative path back to site root (e.g. '../../')."""
    rel = filepath.relative_to(dist_dir)
    depth = len(rel.parts) - 1          # parts includes filename
    return "./" if depth == 0 else "../" * depth


def patch_file(filepath: Path, dist_dir: Path) -> str:
    """
    Inject hamburger button, mobile menu, and JS into a single HTML file.
    Returns 'built' | 'skipped' | 'no_match'
    """
    content = filepath.read_text(encoding="utf-8")

    if 'class="hamburger"' in content:
        return "skipped"

    root = get_root(filepath, dist_dir)
    menu_html = mobile_menu_html(root)

    modified = content

    # 1. Insert hamburger button after closing logo </a>, before <ul class="nav-links">
    for pattern, replacement in [
        ('</a>\n  <ul class="nav-links">',  f'</a>\n  {HAMBURGER}\n  <ul class="nav-links">'),
        ('</a><ul class="nav-links">',       f'</a>{HAMBURGER}<ul class="nav-links">'),
    ]:
        if pattern in modified:
            modified = modified.replace(pattern, replacement, 1)
            break

    # 2. Insert mobile menu right after </nav>
    if '</nav>' in modified:
        modified = modified.replace('</nav>', f'</nav>\n{menu_html}', 1)

    # 3. Insert JS before </body>
    if '</body>' in modified:
        modified = modified.replace('</body>', f'{MENU_JS}\n</body>', 1)

    if modified == content:
        return "no_match"

    filepath.write_text(modified, encoding="utf-8")
    return "built"


def main():
    parser = argparse.ArgumentParser(description="Inject mobile menu into all HTML files")
    parser.add_argument("--dist", default="dist", help="Site directory (default: dist)")
    args = parser.parse_args()

    dist = Path(args.dist)
    if not dist.exists():
        print(f"❌  Directory '{dist}' not found.")
        return

    counts = {"built": 0, "skipped": 0, "no_match": 0}

    for html_file in sorted(dist.rglob("*.html")):
        result = patch_file(html_file, dist)
        counts[result] += 1

    print(f"✅  Patched:        {counts['built']} files")
    print(f"   Already done:   {counts['skipped']} files")
    print(f"   No nav found:   {counts['no_match']} files")


if __name__ == "__main__":
    main()
