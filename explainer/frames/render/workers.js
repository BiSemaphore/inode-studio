// Parallel render with a chunk cache. The frames are cut into 2 s chunks; each worker (a child process running
// render.js --chunks) takes every fourth one. For every chunk the worker draws each frame once to get its
// fingerprint (about 1 ms, no screenshot); the chunk's key is a hash of those fingerprints plus everything else
// that decides the pixels (the page, timings, every engine and theme file, the render settings). A chunk whose key
// is already in out/cache/ is reused as it is; only changed chunks are drawn and encoded. Chunks are dealt round
// robin, so the few chunks an edit touches are drawn by all workers at once. The chunks are then
// joined without re-encoding and the sound is added. Chunks no longer used are removed from the cache.
const path = require('path'), fs = require('fs'), crypto = require('crypto'), { spawn, execFileSync } = require('child_process');
const { AUDIO_ARGS, FPS } = require('./encode');

const CHUNK = 2 * FPS;   // output frames per chunk

// everything other than the drawn DOM that decides the pixels: the engine and theme files (stylesheets, scripts,
// images), the timings and the render settings. page.html is not here on purpose: its content, inline styles and
// scripts all show up in each frame's fingerprint, so editing one card redraws only the chunks that card is in.
function baseKey(dir, cfg) {
  const h = crypto.createHash('sha1');
  const frames = path.resolve(__dirname, '..');
  const files = [path.join(dir, 'voice', 'timings.json')];
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).forEach((e) => {
    const f = path.join(d, e.name);
    // progress.js and workers.js only report and schedule; they never change a pixel
    if (e.isDirectory()) walk(f); else if (/\.(js|css|json|png|woff2?)$/.test(e.name) && !/^(progress|workers)\.js$/.test(e.name)) files.push(f);
  });
  walk(frames);
  for (const f of files.sort()) { h.update(f); h.update(fs.readFileSync(f)); }
  h.update(JSON.stringify({ landscape: cfg.landscape, dsf: cfg.dsf, blur: cfg.blur }));
  return h.digest('hex').slice(0, 16);
}

// cfg: { landscape, dsf, blur }; script: render.js (each worker runs it with --chunks)
async function renderParallel({ script, dir, n, workers, cfg, out, audio, report }) {
  const cacheDir = path.join(dir, 'out', 'cache', `${cfg.landscape ? 'landscape' : 'vertical'}-x${cfg.dsf}${cfg.blur ? '-blur' : ''}`);
  fs.mkdirSync(cacheDir, { recursive: true });
  const base = baseKey(dir, cfg);
  const chunks = [];
  for (let a = 0; a < n; a += CHUNK) chunks.push([a, Math.min(n, a + CHUNK)]);
  // deal the chunks round robin, so an edit (which touches neighbouring chunks) is spread over every worker
  const groups = [...Array(workers)].map((_, w) => chunks.map((c, i) => [i, ...c]).filter(([i]) => i % workers === w)).filter((g) => g.length);
  const done = groups.map(() => 0), keys = [];
  let reused = 0;
  const profiles = [];   // workers' profile lines, printed after the progress bar so they never break it
  const flags = [cfg.blur ? '--blur' : '--no-blur', ...(cfg.landscape ? ['--landscape'] : []), ...(cfg.dsf > 1 ? [`--scale=${cfg.dsf}`] : [])];
  report(0, 'rendering', groups.length);
  const codes = await Promise.all(groups.map((g, w) => new Promise((resolve) => {
    const spec = g.map(([i, a, b]) => `${i}:${a}:${b}`).join(',');
    const child = spawn(process.execPath, [script, dir, '--chunks', spec, '--cache', cacheDir, '--key', base, ...flags],
      { stdio: ['ignore', 'pipe', 'pipe'] });
    let ebuf = '';
    child.stderr.on('data', (d) => {
      ebuf += d; const lines = ebuf.split('\n'); ebuf = lines.pop();
      for (const l of lines) if (l.startsWith('profile ')) profiles.push(l); else if (l) process.stderr.write('\n' + l + '\n');
    });
    let buf = '';
    child.stdout.on('data', (d) => {   // workers report "F <frames done>", "K <chunk> <key> <new|cached>"
      buf += d; const lines = buf.split('\n'); buf = lines.pop();
      for (const l of lines) {
        if (l.startsWith('F ')) { done[w] = +l.slice(2); report(done.reduce((x, y) => x + y, 0), 'rendering', groups.length); }
        if (l.startsWith('K ')) { const [, i, key, how] = l.split(' '); keys[+i] = key; if (how === 'cached') reused++; }
      }
    });
    child.on('close', resolve);
  })));
  if (codes.some((c) => c !== 0) || keys.length !== chunks.length || keys.some((k) => !k)) {
    console.error('a worker failed:', codes); process.exit(1);
  }
  report(n, 'joining', groups.length);
  const list = path.join(cacheDir, 'list.txt');
  fs.writeFileSync(list, keys.map((k) => `file '${path.join(cacheDir, k + '.mp4')}'`).join('\n') + '\n');
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-i', audio, '-map', '0:v', '-map', '1:a',
    '-c:v', 'copy', ...AUDIO_ARGS, '-shortest', '-movflags', '+faststart', out]);
  // keep only the chunks this render used, so the cache never grows past one video's worth per shape
  const used = new Set(keys.map((k) => k + '.mp4'));
  for (const f of fs.readdirSync(cacheDir)) if (f.endsWith('.mp4') && !used.has(f)) fs.rmSync(path.join(cacheDir, f));
  report(n, 'done', groups.length);
  profiles.forEach((l) => console.error(l));
  console.log(`chunks: ${chunks.length - reused} drawn, ${reused} reused from the cache`);
}

module.exports = { renderParallel };
