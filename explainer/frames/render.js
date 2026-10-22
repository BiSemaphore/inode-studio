// Render a frames piece: page.html + voice/timings.json -> out/<name>.mp4 (30 fps, mixed audio).
//   node explainer/frames/render.js motion/<group>/<piece>                 full render, one Chrome
//   node explainer/frames/render.js motion/<group>/<piece> --workers 3     full render, frames split over 3 Chromes
//   ... --blur                                                             draw at 60 fps, blend pairs into 30 (motion blur)
//   node explainer/frames/render.js motion/<group>/<piece> 3.2 9 ...       stills -> out/still-<t>.png
//   AUDIO_ONLY=1 node explainer/frames/render.js motion/<group>/<piece>    remix the sound onto out/<name>.mp4
// Every frame is a pure function of its time, so workers render contiguous frame ranges into
// video-only segments with the same encoder settings; the segments are joined without re-encoding.
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
const root = path.resolve(__dirname, '../..');
const puppeteer = require(path.join(root, 'node_modules/puppeteer-core'));
const chrome = require(path.join(root, 'tools/chrome.js'));
const FPS = 30;   // Reels play at 30; a 60 fps upload gets half its frames thrown away

// Lossless PNG frames in; out comes a clean master for Instagram to re-encode: standard
// (limited range, BT.709, tagged) colour, high bitrate, 2 s keyframes.
// With blur, frames are drawn at 60 fps and each output frame blends two of them (motion blur),
// so zooms and pens move smoothly; anything still is unchanged by the blend.
const SCALE = 'scale=out_range=tv:out_color_matrix=bt709:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p';
const BLEND = "tmix=frames=2:weights='1 1',select='mod(n\\,2)',setpts=N/(30*TB),";
const vf = (blur) => ['-vf', (blur ? BLEND : '') + SCALE];
const ENCODE = [
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-maxrate', '16M', '-bufsize', '32M', '-profile:v', 'high', '-level', '4.2',
  '-x264-params', 'aq-mode=3:colorprim=bt709:transfer=bt709:colormatrix=bt709', '-g', String(FPS * 2),
  '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'];
const AUDIO_ARGS = ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000'];
const pngIn = (blur) => ['-f', 'image2pipe', '-framerate', String(blur ? 2 * FPS : FPS), '-c:v', 'png', '-i', '-'];
const VIDEO_ARGS = (blur) => [...vf(blur), ...ENCODE];
// the times to draw for output frames [a, b): one each, or with blur the 60 fps pair behind each one
const times = (a, b, blur) => blur
  ? [...Array(2 * (b - a)).keys()].map((k) => Math.max(0, 2 * a - 1 + k) / (2 * FPS))
  : [...Array(b - a).keys()].map((k) => (a + k) / FPS);

async function openPage(dir) {
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
  // optimizeForSpeed only lowers PNG compression effort; the pixels are identical (checked)
  const frame = async (t) => { await page.evaluate((x) => window.renderFrame(x), t); await settle(); return page.screenshot({ type: 'png', optimizeForSpeed: true }); };
  return { browser, page, frame, settle };
}

