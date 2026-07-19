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
import re
import argparse
import datetime
from pathlib import Path
from urllib.parse import quote as urlquote

# ── Config ────────────────────────────────────────────────────────────────────

FORMSPREE_ID   = "xkododjy"
PHONE          = "+44 7417 355780"
PHONE_HREF     = "tel:+447417355780"
SITE_NAME      = "RemovalsNation"
SITE_URL       = "https://removalsnation.com"
LEGAL_ENTITY   = "The LeadGenCo LTD"
COMPANY_NUMBER = "17274904"
WHATSAPP_NUMBER = "447417355780"  # digits only, no +, no leading 0 (UK mobile in international format)

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

def favicon_html(root):
    return f"""<link rel="icon" href="{root}assets/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="{root}assets/favicon.svg">
<link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png">
<link rel="mask-icon" href="{root}assets/safari-pinned-tab.svg" color="#f4580a">
<link rel="manifest" href="{root}assets/site.webmanifest">
<meta name="theme-color" content="#0b1628">"""


def gtag_html():
    """Google Ads / Google tag (gtag.js) — loaded on every page. Uses an
    absolute src so it's root-independent regardless of page depth."""
    return """<script async src="https://www.googletagmanager.com/gtag/js?id=AW-18109980077"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'AW-18109980077');
</script>"""


def seo_html(canonical_path, title, description, root, noindex=False):
    """Canonical link + Open Graph / Twitter Card tags, shared by every page.
    canonical_path is site-relative with no leading slash ("" for home,
    "about.html" for a standalone page, "house-removals/camden/" for a
    directory-style page)."""
    canonical = f"{SITE_URL}/{canonical_path}"
    og_image = f"{SITE_URL}/assets/og-image.png"
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ""
    return f"""<link rel="canonical" href="{canonical}">
{robots}<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">"""


def nav_html(root):
    services_dropdown = "".join(
        f'<a href="{root}{slug}/index.html"><span>{icon}</span>{name}</a>'
        for slug, name, icon in SERVICES
    )
    return f"""<nav>
  <a href="{root}index.html" class="logo">Removals<span>Nation</span></a>
  <button class="hamburger" id="hamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <ul class="nav-links">
    <li class="nav-dropdown">
      <button type="button" class="nav-dropdown-trigger" aria-haspopup="true" aria-expanded="false" aria-controls="services-dropdown-panel">Services <span class="nav-caret">▾</span></button>
      <div class="nav-dropdown-panel" id="services-dropdown-panel">
        <div class="nav-dropdown-inner">
          {services_dropdown}
        </div>
      </div>
    </li>
    <li><a href="{root}locations.html">Locations</a></li>
    <li><a href="{root}removals-within-the-m25/index.html">M25 Removals</a></li>
    <li><a href="{root}blog/index.html">Knowledge Hub</a></li>
    <li><a href="{root}partner-with-us/index.html">For Businesses</a></li>
    <li><a href="{root}about.html">About</a></li>
    <li><a href="{root}contact.html">Contact</a></li>
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
    <a href="{root}removals-within-the-m25/index.html" class="mobile-nav-link">Removals Within the M25 <span class="arrow">›</span></a>
    <a href="{root}blog/index.html" class="mobile-nav-link">Knowledge Hub <span class="arrow">›</span></a>
    <a href="{root}partner-with-us/index.html" class="mobile-nav-link">For Businesses <span class="arrow">›</span></a>
    <a href="{root}about.html" class="mobile-nav-link">About Us <span class="arrow">›</span></a>
    <a href="{root}contact.html" class="mobile-nav-link">Contact <span class="arrow">›</span></a>
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
      <p style="font-size:.75rem;color:var(--text-muted);margin-top:10px">
        {SITE_NAME} is a trading style of {LEGAL_ENTITY} (Company No. {COMPANY_NUMBER}).
      </p>
    </div>
    <div class="footer-col">
      <h3>Services</h3>
      <a href="{root}house-removals/index.html">House Removals</a>
      <a href="{root}office-removals/index.html">Office Removals</a>
      <a href="{root}man-and-van/index.html">Man &amp; Van</a>
      <a href="{root}storage/index.html">Storage</a>
      <a href="{root}packing-services/index.html">Packing</a>
      <a href="{root}international-removals/index.html">International</a>
    </div>
    <div class="footer-col">
      <h3>Company</h3>
      <a href="{root}about.html">About Us</a>
      <a href="{root}removals-within-the-m25/index.html">Removals Within the M25</a>
      <a href="{root}partner-with-us/index.html">For Businesses</a>
      <a href="{root}blog/index.html">Knowledge Hub</a>
      <a href="{root}contact.html">Contact</a>
    </div>
    <div class="footer-col">
      <h3>Legal</h3>
      <a href="{root}privacy.html">Privacy Policy</a>
      <a href="{root}terms.html">Terms &amp; Cancellation Policy</a>
      <a href="{root}contact.html">Get in Touch</a>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© {datetime.date.today().year} {SITE_NAME}. All rights reserved.</span>
    <span>Fully insured · Nationwide coverage</span>
  </div>
</footer>"""


