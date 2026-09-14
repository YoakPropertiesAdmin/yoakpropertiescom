#!/usr/bin/env python3
"""Regenerate data/listings.json from the per-agent docs on the leasing Linktree.

Run by .github/workflows/refresh-listings.yml every Friday morning. Writes:

  data/listings.json   the site's source of truth
  refresh-report.md    a human-readable summary + everything it was unsure about

The design rule here is that this script NEVER silently drops or guesses a
listing. Anything it cannot read confidently still lands in listings.json with
the ambiguous field left null, and gets a line in refresh-report.md so a human
sees it in the pull request. A parser that quietly omits a house is worse than
one that says "I could not read this."

Addresses come from the Zillow URL in each row, not the prose, because the URL
is machine-written and the prose is not. Where a row has no Zillow link there is
nothing authoritative to parse, so the address is taken verbatim and flagged.

Standard library only, so the workflow needs no pip install.
"""

import datetime
import json
import os
import re
import sys
import urllib.request

# --------------------------------------------------------------------------
# Agents. Doc IDs come from linktr.ee/derekanders. Phone and area are not in
# the docs, so they live here. Adding an agent = adding a line.
# --------------------------------------------------------------------------

AGENTS = [
    ("Aaliyah", "Akron Area Specialist",      None,           "1U7U3kFVZl7oX8bjv9ktZJRL5k5HIkuPW1d4HAeDhvLQ"),
    ("Harrison", "Akron & Massillon",         "330-324-8255", "1d1YuN1GfKSk10HY_WkY4ZJgLu5WEbx1_nWLNoQcltEQ"),
    ("Danny",   "Canton & Summit County",     "330-551-3539", "1LLPVL5ll-Hh2fGIzkDzuzKJyP6krUn8-5ydYQgsvhNY"),
    ("Adam",    "Akron",                      "330-993-0992", "1fshWiWKxvLq2XV9ux8aJBBF4CpL1zLA2YR9i9Z8quI8"),
    ("Trent",   "Akron & Barberton",          None,           "11KtGOkuyCK9KA-fjWqM_6kASgKzJnRaqkV8MtWVr6DU"),
    ("Aaron",   "Akron & Surrounding Areas",  "330-552-8098", "1k3xO58UhmIvBxkbrtaew14jnU0ZudJc7UtB1aeNYg1g"),
]

# MUST be format=md, not format=txt.
#
# The plain-text export silently discards every hyperlink and all table
# structure: no pipes, no URLs, and a listing's address ends up on a different
# line from its open house time. Nothing errors - you just get zero listings.
# The markdown export keeps the table rows and the Zillow URLs this parser
# depends on for addresses. Do not "simplify" this to txt.
EXPORT = "https://docs.google.com/document/d/{doc}/export?format=md"

# Cities Yoak operates in, longest first so "North Canton" wins over "Canton".
CITIES = sorted([
    "Akron", "Barberton", "Canton", "Massillon", "Lakemore", "Rittman", "Norton",
    "Tallmadge", "Stow", "Kent", "Ravenna", "Wadsworth", "Medina", "Wooster",
    "Alliance", "Louisville", "Navarre", "Brewster", "Dalton", "Orrville",
    "Mogadore", "Hartville", "Doylestown", "Clinton", "Green", "Copley",
    "Fairlawn", "Springfield", "Coventry", "North Canton", "Cuyahoga Falls",
    "New Franklin", "Munroe Falls", "Silver Lake", "Bath", "Richfield",
], key=lambda c: -len(c))

MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Guardrails. These exist to catch "someone broke a doc" rather than "inventory
# genuinely changed". A tripped guardrail fails the workflow; it does not
# publish a half-empty site.
MIN_RETAINED = 0.5      # fail if total listings fall by more than half
MIN_TOTAL = 10          # absolute floor - Yoak has never had fewer than 20
MAX_DAYS_AHEAD = 60     # a showing further out than this is a typo, not a plan
MAX_DAYS_STALE = 120    # older than this and we assume the year rolled over

