// Theme "field": shared defs (brush filter, ink figures) and the leaf light on every frame.
// The leaf light images are not in git: bake them once with `.venv/bin/python tools/make_leaf.py`.
// Load after the page body and before runtime.js:
//   <script src=".../themes/field.js"></script><script src=".../runtime.js"></script>
// Brand mark: <svg width="330" height="275"><use href="#bmark" width="330" height="275"/></svg> (the "b.", cream with a red dot).
// Figures (feet at 0,0, about 110 px tall): #stand #think #point #work #hold. Use them as
//   <use href="#point" class="ink" transform="translate(540 760) scale(1.25)"/>
(function () {
  const here = document.currentScript.src.replace(/[^/]*$/, '');
  const defs = document.createElement('div');
  defs.innerHTML = `<svg width="0" height="0" style="position:absolute"><defs>
    <filter id="dry" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="5" result="wob"/>
      <feDisplacementMap in="SourceGraphic" in2="wob" scale="3"/>
    </filter>
    <g id="stand"><circle cx="0" cy="-98" r="9"/><path d="M -9 -86 L 9 -86 L 7 -46 L -7 -46 Z M -5 -46 L -6 0 l -6 0 M 5 -46 L 6 0 l 6 0"/></g>
    <g id="think"><use href="#stand"/><path d="M -9 -84 L -12 -54 M 9 -84 L 13 -68 L 4 -90"/></g>
    <g id="point"><use href="#stand"/><path d="M -9 -84 L -12 -54 M 9 -84 L 44 -80 M 40 -84 l 6 4 l -6 3"/></g>
    <g id="work"><circle cx="-2" cy="-64" r="9"/><path d="M -9 -52 L 8 -52 L 11 -28 L -6 -28 Z M -4 -28 L -16 -12 L -8 0 l -6 0 M 8 -28 L 18 -12 L 12 0 l 6 0 M 7 -48 L 22 -36 M 16 -30 L 46 -30 M 22 -30 L 30 -50 L 52 -50 L 46 -30"/></g>
    <g id="hold"><use href="#stand"/><path d="M -9 -84 L -12 -54 M 9 -84 L 22 -66 L 36 -78"/><rect x="34" y="-98" width="34" height="42" rx="3" transform="rotate(8 51 -77)"/><path d="M 42 -86 l 18 3 M 41 -77 l 14 2" stroke-width="2"/></g>
    <symbol id="bmark" viewBox="0 -232 300 250"><path d="M69.90-143.70Q77.10-155.40 90.60-162.600Q104.10-169.80 121.50-169.80Q142.20-169.80 159-159.30Q175.80-148.80 185.55-129.30Q195.30-109.80 195.30-84Q195.30-58.20 185.55-38.55Q175.80-18.90 159-8.25Q142.20 2.40 121.50 2.40Q103.80 2.40 90.60-4.65Q77.40-11.70 69.90-23.40L69.90 0L18.60 0L18.60-222L69.90-222L69.90-143.70M143.10-84Q143.10-103.20 132.45-114.15Q121.80-125.10 106.20-125.10Q90.900-125.10 80.25-114Q69.60-102.90 69.60-83.70Q69.60-64.50 80.25-53.40Q90.90-42.30 106.20-42.30Q121.50-42.30 132.30-53.55Q143.10-64.80 143.10-84" fill="var(--cream)" filter="url(#dry)"/><circle cx="246" cy="-25" r="30" fill="var(--thread)"/></symbol>
  </defs></svg>`;
  document.body.prepend(defs.firstChild);

  // leaf light: two layers of one baked image per frame, drifting slowly (studies/21)
  const layers = [];
  document.querySelectorAll('.frame').forEach((f, k) => {
    const src = `${here}leaf-${(k % 8) + 1}.png`;
    for (const cls of ['soft', 'glow']) {
      const img = document.createElement('img');
      img.className = 'leaf ' + cls; img.src = src;
      f.prepend(img); layers.push({ img, k });
    }
    const v = document.createElement('div'); v.className = 'vignette';
    f.insertBefore(v, f.children[2]);
  });
  if (!document.getElementById('grain')) {
    const g = document.createElement('div'); g.id = 'grain'; document.body.appendChild(g);
  }
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => {
    layers.forEach(({ img, k }) => {
      const x = 40 * Math.sin(t * 0.11 + k), y = 30 * Math.cos(t * 0.08 + k * 1.7);
      img.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
    });
  });
})();
