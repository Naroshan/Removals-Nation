"""
build_static_pages.py
----------------------
Generates the hand-authored top-level pages that build_pages.py doesn't
cover: index, about, contact, privacy, thank-you, blog (+ posts), and
partner-with-us.

Usage:
    python scripts/build_static_pages.py
    python scripts/build_static_pages.py --dist output
"""

import argparse
from pathlib import Path

from build_pages import (
    FORMSPREE_ID, PHONE, PHONE_HREF, SITE_NAME, SITE_URL, LEGAL_ENTITY, COMPANY_NUMBER,
    SERVICES, nav_html, mobile_menu_html, footer_html, MENU_JS,
    cost_table_html, favicon_html, gtag_html, seo_html, organization_jsonld, jsonld_html,
    whatsapp_fab_html, call_fab_html, faq_html, quote_contact_and_photos_html,
)

M25_REGIONS = [
    "Central London", "North London", "North West London", "North East London",
    "East London", "South East London", "South London", "South West London", "West London",
    "Surrey", "Hertfordshire", "Essex", "Kent",
]

HOME_FAQS = [
    (
        "How much does a removal cost?",
        "It depends on property size, distance and any extras like packing or storage — "
        "typically £300–£600 for a studio, up to £1,000–£2,000+ for a 4+ bedroom house. "
        "Use the quote form above or pick your location for detailed local pricing.",
    ),
    (
        "How far in advance should I book?",
        "For a fixed date, 2–4 weeks' notice gives you the best choice of slots. If you "
        "need to move sooner, same-day and short-notice man and van hire is available in "
        "most areas — just call to check.",
    ),
    (
        "Are you insured?",
        "Yes — every RemovalsNation team carries full public liability and goods-in-transit "
        "insurance as standard, on every job, at no extra cost.",
    ),
    (
        "Do you offer packing as well as moving?",
        "Yes, packing services can be added to any removal — from a few fragile items to a "
        "full property pack. You can add it when you book or ask your local team on the day.",
    ),
]

CONTACT_FAQS = [
    (
        "How quickly will you respond?",
        "We aim to reply to every enquiry within a few hours during the day, and "
        "same-day for anything sent in the morning. For urgent same-day moves, "
        "calling us directly is faster than the contact form.",
    ),
    (
        "Can I get a quote without booking?",
        "Yes — sending your move details through this form or the quote form on any "
        "page gets you a price with no obligation to book.",
    ),
    (
        "Do you cover my area?",
        "We cover 1,700+ towns and cities across England, Scotland, Wales and "
        "Northern Ireland. Check the full list on our locations page, or just ask.",
    ),
]

def hero_stats_html(stats):
    items = "".join(
        f'<div><span class="hero-stat-n">{n}</span><span class="hero-stat-l">{l}</span></div>'
        for n, l in stats
    )
    return f'<div class="hero-stats">{items}</div>'


HOW_IT_WORKS_STEPS = [
    ("📝", "Get your quote", "Fill in the form above — property size, dates and "
     "postcodes. Takes about 60 seconds, no obligation to book."),
    ("📅", "Confirm your date", "We'll be in touch to confirm details and lock in "
     "your moving slot, so your date is secured in advance."),
    ("🚚", "Team arrives", "A fully insured local crew turns up on the day, loads "
     "up carefully and gets everything where it needs to go."),
    ("✅", "Move complete", "Everything's unloaded and in place. Settle up on the "
     "day — no hidden fees, no surprises."),
]


def how_it_works_html(steps=None):
    steps = steps or HOW_IT_WORKS_STEPS
    cards = "".join(
        f'<div class="step-card"><span class="step-num">{i}</span>'
        f'<span class="step-icon">{icon}</span><h3>{title}</h3><p>{desc}</p></div>'
        for i, (icon, title, desc) in enumerate(steps, start=1)
    )
    return f"""<section class="section" style="padding:0 48px 64px">
  <div class="section-tag">How It Works</div>
  <h2 class="section-title">Moving With RemovalsNation</h2>
  <div class="steps-grid">{cards}</div>
</section>"""


DIFFERENTIATION_POINTS = [
    ("🎯", "One Quote, Not Five", "Comparison and quote-request sites hand your "
     "number to several companies at once, so expect calls from firms you've "
     "never vetted. Get one quote from us, and that's the only call you'll get."),
    ("🚚", "Our Crews, Not a Subcontractor", "The team who gives you a price is "
     "the team who turns up on the day. Every RemovalsNation crew is our own, "
     "directly insured — not a local firm we've passed your job on to."),
    ("⏱️", "Booked in Minutes", "No re-explaining your move to five different "
     "companies. One conversation, one fixed price, and your date is locked "
     "in — usually within the same call."),
]


def differentiation_html(points=None):
    points = points or DIFFERENTIATION_POINTS
    cards = "".join(
        f'<div class="partner-card"><h3>{icon} {title}</h3><p>{desc}</p></div>'
        for icon, title, desc in points
    )
    return f"""<section class="section" style="padding:0 48px 64px">
  <div class="section-tag">Why Book Direct</div>
  <h2 class="section-title">No Middleman, No Bidding War</h2>
  <div class="partner-grid" style="margin-top:0">{cards}</div>
</section>"""


