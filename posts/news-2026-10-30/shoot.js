// Screenshot every <section class="s"> of <dir>/slides.html to <dir>/NN.png (1080x1350).  node shoot.js <dir> [<dir>...]
const path = require('path');
const puppeteer = require(path.resolve('node_modules/puppeteer-core')), chrome = require(path.resolve('tools/chrome.js'));
(async () => {
  const b = await puppeteer.launch({ executablePath: chrome }), p = await b.newPage();
  p.on('pageerror', (e) => console.error('page error:', e.message));
  await p.setViewport({ width: 1080, height: 1350 });
  for (const a of process.argv.slice(2)) {
    const dir = path.resolve(a);
    await p.goto('file://' + path.join(dir, 'slides.html'), { waitUntil: 'networkidle0' });
    await p.evaluate(() => document.fonts.ready);
    const s = await p.$$('section.s');
    for (let i = 0; i < s.length; i++) await s[i].screenshot({ path: path.join(dir, String(i + 1).padStart(2, '0') + '.png') });
    console.log(a, s.length);
  }
  await b.close();
})();
