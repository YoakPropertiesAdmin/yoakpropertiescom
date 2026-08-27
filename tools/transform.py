#!/usr/bin/env python3
"""
Yoak Properties — build script.

Takes the five Claude Design mockup exports in src/ and produces a
deployable static site in site/.

What it fixes, and why:
  * {{DATA:SCREEN:SCREEN_n}} placeholder hrefs never resolved to anything.
  * One href pointed at C:\\Users\\eganj\\... on Joshua's desktop.
  * Every hero / card image pointed at temporary lh3.googleusercontent.com
    URLs that are already dead. Swapped for local files in assets/img.
  * The mobile menu button had no panel and no JS: phones had no nav.
  * The Tenant Portal control was a <button>, so it did nothing.
  * Nav order and footer contents differed on all five pages.
  * Barberton zip was 44302 (that's Akron); correct is 44203.
  * Copyright read 2024.
  * rounded-DEFAULT is not a class Tailwind emits, so those corners were square.
  * Icon <span>s were read aloud by screen readers as "real_estate_agent".
  * Home page showed invented rents and invented tenant testimonials.
  * Properties page advertised open houses that happened in June and July.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Paths are derived from this script's own location so the documented command
# works from the repository root ("python3 tools/transform.py"): sources in
# tools/src, output alongside them in the repo root. The two env vars let a
# different layout drive the same code, which is how this is developed.
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('YOAK_SRC') or os.path.join(HERE, 'src')
OUT = os.environ.get('YOAK_OUT') or os.path.dirname(HERE)

# --------------------------------------------------------------------------
# Single source of truth for every fact that appears on more than one page.
# --------------------------------------------------------------------------
BRAND       = 'Yoak Properties &amp; Construction Co.'
BRAND_SHORT = 'Yoak Properties'
SITE_URL    = 'https://www.yoakproperties.com'
STREET      = '1361 Wooster Road W, Suite A'
CITY_LINE   = 'Barberton, OH 44203'
ADDRESS     = f'{STREET}, {CITY_LINE}'
PHONE_TEXT  = '330-794-7156'
PHONE_HREF  = 'tel:+13307947156'
EMAIL       = 'info@yoakproperties.com'
YEAR        = '2026'
LEGAL_DATE  = 'August 27, 2026'

# Resident portal: DELIBERATELY NONE. Yoak has decided the public site does
# not advertise a resident portal, so there is no Tenant Portal button and no
# copy anywhere that points at one. strip_portal() removes the surrounding
# text, and main() fails the build if the word "portal" or the old Buildium
# hostname reappears in a page.
#
# Tenants who need to pay rent or raise a repair contact the office; the
# number and address are in the header, footer and on the About page.
#
# If that decision is ever reversed, setting this to the AppFolio resident
# portal URL restores the button, and the removals in strip_portal() and
# tools/faq.py are what need undoing.
PORTAL_URL  = ''

# Applications go through Zillow: "All prospective tenants must apply through
# Zillow" (Yoak FAQ). There is no Yoak Zillow profile URL on hand, so this
# points at the public leasing hub that links each agent's current listings.
# TODO(Joshua): replace with the Yoak Zillow profile URL when available.
APPLY_URL   = 'https://linktr.ee/derekanders'

# Per-address Zillow lookup. Lands on the property's own Zillow page, and
# degrades to a Zillow search if the address slug does not resolve.
ZILLOW_ADDR = 'https://www.zillow.com/homes/{slug}_rb/'

APP_FEE     = '$35 per applicant'
BUILD_TODAY = '2026-08-27'
BUILD_DATE_TEXT = '27 August 2026'

# Google Maps search that resolves to the office listing. Swap for the
# place-ID review link if you want the "write a review" dialog to open.
MAPS_URL    = ('https://www.google.com/maps/search/?api=1&amp;query='
               'Yoak+Properties+and+Construction+1361+Wooster+Rd+W+Barberton+OH+44203')
REVIEWS_URL = MAPS_URL

PAGES = [
    # src stem,      output,             nav key,      title, description
    ('home', 'index.html', 'home',
     f'{BRAND_SHORT} | Affordable Rental Homes in Akron, Canton &amp; Barberton, OH',
     'Affordable, well-managed rental homes across Akron, Canton, Barberton, '
     'Massillon and the surrounding Ohio communities, with on-staff maintenance '
     'and responsive tenant support.'),
    ('about', 'about.html', 'about',
     f'About Us | {BRAND_SHORT}',
     'Yoak Properties &amp; Construction Co. provides affordable, quality housing '
     'and expert property management across Summit and Stark County, Ohio.'),
    ('properties', 'properties.html', 'properties',
     f'Our Properties | {BRAND_SHORT}',
     'Browse rental homes managed by Yoak Properties in Akron, Barberton and '
     'the surrounding areas. Current open house times and applications are on Zillow.'),
    ('privacy', 'privacy.html', None,
     f'Privacy Policy | {BRAND_SHORT}',
     'How Yoak Properties &amp; Construction Co. collects, uses and protects '
     'applicant and tenant information.'),
    ('terms', 'terms.html', None,
     f'Terms of Service | {BRAND_SHORT}',
     'Terms governing use of the Yoak Properties website and the rental '
     'application process.'),
    ('faq', 'faq.html', 'faq',
     f'How to Apply | {BRAND_SHORT}',
     'Qualifying criteria, application fees, voucher policy, open house process and '
     'lease-to-purchase terms for Yoak Properties rentals in Akron, Canton and Barberton.'),
    ('404', '404.html', None,
     f'Page Not Found | {BRAND_SHORT}',
     'That page could not be found. Browse current Yoak Properties rentals instead.'),
]

NAV = [('home', 'Home', 'index.html'),
       ('properties', 'Our Properties', 'properties.html'),
       ('faq', 'How to Apply', 'faq.html'),
       ('about', 'About Us', 'about.html')]


# --------------------------------------------------------------------------
# Inline SVGs. Used for the few icons that must render before the icon font
# arrives (the hamburger) or that carry meaning on their own.
# --------------------------------------------------------------------------
SVG_MENU = ('<svg data-icon="open" class="w-6 h-6" fill="none" viewBox="0 0 24 24" '
            'stroke="currentColor" stroke-width="2" aria-hidden="true">'
            '<path stroke-linecap="round" stroke-linejoin="round" d="M4 7h16M4 12h16M4 17h16"/></svg>')
SVG_CLOSE = ('<svg data-icon="close" class="w-6 h-6 hidden" fill="none" viewBox="0 0 24 24" '
             'stroke="currentColor" stroke-width="2" aria-hidden="true">'
             '<path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M18 6L6 18"/></svg>')


def header(active):
    """Canonical sticky header with a working mobile panel."""
    def links(mobile):
        out = []
        for key, label, href in NAV:
            on = (key == active)
            if mobile:
                cls = ('block px-margin-mobile py-4 font-label-bold text-label-bold border-b '
                       'border-outline-variant/20 ' +
                       ('text-heritage-gold font-bold' if on
                        else 'text-deep-navy hover:bg-surface-container-low'))
            else:
                cls = ('font-label-bold text-label-bold transition-colors ' +
                       ('text-heritage-gold font-bold border-b-2 border-heritage-gold pb-1' if on
                        else 'text-slate-gray hover:text-deep-navy'))
            cur = ' aria-current="page"' if on else ''
            out.append(f'<a class="{cls}" href="{href}"{cur}>{label}</a>')
        return '\n'.join(out)

    portal_desktop = (
        f'<div class="hidden md:flex shrink-0">'
        f'<a class="bg-deep-navy text-surface-off-white px-6 py-2 rounded font-label-bold '
        f'text-label-bold hover:bg-primary-container transition-colors" href="{PORTAL_URL}" '
        f'rel="noopener" target="_blank">Tenant Portal</a></div>'
    ) if PORTAL_URL else ''
    portal_mobile = (
        f'\n<a class="block px-margin-mobile py-4 font-label-bold text-label-bold '
        f'text-heritage-gold" href="{PORTAL_URL}" rel="noopener" target="_blank">'
        f'Tenant Portal &#8599;</a>'
    ) if PORTAL_URL else ''

    return f'''<a class="skip-link" href="#main">Skip to main content</a>
<header class="bg-surface-off-white/95 backdrop-blur-md sticky top-0 z-50 border-b border-outline-variant/30 shadow-sm">
<div class="flex justify-between items-center gap-4 w-full px-margin-mobile md:px-gutter max-w-container-max mx-auto h-20">
<a class="flex items-center gap-3 shrink-0 hover:opacity-80 transition-opacity" href="index.html">
<img alt="" class="w-10 h-10 rounded object-cover shrink-0" height="40" src="assets/img/logo-yoak.png" width="40"/>
<span class="font-headline-md text-headline-md font-bold text-deep-navy tracking-tight leading-none">{BRAND_SHORT}</span>
</a>
<nav aria-label="Main navigation" class="hidden md:flex items-center gap-8">
{links(False)}
</nav>
{portal_desktop}
<button aria-controls="mobile-nav" aria-expanded="false" aria-label="Open menu" class="md:hidden text-deep-navy p-2 -mr-2 hover:bg-surface-container-low rounded-lg transition-colors" id="nav-toggle" type="button">
{SVG_MENU}{SVG_CLOSE}
</button>
</div>
<div class="md:hidden hidden border-t border-outline-variant/30 bg-surface-off-white shadow-lg" id="mobile-nav">
<nav aria-label="Mobile navigation" class="flex flex-col">
{links(True)}{portal_mobile}
</nav>
</div>
</header>'''


FOOTER_PORTAL = (f'\n<a class="hover:text-heritage-gold transition-colors" href="{PORTAL_URL}"'
                 f' rel="noopener" target="_blank">Tenant Portal</a>') if PORTAL_URL else ''

FOOTER = f'''<footer class="bg-deep-navy text-surface-off-white border-t border-slate-gray/20 mt-auto">
<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-gutter px-margin-mobile md:px-gutter py-section-gap-mobile md:py-16 max-w-container-max mx-auto">
<div class="space-y-4">
<div class="font-headline-md text-headline-md text-heritage-gold">{BRAND_SHORT}</div>
<p class="font-body-md text-body-md text-surface-variant/80 max-w-xs">Affordable homes for families. Expert property management and quality construction across Northeast Ohio.</p>
</div>
<div class="space-y-3">
<h2 class="font-label-bold text-label-bold uppercase text-heritage-gold">Contact</h2>
<address class="not-italic font-body-md text-body-md text-surface-variant/80 space-y-2">
<a class="block hover:text-heritage-gold transition-colors" href="{MAPS_URL}" rel="noopener" target="_blank">{STREET}<br/>{CITY_LINE}</a>
<a class="block hover:text-heritage-gold transition-colors" href="{PHONE_HREF}">{PHONE_TEXT}</a>
<a class="block hover:text-heritage-gold transition-colors" href="mailto:{EMAIL}">{EMAIL}</a>
</address>
</div>
<div class="space-y-3">
<h2 class="font-label-bold text-label-bold uppercase text-heritage-gold">Quick Links</h2>
<nav aria-label="Footer navigation" class="flex flex-col gap-2 font-body-md text-body-md text-surface-variant/80">
<a class="hover:text-heritage-gold transition-colors" href="index.html">Home</a>
<a class="hover:text-heritage-gold transition-colors" href="properties.html">Our Properties</a>
<a class="hover:text-heritage-gold transition-colors" href="about.html">About Us</a>
<a class="hover:text-heritage-gold transition-colors" href="faq.html">How to Apply</a>
<a class="hover:text-heritage-gold transition-colors" href="about.html#contact">Contact Us</a>{FOOTER_PORTAL}
</nav>
</div>
<div class="space-y-3">
<h2 class="font-label-bold text-label-bold uppercase text-heritage-gold">Legal</h2>
<nav aria-label="Legal navigation" class="flex flex-col gap-2 font-body-md text-body-md text-surface-variant/80">
<a class="hover:text-heritage-gold transition-colors" href="privacy.html">Privacy Policy</a>
<a class="hover:text-heritage-gold transition-colors" href="terms.html">Terms of Service</a>
</nav>
<p class="font-caption text-caption text-surface-variant/60 pt-2">Equal Housing Opportunity.<br/>We do not discriminate on the basis of race, color, religion, sex, disability, familial status or national origin.</p>
</div>
</div>
<div class="px-margin-mobile md:px-gutter py-6 max-w-container-max mx-auto border-t border-slate-gray/20">
<p class="font-caption text-caption text-surface-variant/60">&#169; {YEAR} {BRAND} All rights reserved.</p>
</div>
</footer>'''


def head(title, desc, canonical, page_key):
    og_type = 'website'
    jsonld = ''
    if page_key == 'home':
        jsonld = f'''
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "RealEstateAgent",
  "name": "Yoak Properties and Construction Co.",
  "url": "{SITE_URL}",
  "image": "{SITE_URL}/assets/img/og-banner.jpg",
  "logo": "{SITE_URL}/assets/img/logo-yoak.png",
  "telephone": "+1-330-794-7156",
  "email": "{EMAIL}",
  "address": {{
    "@type": "PostalAddress",
    "streetAddress": "1361 Wooster Road W, Suite A",
    "addressLocality": "Barberton",
    "addressRegion": "OH",
    "postalCode": "44203",
    "addressCountry": "US"
  }},
  "areaServed": [
    {{"@type": "City", "name": "Akron"}},
    {{"@type": "City", "name": "Canton"}},
    {{"@type": "City", "name": "Barberton"}},
    {{"@type": "City", "name": "Massillon"}}
  ]
}}
</script>'''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{title}</title>
<meta content="{desc}" name="description"/>
<link href="{SITE_URL}/{canonical}" rel="canonical"/>
<meta content="{og_type}" property="og:type"/>
<meta content="{title}" property="og:title"/>
<meta content="{desc}" property="og:description"/>
<meta content="{SITE_URL}/{canonical}" property="og:url"/>
<meta content="{SITE_URL}/assets/img/og-banner.jpg" property="og:image"/>
<meta content="{BRAND_SHORT}" property="og:site_name"/>
<meta content="summary_large_image" name="twitter:card"/>
<meta content="#0F172A" name="theme-color"/>
<link href="assets/img/favicon-32.png" rel="icon" sizes="32x32" type="image/png"/>
<link href="assets/img/favicon-64.png" rel="icon" sizes="64x64" type="image/png"/>
<link href="assets/img/apple-touch-icon.png" rel="apple-touch-icon"/>
<link as="font" crossorigin href="assets/fonts/inter-latin-400-normal.woff2" rel="preload" type="font/woff2"/>
<link as="font" crossorigin href="assets/fonts/montserrat-latin-700-normal.woff2" rel="preload" type="font/woff2"/>
<link as="font" crossorigin href="assets/fonts/yoak-icons.woff2" rel="preload" type="font/woff2"/>
<link href="assets/css/site.css" rel="stylesheet"/>{jsonld}
</head>'''


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def read(stem):
    with open(os.path.join(SRC, stem + '.html'), encoding='utf-8') as f:
        return f.read()


def grab_main(html):
    m = re.search(r'(?s)<main\b[^>]*>(.*)</main>', html)
    if not m:
        sys.exit('no <main> found')
    return m.group(1)


def split_sections(main):
    """Split into top-level <section> blocks, tracking nesting depth."""
    parts, i = [], 0
    for m in re.finditer(r'<(/?)section\b[^>]*>', main):
        pass
    depth, start = 0, None
    for m in re.finditer(r'<(/?)section\b[^>]*>', main):
        if not m.group(1):
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                parts.append(main[start:m.end()])
                start = None
    return parts


def img(src, alt, cls, eager=False, w=None, h=None):
    load = ('fetchpriority="high" loading="eager"' if eager
            else 'decoding="async" loading="lazy"')
    dims = f' height="{h}" width="{w}"' if w else ''
    return f'<img alt="{alt}" class="{cls}" {load} src="{src}"{dims}/>'


# --------------------------------------------------------------------------
# global cleanups applied to every page's <main>
# --------------------------------------------------------------------------
SCREEN_MAP = {
    'SCREEN_2': 'index.html',
    'SCREEN_9': 'properties.html',
    'SCREEN_10': 'about.html',
    'SCREEN_6': 'privacy.html',
    'SCREEN_8': 'terms.html',
}


ICON_CP = json.load(open(os.path.join(HERE, 'icons.json'), encoding='utf-8'))


def icons_to_entities(html):
    """Address icons by codepoint, not by ligature name.

    The mockups wrote the icon name as the element's text ("real_estate_agent").
    If the icon font fails to load, that name is what the visitor reads. Using
    the codepoint means a failed load renders nothing at all.
    """
    unknown = set()

    def sub(m):
        name = m.group(2)
        cp = ICON_CP.get(name)
        if cp is None:
            unknown.add(name)
            return m.group(0)
        return f'{m.group(1)}&#x{cp:X};{m.group(3)}'

    html = re.sub(r'(<span[^>]*material-symbols-outlined[^>]*>)\s*([a-z_0-9]+)\s*(</span>)',
                  sub, html)
    if unknown:
        print('  !! unmapped icons:', sorted(unknown))
    return html


def clean(html):
    for k, v in SCREEN_MAP.items():
        html = html.replace('{{DATA:SCREEN:' + k + '}}', v)
    # the stray absolute path to Joshua's desktop
    html = re.sub(r'href="[A-Za-z]:\\\\?[^"]*"', 'href="index.html"', html)
    html = re.sub(r'href="[A-Za-z]:\\[^"]*"', 'href="index.html"', html)
    # Tailwind never emits `rounded-DEFAULT`; `rounded` is the DEFAULT key.
    html = re.sub(r'\brounded-DEFAULT\b', 'rounded', html)
    # leftovers from the design tool that mean nothing in CSS
    html = re.sub(r'\b(docked|full-width)\b\s*', '', html)
    # wrong zip: 44302 is Akron, the office is in Barberton 44203
    html = html.replace('OH 44302', 'OH 44203').replace('44302', '44203')
    html = html.replace('&copy; 2024', f'&copy; {YEAR}').replace('© 2024', f'© {YEAR}')
    # icon spans are decorative; stop screen readers reading "real_estate_agent"
    html = re.sub(r'<span class="([^"]*material-symbols-outlined[^"]*)"(?![^>]*aria-hidden)',
                  r'<span aria-hidden="true" class="\1"', html)
    # phone numbers should be tappable
    html = html.replace('href="tel:330-794-7156"', f'href="{PHONE_HREF}"')
    # external links need rel=noopener
    html = re.sub(r'<a ([^>]*href="https?://(?!www\.yoakproperties)[^"]*")((?![^>]*rel=)[^>]*)>',
                  r'<a \1 rel="noopener" target="_blank"\2>', html)
    html = html.replace('fill-icon', '')
    # design-tool comments ("<!-- Portal Card -->", "<!-- Smaller Card 1 -->")
    # are noise in a shipped page, and one of them named a feature we are not
    # advertising yet
    html = re.sub(r'<!--(?!\[if).*?-->', '', html, flags=re.S)
    html = icons_to_entities(html)
    return html


# --------------------------------------------------------------------------
# Portal language
# --------------------------------------------------------------------------
# The resident portal is not being advertised on the public site yet, so no page
# may direct a visitor to one. PORTAL_URL being empty removes the button; this
# removes the surrounding copy, including a whole Terms section that described a
# portal as a service of this website. Section numbering is closed up after the
# removal so the document does not skip from 1 to 3.
def strip_portal(html, page):
    if page == 'home':
        html = html.replace(
            'Online Portal',
            'Simple Applications').replace(
            'Convenient online portal for quick access to important services.',
            'One $35 application on Zillow covers every property we manage for '
            '30 days. <a class="underline hover:no-underline" href="faq.html">'
            'See the requirements</a>.')
        html = html.replace('&#xE30A;', '&#xE85D;')          # computer -> assignment

    if page == 'about':
        html = html.replace(
            'Online Portal',
            'Select Homes Offered Lease to Purchase').replace(
            'Convenient online portal for quick access to important services and payments.',
            'Helping to build your credit toward home buying.')
        html = html.replace('&#xE1B1;', '&#xEA09;')          # devices -> home_work

    if page == 'privacy':
        # The contents list linked to a "#tenant-portal" section that the mockup
        # never actually contained, so this was a dead anchor as well.
        html = re.sub(r'<a\b[^>]*href="#tenant-portal"[^>]*>.*?</a>', '', html, flags=re.S)

    if page == 'terms':
        html = html.replace(
            'By accessing our website, using our Tenant Portal, or submitting a '
            'rental application,',
            'By accessing our website or submitting a rental application,')
        html = html.replace(
            'that will affect the functionality of the Tenant Portal.',
            'that will affect the functionality of this website.')
        # drop the section and its contents entry
        html = re.sub(r'<a\b[^>]*href="#tenant-portal"[^>]*>.*?</a>', '', html, flags=re.S)
        html = re.sub(r'<section id="tenant-portal">.*?</section>', '', html, flags=re.S)
        # close up the numbering: 3,4,5 -> 2,3,4
        for old, new in ((3, 2), (4, 3), (5, 4)):
            html = html.replace(f'{old}. Rental Applications', f'{new}. Rental Applications')
            html = html.replace(f'{old}. Prohibited Activities', f'{new}. Prohibited Activities')
            html = html.replace(f'{old}. Limitation of Liability', f'{new}. Limitation of Liability')

    return html


def strip_dates(html):
    """Remove past open-house dates and times from listing copy."""
    # e.g. "Open House is Thursday, June 25th 5:00-5:30 PM"
    html = re.sub(r'\s*Open [Hh]ouse is [A-Z][a-z]+day,\s*[A-Z][a-z]+\s*\d+(st|nd|rd|th)?'
                  r'\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M', '', html)
    # e.g. "Open House Tue, Jun 16, 6:00-6:15 PM"
    html = re.sub(r'\s*Open House\s+[A-Z][a-z]{2},\s*[A-Z][a-z]{2}\s*\d+,\s*'
                  r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M', '', html)
    # e.g. "Mon, July 20th • 5:00 - 5:30 PM"  /  "Mon, July 20th"
    html = re.sub(r'\s*[A-Z][a-z]{2},\s*[A-Z][a-z]+\s*\d+(st|nd|rd|th)?'
                  r'(\s*(&#8226;|•|\|)\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M)?', '', html)
    html = re.sub(r'\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M', '', html)
    return html


# ==========================================================================
# HOME
# ==========================================================================
CARD = ('bg-surface-container-lowest rounded-xl shadow-card overflow-hidden group '
        'hover:-translate-y-2 hover:shadow-card-hover transition-all duration-300 '
        'border-b border-transparent hover:border-heritage-gold flex flex-col')

AREAS = [
    ('Canton &amp; Massillon', 'area-canton.jpg',
     'Front exterior of a renovated two-storey Yoak Properties rental home',
     'Modern, affordable single-family homes and duplexes in Canton, Massillon '
     'and the surrounding Stark County communities.'),
    ('Akron', 'area-akron.jpg',
     'Front exterior of a single-storey Yoak Properties rental home',
     'Comfortable rentals across Akron, close to schools, transit and everyday '
     'amenities, all managed by our in-house team.'),
    ('Barberton', 'area-massillon.jpg',
     'Front porch and exterior of a Yoak Properties rental home',
     'Our home base. Barberton and the surrounding Summit County neighbourhoods, '
     'with maintenance crews minutes away.'),
]


def home_hero():
    return f'''<section class="relative min-h-[80vh] flex items-center justify-center px-margin-mobile md:px-gutter py-section-gap-mobile md:py-section-gap-desktop bg-deep-navy">
<div class="absolute inset-0 z-0">
{img('assets/img/hero-home.jpg',
     'A renovated two-storey family home managed by Yoak Properties',
     'w-full h-full object-cover', eager=True, w=1600, h=900)}
<div class="absolute inset-0 bg-deep-navy/75"></div>
</div>
<div class="relative z-10 max-w-container-max mx-auto grid grid-cols-1 md:grid-cols-12 gap-gutter w-full">
<div class="col-span-1 md:col-span-8 lg:col-span-7 flex flex-col justify-center space-y-6">
<h1 class="font-headline-xl text-headline-lg-mobile md:text-headline-xl text-surface-off-white text-balance drop-shadow-sm">
Affordable Homes <br/><span class="text-heritage-gold">for Families</span>
</h1>
<p class="font-body-lg text-body-lg text-surface-container-low max-w-2xl text-balance">
Expertly managed rentals in Akron, Canton, Barberton, Massillon and the surrounding areas, with on-staff maintenance crews and a leasing team that answers the phone.
</p>
<div class="flex flex-wrap gap-4 pt-4">
<a class="bg-heritage-gold text-deep-navy px-8 py-3 rounded hover:-translate-y-1 hover:shadow-lg transition-all font-label-bold text-label-bold" href="properties.html">View Listings</a>
<a class="bg-transparent border-2 border-surface-off-white text-surface-off-white px-8 py-3 rounded hover:bg-surface-off-white/10 transition-colors font-label-bold text-label-bold" href="about.html">Learn More</a>
</div>
</div>
</div>
</section>'''


def home_areas():
    cards = []
    for name, f, alt, body in AREAS:
        cards.append(f'''<article class="{CARD}">
<a class="relative h-64 overflow-hidden bg-surface-dim block" href="properties.html">
{img('assets/img/' + f, alt,
     'w-full h-full object-cover group-hover:scale-105 transition-transform duration-700',
     w=800, h=600)}
</a>
<div class="p-6 flex flex-col flex-grow">
<h3 class="font-headline-md text-headline-md text-deep-navy mb-2">{name}</h3>
<p class="font-body-md text-body-md text-slate-gray mb-6 flex-grow">{body}</p>
<div class="pt-4 border-t border-surface-container-highest">
<a class="text-heritage-gold font-label-bold text-label-bold hover:underline inline-flex items-center gap-1" href="properties.html">View homes in this area <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_forward</span></a>
</div>
</div>
</article>''')
    return f'''<section class="px-margin-mobile md:px-gutter py-section-gap-mobile md:py-section-gap-desktop bg-surface-bright">
<div class="max-w-container-max mx-auto">
<div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-4">
<div>
<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-deep-navy mb-2">Where We Manage</h2>
<p class="font-body-md text-body-md text-slate-gray max-w-2xl">Quality rental homes across Summit and Stark County. Availability changes weekly, so the properties page is always the current list.</p>
</div>
<a class="text-heritage-gold font-label-bold text-label-bold flex items-center gap-1 hover:opacity-80 transition-opacity shrink-0" href="properties.html">
View All Listings <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_forward</span>
</a>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
{''.join(cards)}
</div>
</div>
</section>'''


def home_reviews():
    """Real Google reviews, from data/reviews.json.

    Replaces the three invented testimonials the mockup shipped. Falls back to a
    link to the Google profile when the file holds no usable reviews, so the page
    never carries filler.
    """
    import reviews
    html, n = reviews.build(CFG)
    global REVIEW_COUNT
    REVIEW_COUNT = n
    return html


def home_open_houses():
    """Surface real upcoming open houses on the landing page.

    A prospective renter arriving at the home page previously had to click
    through to find out whether anything was actually being shown this week.
    """
    import properties
    items = properties.upcoming_listings(CFG, BUILD_TODAY, limit=3)
    if not items:
        return ''
    rows = []
    for l in items:
        zurl = ZILLOW_ADDR.format(slug=properties.addr_slug(l))
        when = properties.fmt_open_house(l['openHouse'], l.get('openHouseEnd'))
        bb = []
        if l.get('beds') is not None:
            bb.append(f'{properties.num(l["beds"])} bed')
        if l.get('baths') is not None:
            bb.append(f'{properties.num(l["baths"])} bath')
        meta = ' &middot; '.join(bb)
        meta = f'<p class="font-caption text-caption text-slate-gray mb-3">{meta}</p>' if meta else ''
        rows.append(
            f'<a class="group block bg-surface-container-lowest rounded-xl p-6 shadow-card '
            f'border border-outline-variant/20 hover:shadow-card-hover '
            f'hover:border-b-heritage-gold transition-all duration-300" href="{zurl}" '
            f'rel="noopener" target="_blank" data-openhouse-remove="{l["openHouse"]}">'
            f'<h3 class="font-headline-md text-headline-md text-deep-navy leading-snug mb-1">'
            f'{l["address"]}</h3>'
            f'<p class="font-body-md text-body-md text-slate-gray mb-3">{l["city"]}, '
            f'{l["state"]}</p>{meta}'
            f'<p class="font-body-md text-body-md text-deep-navy flex items-start gap-2">'
            f'<span aria-hidden="true" class="material-symbols-outlined text-[19px] '
            f'text-heritage-gold shrink-0 mt-0.5">event</span><span>{when}</span></p>'
            f'<span class="mt-4 inline-flex items-center gap-1 font-label-bold '
            f'text-label-bold text-heritage-gold group-hover:underline">View on Zillow '
            f'<span aria-hidden="true" class="material-symbols-outlined text-[15px]">'
            f'arrow_outward</span></span></a>')

    return f'''<section class="px-margin-mobile md:px-gutter py-section-gap-mobile md:py-24 bg-soft-gold">
<div class="max-w-container-max mx-auto">
<div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-10 gap-4">
<div>
<p class="font-label-bold text-label-bold uppercase text-secondary mb-2">Coming up</p>
<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-deep-navy mb-2">Next open houses</h2>
<p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">No appointment needed &mdash; just turn up. Times are confirmed on each Zillow listing.</p>
</div>
<a class="text-secondary font-label-bold text-label-bold flex items-center gap-1 hover:underline shrink-0" href="properties.html">All properties &amp; open houses <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_forward</span></a>
</div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-gutter" data-openhouse-group>{''.join(rows)}</div>
</div>
</section>'''


def build_home():
    secs = split_sections(grab_main(read('home')))
    offer = clean(secs[2])          # "What We Offer" — keep as designed
    body = ('<main id="main">'
            + home_hero() + home_open_houses() + home_areas() + offer + home_reviews()
            + '</main>')
    return body


# ==========================================================================
# ABOUT
# ==========================================================================
def build_about():
    main = clean(grab_main(read('about')))

    # hero photo
    main = re.sub(
        r'<img[^>]*src="https://lh3\.googleusercontent\.com/aida-public/AB6AXuBdgR9q[^"]*"[^>]*>',
        img('assets/img/about-hero.jpg',
            'A renovated kitchen in a Yoak Properties rental home',
            'w-full h-[400px] object-cover', eager=True, w=1200, h=600),
        main)

    # The second image was a made-up "map illustration" of Barberton. A real
    # link to the office on Google Maps is more use to a visitor than a drawing.
    main = re.sub(
        r'<img[^>]*src="https://lh3\.googleusercontent\.com/aida-public/AB6AXuDUS113[^"]*"[^>]*>',
        f'''<a class="group flex flex-col items-center justify-center text-center w-full h-full min-h-[18rem] bg-soft-gold text-deep-navy p-8 gap-3 hover:bg-secondary-fixed/40 transition-colors" href="{MAPS_URL}" rel="noopener" target="_blank">
<span aria-hidden="true" class="material-symbols-outlined text-heritage-gold" style="font-size:56px">location_on</span>
<span class="font-headline-md text-headline-md">Visit the office</span>
<span class="font-body-md text-body-md text-on-surface-variant">{STREET}<br/>{CITY_LINE}</span>
<span class="font-label-bold text-label-bold text-secondary inline-flex items-center gap-1 mt-2 group-hover:underline">Get directions <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_outward</span></span>
</a>''',
        main)

    # footer link points at about.html#contact, so give the section that id
    main = main.replace('id="contact-section"', 'id="contact"')
    main = main.replace('href="#contact-section"', 'href="#contact"')

    # dead buttons -> real links
    main = re.sub(r'<button([^>]*)>\s*Explore Our Services\s*</button>',
                  r'<a\1 href="#services">Explore Our Services</a>', main)
    main = re.sub(r'<button([^>]*)>\s*View Our Listings\s*</button>',
                  r'<a\1 href="properties.html">View Our Listings</a>', main)
    return f'<main id="main">{main}</main>'


# ==========================================================================
# PROPERTIES / FAQ — delegated to build/properties.py and build/faq.py
# ==========================================================================
REVIEW_COUNT = 0

CFG = dict(OUT=OUT, ZILLOW_ADDR=ZILLOW_ADDR, APPLY_URL=APPLY_URL, APP_FEE=APP_FEE,
           REVIEWS_URL=REVIEWS_URL, MAPS_URL=MAPS_URL,
           BUILD_DATE_TEXT=BUILD_DATE_TEXT, PHONE_HREF=PHONE_HREF,
           PHONE_TEXT=PHONE_TEXT, EMAIL=EMAIL, PORTAL_URL=PORTAL_URL)


def build_properties():
    import properties
    return properties.build(CFG, img, BUILD_TODAY)


def build_faq():
    import faq
    return faq.build(CFG)


# ==========================================================================
# LEGAL PAGES
# ==========================================================================
# --------------------------------------------------------------------------
# Privacy policy: the three sections the mockup listed but never wrote
# --------------------------------------------------------------------------
# The contents list linked to "Data Sharing & Disclosure", "Your Rights" and
# "Contact Us". None of those sections existed, so all three were dead links -
# and they are the sections a reader actually looks for. Drafted to match how
# Yoak operates (screening through Zillow, work orders to contractors,
# reporting to owners). NOT reviewed by counsel: see README.
PRIVACY_ICON = ('<div class="w-10 h-10 rounded bg-soft-gold flex items-center justify-center">'
                '<span aria-hidden="true" class="material-symbols-outlined '
                'text-on-secondary-container">{icon}</span></div>')


def privacy_section(sid, icon, title, body):
    return ('\n<div class="scroll-mt-28" id="' + sid + '">'
            '<div class="flex items-center gap-4 mb-6">'
            + PRIVACY_ICON.format(icon=icon) +
            '<h2 class="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile '
            'md:text-headline-lg text-deep-navy">' + title + '</h2></div>'
            '<div class="prose max-w-none text-on-surface-variant font-body-md '
            'text-body-md space-y-4">' + body + '</div></div>')


def _card(h, p):
    return ('<div class="p-6 bg-surface-off-white border border-outline-variant/30 '
            'rounded-lg shadow-card"><h4 class="font-label-bold text-label-bold '
            'text-deep-navy mb-2">' + h + '</h4><p class="text-slate-gray text-sm">'
            + p + '</p></div>')


PRIVACY_EXTRA = (
    privacy_section(
        'data-sharing', 'domain', 'Data Sharing &amp; Disclosure',
        '<p>We do not sell your personal information, and we do not share it for '
        'advertising. We disclose it only where doing so is necessary to run the '
        'tenancy:</p>'
        '<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">'
        + _card('Tenant screening',
                'Applications are submitted and screened through Zillow, whose own '
                'privacy terms govern that process. Screening providers supply us '
                'with credit, background and rental history reports.')
        + _card('Property owners',
                'We report on applications, tenancy status and payment history to '
                'the owner of the property you are applying for or renting.')
        + _card('Contractors and maintenance staff',
                'Work orders are shared with our own crews and trusted contractors, '
                'including the contact and access details needed to carry out the '
                'repair.')
        + _card('Service providers',
                'Our property management software provider, payment processors and '
                'professional advisers process data on our behalf under contract.')
        + '</div>'
        '<p class="mt-6">We may also disclose information where we are required to '
        'by law or by a court order, or in connection with the sale or transfer of '
        'a property.</p>'),
    privacy_section(
        'your-rights', 'security', 'Your Rights',
        '<p>You can ask to see the personal information we hold about you, and ask '
        'us to correct it if it is wrong or out of date. Write to us using the '
        'details below and we will respond within a reasonable period.</p>'
        '<p>If an application is denied on the basis of a screening report, federal '
        'law gives you the right to be told, to obtain a free copy of that report '
        'from the agency that produced it, and to dispute anything in it that is '
        'inaccurate. The adverse action notice you receive names the agency and '
        'explains how to reach them.</p>'
        '<p>We keep applicant and tenant records only for as long as we need them '
        'for the tenancy, for our legitimate business purposes, and to meet legal '
        'and tax retention requirements.</p>'
        '<p>Yoak Properties &amp; Construction Co. is an Equal Housing Opportunity '
        'provider, and screening criteria are applied uniformly to every '
        'applicant.</p>'),
    privacy_section(
        'contact', 'mail', 'Contact Us',
        '<p>For any question about this policy, or to make a request about your '
        'personal information, contact us:</p>'
        '<address class="not-italic space-y-1 mt-4">'
        '<span class="block">' + STREET + '</span>'
        '<span class="block">' + CITY_LINE + '</span>'
        '<a class="block text-secondary font-semibold hover:underline" href="'
        + PHONE_HREF + '">' + PHONE_TEXT + '</a>'
        '<a class="block text-secondary font-semibold hover:underline" href="mailto:'
        + EMAIL + '">' + EMAIL + '</a></address>'),
)


def build_legal(stem):
    main = clean(grab_main(read(stem)))
    if stem == 'privacy':
        # the content column closes with </div></div></div></div></section>;
        # insert before the innermost close so the sections land inside it
        marker = '</div>\n</div>\n</div>\n</div>\n</section>'
        if marker in main:
            main = main.replace(marker, ''.join(PRIVACY_EXTRA) + '\n' + marker, 1)
        else:
            print('  !! privacy: could not locate content column close')
    # These documents have never been published; dating them 2024 would claim a
    # history they do not have. Set to first-publication date.
    main = re.sub(r'Last Updated:\s*[A-Z][a-z]+\s+\d{1,2},\s*\d{4}',
                  f'Last Updated: {LEGAL_DATE}', main)
    main = re.sub(r'<button([^>]*)>\s*Contact Us\s*</button>',
                  r'<a\1 href="about.html#contact">Contact Us</a>', main)
    # tag the sidebar table of contents so site.js can highlight it
    main = re.sub(r'(<(?:nav|div|ul)[^>]*>)(\s*(?:<[^>]+>\s*)?(?:Contents))',
                  r'\1\2', main)
    cls = ('flex-grow pt-12 pb-section-gap-desktop' if stem == 'terms' else 'w-full')
    return f'<main class="{cls}" id="main">{main}</main>'


# ==========================================================================
# 404 — GitHub Pages serves this for any unknown path
# ==========================================================================
def build_404():
    return f'''<main class="flex-grow flex items-center justify-center px-margin-mobile md:px-gutter py-section-gap-mobile md:py-section-gap-desktop" id="main">
<div class="max-w-2xl text-center">
<p class="font-label-bold text-label-bold uppercase text-heritage-gold mb-4">Error 404</p>
<h1 class="font-headline-xl text-headline-lg-mobile md:text-headline-xl text-deep-navy mb-4">We could not find that page</h1>
<p class="font-body-lg text-body-lg text-slate-gray mb-10">The link may be out of date, or the page may have moved. Here is where most visitors are heading.</p>
<div class="flex flex-wrap gap-4 justify-center">
<a class="bg-deep-navy text-surface-off-white px-8 py-3 rounded font-label-bold text-label-bold hover:bg-primary-container transition-colors" href="/properties.html">Browse our properties</a>
<a class="bg-transparent border border-heritage-gold text-deep-navy px-8 py-3 rounded font-label-bold text-label-bold hover:bg-heritage-gold/10 transition-colors" href="/">Back to the home page</a>
</div>
<p class="font-body-md text-body-md text-slate-gray mt-10">Looking for something specific? Call us on <a class="text-deep-navy font-bold hover:text-heritage-gold" href="{PHONE_HREF}">{PHONE_TEXT}</a>.</p>
</div>
</main>'''


# ==========================================================================
# assemble
# ==========================================================================
BUILDERS = {'home': build_home, 'about': build_about, 'properties': build_properties,
            'privacy': lambda: build_legal('privacy'), 'terms': lambda: build_legal('terms'),
            'faq': build_faq, '404': build_404}

BODY_CLASS = ('bg-surface-off-white text-on-background font-body-md antialiased '
              'min-h-screen flex flex-col selection:bg-heritage-gold/30 selection:text-deep-navy')


def main():
    os.makedirs(OUT, exist_ok=True)
    for stem, outname, navkey, title, desc in PAGES:
        body = BUILDERS[stem]()
        page = (head(title, desc, outname, stem) + '\n'
                + f'<body class="{BODY_CLASS}">\n'
                + header(navkey) + '\n'
                + body + '\n'
                + FOOTER + '\n'
                + '<script src="assets/js/site.js" defer></script>\n'
                + '</body>\n</html>\n')
        page = strip_portal(page, stem)
        page = icons_to_entities(page)
        if outname == '404.html':
            page = page.replace('href="assets/', 'href="/assets/')
            page = page.replace('src="assets/', 'src="/assets/')
            page = re.sub(r'href="(index|about|properties|privacy|terms|faq)\.html"',
                          r'href="/\1.html"', page)
            page = page.replace('href="about.html#contact"', 'href="/about.html#contact"')
        with open(os.path.join(OUT, outname), 'w', encoding='utf-8') as f:
            f.write(page)
        print(f'  wrote {outname:18s} {len(page)//1024}KB')

    if REVIEW_COUNT:
        print(f'  -- {REVIEW_COUNT} review(s) rendered on the home page')
    else:
        print('  -- no usable reviews in data/reviews.json, so the home page links'
              ' to Google instead. Add entries to show the widget.')

    if not PORTAL_URL:
        print('  -- no resident portal, by decision. The build rejects any page that'
              ' mentions one.')

    leftovers = 0
    for _, outname, *_ in PAGES:
        s = open(os.path.join(OUT, outname), encoding='utf-8').read()
        stray = re.findall(r'material-symbols-outlined[^>]*>\s*([a-z][a-z_0-9]{2,})\s*<', s)
        if stray:
            print(f'  !! {outname}: icon names left as text {sorted(set(stray))}')
            leftovers += len(stray)
        for bad, label in [('DATA:SCREEN', 'screen placeholder'),
                           ('lh3.googleusercontent', 'dead image URL'),
                           ('cdn.tailwindcss.com', 'tailwind CDN'),
                           ('C:\\', 'windows path'),
                           ('44302', 'wrong zip'),
                           ('rounded-DEFAULT', 'bad radius class'),
                           ('2024 Yoak', 'stale copyright'),
                           ('portal', 'portal reference'),
                           ('Portal', 'portal reference'),
                           ('managebuilding.com', 'old Buildium portal link')]:
            n = s.count(bad)
            if n:
                print(f'  !! {outname}: {n}x {label}')
                leftovers += n
    print('  leftovers:', leftovers)
    return 0 if leftovers == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
