"""Google reviews section, generated from site/data/reviews.json.

Yoak has 68 Google reviews. Google's own Places API caps a response at five and
forbids caching review content, so showing a real selection means curating it
here rather than calling the API.

Two deliberate safety rules, because the mockups this site replaced shipped
three invented testimonials attributed to named people:

  * A review is only rendered if it has a real author and real text. Anything
    half-filled fails the build rather than reaching the page.
  * With no usable reviews, the section is replaced by a plain link to the
    Google profile. The page degrades to "go read them on Google" instead of
    displaying filler.
"""

import json
import os
import re

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']

PLACEHOLDER_HINTS = ('lorem', 'example', 'placeholder', 'your review here',
                     'replace me', 'todo', 'xxx', 'liam smith', 'ava brown',
                     'noah garcia', 'olivia lee')

STAR = ('M12 2.6l2.85 5.95 6.5.89-4.72 4.53 1.17 6.44L12 17.35l-5.8 3.06 '
        '1.17-6.44L2.65 9.44l6.5-.89z')


def load(outdir):
    p = os.path.join(outdir, 'data', 'reviews.json')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def stars(rating, size=18, idp=''):
    """Five stars with the last one partially filled to match the rating."""
    out = []
    for i in range(5):
        frac = max(0.0, min(1.0, (rating or 0) - i))
        if frac >= 0.999:
            fill = '#D4AF37'
        elif frac <= 0.001:
            fill = 'none'
        else:
            gid = f'st{idp}{i}'
            out.append(
                f'<svg aria-hidden="true" viewBox="0 0 24 24" width="{size}" height="{size}">'
                f'<defs><linearGradient id="{gid}">'
                f'<stop offset="{frac:.3f}" stop-color="#D4AF37"/>'
                f'<stop offset="{frac:.3f}" stop-color="transparent"/>'
                f'</linearGradient></defs>'
                f'<path d="{STAR}" fill="url(#{gid})" stroke="#D4AF37" stroke-width="1.3"/></svg>')
            continue
        out.append(
            f'<svg aria-hidden="true" viewBox="0 0 24 24" width="{size}" height="{size}">'
            f'<path d="{STAR}" fill="{fill}" stroke="#D4AF37" stroke-width="1.3"/></svg>')
    return ''.join(out)


def pretty_date(d):
    """'2026-07-14' or '2026-07' -> 'July 2026'. Absolute, so it never goes stale."""
    if not d:
        return ''
    m = re.match(r'^(\d{4})-(\d{2})', str(d))
    if not m:
        return str(d)
    return f'{MONTHS[int(m.group(2)) - 1]} {m.group(1)}'


def usable(r):
    author = (r.get('author') or '').strip()
    text = (r.get('text') or '').strip()
    if not author or not text:
        return False
    low = (author + ' ' + text).lower()
    return not any(h in low for h in PLACEHOLDER_HINTS)


