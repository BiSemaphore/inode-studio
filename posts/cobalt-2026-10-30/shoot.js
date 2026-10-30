// Screenshot each <section class="post"> of posts.html to <id>.png (1080x1350).  node posts/<dir>/shoot.js posts/<dir>
const path = require('path');
const puppeteer = require(path.resolve('node_modules/puppeteer-core')), chrome = require(path.resolve('tools/chrome.js'));
(async () => {
  const dir = path.resolve(process.argv[2]), b = await puppeteer.launch({ executablePath: chrome }), p = await b.newPage();
  p.on('pageerror', (e) => console.error('page error:', e.message));
  await p.setViewport({ width: 1080, height: 1350 });
  await p.goto('file://' + path.join(dir, 'posts.html'), { waitUntil: 'networkidle0' });
  await p.evaluate(() => document.fonts.ready);
  for (const s of await p.$$('section.post')) { const id = await s.evaluate((e) => e.id); await s.screenshot({ path: path.join(dir, `post-${id}.png`) }); }
  await b.close();
})();
