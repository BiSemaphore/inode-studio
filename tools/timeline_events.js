// Every real tween of a HyperFrames film, as GSAP built it at run time (times computed from the voice included).
//   node tools/timeline_events.js motion/<topic>/<part> [composition=film]
// Loads compositions/<composition>.html in headless Chrome, walks window.__timelines[<composition>], and writes
// <piece>/sound/timeline.json: [{"target": "#id", "start": s, "duration": d, "ease": "expo.out"}], one row per
// target element with an id. tools/sound_mix.py places every "on" cue from this file.
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');
const CHROME = require('./chrome');

(async () => {
  const piece = path.resolve(process.argv[2]);
  const comp = process.argv[3] || 'film';
  const src = fs.readFileSync(path.join(piece, 'compositions', `${comp}.html`), 'utf8');
  const inner = src.slice(src.indexOf('<template>') + 10, src.lastIndexOf('</template>'));
  const gsapTag = (fs.readFileSync(path.join(piece, 'index.html'), 'utf8').match(/<script src="[^"]*gsap[^"]*"><\/script>/) || [])[0];
  const probe = path.join(piece, '.hyperframes', 'timeline-probe.html');
  fs.mkdirSync(path.dirname(probe), { recursive: true });
  fs.writeFileSync(probe, `<!doctype html><html><head><base href="../">${gsapTag}</head><body><script>window.__timelines = {};</script>${inner}</body></html>`);
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('file://' + probe, { waitUntil: 'load' });
  const rows = await page.evaluate((comp) => {
    const tl = window.__timelines[comp];
    if (!tl) return null;
    const out = [];
    for (const t of tl.getChildren(true, true, false)) {
      const ease = typeof t.vars.ease === 'string' ? t.vars.ease : (t.vars.ease ? 'custom' : 'power1.out');
      for (const el of t.targets()) {
        if (el && el.id) out.push({ target: '#' + el.id, start: +t.startTime().toFixed(4), duration: +t.duration().toFixed(4), ease });
      }
    }
    return out.sort((a, b) => a.start - b.start);
  }, comp);
  await browser.close();
  fs.unlinkSync(probe);
  if (!rows) { console.error(`no timeline "${comp}"`, errors.join('\n')); process.exit(1); }
  const out = path.join(piece, 'sound', 'timeline.json');
  fs.writeFileSync(out, JSON.stringify(rows, null, 1));
  console.log(`${rows.length} tweens on ids -> ${path.relative(process.cwd(), out)}` + (errors.length ? `\npage errors: ${errors.join('; ')}` : ''));
})();
