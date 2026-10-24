// Live progress for a render: out/render-progress.json (read by tools/render_status.py) and a line every 5%.
const path = require('path'), fs = require('fs');

function progress(dir, name, n) {
  const file = path.join(dir, 'out', 'render-progress.json'), t0 = Date.now();
  let lastPct = -1;
  return (f, state, workers) => {
    const pct = Math.floor((f / n) * 100), secs = (Date.now() - t0) / 1000, eta = f ? secs / f * (n - f) : null;
    fs.writeFileSync(file, JSON.stringify({ piece: name, frame: f, frames: n, pct, state, workers: workers || 1, elapsed_s: Math.round(secs),
      eta_s: eta === null ? null : Math.round(eta), finish_at: eta === null ? null : new Date(Date.now() + eta * 1000).toLocaleTimeString() }));
    if (state === 'rendering' && pct >= lastPct + 5) {
      lastPct = pct - (pct % 5);
      console.log(`${name}: ${pct}% (${f}/${n} frames), about ${eta === null ? '?' : Math.round(eta / 60)} min left`);
    }
  };
}

module.exports = { progress };
