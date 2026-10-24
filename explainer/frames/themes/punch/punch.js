// Theme "punch": tiny flat figures with a thick black outline (studies/18-inspired.png), the brand
// mark, grain, and the punchline fit. Load after runtime.js:
//   <script src=".../runtime.js"></script><script src=".../themes/punch.js"></script>
// Figures (feet at 0,0, about 170 px tall at scale 1):
//   <g data-fig="agent sit" transform="translate(380 1360) scale(1.5)"></g>
//   kinds: agent (cream robot), stranger (dark), human (orange top)
//   poses: stand walk keyup shrug bow sit ask lens sign
// Line people instead of flat cartoons: <body data-figs="line"> (see inkPerson below).
// Props: <g data-prop="key|letter|page|podium|grass|sign:TEXT|bubble:TEXT" transform="..."></g>
(function () {
  const C = { cream: '#F2ECDE', dark: '#1E2A2A', orange: '#C8643B', pants: '#0E4A4E', skin: '#8A6A4E',
    yel: '#F8EB44', grass: '#3E8A5A', paper: '#E9E6DA', line: '#7D7A72' };
  const seg = (pts) => 'M ' + pts.map((p) => p.join(' ')).join(' L ');
  const limb = (pts, w, col) => `<path d="${seg(pts)}" stroke="#000" stroke-width="${w + 8}" fill="none"/>` +
    `<path d="${seg(pts)}" stroke="${col}" stroke-width="${w}" fill="none"/>`;
  const stand = { hip: [0, -74], neck: [4, -128], head: [8, -150], la: [[-8, -100], [-12, -74]], ra: [[16, -100], [20, -74]],
    ll: [[-6, -38], [-12, 0]], rl: [[6, -38], [12, 0]] };
  const POSES = {
    stand,
    walk: { ...stand, neck: [8, -128], head: [12, -150], la: [[-10, -102], [-20, -82]], ra: [[24, -100], [36, -84]],
      ll: [[-12, -38], [-26, 0]], rl: [[12, -40], [24, 0]] },
    keyup: { ...stand, ra: [[26, -140], [32, -170]] },
    shrug: { ...stand, la: [[-26, -112], [-34, -136]], ra: [[34, -112], [42, -136]] },
    bow: { ...stand, neck: [46, -104], head: [70, -94], la: [[50, -80], [52, -56]], ra: [[58, -80], [62, -56]] },
    sit: { hip: [0, -24], neck: [-8, -80], head: [-10, -104], la: [[14, -58], [38, -76]], ra: [[20, -62], [44, -84]],
      ll: [[36, -42], [66, -4]], rl: [[42, -34], [74, 0]] },
    ask: { ...stand, ra: [[36, -128], [52, -178]] },
    lens: { ...stand, neck: [18, -124], head: [26, -148], ra: [[42, -106], [66, -96]] },
    sign: { ...stand, la: [[-22, -160], [-14, -226]], ra: [[30, -160], [24, -226]] },
  };
  const KINDS = {
    agent: { body: C.cream, arm: C.cream, leg: C.cream, tw: 34, aw: 13, lw: 14 },
    stranger: { body: C.dark, arm: C.dark, leg: C.dark, tw: 27, aw: 10, lw: 12, head: C.dark, hand: C.dark },
    human: { body: C.orange, arm: C.orange, leg: C.pants, tw: 30, aw: 11, lw: 13, head: C.skin, hand: C.skin },
  };
  function head(kind, [x, y]) {
    if (kind === 'agent') {
      y -= 8;
      return `<rect x="${x - 27}" y="${y - 24}" width="54" height="46" rx="11" fill="${C.cream}" stroke="#000" stroke-width="5"/>` +
        `<path d="M ${x - 15} ${y - 2} q 5 5 10 0 M ${x + 5} ${y - 2} q 5 5 10 0" stroke="#000" stroke-width="4.5" fill="none"/>` +
        `<path d="M ${x} ${y - 24} L ${x + 4} ${y - 46}" stroke="#000" stroke-width="5"/>` +
        `<circle cx="${x + 5}" cy="${y - 54}" r="10" fill="${C.yel}" stroke="#000" stroke-width="4"/>`;
    }
    const k = KINDS[kind];
    const hair = kind === 'human' ? `<path d="M ${x - 15} ${y - 6} Q ${x - 4} ${y - 26} ${x + 16} ${y - 8} Q ${x + 6} ${y - 14} ${x - 15} ${y - 6} Z" fill="#111" stroke="#000" stroke-width="3"/>` : '';
    return `<circle cx="${x}" cy="${y}" r="16" fill="${k.head}" stroke="#000" stroke-width="5"/>${hair}`;
  }
  function person(kind, pose) {
    const p = POSES[pose], k = KINDS[kind];
    const sh = [p.neck[0] + (p.hip[0] - p.neck[0]) * 0.12, p.neck[1] + (p.hip[1] - p.neck[1]) * 0.12];
    const hand = (h) => k.hand ? `<circle cx="${h[0]}" cy="${h[1]}" r="7" fill="${k.hand}" stroke="#000" stroke-width="3.5"/>` : '';
    const foot = (f) => kind === 'agent' ? '' : `<ellipse cx="${f[0] + 4}" cy="${f[1] - 2}" rx="11" ry="6" fill="#111" stroke="#000" stroke-width="3"/>`;
    return `<g stroke-linecap="round" stroke-linejoin="round">` +
      limb([sh, ...p.la], k.aw, k.arm) + hand(p.la[1]) +
      limb([p.hip, ...p.ll], k.lw, k.leg) + limb([p.hip, ...p.rl], k.lw, k.leg) + foot(p.ll[1]) + foot(p.rl[1]) +
      limb([p.hip, p.neck], k.tw, k.body) + head(kind, p.head) +
      limb([sh, ...p.ra], k.aw, k.arm) + hand(p.ra[1]) + '</g>';
  }
  const PROPS = {
    key: () => `<g stroke-linecap="round"><circle cx="0" cy="-12" r="11" fill="none" stroke="#000" stroke-width="11"/>` +
      `<circle cx="0" cy="-12" r="11" fill="none" stroke="${C.yel}" stroke-width="6"/>` +
      `<path d="M -5 -2 L -17 22 M -14 16 L -5 20" stroke="#000" stroke-width="11" fill="none"/>` +
      `<path d="M -5 -2 L -17 22 M -14 16 L -5 20" stroke="${C.yel}" stroke-width="6" fill="none"/></g>`,
    letter: () => `<rect x="-30" y="-40" width="60" height="80" rx="3" fill="${C.paper}" stroke="#000" stroke-width="4"/>` +
      `<path d="M -18 -24 h 36 M -18 -12 h 30 M -18 0 h 36 M -18 12 h 22" stroke="${C.line}" stroke-width="3"/>`,
    page: () => `<rect x="-70" y="-95" width="140" height="190" rx="4" fill="${C.paper}" stroke="#000" stroke-width="5"/>`,
    podium: () => `<g stroke="#000" stroke-width="5"><rect x="-150" y="-60" width="100" height="60" fill="${C.cream}"/>` +
      `<rect x="-50" y="-110" width="100" height="110" fill="${C.cream}"/><rect x="50" y="-40" width="100" height="40" fill="${C.cream}"/></g>` +
      `<text x="0" y="-38" text-anchor="middle" font-family="Inter" font-weight="900" font-size="56" fill="${C.field || '#0B452C'}">1</text>`,
    grass: (w = 140) => `<path d="${[...Array(6)].map((_, i) => { const x = -w / 2 + (i * w) / 5; return `M ${x} 4 l ${(i % 2 ? 4 : -5)} -16`; }).join(' ')}" stroke="${C.grass}" stroke-width="6" stroke-linecap="round" fill="none"/>`,
    sign: (t) => `<rect x="-96" y="-46" width="192" height="58" rx="6" fill="${C.cream}" stroke="#000" stroke-width="5"/>` +
      `<text x="0" y="-8" text-anchor="middle" font-family="Inter" font-weight="800" font-size="22" fill="#111">${t}</text>`,
    bubble: (t) => `<path d="M -40 -70 h 80 a 12 12 0 0 1 12 12 v 34 a 12 12 0 0 1 -12 12 h -50 l -16 16 l 2 -16 h -16 a 12 12 0 0 1 -12 -12 v -34 a 12 12 0 0 1 12 -12 Z" fill="${C.cream}" stroke="#000" stroke-width="5"/>` +
      `<text x="0" y="-27" text-anchor="middle" font-family="Inter" font-weight="900" font-size="36" fill="#111">${t}</text>`,
  };

  // <body data-figs="line">: the field theme's cream ink people instead (single-weight line, no fill),
  // same poses and props. Characters differ by one detail: the agent's square head and yellow light,
  // the stranger's hood. The key keeps its yellow: it is the one thing everyone wants.
  const INK = 'stroke="#F2ECDE" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"', HOLE = '#0B452C';
  function inkPerson(kind, pose) {
    const p = POSES[pose], line = (pts) => `<path d="${seg(pts)}" fill="none" ${INK}/>`;
    const sh = [p.neck[0] + (p.hip[0] - p.neck[0]) * 0.12, p.neck[1] + (p.hip[1] - p.neck[1]) * 0.12];
    // torso: a narrow outlined wedge from the shoulders to the hips, filled so limbs behind it are hidden
    const dx = p.neck[0] - p.hip[0], dy = p.neck[1] - p.hip[1], L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L;
    const torso = `<path d="M ${p.neck[0] + nx * 11} ${p.neck[1] + ny * 11} L ${p.hip[0] + nx * 8} ${p.hip[1] + ny * 8} ` +
      `L ${p.hip[0] - nx * 8} ${p.hip[1] - ny * 8} L ${p.neck[0] - nx * 11} ${p.neck[1] - ny * 11} Z" fill="${HOLE}" ${INK}/>`;
    const foot = (k, f) => { const d = f[0] >= k[0] ? 9 : -9; return line([f, [f[0] + d, f[1]]]); };
    let head;
    const [x, y] = p.head;
    if (kind === 'agent') {
      head = `<rect x="${x - 17}" y="${y - 24}" width="34" height="30" rx="6" fill="${HOLE}" ${INK}/>` +
        `<path d="M ${x - 9} ${y - 10} q 3 3 6 0 M ${x + 3} ${y - 10} q 3 3 6 0" fill="none" ${INK.replace('4.5', '3')}/>` +
        line([[x, y - 24], [x + 2, y - 38]]) + `<circle cx="${x + 2}" cy="${y - 43}" r="6" fill="${C.yel}"/>`;
    } else {
      head = `<circle cx="${x}" cy="${y}" r="12" fill="${HOLE}" ${INK}/>`;
      if (kind === 'stranger') head += `<path d="M ${x - 15} ${y + 12} C ${x - 22} ${y - 10} ${x - 12} ${y - 24} ${x} ${y - 24} C ${x + 12} ${y - 24} ${x + 22} ${y - 10} ${x + 15} ${y + 12}" fill="none" ${INK}/>`;
    }
    return line([sh, ...p.la]) + line([p.hip, ...p.ll]) + line([p.hip, ...p.rl]) + foot(p.ll[0], p.ll[1]) + foot(p.rl[0], p.rl[1]) +
      torso + head + line([sh, ...p.ra]);
  }
  const INK_PROPS = {
    key: () => `<g stroke="${C.yel}" stroke-width="7" stroke-linecap="round" fill="none"><circle cx="0" cy="-12" r="10"/><path d="M -5 -3 L -16 20 M -13 14 L -5 18"/></g>`,
    letter: () => `<rect x="-30" y="-40" width="60" height="80" rx="3" fill="${HOLE}" ${INK}/>` +
      `<path d="M -18 -24 h 36 M -18 -12 h 30 M -18 0 h 36 M -18 12 h 22" stroke="#F2ECDE" stroke-width="3" opacity=".55" stroke-linecap="round"/>`,
    page: () => `<rect x="-70" y="-95" width="140" height="190" rx="4" fill="${HOLE}" ${INK}/>`,
    podium: () => `<g fill="${HOLE}" ${INK}><rect x="-150" y="-60" width="100" height="60"/><rect x="-50" y="-110" width="100" height="110"/><rect x="50" y="-40" width="100" height="40"/></g>` +
      `<text x="0" y="-38" text-anchor="middle" font-family="Inter" font-weight="900" font-size="56" fill="#F2ECDE">1</text>`,
    grass: () => `<ellipse cx="0" cy="2" rx="30" ry="6" fill="rgba(4,22,12,.45)"/>`,
    sign: (t) => `<rect x="-96" y="-46" width="192" height="58" rx="6" fill="${HOLE}" ${INK}/>` +
      `<text x="0" y="-8" text-anchor="middle" font-family="Inter" font-weight="800" font-size="22" fill="#F2ECDE">${t}</text>`,
    bubble: (t) => `<path d="M -40 -70 h 80 a 12 12 0 0 1 12 12 v 34 a 12 12 0 0 1 -12 12 h -50 l -16 16 l 2 -16 h -16 a 12 12 0 0 1 -12 -12 v -34 a 12 12 0 0 1 12 -12 Z" fill="${HOLE}" ${INK}/>` +
      `<text x="0" y="-27" text-anchor="middle" font-family="Inter" font-weight="900" font-size="36" fill="#F2ECDE">${t}</text>`,
  };
  const ink = document.body.dataset.figs === 'line';
  document.querySelectorAll('[data-fig]').forEach((g) => { const [kind, pose] = g.dataset.fig.split(' '); g.innerHTML = (ink ? inkPerson : person)(kind, pose); });
  document.querySelectorAll('[data-prop]').forEach((g) => { const [k, ...arg] = g.dataset.prop.split(':'); g.innerHTML = (ink ? INK_PROPS : PROPS)[k](arg.join(':') || undefined); });

  // brand mark: the "b." lockup (cream b, red dot) next to "binary.semaphore", vertically centred,
  // matching the owner's logo. A gentle turbulence wobble gives the mark a hand-drawn edge.
  const BMARK = `M69.90-143.70Q77.10-155.40 90.60-162.600Q104.10-169.80 121.50-169.80Q142.20-169.80 159-159.30Q175.80-148.80 185.55-129.30Q195.30-109.80 195.300-84Q195.30-58.20 185.55-38.55Q175.80-18.90 159-8.25Q142.20 2.40 121.50 2.40Q103.80 2.40 90.60-4.65Q77.40-11.70 69.90-23.40L69.90 0L18.60 0L18.60-222L69.90-222L69.90-143.70M143.10-84Q143.10-103.20 132.45-114.15Q121.80-125.10 106.20-125.10Q90.900-125.10 80.25-114Q69.600-102.90 69.60-83.70Q69.60-64.50 80.25-53.40Q90.90-42.30 106.20-42.30Q121.50-42.30 132.30-53.55Q143.10-64.80 143.10-84`;
  const DOT = '#E8483B';
  const wm = document.createElement('div'); wm.id = 'wm';
  wm.innerHTML = `<svg class="wmark" viewBox="10 -232 286 262">` +
    `<path d="${BMARK}" fill="${C.cream}" filter="url(#wmdry)"/>` +
    `<circle cx="246" cy="-22" r="32" fill="${DOT}" filter="url(#wmdry)"/></svg>` +
    `<span>binary<b>.</b>semaphore</span>`;
  document.body.appendChild(wm);
  const defs = document.createElement('div');
  defs.innerHTML = `<svg width="0" height="0" style="position:absolute"><defs>` +
    `<filter id="wmdry" x="-15%" y="-15%" width="130%" height="130%"><feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3"/></filter>` +
    `<g id="bmark-shape"><path d="${BMARK}" fill="${C.cream}"/><circle cx="246" cy="-25" r="30" fill="${DOT}"/></g></defs></svg>`;
  document.body.prepend(defs.firstChild);
  // leafy green background for vertical posts (owner likes the field theme's dappled light):
  // baked leaf PNGs drift slowly behind each frame, or behind the cover body. CSS hides them in
  // landscape, so the LinkedIn cut stays flat green.
  const leafBase = (document.currentScript && document.currentScript.src || '').replace(/[^/]*$/, '') + '../field/';   // the leaf light belongs to the field theme
  const leafHosts = document.querySelectorAll('.frame').length ? [...document.querySelectorAll('.frame')] : [document.body];
  const leaves = [];
  leafHosts.forEach((h, k) => {
    const img = document.createElement('img');
    img.className = 'leaf soft'; img.src = leafBase + 'leaf-' + ((k % 8) + 1) + '.png';
    const vig = document.createElement('div'); vig.className = 'vignette';
    h.prepend(vig); h.prepend(img);
    leaves.push({ img, k });
  });
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => {
    leaves.forEach(({ img, k }) => { img.style.transform = 'translate(' + (40 * Math.sin(t * 0.11 + k)).toFixed(1) + 'px,' + (30 * Math.cos(t * 0.08 + k * 1.7)).toFixed(1) + 'px)'; });
  });

  if (!document.getElementById('grain')) { const g = document.createElement('div'); g.id = 'grain'; document.body.appendChild(g); }

  // the punchline fills at most the safe width, whatever its length; runs again once fonts are in
  const fit = () => document.querySelectorAll('.huge').forEach((e) => {
    if (!e.firstElementChild || e.firstElementChild.tagName !== 'SPAN') e.innerHTML = `<span>${e.innerHTML}</span>`;
    e.style.fontSize = ''; const max = document.documentElement.clientWidth - 140;
    let fs = parseFloat(getComputedStyle(e).fontSize);
    while (e.firstElementChild.getBoundingClientRect().width > max && fs > 80) { fs -= 6; e.style.fontSize = fs + 'px'; }
  });
  fit();
  // the corner mark steps aside for the end card's big mark
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => { wm.style.opacity = t >= window.END ? 0 : ''; });
  const measure = window.MEASURE;
  window.MEASURE = () => { fit(); measure && measure(); };
})();
