// Render a frames piece: page.html + voice/timings.json -> out/<name>.mp4 (30 fps, mixed audio).
//   node explainer/frames/render.js motion/<group>/<piece>                 full render, one Chrome
//   node explainer/frames/render.js motion/<group>/<piece> --workers 3     full render, frames split over 3 Chromes
//   ... --blur                                                             draw at 60 fps, blend pairs into 30 (motion blur)
//   node explainer/frames/render.js motion/<group>/<piece> 3.2 9 ...       stills -> out/still-<t>.png
//   ... --scale=2                                                          draw at 2x: <name>-master.mp4 (2x) + <name>.mp4 (shrunk, cleaner)
//   ... --landscape                                                        1920x1080 (16:9) for LinkedIn -> out/<name>-landscape.mp4
//   AUDIO_ONLY=1 node explainer/frames/render.js motion/<group>/<piece>    remix the sound onto out/<name>.mp4
// Every frame is a pure function of its time, so workers render contiguous frame ranges into
// video-only segments with the same encoder settings; the segments are joined without re-encoding.
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
const root = path.resolve(__dirname, '../..');
const puppeteer = require(path.join(root, 'node_modules/puppeteer-core'));
const chrome = require(path.join(root, 'tools/chrome.js'));
const FPS = 30;   // Reels play at 30; a 60 fps upload gets half its frames thrown away
const LANDSCAPE = process.argv.includes('--landscape');   // 1440x1080 (LinkedIn 4:3); the page's CSS lays itself out
// --scale=2: frames are drawn at 2x. One ffmpeg run writes the master at that size (<name>-master.mp4,
// 2160x3840 or 2880x2160) and the delivery file shrunk from the same frames (<name>.mp4), so nothing is
// compressed twice. The delivery file is cleaner than a 1x render; the master stays sharp when zoomed.
const DSF = +((process.argv.find((a) => a.startsWith('--scale=')) || '=1').split('=')[1]);
const W = LANDSCAPE ? 1920 : 1080, H = LANDSCAPE ? 1080 : 1920;   // LinkedIn landscape is 16:9

// Lossless PNG frames in; out comes a clean master for Instagram to re-encode: standard
// (limited range, BT.709, tagged) colour, high bitrate, 2 s keyframes.
// With blur, frames are drawn at 60 fps and each output frame blends two of them (motion blur),
// so zooms and pens move smoothly; anything still is unchanged by the blend.
const SCALE = 'scale=out_range=tv:out_color_matrix=bt709:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p';
const BLEND = "tmix=frames=2:weights='1 1',select='mod(n\\,2)',setpts=N/(30*TB),";
const vf = (blur) => ['-vf', (blur ? BLEND : '') + SCALE];
const AUDIO_ARGS = ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000'];
// tune animation: flat colour and hard edges (more B-frames, softer deblocking)
const enc = (maxrate, level) => [
  '-c:v', 'libx264', '-preset', 'slow', '-tune', 'animation', '-crf', '14', '-maxrate', maxrate, '-bufsize', 2 * parseInt(maxrate) + 'M',
  '-profile:v', 'high', '-level', level,
  '-x264-params', 'aq-mode=3:colorprim=bt709:transfer=bt709:colormatrix=bt709', '-g', String(FPS * 2),
  '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'];