// output frames [a, b) into ffmpeg; onFrame(output frames done) as it goes
async function renderRange(frame, a, b, ff, onFrame, blur) {
  const ts = times(a, b, blur), per = blur ? 2 : 1;
  for (let k = 0; k < ts.length; k++) {
    const png = await frame(ts[k]);
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((k + 1) % per === 0) onFrame((k + 1) / per);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
}

function progress(dir, name, n) {
  const prog = path.join(dir, 'out', 'render-progress.json'), t0 = Date.now();
  let lastPct = -1;
  return (f, state, workers) => {
    const pct = Math.floor((f / n) * 100), secs = (Date.now() - t0) / 1000, eta = f ? secs / f * (n - f) : null;
    fs.writeFileSync(prog, JSON.stringify({ piece: name, frame: f, frames: n, pct, state, workers: workers || 1, elapsed_s: Math.round(secs),
      eta_s: eta === null ? null : Math.round(eta), finish_at: eta === null ? null : new Date(Date.now() + eta * 1000).toLocaleTimeString() }));
    if (state === 'rendering' && pct >= lastPct + 5) { lastPct = pct - (pct % 5); console.log(`${name}: ${pct}% (${f}/${n} frames), about ${eta === null ? '?' : Math.round(eta / 60)} min left`); }
  };
}

(async () => {
  const args = process.argv.slice(2), dir = path.resolve(args[0]), name = path.basename(dir);
  const flag = (k) => { const i = args.indexOf(k); return i < 0 ? null : args[i + 1]; };
  fs.mkdirSync(path.join(dir, 'out'), { recursive: true });

  // worker: one frame range into a video-only segment; reports "F <done>" lines to the parent
  const seg = flag('--segment');
  if (seg) {
    const [a, b, file] = seg.split(':');
    const { browser, frame } = await openPage(dir);
    const blur = args.includes('--blur');
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', ...pngIn(blur), ...VIDEO_ARGS(blur), '-an', file], { stdio: ['pipe', 'inherit', 'inherit'] });
    await renderRange(frame, +a, +b, ff, (k) => { if (k % 10 === 0 || +a + k === +b) process.stdout.write(`F ${k}\n`); }, blur);
    // the segment is written; closing Chrome can hang, so give it a moment and then leave
    await Promise.race([browser.close(), new Promise((r) => setTimeout(r, 5000))]);
    process.exit(0);
  }

  const workers = Math.max(1, +(flag('--workers') || 1)), blur = args.includes('--blur');
  const stills = args.slice(1).filter((x, i, all) => !x.startsWith('--') && !(all[i - 1] || '').startsWith('--')).map(Number);
  const { browser, page, frame, settle } = await openPage(dir);
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
  execFileSync(path.join(root, '.venv/bin/python'), [path.join(root, 'explainer/mix.py'), dir], { stdio: 'inherit' });
  const out = path.join(dir, 'out', name + '.mp4'), audio = path.join(dir, 'audio.wav');
  if (process.env.AUDIO_ONLY) {   // remix the soundtrack onto the existing video, no frames rendered
    const tmp = out.replace(/\.mp4$/, '.remix.mp4');
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', out, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
      ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart', tmp]);
    fs.renameSync(tmp, out); await browser.close(); return;
  }
  const n = Math.round(total * FPS), report = progress(dir, name, n);

  if (workers === 1) {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', ...pngIn(blur), '-i', audio, '-map', '0:v', '-map', '1:a', ...VIDEO_ARGS(blur),
      ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    report(0, 'rendering');
    await renderRange(frame, 0, n, ff, (k) => { if (k % FPS === 0) report(k, 'rendering'); }, blur);
    report(n, 'done');
    await browser.close();
    console.log(out, total.toFixed(2) + 's');
    return;
  }

  // parallel: equal contiguous ranges, one Chrome each; then join the segments and add the sound
  await browser.close();
  const segDir = path.join(dir, 'out', 'segments');
  fs.mkdirSync(segDir, { recursive: true });
  const ranges = [...Array(workers)].map((_, i) => [Math.round((n * i) / workers), Math.round((n * (i + 1)) / workers)]);
  const done = ranges.map(() => 0);
  report(0, 'rendering', workers);
  const codes = await Promise.all(ranges.map(([a, b], i) => new Promise((resolve) => {
    const file = path.join(segDir, `seg-${i}.mp4`);
    const child = spawn(process.execPath, [__filename, dir, '--segment', `${a}:${b}:${file}`, ...(blur ? ['--blur'] : [])], { stdio: ['ignore', 'pipe', 'inherit'] });
    let buf = '';
    child.stdout.on('data', (d) => {
      buf += d; const lines = buf.split('\n'); buf = lines.pop();
      for (const l of lines) if (l.startsWith('F ')) { done[i] = +l.slice(2); report(done.reduce((x, y) => x + y, 0), 'rendering', workers); }
    });
    child.on('close', resolve);
  })));
  if (codes.some((c) => c !== 0)) { console.error('a worker failed:', codes); process.exit(1); }
  report(n, 'joining', workers);
  const list = path.join(segDir, 'list.txt');
  fs.writeFileSync(list, ranges.map((_, i) => `file '${path.join(segDir, `seg-${i}.mp4`)}'`).join('\n') + '\n');
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-i', audio, '-map', '0:v', '-map', '1:a',
    '-c:v', 'copy', ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart', out]);
  fs.rmSync(segDir, { recursive: true, force: true });
  report(n, 'done', workers);
  console.log(out, total.toFixed(2) + 's', `(${workers} workers${blur ? ', 60 fps blended to 30' : ''})`);
})();