flags = []


def flag(agent, msg):
    flags.append((agent, msg))


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def fetch(doc_id):
    url = EXPORT.format(doc=doc_id)
    req = urllib.request.Request(url, headers={"User-Agent": "yoak-listings-refresh/1"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")


# --------------------------------------------------------------------------
# Address, from the Zillow URL
# --------------------------------------------------------------------------

ZPID = re.compile(r"/homedetails/([A-Za-z0-9\-]+?)/\d+_zpid")


def address_from_zillow(text):
    """'1169-7th-Ave-Akron-OH-44306' -> (address, city, state, zip). None if absent."""
    m = ZPID.search(text.replace("\\", ""))
    if not m:
        return None
    parts = m.group(1).split("-")
    zipcode = state = None
    if parts and re.fullmatch(r"\d{5}", parts[-1]):
        zipcode = parts.pop()
    if parts and re.fullmatch(r"[A-Z]{2}", parts[-1]):
        state = parts.pop()
    rest = " ".join(parts)
    city = None
    for c in CITIES:
        if rest.lower().endswith(" " + c.lower()):
            city = c
            rest = rest[: -(len(c) + 1)]
            break
    addr = rest.strip()
    addr = re.sub(r"\bAPT\s+(\S+)$", r"#\1", addr)   # APT 2 -> #2
    addr = re.sub(r"\s+", " ", addr)
    return addr, city, state or "OH", zipcode


# --------------------------------------------------------------------------
# Dates and times
# --------------------------------------------------------------------------

DATE_RE = re.compile(
    r"(?:(" + "|".join(WEEKDAYS) + r"),?\s+)?"
    r"(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:st|nd|rd|th)?"
    r"(?:,?\s*(\d{4}))?",
    re.I)

TIME_RE = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:-|–|—|to)\s*"
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
    re.I)


def parse_date(text, today, agent, label):
    m = DATE_RE.search(text)
    if not m:
        return None
    weekday, month_name, day, year = m.groups()
    month = MONTHS[month_name.lower()]
    day = int(day)

    if year:
        y = int(year)
    else:
        # No year written. Choose the one that puts the date in a sane window.
        y = today.year
        try_d = datetime.date(y, month, day)
        if (today - try_d).days > MAX_DAYS_STALE:
            y += 1

    try:
        d = datetime.date(y, month, day)
    except ValueError:
        flag(agent, f"{label}: '{m.group(0)}' is not a real date - skipped the date, listing kept")
        return None

    # The cross-check that matters. If the agent wrote a weekday and it does not
    # match the date they wrote, we do not pick a winner - a human must.
    if weekday and WEEKDAYS[d.weekday()] != weekday.lower():
        flag(agent, f"{label}: doc says '{weekday.title()}, {month_name.title()} {day}' "
                    f"but {d.isoformat()} is a {WEEKDAYS[d.weekday()].title()}. "
                    f"Used the date, NOT the weekday - confirm which is right.")

    ahead = (d - today).days
    if ahead > MAX_DAYS_AHEAD:
        raise SystemExit(
            f"GUARDRAIL: {agent} {label} has an open house {ahead} days out ({d}). "
            f"That is almost certainly a typo. Nothing was written.")
    return d


