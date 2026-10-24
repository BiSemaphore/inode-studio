// Theme "card": our people, line icons, the card deal and swipe, the brand mark. Load after runtime.js:
//   <script src=".../runtime.js"></script><script src=".../themes/card.js"></script>
// People (owner-approved 2026-10-24; studies/48-59-doodle-people.md, studies/doodle-style.png): round-head stick
// people drawn with one thin line (5.5 px on screen at every scale, class .d), dot eyes and a smile; the pose does
// the acting. Feet at the translate point; a negative x scale mirrors.
//   <g data-doodle="point" transform="translate(250 1430) scale(.9)"></g>
//   poses: stand point think fast heavy reads wonders sits   (sits: on a line at the translate point, seen side on)
//   heavy takes data-label (the text on the block it pushes); data-paint fills props (default white)
//   data-color: one strong colour for the whole person (owner 2026-10-24): cobalt tomato violet teal magenta forest
//   (all 4.2:1 or more on white and cream; on the yellow card use only cobalt, violet or forest)
// Icons in the same line: data-doodle="pin" (tip at the point), "idea" (bulb), "choice" (signpost).
// <body data-page="green">: the same cards on the green paper surface (card.css, tools/make_surface.py).
// Cards: each .frame's .stage lands from the right when the frame starts and swipes off to the left when it ends.
(function () {
  const INK = '#111111';
  const P = (d, c = '') => `<path class="d ${c}" d="${d}"/>`;
  const dot = (x, y, r = 6) => `<circle cx="${x}" cy="${y}" r="${r}" fill="currentColor"/>`;
  const head = (x, y, r = 44) => `<circle class="d" cx="${x}" cy="${y}" r="${r}"/>` + dot(x - 15, y - 4) + dot(x + 15, y - 4) +
    P(`M ${x - 13} ${y + 16} Q ${x} ${y + 26} ${x + 13} ${y + 16}`);
  const fist = (x, y) => dot(x, y, 9);
  const legs = P('M 0 -112 L -26 0') + P('M 0 -112 L 26 0');
  const cloud = (dx, dy) => `<g transform="translate(${dx} ${dy})">` + `<circle class="d thin" cx="0" cy="0" r="8"/><circle class="d thin" cx="22" cy="-30" r="12"/>` +
    P('M 20 -88 C 0 -108 16 -140 44 -136 C 52 -164 92 -166 102 -142 C 126 -158 164 -140 154 -112 C 180 -98 172 -64 146 -64 C 142 -38 104 -36 96 -54 C 78 -36 42 -44 44 -66 C 20 -64 6 -76 20 -88 Z') + '</g>';
  const DOODLE = {
    stand: () => head(0, -256) + P('M 0 -212 L 0 -112') + legs + P('M 0 -192 L -34 -126') + P('M 0 -192 L 34 -126'),
    point: () => head(-4, -256) + P('M 0 -212 L 0 -112') + legs + P('M 0 -192 L -34 -126') + P('M 0 -192 L 60 -206 L 112 -238') + fist(116, -240),
    think: () => head(6, -256) + P('M 0 -212 L 0 -112') + legs + P('M 0 -192 L -34 -126') + P('M 0 -192 L 40 -156 L 30 -214') +
      `<text x="64" y="-310" font-family="Inter" font-weight="900" font-size="64" fill="currentColor">?</text>`,
    fast: () => head(34, -252) + P('M 22 -208 L 0 -112') + P('M 0 -112 L 44 -66 L 86 -82') + P('M 0 -112 L -26 -54 L -70 -26') +
      P('M 16 -184 L 54 -150 L 78 -176') + P('M 14 -180 L -22 -150 L -48 -168') +
      P('M -110 -214 h -70', 'thin') + P('M -120 -180 h -90', 'thin') + P('M -112 -146 h -56', 'thin'),
    heavy: (g) => head(96, -206, 40) + P('M 60 -176 L -12 -100') + P('M -12 -100 L -40 -50 L -76 0') + P('M -12 -100 L 2 -48 L -24 0') +
      P('M 56 -170 L 132 -168') + P('M 46 -160 L 132 -136') +
      `<rect class="d paint" x="134" y="-236" width="160" height="236" rx="8"/>` +
      `<text x="214" y="-104" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-weight="800" font-size="50" fill="${INK}">${g.dataset.label || ''}</text>` +
      P('M 140 -262 q 6 -14 10 0 q 0 8 -5 8 q -5 0 -5 -8 Z', 'thin') + P('M 52 -250 q 6 -14 10 0 q 0 8 -5 8 q -5 0 -5 -8 Z', 'thin') +
      P('M 300 -250 l 12 -10 M 306 -226 l 16 -4', 'thin'),
    reads: () => head(0, -256) + P('M 0 -212 L 0 -112') + legs +
      `<path class="d paint" d="M -84 -196 L 0 -178 L 84 -196 L 84 -104 L 0 -86 L -84 -104 Z"/>` + P('M 0 -178 L 0 -86', 'thin') +
      P('M -64 -166 L -18 -158 M -64 -146 L -18 -138 M 18 -158 L 64 -166', 'thin') + dot(-88, -150, 11) + dot(88, -150, 11),
    wonders: () => head(-10, -170) + P('M -10 -126 L -10 -40') + P('M 20 -60 C 50 -86 44 -126 22 -150') + P('M -150 -40 L 160 -40') + cloud(40, -232),
    sits: () => head(-6, -150) + P('M -4 -106 L -10 -4') + P('M -10 -4 L 78 -6 L 86 106') + P('M -10 -4 L 64 -2 L 66 108') + P('M -6 -84 L -44 -36 L -62 -6'),
    pin: () => P('M 0 0 C -18 -26 -40 -50 -40 -76 C -40 -100 -22 -118 0 -118 C 22 -118 40 -100 40 -76 C 40 -50 18 -26 0 0 Z', 'paint') + `<circle class="d" cx="0" cy="-78" r="14"/>`,
    idea: () => P('M -40 -60 C -76 -96 -60 -170 0 -172 C 60 -170 76 -96 40 -60 C 30 -48 28 -36 28 -24 L -28 -24 C -28 -36 -30 -48 -40 -60 Z') +
      P('M -24 -8 L 24 -8 M -18 8 L 18 8') + P('M -10 -26 L -10 -70 Q 0 -88 10 -70 L 10 -26', 'thin') +
      P('M 0 -196 L 0 -226 M -76 -160 L -98 -180 M 76 -160 L 98 -180 M -90 -96 L -120 -96 M 90 -96 L 120 -96', 'yel'),
    choice: () => P('M 0 0 L 0 -200') + P('M -40 0 L 40 0') + `<path class="d paint" d="M -90 -186 L 20 -186 L 20 -146 L -90 -146 L -112 -166 Z"/>` +
      `<path class="d paint" d="M -20 -126 L 92 -126 L 114 -106 L 92 -86 L -20 -86 Z"/>`,
  };
  const COLOR = { cobalt: '#1F4ED8', tomato: '#D7351F', violet: '#6B3FC9', teal: '#0B7A70', magenta: '#C2187A', forest: '#0B452C', ink: INK };
  document.querySelectorAll('[data-doodle]').forEach((g) => {
    g.style.color = COLOR[g.dataset.color] || g.dataset.color || INK;
    g.innerHTML = DOODLE[g.dataset.doodle](g);
    g.querySelectorAll('.paint').forEach((e) => { e.style.fill = g.dataset.paint || '#FFFFFF'; });
  });

  // shared defs: the hand wobble for drawn lines (user space, so straight strokes keep their wobble region),
  // the older #dry filter, and the brand mark ("b." lockup, ink b, red dot)
  const BMARK = `M69.90-143.70Q77.10-155.40 90.60-162.600Q104.10-169.80 121.50-169.80Q142.20-169.80 159-159.30Q175.80-148.80 185.55-129.30Q195.30-109.80 195.300-84Q195.30-58.20 185.55-38.55Q175.80-18.90 159-8.25Q142.20 2.40 121.50 2.40Q103.80 2.40 90.60-4.65Q77.40-11.70 69.90-23.40L69.90 0L18.60 0L18.60-222L69.90-222L69.90-143.70M143.10-84Q143.10-103.20 132.45-114.15Q121.80-125.10 106.20-125.10Q90.900-125.10 80.25-114Q69.600-102.90 69.60-83.70Q69.60-64.50 80.25-53.40Q90.90-42.30 106.20-42.30Q121.50-42.30 132.30-53.55Q143.10-64.80 143.10-84`;
  const defs = document.createElement('div');
  defs.innerHTML = `<svg width="0" height="0" style="position:absolute"><defs>` +
    `<filter id="hand" filterUnits="userSpaceOnUse" x="-4000" y="-4000" width="9000" height="9000"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="7" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3"/></filter>` +
    `<filter id="dry" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="4"/></filter>` +
    `<g id="bmark-shape"><path d="${BMARK}" fill="${INK}"/><circle cx="246" cy="-25" r="30" fill="#E8483B"/></g>` +
    `<g id="bmark-cream"><path d="${BMARK}" fill="#F2ECDE"/><circle cx="246" cy="-25" r="30" fill="#E8483B"/></g></defs></svg>`;
  document.body.prepend(defs.firstChild);
  if (!document.body.dataset.nowm) {
    const wm = document.createElement('div'); wm.id = 'wm';
    const mark = document.body.dataset.page === 'green' ? '#bmark-cream' : '#bmark-shape';
    wm.innerHTML = `<svg viewBox="10 -232 286 262"><use href="${mark}"/></svg><span>binary<b>.</b>semaphore</span>`;
    document.body.appendChild(wm);
    (window.ON_FRAME = window.ON_FRAME || []).push((t) => { wm.style.opacity = t >= window.END ? 0 : ''; });
  }

  // the deal: same frame windows as the runtime (a frame starts 0.3 s before its first beat)
  const TM = window.TIMINGS; if (!TM) return;
  const NB = TM.length, ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const clamp = (x) => Math.max(0, Math.min(1, x));
  const decks = [...document.querySelectorAll('.frame')].map((f, k) => {
    const a = f.dataset.from, z = f.dataset.to;
    const t0 = a === 'end' ? window.END : Math.max(0, TM[+a].start - 0.3);
    const t1 = z === 'end' ? 1e9 : (+z + 1 < NB ? TM[+z + 1].start - 0.3 : window.END);
    return { st: f.querySelector('.stage'), t0, t1, k };
  }).filter((d) => d.st);
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => {
    decks.forEach(({ st, t0, t1, k }) => {
      const pin = k === 0 ? 1 : ease(clamp((t - t0) / 0.55)), out = ease(clamp((t - t1) / 0.3));
      st.style.translate = `${(1 - pin) * 1150 - out * 1250}px ${(1 - pin) * 40}px`;
      st.style.rotate = `${(1 - pin) * 6 - out * 8}deg`;
    });
  });
})();