PAGE_CSS = """<style>
.hero{padding:150px 48px 90px;max-width:1200px;margin:0 auto;display:grid;
  grid-template-columns:1.1fr .9fr;gap:60px;align-items:start}
.hero-badge{display:inline-block;background:rgba(244,88,10,.12);border:1px solid rgba(244,88,10,.3);
  border-radius:100px;padding:6px 16px;font-size:.8rem;font-weight:700;
  color:var(--orange-light);text-transform:uppercase;letter-spacing:.06em;margin-bottom:20px}
.hero h1{font-family:'Syne',sans-serif;font-size:clamp(2.2rem,4.5vw,3.6rem);
  font-weight:800;letter-spacing:-.03em;line-height:1.05;margin-bottom:20px}
.hero p{font-size:1.05rem;color:var(--text-muted);line-height:1.7;margin-bottom:28px;max-width:520px}
.trust-pills{display:flex;gap:10px;flex-wrap:wrap}
.trust-pills span{background:rgba(255,255,255,.05);border:1px solid var(--border);
  border-radius:100px;padding:6px 14px;font-size:.78rem;color:var(--text-muted)}
.quote-card{background:var(--navy-mid);border:1px solid var(--border);border-radius:20px;padding:32px}
.quote-card h2{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:4px}
.form-sub{font-size:.82rem;color:var(--text-muted);margin-bottom:24px}
.qrow{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px;margin-bottom:12px}
.section{padding:70px 48px;max-width:1200px;margin:0 auto}
.section-tag{display:inline-block;color:var(--orange);font-weight:700;font-size:.8rem;
  text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}
.section-title{font-family:'Syne',sans-serif;font-size:clamp(1.6rem,3vw,2.4rem);
  font-weight:800;letter-spacing:-.02em;margin-bottom:36px}
.svc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.svc-card{background:var(--navy-mid);border:1px solid var(--border);border-radius:16px;
  padding:24px;text-decoration:none;color:#fff;transition:border-color .2s,transform .2s}
.svc-card:hover{border-color:var(--orange);transform:translateY(-3px)}
.svc-icon{font-size:1.8rem;display:block;margin-bottom:10px}
.svc-card h3{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700}
.steps-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.step-card{background:var(--navy-mid);border:1px solid var(--border);border-radius:16px;
  padding:26px 22px;position:relative}
.step-num{position:absolute;top:18px;right:20px;font-family:'Syne',sans-serif;
  font-size:.78rem;font-weight:800;color:var(--text-muted);opacity:.5}
.step-icon{font-size:1.7rem;display:block;margin-bottom:14px}
.step-card h3{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;margin-bottom:8px}
.step-card p{color:var(--text-muted);font-size:.85rem;line-height:1.6}
@media(max-width:900px){.steps-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.steps-grid{grid-template-columns:1fr}}
.content-block{max-width:820px;margin:0 auto;padding:150px 48px 80px}
.content-block h1{font-family:'Syne',sans-serif;font-size:clamp(2rem,4vw,2.8rem);
  font-weight:800;letter-spacing:-.03em;margin-bottom:24px}
.content-block h2{font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;margin:32px 0 14px}
.content-block p{font-size:.95rem;line-height:1.8;color:rgba(255,255,255,.8);margin-bottom:16px}
.content-block ul{margin:0 0 16px 22px;color:rgba(255,255,255,.8);font-size:.95rem;line-height:1.9}
.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:48px;max-width:1100px;
  margin:0 auto;padding:150px 48px 90px}
.contact-info h1{font-family:'Syne',sans-serif;font-size:clamp(2rem,4vw,2.8rem);
  font-weight:800;letter-spacing:-.03em;margin-bottom:16px}
.contact-info p{color:var(--text-muted);line-height:1.7;margin-bottom:24px}
.contact-detail{display:flex;align-items:center;gap:12px;margin-bottom:14px;font-size:.95rem}
.thanks{max-width:600px;margin:0 auto;padding:180px 48px 120px;text-align:center}
.thanks .icon{font-size:3rem;margin-bottom:20px}
.thanks h1{font-family:'Syne',sans-serif;font-size:clamp(1.8rem,4vw,2.6rem);
  font-weight:800;letter-spacing:-.03em;margin-bottom:16px}
.thanks p{color:var(--text-muted);line-height:1.7;margin-bottom:28px}
.blog-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.blog-card{background:var(--navy-mid);border:1px solid var(--border);border-radius:16px;
  padding:28px;text-decoration:none;color:#fff;transition:border-color .2s}
.blog-card:hover{border-color:var(--orange)}
.blog-card h3{font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:700;margin-bottom:10px}
.blog-card p{color:var(--text-muted);font-size:.88rem;line-height:1.6}
.partner-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:36px}
.partner-card{background:var(--navy-mid);border:1px solid var(--border);border-radius:16px;padding:26px}
.partner-card h3{font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:700;margin-bottom:10px}
.partner-card p{color:var(--text-muted);font-size:.88rem;line-height:1.7}
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
.hero-stats{display:flex;gap:36px;margin-top:36px;padding-top:28px;border-top:1px solid var(--border)}
.hero-stat-n{display:block;font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;color:var(--orange);white-space:nowrap}
.hero-stat-l{font-size:.8rem;color:var(--text-muted)}
@media(max-width:900px){
  .hero{grid-template-columns:1fr;padding:110px 24px 50px}
  .hero-stats{gap:16px;margin-top:28px;padding-top:22px}
  .hero-stat-n{font-size:1.15rem}
  .hero-stat-l{font-size:.7rem}
  .svc-grid{grid-template-columns:repeat(2,1fr)}
  .contact-grid{grid-template-columns:1fr;padding:110px 24px 50px}
  .blog-grid{grid-template-columns:1fr}
  .partner-grid{grid-template-columns:1fr}
  .content-block,.thanks{padding-top:110px}
}
@media(max-width:420px){
  .qrow{grid-template-columns:1fr}
}
@media(min-width:901px) and (max-width:1200px){
  /* .hero is 2-column here but not wide enough for the quote-card's own
     2-column fields — text was truncating ("House Remo…", "Destinatio…").
     Stack the fields instead of shrinking the whole layout. */
  .qrow{grid-template-columns:1fr}
}
</style>"""


def page_shell(root, title, description, body, extra_css="", canonical_path="", noindex=False, jsonld=""):
    return f"""<!DOCTYPE html>
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
{seo_html(canonical_path, title, description, root, noindex=noindex)}
{jsonld}
{PAGE_CSS}
{extra_css}
</head>
<body>
{nav_html(root)}
{mobile_menu_html(root)}
<main>
{body}
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


def booking_form_html(root):
    return f"""<div class="quote-card" id="quote">
  <h2>Get an Instant Quote</h2>
  <p class="form-sub">60 seconds · Confirmed price instantly</p>
  <form action="https://formspree.io/f/{FORMSPREE_ID}" method="POST" enctype="multipart/form-data">
    <div class="qrow">
      <div class="form-group">
        <label for="f-move-type">Move Type</label>
        <select id="f-move-type" name="move_type">
          {"".join(f"<option>{name}</option>" for _, name, _ in SERVICES)}
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
        <input type="text" id="f-from-postcode" name="from_postcode" placeholder="e.g. NW1 1AA" style="font-size:16px">
      </div>
      <div class="form-group">
        <label for="f-to-postcode">To Postcode</label>
        <input type="text" id="f-to-postcode" name="to_postcode" placeholder="Destination" style="font-size:16px">
      </div>
    </div>
    {quote_contact_and_photos_html()}
    <input type="hidden" name="_subject" value="New Removal Booking — {SITE_NAME}">
    <input type="hidden" name="_next" value="{SITE_URL}/thank-you.html">
    <button type="submit" class="btn-primary" style="width:100%;margin-top:6px;text-align:center">
      Book My Removal →
    </button>
  </form>
  <p style="text-align:center;font-size:.72rem;color:var(--text-muted);margin-top:10px">
    🔒 Fully insured · No hidden fees · Nationwide coverage
  </p>
</div>"""


def build_index(dist_dir):
    root = "./"
    svc_cards = "".join(
        f'<a href="{slug}/index.html" class="svc-card">'
        f'<span class="svc-icon">{icon}</span><h3>{name}</h3></a>'
        for slug, name, icon in SERVICES
    )
    body = f"""<section class="hero">
  <div>
    <div class="hero-badge">📦 Nationwide UK Removals</div>
    <h1>Moving House Made Simple</h1>
    <p>Fully insured removal teams, instant online pricing, and a booking that
       takes 60 seconds.</p>
    <div class="trust-pills">
      <span>✓ Fully insured</span>
      <span>✓ 1,700+ locations covered</span>
      <span>✓ Instant online booking</span>
      <span>✓ Same-day available</span>
    </div>
    {hero_stats_html([("4.8★", "Average rating"), ("1,700+", "UK locations"), ("Same-Day", "Availability")])}
  </div>
  {booking_form_html(root)}
</section>
{how_it_works_html()}
{differentiation_html()}
<section class="section" style="padding:48px 48px">
  <div class="section-tag">What We Do</div>
  <h2 class="section-title">Our Services</h2>
  <div class="svc-grid">{svc_cards}</div>
