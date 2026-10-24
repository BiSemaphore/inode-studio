// Live progress for a render, written two ways:
//   out/render-progress.json, read by tools/render_status.py (any terminal can watch any render);
//   the render's own output: in a terminal, one line redrawn in place like a package manager,
//     embeddings-01-v2  [==============>               ]  48%  940/1951 frames  render speed 9.4 frames/s  ETA 1:47
//   and, when the output goes to a file (a background job's log), one plain line every 5% instead.
const path = require('path'), fs = require('fs');

const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;
function bar(pct, width = 30) {
  const full = Math.floor((pct / 100) * width);
  return '[' + (full >= width ? '='.repeat(width) : '='.repeat(Math.max(0, full - 1)) + (full ? '>' : '') + ' '.repeat(width - full)) + ']';
}

function progress(dir, name, n) {
  const file = path.join(dir, 'out', 'render-progress.json'), t0 = Date.now(), tty = process.stdout.isTTY;
  let lastPct = -1, lastDraw = 0;
  return (f, state, workers) => {
    const pct = Math.floor((f / n) * 100), secs = (Date.now() - t0) / 1000, fps = secs > 0 ? f / secs : 0;
    const eta = f ? secs / f * (n - f) : null;
    fs.writeFileSync(file, JSON.stringify({ piece: name, frame: f, frames: n, pct, state, workers: workers || 1, elapsed_s: Math.round(secs),
      fps: Math.round(fps * 10) / 10, eta_s: eta === null ? null : Math.round(eta),
      finish_at: eta === null ? null : new Date(Date.now() + eta * 1000).toLocaleTimeString() }));
    const text = `${name}  ${bar(pct)} ${String(pct).padStart(3)}%  ${f}/${n} frames  render speed ${fps.toFixed(1)} frames/s  ` +
      (state === 'rendering' ? `ETA ${eta === null ? '?' : mmss(eta)}` : state === 'joining' ? 'joining chunks' : `done in ${mmss(secs)}`);
    if (tty) {
      if (state === 'rendering' && Date.now() - lastDraw < 150) return;   // redraw at most about 7 times a second
      lastDraw = Date.now();
      process.stdout.write('\r\x1b[2K' + text + (state === 'done' ? '\n' : ''));
    } else if (state !== 'rendering' || pct >= lastPct + 5) {
      lastPct = pct - (pct % 5);
      console.log(text);
    }
  };
}

module.exports = { progress, bar, mmss };