def whatsapp_fab_html():
    """Floating WhatsApp button, bottom-right on every page. Sits above the
    reserved bottom-right zone (below it) where the live chat widget will go
    once it's added — do not lower this button's `bottom` offset without
    also checking it won't collide with the live chat bubble."""
    message = "Hi RemovalsNation, I'd like a quote"
    return f"""<a href="https://wa.me/{WHATSAPP_NUMBER}?text={urlquote(message)}"
   class="whatsapp-fab" target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp">
  <svg viewBox="0 0 24 24" fill="#fff" xmlns="http://www.w3.org/2000/svg">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
    <path d="M12.001 2C6.478 2 2 6.477 2 12c0 1.82.478 3.6 1.386 5.163L2 22l4.951-1.328A9.96 9.96 0 0 0 12.001 22C17.523 22 22 17.523 22 12S17.523 2 12.001 2zm0 18.194a8.17 8.17 0 0 1-4.166-1.144l-.299-.177-3.048.817.822-3.021-.194-.31A8.19 8.19 0 0 1 3.805 12c0-4.516 3.68-8.194 8.196-8.194 4.516 0 8.194 3.678 8.194 8.194 0 4.516-3.678 8.194-8.194 8.194z"/>
  </svg>
</a>"""


def call_fab_html():
    """Floating Call Now button, bottom-left on every page (mirrors
    whatsapp_fab_html() on the opposite corner so they never collide),
    always visible while scrolling, showing the phone number."""
    return f"""<a href="{PHONE_HREF}" class="call-fab" aria-label="Call {SITE_NAME} now">
  <svg viewBox="0 0 24 24" fill="#fff" xmlns="http://www.w3.org/2000/svg">
    <path d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1C10.61 21 3 13.39 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.46.57 3.58a1 1 0 0 1-.25 1.01l-2.2 2.2Z"/>
  </svg>
  <span>{PHONE}</span>
</a>"""


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
(function(){
  document.querySelectorAll('.file-upload input[type="file"]').forEach(function(input) {
    var wrap = input.closest('.file-upload');
    var out = wrap.querySelector('.file-upload-filenames');
    input.addEventListener('change', function() {
      var n = input.files.length;
      wrap.classList.toggle('has-files', n > 0);
      if (!out) return;
      if (n === 0) { out.textContent = ''; }
      else if (n === 1) { out.textContent = input.files[0].name; }
      else { out.textContent = n + ' photos selected'; }
    });
  });
})();
(function(){
  var dropdown = document.querySelector('.nav-dropdown');
  var trigger = document.querySelector('.nav-dropdown-trigger');
  if (!dropdown || !trigger) return;
  function open() { trigger.setAttribute('aria-expanded', 'true'); }
  function close() { trigger.setAttribute('aria-expanded', 'false'); }
  dropdown.addEventListener('mouseenter', open);
  dropdown.addEventListener('mouseleave', close);
  dropdown.addEventListener('focusin', open);
  dropdown.addEventListener('focusout', function(e) {
    if (!dropdown.contains(e.relatedTarget)) close();
  });
})();
</script>"""



# ── Cost tables per service ────────────────────────────────────────────────────
# Base figures represent typical UK-average pricing. Actual on-page tables are
# scaled by REGION_PRICE_TIERS below so a page doesn't show identical numbers
# for Mayfair and a village in the Highlands — this is informational banding,
# not a binding quote (the copy and quote form make that clear).
#
# Rows are (label, low, high, suffix) where suffix is "" (plain range),
# "+" (open-ended top end), "/mo" (storage rental), or "add" (add-on charge,
# rendered as "Add £X – £Y").
COST_TABLES_BASE = {
    "house-removals": [
        ("Studio / 1 Bedroom", 300, 600, ""),
        ("2 Bedroom Property", 500, 900, ""),
        ("3 Bedroom Property", 700, 1200, ""),
        ("4+ Bedroom Property", 1000, 2000, "+"),
        ("Long Distance (200+ miles)", 200, 500, "add"),
    ],
    "office-removals": [
        ("Small Office (1–5 desks)", 400, 900, ""),
        ("Medium Office (5–20 desks)", 800, 2000, ""),
        ("Large Office (20+ desks)", 2000, 5000, "+"),
        ("IT Equipment Move", 200, 500, "add"),
    ],
    "man-and-van": [
        ("1 Man + Small Van (2hr)", 60, 120, ""),
        ("1 Man + Large Van (2hr)", 80, 150, ""),
        ("2 Men + Van (half day)", 150, 280, ""),
        ("2 Men + Van (full day)", 250, 450, ""),
    ],
    "storage": [
        ("Small Unit (25 sq ft)", 30, 60, "/mo"),
        ("Medium Unit (50 sq ft)", 60, 100, "/mo"),
        ("Large Unit (100 sq ft)", 100, 160, "/mo"),
        ("Container Storage", 80, 150, "/mo"),
    ],
    "packing-services": [
        ("Studio / 1 Bed", 150, 300, ""),
        ("2 Bedroom", 250, 450, ""),
        ("3 Bedroom", 350, 600, ""),
        ("4+ Bedroom", 500, 900, ""),
    ],
    "same-day-removals": [
        ("Single Item", 80, 180, ""),
        ("Small Load", 150, 280, ""),
        ("Half House Load", 280, 500, ""),
        ("Full House Load", 500, 900, ""),
    ],
    # International removals aren't scaled by UK origin region — destination
    # country/distance dominates the price far more than which UK town the
    # move starts in, so scaling this table would be misleading rather than
    # more accurate.
    "international-removals": [
        ("Europe (1–2 bed)", "£1,500 – £3,500"),
        ("Europe (3–4 bed)", "£3,000 – £6,000"),
        ("USA / Canada", "£4,000 – £9,000"),
        ("Australia / NZ", "£5,000 – £12,000"),
    ],
    "piano-removals": [
        ("Upright Piano", 150, 350, ""),
        ("Grand Piano", 300, 700, ""),
        ("Upstairs / Stairs", 100, 200, "add"),
        ("Long Distance", 200, 500, "add"),
    ],
}

# Regional price-tier multipliers, grounded in 2026 UK removals market data:
# London runs ~25-35% above the national average (highest in central/west
# London due to parking permits, ULEZ/congestion charge exposure and access
# time); the South East commuter belt sits ~10-15% above average; the
# Midlands is close to the national baseline; the North, Scotland, Wales and
# Northern Ireland typically run 10-15% below it. These are deliberately
# rounded, approximate bands — not a substitute for the quote form.
REGION_PRICE_TIERS = {
    # Central London — highest tier
    "Central London": 1.35,
    # Rest of Greater London
    "North London": 1.18, "North West London": 1.18, "North East London": 1.16,
    "East London": 1.18, "South East London": 1.16, "South London": 1.18,
    "South West London": 1.22, "West London": 1.28,
    # M25 commuter belt
    "Surrey": 1.12, "Hertfordshire": 1.12, "Essex": 1.10, "Kent": 1.10, "Berkshire": 1.12,
    # Wider South East / South
    "East Sussex": 1.06, "West Sussex": 1.06, "Oxfordshire": 1.08,
    "Buckinghamshire": 1.08, "Hampshire": 1.05, "Isle of Wight": 1.04,
    # East of England
    "Bedfordshire": 1.03, "Cambridgeshire": 1.03, "Suffolk": 1.01,
    "Norfolk": 1.00, "Northamptonshire": 1.00,
    # Midlands — national baseline
    "West Midlands": 1.00, "Warwickshire": 1.00, "Staffordshire": 0.98,
    "Shropshire": 0.97, "Worcestershire": 0.98, "Herefordshire": 0.96,
    "Leicestershire": 0.98, "Nottinghamshire": 0.97, "Derbyshire": 0.97,
    "Lincolnshire": 0.96, "Rutland": 0.98,
    # South West
    "Gloucestershire": 0.99, "Wiltshire": 0.98, "Somerset": 0.96,
    "Dorset": 0.98, "Devon": 0.95, "Cornwall": 0.94,
    # North of England
    "Greater Manchester": 0.92, "Merseyside": 0.90, "Cheshire": 0.93,
    "Lancashire": 0.90, "West Yorkshire": 0.91, "South Yorkshire": 0.90,
    "East Yorkshire": 0.89, "North Yorkshire": 0.91, "County Durham": 0.88,
    "Tyne and Wear": 0.89, "Northumberland": 0.88, "Cumbria": 0.90, "Teesside": 0.88,
    # Devolved nations
    "Scotland": 0.87, "Wales": 0.87, "Northern Ireland": 0.85,
}


def region_price_multiplier(region):
    return REGION_PRICE_TIERS.get(region, 1.0)


# Postcode-area multipliers for pages with no fixed location (homepage, M25
# page, service landing pages) — the live quote calculator on those pages
# only has a free-text postcode to work with, so it maps the postcode's
# leading letters (its "area", e.g. "SW", "M", "BT") straight to a
# multiplier using the same tiering logic as REGION_PRICE_TIERS, rather than
# going through the region system built for known locations. Not exhaustive
# — postcode areas covering only a handful of small towns are omitted and
# fall back to the UK-average 1.0 multiplier, same graceful degradation as
# an unmapped region.
POSTCODE_AREA_TIERS = {
    # Central London
    "EC": 1.35, "WC": 1.35,
    # Rest of Greater London
    "W": 1.28, "SW": 1.22, "NW": 1.18, "N": 1.18, "E": 1.18, "SE": 1.16,
    # Outer London / M25 fringe
    "BR": 1.16, "CR": 1.18, "DA": 1.12, "EN": 1.15, "HA": 1.18, "IG": 1.16,
    "KT": 1.18, "RM": 1.10, "SM": 1.16, "TW": 1.18, "UB": 1.16, "WD": 1.12,
    # Surrey / Berkshire / Hertfordshire commuter belt
    "GU": 1.12, "RH": 1.10, "SL": 1.10, "RG": 1.08, "AL": 1.12, "SG": 1.05,
    "HP": 1.08, "LU": 1.03, "MK": 1.02,
    # Essex / Kent / Sussex
    "CM": 1.08, "SS": 1.05, "CO": 1.00, "ME": 1.08, "CT": 1.04, "TN": 1.08,
    "BN": 1.08,
    # Wider South / South East
    "OX": 1.08, "SO": 1.02, "PO": 1.02, "BH": 1.00, "SP": 0.98, "DT": 0.98,
    # East of England
    "CB": 1.05, "PE": 0.98, "NR": 0.98, "IP": 0.99,
    # Midlands
    "B": 1.00, "CV": 0.99, "DY": 0.98, "WV": 0.97, "WS": 0.98, "ST": 0.96,
    "TF": 0.96, "SY": 0.96, "WR": 0.97, "HR": 0.95, "LE": 0.97, "NG": 0.96,
    "DE": 0.96, "LN": 0.95, "NN": 1.00,
    # South West
    "BS": 0.99, "GL": 0.98, "SN": 0.98, "BA": 1.00, "TA": 0.96, "EX": 0.95,
    "PL": 0.94, "TQ": 0.94, "TR": 0.94,
    # North of England
    "M": 0.92, "OL": 0.91, "SK": 0.92, "WA": 0.92, "WN": 0.90, "BL": 0.90,
    "L": 0.90, "CH": 0.93, "PR": 0.90, "BB": 0.89, "FY": 0.89, "LA": 0.90,
    "CA": 0.90, "LS": 0.91, "BD": 0.90, "HX": 0.90, "HD": 0.90, "WF": 0.90,
    "S": 0.90, "DN": 0.89, "HU": 0.89, "YO": 0.92, "DL": 0.88, "DH": 0.88,
    "SR": 0.89, "NE": 0.89, "TS": 0.88,
    # Scotland
    "G": 0.87, "EH": 0.87, "AB": 0.87, "DD": 0.87, "KY": 0.87, "FK": 0.87,
    "PA": 0.87, "ML": 0.87, "PH": 0.87, "IV": 0.87, "KA": 0.87, "DG": 0.87,
    "TD": 0.87, "ZE": 0.87, "KW": 0.87, "HS": 0.87,
    # Wales
    "CF": 0.87, "SA": 0.87, "NP": 0.87, "LD": 0.87, "LL": 0.87,
    # Northern Ireland
    "BT": 0.85,
}


def postcode_price_multiplier(postcode):
    """Extract the leading letters (postcode area) from free-text input and
    look up its multiplier, falling back to the UK-average 1.0."""
    match = re.match(r"[A-Za-z]+", (postcode or "").strip())
    if not match:
        return 1.0
    area = match.group(0).upper()
    # Try the full 2-letter area first (e.g. "EC"), then the 1-letter
    # fallback (e.g. area "ECB" doesn't exist, but this keeps the lookup
    # order correct for genuinely single-letter areas like "M" or "B").
    return POSTCODE_AREA_TIERS.get(area[:2], POSTCODE_AREA_TIERS.get(area[:1], 1.0))


def _scale(n, mult):
    """Scale a base price by the regional multiplier, rounding to a clean
    number (nearest £5 under £150, nearest £10 above) so the result still
    reads like a real price band rather than an oddly precise output."""
    scaled = n * mult
    step = 5 if n < 150 else 10
    return int(round(scaled / step) * step)


# ── Page builder ──────────────────────────────────────────────────────────────

def cost_table_html(svc_slug, multiplier=1.0):
    rows = COST_TABLES_BASE.get(svc_slug, COST_TABLES_BASE["house-removals"])
    cells = []
    for row in rows:
        if len(row) == 2:
            # international-removals: fixed strings, not regionally scaled
            label, price = row
            cells.append(f'<div class="cost-row"><span>{label}</span><span>{price}</span></div>')
            continue
        label, lo, hi, suffix = row
        lo_s, hi_s = _scale(lo, multiplier), _scale(hi, multiplier)
        if suffix == "+":
            price = f"£{lo_s:,} – £{hi_s:,}+"
        elif suffix == "/mo":
            price = f"£{lo_s:,} – £{hi_s:,}/mo"
        elif suffix == "add":
            price = f"Add £{lo_s:,} – £{hi_s:,}"
        else:
            price = f"£{lo_s:,} – £{hi_s:,}"
        cells.append(f'<div class="cost-row"><span>{label}</span><span>{price}</span></div>')
    return '<div class="cost-table">' + "".join(cells) + "</div>"


# Area profiles group regions by the access/context factors that actually
# change what's relevant to ask — parking permits and ULEZ in London,
# driveway access in commuter towns, city-centre flats in regional cities,
# rural/village access elsewhere, and cross-border context for the devolved
# nations. This is the second half of the differentiation: pricing tiers
# handle "how much", profiles handle "what's actually relevant here".
LONDON_REGIONS = {
    "Central London", "North London", "North West London", "North East London",
    "East London", "South East London", "South London", "South West London", "West London",
}
COMMUTER_BELT_REGIONS = {
    "Surrey", "Hertfordshire", "Essex", "Kent", "Berkshire",
    "East Sussex", "West Sussex", "Oxfordshire", "Buckinghamshire",
    "Hampshire", "Bedfordshire", "Cambridgeshire",
}
CITY_URBAN_REGIONS = {
    "West Midlands", "Greater Manchester", "Merseyside",
    "West Yorkshire", "South Yorkshire", "Tyne and Wear",
}
# Standalone major cities whose county/region is otherwise a mostly-rural
# area (e.g. Nottingham sits in Nottinghamshire alongside dozens of small
# market towns and villages) — region-level classification alone would file
# these under "rural-regional" and generate FAQs about narrow country lanes
# and village addresses, which reads as obviously wrong for a city of this
# size. Checked by location name instead of region so the surrounding
# smaller towns in the same county still get the rural-regional profile
# they actually match.
CITY_URBAN_NAMES = {
    "Bristol", "Leicester", "Nottingham", "Derby", "Stoke-on-Trent",
    "Hull", "Norwich", "Plymouth",
}
DEVOLVED_REGIONS = {"Scotland": "Scotland", "Wales": "Wales", "Northern Ireland": "Northern Ireland"}


def area_profile(region, loc_name=None):
    if loc_name in CITY_URBAN_NAMES:
        return "city-urban"
    if region in LONDON_REGIONS:
        return "london"
    if region in COMMUTER_BELT_REGIONS:
        return "commuter-belt"
    if region in CITY_URBAN_REGIONS:
        return "city-urban"
    if region in DEVOLVED_REGIONS:
        return "devolved"
    return "rural-regional"


def build_intro_html(svc_name, loc_name, region, county, postcode):
    """Profile-aware 'Why Choose Us' copy — same five area profiles as the
    FAQs, so the two genuinely different-content blocks on the page (pricing
    context aside) aren't both running off the same underlying logic twice."""
    svc = svc_name.lower()
    profile = area_profile(region, loc_name)

    if profile == "london":
        return f"""<p>{SITE_NAME} is a London removal company serving {loc_name} and the
       wider {region} area. Narrow streets, permit parking and lift access are
       part of daily life here — our teams plan for it rather than treat it
       as a surprise on moving day.</p>
    <p>Whether you're moving locally within {loc_name} or relocating further
       afield, our {svc} teams are fully insured and ready to help. We cover
       all postcodes in the {postcode} area.</p>"""

    if profile == "commuter-belt":
        return f"""<p>{SITE_NAME} regularly serves {loc_name} and the wider {county}
       commuter belt, including moves in and out of London. Our fully insured
       teams handle everything from a straightforward local move to a longer
       relocation across {region}.</p>
    <p>Whether you're moving locally within {loc_name} or relocating further
       afield, our {svc} teams are ready to help. We cover all postcodes in
       the {postcode} area.</p>"""

    if profile == "city-urban":
        return f"""<p>{SITE_NAME} is a nationwide removal company with regular {svc}
       experience across {loc_name} and the wider {county} area — from
       city-centre flats to family homes further out.</p>
    <p>Whether you're moving locally within {loc_name} or relocating further
       afield, our fully insured {svc} teams are ready to help. We cover all
       postcodes in the {postcode} area.</p>"""

    if profile == "devolved":
        return f"""<p>{SITE_NAME} is a nationwide removal company serving {loc_name} and
       all of {region}, including cross-border moves to and from the rest of
       the UK. Our experienced, fully insured teams handle every aspect of
       your move with care and efficiency.</p>
    <p>Whether you're moving locally within {loc_name} or relocating further
       afield, our {svc} teams are ready to help. We cover all postcodes in
       the {postcode} area.</p>"""

    # rural-regional
    return f"""<p>{SITE_NAME} is a nationwide removal company serving {loc_name} and all
       of {county}, including villages and rural addresses beyond the town
       centre. Our experienced, fully insured teams handle every aspect of
       your move with care and efficiency.</p>
    <p>Whether you're moving locally within {loc_name} or relocating further
       afield, our {svc} teams are ready to help. We cover all postcodes in
       the {postcode} area.</p>"""