def parse_times(text, agent, label):
    m = TIME_RE.search(text)
    if not m:
        return None, None
    h1, m1, ap1, h2, m2, ap2 = m.groups()
    h1, h2 = int(h1), int(h2)
    m1, m2 = int(m1 or 0), int(m2 or 0)
    ap1 = (ap1 or "").lower()
    ap2 = (ap2 or "").lower()

    if not ap1 and ap2:
        # "5:00-5:30 PM" - the end's meridiem governs, unless that would make
        # the window run backwards ("11:40 AM-12:10 PM").
        ap1 = ap2
        if (h1 % 12) > (h2 % 12):
            ap1 = "am" if ap2 == "pm" else "pm"
    if not ap1 and not ap2:
        # Nothing written at all. Showings are afternoon/evening.
        ap1 = "pm" if h1 < 8 else "am"
        if 8 <= h1 < 12:
            flag(agent, f"{label}: time '{m.group(0)}' has no AM/PM - assumed AM. Verify.")
        ap2 = ap1
    if not ap2:
        ap2 = ap1
        if (h2 % 12) < (h1 % 12):
            ap2 = "pm" if ap1 == "am" else "am"

    def to24(h, ap):
        h = h % 12
        return h + 12 if ap == "pm" else h

    return f"{to24(h1, ap1):02d}:{m1:02d}", f"{to24(h2, ap2):02d}:{m2:02d}"


# --------------------------------------------------------------------------
# The rest of a row
# --------------------------------------------------------------------------

# Trent and Aaliyah write "3/1.5OPEN HOUSE..." with no space, so the bath group
# cannot end on a word boundary - "5" and "O" are both word characters and \b
# would backtrack to give 1 bath instead of 1.5. Assert "not followed by another
# digit or a dot" instead.
BEDBATH_SLASH = re.compile(r"(?<![\d.])(\d)\s*/\s*(\d(?:\.5)?)(?![\d.])")
BEDBATH_WORDS = re.compile(r"(\d)\s*BD\s*\|?\s*(\d(?:\.5)?)\s*B(?![A-Za-z])", re.I)
RENT_RE = re.compile(r"\$\s?([\d,]{3,6})")

NOTES = [
    (re.compile(r"lease\s+to\s+purchase", re.I), "Lease to purchase only"),
    (re.compile(r"lease\s+to\s+own", re.I),      "Lease to own"),
    (re.compile(r"private\s+tours?\s+only", re.I), "Private tours only"),
    (re.compile(r"open\s+house\s+(?:is\s+)?TBD", re.I), "Open house TBD"),
]