</section>
<section class="section" style="padding:0 48px 64px">
  <div class="section-tag">Coverage</div>
  <h2 class="section-title" style="margin-bottom:16px">We Cover the Whole UK</h2>
  <p style="color:var(--text-muted);line-height:1.7;max-width:600px;margin-bottom:20px">
    1,700+ towns across England, Scotland, Wales and Northern Ireland —
    find yours and get a price in seconds.
  </p>
  <a href="locations.html" class="btn-primary">Browse All Locations →</a>
</section>
<section class="section" style="padding:0 48px 64px">
  <div class="section-tag">FAQs</div>
  <h2 class="section-title">Common Questions</h2>
  {faq_html(HOME_FAQS)}
</section>"""
    faqpage = jsonld_html({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in HOME_FAQS
        ],
    })
    (Path(dist_dir) / "index.html").write_text(
        page_shell(root, f"{SITE_NAME} | UK Removal Services",
                   f"{SITE_NAME} provides professional, fully insured removal services "
                   f"across the UK. Instant online booking and pricing.", body,
                   canonical_path="", jsonld=organization_jsonld() + "\n" + faqpage),
        encoding="utf-8",
    )


def build_about(dist_dir):
    root = "./"
    body = f"""<div class="content-block">
  <h1>About {SITE_NAME}</h1>
  <p>{SITE_NAME} is a nationwide removal company built to make moving house or
     office straightforward. We work with experienced, fully insured removal
     teams across the UK to deliver a consistent, reliable service — whether
     you're moving down the street or across the country.</p>
  <p>Moving is consistently ranked among the most stressful life events, and most
     of that stress comes from uncertainty — not knowing what something will cost,
     whether the team will turn up on time, or whether your belongings are covered
     if something goes wrong. We built {SITE_NAME} to remove that uncertainty:
     confirmed pricing before you book, fully insured teams as standard, and local
     coverage in over 1,700 towns and cities so there's almost always a team near
     your move.</p>
  <h2>How We Work</h2>
  <p>Every booking starts with the details of your move — property size, distance,
     and any extras like packing or storage. We match that against local team
     availability to give you a confirmed price in around 60 seconds, with no
     obligation to book. On moving day, your assigned team handles loading,
     transport and unloading, with packing, dismantling and storage available as
     add-ons for jobs that need them.</p>
  <h2>Our Promise</h2>
  <ul>
    <li>Fully insured teams on every job</li>
    <li>Transparent, upfront pricing — no hidden fees</li>
    <li>Instant online booking, confirmed within hours</li>
    <li>Coverage across 1,700+ UK towns and cities</li>
    <li>Same-day and short-notice availability in most areas</li>
  </ul>
  <h2>Get in Touch</h2>
  <p>Have a question before booking? Call us on <a href="{PHONE_HREF}" style="color:var(--orange)">{PHONE}</a>
     or visit our <a href="contact.html" style="color:var(--orange)">contact page</a>.</p>
  <p style="font-size:.85rem;color:var(--text-muted);margin-top:32px">
    {SITE_NAME} is a trading style of {LEGAL_ENTITY} (Company No. {COMPANY_NUMBER}).
  </p>
</div>"""
    (Path(dist_dir) / "about.html").write_text(
        page_shell(root, f"About Us | {SITE_NAME}",
                   f"Learn about {SITE_NAME}, a nationwide UK removal company offering "
                   f"fully insured, professional moving services.", body,
                   canonical_path="about.html"),
        encoding="utf-8",
    )


def build_contact(dist_dir):
    root = "./"
    body = f"""<section class="contact-grid">
  <div class="contact-info">
    <h1>Get in Touch</h1>
    <p>Questions about a move, a quote, or an existing booking? Our team is
       available 7 days a week.</p>
    <div class="contact-detail">📞 <a href="{PHONE_HREF}" style="color:#fff;text-decoration:none">{PHONE}</a></div>
    <div class="contact-detail">📍 Nationwide coverage across the UK</div>
    <div class="contact-detail">🕐 7 days a week</div>
  </div>
  <div class="quote-card">
    <h2>Send a Message</h2>
    <p class="form-sub">We'll get back to you within a few hours</p>
    <form action="https://formspree.io/f/{FORMSPREE_ID}" method="POST">
      <div class="form-group" style="margin-bottom:12px">
        <label for="c-name">Name</label>
        <input type="text" id="c-name" name="name" required style="font-size:16px">
      </div>
      <div class="form-group" style="margin-bottom:12px">
        <label for="c-contact">Phone or Email</label>
        <input type="text" id="c-contact" name="contact" required style="font-size:16px">
      </div>
      <div class="form-group" style="margin-bottom:12px">
        <label for="c-message">Message</label>
        <textarea id="c-message" name="message" rows="4" style="width:100%;font-size:16px;padding:10px;
          background:var(--navy-light);border:1px solid var(--border);border-radius:8px;color:#fff"></textarea>
      </div>
      <input type="hidden" name="_subject" value="New Contact Enquiry — {SITE_NAME}">
      <input type="hidden" name="_next" value="{SITE_URL}/thank-you.html">
      <button type="submit" class="btn-primary" style="width:100%;text-align:center">Send Message →</button>
    </form>
  </div>
</section>
<section class="section" style="padding:0 48px 70px">
  <div class="section-tag">FAQs</div>
  <h2 class="section-title">Before You Get in Touch</h2>
  {faq_html(CONTACT_FAQS)}
</section>"""
    (Path(dist_dir) / "contact.html").write_text(
        page_shell(root, f"Contact Us | {SITE_NAME}",
                   f"Get in touch with {SITE_NAME} for removal quotes, booking questions, "
                   f"or general enquiries.", body,
                   canonical_path="contact.html"),
        encoding="utf-8",
    )


def build_privacy(dist_dir):
    root = "./"
    body = f"""<div class="content-block">
  <h1>Privacy Policy</h1>
  <p>This policy explains how {SITE_NAME} collects, uses, and protects information
     submitted through our website. {SITE_NAME} is a trading style of
     {LEGAL_ENTITY} (Company No. {COMPANY_NUMBER}), which is the data controller
     for information collected through this site.</p>
  <h2>Information We Collect</h2>
  <p>When you request a quote or contact us, we collect the information you
     provide directly — such as your name, contact details, moving dates, and
     postcodes — via our booking and contact forms, which are processed through
     Formspree. If you upload photos of items when requesting a quote, those
     images are collected the same way, solely to help us price your move
     accurately.</p>
  <h2>How We Use It</h2>
  <p>We use this information solely to respond to your enquiry, provide a
     removal quote, and coordinate your booking. We do not sell your
     information to third parties.</p>
  <h2>Cookies &amp; Analytics</h2>
  <p>We use Google Ads conversion tracking to understand which pages lead to
     enquiries, which sets cookies in your browser. You can disable these at
     any time through your browser settings without affecting your ability to
     use the site or request a quote.</p>
  <h2>Third-Party Services</h2>
  <p>We use the following third-party services to run this site and process
     enquiries: Formspree (form submissions), Google Ads (analytics and
     conversion tracking), and WhatsApp (optional live chat, if you choose to
     message us that way). Each is bound by its own privacy policy for data it
     processes on our behalf.</p>
  <h2>Data Retention</h2>
  <p>We retain enquiry and booking information for as long as needed to
     provide our service and meet our legal and accounting obligations, after
     which it's deleted or anonymised.</p>
  <h2>Your Rights</h2>
  <p>You can ask us at any time what information we hold about you, request a
     correction, or ask us to delete it, by contacting us via the details
     below.</p>
  <h2>Changes to This Policy</h2>
  <p>We may update this policy from time to time to reflect changes to our
     services or legal requirements. The version on this page is always the
     current one.</p>
  <h2>Contact</h2>
  <p>Questions about this policy can be directed to us via our
     <a href="contact.html" style="color:var(--orange)">contact page</a>.</p>