def build_faqs(svc_name, loc_name, region, county):
    svc = svc_name.lower()
    profile = area_profile(region, loc_name)

    if profile == "london":
        return [
            (
                f"Do I need a parking permit for the {svc} van in {loc_name}?",
                f"Many streets in {loc_name} operate controlled parking zones. "
                f"Flag it when you book and we can look at arranging a parking "
                f"suspension in advance where needed.",
            ),
            (
                f"Does {svc} cost more if there are stairs or no lift?",
                f"Access is factored into your quote up front, not added as a "
                f"surprise fee on the day — tell us about stairs, lift size or "
                f"restricted access in {loc_name} when you book.",
            ),
            (
                "Will ULEZ or the Congestion Charge affect my move?",
                f"Both apply to vehicles driving within their zones. Mention your "
                f"postcode in {loc_name} and destination when you book and we'll "
                f"factor it into your price upfront, not after.",
            ),
            (
                f"How far ahead should I book {svc} in {loc_name}?",
                "A few days' notice usually works for a weekday move. If a "
                "parking suspension or lift booking is needed, 1-2 weeks ahead "
                "gives the best chance of your preferred slot.",
            ),
        ]

    if profile == "commuter-belt":
        return [
            (
                f"Do you cover moves between {loc_name} and London?",
                f"Yes — {loc_name} is one of our regular routes in and out of "
                f"London, so we know the journey times and access points well.",
            ),
            (
                f"Is parking easier in {loc_name} than in central London?",
                f"Generally yes — most {region} properties have driveways or "
                f"easier on-street parking, which usually means a quicker, "
                f"more cost-effective move than an equivalent central London job.",
            ),
            (
                f"Are your teams in {loc_name} fully insured?",
                f"Yes — every RemovalsNation team operating in {loc_name} carries "
                f"full public liability and goods-in-transit insurance as standard.",
            ),
            (
                f"What's included in your {svc} service in {loc_name}?",
                "Our standard service includes loading, transport and unloading. "
                "Packing, storage and dismantling can all be added.",
            ),
        ]

    if profile == "city-urban":
        return [
            (
                f"Do you cover city-centre flats in {loc_name}?",
                f"Yes — city-centre moves in {loc_name} are common for us, "
                f"including flats with lifts, secure entry systems or resident "
                f"parking permits.",
            ),
            (
                f"Do you charge extra for awkward access in {loc_name}?",
                "No hidden charges — if a building or street has awkward access, "
                "we ask about it before booking, not on the day.",
            ),
            (
                f"How quickly can you arrange {svc} in {loc_name}?",
                f"We can typically confirm a booking in {loc_name} within a few "
                f"hours. For urgent same-day moves, call us directly on {PHONE}.",
            ),
            (
                f"What's included in your {svc} service in {loc_name}?",
                "Our standard service includes loading, transport and unloading. "
                "Packing, storage and dismantling can all be added.",
            ),
        ]

    if profile == "devolved":
        return [
            (
                f"Do you handle moves between {loc_name} and the rest of the UK?",
                f"Yes — cross-border moves to and from {loc_name} are one of our "
                f"regular services. Get a distance-based price with the quote form.",
            ),
            (
                f"Are your teams in {loc_name} fully insured?",
                f"Yes — every RemovalsNation team operating in {loc_name} carries "
                f"full public liability and goods-in-transit insurance as standard.",
            ),
            (
                f"How far in advance should I book {svc} in {loc_name}?",
                "For a fixed date, 2-4 weeks' notice gives the best choice of "
                "slots, especially for longer cross-border routes.",
            ),
            (
                f"What's included in your {svc} service in {loc_name}?",
                "Our standard service includes loading, transport and unloading. "
                "Packing, storage and dismantling can all be added.",
            ),
        ]

    # rural-regional
    return [
        (
            f"Do you cover villages and rural addresses near {loc_name}?",
            f"Yes — we regularly serve rural properties around {loc_name} and "
            f"the wider {county} area, including addresses without a formal "
            f"street address.",
        ),
        (
            f"Will a large van fit down narrow lanes near {loc_name}?",
            "We assess access in advance and can arrange a smaller shuttle "
            "vehicle where a long or narrow driveway needs it.",
        ),
        (
            f"How far is {loc_name} from your nearest available team?",
            f"We operate across {county} and the wider region, so response "
            f"times in {loc_name} are generally quick — call to check "
            f"availability for your date.",
        ),
        (
            f"Are your teams in {loc_name} fully insured?",
            f"Yes — every RemovalsNation team operating in {loc_name} carries "
            f"full public liability and goods-in-transit insurance as standard.",
        ),
    ]


