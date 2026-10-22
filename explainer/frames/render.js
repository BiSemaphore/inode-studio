// Render a frames piece: page.html + voice/timings.json -> out/<name>.mp4 (30 fps, mixed audio).
//   node explainer/frames/render.js motion/<group>/<piece>            full render
//   node explainer/frames/render.js motion/<group>/<piece> 3.2 9 ...  stills -> out/still-<t>.png
//   AUDIO_ONLY=1 node explainer/frames/render.js motion/<group>/<piece>  remix the sound onto out/<name>.mp4
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
const root = path.resolve(__dirname, '../..');
const puppeteer = require(path.join(root, 'node_modules/puppeteer-core'));
const chrome = require(path.join(root, 'tools/chrome.js'));
const FPS = 30;   // Reels play at 30; a 60 fps upload gets half its frames thrown away

(async () => {
  const dir = path.resolve(process.argv[2]);
  const stills = process.argv.slice(3).map(Number);
  const name = path.basename(dir);
  fs.mkdirSync(path.join(dir, 'out'), { recursive: true });
  const timings = JSON.parse(fs.readFileSync(path.join(dir, 'voice/timings.json'), 'utf8'));
  const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new', args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exit(1); });
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.evaluateOnNewDocument((t) => { window.TIMINGS = t; }, timings.beats || timings);
  await page.goto('file://' + path.join(dir, 'page.html'), { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.MEASURE && window.MEASURE());   // circles need the real font metrics
  // wait until Chrome has painted the new frame: big zoomed canvases otherwise mix old and new tiles
  const settle = () => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(() => requestAnimationFrame(r), 40)))));
  const { total, end, cues } = await page.evaluate(() => ({ total: window.TOTAL, end: window.END, cues: window.CUES }));

  if (stills.length) {
    for (const t of stills) {
      await page.evaluate((x) => window.renderFrame(x), t);
      await settle();
      await page.screenshot({ path: path.join(dir, 'out', `still-${t}.png`) });
    }
    await browser.close();
    return;
  }
  fs.writeFileSync(path.join(dir, 'sfx.json'), JSON.stringify({ total, keys: cues.keys.map((k) => [k, 'key']), ticks: cues.ticks,
    pops: [], whooshes: [], misses: [], hits: [], chord: [end], thumps: [],
    draws: cues.draws, taps: cues.taps, brushes: cues.brushes, moves: cues.moves, cuts: cues.cuts, zooms: cues.zooms, checks: cues.checks, bed: 'ambient', kit: 'recorded' }));
  if (process.env.AUDIO_ONLY) {   // remix the soundtrack onto the existing video, no frames rendered
    execFileSync(path.join(root, '.venv/bin/python'), [path.join(root, 'explainer/mix.py'), dir], { stdio: 'inherit' });
    const out = path.join(dir, 'out', name + '.mp4'), tmp = out.replace(/\.mp4$/, '.remix.mp4');
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', out, '-i', path.join(dir, 'audio.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
      '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp]);
    fs.renameSync(tmp, out); await browser.close(); return;
  }
  execFileSync(path.join(root, '.venv/bin/python'), [path.join(root, 'explainer/mix.py'), dir], { stdio: 'inherit' });
  const out = path.join(dir, 'out', name + '.mp4');
  // Lossless PNG frames in; out comes a clean master for Instagram to re-encode: standard
  // (limited range, BT.709, tagged) colour, high bitrate, 2 s keyframes, AAC 48 kHz.
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-i', path.join(dir, 'audio.wav'), '-map', '0:v', '-map', '1:a',
    '-vf', 'scale=out_range=tv:out_color_matrix=bt709:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-maxrate', '16M', '-bufsize', '32M', '-profile:v', 'high', '-level', '4.2',
    '-x264-params', 'aq-mode=3:colorprim=bt709:transfer=bt709:colormatrix=bt709', '-g', String(FPS * 2),
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(total * FPS);
  // progress: out/render-progress.json (read by tools/render_status.py) and a line every 5%
  const prog = path.join(dir, 'out', 'render-progress.json'), t0 = Date.now();
  let lastPct = -1;
  const report = (f, state) => {
    const pct = Math.floor((f / n) * 100), secs = (Date.now() - t0) / 1000, eta = f ? secs / f * (n - f) : null;
    fs.writeFileSync(prog, JSON.stringify({ piece: name, frame: f, frames: n, pct, state, elapsed_s: Math.round(secs),
      eta_s: eta === null ? null : Math.round(eta), finish_at: eta === null ? null : new Date(Date.now() + eta * 1000).toLocaleTimeString() }));
    if (state === 'rendering' && pct >= lastPct + 5) { lastPct = pct - (pct % 5); console.log(`${name}: ${pct}% (${f}/${n} frames), about ${eta === null ? '?' : Math.round(eta / 60)} min left`); }
  };
  for (let f = 0; f < n; f++) {
    if (f % FPS === 0) report(f, 'rendering');
    await page.evaluate((x) => window.renderFrame(x), f / FPS);
    await settle();
    const png = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  report(n, 'encoding');
  await new Promise((r) => ff.on('close', r));
  report(n, 'done');
  await browser.close();
  console.log(out, total.toFixed(2) + 's');
})();
