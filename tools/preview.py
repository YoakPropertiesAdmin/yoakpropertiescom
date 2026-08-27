#!/usr/bin/env python3
"""Assemble the built site into one self-contained preview file.

The point is fidelity: this must render exactly what GitHub Pages will serve, so
the real CSS, the real JS and the real assets go in untouched. Only the delivery
changes.

How it works:
  * Every asset becomes a data: URI once, in an ASSETS map. Page markup keeps a
    short token in place of each reference, expanded at the moment a page is
    written into the frame. Inlining directly would repeat the 243 KB logo
    across all seven pages.
  * Each page is rendered inside a srcdoc iframe. That matters for two reasons:
    the site's stylesheet cannot collide with the preview chrome, and CSS media
    queries resolve against the iframe's width - so the 390 px view exercises
    the real mobile breakpoints rather than faking them with a transform.
  * Links between pages are intercepted inside the frame and swapped, so the
    preview is clickable end to end.
"""

import base64
import json
import mimetypes
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get('YOAK_OUT') or os.path.dirname(HERE)
OUT = os.environ.get('YOAK_PREVIEW') or os.path.join(SITE, 'preview', 'yoak-preview.html')

PAGES = [
    ('index.html', 'Home'),
    ('properties.html', 'Our Properties'),
    ('faq.html', 'How to Apply'),
    ('about.html', 'About Us'),
    ('privacy.html', 'Privacy'),
    ('terms.html', 'Terms'),
    ('404.html', '404'),
]

BUILD_DATE = '27 August 2026'


def data_uri(path):
    mime, _ = mimetypes.guess_type(path)
    if path.endswith('.woff2'):
        mime = 'font/woff2'
    raw = open(path, 'rb').read()
    return f'data:{mime};base64,' + base64.b64encode(raw).decode('ascii')


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    # ---- assets -----------------------------------------------------------
    assets = {}
    for f in sorted(os.listdir(f'{SITE}/assets/img')):
        assets[f] = data_uri(f'{SITE}/assets/img/{f}')

    # ---- stylesheet, with the self-hosted fonts folded in -----------------
    css = open(f'{SITE}/assets/css/site.css', encoding='utf-8').read()

    def font_sub(m):
        name = m.group(1)
        p = f'{SITE}/assets/fonts/{name}'
        return f"url('{data_uri(p)}')" if os.path.exists(p) else m.group(0)

    css = re.sub(r"url\(\s*['\"]?\.\./fonts/([^'\")]+)['\"]?\s*\)", font_sub, css)
    if '../fonts/' in css:
        raise SystemExit('a font reference was left unresolved')

    js = open(f'{SITE}/assets/js/site.js', encoding='utf-8').read()

    # ---- page bodies ------------------------------------------------------
    pages = {}
    for name, _label in PAGES:
        html = open(f'{SITE}/{name}', encoding='utf-8').read()
        m = re.search(r'(?s)<body([^>]*)>(.*)</body>', html)
        if not m:
            raise SystemExit(f'{name}: no <body>')
        body_attrs, body = m.group(1), m.group(2)
        # the real page loads site.js with a <script src>; the frame gets it
        # from the shared head instead
        body = re.sub(r'<script[^>]*src="[^"]*site\.js"[^>]*>\s*</script>', '', body)
        # asset references become tokens
        body = re.sub(r'(?:\./)?(?:/)?assets/img/([A-Za-z0-9._-]+)',
                      lambda mm: '@@' + mm.group(1) + '@@', body)
        # the 404 page uses root-absolute page links; make them relative so the
        # frame's click handler treats them like any other internal link
        body = re.sub(r'href="/([a-z0-9]+\.html)"', r'href="\1"', body)
        body = body.replace('href="/"', 'href="index.html"')
        pages[name] = {'attrs': body_attrs, 'body': body}

        missing = [t for t in re.findall(r'@@([^@]+)@@', body) if t not in assets]
        if missing:
            raise SystemExit(f'{name}: unknown assets {missing}')

    def js_str(s):
        return json.dumps(s).replace('</', '<\\/')

    payload = {
        'assets': assets,
        'css': css,
        'js': js,
        'pages': pages,
        'order': [p for p, _ in PAGES],
        'labels': {p: l for p, l in PAGES},
    }

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(TEMPLATE.replace('__PAYLOAD__', js_str(json.dumps(payload)))
                        .replace('__BUILD_DATE__', BUILD_DATE))

    kb = os.path.getsize(OUT) / 1024
    print(f'  wrote {OUT}  {kb/1024:.2f} MB')
    print(f'  {len(assets)} assets, {len(pages)} pages, css {len(css)/1024:.0f} KB')


