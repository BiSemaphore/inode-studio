// Find frames where motion blur would print two different texts on top of each other.
//   node tools/check_blend.js <piece> [--landscape]
// render/encode.js blends the moments (2k-1)/60 and 2k/60 into output frame k. For every k this draws the page at both
// moments and compares the visible subtitle text and every [data-count] number; a difference means that frame shows a
// half-and-half ghost (the "39/32" counter and the doubled subtitle line, 2026-10-29). Exit 1 if any frame differs.
const path = require('path'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const { openPage } = require(path.join(root, 'explainer/frames/render/capture'));

(async () => {
  const args = process.argv.slice(2), landscape = args.includes('--landscape');
  const dir = path.resolve(root, args[0]);
  const page = [landscape ? 'page-linkedin.html' : 'page-instagram.html', 'page.html'].find((f) => fs.existsSync(path.join(dir, f)));
  const { browser, page: tab } = await openPage(dir, { landscape, dsf: 1, page });
  const bad = await tab.evaluate(() => {
    const seen = (t) => {
      window.renderFrame(t);
      const subs = [...document.querySelectorAll('.sub-bubble')].filter((b) => +getComputedStyle(b).opacity > 0.01)
        .map((b) => [...b.querySelectorAll('.sub-text span')].filter((s) => s.style.opacity !== '0' && !s.querySelector('span')).map((s) => s.textContent).join(' '));
      // every counter, visible or not: a ghost is the same counter showing two values (a fade-in is not a ghost)
      const nums = [...document.querySelectorAll('[data-count]')].map((e) => e.textContent);
      return subs.join(' | ') + ' || ' + nums.join(',');
    };
    const out = [], n = Math.floor(window.TOTAL * 30);
    for (let k = 1; k < n; k++) {
      const a = seen((2 * k - 1) / 60), b = seen((2 * k) / 60);
      if (a !== b) out.push([k, a, b]);
    }
    return out;
  });
  await browser.close();
  for (const [k, a, b] of bad) console.log(`frame ${k} (${(k / 30).toFixed(2)}s)\n  A: ${a}\n  B: ${b}`);
  console.log(`${args[0]}: ${bad.length} frames would blend two different texts`);
  process.exit(bad.length ? 1 : 0);
})().catch((e) => { console.error(e.message); process.exit(2); });