def faq_html(faqs):
    return '<div class="faqs">' + "".join(
        f'<div class="faq">'
        f'<div class="faq-q">{q}</div>'
        f'<div class="faq-a">{a}</div>'
        f"</div>"
        for q, a in faqs
    ) + "</div>"


def jsonld_html(data):
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def organization_jsonld():
    # "sameAs" (links to social/profile pages) is deliberately omitted rather than
    # left as an empty array — an empty array isn't a valid value for a URL-typed
    # schema.org property and gets flagged as a structured-data error. Add it back
    # with real profile URLs (Facebook, Instagram, Google Business Profile, etc.)
    # once they exist.
    return jsonld_html({
        "@context": "https://schema.org",
        "@type": "MovingCompany",
        "name": SITE_NAME,
        "url": f"{SITE_URL}/",
        "logo": f"{SITE_URL}/assets/android-chrome-512x512.png",
        "image": f"{SITE_URL}/assets/og-image.png",
        "telephone": PHONE_HREF.replace("tel:", ""),
        "priceRange": "££",
        "areaServed": {"@type": "Country", "name": "United Kingdom"},
    })


def location_jsonld(svc_slug, svc_name, loc_name, region, county, postcode, faqs, canonical):
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": svc_name, "item": f"{SITE_URL}/{svc_slug}/"},
            {"@type": "ListItem", "position": 3, "name": loc_name, "item": canonical},
        ],
    }
    business = {
        "@context": "https://schema.org",
        "@type": "MovingCompany",
        "name": f"{SITE_NAME} — {svc_name} in {loc_name}",
        "url": canonical,
        "image": f"{SITE_URL}/assets/og-image.png",
        "telephone": PHONE_HREF.replace("tel:", ""),
        "priceRange": "££",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": loc_name,
            "addressRegion": county,
            "postalCode": postcode,
            "addressCountry": "GB",
        },
        "areaServed": {"@type": "City", "name": f"{loc_name}, {region}"},
        "parentOrganization": {"@type": "Organization", "name": SITE_NAME, "url": f"{SITE_URL}/"},
    }
    faqpage = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }
    return "\n".join(jsonld_html(d) for d in (business, breadcrumb, faqpage))


