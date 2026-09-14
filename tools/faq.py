"""How to Apply / FAQ page.

Content is Yoak's own FAQ, which until now lived in a Google Doc behind a
Linktree where no prospective tenant would find it and no search engine would
index it. Wording follows the source document closely.

Two deliberate departures from the source, both flagged in the README:
  * The source says monthly rent is paid through "the Resident Center App and
    Buildium account". Yoak has moved to AppFolio, so that sentence would send
    tenants to a decommissioned system. Because the resident portal is not being
    advertised on the public site yet, the line now states only when rent is due
    and says the leasing agent sets up payment at move-in.
  * Yoak's own FAQ document names the payee as "Yoak Properties and Construction
    LLC". Joshua confirmed on 14 Sep 2026 that "Co." is correct, so the payee
    line reads "Co." here and no longer matches the source document. Do not
    "restore" it to LLC from the source without asking Steve or Kipp - a
    cashier's check made out to the wrong entity does not clear.
"""

SECTIONS = [
    {
        'id': 'criteria',
        'icon': 'check_circle',
        'title': 'Do I qualify?',
        'lead': 'These are the standard approval criteria applied to every application. '
                'The specific requirements for an individual property are on its Zillow '
                'listing, under Overview &rarr; Show More.',
        'checks': [
            ('Income', 'Minimum <strong>net</strong> income of three times the monthly rent.'),
            ('Credit', 'Credit score of <strong>550 or above</strong>, with a high '
                       'on-time payment percentage.'),
            ('Rental history', 'No recent evictions.'),
            ('Utilities', 'Tenants are responsible for all utilities.'),
            ('Smoking', 'No smoking in any Yoak property.'),
            ('Pets', 'Permitted, with a one-time fee and a monthly rent increase.'),
        ],
        'after': '<p class="font-body-md text-body-md text-on-surface-variant">'
                 '<strong>If you do not fully qualify:</strong> you may be offered the '
                 'option to pay an additional last month&#8217;s rent deposit. That deposit '
                 'is applied to the final month of your tenancy &mdash; not to the end of '
                 'the initial twelve-month lease.</p>',
    },
    {
        'id': 'vouchers',
        'icon': 'assignment',
        'title': 'Housing Choice Vouchers and Section 8',
        'lead': 'Owners consider voucher applicants on equal footing with every other '
                'applicant. The minimum requirements are:',
        'checks': [
            ('Credit', 'Credit score of <strong>560 or above</strong>.'),
            ('Payment history', '85&ndash;100% on-time payments.'),
            ('Rental history', 'No recent evictions.'),
            ('Income', 'Supplemental income which, combined with the voucher, totals '
                       'approximately three times the monthly rent.'),
        ],
        'after': '',
    },
    {
        'id': 'applying',
        'icon': 'devices',
        'title': 'How to apply',
        'lead': '',
        'steps': [
            ('Find the property on Zillow',
             'Every Yoak listing, including its open house dates and times, is published '
             'on Zillow. The Zillow listing is always the authoritative source.'),
            ('Come to the open house',
             'Open house times are listed on each Zillow listing and on our properties '
             'page. No appointment is needed to attend.'),
            ('Apply on Zillow',
             'All prospective tenants must apply through Zillow. The fee is $35 per '
             'applicant, valid for 30 days and good for an unlimited number of Yoak '
             'properties. Every party must complete their own portion, with PDF proof '
             'of income attached &mdash; partial applications cannot be processed.'),
            ('Wait for a decision',
             'Applications are processed the evening of, or the day after, the open '
             'house. In the best case a decision follows within 24 to 72 hours of the '
             'initial open house.'),
        ],
        'after': '<p class="font-body-md text-body-md text-on-surface-variant">'
                 '<strong>Private showings:</strong> because of high demand, private '
                 'showings are arranged only for pre-approved applicants who have already '
                 'applied and been approved through Zillow. Once approved, you can tour '
                 'any property we manage.</p>',
    },
    {
        'id': 'approved',
        'icon': 'security',
        'title': 'Once you are approved',
        'lead': 'A leasing agent will arrange a deposit appointment at our Barberton '
                'office. The deposit holds the property for 30 days. When the deposit is '
                'received and a move-in date is set, the lease is sent to you '
                'electronically.',
        'steps': [
            ('Switch the utilities into your name',
             'Then provide us with the new account numbers.'),
            ('Sign and initial the lease in full',
             'Every area of the lease needs to be completed.'),
            ('Return to the Barberton office',
             'To pay any outstanding deposit or rental amounts and collect your keys.'),
        ],
        'after': '',
    },
    {
        'id': 'paying',
        'icon': 'domain',
        'title': 'Deposits and paying rent',
        'lead': '',
        'checks': [
            ('Initial deposits and payments',
             'Cash, cashier&#8217;s check or money order, made payable to '
             '<strong>Yoak Properties and Construction Co</strong>.'),
            ('Monthly rent, once you have moved in',
             'Due on or before the first of the month. Your leasing agent will set up '
             'your payment method with you at move-in.'),
        ],
        'after': '',
    },
    {
        'id': 'ltp',
        'icon': 'home_work',
        'title': 'Lease to purchase',
        'lead': 'Some properties are offered as lease to purchase. The intent is to help '
                'you build credit while securing the home: on-time payments are reported, '
                'which accelerates credit repair. The terms are:',
        'checks': [
            ('Rent does not build equity',
             'No portion of the rent goes toward the purchase price. Fair market rent is '
             'charged, and you save toward the purchase independently.'),
            ('Your down payment does count',
             'The down payment, or lease option amount, applies to the purchase price. '
             'The security deposit may also apply.'),
            ('You can buy at any point',
             'The purchase is available at any time during the lease.'),
            ('If financing takes longer than a year',
             'You renegotiate a lease extension with new rental and purchase amounts. '
             '<strong>Your down payment and purchase option carry over to the new '
             'lease.</strong>'),
        ],
        'after': '',
    },
    {
        'id': 'esa',
        'icon': 'support_agent',
        'title': 'Assistance and emotional support animals',
        'lead': 'Requests for an assistance or emotional support animal are handled under '
                'the Fair Housing Act. Supporting documentation should come from a mental '
                'health professional holding a current Ohio licence, follow a genuine and '
                'recent evaluation, and appear on official letterhead showing their name, '
                'licence number and contact details. The letter should describe how the '
                'animal helps with your symptoms; it does not need to disclose your '
                'diagnosis. Speak to your leasing agent and we will walk you through it.',
        'checks': [],
        'after': '',
    },
]


