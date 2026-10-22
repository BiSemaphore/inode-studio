// Notebook page: one sheet (2160 x 3840, twice the screen) inside a frame with class "notebook";
// the camera zooms in to write each part and out to connect it, and holds the finished page at
// the end so it can be screenshotted. Load after the page body and before field.js and runtime.js:
//   <script>window.NOTEBOOK = { regions: {4: [600, 910], ...}, out: [4, 5], connectors: {c1: 4}, checks: ['w8:proof.'] };</script>
//   <script src=".../notebook.js"></script><script src=".../themes/field.js"></script><script src=".../runtime.js"></script>
// Page markup inside <div class="frame notebook" data-from="2" data-to="13"><div id="canvas">...</div></div>:
//   class="w" data-w="spec|seconds"   written left to right like a pen, in about that time (and gets pen sound)
//   <path class="pen yelp" id="c1">   a connector: drawn in the zoomed-out view at the end of its beat
// Config:
//   regions      {beat: [x, y]}  the camera zooms to this sheet point for that beat; beats without one stay zoomed out
//   out          [beats]         zoom out at the end of these beats (to draw their connectors)
//   connectors   {id: beat}      connector path ids and the beat they close
//   checks       [specs]         a check sound at these times
//   hold         [top, bottom]   sheet rows to fill the screen during the final hold (default 70 to 3060)
//   zoom         scale when zoomed in (default 0.88; the overview is 0.5)
(function () {
  const C = window.NOTEBOOK || {}, TM = window.TIMINGS;
  const T = (spec) => {
    if (/^\d+(\.\d+)?$/.test(String(spec))) return +spec;
    const m = String(spec).match(/^([bw])(\d+)(?::([^+-]+))?([+-][\d.]+)?$/);
    if (!m) throw new Error('bad time ' + spec);
    const b = TM[+m[2]], off = m[4] ? parseFloat(m[4]) : 0;
    if (m[1] === 'b') return b.start + off;
    const w = b.words.find((x) => x[0] === m[3]); if (!w) throw new Error('no word ' + spec); return w[1] + off;
  };
  const frame = document.querySelector('.frame.notebook'), cv = document.getElementById('canvas');
  const from = +frame.dataset.from, to = +frame.dataset.to;

  // connectors draw while the camera is out, at the end of their beat
  Object.entries(C.connectors || {}).forEach(([id, k]) => {
    const e = document.getElementById(id), t = TM[k].end - 0.1;
    e.dataset.t0 = t.toFixed(2); e.dataset.t1 = (t + 0.5).toFixed(2);
  });

  // camera keys: [time, sheet x, sheet y, scale]; each move eases over MOVE seconds from the key time
  const OV = [1080, 1720, 0.5], Z = C.zoom || 0.88, out = new Set(C.out || []), MOVE = 0.75;
  const CAM = [[TM[from].start - 0.4, ...OV]];
  let zoomed = false, prevOut = false;
  for (let k = from; k <= to; k++) {
    const r = (C.regions || {})[k];
    if (r) {
      CAM.push([TM[k].start + (prevOut ? 0.35 : 0.15), r[0], r[1], Z]); zoomed = true;
      prevOut = out.has(k);
      if (prevOut) { CAM.push([TM[k].end - 0.35, ...OV]); zoomed = false; }
    } else {
      if (zoomed) { CAM.push([TM[k].start - 0.2, ...OV]); zoomed = false; }
      prevOut = false;
    }
  }
  if (zoomed) CAM.push([TM[to].end - 0.2, ...OV]);
  // the screenshot hold: the sheet's used rows centred on screen, a little larger than the overview
  const [top, bottom] = C.hold || [70, 3060], HS = 0.525;
  CAM.push([TM[to].end + 0.3, 1080, (top + bottom) / 2 - 100 / HS, HS]);

  // sound cues for the mixer: zooms, checks, pen under every written note
  window.ZOOMS = CAM.slice(1).map(([t, , , s], i) => [t, s > CAM[i][3] ? 'in' : 'out']);
  window.CHECKS = (C.checks || []).map(T);
  const writes = [...document.querySelectorAll('.w')].map((e) => { const [s, d] = e.dataset.w.split('|'); return { e, t0: T(s), d: +d }; });
  writes.forEach(({ e }) => { e.style.clipPath = 'inset(0 100% 0 0)'; });
  window.WRITES = (window.WRITES || []).concat(writes.map(({ t0, d }) => [t0, d]));

  const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => {
    let i = 0; while (i + 1 < CAM.length && CAM[i + 1][0] <= t) i++;
    const b = CAM[i], a = i === 0 ? b : CAM[i - 1], p = i === 0 ? 1 : ease(Math.min(1, Math.max(0, (t - b[0]) / MOVE)));
    const cx = a[1] + (b[1] - a[1]) * p, cy = a[2] + (b[2] - a[2]) * p, s = a[3] + (b[3] - a[3]) * p;
    cv.style.transform = `translate(${540 - cx * s}px, ${860 - cy * s}px) scale(${s})`;
    writes.forEach(({ e, t0, d }) => { const q = Math.min(1, Math.max(0, (t - t0) / d)); e.style.clipPath = `inset(-20px ${(1 - q) * 100}% -20px -20px)`; });
  });
})();