</div>"""
    (Path(dist_dir) / "privacy.html").write_text(
        page_shell(root, f"Privacy Policy | {SITE_NAME}",
                   f"{SITE_NAME}'s privacy policy covering how customer information "
                   f"is collected and used.", body,
                   canonical_path="privacy.html"),
        encoding="utf-8",
    )


def build_thank_you(dist_dir):
    root = "./"
    body = f"""<div class="thanks">
  <div class="icon">✅</div>
  <h1>Thank You!</h1>
  <p>Your request has been received. A member of the {SITE_NAME} team will be
     in touch shortly to confirm your quote and booking details.</p>
  <a href="index.html" class="btn-primary">Back to Home</a>
</div>"""
    (Path(dist_dir) / "thank-you.html").write_text(
        page_shell(root, f"Thank You | {SITE_NAME}",
                   "Thank you for your enquiry — we'll be in touch shortly.", body,
                   canonical_path="thank-you.html", noindex=True),
        encoding="utf-8",
    )


def build_terms(dist_dir):
    root = "./"
    body = f"""<div class="content-block">
  <h1>Terms &amp; Cancellation Policy</h1>
  <p>These terms apply to every booking made with {SITE_NAME}, a trading style
     of {LEGAL_ENTITY} (Company No. {COMPANY_NUMBER}). By confirming a booking,
     you agree to the terms below.</p>
  <h2>Bookings &amp; Quotes</h2>
  <p>Quotes provided through our online form or by phone are estimates based on
     the details you give us (property size, distance, access and inventory).
     The final price is confirmed once we've reviewed your full moving details,
     and may be adjusted if the actual job differs materially from what was
     described — for example significantly more items, restricted parking, or
     lack of lift access that wasn't mentioned at quote stage. We'll always
     confirm any change with you before the work goes ahead.</p>
  <h2>Cancellations &amp; Rescheduling</h2>
  <ul>
    <li><strong>More than 7 days before your move:</strong> cancel or reschedule
        free of charge.</li>
    <li><strong>48 hours to 7 days before your move:</strong> a cancellation or
        reschedule may incur a partial charge to cover crew and vehicle
        allocation already committed to your slot.</li>
    <li><strong>Less than 48 hours before your move:</strong> cancellations may
        be charged in full, as a crew and vehicle have been reserved
        exclusively for your booking.</li>
  </ul>
  <p>If we need to cancel or reschedule a confirmed booking on our side (for
     example due to a vehicle issue or severe weather), we'll contact you as
     early as possible to arrange a new slot at no extra cost.</p>
  <h2>Payment</h2>
  <p>Payment terms are confirmed at the time of booking. Any deposit required
     to secure a date will be communicated upfront — no work begins until a
     booking is confirmed.</p>
  <h2>Insurance &amp; Liability</h2>
  <p>Every {SITE_NAME} team carries public liability and goods-in-transit
     insurance as standard. If an item is lost or damaged during your move,
     let your crew know on the day and follow up in writing within 48 hours so
     we can log and assess the claim.</p>
  <h2>Access &amp; Delays</h2>
  <p>Please let us know about parking restrictions, permit requirements, lift
     access or narrow staircases when you book. Delays caused by access
     issues not disclosed at quote stage may affect timing and cost on the
     day.</p>
  <h2>Changes to These Terms</h2>
  <p>We may update these terms from time to time. The version on this page is
     always the current one.</p>
  <h2>Questions</h2>
  <p>For anything not covered here, get in touch via our
     <a href="contact.html" style="color:var(--orange)">contact page</a> or call
     <a href="{PHONE_HREF}" style="color:var(--orange)">{PHONE}</a>.</p>
</div>"""
    (Path(dist_dir) / "terms.html").write_text(
        page_shell(root, f"Terms & Cancellation Policy | {SITE_NAME}",
                   f"{SITE_NAME}'s terms of service and cancellation policy for "
                   f"removal bookings.", body,
                   canonical_path="terms.html"),
        encoding="utf-8",
    )


def build_404(dist_dir):
    root = "./"
    body = f"""<div class="thanks">
  <div class="icon">🧭</div>
  <h1>Page Not Found</h1>
  <p>Sorry, we couldn't find that page. It may have moved, or the link might be
     out of date. Try heading back home or searching our full list of locations.</p>
  <a href="index.html" class="btn-primary" style="margin-right:10px">Back to Home</a>
  <a href="locations.html" class="btn-primary" style="background:var(--navy-light)">Browse Locations</a>
