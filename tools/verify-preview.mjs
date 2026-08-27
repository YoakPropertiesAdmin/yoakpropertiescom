/* The preview is only useful if it renders identically to the real site, so
   check the assembled single file the same way verify.mjs checks the pages. */
import { chromium } from 'playwright';
import path from 'path';

const ROOT = process.env.YOAK_OUT
  ? path.resolve(process.env.YOAK_OUT)
  : path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const FILE = 'file://' + path.join(ROOT, 'preview', 'yoak-preview.html');
const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const ctx = await b.newContext({viewport:{width:1500,height:1000}});
const pg = await ctx.newPage();
const errs = [];
pg.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
pg.on('pageerror', e => errs.push('pageerror: '+e.message));

await pg.goto(FILE, {waitUntil:'load'});
await pg.waitForTimeout(1200);

const problems = [];
const tabs = await pg.$$eval('#pages button', els => els.map(e => e.textContent));
if (tabs.length !== 7) problems.push(`expected 7 page tabs, got ${tabs.length}`);
console.log('tabs:', tabs.join(' | '));

async function inspect(label) {
  const f = pg.frames().find(fr => fr !== pg.mainFrame());
  if (!f) { problems.push(`${label}: no frame`); return null; }
  // scroll inside the frame so lazy images load (scroll-behavior is smooth)
  await f.evaluate(async () => {
    const r = document.documentElement; const prev = r.style.scrollBehavior;
    r.style.scrollBehavior = 'auto';
    const step = Math.round(window.innerHeight * 0.6);
    for (let y = 0; y < r.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise(res => requestAnimationFrame(() => setTimeout(res, 80)));
    }
    window.scrollTo(0, 0); r.style.scrollBehavior = prev;
  });
  await pg.waitForTimeout(1500);
  const r = await f.evaluate(() => ({
    h1: document.querySelectorAll('h1').length,
    imgs: document.querySelectorAll('img').length,
    broken: [...document.querySelectorAll('img')].filter(i=>!i.complete||i.naturalWidth===0).map(i=>(i.src||'').slice(0,40)),
    tokens: /@@[^@]+@@/.test(document.body.innerHTML),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    iconFont: getComputedStyle(document.querySelector('.material-symbols-outlined') || document.body).fontFamily,
    iconGlyphOK: (() => {
      const s = document.querySelector('.material-symbols-outlined');
      if (!s) return 'none';
      return s.getBoundingClientRect().width > 6 ? 'rendered' : 'zero-width';
    })(),
    bodyFont: getComputedStyle(document.body).fontFamily,
    navLinks: document.querySelectorAll('header nav a').length,
    portal: /portal/i.test(document.body.textContent),
    title: (document.querySelector('h1')||{}).textContent,
  }));
  if (r.h1 !== 1) problems.push(`${label}: ${r.h1} <h1>`);
  if (r.broken.length) problems.push(`${label}: broken images ${JSON.stringify(r.broken)}`);
  if (r.tokens) problems.push(`${label}: unexpanded asset token left in markup`);
  if (r.overflow > 1) problems.push(`${label}: horizontal overflow ${r.overflow}px`);
  // some pages (404) legitimately contain no icons
  if (r.iconGlyphOK !== 'none' && !/Yoak Icons/.test(r.iconFont))
    problems.push(`${label}: icon font not applied (${r.iconFont})`);
  if (r.iconGlyphOK === 'zero-width') problems.push(`${label}: icon glyphs have no width - font failed to load`);
  if (!/Inter/.test(r.bodyFont)) problems.push(`${label}: body font not Inter (${r.bodyFont})`);
  if (r.portal) problems.push(`${label}: the word "portal" appears`);
  console.log(`  ${label}: h1="${(r.title||'').trim().slice(0,34)}" imgs=${r.imgs} icons=${r.iconGlyphOK} nav=${r.navLinks}`);
  return r;
}

for (const t of tabs) {
  await pg.click(`#pages button:text-is("${t}")`);
  await pg.waitForTimeout(900);
  await inspect('desktop/'+t);
}

// navigate by clicking a link INSIDE the frame
await pg.click('#pages button:text-is("Home")');
await pg.waitForTimeout(900);
{
  const f = pg.frames().find(fr => fr !== pg.mainFrame());
  await f.click('header nav a:text-is("How to Apply")');
  await pg.waitForTimeout(1200);
  const cur = await pg.$eval('#pages button[aria-current="true"]', e=>e.textContent);
  if (cur !== 'How to Apply') problems.push(`in-frame link nav failed: landed on "${cur}"`);
  else console.log('  in-frame link navigation: ok ->', cur);
}
await pg.screenshot({path:'shots/preview-desktop.png'});

// mobile width must trigger the real breakpoints
await pg.click('.seg button[data-w="mobile"]');
await pg.waitForTimeout(1000);
await pg.click('#pages button:text-is("Home")');
await pg.waitForTimeout(1200);
{
  const f = pg.frames().find(fr => fr !== pg.mainFrame());
  const m = await f.evaluate(() => ({
    w: window.innerWidth,
    burgerVisible: !!document.getElementById('nav-toggle')?.offsetParent,
    desktopNavHidden: !document.querySelector('header nav[aria-label="Main navigation"]')?.offsetParent,
  }));
  console.log('  mobile frame width:', m.w, '| burger visible:', m.burgerVisible, '| desktop nav hidden:', m.desktopNavHidden);
  if (m.w > 420) problems.push(`mobile frame too wide (${m.w}px)`);
  if (!m.burgerVisible) problems.push('mobile: hamburger not visible - media queries not resolving in frame');
  if (!m.desktopNavHidden) problems.push('mobile: desktop nav still shown');
  // open the menu
  await f.click('#nav-toggle');
  await pg.waitForTimeout(500);
  const open = await f.evaluate(() => !document.getElementById('mobile-nav').classList.contains('hidden'));
  if (!open) problems.push('mobile: menu did not open inside the preview');
  else console.log('  mobile menu opens: ok');
}
await pg.screenshot({path:'shots/preview-mobile.png'});

const realErrs = errs.filter(e => !/favicon/i.test(e));
if (realErrs.length) problems.push('console: '+JSON.stringify(realErrs.slice(0,4)));

await b.close();
console.log(problems.length ? '\nPROBLEMS:\n'+problems.join('\n') : '\nPREVIEW OK');
process.exit(problems.length?1:0);
