// Snapshot a motion piece at given times (seconds) without recording the whole video.
// Usage: node tools/peek.js <piece.html> <outdir> <t1> [t2 ...]
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer-core');
const CHROME = require('./chrome');
(async () => {
  const [piece, outdir, ...times] = process.argv.slice(2);
  fs.mkdirSync(outdir, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(piece), { waitUntil: 'networkidle0' });
  const { width = 1080, height = 1350 } = await page.evaluate(() => window.MOTION);
  await page.setViewport({ width, height, deviceScaleFactor: 1 });
  await page.evaluate(() => document.fonts.ready);
  // Pieces that build their animations after loading fonts set MOTION.ready = false, then true.
  await page.waitForFunction(() => window.MOTION.ready !== false);
  const stage = await page.$('#stage');
  for (const t of times) {
    await page.evaluate((ms) => { for (const a of document.getAnimations()) { a.pause(); a.currentTime = ms; } }, parseFloat(t) * 1000);
    await stage.screenshot({ path: path.join(outdir, `t${t}.png`) });
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
