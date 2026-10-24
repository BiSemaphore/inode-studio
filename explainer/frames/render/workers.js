// Parallel render: split the frames into equal contiguous ranges, one Chrome each (a child process running
// render.js --segment), then join the video-only segments without re-encoding and add the sound.
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
const { AUDIO_ARGS } = require('./encode');

// cfg: { landscape, dsf, blur }; script: render.js (each worker runs it with --segment)
async function renderParallel({ script, dir, n, workers, cfg, out, audio, report }) {
  const segDir = path.join(dir, 'out', 'segments');
  fs.mkdirSync(segDir, { recursive: true });
  const ranges = [...Array(workers)].map((_, i) => [Math.round((n * i) / workers), Math.round((n * (i + 1)) / workers)]);
  const done = ranges.map(() => 0);
  const flags = [cfg.blur ? '--blur' : '--no-blur', ...(cfg.landscape ? ['--landscape'] : []), ...(cfg.dsf > 1 ? [`--scale=${cfg.dsf}`] : [])];
  report(0, 'rendering', workers);
  const codes = await Promise.all(ranges.map(([a, b], i) => new Promise((resolve) => {
    const child = spawn(process.execPath, [script, dir, '--segment', `${a}:${b}:${path.join(segDir, `seg-${i}.mp4`)}`, ...flags],
      { stdio: ['ignore', 'pipe', 'inherit'] });
    let buf = '';
    child.stdout.on('data', (d) => {   // workers report "F <frames done>" lines
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
}

module.exports = { renderParallel };