TEMPLATE = r'''<title>Yoak Properties Site Preview</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  /* Preview chrome only. Everything inside the frame is the site's own CSS,
     isolated from this by the iframe boundary.

     The chrome commits to one dark treatment on purpose: it is tool furniture,
     it should read as separate from the page under review in either host
     theme, and a dark surround is what makes the 390px frame read as a phone.
     Every colour is painted explicitly so nothing is borrowed from the host. */
  :root {
    --chrome:       #12161f;   /* navy-biased near-black: adjacent to Yoak's
                                  deep navy without matching it */
    --chrome-2:     #1a2030;
    --hairline:     #262e40;
    --ink:          #dbe1ec;
    --ink-dim:      #8b95a8;
    --gold:         #D4AF37;   /* the site's own accent, for active state */
    --stage:        #0b0e14;
    --bar: 52px;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0;
    background: var(--stage);
    color: var(--ink);
    font: 400 13px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  header {
    flex: 0 0 auto;
    height: var(--bar);
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 0 14px;
    background: var(--chrome);
    border-bottom: 1px solid var(--hairline);
    overflow-x: auto;
    scrollbar-width: none;
  }
  header::-webkit-scrollbar { display: none; }

  .brand { display: flex; align-items: baseline; gap: 9px; white-space: nowrap; }
  .brand b {
    font-weight: 600; font-size: 13px; letter-spacing: .01em; color: var(--ink);
  }
  .brand span {
    font-size: 11px; color: var(--ink-dim); letter-spacing: .04em;
    text-transform: uppercase;
  }
  .dot {
    width: 6px; height: 6px; border-radius: 50%; background: var(--gold);
    flex: 0 0 auto; align-self: center;
  }

  nav { display: flex; gap: 2px; white-space: nowrap; }
  nav button, .seg button {
    font: inherit; font-size: 12px; color: var(--ink-dim);
    background: none; border: 0; cursor: pointer;
    padding: 6px 11px; border-radius: 5px;
    transition: color .15s, background .15s;
  }
  nav button:hover, .seg button:hover { color: var(--ink); background: var(--chrome-2); }
  nav button[aria-current="true"] {
    color: #14181f; background: var(--gold); font-weight: 600;
  }

  .spacer { margin-left: auto; }

  .seg {
    display: flex; gap: 2px; padding: 2px;
    background: var(--chrome-2); border: 1px solid var(--hairline); border-radius: 7px;
  }
  .seg button[aria-pressed="true"] { color: var(--ink); background: #2b3446; }

  .meta {
    font-size: 11px; color: var(--ink-dim); white-space: nowrap;
    letter-spacing: .02em;
  }

  main {
    flex: 1 1 auto; min-height: 0;
    display: flex; justify-content: center;
    padding: 0;
    overflow: hidden;
  }
  #stage {
    height: 100%;
    width: 100%;
    max-width: 100%;
    transition: max-width .28s cubic-bezier(.4,0,.2,1);
    display: flex; flex-direction: column;
  }
  body[data-w="mobile"] #stage {
    max-width: 402px;
    padding: 14px 0 0;
  }
  body[data-w="mobile"] #frame {
    border: 1px solid var(--hairline);
    border-bottom: 0;
    border-radius: 14px 14px 0 0;
  }
  #frame {
    flex: 1 1 auto;
    width: 100%;
    border: 0;
    background: #fff;
    display: block;
  }

  @media (prefers-reduced-motion: reduce) {
    #stage { transition: none; }
  }

  :focus-visible { outline: 2px solid var(--gold); outline-offset: 2px; }

  @media (max-width: 720px) {
    .meta, .brand span { display: none; }
  }
</style>

<header>
  <span class="dot" aria-hidden="true"></span>
  <span class="brand"><b>Yoak Properties</b><span>pre&#8209;launch preview</span></span>

  <nav id="pages" aria-label="Page"></nav>

  <span class="spacer"></span>

  <div class="seg" role="group" aria-label="Viewport width">
    <button type="button" data-w="desktop" aria-pressed="true">Desktop</button>
    <button type="button" data-w="mobile" aria-pressed="false">Mobile</button>
  </div>

  <span class="meta">Built __BUILD_DATE__ &middot; not yet live</span>
</header>

<main>
  <div id="stage">
    <iframe id="frame" title="Yoak Properties website preview"></iframe>
  </div>
</main>

<script>
(function () {
  'use strict';

  var D = JSON.parse(__PAYLOAD__);

  // Expand asset tokens to the data: URIs held once in D.assets.
  function expand(html) {
    return html.replace(/@@([^@]+)@@/g, function (m, name) {
      return D.assets[name] || m;
    });
  }

  // The frame's <head>: the site's real stylesheet and script, plus a small
  // shim that hands link clicks back to this page.
  function head() {
    return '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
      + '<meta name="viewport" content="width=device-width, initial-scale=1">'
      + '<style>' + D.css + '</style>'
      + '<script>' + D.js + '<\/script>'
      + '<script>' + SHIM + '<\/script>'
      + '</head>';
  }

  var SHIM = [
    'document.addEventListener("click", function (e) {',
    '  var a = e.target.closest && e.target.closest("a");',
    '  if (!a) return;',
    '  var href = a.getAttribute("href") || "";',
    '  if (/^(https?:|mailto:|tel:)/.test(href)) return;',   // leave real links alone
    '  if (href.charAt(0) === "#") return;',                 // in-page anchor: native
    '  var m = /^([a-z0-9.-]+\\.html)(#.*)?$/i.exec(href);',
    '  if (!m) return;',
    '  e.preventDefault();',
    '  parent.postMessage({ yoakGo: m[1], hash: m[2] || "" }, "*");',
    '});'
  ].join('\n');

  var frame = document.getElementById('frame');
  var nav = document.getElementById('pages');
  var current = null;

  function show(name, hash) {
    if (!D.pages[name]) name = 'index.html';
    current = name;
    var p = D.pages[name];
    frame.srcdoc = head() + '<body' + p.attrs + '>' + expand(p.body) + '</body></html>';
    if (hash) {
      frame.addEventListener('load', function once() {
        frame.removeEventListener('load', once);
        try {
          var el = frame.contentDocument.getElementById(hash.slice(1));
          if (el) el.scrollIntoView();
        } catch (err) { /* cross-origin guard; harmless */ }
      });
    }
    [].forEach.call(nav.children, function (b) {
      b.setAttribute('aria-current', b.dataset.page === name ? 'true' : 'false');
    });
  }

  D.order.forEach(function (name) {
    var b = document.createElement('button');
    b.type = 'button';
    b.dataset.page = name;
    b.textContent = D.labels[name];
    b.addEventListener('click', function () { show(name, ''); });
    nav.appendChild(b);
  });

  window.addEventListener('message', function (e) {
    if (e.data && e.data.yoakGo) show(e.data.yoakGo, e.data.hash);
  });

  [].forEach.call(document.querySelectorAll('.seg button'), function (b) {
    b.addEventListener('click', function () {
      document.body.dataset.w = b.dataset.w;
      [].forEach.call(document.querySelectorAll('.seg button'), function (o) {
        o.setAttribute('aria-pressed', String(o === b));
      });
    });
  });

  document.body.dataset.w = 'desktop';
  show('index.html', '');
})();
</script>
'''

if __name__ == '__main__':
    main()
