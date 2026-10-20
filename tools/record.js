// Record an animated HTML piece to MP4, frame by frame (deterministic, no screen capture).
//
// The piece must contain #stage (the frame to capture) and set
//   window.MOTION = { duration, fps, width?, height?, scale?, outputs? }
// width/height default to 1080x1350; scale (default 1) renders at a higher
// pixel density and downscales in ffmpeg for sharper text.
// All motion is CSS animations / Web Animations; this script pauses them and seeks
// document.getAnimations() to each frame time before taking a screenshot.
//
// Usage: node tools/record.js <piece.html> <outdir> [--workers N] [--range FROM:TO]
//   --workers  Chrome processes capturing in parallel (default 6)
//   --range    capture only frames FROM..TO-1 into <name>-range.mp4, no audio (for testing)
//
// Every render is checked (tools/check_video.py): frames that blink or come out
// black are captured again, up to 3 rounds; if any are still broken the render
// fails. Progress is printed and written to <outdir>/progress.txt.
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');
const puppeteer = require('puppeteer-core');
const CHROME = require('./chrome');
const STUDIO = path.resolve(__dirname, '..');

// Make Chrome finish every drawing stage before producing a frame. (Missing
// strokes and text in earlier renders came from huge SVG masks in the kit,
// now removed; see explainer/README.md.)
const CHROME_ARGS = [
  '--run-all-compositor-stages-before-draw', '--disable-checker-imaging',
  '--disable-threaded-animation', '--disable-threaded-scrolling', '--disable-new-content-rendering-timeout',
  '--force-color-profile=srgb', '--hide-scrollbars',
];

const argv = process.argv.slice(2);
const flag = (name, def) => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : def; };
const [piece, outdir] = argv.filter((a, i) => !a.startsWith('--') && !(i && argv[i - 1].startsWith('--')));
const WORKERS = parseInt(flag('--workers', '6'), 10);
const RANGE = flag('--range', null);
// PNG is lossless but slow to compress at 2x; JPEG q95 is visually identical after the downscale.
const FMT = flag('--format', 'png');
// Frames where no animation changes are copied from the previous frame
// instead of captured (tools/change_times.js); --no-skip captures all.
const SKIP = !argv.includes('--no-skip');
const KEEP = argv.includes('--keep-frames');

async function openPage() {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: CHROME_ARGS });
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(piece), { waitUntil: 'networkidle0' });
  const m = await page.evaluate(() => window.MOTION);
  await page.setViewport({ width: m.width || 1080, height: m.height || 1350, deviceScaleFactor: m.scale || 1 });
  await page.evaluate(() => document.fonts.ready);
  // Pieces that build their animations after loading fonts set MOTION.ready = false, then true.
  await page.waitForFunction(() => window.MOTION.ready !== false);
  return { browser, page, stage: await page.$('#stage'), motion: m };
}

function fmt(s) { return s >= 60 ? `${Math.floor(s / 60)}m${String(Math.round(s % 60)).padStart(2, '0')}s` : `${Math.round(s)}s`; }