def build(cfg):
    def check_list(items):
        if not items:
            return ''
        rows = ''.join(
            f'<li class="flex items-start gap-3">'
            f'<span aria-hidden="true" class="material-symbols-outlined text-heritage-gold '
            f'text-[20px] shrink-0 mt-0.5">check_circle</span>'
            f'<span class="font-body-md text-body-md text-on-surface-variant">'
            f'<strong class="text-deep-navy">{k}:</strong> {v}</span></li>'
            for k, v in items)
        return f'<ul class="space-y-3 mb-6">{rows}</ul>'

    def step_list(items):
        if not items:
            return ''
        rows = ''.join(
            f'<li class="flex items-start gap-4">'
            f'<span aria-hidden="true" class="w-8 h-8 shrink-0 rounded-full bg-deep-navy '
            f'text-heritage-gold font-label-bold text-label-bold flex items-center '
            f'justify-center">{i}</span>'
            f'<span><span class="font-headline-md text-body-lg text-deep-navy block mb-1">'
            f'{k}</span><span class="font-body-md text-body-md text-on-surface-variant">'
            f'{v}</span></span></li>'
            for i, (k, v) in enumerate(items, 1))
        return f'<ol class="space-y-5 mb-6">{rows}</ol>'

    toc = ''.join(
        f'<a class="block font-body-md text-body-md text-slate-gray hover:text-heritage-gold '
        f'transition-colors py-1" href="#{s["id"]}">{s["title"]}</a>' for s in SECTIONS)

    blocks = []
    for s in SECTIONS:
        lead = (f'<p class="font-body-lg text-body-lg text-on-surface-variant mb-6">'
                f'{s["lead"]}</p>') if s.get('lead') else ''
        blocks.append(
            f'<section class="scroll-mt-28" id="{s["id"]}">'
            f'<div class="flex items-center gap-4 mb-5">'
            f'<span aria-hidden="true" class="w-11 h-11 shrink-0 rounded bg-soft-gold '
            f'text-deep-navy flex items-center justify-center">'
            f'<span class="material-symbols-outlined">{s["icon"]}</span></span>'
            f'<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg '
            f'text-deep-navy">{s["title"]}</h2></div>'
            f'{lead}{check_list(s.get("checks"))}{step_list(s.get("steps"))}'
            f'{s.get("after", "")}</section>')

    return f'''<main class="w-full" id="main">
<section class="w-full pt-16 pb-12 md:pt-24 md:pb-16 bg-surface-container-low border-b border-outline-variant/30 relative overflow-hidden">
<div class="absolute inset-0 opacity-5" style="background-image: radial-gradient(#0F172A 1px, transparent 1px); background-size: 24px 24px;"></div>
<div class="max-w-container-max mx-auto px-margin-mobile md:px-gutter relative z-10 text-center">
<h1 class="font-headline-xl text-headline-lg-mobile md:text-headline-xl text-deep-navy mb-4">How to Apply</h1>
<p class="font-body-lg text-body-lg text-slate-gray max-w-3xl mx-auto">Everything you need before you attend an open house: what we look for, what applying costs, how long a decision takes, and what happens once you are approved.</p>
<div class="mt-8 flex flex-wrap gap-4 justify-center">
<a class="bg-deep-navy text-surface-off-white px-8 py-3 rounded font-label-bold text-label-bold hover:bg-primary-container transition-colors inline-flex items-center gap-2" href="{cfg['APPLY_URL']}" rel="noopener" target="_blank">Apply on Zillow <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_outward</span></a>
<a class="border border-heritage-gold text-deep-navy px-8 py-3 rounded font-label-bold text-label-bold hover:bg-heritage-gold/10 transition-colors" href="properties.html">See current open houses</a>
</div>
</div>
</section>

<section class="py-section-gap-mobile md:py-section-gap-desktop">
<div class="max-w-container-max mx-auto px-margin-mobile md:px-gutter">
<div class="grid grid-cols-1 lg:grid-cols-12 gap-gutter">

<aside class="lg:col-span-4 lg:sticky lg:top-28 lg:self-start" data-toc>
<div class="p-6 bg-surface-off-white rounded-xl shadow-card border border-outline-variant/20">
<h2 class="font-label-bold text-label-bold uppercase text-deep-navy mb-4">Contents</h2>
<nav aria-label="On this page">{toc}</nav>
</div>
<div class="mt-6 p-6 bg-soft-gold rounded-xl border-l-4 border-heritage-gold">
<p class="font-label-bold text-label-bold uppercase text-deep-navy mb-2">Questions?</p>
<p class="font-body-md text-body-md text-on-surface-variant mb-3">Our office is open for deposit appointments and general enquiries.</p>
<a class="block font-body-md text-body-md text-secondary font-semibold hover:underline" href="{cfg['PHONE_HREF']}">{cfg['PHONE_TEXT']}</a>
<a class="block font-body-md text-body-md text-secondary font-semibold hover:underline" href="mailto:{cfg['EMAIL']}">{cfg['EMAIL']}</a>
</div>
</aside>

<div class="lg:col-span-8 space-y-16">
{''.join(blocks)}
<div class="bg-surface-container-low rounded-xl p-6 border border-outline-variant/30">
<p class="font-caption text-caption text-on-surface-variant">Criteria and fees are applied uniformly to every applicant and are subject to change. Requirements for an individual property are on its Zillow listing. Yoak Properties &amp; Construction Co. is an Equal Housing Opportunity provider.</p>
</div>
</div>

</div>
</div>
</section>
</main>'''