def sidebar_services_html(root, loc_slug=None, current_svc_slug=None):
    """Service list for the sidebar. When loc_slug is given (location pages),
    links point to the same location under each other service — this is the
    main internal-linking path that makes the ~10,000 location/service pages
    reachable by crawlers instead of orphaned pages reliant on the sitemap alone."""
    parts = []
    for slug, name, icon in SERVICES:
        current_attr = ' aria-current="page"' if slug == current_svc_slug else ""
        href = f"{root}{slug}/{loc_slug}/index.html" if loc_slug else f"{root}{slug}/index.html"
        parts.append(
            f'<a href="{href}" class="sidebar-link"{current_attr}>'
            f"<span>{icon}</span>{name}</a>"
        )
    links = "".join(parts)
    return f'<div class="sidebar-card" style="margin-bottom:20px"><h3>Our Services</h3>{links}</div>'


def quote_contact_and_photos_html():
    """Phone number, email, and an optional photo-upload dropzone — shared by
    both booking_form_html() implementations (this file's location-page
    version and build_static_pages.py's generic version) so they can't drift
    out of sync. Requires the enclosing <form> to have
    enctype="multipart/form-data" for the photo upload to actually work."""
    return """<div class="qrow">
      <div class="form-group">
        <label for="f-moving-date">Moving Date</label>
        <input type="date" id="f-moving-date" name="moving_date" style="font-size:16px">
      </div>
      <div class="form-group">
        <label for="f-phone">Phone Number</label>
        <input type="tel" id="f-phone" name="phone" placeholder="07123 456789" required style="font-size:16px">
      </div>
    </div>
    <div class="form-group" style="margin-bottom:12px">
      <label for="f-email">Email Address</label>
      <input type="email" id="f-email" name="email" placeholder="you@example.com" style="font-size:16px">
    </div>
    <div class="form-group" style="margin-bottom:12px">
      <label for="f-photos">Photos of Items (optional)</label>
      <label class="file-upload">
        <span class="file-upload-icon">📷</span>
        <span class="file-upload-text"><strong>Click to upload</strong> photos of what needs removing</span>
        <span class="file-upload-filenames"></span>
        <input type="file" id="f-photos" name="photos" accept="image/*" multiple>
      </label>
    </div>"""