// Capture the given frame numbers with WORKERS parallel Chrome processes.
async function capture(list, fps, frames, offset, label) {
  const queue = [...list];
  let done = 0;
  const t0 = Date.now();
  const report = () => {
    const el = (Date.now() - t0) / 1000;
    const left = done ? (el / done) * (list.length - done) : 0;
    const line = `${path.basename(path.dirname(path.resolve(piece)))} ${label}: ${done}/${list.length} frames (${Math.round((100 * done) / list.length)}%), ${fmt(el)} elapsed, about ${fmt(left)} left`;
    console.log(line);
    fs.writeFileSync(path.join(outdir, 'progress.txt'), line + '\n');
  };
  const worker = async () => {
    const { browser, page, stage } = await openPage();
    while (queue.length) {
      const f = queue.shift();
      await page.evaluate((ms) => {
        for (const a of document.getAnimations()) { a.pause(); a.currentTime = ms; }
        return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      }, (f / fps) * 1000);
      await stage.screenshot(FMT === 'jpeg' ? { path: path.join(frames, `${String(f - offset).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 95 } : { path: path.join(frames, `${String(f - offset).padStart(5, '0')}.png`) });
      if (++done % 50 === 0) report();
    }
    await browser.close();
  };
  await Promise.all(Array.from({ length: Math.min(WORKERS, list.length) }, worker));
  report();
}

function encode(frames, fps, o, mp4, audio) {
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps),
    '-i', path.join(frames, FMT === 'jpeg' ? '%05d.jpg' : '%05d.png'), ...audio, '-vf', `scale=${o.width}:${o.height}:flags=lanczos`,
    '-c:v', 'libx264', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-crf', String(o.crf || 14),
    '-profile:v', 'high', '-g', String(fps * 2), '-r', String(fps),
    '-preset', 'slow', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
}

// MOTION.cuts: times of intentional hard cuts and flashes (a frame there
// legitimately differs from both neighbours); frames within one frame of
// them are not counted as broken.
let CUTS = [];
function brokenFrames(mp4, fps) {
  const out = execFileSync(path.join(STUDIO, '.venv/bin/python'), [path.join(STUDIO, 'tools/check_video.py'), mp4, '--json']).toString();
  return JSON.parse(out).broken.filter((f) => !CUTS.some((t) => Math.abs(f - t * fps) <= 1.5));
}

(async () => {
  const frames = path.join(outdir, 'frames');
  fs.rmSync(frames, { recursive: true, force: true });
  fs.mkdirSync(frames, { recursive: true });

  const probe = await openPage();
  const { duration, fps, width = 1080, height = 1350, outputs, cuts = [] } = probe.motion;
  CUTS = cuts;
  const total = Math.round(duration * fps);
  let changed = null;
  if (SKIP) {
    await probe.page.addScriptTag({ path: path.join(__dirname, 'change_times.js') });
    changed = Array.from(await probe.page.evaluate((fps, d) => Array.from(window.__changes(fps, d)), fps, duration));
  }
  await probe.browser.close();
  const [from, to] = RANGE ? RANGE.split(':').map(Number) : [0, total];
  const all = Array.from({ length: to - from }, (_, k) => from + k);
  // Capture the first frame of the range and every frame that can change.
  const toCapture = changed ? all.filter((f) => f === from || changed[f]) : all;

  const T0 = Date.now();
  const stage = (label) => console.log(`[time] ${label}: ${((Date.now() - T0) / 1000).toFixed(1)}s`);
  await capture(toCapture, fps, frames, from, 'capturing');
  const ext = FMT === 'jpeg' ? 'jpg' : 'png';
  const file = (f) => path.join(frames, `${String(f - from).padStart(5, '0')}.${ext}`);
  let copied = 0;
  for (const f of all) {
    if (!fs.existsSync(file(f))) { fs.linkSync(file(f - 1), file(f)); copied++; }
  }
  stage(`captured ${toCapture.length}, reused ${copied} still frames`);

  const name = path.basename(path.dirname(path.resolve(piece)));
  const wav = path.join(path.dirname(path.resolve(piece)), 'audio.wav');
  const audio = !RANGE && fs.existsSync(wav) ? ['-i', wav, '-c:a', 'aac', '-b:a', '192k', '-shortest'] : [];
  const outs = RANGE ? [{ width, height, ...(outputs || [{}])[0], suffix: '-range' }] : outputs || [{ width, height }];

  // Encode the first output, check it, recapture broken frames, repeat.
  const first = path.join(outdir, `${name}${outs[0].suffix || ''}.mp4`);
  for (let round = 1; ; round++) {
    encode(frames, fps, outs[0], first, audio);
    stage(`encoded (round ${round})`);
    const bad = brokenFrames(first, fps);
    stage(`checked (round ${round})`);
    console.log(`check ${round}: ${bad.length} broken frames${bad.length ? ': ' + bad.slice(0, 20).map((b) => b + from).join(', ') : ''}`);
    if (!bad.length) break;
    if (round === 3) {
      fs.renameSync(first, first.replace(/\.mp4$/, '.BROKEN.mp4'));
      console.error('frames still broken after 3 rounds; render failed');
      process.exit(1);
    }
    for (const b of bad) fs.rmSync(path.join(frames, `${String(b).padStart(5, '0')}.${FMT === 'jpeg' ? 'jpg' : 'png'}`), { force: true });
    await capture(bad.map((b) => b + from), fps, frames, from, `recapturing (round ${round})`);
  }
  for (const o of outs.slice(1)) encode(frames, fps, o, path.join(outdir, `${name}${o.suffix || ''}.mp4`), audio);
  console.log(`${all.length} frames, checked clean -> ${outs.map((o) => `${name}${o.suffix || ''}.mp4`).join(', ')}`);
  if (!KEEP) fs.rmSync(frames, { recursive: true, force: true });
  fs.writeFileSync(path.join(outdir, 'progress.txt'), `done: ${all.length} frames, checked clean, ${new Date().toISOString()}\n`);
  // A Chrome child can linger after browser.close() and keep Node alive
  // (renders looked "stuck" after finishing); exit explicitly.
  process.exit(0);
})().catch((e) => { console.error(e); process.exit(1); });
