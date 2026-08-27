# Yoak Properties &amp; Construction Co. — website

Static site for **www.yoakproperties.com**. No framework, no build step required to
serve it: every file in the repository root is the deployed site exactly as it ships.

| | |
|---|---|
| Host | GitHub Pages, served from the repository root |
| Custom domain | `www.yoakproperties.com` (see [DNS](#dns-cutover)) |
| Pages | `index.html`, `properties.html`, `faq.html`, `about.html`, `privacy.html`, `terms.html`, `404.html` |
| Listings | generated from `data/listings.json` &mdash; **edit that, not `properties.html`** |
| Third-party runtime requests | **none** — fonts, icons, CSS, JS and images are all local |
| Total weight, home page | ~330 KB first visit, ~30 KB on repeat visits |

---

## Before this goes live — open items

Two of these are blockers. The rest are improvements.

### 1. Resident portal link — BLOCKER, needs a URL

`PORTAL_URL` in `tools/transform.py` is **deliberately empty**. While it is
empty, the Tenant Portal button is omitted from the header, the mobile menu and
the footer, and the build prints a reminder. The site currently contains **no
reference to a resident portal anywhere** — that was an explicit decision, not
an oversight.

Do not paste the AppFolio *staff* login (`account.appfolio.com/realms/...`).
That is the employee account picker, and the URL carries a session-specific
`state` token. The resident portal is a per-company subdomain, typically
`https://<company>.appfolio.com/connect`, found under **Settings → Online
Portal** in AppFolio.

The old Buildium portal (`yoakproperties.managebuilding.com`) must never be
linked — Yoak has migrated off it. The build fails if that hostname reappears.

When you are ready to advertise the portal: set `PORTAL_URL`, then restore the
"Online Portal" service cards on the home and about pages and the rent-payment
line on the FAQ page. All three live in `strip_portal()` and `tools/faq.py`.

### 2. Zillow destination — needs a URL

`APPLY_URL` points at the leasing Linktree (`linktr.ee/derekanders`) because no
Yoak Zillow *profile* URL was available. It is used by "See all current
listings" and "Apply on Zillow". Individual listing cards do not depend on it —
they build a per-address Zillow lookup from `ZILLOW_ADDR`.

### 3. Legal pages have not been reviewed by counsel

`privacy.html` and `terms.html` came from the mockups and have been edited:

- **Terms section 2, "Tenant Portal & Accounts", was removed** and sections 3–5
  renumbered to 2–4. It described a first-party portal as a service of this
  website, which is not accurate and is not being advertised yet.
- **Three privacy sections were written from scratch** — "Data Sharing &
  Disclosure", "Your Rights" and "Contact Us". The mockup listed all three in
  its contents but never wrote them, so they were dead links. The drafts
  describe how Yoak actually operates (screening via Zillow, work orders to
  contractors, reporting to owners) and cover FCRA adverse-action rights. **They
  are a reasonable starting point, not legal advice.**
- **"Last Updated" is 27 August 2026**, the first-publication date. The mockups
  said October 2024, which would assert a history these documents do not have.

### 4. Listing data goes stale — but the page no longer lies about it

`data/listings.json` was populated on 27 August 2026 from the six per-agent
documents on the leasing Linktree. Two of those six (Aaron's and Trent's) were
*already* advertising open houses that had passed.

The page handles this in two places, so a past date is never shown as upcoming:

- **At build time**, any open house before today renders as "Open house times on
  Zillow" instead of a date.
- **In the browser**, `assets/js/site.js` re-checks against the visitor's own
  clock and does the same swap for anything that expired since the last build.
  Home-page teaser cards are removed outright, and the whole "Next open houses"
  section hides itself if all three expire.

`tools/test-expiry.mjs` proves this by fast-forwarding the browser clock. Run it
after touching the listings or the JS.

Still worth doing: **Ashley's and Derek's Stark County listings are missing** —
their documents were not linked on the Linktree. And longer term this should
pull from AppFolio rather than being maintained by hand.

### 5. Photographs are representative, not per-address

The 13 photographs are genuine Yoak interiors and exteriors taken from the
current Wix site, but there is no record of which unit each one shows. So
listing cards carry **no photograph at all** — with 13 images and 29 listings,
any mapping would repeat photos across different addresses and imply each was of
that house. The real interiors appear once, in a gallery labelled as
representative. Add per-address photos and the card layout can gain an image.

### 6. Entity name differs between the branding and the payee line — left as-is

The site brand is "Yoak Properties & Construction **Co.**", which matches the
Ohio registration ("YOAK PROPERTIES AND CONSTRUCTION CO."). The FAQ tells
applicants to make payments out to "Yoak Properties and Construction **LLC**",
taken verbatim from Yoak's own FAQ document.

**This is intentional and needs no action from IT.** A payee line has to match
whatever the bank expects, and that is an ownership and finance call, not a
website one. Noted here only so nobody "fixes" the inconsistency later without
asking Steve or Kipp first.

### 7. Google reviews link

Uses a Maps *search* URL that resolves to the office. The place-ID review link
would open the "write a review" dialog directly.

## Deploying

### First time

1. **Settings → Pages → Build and deployment**
   - Source: *Deploy from a branch*
   - Branch: `main`, folder: `/ (root)`
2. Wait for the green check. Because `CNAME` is present, Pages will immediately
   claim `www.yoakproperties.com` — so until DNS is switched, the
   `YoakPropertiesAdmin.github.io/yoakproperties` URL will redirect to a domain
   that still points at Wix.
   **To preview before cutting over, delete `CNAME`, push, look at the
   `github.io` URL, then add `CNAME` back.** Every internal link is relative, so
   the site works correctly at either address.
3. Tick **Enforce HTTPS** once the certificate is issued (can take ~15 minutes
   after DNS propagates).

### DNS cutover

The domain is on Wix today. Nothing on GitHub's side breaks while that is true.
When ready, at the registrar:

| Record | Name | Value |
|---|---|---|
| CNAME | `www` | `YoakPropertiesAdmin.github.io` |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

The four A records let the bare `yoakproperties.com` redirect to `www`. Remove the
old Wix records for the same names. Allow up to 48 hours, though it is usually
minutes. **Keep the Wix site paid up until the new one resolves and looks right** —
that is the rollback.

### Every time after

Edit, commit, push to `main`. Pages redeploys in about a minute.

---

## Editing content

**Listings live in `data/listings.json`.** That is the only file to touch when
inventory changes:

```json
{ "address": "168 Roswell St", "city": "Akron", "state": "OH", "zip": null,
  "beds": 4, "baths": 2, "rent": null,
  "openHouse": "2026-08-29T10:00", "openHouseEnd": "10:30", "note": null }
```

`openHouse` is local Eastern time. Set it to `null` when there is no scheduled
open house — the card then links to Zillow for times. `note` renders as a badge
("Lease to purchase only", "Private tours only"). Adding an agent is a new entry
in the `agents` array; the page, the home-page teaser and the open-house count
all follow automatically.

Most other copy lives directly in the page HTML — open the file, change the words.

Anything that appears on **more than one page** is generated, and editing the HTML
by hand will be overwritten on the next build. That includes the header, the
footer, the address, the phone number, and every page's `<title>` and meta tags.
Those live at the top of `tools/transform.py`:

```python
STREET     = '1361 Wooster Road W, Suite A'
CITY_LINE  = 'Barberton, OH 44203'
PHONE_TEXT = '330-794-7156'
EMAIL      = 'info@yoakproperties.com'
PORTAL_URL = ''                                  # empty = no portal link anywhere
APPLY_URL  = 'https://linktr.ee/derekanders'
```

Change one, rebuild, and it updates on all six pages at once.

### Rebuilding

```bash
cd tools && npm install && cd ..
python3 tools/transform.py     # -> the seven page files
npm --prefix tools run css     # recompile assets/css/site.css
node tools/verify.mjs          # render every page and check it
node tools/test-expiry.mjs     # fast-forward the clock, check dates expire
```

`transform.py` fails loudly if a page still contains a placeholder link, a dead
image URL, the wrong zip code, an icon name left as text, **any mention of a
portal**, or the old Buildium hostname.

`verify.mjs` loads all six pages at 1440px and 390px in headless Chromium and
fails on: broken images, horizontal overflow, links that go nowhere, buttons
with no behaviour, a page without exactly one `<h1>`, any 4xx response, a
console error, **a past open house still on the page**, or a `<template>`
rendering visibly. It also opens and closes the mobile menu. Screenshots land in
`shots/`. **Run both before pushing.**

---

## How this repository is laid out

```
index.html  properties.html  faq.html      the deployed pages
about.html  privacy.html  terms.html  404.html
data/listings.json                           inventory: the one file to edit
assets/css/site.css                          compiled Tailwind, minified
assets/js/site.js                            mobile menu, open-house expiry, TOC highlight
assets/fonts/                                7 text faces + a 3 KB icon subset
assets/img/                                  photographs, logo, favicons, OG image
CNAME  robots.txt  sitemap.xml  .nojekyll    hosting metadata
tools/                                       build tooling, not served
tools/src/                                   the original design mockups
tools/properties.py  tools/faq.py            page generators
```

`.nojekyll` stops GitHub from running the files through Jekyll, which would
otherwise ignore any future directory beginning with an underscore.

---

## What changed from the mockups, and why

The five files in `tools/src/` are the original Claude Design exports. They looked
right in a screenshot but were not a working website. For the record:

**Would have been broken on arrival**

- Every internal link was an unresolved `{{DATA:SCREEN:SCREEN_n}}` token, so no
  page reached any other page.
- One header link pointed at `C:\Users\eganj\OneDrive\Desktop\...` — a path on
  one specific laptop.
- All 13 hero and card images pointed at temporary `lh3.googleusercontent.com`
  URLs. Those are already dead; every image on the site would have been a broken
  icon. They are now local files in `assets/img/`.
- **On a phone there was no navigation at all.** The menu button had no panel
  behind it and the site shipped no JavaScript. Since most rental search traffic
  is mobile, this alone made the site unusable for the majority of visitors.
- The hero's "View Listings" and "Learn More", the "Tenant Portal" control, and
  "View All Listings" were `<button>` elements with no handler — they looked
  clickable and did nothing. All are now links.
- Two "Interested in a private tour?" links were `href="#"`.
- `rounded-DEFAULT` was used in several places. Tailwind emits that key as
  `rounded`, so those corners were silently square.

**Wrong facts**

- The Barberton office zip was `44302` on four of the five pages. `44302` is
  Akron; the office is `44203`. Confirmed against the LoopNet and Zillow listings
  for 1361 Wooster Rd W and the chamber of commerce record for the phone number.
- Copyright read 2024.
- The properties page advertised open houses on dates in June and July.

**Things that were not true**

- Three tenant testimonials attributed to invented people.
- The home page showed "$950/mo", "$1,100/mo" and "$850/mo" against *cities*
  rather than units, with "Available" and "Newly Renovated" badges. Those cards
  are now what they always were — area descriptions — and link to the listings
  page.
- An agent headshot generated for a real named employee. Replaced with a monogram.
- A drawn "map illustration" of Barberton. Replaced with a link that opens the
  real office location in Google Maps.

**Made faster and more robust**

- Tailwind was loaded from `cdn.tailwindcss.com`, which compiles CSS in the
  visitor's browser and which Tailwind documents as not for production. Replaced
  with 32 KB of precompiled CSS.
- Icons came from Google's Material Symbols variable font, about 4 MB, and were
  addressed *by ligature* — the element's text was the literal string
  `real_estate_agent`. When that font is slow or blocked, the visitor reads icon
  names as words all over the page. They now come from a **3 KB local subset**
  containing only the 29 glyphs this site uses, addressed by codepoint, so a
  failed load renders nothing instead of gibberish.
- Montserrat and Inter are self-hosted (156 KB for all 8 faces), so the site
  makes no third-party requests at all. It renders identically on networks that
  block Google Fonts, and nothing about visitors is shared with a third party.
- Images are sized, `loading="lazy"` below the fold, and the hero is
  `fetchpriority="high"`.

**Added in the second pass**

- **A "How to Apply" page** built from Yoak's own FAQ document, which until now
  sat in a Google Doc behind a link tree — invisible to prospective tenants and
  to search engines. It covers qualifying criteria, the voucher policy, the
  application fee and timeline, the deposit process, and lease-to-purchase
  terms. These are the questions the office answers on the phone all day.
- **A "Next open houses" strip on the home page**, so a visitor can see whether
  anything is actually being shown this week without clicking through.
- **Listings moved out of HTML into `data/listings.json`**, and populated with
  real current inventory for six agents pulled from the leasing documents.
- **Open houses now expire by themselves**, at build time and again in the
  browser. This is the difference between a page that is out of date and a page
  that is wrong.
- **All portal language removed** — the button, the service cards on the home
  and about pages, the FAQ rent-payment line, a Terms section, and a stale
  privacy contents entry.
- **Three missing privacy sections written**, replacing three dead anchors.
- **HTML comments stripped** from output; one of them was `<!-- Portal Card -->`.

**Accessibility and SEO**

- Every icon is `aria-hidden`. Screen readers were previously announcing
  "real_estate_agent" and "support_agent" as content.
- Added a skip link, visible keyboard focus rings, `aria-expanded` /
  `aria-controls` on the menu button, `aria-current` on the active nav item, and
  a `prefers-reduced-motion` block.
- Every image has real alt text describing the photograph. The mockups had put
  the image-generation prompt in a `data-alt` attribute and left `alt` empty.
- Added per-page titles and meta descriptions, canonical URLs, Open Graph and
  Twitter card tags, favicons, `RealEstateAgent` structured data with the
  corrected address, `sitemap.xml`, and `robots.txt`.
- Added an Equal Housing Opportunity notice to the footer.
- Nav order and footer contents differed on all five pages; both are now
  generated once.

---

## Contact details, in one place

| | |
|---|---|
| Office | 1361 Wooster Road W, Suite A, Barberton, OH 44203 |
| Phone | 330-794-7156 |
| Email | info@yoakproperties.com |
| Resident portal | AppFolio &mdash; URL still needed, see open item 1. The old Buildium portal is dead and must not be linked. |