</div>"""
    (Path(dist_dir) / "404.html").write_text(
        page_shell(root, f"Page Not Found | {SITE_NAME}",
                   "The page you're looking for couldn't be found.", body,
                   canonical_path="404.html", noindex=True),
        encoding="utf-8",
    )


BLOG_POSTS = [
    (
        "how-much-do-removals-cost",
        "How Much Do Removals Cost in the UK?",
        "A breakdown of typical UK removal costs by property size and service type.",
        f"""<p>Removal costs in the UK vary widely depending on property size, distance,
     and the level of service you need. As a general guide:</p>
  <ul>
    <li><strong>Studio / 1 bed:</strong> £300 – £600</li>
    <li><strong>2 bedroom:</strong> £500 – £900</li>
    <li><strong>3 bedroom:</strong> £700 – £1,200</li>
    <li><strong>4+ bedroom:</strong> £1,000 – £2,000+</li>
  </ul>
  <p>Long-distance moves (200+ miles) typically add £200–£500 to the base cost.
     Additional services like packing, storage, or piano removal are priced
     separately — see our <a href="../../locations.html" style="color:var(--orange)">location pages</a>
     for detailed pricing in your area.</p>
  <h2>What Affects the Price?</h2>
  <p>The main factors are property size, distance travelled, access (stairs,
     parking, lift availability), and any additional services such as packing
     or temporary storage. Booking early and being flexible on moving dates can
     also help reduce cost.</p>
  <p>For an accurate, instant price, use the quote form on any
     <a href="../../index.html" style="color:var(--orange)">{SITE_NAME}</a> page.</p>""",
    ),
    (
        "moving-house-checklist",
        "The Complete Moving House Checklist",
        "Everything you need to do before, during, and after moving day.",
        f"""<p>Moving house involves a lot of moving parts. Use this checklist to stay
     organised from booking to unpacking.</p>
  <h2>4–6 Weeks Before</h2>
  <ul>
    <li>Book your removal company</li>
    <li>Declutter and decide what to keep, sell, or donate</li>
    <li>Start collecting packing materials</li>
  </ul>
  <h2>1–2 Weeks Before</h2>
  <ul>
    <li>Confirm your moving date and access arrangements</li>
    <li>Notify utility providers, banks, and change your address</li>
    <li>Pack non-essential items room by room</li>
  </ul>
  <h2>Moving Day</h2>
  <ul>
    <li>Keep essentials (documents, chargers, medication) in a separate bag</li>
    <li>Do a final walkthrough of your old property</li>
    <li>Check inventory as items are loaded and unloaded</li>
  </ul>
  <p>Ready to book? Get an instant quote on our
     <a href="../../index.html" style="color:var(--orange)">home page</a>.</p>""",
    ),
    (
        "packing-tips-for-a-stress-free-move",
        "Packing Tips for a Stress-Free House Move",
        "Room-by-room packing strategy, labelling that actually works, and when it's worth calling in professional packers.",
        f"""<p>Good packing is what separates a smooth moving day from a chaotic one.
     Most of the stress people associate with moving — breakages, missing
     items, boxes in the wrong room — comes down to how (and when) things
     were packed, not the move itself.</p>
  <h2>Start With a Room-by-Room Plan</h2>
  <p>Pack the rooms you use least first — spare rooms, lofts, garages,
     seasonal storage — and work towards the rooms you use daily. Kitchens
     and bedrooms should always be packed last, since you'll need them
     right up until moving day.</p>
  <h2>Label Everything Properly</h2>
  <p>A box marked simply "kitchen" is far more useful on moving day than one
     marked "misc". Label each box with its destination room and a rough
     idea of contents, and mark anything fragile clearly on more than one
     side of the box — it's easy to miss a single label when boxes are
     stacked.</p>
  <h2>Pack an Essentials Box — and Keep It Separate</h2>
  <p>Chargers, medication, important documents, a change of clothes, and
     basic kitchen items (kettle, mugs, teabags) should travel with you, not
     in the removal van. This one box saves more first-night stress than
     almost anything else on this list.</p>
  <h2>When to Call in the Professionals</h2>
  <p>DIY packing works well for most household items, but fragile
     collections, valuable furniture, and tight timelines are where
     professional packing genuinely pays for itself — both in time saved
     and in reduced risk of damage in transit. See our
     <a href="../../packing-services/index.html" style="color:var(--orange)">packing services</a>
     for what's included, or get an instant estimate on the
     <a href="../../index.html" style="color:var(--orange)">home page</a>.</p>""",
    ),
    (
        "moving-to-london-parking-permits-and-ulez",
        "Moving to London: Parking Permits, ULEZ and What You Need to Know",
        "Controlled parking zones, ULEZ charges, and flat access — the extra logistics that catch people out on a London move.",
        f"""<p>Moving within or into London involves a few extra considerations that
     don't come up with moves elsewhere in the country. None of them are
     complicated, but they're worth knowing about before moving day rather
     than discovering them on the morning of.</p>
  <h2>Controlled Parking Zones and Bay Suspensions</h2>
  <p>Many London boroughs operate controlled parking zones (CPZs), which
     means a removal van can't simply park outside your building without a
     permit. If your street is affected, you can usually apply to your
     local council for a temporary parking bay suspension to guarantee
     space directly outside on moving day. Councils vary in how much notice
     they need — some accept a few days, others ask for two weeks or more —
     so it's worth checking as soon as your date is confirmed.</p>
  <h2>ULEZ and the Congestion Charge</h2>
  <p>The Ultra Low Emission Zone (ULEZ) covers all London boroughs and
     charges non-compliant vehicles a daily fee to drive anywhere within
     Greater London, 24 hours a day. The separate Congestion Charge applies
     only within a smaller central London zone, on weekdays and at busier
     weekend hours. Both charges are based on the vehicle doing the driving,
     so if you're comparing removal companies, it's a fair question to ask
     whether their vehicles are ULEZ-compliant — this can affect your final
     price if it isn't factored in upfront. Rates change periodically, so
     for the current daily charge it's worth checking
     <a href="https://tfl.gov.uk" style="color:var(--orange)" rel="nofollow">Transport for London's website</a>
     directly.</p>
  <h2>Flats, Stairs and Lift Access</h2>
  <p>A large share of London properties are flats rather than houses, which
     brings its own set of access questions: is there a lift, and is it
     large enough for furniture? Does the building require advance notice
     to book a service lift or hold a door open? Flagging this when you
     book means it's factored into your quote rather than causing delays on
     the day.</p>
  <p>See typical costs and coverage for your area on our
     <a href="../../removals-within-the-m25/index.html" style="color:var(--orange)">London &amp; M25 removals page</a>,
     or get an instant estimate on the
     <a href="../../index.html" style="color:var(--orange)">home page</a>.</p>""",
    ),
    (
        "office-relocation-checklist",
        "Office Relocation Checklist: How to Move Your Business Without Downtime",
        "A practical timeline for relocating your office with minimal disruption to staff, clients, and IT systems.",
        f"""<p>An office move carries a different kind of risk than a house move —
     the cost isn't just the move itself, it's every hour your team can't
     work. A bit of planning goes a long way toward keeping disruption to a
     minimum.</p>
  <h2>6–8 Weeks Before</h2>
  <ul>
    <li>Notify staff and key clients of the move date</li>
    <li>Audit IT equipment, servers, and cabling requirements at the new site</li>
    <li>Plan the new office layout so furniture goes straight to the right desk, not into storage limbo</li>
    <li>Book your removal company, particularly if you need an evening or weekend slot</li>
  </ul>
  <h2>2 Weeks Before</h2>
  <ul>
    <li>Label equipment and furniture by department or desk number</li>
    <li>Back up all data before anything is disconnected</li>
    <li>Arrange IT disconnection and reconnection with your provider around the move dates</li>
    <li>Confirm lift bookings or loading bay access at both the old and new building</li>
  </ul>
  <h2>Moving Day</h2>
  <p>Where possible, schedule the physical move outside business hours —
     evenings or weekends cut disruption significantly for client-facing
     teams. Keep highly sensitive documents or servers under your own
     control during transit if your policies require it, and designate one
     person as the day's point of contact who isn't also packing boxes.</p>
  <h2>The Week After</h2>
  <p>Get IT and phone lines working first — everything else can follow.
     Update your address on your Google Business Profile, invoices,
     website, and with Companies House as early as possible, since these
     updates take time to propagate.</p>
  <p>See what's included in our
     <a href="../../office-removals/index.html" style="color:var(--orange)">office removals service</a>,
     or get an instant estimate on the
     <a href="../../index.html" style="color:var(--orange)">home page</a>.</p>""",
    ),
    (
        "man-and-van-vs-full-removal-service",
        "Man and Van vs Full Removal Service: Which Do You Need?",
        "A straightforward comparison to help you choose between a man and van booking and a full house removal.",
        f"""<p>Both are legitimate, commonly used options — the right one depends on
     how much you're moving, how far, and how much of the work you want to
     hand over.</p>
  <h2>When Man and Van Makes Sense</h2>
  <p>A man and van booking suits smaller loads: a studio or one-bedroom
     flat, a handful of large items, or a move that doesn't need a full
     crew. It also works well for short-notice moves, since it's typically
     quicker to book than a full removal team, and for budget-conscious
     moves where you're happy to help with some of the loading yourself.</p>
  <h2>When a Full Removal Service Makes Sense</h2>
  <p>Larger properties (three bedrooms or more), long-distance moves, and
     anything involving fragile or particularly valuable items generally
     suit a full removal service better. You get a dedicated crew handling
     loading, transport, and unloading from end to end, with no lifting
     required on your part.</p>
  <h2>Cost Comparison</h2>
  <p>Man and van bookings are usually charged by the hour, which makes them
     cost-effective for quick jobs but can add up if a bigger load takes
     longer than expected. Full removal services are typically quoted as a
     fixed price based on property size, which makes the cost more
     predictable — and, past a certain load size, often works out more
     cost-effective than paying hourly for a job that simply takes longer
     with fewer hands.</p>
  <p>Not sure which fits your move? Get an instant estimate for either
     option on our
     <a href="../../index.html" style="color:var(--orange)">home page</a>, or see full details on the
     <a href="../../man-and-van/index.html" style="color:var(--orange)">man and van service</a> page.</p>""",
    ),
    (
        "how-to-move-a-piano-safely",
        "How to Move a Piano Safely (and Why You Shouldn't DIY It)",
        "What makes pianos so difficult to move, the real risks of doing it yourself, and what professional piano removals involve.",
        f"""<p>Pianos are unlike anything else in a house move. An upright piano
     typically weighs somewhere in the region of 200–300kg, and a grand
     piano can weigh considerably more — combined with an awkward, uneven
     weight distribution that makes them genuinely dangerous to move
     without the right technique and equipment.</p>
  <h2>Why Pianos Are Different From Other Furniture</h2>
  <p>It isn't just the weight. A piano's internal mechanism — the strings,
     hammers, and soundboard — is sensitive to jolts, tilting, and changes
     in angle. It's entirely possible to damage a piano's sound and
     mechanism during a move without any visible external damage at all,
     which is why "carefully" carrying one isn't the same as moving it
     correctly.</p>
  <h2>The Real Risks of DIY Moving</h2>
  <p>The injury risk is real: a piano's weight and awkward balance make
     crush injuries and back injuries genuine possibilities, particularly
     on stairs or through doorways. Beyond personal injury, there's a real
     risk of irreparable damage to the piano itself, and to your property —
     doorframes, walls, and staircases are common casualties of DIY piano
     moves.</p>
  <h2>What Professional Piano Movers Actually Do</h2>
  <p>Specialist piano removals use purpose-built equipment — piano skids or
     boards, heavy-duty dollies, and ramps — along with lifting techniques
     designed specifically for a piano's weight distribution. Routes are
     planned before anything is lifted, and the piano is properly wrapped
     and protected throughout, not just for the journey but for the tricky
     bits: doorways, stairs, and tight turns.</p>
  <p>See what's included in our
     <a href="../../piano-removals/index.html" style="color:var(--orange)">piano removals service</a>,
     or get an instant estimate on the
     <a href="../../index.html" style="color:var(--orange)">home page</a>.</p>""",
    ),
    (
        "storage-guide-between-moves",
        "Self Storage vs Moving Straight In: A Guide for Gaps Between Moves",
        "What to consider when there's a gap between moving out and moving in, and how to decide what's worth storing.",
        f"""<p>Not every move goes straight from one front door to another. Chain
     breaks, gaps between tenancies, renovations, and downsizing all create
     situations where your belongings need somewhere to go before your new
     home is ready for them.</p>
  <h2>When You Might Need Storage</h2>
  <ul>
    <li>A gap between completing on a sale and completing on a purchase</li>
    <li>Downsizing to a smaller property and needing time to decide what to keep</li>
    <li>Renovating a new property before moving your furniture in</li>
    <li>Decluttering before putting your current home on the market</li>
  </ul>
  <h2>What to Store vs What to Let Go</h2>
  <p>A storage gap is also a natural opportunity to be honest about what
     you actually want in your next home. Seasonal items and genuinely
     sentimental pieces are usually worth storing; furniture you've been
     meaning to replace anyway often isn't. Sorting this before your items
     go into storage saves you paying to store — and later move again —
     things you were never going to unpack.</p>
  <h2>Choosing the Right Unit Size</h2>
  <p>As a rough guide: a small unit (around 25 sq ft) suits a few boxes and
     small furniture, a medium unit (around 50 sq ft) typically covers the
     contents of a one-bedroom flat, and a large unit (around 100 sq ft)
     is usually enough for a three-bedroom house. If you're unsure, it's
     worth discussing your specific inventory rather than guessing — it's
     a common (and costly) mistake to book a unit that's too small.</p>
  <p>See pricing and options on our
     <a href="../../storage/index.html" style="color:var(--orange)">storage services</a> page,
     or get an instant estimate on the
     <a href="../../index.html" style="color:var(--orange)">home page</a>.</p>""",
    ),
]


def build_blog(dist_dir):
    root = "../"
    post_cards = "".join(
        f'<a href="{slug}/index.html" class="blog-card"><h3>{title}</h3><p>{desc}</p></a>'
        for slug, title, desc, _ in BLOG_POSTS
    )
    body = f"""<div class="section" style="padding-top:150px">
  <div class="section-tag">Knowledge Hub</div>
  <h1 class="section-title">Latest Articles</h1>
  <p style="color:var(--text-muted);line-height:1.8;max-width:700px;margin:-20px 0 36px">
    Practical guides for anyone planning a move — real costs, what to expect on
    moving day, and how to avoid the most common mistakes. Written from what we
    see on the ground with {SITE_NAME} teams across the UK.
  </p>
  <div class="blog-grid">{post_cards}</div>
