// Render a frames piece: page.html + voice/timings.json -> out/<name>.mp4 (30 fps, mixed audio).
//   node explainer/frames/render.js motion/<group>/<piece>                 full render, 4 Chromes (--workers N)
//   ... --scale=2                                                          draw at 2x, shrunk to 1080x1920 (cleaner)
//   ... --landscape                                                        1920x1080 (16:9) for LinkedIn -> out/<name>-landscape.mp4
//   ... --no-blur                                                          plain 30 fps (default: drawn at 60 fps, pairs blended into 30)
//   ... --draft                                                            quick preview: 1x, no blur -> out/<name>-draft.mp4 (never the final)
//   node explainer/frames/render.js motion/<group>/<piece> 3.2 9 ...       stills -> out/still-<t>.png
//   AUDIO_ONLY=1 node explainer/frames/render.js motion/<group>/<piece>    remix the sound onto out/<name>.mp4
// Only the delivery files are made: one for Instagram, one for LinkedIn (--landscape); no master (owner 2026-10-24).
// Modules: render/capture.js (Chrome, frames), render/encode.js (ffmpeg), render/workers.js (parallel),
// render/progress.js (out/render-progress.json). Each worker prints a per-stage profile when it finishes.
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
const { FPS, AUDIO_ARGS, pngIn, outputs } = require('./render/encode');
const { openPage, renderRange, profileLine } = require('./render/capture');
const { renderParallel } = require('./render/workers');
const { progress } = require('./render/progress');
const root = path.resolve(__dirname, '../..');

const args = process.argv.slice(2), dir = path.resolve(args[0]), name = path.basename(dir);
const flag = (k) => { const i = args.indexOf(k); return i < 0 ? null : args[i + 1]; };
const landscape = args.includes('--landscape'), draft = args.includes('--draft');
// motion blur is the default for renders (owner 2026-10-24): frames drawn at 60 fps, each output frame blends a pair,
// so swipes, zooms and pens move smoothly; it doubles render time. --no-blur for a plain 30 fps draft.
const cfg = { landscape, dsf: draft ? 1 : +((args.find((a) => a.startsWith('--scale=')) || '=1').split('=')[1]), blur: !draft && !args.includes('--no-blur'),
  w: landscape ? 1920 : 1080, h: landscape ? 1080 : 1920 };
// 4 Chromes by default: measured 9.2 frames/s at 2x vs 6.7 with 2 and 10.4 with 6 (CPU-bound past 4); memory stays
// about 50% free on 16 GB now that no master is encoded (2026-10-24)
const workers = Math.max(1, +(flag('--workers') || 4));
const stills = args.slice(1).filter((x, i, all) => !x.startsWith('--') && !['--workers', '--segment'].includes(all[i - 1])).map(Number);

// one worker: a frame range into a video-only segment; reports "F <done>" lines to the parent
async function segment(spec) {
  const [a, b, file] = spec.split(':');
  const { browser, frame, prof } = await openPage(dir, cfg), t0 = performance.now();
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', ...pngIn(cfg.blur), ...outputs(cfg, file, false)], { stdio: ['pipe', 'inherit', 'inherit'] });
  await renderRange(frame, +a, +b, ff, (k) => { if (k % 10 === 0 || +a + k === +b) process.stdout.write(`F ${k}\n`); }, cfg.blur, prof);
  console.error(profileLine(prof, t0, `${a}-${b}`));
  // the segment is written; closing Chrome can hang, so give it a moment and then leave
  await Promise.race([browser.close(), new Promise((r) => setTimeout(r, 5000))]);
  process.exit(0);
}

(async () => {
  fs.mkdirSync(path.join(dir, 'out'), { recursive: true });
  if (flag('--segment')) return segment(flag('--segment'));

  const { browser, page, frame, settle } = await openPage(dir, cfg);
  const { total, end, cues } = await page.evaluate(() => ({ total: window.TOTAL, end: window.END, cues: window.CUES }));

  if (stills.length) {
    for (const t of stills) {
      await page.evaluate((x) => window.renderFrame(x), t);
      await settle();
      await page.screenshot({ path: path.join(dir, 'out', `still-${t}${landscape ? '-landscape' : ''}${cfg.dsf > 1 ? '-x' + cfg.dsf : ''}.png`) });
    }
    return browser.close();
  }

  // sound: the page's cues (pen strokes, taps, cuts) go to the mixer, which writes audio.wav
  fs.writeFileSync(path.join(dir, 'sfx.json'), JSON.stringify({ total, keys: cues.keys.map((k) => [k, 'key']), ticks: cues.ticks,
    pops: [], whooshes: [], misses: [], hits: [], chord: [end], thumps: [],
    draws: cues.draws, taps: cues.taps, brushes: cues.brushes, moves: cues.moves, cuts: cues.cuts, zooms: cues.zooms, checks: cues.checks, bed: 'ambient', kit: 'recorded' }));
  execFileSync(path.join(root, '.venv/bin/python'), [path.join(root, 'explainer/mix.py'), dir], { stdio: 'inherit' });
  const out = path.join(dir, 'out', name + (landscape ? '-landscape' : '') + (draft ? '-draft' : '') + '.mp4'), audio = path.join(dir, 'audio.wav');

  if (process.env.AUDIO_ONLY) {   // remix the soundtrack onto the existing video, no frames rendered
    if (fs.existsSync(out)) {
      const tmp = out.replace(/\.mp4$/, '.remix.mp4');
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', out, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
        ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart', tmp]);
      fs.renameSync(tmp, out);
    }
    return browser.close();
  }

  const n = Math.round(total * FPS), report = progress(dir, name, n);
  if (workers === 1) {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', ...pngIn(cfg.blur), '-i', audio, ...outputs(cfg, out, true)], { stdio: ['pipe', 'inherit', 'inherit'] });
    report(0, 'rendering');
    await renderRange(frame, 0, n, ff, (k) => { if (k % FPS === 0) report(k, 'rendering'); }, cfg.blur);
    report(n, 'done');
    await browser.close();
  } else {
    await browser.close();
    await renderParallel({ script: __filename, dir, n, workers, cfg, out, audio, report });
  }
  console.log(out, total.toFixed(2) + 's', `(${workers} worker${workers > 1 ? 's' : ''}${cfg.blur ? ', 60 fps blended to 30' : ''})`);
})();