def build(cfg):
    """Returns the reviews section HTML, or the fallback block if there is nothing real."""
    data = load(cfg['OUT']) or {}
    all_reviews = data.get('reviews') or []
    profile = (data.get('profileUrl') or '').strip()
    leave = (data.get('reviewUrl') or '').strip()
    rating = data.get('rating')
    total = data.get('total')

    # A half-filled entry is a mistake, not a placeholder to render.
    broken = []
    for i, r in enumerate(all_reviews):
        has_any = any((r.get(k) or '').strip() for k in ('author', 'text'))
        if has_any and not usable(r):
            broken.append(i)
    if broken:
        raise SystemExit(
            f'reviews.json: entries {broken} are incomplete or look like placeholder '
            f'text. Fill in author and text, or remove them. Refusing to publish '
            f'reviews that are not real.')

    reviews = [r for r in all_reviews if usable(r)]
    link = profile or cfg['REVIEWS_URL']

    count_txt = ''
    if total:
        count_txt = f'{total} review{"" if total == 1 else "s"} on Google'
    elif reviews:
        count_txt = 'Reviews on Google'

    # ---- aggregate header ------------------------------------------------
    agg = ''
    if rating:
        agg = (f'<div class="flex items-center gap-3 flex-wrap">'
               f'<span class="font-headline-xl text-headline-lg text-deep-navy '
               f'leading-none" style="font-variant-numeric:tabular-nums">'
               f'{rating:.1f}</span>'
               f'<span class="flex items-center gap-0.5">{stars(rating, 22, "agg")}</span>'
               f'<span class="font-body-md text-body-md text-on-surface-variant">'
               f'{count_txt}</span></div>')
    elif count_txt:
        agg = (f'<p class="font-body-md text-body-md text-on-surface-variant">'
               f'{count_txt}</p>')

    buttons = (
        f'<div class="flex flex-wrap gap-3">'
        + (f'<a class="bg-deep-navy text-surface-off-white px-6 py-3 rounded '
           f'font-label-bold text-label-bold hover:bg-primary-container '
           f'transition-colors inline-flex items-center gap-2" href="{leave}" '
           f'rel="noopener" target="_blank">Leave a review '
           f'<span aria-hidden="true" class="material-symbols-outlined text-base">'
           f'arrow_outward</span></a>' if leave else '')
        + (f'<a class="border border-heritage-gold text-deep-navy px-6 py-3 rounded '
           f'font-label-bold text-label-bold hover:bg-heritage-gold/10 '
           f'transition-colors inline-flex items-center gap-2" href="{link}" '
           f'rel="noopener" target="_blank">'
           f'{"Read all on Google" if total else "Read our reviews"} '
           f'<span aria-hidden="true" class="material-symbols-outlined text-base">'
           f'arrow_outward</span></a>' if link else '')
        + '</div>')

    # ---- no real reviews yet: link out rather than show filler ----------
    if not reviews:
        return (
            f'<section class="px-margin-mobile md:px-gutter py-section-gap-mobile '
            f'md:py-24 bg-soft-gold">'
            f'<div class="max-w-container-max mx-auto">'
            f'<div class="flex flex-col lg:flex-row lg:items-center gap-8 justify-between">'
            f'<div class="max-w-2xl">'
            f'<span aria-hidden="true" class="material-symbols-outlined text-heritage-gold '
            f'text-4xl">format_quote</span>'
            f'<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg '
            f'text-deep-navy mt-2 mb-3">What Our Tenants Say</h2>'
            f'<p class="font-body-lg text-body-lg text-on-surface-variant mb-4">'
            f'Our residents leave reviews on our Google Business Profile.</p>{agg}</div>'
            f'{buttons}</div></div></section>'), 0

    # ---- the widget ------------------------------------------------------
    cards = []
    for i, r in enumerate(reviews):
        rr = r.get('rating')
        star_row = (f'<span class="flex items-center gap-0.5 mb-4">'
                    f'{stars(rr, 17, f"c{i}")}</span>') if rr else ''
        when = pretty_date(r.get('date'))
        when_html = (f'<span class="font-caption text-caption text-slate-gray">'
                     f'{when}</span>') if when else ''
        initial = r['author'].strip()[0].upper()
        reply = ''
        if (r.get('response') or '').strip():
            reply = (f'<div class="mt-4 pt-4 border-t border-outline-variant/20">'
                     f'<p class="font-caption text-caption uppercase tracking-wider '
                     f'text-heritage-gold font-bold mb-1">Yoak Properties responded</p>'
                     f'<p class="font-body-md text-body-md text-on-surface-variant">'
                     f'{r["response"].strip()}</p></div>')
        cards.append(
            f'<figure class="bg-surface-container-lowest rounded-xl shadow-card '
            f'border border-outline-variant/20 p-6">'
            f'{star_row}'
            f'<blockquote class="font-body-md text-body-md text-on-surface-variant">'
            f'{r["text"].strip()}</blockquote>'
            f'<figcaption class="flex items-center gap-3 mt-5 pt-4 '
            f'border-t border-outline-variant/20">'
            f'<span aria-hidden="true" class="w-9 h-9 shrink-0 rounded-full bg-deep-navy '
            f'text-heritage-gold font-label-bold text-label-bold flex items-center '
            f'justify-center">{initial}</span>'
            f'<span class="min-w-0"><span class="block font-label-bold text-label-bold '
            f'text-deep-navy truncate">{r["author"].strip()}</span>{when_html}</span>'
            f'</figcaption>{reply}</figure>')

    cols = 'md:grid-cols-2 lg:grid-cols-3' if len(cards) >= 3 else 'md:grid-cols-2'

    return (
        f'<section class="px-margin-mobile md:px-gutter py-section-gap-mobile '
        f'md:py-24 bg-soft-gold">'
        f'<div class="max-w-container-max mx-auto">'
        f'<div class="flex flex-col lg:flex-row lg:items-end gap-6 justify-between mb-10">'
        f'<div>'
        f'<p class="font-label-bold text-label-bold uppercase text-secondary mb-2">'
        f'Tenant reviews</p>'
        f'<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg '
        f'text-deep-navy mb-3">What Our Tenants Say</h2>'
        f'{agg}</div>'
        f'{buttons}</div>'
        f'<div class="grid grid-cols-1 {cols} gap-gutter items-start">'
        f'{"".join(cards)}</div>'
        f'<p class="font-caption text-caption text-on-surface-variant mt-6">'
        f'Reviews are reproduced from our Google Business Profile.'
        + (f' <a class="text-secondary font-semibold hover:underline" href="{link}" '
           f'rel="noopener" target="_blank">Read all of them on Google</a>.' if link else '')
        + f'</p>'
        f'</div></section>'), len(reviews)