</div>"""
    out_dir = Path(dist_dir) / "blog"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        page_shell(root, f"Knowledge Hub | {SITE_NAME}",
                   f"Moving tips, cost guides, and checklists from {SITE_NAME}.", body,
                   canonical_path="blog/"),
        encoding="utf-8",
    )

    for slug, title, desc, content in BLOG_POSTS:
        post_root = "../../"
        post_body = f"""<div class="content-block">
  <h1>{title}</h1>
  {content}
</div>"""
        post_dir = out_dir / slug
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "index.html").write_text(
            page_shell(post_root, f"{title} | {SITE_NAME}", desc, post_body,
                       canonical_path=f"blog/{slug}/"),
            encoding="utf-8",
        )


def build_man_and_van_page(dist_dir):
    """Dedicated dist/man-and-van/index.html — unlike the other generic service
    landing pages, this one leads with on-demand / same-day / call-now framing
    rather than the templated 'Across the UK' copy."""
    root = "../"
    slug, name, icon = next(s for s in SERVICES if s[0] == "man-and-van")
    other_cards = "".join(
        f'<a href="../{s}/index.html" class="svc-card">'
        f'<span class="svc-icon">{i}</span><h3>{n}</h3></a>'
        for s, n, i in SERVICES if s != slug
    )
    steps = [
        ("📞", "Call or Book Online", "Call now for an instant slot check, or get a confirmed "
         "price online in 60 seconds — no waiting for callbacks."),
        ("✅", "We Confirm Within Minutes", "We match you with the nearest available van and "
         "driver and confirm your booking straight away."),
        ("🚐", "Van Arrives Same Day", "Most bookings — even last-minute ones — can be on the "
         "road the same day. Just tell us what you're moving."),
    ]
    steps_html = "".join(
        f'<div class="partner-card"><h3>{icon} {title}</h3><p>{desc}</p></div>'
        for icon, title, desc in steps
    )
    faqs = [
        (
            "Can I book a man and van the same day?",
            "Yes — same-day man and van hire is available in most areas, subject to "
            "driver availability. Call us directly for the fastest confirmation.",
        ),
        (
            "Do I need to book in advance, or is it on-demand?",
            "Neither is required — you can book ahead for a fixed time, or call now for "
            "on-demand hire and we'll get a van to you as quickly as possible.",
        ),
        (
            "How is man and van hire priced?",
            "By the hour, with pricing based on van size and crew — see the cost guide "
            "below. There's no minimum notice period and no hidden fees.",
        ),
        (
            "What can a man and van move?",
            "Anything from a single item or a few boxes to a full studio or small house "
            "move — furniture, appliances, flat-pack, you name it.",
        ),
    ]
    faqpage = jsonld_html({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    })

    body = f"""<section class="hero">
  <div>
    <div class="hero-badge">{icon} On-Demand Man &amp; Van</div>
    <h1>Man &amp; Van Hire — On Demand, Same Day</h1>
    <p>Need a van right now? {SITE_NAME}'s man and van service is available for
       same-day hire across the UK — no advance notice required. Call now for
       instant availability, or book online in 60 seconds.</p>
    <div class="trust-pills">
      <span>✓ Same-day hire</span>
      <span>✓ Fully insured</span>
      <span>✓ From £60</span>
      <span>✓ No job too small</span>
    </div>
    <a href="{PHONE_HREF}" class="btn-primary" style="margin-top:22px;font-size:1.05rem;padding:16px 32px;display:inline-block">
      📞 Call Now — {PHONE}
    </a>
    {hero_stats_html([("4.8★", "Average rating"), ("60 Sec", "Online booking"), ("Nationwide", "Coverage")])}
  </div>
  {booking_form_html(root)}
