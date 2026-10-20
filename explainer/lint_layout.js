// Layout lint: for every camera shot, at its fullest moment (just before the
// camera moves on), check that no text is cut by the frame, sits under the
// subtitle band or the watermark, or overlaps other text.
// Usage: node explainer/lint_layout.js motion/<piece>      (exit 1 on problems)
const path = require('path');
const puppeteer = require('puppeteer-core');
const CHROME = require('../tools/chrome');
let W = 1920, H = 1080, SUB_TOP = H - 130;

(async () => {
  const dir = path.resolve(process.argv[2]);
  const b = await puppeteer.launch({ executablePath: CHROME, headless: true });
  const p = await b.newPage();
  await p.setViewport({ width: W, height: H });
  await p.goto('file://' + path.join(dir, 'piece.html'), { waitUntil: 'networkidle0' });
  await p.waitForFunction(() => window.MOTION.ready === true);
  ({ W, H } = await p.evaluate(() => ({ W: window.MOTION.width, H: window.MOTION.height })));
  await p.setViewport({ width: W, height: H });
  SUB_TOP = H - (await p.evaluate(() => parseFloat(getComputedStyle(document.getElementById('subtitles')).bottom) || 56)) - 74;
  const { cams, total } = await p.evaluate(() => ({ cams: window.STORY.cams, total: window.STORY.total }));
  const problems = [];
  for (let i = 0; i < cams.length; i++) {
    const settled = cams[i].at + (cams[i].dur || 1.2);
    const t = i + 1 < cams.length ? cams[i + 1].at - 0.05 : total - 4.5;
    if (t <= settled) continue;
    const found = await p.evaluate((ms, W, H, SUB_TOP) => {
      for (const a of document.getAnimations()) { a.pause(); a.currentTime = ms; }
      const vis = (el) => {
        for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
          const cs = getComputedStyle(e);
          if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
          if (e.id === 'endcard' || e.id === 'introcard') return false;
        }
        return true;
      };
      const items = [];
      const add = (el, kind, label) => {
        if (!vis(el)) return;
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return;
        if (r.right < 0 || r.left > W || r.bottom < 0 || r.top > H) return;   // another shot
        items.push({ kind, label: label.slice(0, 40), x0: r.left, y0: r.top, x1: r.right, y1: r.bottom });
      };
      document.querySelectorAll('#world text').forEach((e) => add(e, 'text', e.textContent));
      document.querySelectorAll('#world .term').forEach((e) => add(e, 'terminal', (e.querySelector('.ln') || {}).textContent || 'terminal'));
      document.querySelectorAll('#world .dlabel').forEach((e) => add(e, 'label', e.textContent));
      const el = document.getElementById('watermark');   // absent when brand.json has no logo
      const wm = el ? el.getBoundingClientRect() : { left: 0, right: 0, top: 0, bottom: 0 };
      const subOn = [...document.querySelectorAll('#subtitles .w')].some((w) => getComputedStyle(w).visibility === 'visible');
      const out = [];
      for (const it of items) {
        if (it.x0 < -1 || it.y0 < -1 || it.x1 > W + 1 || it.y1 > H + 1) out.push(`${it.kind} "${it.label}" is cut by the frame`);
        if (subOn && it.y1 > SUB_TOP && it.x1 > W * 0.2 && it.x0 < W * 0.8) out.push(`${it.kind} "${it.label}" is under the subtitles`);
        if (it.x1 > wm.left && it.x0 < wm.right && it.y1 > wm.top && it.y0 < wm.bottom) out.push(`${it.kind} "${it.label}" is under the watermark`);
      }
      const texts = items.filter((i) => i.kind !== 'terminal');
      for (let a = 0; a < texts.length; a++) for (let c = a + 1; c < texts.length; c++) {
        const A = texts[a], C = texts[c];
        const ix = Math.min(A.x1, C.x1) - Math.max(A.x0, C.x0), iy = Math.min(A.y1, C.y1) - Math.max(A.y0, C.y0);
        if (ix <= 0 || iy <= 0) continue;
        const small = Math.min((A.x1 - A.x0) * (A.y1 - A.y0), (C.x1 - C.x0) * (C.y1 - C.y0));
        if (ix * iy > 0.15 * small) out.push(`"${A.label}" overlaps "${C.label}"`);
      }
      return out;
    }, t * 1000, W, H, SUB_TOP);
    found.forEach((f) => problems.push(`shot ${i + 1} at ${t.toFixed(1)}s: ${f}`));
  }
  problems.forEach((x) => console.log('  ' + x));
  console.log(`layout: ${cams.length} shots checked, ${problems.length} problem(s)`);
  await b.close();
  process.exit(problems.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