def booking_form_html(svc_name, loc_name, postcode):
    return f"""<div class="quote-card">
  <h2>Book Now — {loc_name}</h2>
  <p class="form-sub">60 seconds · Confirmed price instantly</p>
  <form action="https://formspree.io/f/{FORMSPREE_ID}" method="POST" enctype="multipart/form-data">
    <div class="qrow">
      <div class="form-group">
        <label for="f-move-type">Move Type</label>
        <select id="f-move-type" name="move_type">
          <option>{svc_name}</option>
          <option>House Removals</option><option>Office Removals</option>
          <option>Man &amp; Van</option><option>Storage</option><option>International</option>
        </select>
      </div>
      <div class="form-group">
        <label for="f-property-size">Property Size</label>
        <select id="f-property-size" name="property_size">
          <option>Studio/1 Bed</option><option>2 Bedroom</option>
          <option>3 Bedroom</option><option>4+ Bedroom</option><option>Commercial</option>
        </select>
      </div>
    </div>
    <div class="qrow">
      <div class="form-group">
        <label for="f-from-postcode">From Postcode</label>
        <input type="text" id="f-from-postcode" name="from_postcode" placeholder="{postcode} 1AA" style="font-size:16px">
      </div>
      <div class="form-group">
        <label for="f-to-postcode">To Postcode</label>
        <input type="text" id="f-to-postcode" name="to_postcode" placeholder="Destination" style="font-size:16px">
      </div>
    </div>
    {quote_contact_and_photos_html()}
    <input type="hidden" name="_subject" value="New Removal Booking — {SITE_NAME}">
    <input type="hidden" name="location" value="{loc_name}">
    <input type="hidden" name="service" value="{svc_name}">
    <input type="hidden" name="_next" value="{SITE_URL}/thank-you.html">
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
    canonical_path = f"{svc_slug}/{slug}/"
    canonical = f"{SITE_URL}/{canonical_path}"
    title = f"{svc_name} in {name} | {SITE_NAME}"
    description = (
        f"Professional {svc_name.lower()} in {name}, {county}. "
        f"Fully insured, instant booking. {SITE_NAME} — your trusted removal company."
    )
    faqs = build_faqs(svc_name, name, region, county)
    price_mult = region_price_multiplier(region)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{description}">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/shared.css">
{favicon_html(root)}
{gtag_html()}
{seo_html(canonical_path, title, description, root)}
{location_jsonld(svc_slug, svc_name, name, region, county, postcode, faqs, canonical)}
</head>
<body>
<a href="#main-content" class="skip-link">Skip to main content</a>
{nav_html(root)}
{mobile_menu_html(root)}
<main id="main-content">
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
      <a href="{PHONE_HREF}" class="btn-primary" style="margin-top:22px;font-size:1.05rem;padding:16px 32px;display:inline-block">
        📞 Call Now — {PHONE}
      </a>
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
    {build_intro_html(svc_name, name, region, county, postcode)}
    <h2>{svc_name} Costs in {name}</h2>
    {cost_table_html(svc_slug, price_mult)}
    <p style="font-size:.8rem;color:var(--text-muted);margin-top:10px">
      Typical {region} pricing band, based on property size and access — get an
      exact quote in 60 seconds using the form above.
    </p>
    <h2>Frequently Asked Questions</h2>
    {faq_html(faqs)}
  </div>
  <aside class="content-sidebar">
    {sidebar_services_html(root, loc_slug=slug, current_svc_slug=svc_slug)}
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
{whatsapp_fab_html()}
{call_fab_html()}
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
    title = f"All UK Locations | {SITE_NAME}"
    description = f"{SITE_NAME} covers {total}+ locations across the UK. Find professional removal services in your area."

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{description}">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/shared.css">
{favicon_html(root)}
{gtag_html()}
{seo_html("locations.html", title, description, root)}
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
<a href="#main-content" class="skip-link">Skip to main content</a>
{nav_html(root)}
{mobile_menu_html(root)}
<main id="main-content">
<div class="locs-hero">
  <div class="locs-count">📍 {total} Locations Covered</div>
  <h1>Removal Services Across the UK</h1>
  <p>{SITE_NAME} provides professional, fully insured removal services in {total}+ towns and cities
     across England, Scotland, Wales and Northern Ireland. Find your location below.</p>
  <p style="margin-top:14px">Moving in the capital? See our dedicated
     <a href="{root}removals-within-the-m25/index.html" style="color:var(--orange)">removals within the M25</a>
     page for London, Surrey, Herts, Essex &amp; Kent coverage.</p>
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
{whatsapp_fab_html()}
{call_fab_html()}
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
