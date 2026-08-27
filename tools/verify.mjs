import { chromium } from 'playwright';
import http from 'http';
import fs from 'fs';
import path from 'path';

const ROOT = process.env.YOAK_OUT
  ? path.resolve(process.env.YOAK_OUT)
  : path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const MIME = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.png':'image/png','.jpg':'image/jpeg','.xml':'application/xml','.txt':'text/plain'};
const server = http.createServer((req,res)=>{
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT,p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404,{'Content-Type':'text/html'});
    return res.end(fs.readFileSync(path.join(ROOT,'404.html')));
  }
  res.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});
  res.end(fs.readFileSync(f));
});
await new Promise(r=>server.listen(8899,r));

let problems = [];

// The stylesheet is generated, and a bad `content` glob in tailwind.config.js
// yields a valid-looking CSS file containing no utility classes at all - the
// site then renders completely unstyled with no error anywhere in the build.
// This happened once. Check the output actually has utilities in it.
{
  const cssPath = path.join(ROOT, 'assets', 'css', 'site.css');
  const css = fs.readFileSync(cssPath, 'utf8');
  const bytes = Buffer.byteLength(css);
  const markers = ['deep-navy', 'heritage-gold', 'container-max', 'margin-mobile'];
  const missing = markers.filter(m => !css.includes(m));
  if (bytes < 20000) problems.push(`site.css is only ${bytes} bytes - Tailwind probably scanned no files`);
  if (missing.length) problems.push(`site.css is missing utilities ${JSON.stringify(missing)} - check tailwind.config.js content globs`);
  console.log(`stylesheet: ${(bytes/1024).toFixed(0)} KB, utilities present: ${markers.length - missing.length}/${markers.length}`);
}

const PAGES=['index.html','about.html','properties.html','faq.html','privacy.html','terms.html','404.html'];
const browser = await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});

for (const view of [{name:'desktop',width:1440,height:1000},{name:'mobile',width:390,height:844}]) {
  const ctx = await browser.newContext({viewport:{width:view.width,height:view.height}, deviceScaleFactor:1});
  for (const pg of PAGES) {
    const page = await ctx.newPage();
    const consoleErrs=[], failed=[];
    page.on('console', m=>{ if(m.type()==='error') consoleErrs.push(m.text()); });
    page.on('requestfailed', r=>failed.push(r.url()));
    const resp = [];
    page.on('response', r=>{ if(r.status()>=400) resp.push(r.status()+' '+r.url()); });

    await page.goto(`http://127.0.0.1:8899/${pg}`, {waitUntil:'networkidle', timeout:30000});
    // Scroll the whole page so loading="lazy" images actually fetch.
    // The site sets `scroll-behavior: smooth`, which animates programmatic
    // scrolling and stops this loop from ever reaching the bottom, so disable
    // it for the duration of the sweep.
    await page.evaluate(async () => {
      const root = document.documentElement;
      const prev = root.style.scrollBehavior;
      root.style.scrollBehavior = 'auto';
      const step = Math.round(window.innerHeight * 0.6);
      for (let y = 0; y < root.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => requestAnimationFrame(() => setTimeout(r, 90)));
      }
      window.scrollTo(0, 0);
      root.style.scrollBehavior = prev;
    });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2500);

    // broken images
    const brokenImgs = await page.$$eval('img', els => els.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src')));
    // horizontal overflow
    const overflow = await page.evaluate(()=> document.documentElement.scrollWidth - document.documentElement.clientWidth);
    // dead controls: buttons with no handler & no form, links with empty/# href
    const deadLinks = await page.$$eval('a', els => els.filter(a=>{
      const h=a.getAttribute('href'); return !h || h==='#' || h.startsWith('{{') || h.startsWith('C:');
    }).map(a=>a.textContent.trim().slice(0,40)));
    const bareButtons = await page.$$eval('button', els => els.filter(b=>!b.id&&b.type!=='submit').map(b=>b.textContent.trim().slice(0,40)));
    // visible raw ligature text (icon font failed AND text showing)
    const h1 = await page.$$eval('h1', e=>e.length);

    const tag = `${view.name}/${pg}`;
    if (brokenImgs.length) problems.push(`${tag}: broken images ${JSON.stringify(brokenImgs)}`);
    if (overflow > 1) problems.push(`${tag}: horizontal overflow ${overflow}px`);
    if (deadLinks.length) problems.push(`${tag}: dead links ${JSON.stringify(deadLinks)}`);
    if (bareButtons.length) problems.push(`${tag}: non-functional buttons ${JSON.stringify(bareButtons)}`);
    if (h1 !== 1) problems.push(`${tag}: ${h1} <h1> elements (want exactly 1)`);
    if (resp.length) problems.push(`${tag}: bad responses ${JSON.stringify(resp)}`);
    if (failed.filter(u=>!u.includes('fonts.g')).length) problems.push(`${tag}: request failed ${JSON.stringify(failed.filter(u=>!u.includes('fonts.g')))}`);
    const realErrs = consoleErrs.filter(e => !/ERR_TUNNEL_CONNECTION_FAILED|fonts\.g/.test(e));
    if (realErrs.length) problems.push(`${tag}: console ${JSON.stringify(realErrs)}`);

    // no open-house date still on the page may be in the past
    const staleOH = await page.$$eval('[data-openhouse],[data-openhouse-remove]', els =>
      els.map(e => e.getAttribute('data-openhouse') || e.getAttribute('data-openhouse-remove')));
    const todayISO = new Date().toISOString().slice(0,10);
    const bad = staleOH.filter(d => d && d.slice(0,10) < todayISO);
    if (bad.length) problems.push(`${tag}: past open house still shown ${JSON.stringify(bad)}`);
    // and any <template> fallback must not be leaking visible text
    const tplText = await page.$$eval('template', els => els.map(e => e.textContent.trim()).filter(Boolean).length);
    const visibleTpl = await page.evaluate(() => {
      let n = 0;
      document.querySelectorAll('template').forEach(t => { if (t.offsetParent) n++; });
      return n;
    });
    if (visibleTpl) problems.push(`${tag}: ${visibleTpl} <template> rendering visibly`);

    await page.screenshot({path:`shots/${view.name}-${pg.replace('.html','')}.png`, fullPage:true});

    // mobile menu behaviour
    if (view.name==='mobile' && pg==='index.html') {
      const t = await page.$('#nav-toggle');
      await t.click(); await page.waitForTimeout(350);
      const open = await page.$eval('#mobile-nav', e=>!e.classList.contains('hidden'));
      if (!open) problems.push('mobile menu did not open');
      const visible = await page.$eval('#mobile-nav', e=>e.getBoundingClientRect().height>0);
      if (!visible) problems.push('mobile menu has zero height when open');
      await page.screenshot({path:'shots/mobile-menu-open.png'});
      await page.keyboard.press('Escape'); await page.waitForTimeout(300);
      const closed = await page.$eval('#mobile-nav', e=>e.classList.contains('hidden'));
      if (!closed) problems.push('mobile menu did not close on Escape');
    }
    await page.close();
  }
  await ctx.close();
}
await browser.close();
server.close();
console.log(problems.length ? 'PROBLEMS:\n'+problems.join('\n') : 'ALL CHECKS PASSED');