const ENCODE = enc('16M', '4.2'), ENCODE_MASTER = enc('40M', '5.1');
const masterOf = (file) => file.replace(/\.mp4$/, '-master.mp4');
// output options after the inputs: one file, or with --scale the delivery file plus the master
function outputs(blur, out, withAudio) {
  const a = withAudio ? ['-map', '1:a', ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart'] : ['-an'];
  if (DSF === 1) return [...(withAudio ? ['-map', '0:v'] : []), ...vf(blur), ...ENCODE, ...a, out];
  const fc = `[0:v]${blur ? BLEND : ''}split=2[d][m];[d]${SCALE.replace('scale=', `scale=${W}:${H}:`)}[do];[m]${SCALE}[mo]`;
  return ['-filter_complex', fc, '-map', '[do]', ...ENCODE, ...a, out, '-map', '[mo]', ...ENCODE_MASTER, ...a, masterOf(out)];
}
const pngIn = (blur) => ['-f', 'image2pipe', '-framerate', String(blur ? 2 * FPS : FPS), '-c:v', 'png', '-i', '-'];
// the times to draw for output frames [a, b): one each, or with blur the 60 fps pair behind each one
const times = (a, b, blur) => blur
  ? [...Array(2 * (b - a)).keys()].map((k) => Math.max(0, 2 * a - 1 + k) / (2 * FPS))
  : [...Array(b - a).keys()].map((k) => (a + k) / FPS);

async function openPage(dir) {
  const timings = JSON.parse(fs.readFileSync(path.join(dir, 'voice/timings.json'), 'utf8'));
  const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new', args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exit(1); });
  await page.setViewport(LANDSCAPE ? { width: 1920, height: 1080, deviceScaleFactor: DSF } : { width: 1080, height: 1920, deviceScaleFactor: DSF });
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
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', ...pngIn(blur), ...outputs(blur, file, false)], { stdio: ['pipe', 'inherit', 'inherit'] });
    await renderRange(frame, +a, +b, ff, (k) => { if (k % 10 === 0 || +a + k === +b) process.stdout.write(`F ${k}\n`); }, blur);
    // the segment is written; closing Chrome can hang, so give it a moment and then leave
    await Promise.race([browser.close(), new Promise((r) => setTimeout(r, 5000))]);
    process.exit(0);
  }

  const workers = Math.max(1, +(flag('--workers') || 1)), blur = args.includes('--blur');
  const stills = args.slice(1).filter((x, i, all) => !x.startsWith('--') && !['--workers', '--segment'].includes(all[i - 1])).map(Number);
  const { browser, page, frame, settle } = await openPage(dir);
  const { total, end, cues } = await page.evaluate(() => ({ total: window.TOTAL, end: window.END, cues: window.CUES }));

  if (stills.length) {
    for (const t of stills) {
      await page.evaluate((x) => window.renderFrame(x), t);
      await settle();
      await page.screenshot({ path: path.join(dir, 'out', `still-${t}${LANDSCAPE ? '-landscape' : ''}${DSF > 1 ? '-x' + DSF : ''}.png`) });
    }
    await browser.close();
    return;
  }
  fs.writeFileSync(path.join(dir, 'sfx.json'), JSON.stringify({ total, keys: cues.keys.map((k) => [k, 'key']), ticks: cues.ticks,
    pops: [], whooshes: [], misses: [], hits: [], chord: [end], thumps: [],
    draws: cues.draws, taps: cues.taps, brushes: cues.brushes, moves: cues.moves, cuts: cues.cuts, zooms: cues.zooms, checks: cues.checks, bed: 'ambient', kit: 'recorded' }));
  execFileSync(path.join(root, '.venv/bin/python'), [path.join(root, 'explainer/mix.py'), dir], { stdio: 'inherit' });
  const out = path.join(dir, 'out', name + (LANDSCAPE ? '-landscape' : '') + '.mp4'), audio = path.join(dir, 'audio.wav');
  if (process.env.AUDIO_ONLY) {   // remix the soundtrack onto the existing video, no frames rendered
    for (const file of [out, masterOf(out)].filter((f) => fs.existsSync(f))) {
      const tmp = file.replace(/\.mp4$/, '.remix.mp4');
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', file, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
        ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart', tmp]);
      fs.renameSync(tmp, file);
    }
    await browser.close(); return;
  }
  const n = Math.round(total * FPS), report = progress(dir, name, n);

  if (workers === 1) {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', ...pngIn(blur), '-i', audio, ...outputs(blur, out, true)], { stdio: ['pipe', 'inherit', 'inherit'] });
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
    const child = spawn(process.execPath, [__filename, dir, '--segment', `${a}:${b}:${file}`, ...(blur ? ['--blur'] : []), ...(LANDSCAPE ? ['--landscape'] : []), ...(DSF > 1 ? [`--scale=${DSF}`] : [])], { stdio: ['ignore', 'pipe', 'inherit'] });
    let buf = '';
    child.stdout.on('data', (d) => {
      buf += d; const lines = buf.split('\n'); buf = lines.pop();
      for (const l of lines) if (l.startsWith('F ')) { done[i] = +l.slice(2); report(done.reduce((x, y) => x + y, 0), 'rendering', workers); }
    });
    child.on('close', resolve);
  })));
  if (codes.some((c) => c !== 0)) { console.error('a worker failed:', codes); process.exit(1); }
  report(n, 'joining', workers);
  const join = (seg, file) => {
    const list = path.join(segDir, 'list.txt');
    fs.writeFileSync(list, ranges.map((_, i) => `file '${path.join(segDir, seg(i))}'`).join('\n') + '\n');
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-i', audio, '-map', '0:v', '-map', '1:a',
      '-c:v', 'copy', ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart', file]);
  };
  join((i) => `seg-${i}.mp4`, out);
  if (DSF > 1) join((i) => `seg-${i}-master.mp4`, masterOf(out));
  fs.rmSync(segDir, { recursive: true, force: true });
  report(n, 'done', workers);
  console.log(out, total.toFixed(2) + 's', `(${workers} workers${blur ? ', 60 fps blended to 30' : ''})`);
})();
