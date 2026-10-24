// Chrome side: open a piece's page in headless Chrome and turn a time into a PNG frame.
// Every frame is a pure function of its time (window.renderFrame(t) from runtime.js), so any range can be
// drawn by any Chrome and the frames are the same.
const path = require('path'), fs = require('fs');
const root = path.resolve(__dirname, '../../..');
const puppeteer = require(path.join(root, 'node_modules/puppeteer-core'));
const chrome = require(path.join(root, 'tools/chrome.js'));
const { times } = require('./encode');

// Wait after drawing, before the screenshot (tested 2026-10-24 against frames from the full wait, 120-frame runs on a
// card swipe and a notebook zoom): 'full' (2 frames + 40 ms + 1 frame) is the default, proven; 'raf2' (2 frames)
// matched in 6 of 6 runs and is about 10% faster; 'raf' (1 frame) broke 12 frames in 1 run of 4; 'none' breaks
// frames every time (zoomed canvases mix old and new tiles). Override with SETTLE=raf2 only after re-testing.
const SETTLE = process.env.SETTLE || 'full';

// cfg: { landscape, dsf }. Returns { browser, page, frame(t) -> PNG buffer, settle(), prof }.
async function openPage(dir, cfg) {
  const timings = JSON.parse(fs.readFileSync(path.join(dir, 'voice/timings.json'), 'utf8'));
  const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new', args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exit(1); });
  await page.setViewport(cfg.landscape ? { width: 1920, height: 1080, deviceScaleFactor: cfg.dsf } : { width: 1080, height: 1920, deviceScaleFactor: cfg.dsf });
  await page.evaluateOnNewDocument((t) => { window.TIMINGS = t; }, timings.beats || timings);
  await page.goto('file://' + path.join(dir, 'page.html'), { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.MEASURE && window.MEASURE());   // circles need the real font metrics
  const settle = () => page.evaluate((mode) => new Promise((r) => mode === 'none' ? r() : mode === 'raf' ? requestAnimationFrame(() => r())
    : mode === 'raf2' ? requestAnimationFrame(() => requestAnimationFrame(() => r()))
    : requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(() => requestAnimationFrame(r), 40)))), SETTLE);
  // per-stage time, summed over frames (ms); optimizeForSpeed only lowers PNG compression effort, same pixels
  const prof = { draw: 0, settle: 0, shot: 0, encode: 0, n: 0 }, now = () => performance.now();
  const frame = async (t) => {
    const a = now(); await page.evaluate((x) => window.renderFrame(x), t);
    const b = now(); await settle();
    const c = now(); const png = await page.screenshot({ type: 'png', optimizeForSpeed: true });
    prof.draw += b - a; prof.settle += c - b; prof.shot += now() - c; prof.n++;
    return png;
  };
  // what can be seen at time t, as a short hash (FNV-1a): the head (styles), the body's attributes, and the full
  // markup of every visible top-level layer (elements, inline styles, text); a hidden layer counts only as hidden,
  // so editing one card changes only the frames that show it. Same fingerprint, same engine files and settings,
  // same pixels: a cached chunk can be reused.
  const fingerprint = (t) => page.evaluate((x) => {
    window.renderFrame(x);
    let s = document.head.outerHTML + [...document.body.attributes].map((a) => a.name + '=' + a.value).join(' ');
    for (const el of document.body.children) {
      const cs = getComputedStyle(el);
      s += cs.display === 'none' || cs.opacity === '0' ? '<hidden ' + el.tagName + '>' : el.outerHTML;
    }
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return h.toString(36) + '.' + s.length.toString(36);
  }, t);
  return { browser, page, frame, settle, prof, fingerprint };
}

// draw output frames [a, b) into ffmpeg's stdin; onFrame(output frames done) as it goes
async function renderRange(frame, a, b, ff, onFrame, blur, prof) {
  const ts = times(a, b, blur), per = blur ? 2 : 1;
  for (let k = 0; k < ts.length; k++) {
    const png = await frame(ts[k]);
    const w0 = performance.now();
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
    if (prof) prof.encode += performance.now() - w0;   // time spent waiting for ffmpeg
    if ((k + 1) % per === 0) onFrame((k + 1) / per);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
}

const profileLine = (prof, ms0, label) => {
  const ms = (x) => Math.round(x / prof.n);
  return `profile ${label}: ${prof.n} frames, ${Math.round((performance.now() - ms0) / prof.n)} ms/frame = draw ${ms(prof.draw)} + settle ${ms(prof.settle)}` +
    ` + screenshot ${ms(prof.shot)} + wait for encoder ${ms(prof.encode)} (SETTLE=${SETTLE})`;
};

module.exports = { openPage, renderRange, profileLine };
