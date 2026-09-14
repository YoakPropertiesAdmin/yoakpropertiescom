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

// The three clocks used to be hardcoded ('2026-08-27', '2026-09-05',
// '2027-03-01'). That tied the test to one week's inventory: once the listings
// moved past September the "9 days on" clock fell BEFORE every open house, so
// nothing had expired and the test failed on correct output. Derive the clocks
// from the data instead, so this keeps testing the behaviour rather than a
// particular calendar.
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'listings.json'), 'utf8'));
const allListings = data.agents.flatMap(a => a.listings);
const build = process.env.BUILD_TODAY || data.updated || new Date().toISOString().slice(0, 10);
const futureDays = [...new Set(
  allListings.map(l => l.openHouse).filter(Boolean)
    .map(s => s.slice(0, 10)).filter(d => d >= build)
)].sort();

const addDays = (iso, n) => {
  const d = new Date(iso + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
};

if (futureDays.length === 0) {
  console.log('No upcoming open houses in the data - nothing to expire. Skipping.');
  await b.close(); srv.close();
  process.exit(0);
}

const now  = await at(`${futureDays[0]}T00:01:00`, 'ON THE FIRST OPEN HOUSE DAY');
// One day past the earliest open house day: everything on that day must be gone.
const soon = await at(`${addDays(futureDays[0], 1)}T00:01:00`, 'THE DAY AFTER');
const far  = await at(`${addDays(futureDays[futureDays.length - 1], 365)}T00:01:00`, 'A YEAR AFTER THE LAST');

if (now.datedRows === 0) problems.push('today: expected some dated rows, got none');
if (now.teaserVisible !== 'visible') problems.push('today: teaser section should be visible');
if (far.datedRows !== 0) problems.push(`far future: ${far.datedRows} dated rows still present`);
if (far.shownDates !== 0) problems.push(`far future: ${far.shownDates} "Open house" date paragraphs still shown`);
if (far.teaserCards !== 0) problems.push(`far future: ${far.teaserCards} teaser cards still present`);
if (far.teaserVisible !== 'hidden') problems.push('far future: teaser section should be hidden');
// Every listing, dated or not, should offer the Zillow link once all times pass.
if (far.zillowRows < allListings.length)
  problems.push(`far future: only ${far.zillowRows} of ${allListings.length} rows fell back to Zillow`);
// Only provable when the upcoming showings span more than one day.
if (futureDays.length > 1) {
  if (!(soon.datedRows < now.datedRows))
    problems.push(`day after ${futureDays[0]}: expected fewer than ${now.datedRows} dated rows, got ${soon.datedRows}`);
} else {
  console.log(`(only one day of upcoming open houses (${futureDays[0]}) - skipping the partial-expiry check)`);
}

await b.close(); srv.close();
console.log(problems.length ? '\nPROBLEMS:\n'+problems.join('\n') : '\nEXPIRY LOGIC OK');
process.exit(problems.length ? 1 : 0);