def clean(row):
    """Strip the markdown escaping Google's txt export adds."""
    t = row.strip().strip("|").strip()
    t = re.sub(r"\\(.)", r"\1", t)      # \* -> *
    t = re.sub(r"[*#]+", " ", t)        # bold/heading noise
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def parse_doc(text, agent, today):
    listings, seen = [], set()

    # Fail loudly if the document does not look like the markdown table export.
    # Without this, a wrong export format just returns an empty list and the
    # failure looks like "no listings this week" instead of "wrong format".
    rows = [l for l in text.splitlines() if l.lstrip().startswith("|")]
    has_links = "zillow.com" in text.lower()
    if len(rows) < 2 and has_links:
        raise SystemExit(
            f"GUARDRAIL: {agent}'s document has Zillow links but no markdown table "
            f"rows. The export format is wrong - it must be format=md. format=txt "
            f"strips the table and every hyperlink. Nothing was written.")
    if not has_links:
        flag(agent, "no Zillow links anywhere in this doc - every address in it is "
                    "unverified, and the export format may be wrong.")

    for raw in text.splitlines():
        if not raw.lstrip().startswith("|"):
            continue
        row = clean(raw)
        if len(row) < 12:
            continue
        # Section headers and city headers are rows too.
        if re.fullmatch(r"(UPCOMING|PAST|:-:|[A-Za-z ]{3,20})[:.]?", row, re.I) and "zillow" not in raw.lower():
            continue

        # Video Tour links are not listings.
        body = re.sub(r"\[?\s*Video Tour\s*\]?\([^)]*\)", " ", row, flags=re.I)

        addr = address_from_zillow(raw)
        if addr:
            address, city, state, zipcode = addr
        else:
            # No Zillow link. Take the leading text before the first "Open House"
            # and flag it - we have nothing authoritative to check it against.
            lead = re.split(r"open\s+house", body, flags=re.I)[0]
            lead = re.sub(r"\b\d\s*/\s*\d(?:\.5)?\b", "", lead).strip(" ,")
            if not lead or len(lead) < 6:
                continue
            city = next((c for c in CITIES if re.search(rf"\b{c}\b", lead, re.I)), None)
            if city:
                lead = re.sub(rf"[\s,]*\b{city}\b.*$", "", lead, flags=re.I)
            address, state, zipcode = lead.strip(" ,"), "OH", None
            flag(agent, f"'{address}' has no Zillow link - address, city and zip are "
                        f"unverified and the site's Zillow lookup may not resolve.")

        key = (address.lower(), (city or "").lower())
        if key in seen:
            continue
        seen.add(key)

        label = address
        after = re.split(r"open\s+house", body, flags=re.I)
        when = after[1] if len(after) > 1 else ""

        d = parse_date(when, today, agent, label) if when else None
        start = end = None
        if d:
            start, end = parse_times(when, agent, label)
            if not start:
                flag(agent, f"{label}: found a date but no readable time - left the "
                            f"open house off rather than guess.")
                d = None

        beds = baths = rent = None
        # Only look before "open house" so a date written as 9/14 can never be
        # read as 9 beds.
        head = after[0]
        mb = BEDBATH_WORDS.search(head) or BEDBATH_SLASH.search(head)
        if mb:
            b_ = int(mb.group(1))
            v = float(mb.group(2))
            if 1 <= b_ <= 8 and 0.5 <= v <= 8:
                beds = b_
                baths = int(v) if v.is_integer() else v
        mr = RENT_RE.search(body)
        if mr:
            rent = int(mr.group(1).replace(",", ""))

        note = next((n for rx, n in NOTES if rx.search(body)), None)

        listings.append({
            "address": address, "city": city, "state": state, "zip": zipcode,
            "beds": beds, "baths": baths, "rent": rent,
            "openHouse": f"{d.isoformat()}T{start}" if d else None,
            "openHouseEnd": end if d else None,
            "note": note,
        })

        if city is None:
            flag(agent, f"{label}: could not determine the city.")

    return listings


