// Theme "blueprint": the sky and the ruled grid behind every frame (16:9 and 9:16), drawn once; the sky drifts slowly.
// Load after runtime.js.
(function () {
  const land = innerWidth > innerHeight, W = land ? 1920 : 1080, H = land ? 1080 : 1920;
  const sky = document.createElement('div'); sky.className = 'bp-sky'; document.body.prepend(sky);
  const ns = 'http://www.w3.org/2000/svg', S = document.createElementNS(ns, 'svg');
  S.setAttribute('class', 'bp-grid'); S.setAttribute('width', W); S.setAttribute('height', H); sky.after(S);
  const el = (t, a) => { const e = document.createElementNS(ns, t); for (const k in a) e.setAttribute(k, a[k]); S.appendChild(e); return e; };
  const u = land ? 80 : 50, nx = land ? 20 : 18, ny = land ? 10 : 34;
  const x0 = (W - nx * u) / 2, y0 = (H - ny * u) / 2, x1 = x0 + nx * u, y1 = y0 + ny * u;
  for (let i = 0; i <= nx * 2; i++) el('line', { x1: x0 + i * u / 2, y1: y0, x2: x0 + i * u / 2, y2: y1, class: i % 10 === 0 ? 'g5' : 'g1' });
  for (let j = 0; j <= ny * 2; j++) el('line', { x1: x0, y1: y0 + j * u / 2, x2: x1, y2: y0 + j * u / 2, class: j % 10 === 0 ? 'g5' : 'g1' });
  for (let i = 0; i <= nx; i++) { const x = x0 + i * u;
    el('line', { x1: x, y1: y0 - 22, x2: x, y2: y0 - (i % 5 ? 10 : 2), class: 'tick' }); el('line', { x1: x, y1: y1 + 22, x2: x, y2: y1 + (i % 5 ? 10 : 2), class: 'tick' });
    if (i % 5 === 0) { const t = el('text', { x, y: y0 - 34, 'text-anchor': 'middle', class: 'num' }); t.textContent = i; } }
  for (let j = 0; j <= ny; j++) { const y = y1 - j * u;
    el('line', { x1: x0 - 22, y1: y, x2: x0 - (j % 5 ? 10 : 2), y2: y, class: 'tick' }); el('line', { x1: x1 + 22, y1: y, x2: x1 + (j % 5 ? 10 : 2), y2: y, class: 'tick' });
    if (j % 5 === 0) { const t = el('text', { x: x0 - 34, y: y + 7, 'text-anchor': 'end', class: 'num' }); t.textContent = j; const v = el('text', { x: x1 + 34, y: y + 7, class: 'num' }); v.textContent = j; } }
  [15, 30, 45, 60].forEach((a) => { const r = a * Math.PI / 180; el('line', { x1: x0, y1: y1, x2: x0 + 3000 * Math.cos(r), y2: y1 - 3000 * Math.sin(r), class: 'dash' }); });
  const R = Math.min(x1 - x0, y1 - y0) * 0.95;
  el('path', { d: `M ${x0 + R} ${y1} A ${R} ${R} 0 0 0 ${x0} ${y1 - R}`, class: 'dash', style: 'stroke-dasharray:none;stroke:rgba(244,246,255,.45)' });
  S.style.clipPath = `inset(0 0 0 0)`;
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => { sky.style.transform = `translate(${Math.sin(t / 9) * 40}px, ${Math.cos(t / 11) * 30}px)`; });
})();
