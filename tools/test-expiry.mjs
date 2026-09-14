/* Fast-forward the browser clock and confirm the site stops advertising
   open houses that have passed. Without this, the failure mode is silent:
   the page keeps showing a date that is weeks old. */
import { chromium } from 'playwright';
import http from 'http'; import fs from 'fs'; import path from 'path';
const ROOT = process.env.YOAK_OUT
  ? path.resolve(process.env.YOAK_OUT)
  : path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const MIME={'.html':'text/html','.css':'text/css','.js':'text/javascript','.png':'image/png','.jpg':'image/jpeg','.woff2':'font/woff2','.json':'application/json'};
const srv=http.createServer((q,r)=>{let p=q.url.split('?')[0]; if(p.endsWith('/'))p+='index.html';
 const f=path.join(ROOT,p); if(!fs.existsSync(f)){r.writeHead(404);return r.end('x');}
 r.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'}); r.end(fs.readFileSync(f));});
await new Promise(r=>srv.listen(8896,r));
// Playwright resolves its own browser. Do NOT hardcode an executablePath here:
// this line used to point at a chromium inside the container the site was
// originally built in. That path exists on no other machine, so the verifier
// failed on GitHub Actions and on Windows while looking like a Playwright
// problem. Set CHROME_PATH only if you deliberately need a specific binary.
const LAUNCH = process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {};
const b = await chromium.launch(LAUNCH);
const problems=[];

async function at(fakeISO, label) {
  const ctx=await b.newContext({viewport:{width:1440,height:1000}});
  await ctx.addInitScript(`{
    const FAKE = new Date('${fakeISO}').getTime();
    const _D = Date;
    class MockDate extends _D {
      constructor(...a){ super(...(a.length ? a : [FAKE])); }
      static now(){ return FAKE; }
    }
    MockDate.parse = _D.parse; MockDate.UTC = _D.UTC;
    Date = MockDate;
  }`);

  // home page teaser
  let pg = await ctx.newPage();
  await pg.goto('http://127.0.0.1:8896/index.html',{waitUntil:'networkidle'});
  await pg.waitForTimeout(400);
  const teaserCards = await pg.$$eval('[data-openhouse-remove]', e=>e.length);
  const teaserVisible = await pg.evaluate(()=>{
    const g=document.querySelector('[data-openhouse-group]');
    if(!g) return 'no-group';
    const s=g.closest('section');
    return s && s.style.display==='none' ? 'hidden' : 'visible';
  });
  await pg.close();

  // properties page
  pg = await ctx.newPage();
  await pg.goto('http://127.0.0.1:8896/properties.html',{waitUntil:'networkidle'});
  await pg.waitForTimeout(400);
  const datedRows = await pg.$$eval('[data-openhouse]', e=>e.length);
  const zillowRows = await pg.evaluate(()=>
    [...document.querySelectorAll('a')].filter(a=>/Open house times on Zillow/.test(a.textContent)).length);
  // is any literal month name still shown next to "Open house"?
  const shownDates = await pg.evaluate(()=>
    [...document.querySelectorAll('p')].filter(p=>/Open house\s/.test(p.textContent)).length);
  await pg.close();
  await ctx.close();

  console.log(`${label} (clock=${fakeISO})`);
  console.log(`   home: ${teaserCards} teaser cards, section ${teaserVisible}`);
  console.log(`   properties: ${datedRows} dated rows, ${zillowRows} zillow-fallback rows, ${shownDates} "Open house" paragraphs`);
  return {teaserCards, teaserVisible, datedRows, zillowRows, shownDates};
}

const now  = await at('2026-08-27T09:00:00', 'TODAY');
const soon = await at('2026-09-05T09:00:00', 'AFTER most open houses');
const far  = await at('2027-03-01T09:00:00', 'SIX MONTHS LATER');

if (now.datedRows === 0) problems.push('today: expected some dated rows, got none');
if (now.teaserVisible !== 'visible') problems.push('today: teaser section should be visible');
if (far.datedRows !== 0) problems.push(`far future: ${far.datedRows} dated rows still present`);
if (far.shownDates !== 0) problems.push(`far future: ${far.shownDates} "Open house" date paragraphs still shown`);
if (far.teaserCards !== 0) problems.push(`far future: ${far.teaserCards} teaser cards still present`);
if (far.teaserVisible !== 'hidden') problems.push('far future: teaser section should be hidden');
if (far.zillowRows < 20) problems.push(`far future: only ${far.zillowRows} rows fell back to Zillow`);
if (!(soon.datedRows < now.datedRows)) problems.push('9 days on: expected fewer dated rows');

await b.close(); srv.close();
console.log(problems.length ? '\nPROBLEMS:\n'+problems.join('\n') : '\nEXPIRY LOGIC OK');
process.exit(problems.length ? 1 : 0);
