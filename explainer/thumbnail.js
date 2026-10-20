// Thumbnail for an explainer: a real frame of the video (no subtitles), on a
// 4:5 canvas at the video's width, the video's title above (in the board's
// handwriting, with an optional plain line under it), the logo from
// brand.json below (none when brand.json has no logo).
// Everything sits in a 16:9 block (the video's ratio) centred on the 4:5
// canvas; above and below is blank black (OUTSIDE colour, default #000000).
// Usage: [OUTSIDE=#ffffff] node explainer/thumbnail.js motion/<piece>/piece.html <seconds> <out.png> "<title>" ["<line>"]
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer-core');
const CHROME = require('../tools/chrome');
const { ROOT: STUDIO, load, lockup } = require('../tools/brand');
const OUTSIDE = process.env.OUTSIDE || '#000000';

(async () => {
  const [piece, seconds, out, title = '', line = ''] = process.argv.slice(2);
  const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--run-all-compositor-stages-before-draw'] });
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(piece), { waitUntil: 'networkidle0' });
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
  await page.waitForFunction(() => window.MOTION.ready === true);
  // The lockup goes below the frame, so the in-video watermark is hidden here.
  // White paper without the dot grid, so the frame sits on the white canvas seamlessly.
  await page.addStyleTag({ content: '#subtitles, #watermark { display: none !important; } #stage { background: #ffffff !important; }' });
  await page.evaluate((ms) => { for (const a of document.getAnimations()) { a.pause(); a.currentTime = ms; } return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); }, parseFloat(seconds) * 1000);
  const frame = await (await page.$('#stage')).screenshot({ encoding: 'base64' });

  const logo = lockup(load(), (f) => 'file://' + path.join(STUDIO, f));
  await page.setViewport({ width: 1920, height: 2400, deviceScaleFactor: 1 });
  await page.setContent(`<!doctype html><html><head><style>
    @font-face { font-family: "Virgil"; src: url("file://${path.join(STUDIO, 'fonts/Virgil.woff2')}") format("woff2"); }
    @font-face { font-family: "Overused Grotesk"; src: url("file://${path.join(STUDIO, 'fonts/OverusedGrotesk-SemiBold.woff2')}") format("woff2"); font-weight: 600; }
    html, body { margin: 0; background: ${OUTSIDE}; }
    #canvas { position: relative; width: 1920px; height: 2400px; background: ${OUTSIDE}; display: flex; align-items: center; }
    /* The 16:9 block: title, frame and lockup with equal gaps inside it. */
    #band { width: 1920px; height: 1080px; background: #ffffff; display: flex; flex-direction: column;
      align-items: center; justify-content: space-evenly; box-sizing: border-box; padding: 20px 0; }
    #frame { height: 640px; display: block; }
    #head { display: flex; flex-direction: column; align-items: center; gap: 12px; }
    #head h1 { margin: 0; font: 400 76px/1.1 "Virgil"; color: #1e1e1e; text-align: center; }
    #head p { margin: 0; font: 600 32px "Overused Grotesk", sans-serif; color: #6c717a; }
    /* Same lockup as explainer/style.css. */
    .lockup { font-size: 46px; display: flex; align-items: center; gap: 0.3em; }
    .logo-mark { height: 1.6em; }
    .logo-word { height: 1em; }
  </style></head><body><div id="canvas"><div id="band">
    <div id="head">${title ? `<h1>${esc(title)}</h1>` : ''}${line ? `<p>${esc(line)}</p>` : ''}</div>
    <canvas id="frame"></canvas>
    ${logo}
  </div></div></body></html>`, { waitUntil: 'load' });
  // Crop the frame to its drawing (plus a margin) so the empty band where
  // subtitles sit does not unbalance the spacing; shown 1720 px wide so it
  // stays inside Instagram's 3:4 grid crop.
  await page.evaluate(async (src) => {
    const img = new Image();
    img.src = src;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const g = c.getContext('2d');
    g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, c.width, c.height).data;
    let x0 = c.width, y0 = c.height, x1 = 0, y1 = 0;
    for (let y = 0; y < c.height; y += 2) for (let x = 0; x < c.width; x += 2) {
      const i = (y * c.width + x) * 4;
      if (d[i] < 235 || d[i + 1] < 235 || d[i + 2] < 235) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    }
    const m = 60;
    x0 = Math.max(0, x0 - m); y0 = Math.max(0, y0 - m); x1 = Math.min(c.width, x1 + m); y1 = Math.min(c.height, y1 + m);
    const out = document.getElementById('frame');
    out.width = x1 - x0; out.height = y1 - y0;
    out.getContext('2d').drawImage(img, x0, y0, x1 - x0, y1 - y0, 0, 0, x1 - x0, y1 - y0);
  }, 'data:image/png;base64,' + frame);
  await page.evaluate(() => document.fonts.ready);
  await (await page.$('#canvas')).screenshot({ path: out });
  await browser.close();
  console.log('thumbnail ->', out);
})().catch((e) => { console.error(e); process.exit(1); });