</section>
<section class="section">
  <div class="section-tag">How It Works</div>
  <h2 class="section-title">On-Demand Hire in 3 Steps</h2>
  <div class="partner-grid">{steps_html}</div>
</section>
<section class="section">
  <div class="section-tag">Pricing</div>
  <h2 class="section-title">Man &amp; Van Costs</h2>
  {cost_table_html(slug)}
</section>
<section class="section">
  <div class="section-tag">FAQs</div>
  <h2 class="section-title">Same-Day &amp; On-Demand Hire — FAQs</h2>
  {faq_html(faqs)}
</section>
<section class="section">
  <div class="section-tag">Coverage</div>
  <h2 class="section-title">Find Man &amp; Van Hire in Your Area</h2>
  <p style="color:var(--text-muted);line-height:1.8;max-width:700px;margin-bottom:24px">
    We cover 1,700+ towns and cities across the UK — search our full location list
    to find same-day man and van hire near you.
  </p>
  <a href="{root}locations.html" class="btn-primary">Browse All Locations →</a>
</section>
<section class="section">
  <div class="section-tag">Other Services</div>
  <h2 class="section-title">You Might Also Need</h2>
  <div class="svc-grid">{other_cards}</div>
</section>"""

    title = "Man & Van Hire | On-Demand & Same Day | RemovalsNation"
    description = (
        f"On-demand man and van hire across the UK. Same-day availability, fully "
        f"insured, from £60. Call now or book online in 60 seconds with {SITE_NAME}."
    )
    out_dir = Path(dist_dir) / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        page_shell(root, title, description, body,
                   canonical_path=f"{slug}/", jsonld=faqpage),
        encoding="utf-8",
    )
    print("✅  Man & Van on-demand page built")


def build_service_pages(dist_dir):
    """Build dist/{service_slug}/index.html — the generic (non-location) service landing page.
    man-and-van is handled separately by build_man_and_van_page() with dedicated
    on-demand/same-day/call-now content instead of this generic template."""
    root = "../"
    for slug, name, icon in SERVICES:
        if slug == "man-and-van":
            continue
        other_cards = "".join(
            f'<a href="../{s}/index.html" class="svc-card">'
            f'<span class="svc-icon">{i}</span><h3>{n}</h3></a>'
            for s, n, i in SERVICES if s != slug
        )
        body = f"""<section class="hero">
  <div>
    <div class="hero-badge">{icon} {name}</div>
    <h1>{name} Across the UK</h1>
    <p>{SITE_NAME} provides professional, fully insured {name.lower()} nationwide.
       Find your location below or get an instant quote now.</p>
    <div class="trust-pills">
      <span>✓ Fully insured</span>
      <span>✓ Instant booking</span>
      <span>✓ Nationwide coverage</span>
    </div>
    {hero_stats_html([("4.8★", "Average rating"), ("1,700+", "UK locations"), ("Fully", "Insured teams")])}
  </div>
  {booking_form_html(root)}
</section>
<section class="section">
  <div class="section-tag">Pricing</div>
  <h2 class="section-title">{name} Costs</h2>
  {cost_table_html(slug)}
</section>
<section class="section">
  <div class="section-tag">Coverage</div>
  <h2 class="section-title">Find {name} in Your Area</h2>
  <p style="color:var(--text-muted);line-height:1.8;max-width:700px;margin-bottom:24px">
    We cover 1,700+ towns and cities across the UK — search our full location list
    to find {name.lower()} near you.
  </p>
  <a href="{root}locations.html" class="btn-primary">Browse All Locations →</a>
</section>
<section class="section">
  <div class="section-tag">Other Services</div>
  <h2 class="section-title">You Might Also Need</h2>
  <div class="svc-grid">{other_cards}</div>
</section>"""
        out_dir = Path(dist_dir) / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(
            page_shell(root, f"{name} | {SITE_NAME}",
                       f"Professional, fully insured {name.lower()} across the UK. "
                       f"Instant online pricing and booking with {SITE_NAME}.", body,
                       canonical_path=f"{slug}/"),
            encoding="utf-8",
        )
    print(f"✅  {len(SERVICES) - 1} service landing pages built")


def build_m25_page(dist_dir, locations):
    """Pillar page targeting 'removals within the M25' / 'London removal company' —
    the page that should rank for those terms, linking out to every Greater
    London, Surrey, Hertfordshire, Essex and Kent location page (also gives
    those ~354 pages extra internal-link equity beyond the flat locations.html
    directory)."""
    from collections import defaultdict

    root = "../"
    regions = defaultdict(list)
    for name, region, county, postcode, slug in locations:
        if region in M25_REGIONS:
            regions[region].append((name, slug))

    total = sum(len(v) for v in regions.values())
    sections = ""
    for region in M25_REGIONS:
        if region not in regions:
            continue
        links = "".join(
            f'<a href="{root}house-removals/{slug}/index.html" class="loc-link">{name}</a>'
            for name, slug in sorted(regions[region])
        )
        sections += f"""
<div class="region-section">
  <h3 class="region-title">{region}</h3>
  <div class="loc-grid">{links}</div>
