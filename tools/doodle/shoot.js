// Screenshot a local page at an exact size, after its web fonts load (used by tools/doodle/doodle.py).
//   node tools/doodle/shoot.js <page.html> <out.png> <width> <height>
const path = require('path');
const root = path.resolve(__dirname, '..', '..');
const puppeteer = require(path.join(root, 'node_modules/puppeteer-core'));
const chrome = require(path.join(root, 'tools/chrome.js'));

(async () => {
  const [page, out, w, h] = process.argv.slice(2);
  const browser = await puppeteer.launch({ executablePath: chrome, args: ['--allow-file-access-from-files'] });
  try {
    const tab = await browser.newPage();
    await tab.setViewport({ width: +w, height: +h });
    await tab.goto('file://' + path.resolve(page), { waitUntil: 'networkidle0', timeout: 60000 });
    await tab.evaluate(() => document.fonts.ready);
    await new Promise((r) => setTimeout(r, 300));
    await tab.screenshot({ path: out });
  } finally {
    await browser.close();
  }
})().catch((e) => { console.error(e.message); process.exit(1); });
