"""
build_pages.py
--------------
Generates all location × service HTML pages for RemovalsNation.

Usage:
    python scripts/build_pages.py                  # build everything
    python scripts/build_pages.py --force          # rebuild even existing pages
    python scripts/build_pages.py --service house-removals  # one service only

Output goes to dist/  (mirrors the deployable site structure).
"""

import json
import os
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

FORMSPREE_ID   = "xkododjy"
PHONE          = "0800 123 4567"
PHONE_HREF     = "tel:08001234567"
SITE_NAME      = "RemovalsNation"
SITE_URL       = "https://removalsnation.com"

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

# ── Shared HTML fragments ─────────────────────────────────────────────────────

def nav_html(root):
    return f"""<nav>
  <a href="{root}index.html" class="logo">Removals<span>Nation</span></a>
  <button class="hamburger" id="hamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <ul class="nav-links">
    <li><a href="{root}house-removals/index.html">House Removals</a></li>
    <li><a href="{root}locations.html">Locations</a></li>
    <li><a href="{root}blog/index.html">Knowledge Hub</a></li>
    <li><a href="{root}partner-with-us/index.html">For Businesses</a></li>
  </ul>
  <a href="{root}index.html#quote" class="nav-cta">Book Now</a>
</nav>"""


def mobile_menu_html(root):
    services_html = "\n    ".join(
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
    {services_html}
    <a href="{root}index.html#quote" class="mobile-menu-cta">📦 Book My Removal Now</a>
    <a href="{PHONE_HREF}" class="mobile-menu-tel">📞 {PHONE}</a>
  </div>
</div>"""


def footer_html(root):
    return f"""<footer>
  <div class="footer-grid">
    <div class="footer-brand">
      <a href="{root}index.html" class="logo">Removals<span>Nation</span></a>
      <p>Professional, fully insured removal services across the UK. Your trusted nationwide removal company.</p>
    </div>
    <div class="footer-col">
      <h4>Services</h4>
      <a href="{root}house-removals/index.html">House Removals</a>
      <a href="{root}office-removals/index.html">Office Removals</a>
      <a href="{root}man-and-van/index.html">Man &amp; Van</a>
      <a href="{root}storage/index.html">Storage</a>
      <a href="{root}packing-services/index.html">Packing</a>
      <a href="{root}international-removals/index.html">International</a>
    </div>
    <div class="footer-col">
      <h4>Company</h4>
      <a href="{root}about.html">About Us</a>
      <a href="{root}partner-with-us/index.html">For Businesses</a>
      <a href="{root}blog/index.html">Knowledge Hub</a>
      <a href="{root}contact.html">Contact</a>
    </div>
    <div class="footer-col">
      <h4>Legal</h4>
      <a href="{root}privacy.html">Privacy Policy</a>
      <a href="{root}contact.html">Get in Touch</a>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© 2025 {SITE_NAME}. All rights reserved.</span>
    <span>Fully insured · Nationwide coverage</span>
  </div>
</footer>"""


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

LOCATION_PAGE_CSS = """<style>
.loc-hero{padding:120px 48px 70px}
.loc-inner{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:start;max-width:1200px;margin:0 auto}
.breadcrumb{font-size:.8rem;color:var(--text-muted);margin-bottom:20px}
.breadcrumb a{color:var(--text-muted);text-decoration:none}.breadcrumb a:hover{color:#fff}
.hero-badge{display:inline-block;background:rgba(244,88,10,.12);border:1px solid rgba(244,88,10,.3);
  border-radius:100px;padding:5px 14px;font-size:.78rem;font-weight:700;
  color:var(--orange-light);text-transform:uppercase;letter-spacing:.06em;margin-bottom:20px}
.loc-hero h1{font-family:'Syne',sans-serif;font-size:clamp(2rem,4vw,3.2rem);
  font-weight:800;letter-spacing:-.03em;line-height:1.08;margin-bottom:20px}
.loc-hero p{font-size:1rem;color:var(--text-muted);line-height:1.7;margin-bottom:24px}
.trust-pills{display:flex;gap:10px;flex-wrap:wrap}
.trust-pills span{background:rgba(255,255,255,.05);border:1px solid var(--border);
  border-radius:100px;padding:6px 14px;font-size:.78rem;color:var(--text-muted)}
.quote-card{background:var(--navy-mid);border:1px solid var(--border);border-radius:20px;padding:32px}
.quote-card h2{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:4px}
.form-sub{font-size:.82rem;color:var(--text-muted);margin-bottom:24px}
.qrow{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.loc-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
  background:var(--border);border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
.stat-i{background:var(--navy);padding:28px;text-align:center}
.stat-n{font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:var(--orange)}
.stat-l{font-size:.78rem;color:var(--text-muted);margin-top:6px}
.loc-content{display:grid;grid-template-columns:1fr 300px;gap:48px;
  padding:70px 48px;max-width:1200px;margin:0 auto}
.content-main h2{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;margin:32px 0 14px}
.content-main h2:first-child{margin-top:0}
.content-main p{font-size:.93rem;line-height:1.8;color:rgba(255,255,255,.8);margin-bottom:14px}
.cost-table{background:var(--navy-mid);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.cost-row{display:flex;justify-content:space-between;padding:13px 18px;
  border-bottom:1px solid var(--border);font-size:.88rem}
.cost-row:last-child{border-bottom:none}
.cost-row span:last-child{font-weight:700;color:var(--orange)}
.faqs{margin-top:8px}
.faq{border-bottom:1px solid var(--border);padding:18px 0}
.faq:last-child{border-bottom:none}
.faq-q{font-family:'Syne',sans-serif;font-weight:700;font-size:.93rem;margin-bottom:8px}
.faq-a{font-size:.86rem;color:var(--text-muted);line-height:1.7}
.sidebar-card{background:var(--navy-mid);border:1px solid var(--border);border-radius:14px;padding:22px}
.sidebar-card h3{font-family:'Syne',sans-serif;font-size:.95rem;font-weight:700;margin-bottom:14px}
.sidebar-link{display:flex;align-items:center;gap:10px;text-decoration:none;
  color:rgba(255,255,255,.7);font-size:.85rem;padding:9px 0;
  border-bottom:1px solid var(--border);transition:color .2s}
.sidebar-link:last-child{border-bottom:none}
.sidebar-link:hover{color:#fff}
@media(max-width:900px){
  .loc-hero{padding:90px 24px 40px}
  .loc-inner{grid-template-columns:1fr}
  .loc-stats{grid-template-columns:repeat(2,1fr)}
  .loc-content{grid-template-columns:1fr;padding:40px 24px}
}
</style>"""


# ── Cost tables per service ────────────────────────────────────────────────────

COST_TABLES = {
    "house-removals": [
        ("Studio / 1 Bedroom", "£300 – £600"),
        ("2 Bedroom Property", "£500 – £900"),
        ("3 Bedroom Property", "£700 – £1,200"),
        ("4+ Bedroom Property", "£1,000 – £2,000+"),
        ("Long Distance (200+ miles)", "Add £200 – £500"),
    ],
    "office-removals": [
        ("Small Office (1–5 desks)", "£400 – £900"),
        ("Medium Office (5–20 desks)", "£800 – £2,000"),
        ("Large Office (20+ desks)", "£2,000 – £5,000+"),
        ("IT Equipment Move", "Add £200 – £500"),
    ],
    "man-and-van": [
        ("1 Man + Small Van (2hr)", "£60 – £120"),
        ("1 Man + Large Van (2hr)", "£80 – £150"),
        ("2 Men + Van (half day)", "£150 – £280"),
        ("2 Men + Van (full day)", "£250 – £450"),
    ],
    "storage": [
        ("Small Unit (25 sq ft)", "£30 – £60/mo"),
        ("Medium Unit (50 sq ft)", "£60 – £100/mo"),
        ("Large Unit (100 sq ft)", "£100 – £160/mo"),
        ("Container Storage", "£80 – £150/mo"),
    ],
    "packing-services": [
        ("Studio / 1 Bed", "£150 – £300"),
        ("2 Bedroom", "£250 – £450"),
        ("3 Bedroom", "£350 – £600"),
        ("4+ Bedroom", "£500 – £900"),
    ],
    "same-day-removals": [
        ("Single Item", "£80 – £180"),
        ("Small Load", "£150 – £280"),
        ("Half House Load", "£280 – £500"),
        ("Full House Load", "£500 – £900"),
    ],
    "international-removals": [
        ("Europe (1–2 bed)", "£1,500 – £3,500"),
        ("Europe (3–4 bed)", "£3,000 – £6,000"),
        ("USA / Canada", "£4,000 – £9,000"),
        ("Australia / NZ", "£5,000 – £12,000"),
    ],
    "piano-removals": [
        ("Upright Piano", "£150 – £350"),
        ("Grand Piano", "£300 – £700"),
        ("Upstairs / Stairs", "Add £100 – £200"),
        ("Long Distance", "Add £200 – £500"),
    ],
}


# ── Page builder ──────────────────────────────────────────────────────────────

def cost_table_html(svc_slug):
    rows = COST_TABLES.get(svc_slug, COST_TABLES["house-removals"])
    return (
        '<div class="cost-table">'
        + "".join(
            f'<div class="cost-row"><span>{r}</span><span>{p}</span></div>'
            for r, p in rows
        )
        + "</div>"
    )


def faq_html(svc_name, loc_name, region):
    faqs = [
        (
            f"How quickly can you arrange {svc_name.lower()} in {loc_name}?",
            f"We can typically confirm a booking in {loc_name} within a few hours. "
            f"For urgent same-day moves, call us directly on {PHONE}.",
        ),
        (
            f"Are your removal teams in {loc_name} fully insured?",
            f"Yes — all RemovalsNation teams operating in {loc_name} carry full "
            f"public liability and goods-in-transit insurance.",
        ),
        (
            f"Do you cover all areas of {loc_name}?",
            f"We cover {loc_name} and all surrounding areas in {region}. "
            f"If you're unsure, just ask when booking.",
        ),
        (
            f"What's included in your {svc_name.lower()} service in {loc_name}?",
            f"Our standard service includes loading, transport and unloading. "
            f"Packing, storage and dismantling can all be added.",
        ),
    ]
    return '<div class="faqs">' + "".join(
        f'<div class="faq">'
        f'<div class="faq-q">{q}</div>'
        f'<div class="faq-a">{a}</div>'
        f"</div>"
        for q, a in faqs
    ) + "</div>"


def sidebar_services_html(root):
    links = "".join(
        f'<a href="{root}{slug}/index.html" class="sidebar-link">'
        f"<span>{icon}</span>{name}</a>"
        for slug, name, icon in SERVICES
    )
    return f'<div class="sidebar-card" style="margin-bottom:20px"><h3>Our Services</h3>{links}</div>'


def booking_form_html(svc_name, loc_name, postcode):
    return f"""<div class="quote-card">
  <h2>Book Now — {loc_name}</h2>
  <p class="form-sub">60 seconds · Confirmed price instantly</p>
  <form action="https://formspree.io/f/{FORMSPREE_ID}" method="POST">
    <div class="qrow">
      <div class="form-group">
        <label>Move Type</label>
        <select name="move_type">
          <option>{svc_name}</option>
          <option>House Removals</option><option>Office Removals</option>
          <option>Man &amp; Van</option><option>Storage</option><option>International</option>
        </select>
      </div>
      <div class="form-group">
        <label>Property Size</label>
        <select name="property_size">
          <option>Studio/1 Bed</option><option>2 Bedroom</option>
          <option>3 Bedroom</option><option>4+ Bedroom</option><option>Commercial</option>
        </select>
      </div>
    </div>
    <div class="qrow">
      <div class="form-group">
        <label>From Postcode</label>
        <input type="text" name="from_postcode" placeholder="{postcode} 1AA" style="font-size:16px">
      </div>
      <div class="form-group">
        <label>To Postcode</label>
        <input type="text" name="to_postcode" placeholder="Destination" style="font-size:16px">
      </div>
    </div>
    <div class="qrow">
      <div class="form-group">
        <label>Moving Date</label>
        <input type="date" name="moving_date" style="font-size:16px">
      </div>
      <div class="form-group">
        <label>Phone / Email</label>
        <input type="text" name="contact" placeholder="Phone or email" required style="font-size:16px">
      </div>
    </div>
    <input type="hidden" name="_subject" value="New Removal Booking — {SITE_NAME}">
    <input type="hidden" name="location" value="{loc_name}">
    <input type="hidden" name="service" value="{svc_name}">
    <button type="submit" class="btn-primary" style="width:100%;margin-top:6px;text-align:center">
      Book My Removal →
    </button>
  </form>
  <p style="text-align:center;font-size:.72rem;color:var(--text-muted);margin-top:10px">
    🔒 Fully insured · No hidden fees · Nationwide coverage
  </p>
</div>"""


def build_location_page(svc_slug, svc_name, svc_icon, loc, dist_dir):
    """Build one /{svc_slug}/{slug}/index.html"""
    name, region, county, postcode, slug = loc
    root = "../../"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Professional {svc_name.lower()} in {name}, {county}. Fully insured, instant booking. {SITE_NAME} — your trusted removal company.">
<title>{svc_name} in {name} | {SITE_NAME}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/shared.css">
{LOCATION_PAGE_CSS}
</head>
<body>
{nav_html(root)}
{mobile_menu_html(root)}
<main>
<section class="loc-hero">
  <div class="loc-inner">
    <div>
      <div class="breadcrumb">
        <a href="{root}index.html">Home</a> ›
        <a href="{root}{svc_slug}/index.html">{svc_name}</a> › {name}
      </div>
      <div class="hero-badge">{svc_icon} {region}</div>
      <h1>{svc_name} in {name}</h1>
      <p>Looking for reliable {svc_name.lower()} in {name}? {SITE_NAME} provides professional,
         fully insured removal services across {name} and {county}.
         Book online today for an instant confirmed price.</p>
      <div class="trust-pills">
        <span>✓ Our professional team</span>
        <span>✓ Fully insured</span>
        <span>✓ Instant booking</span>
        <span>✓ Instant pricing</span>
      </div>
    </div>
    {booking_form_html(svc_name, name, postcode)}
  </div>
</section>
<div class="loc-stats">
  <div class="stat-i"><div class="stat-n">4.8★</div><div class="stat-l">Average rating</div></div>
  <div class="stat-i"><div class="stat-n">{county}</div><div class="stat-l">Area served</div></div>
  <div class="stat-i"><div class="stat-n">Same Day</div><div class="stat-l">Available in {name}</div></div>
  <div class="stat-i"><div class="stat-n">Insured</div><div class="stat-l">All our teams</div></div>
</div>
<div class="loc-content">
  <div class="content-main">
    <h2>Why Choose {SITE_NAME} for {svc_name} in {name}?</h2>
    <p>{SITE_NAME} is a professional nationwide removal company serving {name} and all of {county}.
       Our experienced, fully insured teams handle every aspect of your move with care and efficiency.</p>
    <p>Whether you're moving locally within {name} or relocating further afield, our {svc_name.lower()}
       teams are ready to help. We cover all postcodes in the {postcode} area.</p>
    <h2>{svc_name} Costs in {name}</h2>
    {cost_table_html(svc_slug)}
    <h2>Frequently Asked Questions</h2>
    {faq_html(svc_name, name, region)}
  </div>
  <aside class="content-sidebar">
    {sidebar_services_html(root)}
    <div class="sidebar-card">
      <h3>📞 Need Help?</h3>
      <p style="font-size:.85rem;color:var(--text-muted);margin-bottom:14px">
        Our team is available 7 days a week to help plan your move in {name}.
      </p>
      <a href="{PHONE_HREF}" class="btn-primary" style="width:100%;text-align:center;display:block">
        Call {PHONE}
      </a>
    </div>
  </aside>
</div>
</main>
{footer_html(root)}
<div class="sticky-mobile">
  <a href="{root}index.html#quote">Book Now</a>
  <a href="{PHONE_HREF}">📞 Call Now</a>
</div>
{MENU_JS}
</body>
</html>"""

    out_dir = Path(dist_dir) / svc_slug / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")


# ── Locations page ────────────────────────────────────────────────────────────

def build_locations_page(locations, dist_dir):
    """Rebuild /locations.html grouped by region."""
    from collections import defaultdict

    regions = defaultdict(list)
    for loc in locations:
        name, region, county, postcode, slug = loc
        regions[region].append((name, slug))

    REGION_ORDER = [
        "Central London", "North London", "North West London", "North East London",
        "East London", "South East London", "South London", "South West London", "West London",
        "Surrey", "Hertfordshire", "Essex", "Kent", "East Sussex", "West Sussex",
        "Berkshire", "Oxfordshire", "Buckinghamshire", "Cambridgeshire", "Bedfordshire",
        "Northamptonshire", "Hampshire", "Dorset", "Wiltshire", "Somerset",
        "Gloucestershire", "Devon", "Cornwall",
        "West Midlands", "Staffordshire", "Warwickshire", "Shropshire",
        "Worcestershire", "Herefordshire",
        "East Midlands", "Leicestershire", "Nottinghamshire", "Derbyshire", "Lincolnshire",
        "Greater Manchester", "Merseyside", "Cheshire", "Lancashire",
        "West Yorkshire", "South Yorkshire", "East Yorkshire", "North Yorkshire", "Teesside",
        "County Durham", "Tyne and Wear", "Northumberland", "Cumbria",
        "Norfolk", "Suffolk",
        "Scotland", "Wales", "Northern Ireland",
        "Isle of Wight", "Rutland",
    ]

    ordered = []
    seen = set()
    for r in REGION_ORDER:
        if r in regions and r not in seen:
            ordered.append((r, sorted(regions[r])))
            seen.add(r)
    for r in sorted(regions):
        if r not in seen:
            ordered.append((r, sorted(regions[r])))

    sections = ""
    for region, locs in ordered:
        links = "".join(
            f'<a href="./house-removals/{slug}/index.html" class="loc-link">{name}</a>'
            for name, slug in locs
        )
        sections += f"""
<div class="region-section">
  <h2 class="region-title">{region}</h2>
  <div class="loc-grid">{links}</div>
</div>"""

    root = "./"
    total = len(locations)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{SITE_NAME} covers {total}+ locations across the UK. Find professional removal services in your area.">
<title>All UK Locations | {SITE_NAME}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/shared.css">
<style>
.locs-hero{{padding:120px 48px 60px;max-width:900px;margin:0 auto;text-align:center}}
.locs-hero h1{{font-family:'Syne',sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.03em;margin-bottom:16px}}
.locs-hero p{{color:var(--text-muted);font-size:1rem;line-height:1.7}}
.locs-count{{display:inline-block;background:rgba(244,88,10,.12);border:1px solid rgba(244,88,10,.3);border-radius:100px;padding:6px 18px;font-size:.82rem;font-weight:700;color:var(--orange-light);margin-bottom:24px}}
.locs-wrap{{max-width:1300px;margin:0 auto;padding:0 48px 80px}}
.region-section{{margin-bottom:48px}}
.region-title{{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:var(--orange);margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border)}}
.loc-grid{{display:flex;flex-wrap:wrap;gap:8px}}
.loc-link{{background:var(--navy-mid);border:1px solid var(--border);border-radius:8px;padding:7px 14px;text-decoration:none;color:rgba(255,255,255,.8);font-size:.83rem;transition:all .2s}}
.loc-link:hover{{border-color:var(--orange);color:#fff;background:rgba(244,88,10,.08)}}
@media(max-width:900px){{.locs-hero{{padding:90px 24px 40px}}.locs-wrap{{padding:0 20px 60px}}}}
</style>
</head>
<body>
{nav_html(root)}
{mobile_menu_html(root)}
<main>
<div class="locs-hero">
  <div class="locs-count">📍 {total} Locations Covered</div>
  <h1>Removal Services Across the UK</h1>
  <p>{SITE_NAME} provides professional, fully insured removal services in {total}+ towns and cities
     across England, Scotland, Wales and Northern Ireland. Find your location below.</p>
</div>
<div class="locs-wrap">
{sections}
</div>
</main>
{footer_html(root)}
<div class="sticky-mobile">
  <a href="{root}index.html#quote">Book Now</a>
  <a href="{PHONE_HREF}">📞 Call Now</a>
</div>
{MENU_JS}
</body>
</html>"""

    (Path(dist_dir) / "locations.html").write_text(page, encoding="utf-8")
    print(f"✅  locations.html rebuilt ({total} locations)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build RemovalsNation location pages")
    parser.add_argument("--force", action="store_true", help="Rebuild existing pages")
    parser.add_argument("--service", help="Build only one service slug")
    parser.add_argument("--dist", default="dist", help="Output directory (default: dist)")
    parser.add_argument("--data", default="data/locations.json", help="Path to locations JSON")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"⚠  {args.data} not found — run: python scripts/locations_db.py")
        return

    with open(args.data) as f:
        locations = json.load(f)

    services_to_build = (
        [s for s in SERVICES if s[0] == args.service]
        if args.service
        else SERVICES
    )

    if not services_to_build:
        print(f"Unknown service '{args.service}'. Valid: {[s[0] for s in SERVICES]}")
        return

    total_built = 0
    total_skipped = 0

    for svc_slug, svc_name, svc_icon in services_to_build:
        svc_dir = Path(args.dist) / svc_slug
        print(f"\n📦 {svc_name}...")

        for loc in locations:
            slug = loc[4]
            out_path = svc_dir / slug / "index.html"
            if out_path.exists() and not args.force:
                total_skipped += 1
                continue
            build_location_page(svc_slug, svc_name, svc_icon, loc, args.dist)
            total_built += 1

        count = len(list(svc_dir.iterdir())) if svc_dir.exists() else 0
        print(f"   → {count} location pages")

    build_locations_page(locations, args.dist)
    print(f"\n✅  Done — built {total_built} pages, skipped {total_skipped} existing")
    print(f"   Total site pages in {args.dist}/: {sum(1 for _ in Path(args.dist).rglob('*.html'))}")


if __name__ == "__main__":
    main()
