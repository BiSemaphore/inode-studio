// Sync check: every typed character must appear on the frame of its key
// sound, and not one frame earlier; every key sound must belong to a
// character. Usage: node explainer/check_sync.js motion/<piece>
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer-core');
const CHROME = require('../tools/chrome');

(async () => {
  const dir = path.resolve(process.argv[2]);
  const sfx = JSON.parse(fs.readFileSync(path.join(dir, 'sfx.json')));
  const keyTimes = sfx.keys.filter((k) => k[1] !== 'enter').map((k) => k[0]).sort((a, b) => a - b);
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true });
  const p = await b.newPage();
  await p.goto('file://' + path.join(dir, 'piece.html'), { waitUntil: 'networkidle0' });
  await p.waitForFunction(() => window.MOTION.ready === true);
  const fps = await p.evaluate(() => window.MOTION.fps);
  // Typed characters: lines with per-character spans, in story order.
  const chars = await p.evaluate(() => {
    const out = [];
    window.STORY.ops.filter((o) => o.kind === 'block').forEach((o) => (o.lines || []).forEach((ln) => {
      if (!ln.times) return;
      for (let k = ln.prompt || 0; k < ln.text.length; k++) out.push(ln.times[k]);
    }));
    return out;
  });
  const seek = (ms) => p.evaluate((ms) => { for (const a of document.getAnimations()) { a.pause(); a.currentTime = ms; } }, ms);
  const spans = await p.$$('.term .ln span');
  let bad = 0, checked = 0;
  const visible = (el) => p.evaluate((e) => getComputedStyle(e).visibility === 'visible', el);
  // spans include prompt characters; map by their own animation start
  for (const el of spans) {
    const t = await p.evaluate((e) => { const a = e.getAnimations()[0]; return a ? a.effect.getTiming().delay / 1000 + 0.004 : null; }, el);
    if (t === null) continue;
    const f = Math.round(t * fps);
    await seek((f / fps) * 1000); const on = await visible(el);
    await seek(((f - 1) / fps) * 1000); const before = await visible(el);
    checked++;
    if (!on || (before && f > 0)) { bad++; if (bad < 10) console.log(`char at ${t.toFixed(3)}s: frame ${f} visible=${on}, frame ${f - 1} visible=${before}`); }
  }
  // Every key sound must coincide with a typed character's frame.
  const charFrames = new Set(chars.map((t) => Math.round(t * fps)));
  const orphan = keyTimes.filter((t) => !charFrames.has(Math.round(t * fps)) || Math.abs(t * fps - Math.round(t * fps)) > 1e-3);
  console.log(`${checked} characters checked, ${bad} off-frame; ${keyTimes.length} key sounds, ${orphan.length} not on a character frame`);
  await b.close();
  process.exit(bad || orphan.length ? 1 : 0);
})();
