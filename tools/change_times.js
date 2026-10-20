// In-page helper (loaded by tools/record.js): which frames can change?
// For every Web Animation, each keyframe segment either holds (equal values),
// steps (step-end easing: changes only at its end), or moves continuously.
// window.__changes(fps, total) returns a Uint8Array: 1 if frame f may differ
// from frame f-1, 0 if it is guaranteed identical.
window.__changes = function (fps, total) {
  const n = Math.round(total * fps);
  const changed = new Uint8Array(n);
  changed[0] = 1;
  const markRange = (a, b) => {           // continuous change during (a, b)
    const f0 = Math.max(1, Math.floor(a * fps) + 1), f1 = Math.min(n - 1, Math.ceil(b * fps));
    for (let f = f0; f <= f1; f++) changed[f] = 1;
  };
  const markAt = (t) => {                 // a step at time t shows from frame ceil(t*fps)
    const f = Math.min(n - 1, Math.max(1, Math.ceil(t * fps - 1e-6)));
    changed[f] = 1;
    if (f + 1 < n) changed[f + 1] = 1;    // one frame of margin
  };
  for (const a of document.getAnimations()) {
    const tm = a.effect.getComputedTiming();
    const delay = (tm.delay || 0) / 1000, dur = (tm.duration || 0) / 1000;
    const kfs = a.effect.getKeyframes();
    const vals = (k) => JSON.stringify(Object.fromEntries(Object.entries(k).filter(([p]) => !['offset', 'computedOffset', 'easing', 'composite'].includes(p))));
    const animEasing = a.effect.getTiming().easing || 'linear';
    if (kfs.length < 2) { markRange(delay, delay + dur); continue; }
    if (animEasing.startsWith('step')) { kfs.forEach((k) => markAt(delay + k.computedOffset * dur)); markAt(delay); markAt(delay + dur); continue; }
    markAt(delay);                         // fill 'none' animations switch on/off at their ends
    markAt(delay + dur);
    for (let i = 0; i + 1 < kfs.length; i++) {
      const k = kfs[i], k2 = kfs[i + 1];
      const t0 = delay + k.computedOffset * dur, t1 = delay + k2.computedOffset * dur;
      if (vals(k) === vals(k2)) continue;                       // hold
      if ((k.easing || '').startsWith('step')) markAt(t1);      // step-end: changes at the end
      else markRange(t0, t1);                                   // moves
    }
  }
  return changed;
};
