// Theme "field": shared defs (brush filter, ink figures) and the leaf light on every frame.
// The leaf light images are not in git: bake them once with `.venv/bin/python tools/make_leaf.py`.
// Load after the page body and before runtime.js:
//   <script src=".../themes/field.js"></script><script src=".../runtime.js"></script>
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
  </defs></svg>`;
  document.body.prepend(defs.firstChild);

  // leaf light: two layers of one baked image per frame, drifting slowly (studies/21)
  const layers = [];
  document.querySelectorAll('.frame').forEach((f, k) => {
    const src = `${here}field/leaf-${(k % 8) + 1}.png`;
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