# --------------------------------------------------------------------------

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "data", "listings.json")
    today = datetime.date.today()

    try:
        with open(out, encoding="utf-8") as f:
            previous = json.load(f)
        prev_total = sum(len(a["listings"]) for a in previous["agents"])
    except (OSError, ValueError):
        previous, prev_total = None, 0

    agents_out = []
    for name, area, phone, doc_id in AGENTS:
        try:
            text = fetch(doc_id)
        except Exception as e:                        # noqa: BLE001
            raise SystemExit(f"GUARDRAIL: could not fetch {name}'s doc ({e}). "
                             f"Nothing was written.")
        listings = parse_doc(text, name, today)
        # An agent doc that still contains Zillow links but yields no listings is
        # a parser failure, not an empty week. Fail on it rather than quietly
        # shrinking the site. A doc with genuinely nothing in it has no links
        # either, and only gets a flag.
        if not listings and "zillow.com" in text.lower():
            raise SystemExit(
                f"GUARDRAIL: parsed ZERO listings from {name}'s doc even though it "
                f"still contains Zillow links. The document format has changed or "
                f"the export format is wrong. Nothing was written.")
        if not listings:
            flag(name, "parsed ZERO listings from this doc - check whether it is empty "
                       "on purpose.")
        listings.sort(key=lambda l: (l["openHouse"] is None or l["openHouse"][:10] < today.isoformat(),
                                     l["openHouse"] or "z"))
        agents_out.append({"name": name, "area": area, "phone": phone, "listings": listings})

    total = sum(len(a["listings"]) for a in agents_out)
    upcoming = [(a["name"], l) for a in agents_out for l in a["listings"]
                if l["openHouse"] and l["openHouse"][:10] >= today.isoformat()]
    past = [(a["name"], l) for a in agents_out for l in a["listings"]
            if l["openHouse"] and l["openHouse"][:10] < today.isoformat()]

    # Absolute floor first: this one does not depend on a previous file being
    # present, so a fresh checkout cannot sail past it and publish an empty site.
    if total < MIN_TOTAL:
        raise SystemExit(
            f"GUARDRAIL: only {total} listings parsed across all {len(AGENTS)} docs. "
            f"Yoak has never had fewer than 20. This is a parsing failure, not a "
            f"quiet week. Nothing was written.")

    if prev_total and total < prev_total * MIN_RETAINED:
        raise SystemExit(
            f"GUARDRAIL: listings fell from {prev_total} to {total} "
            f"(more than half). That reads like a broken doc, not a quiet week. "
            f"Nothing was written.")

    prev_addrs = {l["address"].lower() for a in (previous or {"agents": []})["agents"]
                  for l in a["listings"]}
    now_addrs = {l["address"].lower() for a in agents_out for l in a["listings"]}
    added = sorted(now_addrs - prev_addrs)
    removed = sorted(prev_addrs - now_addrs)

    doc = {
        "_comment": [
            "GENERATED FILE - do not hand-edit.",
            "Rebuilt from the per-agent docs on linktr.ee/derekanders by",
            "tools/refresh-listings.py, run weekly by GitHub Actions.",
            "To change a listing, change the agent's doc. To change the agent",
            "roster, phone numbers or areas, edit AGENTS in that script.",
            "",
            "openHouse is local Eastern time, YYYY-MM-DDTHH:MM, or null. Past",
            "times are hidden by the build and again in the visitor's browser,",
            "so a stale date is never shown as current.",
        ],
        "updated": today.isoformat(),
        "agents": agents_out,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")

    # ---- report -----------------------------------------------------------
    r = [f"Refreshed from {len(AGENTS)} agent docs on {today.isoformat()}.", "",
         f"**{total} listings, {len(upcoming)} with an upcoming open house.**", ""]

    if not upcoming:
        r += ["> **No upcoming open houses at all.** Every listing will show a Zillow",
              "> link instead. That is correct behaviour but a bad look - check whether",
              "> the agents have stopped updating their docs.", ""]

    r.append("| Agent | Listings | Upcoming |")
    r.append("|---|---|---|")
    for a in agents_out:
        u = sum(1 for l in a["listings"]
                if l["openHouse"] and l["openHouse"][:10] >= today.isoformat())
        r.append(f"| {a['name']} | {len(a['listings'])} | {u} |")
    r.append("")

    if flags:
        r += [f"### Needs your eyes ({len(flags)})", ""]
        for agent, msg in flags:
            r.append(f"- **{agent}** - {msg}")
        r.append("")
    else:
        r += ["### Needs your eyes", "", "Nothing ambiguous this week.", ""]

    if past:
        r += [f"### Past open houses still listed ({len(past)})", "",
              "Still on the agent docs, so kept. They show a Zillow link, not a stale",
              "time. Confirm with leasing that these are not already rented.", ""]
        for agent, l in past:
            r.append(f"- {l['address']}, {l['city'] or '?'} - {l['openHouse'][:10]} ({agent})")
        r.append("")

    if added:
        r += [f"### New ({len(added)})", ""] + [f"- {a.title()}" for a in added] + [""]
    if removed:
        r += [f"### Gone from the docs ({len(removed)})", ""] + [f"- {a.title()}" for a in removed] + [""]

    report_path = os.environ.get("REPORT_PATH") or os.path.join(root, "refresh-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(r))

    # Let the workflow branch on these without re-parsing anything.
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"total={total}\n")
            f.write(f"upcoming={len(upcoming)}\n")
            f.write(f"flags={len(flags)}\n")

    print("\n".join(r))
    print(f"\nWrote {out}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    sys.exit(main())