</div>"""

    faqs = [
        (
            "Do you cover removals within the whole M25?",
            f"Yes — {SITE_NAME} covers every London borough plus the surrounding "
            f"Surrey, Hertfordshire, Essex and Kent commuter belt inside and just "
            f"outside the M25, with {total}+ locations served in the area.",
        ),
        (
            "Are you a London removal company or do you cover further afield too?",
            f"We're a nationwide removal company, but London and the M25 corridor "
            f"is one of our busiest coverage areas — with fully insured local teams "
            f"who know the area, parking restrictions and access requirements.",
        ),
        (
            "How much do removals within the M25 cost?",
            "Pricing depends on property size and distance — typically £300–£2,000+ "
            "for a house move. Pick your town below for location-specific pricing, "
            "or use the quote form for an instant estimate.",
        ),
        (
            "Can you handle same-day or short-notice London moves?",
            "Yes, same-day removals are available across most of the M25 area "
            "subject to team availability — call us directly to check your postcode.",
        ),
    ]

    body = f"""<section class="hero">
  <div>
    <div class="hero-badge">🚐 M25 Removal Specialists</div>
    <h1>Removals Within the M25</h1>
    <p>{SITE_NAME} is a trusted London removal company providing fully insured
       removals within the M25 — covering every London borough plus Surrey,
       Hertfordshire, Essex and Kent. Instant online pricing, {total}+ local
       towns covered.</p>
    <div class="trust-pills">
      <span>✓ Fully insured</span>
      <span>✓ {total}+ M25-area locations</span>
      <span>✓ Local London teams</span>
      <span>✓ Same-day available</span>
    </div>
    {hero_stats_html([("4.8★", "Average rating"), (f"{total}+", "M25 locations"), ("Same-Day", "Availability")])}
  </div>
  {booking_form_html(root)}
</section>
{how_it_works_html()}
{differentiation_html()}
<section class="section">
  <div class="section-tag">Why RemovalsNation</div>
  <h2 class="section-title">Your London Removal Company</h2>
  <p style="color:var(--text-muted);line-height:1.8;max-width:800px;margin-bottom:14px">
    Moving within the M25 comes with its own challenges — narrow streets, permit
    parking, lift access in flats, and tight scheduling around London traffic.
    As a dedicated London removal company, {SITE_NAME}'s teams handle removals
    within the M25 every day, from small flat moves in zone 1 to full house
    removals out to the Surrey, Hertfordshire, Essex and Kent commuter belt.
  </p>
  <p style="color:var(--text-muted);line-height:1.8;max-width:800px">
    Every removal within the M25 is fully insured and comes with instant online
    pricing — pick your area below to see local costs, or get a quote in 60
    seconds using the form above.
  </p>
</section>
<section class="section" style="padding:0 48px 64px">
  <div class="section-tag">Pricing</div>
  <h2 class="section-title">Removals Within the M25 — Typical Costs</h2>
  <p style="color:var(--text-muted);line-height:1.7;max-width:700px;margin-bottom:24px;margin-top:-20px">
    Guide prices for a house removal within the M25. Exact pricing depends on
    property size, distance and access (stairs, parking, lift availability) —
    get an instant quote above for your exact move.
  </p>
  {cost_table_html("house-removals")}
</section>
<section class="section">
  <div class="section-tag">Coverage</div>
  <h2 class="section-title">Find Your Area Within the M25</h2>
  {sections}
</section>
<section class="section">
  <div class="section-tag">FAQs</div>
  <h2 class="section-title">Removals Within the M25 — FAQs</h2>
  {faq_html(faqs)}
</section>"""

    title = "Removals Within the M25 | London Removal Company"
    description = (
        f"{SITE_NAME} — a trusted London removal company providing fully insured "
        f"removals within the M25. {total}+ locations across London, Surrey, "
        f"Herts, Essex & Kent."
    )
    breadcrumb = jsonld_html({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Removals Within the M25",
             "item": f"{SITE_URL}/removals-within-the-m25/"},
        ],
    })
    faqpage = jsonld_html({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    })

    extra_css = """<style>
.region-section{margin-bottom:48px}
.region-title{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:var(--orange);margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border)}
.loc-grid{display:flex;flex-wrap:wrap;gap:8px}
.loc-link{background:var(--navy-mid);border:1px solid var(--border);border-radius:8px;padding:7px 14px;text-decoration:none;color:rgba(255,255,255,.8);font-size:.83rem;transition:all .2s}
.loc-link:hover{border-color:var(--orange);color:#fff;background:rgba(244,88,10,.08)}
</style>"""

    out_dir = Path(dist_dir) / "removals-within-the-m25"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        page_shell(root, title, description, body, extra_css=extra_css,
                   canonical_path="removals-within-the-m25/",
                   jsonld=breadcrumb + "\n" + faqpage),
        encoding="utf-8",
    )
    print(f"✅  M25 pillar page built ({total} locations linked)")


def build_partner(dist_dir):
    root = "../"
    body = f"""<div class="section" style="padding-top:150px">
  <div class="section-tag">For Businesses</div>
  <h1 class="section-title">Partner With {SITE_NAME}</h1>
  <p style="color:var(--text-muted);line-height:1.8;max-width:700px;margin-bottom:10px">
     Estate agents, letting agents, and relocation businesses — refer your
     clients to {SITE_NAME} and we'll handle their move end-to-end, fully
     insured and nationwide.
  </p>
  <p style="color:var(--text-muted);line-height:1.8;max-width:700px">
     Whether it's a single referral or a steady stream of tenants and buyers
     needing a removal quote, we handle the whole process directly with your
     client — booking, pricing, and communication — so it takes no extra work
     off your end. Corporate and repeat-referral partners get a dedicated
     account contact rather than the standard booking line.
  </p>
  <div class="partner-grid">
    <div class="partner-card">
      <h3>🤝 Referral Partners</h3>
      <p>Send us your clients and we'll manage bookings, pricing, and
         communication directly with them. No commission structure to manage,
         no extra admin on your side.</p>
    </div>
    <div class="partner-card">
      <h3>🏢 Corporate Accounts</h3>
      <p>Managing multiple office relocations or a steady flow of tenant moves?
         We offer dedicated account support and consistent pricing for
         corporate clients.</p>
    </div>
    <div class="partner-card">
      <h3>📞 Get Started</h3>
      <p>Call us on {PHONE} or use our <a href="../contact.html" style="color:var(--orange)">contact form</a>
         to discuss a partnership — most set-ups take one short call.</p>
    </div>
  </div>
</div>"""
    out_dir = Path(dist_dir) / "partner-with-us"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        page_shell(root, f"Partner With Us | {SITE_NAME}",
                   f"Estate agents and businesses — partner with {SITE_NAME} for "
                   f"nationwide removal services for your clients.", body,
                   canonical_path="partner-with-us/"),
        encoding="utf-8",
    )


def main():
    import json

    parser = argparse.ArgumentParser(description="Build RemovalsNation static top-level pages")
    parser.add_argument("--dist", default="dist", help="Output directory (default: dist)")
    parser.add_argument("--data", default="data/locations.json", help="Path to locations JSON")
    args = parser.parse_args()

    Path(args.dist).mkdir(parents=True, exist_ok=True)

    with open(args.data) as f:
        locations = json.load(f)

    build_index(args.dist)
    build_about(args.dist)
    build_contact(args.dist)
    build_privacy(args.dist)
    build_terms(args.dist)
    build_thank_you(args.dist)
    build_404(args.dist)
    build_blog(args.dist)
    build_service_pages(args.dist)
    build_man_and_van_page(args.dist)
    build_m25_page(args.dist, locations)
    build_partner(args.dist)

    print(f"✅  Static pages built: index, about, contact, privacy, thank-you, 404, blog (+{len(BLOG_POSTS)} posts), "
          "service landing pages, M25 pillar page, partner-with-us")


if __name__ == "__main__":
    main()
