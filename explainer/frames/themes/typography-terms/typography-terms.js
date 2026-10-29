// Theme "typography-terms": the photos breathe. Every .push element (a photo and its subject cut-out) scales from
// 1.00 to 1.06 across the time its frame is on screen, so the words feel placed in a living scene.
// Load after runtime.js (it needs window.TIMINGS and window.END).
(function () {
  const TM = window.TIMINGS, NB = TM.length;
  const frames = [...document.querySelectorAll('.frame')].map((f) => {
    const a = f.dataset.from, z = f.dataset.to;
    const t0 = a === 'end' ? window.END : Math.max(0, TM[+a].start - 0.3);
    const t1 = z === 'end' ? window.TOTAL : (+z + 1 < NB ? TM[+z + 1].start - 0.3 : window.END);
    return { items: [...f.querySelectorAll('.push')], t0, t1 };
  }).filter((d) => d.items.length);
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => {
    frames.forEach(({ items, t0, t1 }) => {
      const p = Math.min(1, Math.max(0, (t - t0) / Math.max(1, t1 - t0)));
      items.forEach((e) => { e.style.transform = `scale(${(1 + 0.06 * p).toFixed(4)})`; });
    });
  });
})();
