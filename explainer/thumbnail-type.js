// Typographic thumbnail (Instagram Reel cover): the title set as the image,
// plus the logo from brand.json, nothing else. 1080x1920 (9:16, the Reel
// cover size), a white 16:9 block (the video's ratio) in the middle, blank
// black above and below. Everything sits inside the block, which is inside
// every crop Instagram applies: 9:16 Reel, 4:5 feed, 3:4 profile grid.
//
// Composition: one left margin shared by headline and lockup (a single grid
// line), the headline in two lines at display size with tight leading and
// tracking, ending in a round dot in the brand colour; the lockup sits on
// the bottom margin. Colours: brand.json "colors" brand-ink and brand-dot.
// FORMAT=landscape gives a 1920x1080 cover (LinkedIn, YouTube: the video's
// 16:9 shape), letterboxed: black bars top and bottom, white block between.
// Usage: [FORMAT=landscape] node explainer/thumbnail-type.js <out.png> "<line 1>" "<line 2>"
const path = require('path');
const fs = require('fs');
const os = require('os');
const puppeteer = require('puppeteer-core');
const CHROME = require('../tools/chrome');
const { ROOT: STUDIO, load, lockup } = require('../tools/brand');
const OUTSIDE = process.env.OUTSIDE || '#000000';
const BRAND = load();
const BLUE = (BRAND.colors || {})['brand-dot'] || '#00a6fb';   // the headline's closing dot
const NAVY = (BRAND.colors || {})['brand-ink'] || '#003554';   // the headline ink

(async () => {
  const [out, l1, l2] = process.argv.slice(2);
  const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const f = (n) => 'file://' + path.join(STUDIO, n);
  const html = `<!doctype html><html><head><style>
    @font-face { font-family: "Overused Grotesk"; src: url("${f('fonts/OverusedGrotesk-Bold.woff2')}") format("woff2"); font-weight: 700; }
    html, body { margin: 0; background: ${OUTSIDE}; }
    #canvas { width: 1080px; height: 1920px; background: ${OUTSIDE}; display: flex; align-items: center; }
    /* 1080 x 607.5 is exactly 16:9, so the landscape export is exactly 1920x1080. */
    #band { position: relative; width: 1080px; height: 607.5px; background: #fff; }
    /* Landscape (LinkedIn, YouTube): the video's 16:9 at 1920x1080, letterboxed:
       black bars top and bottom, a wide white block (1920x810) in the middle. */
    body.landscape #canvas { width: 1920px; height: 1080px; }
    body.landscape #band { width: 1920px; height: 810px; }
    body.landscape h1 { left: 140px; top: 110px; font-size: 210px; }
    body.landscape .lockup { left: 145px; bottom: 120px; font-size: 40px; }
    h1 { position: absolute; left: 76px; top: 84px; margin: 0;
      font: 700 128px/0.9 "Overused Grotesk", sans-serif; letter-spacing: -0.045em; color: ${NAVY}; }
    /* A round dot like the logo's (the font's own full stop is square), on the baseline. */
    h1 .dot { display: inline-block; width: 0.17em; height: 0.17em; border-radius: 50%; background: ${BLUE}; margin-left: 0.04em; }
    .lockup { position: absolute; left: 79px; bottom: 84px; font-size: 26px; display: flex; align-items: center; gap: 0.3em; }
    .logo-mark { height: 1.6em; }
    .logo-word { height: 1em; }
  </style></head><body><div id="canvas"><div id="band">
    <h1>${esc(l1)}<br>${esc(l2)}<span class="dot"></span></h1>
    ${lockup(BRAND, f)}
  </div></div></body></html>`;
  // Loaded from a file:// page so local fonts and logo files are allowed.
  const tmp = path.join(os.tmpdir(), `thumb-${process.pid}.html`);
  fs.writeFileSync(tmp, html);
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
  const page = await browser.newPage();
  // Reel cover at 1x (1080 wide). Landscape: the block alone, drawn at
  // 1920/1080 scale so it comes out at exactly 1920x1080.
  const landscape = process.env.FORMAT === 'landscape';
  await page.setViewport(landscape ? { width: 1920, height: 1080, deviceScaleFactor: 1 } : { width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto('file://' + tmp, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  // Report the headline box so the composition can be checked, not eyeballed.
  const box = await page.evaluate(() => { const r = document.querySelector('h1').getBoundingClientRect(); const b = document.getElementById('band').getBoundingClientRect(); return { left: r.left, right: r.right, top: r.top - b.top, bottom: r.bottom - b.top }; });
  console.log('headline box in band', JSON.stringify(box));
  if (landscape) {
    await page.evaluate(() => document.body.classList.add('landscape'));
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
  } else {
    await (await page.$('#canvas')).screenshot({ path: out });
  }
  await browser.close();
  fs.rmSync(tmp);
  console.log('thumbnail ->', out);
})().catch((e) => { console.error(e); process.exit(1); });
