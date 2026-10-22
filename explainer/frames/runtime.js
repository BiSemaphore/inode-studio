// Frames runtime: vertical, narration-timed pages (one idea per frame).
// A page is plain HTML with data attributes; every frame is a pure function of t,
// so explainer/frames/render.js can render any frame deterministically.
//
// Timing specs: "b3" (beat 3 starts), "b3+0.2", "w3:word" (first time the word is
// said in beat 3), "w3:word-0.1". Times come from voice/timings.json (window.TIMINGS).
//
//   <div class="frame" data-from="2" data-to="4">        shown from beat 2 to beat 4 ("end" = end card)
//   data-at="w2:word"                                     fade + rise in
//   data-out="w5:word"                                    fade out
//   data-hl="w2:word"                                     highlighter sweep (class hl)
//   <path class="pen" data-t0 data-t1 [data-head]>        line draws itself, arrowhead from the real end tangent
//   <span class="type" data-text data-t0 data-t1>         typed text (adds key sounds)
//   <i data-strike="w3:word">                             strike-through line (inside .strike)
//   data-move="spec|dx,dy|dur"                            moves by dx,dy starting at spec
//   data-fill="t0spec|t1spec"                             width grows 0 -> 100% (progress bar)
//   data-pulse="t0spec|t1spec"                            rings while working
//   <div class="stack" data-t0 data-t1 data-cap="9">     lines appear in turn; scrolls up once more than cap
// Frames with class "grid" get ruler numbers on both edges (blueprint theme).
(function () {
  const TM = window.TIMINGS, NB = TM.length;
  const END = TM[NB - 1].end + 0.35, TOTAL = END + (window.END_HOLD || 2.0);
  const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const clamp = (x) => Math.max(0, Math.min(1, x));
  function T(spec) {
    if (/^\d+(\.\d+)?$/.test(String(spec))) return +spec;   // plain seconds
    const m = String(spec).match(/^([bw])(\d+)(?::([^+-]+))?([+-][\d.]+)?$/);
    if (!m) throw new Error('bad time ' + spec);
    const b = TM[+m[2]], off = m[4] ? parseFloat(m[4]) : 0;
    if (m[1] === 'b') return b.start + off;
    const w = b.words.find((x) => x[0] === m[3]);
    if (!w) throw new Error('no word ' + spec + ' in: ' + b.words.map((x) => x[0]).join(' '));
    return w[1] + off;
  }
  const all = (sel) => [...document.querySelectorAll(sel)];

  // rulers on grid frames: a number every 180 px, like a cutting mat
  all('.frame.grid').forEach((f) => {
    for (const side of ['l', 'r']) {
      for (let y = 180, n = 5; y < 1920; y += 180, n += 5) {
        const d = document.createElement('div');
        d.className = 'ruler ' + side; d.style.top = y - 12 + 'px'; d.textContent = n;
        f.appendChild(d);
      }
      for (let y = 36; y < 1920; y += 36) {               // ticks between the numbers
        if (y % 180 === 0) continue;
        const k = document.createElement('div');
        k.className = 'tick ' + side; k.style.top = y + 'px';
        f.appendChild(k);
      }
    }
    // data-construct: dashed angle lines and a protractor arc from the lower-left corner
    if (f.hasAttribute('data-construct')) {
      const ox = 90, oy = 1800, R = 760, NS = 'http://www.w3.org/2000/svg';
      const s = document.createElementNS(NS, 'svg');
      s.setAttribute('class', 'construct'); s.setAttribute('width', 1080); s.setAttribute('height', 1920);
      const col = f.classList.contains('mist') ? 'rgba(28,66,80,.28)' : 'rgba(217,201,138,.30)';
      let inner = `<path d="M ${ox + R} ${oy} A ${R} ${R} 0 0 0 ${ox} ${oy - R}" stroke="${col}" stroke-width="2" fill="none"/>`;
      for (const deg of [15, 30, 45, 60]) {
        const a = deg * Math.PI / 180, x = ox + 1400 * Math.cos(a), y = oy - 1400 * Math.sin(a);
        inner += `<path d="M ${ox} ${oy} L ${x} ${y}" stroke="${col}" stroke-width="2" stroke-dasharray="10 12"/>`;
        const lx = ox + (R * 0.42) * Math.cos(a) + 6, ly = oy - (R * 0.42) * Math.sin(a) - 8;
        inner += `<text x="${lx}" y="${ly}" font-family="JetBrains Mono" font-size="22" fill="${col}">${deg}°</text>`;
      }
      s.innerHTML = inner;
      f.insertBefore(s, f.firstChild);
    }
  });

  const frames = all('.frame').map((f, k) => {
    const a = f.dataset.from, z = f.dataset.to;
    const t0 = a === 'end' ? END : Math.max(0, TM[+a].start - 0.3);
    const t1 = z === 'end' ? 1e9 : (+z + 1 < NB ? TM[+z + 1].start - 0.3 : END);
    return { f, t0, t1, k };
  });
  const els = all('[data-at]').map((e) => ({ e, at: T(e.dataset.at), out: e.dataset.out ? T(e.dataset.out) : 1e9,
    base: getComputedStyle(e).opacity === '0' ? 1 : +getComputedStyle(e).opacity }));
  const hls = all('[data-hl]').map((e) => ({ e, at: T(e.dataset.hl) }));
  const strikes = all('[data-strike]').map((e) => ({ e, at: T(e.dataset.strike) }));
  const moves = all('[data-move]').map((e) => {
    const [s, d, dur] = e.dataset.move.split('|'); const [dx, dy] = d.split(',').map(Number);
    return { e, at: T(s), dx, dy, dur: +(dur || 0.8) };
  });
  const fills = all('[data-fill]').map((e) => { const [a, b] = e.dataset.fill.split('|'); return { e, t0: T(a), t1: T(b) }; });
  const pulses = all('[data-pulse]').map((e) => { const [a, b] = e.dataset.pulse.split('|'); return { e, t0: T(a), t1: T(b) }; });
  const stacks = all('.stack').map((e) => {
    const lines = [...e.children], t0 = T(e.dataset.t0), t1 = T(e.dataset.t1), cap = +(e.dataset.cap || 9);
    return { e, lines, t0, t1, cap, lh: lines[0].getBoundingClientRect().height };
  });
  const pens = [];
  all('.pen').forEach((e) => {
    const L = e.getTotalLength(); e.style.strokeDasharray = `${L} ${L}`;
    const t0 = T(e.dataset.t0), t1 = T(e.dataset.t1);
    pens.push({ e, L, t0, t1 });
    if (e.dataset.head) {
      const p = e.getPointAtLength(L), q = e.getPointAtLength(L - 6);
      const a = Math.atan2(p.y - q.y, p.x - q.x), k = 26;
      const h = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      h.setAttribute('d', `M ${p.x - k * Math.cos(a - 0.5)} ${p.y - k * Math.sin(a - 0.5)} L ${p.x} ${p.y} L ${p.x - k * Math.cos(a + 0.5)} ${p.y - k * Math.sin(a + 0.5)}`);
      ['stroke', 'stroke-width', 'stroke-linecap'].forEach((n) => h.setAttribute(n, e.getAttribute(n) || ''));
      h.setAttribute('stroke-linejoin', 'round'); h.setAttribute('fill', 'none');
      h.setAttribute('class', (e.getAttribute('class') || '').replace(/\bpen\b/, ''));   // same look as its line
      e.after(h);
      const HL = h.getTotalLength(); h.style.strokeDasharray = `${HL} ${HL}`;
      pens.push({ e: h, L: HL, t0: t1, t1: t1 + 0.15, head: true });
    }
  });
  const types = all('.type').map((e) => ({ e, text: e.dataset.text, t0: T(e.dataset.t0), t1: T(e.dataset.t1) }));

  // Sound cues for the mixer: one key per typed character, a tick per bubble.
  window.CUES = {
    keys: types.flatMap((y) => [...y.text].map((_, k) => y.t0 + (y.t1 - y.t0) * (k + 1) / y.text.length)),
    ticks: els.filter(({ e }) => e.classList.contains('bubble')).map(({ at }) => at),
    // drawn sound: a pen scratch while each line draws, a paper tap when things appear (one per
    // 0.15 s cluster), a swish per headline, air when a thing travels or the frame changes
    draws: pens.filter((p) => !p.head && p.t0 < END).map(({ t0, t1 }) => [t0, t1 - t0]).concat(window.WRITES || []),   // WRITES: page-made pen reveals
    taps: els.filter(({ e, at }) => at < END && !e.classList.contains('brush') && !e.closest('.sub-bubble'))
      .map(({ at }) => at).sort((a, b) => a - b).filter((t, i, a) => i === 0 || t - a[i - 1] > 0.15),
    brushes: els.filter(({ e }) => e.classList.contains('brush')).map(({ at }) => at).filter((t) => t < END),
    moves: moves.map(({ at, dur }) => [at, dur]),
    zooms: window.ZOOMS || [], checks: window.CHECKS || [],
    cuts: frames.filter(({ k, t0 }) => k > 0 && t0 > 0.5 && t0 < 1e8).map(({ t0 }) => t0),
  };
  window.TOTAL = TOTAL; window.END = END;

  // ---------- subtitles: a hand-drawn speech bubble (studies/24-speech-bubble.md) ----------
  // Built from the spoken words in TIMINGS. Each beat splits at sentence ends into chunks of
  // at most ~2 lines; words appear as they are said. window.CIRCLE = {beat: "phrase"} loops a
  // hand-drawn circle around that phrase once it has been said. The bubble takes the opposite
  // colour of the frame under it (mist on teal, teal on mist).
  const subs = [];
  if (window.SUBTITLES !== false) {
    const frameOf = (k) => frames.find(({ f }) => f.dataset.from !== 'end' && +f.dataset.from <= k && k <= +f.dataset.to);
    const norm = (w) => w.toLowerCase().replace(/[^a-z0-9']/g, '');
    TM.forEach((b, k) => {
      // chunks: one sentence each; a sentence over ~44 characters splits once, after a comma
      // if there is one near the middle, else at the word nearest the middle.
      const chunks = [], sentences = []; let cur = [];
      b.words.forEach((w, i) => { cur.push(w); if (/[.:?!]$/.test(w[0]) || i === b.words.length - 1) { sentences.push(cur); cur = []; } });
      const len = (ws) => ws.map((x) => x[0]).join(' ').length;
      sentences.forEach((ws) => {
        if (len(ws) <= 46 || ws.length < 6) { chunks.push(ws); return; }
        let best = -1, score = 1e9;
        for (let i = 2; i < ws.length - 2; i++) {
          const d = Math.abs(len(ws.slice(0, i)) - len(ws) / 2) - (/,$/.test(ws[i - 1][0]) ? 14 : 0);
          if (d < score) { score = d; best = i; }
        }
        chunks.push(ws.slice(0, best), ws.slice(best));
      });
      const onMist = (frameOf(k) || {}).f?.classList.contains('mist');
      chunks.forEach((ws) => {
        const el = document.createElement('div');
        el.className = 'sub-bubble ' + (onMist ? 'on-mist' : 'on-teal');
        const tx = document.createElement('div'); tx.className = 'sub-text';
        const spans = ws.map(([w]) => { const s = document.createElement('span'); s.textContent = w + ' '; tx.appendChild(s); return s; });
        el.appendChild(tx);
        document.body.appendChild(el);
        const sub = { el, spans, ws, t0: ws[0][1] - 0.08, t1: ws[ws.length - 1][2] };
        const phrase = (window.CIRCLE || {})[k];
        if (phrase) {
          const p = phrase.split(/\s+/).map(norm), ns = ws.map(([w]) => norm(w));
          const at = ns.findIndex((_, i) => p.every((x, j) => ns[i + j] === x));
          if (at >= 0) {
            // keep the circled phrase on one line
            const keep = document.createElement('span'); keep.style.whiteSpace = 'nowrap'; keep.style.opacity = 1;
            spans[at].before(keep);
            spans.slice(at, at + p.length).forEach((sp) => keep.appendChild(sp));
            sub.circle = { a: spans[at], z: spans[at + p.length - 1], at: ws[at + p.length - 1][1] };
          }
        }
        subs.push(sub);
      });
    });
    // each bubble is fully gone before the next one starts
    window.MEASURE = () => subs.forEach((sub) => {
      if (!sub.circle) return;
      sub.el.querySelector('.sub-loop')?.remove();
      const prev = sub.el.style.opacity; sub.el.style.opacity = 1;
      const br = sub.el.getBoundingClientRect(), ra = sub.circle.a.getBoundingClientRect(), rz = sub.circle.z.getBoundingClientRect();
      const x0 = ra.left - br.left - 2, x1 = rz.right - br.left - 4, y0 = Math.min(ra.top, rz.top) - br.top - 4, y1 = Math.max(ra.bottom, rz.bottom) - br.top + 2;
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, rx = (x1 - x0) / 2 + 4, ry = (y1 - y0) / 2 + 6;
      let d = '';
      for (let i = 0; i <= 48; i++) {                       // a pen loop that overshoots its start
        const th = -2.5 + (i / 48) * (Math.PI * 2 + 0.45), g = 1 + 0.05 * (i / 48);
        d += (i ? ' L ' : 'M ') + (cx + rx * g * Math.cos(th)).toFixed(1) + ' ' + (cy + ry * g * Math.sin(th)).toFixed(1);
      }
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('class', 'sub-loop'); svg.setAttribute('width', br.width); svg.setAttribute('height', br.height);
      svg.innerHTML = `<path d="${d}" fill="none" stroke-width="4" stroke-linecap="round"/>`;
      sub.el.appendChild(svg);
      const path = svg.firstChild, L = path.getTotalLength();
      path.style.strokeDasharray = `${L} ${L}`;
      sub.loop = { path, L, at: sub.circle.at };
      sub.el.style.opacity = prev;
    });
    window.MEASURE();
    subs.forEach((s, i) => {
      // back-to-back lines swap in one frame (no fade, no empty frame between them); a line
      // fades only when it starts or ends a run.
      const n = subs[i + 1];
      if (n && n.t0 - (s.t1 + 0.9) < 0.25) { s.t1 = n.t0; s.cut = true; n.cutIn = true; } else s.t1 = s.t1 + 0.9;
    });
  }

  window.renderFrame = (t) => {
    (window.ON_FRAME || []).forEach((fn) => fn(t));   // theme hooks (field: leaf light drift)
    subs.forEach(({ el, spans, ws, t0, t1, loop, cut, cutIn }) => {
      el.style.opacity = (cutIn ? (t >= t0 ? 1 : 0) : clamp((t - t0) / 0.12)) * (cut ? (t < t1 ? 1 : 0) : 1 - clamp((t - t1) / 0.12));
      spans.forEach((s, i) => { s.style.opacity = i === 0 || t >= ws[i][1] - 0.04 ? 1 : 0; });   // never an empty bubble
      if (loop) loop.path.style.strokeDashoffset = loop.L * (1 - ease(clamp((t - loop.at) / 0.45)));
    });
    frames.forEach(({ f, t0, t1, k }) => {
      f.style.opacity = clamp((t - t0) / 0.3) * (t < t1 + 0.3 ? 1 : 0);
      f.style.zIndex = k;
    });
    els.forEach(({ e, at, out, base }) => {
      const p = ease(clamp((t - at) / 0.35)) * (1 - ease(clamp((t - out) / 0.3)));
      e.style.opacity = p * base;
      e.style.translate = `0 ${(1 - ease(clamp((t - at) / 0.35))) * 24}px`;
    });
    moves.forEach(({ e, at, dx, dy, dur }) => { const p = ease(clamp((t - at) / dur)); e.style.transform = `translate(${dx * p}px, ${dy * p}px)`; });
    hls.forEach(({ e, at }) => { const p = ease(clamp((t - at) / 0.4)); e.style.backgroundSize = `${p * 100}% var(--hl-h, 100%)`; });
    strikes.forEach(({ e, at }) => { e.style.transform = `scaleX(${ease(clamp((t - at) / 0.3))})`; });
    fills.forEach(({ e, t0, t1 }) => { e.style.width = `${clamp((t - t0) / (t1 - t0)) * 100}%`; });
    pulses.forEach(({ e, t0, t1 }) => {
      const on = t >= t0 && t <= t1, ph = ((t - t0) % 1.0) / 1.0;
      e.style.boxShadow = on ? `0 0 0 ${ph * 26}px rgba(202,255,166,${0.55 * (1 - ph)})` : 'none';
    });
    stacks.forEach(({ lines, t0, t1, cap, lh }) => {
      const n = lines.length, shown = Math.floor(clamp((t - t0) / (t1 - t0)) * n + 1e-6);
      const shift = Math.max(0, shown - cap);
      lines.forEach((l, i) => {
        l.style.opacity = i < shown ? 1 : 0;
        l.style.transform = `translateY(${-shift * lh}px)`;
      });
    });
    // eased like data-move, so anything travelling with a line stays at its tip
    pens.forEach(({ e, L, t0, t1 }) => { e.style.visibility = t < t0 ? 'hidden' : ''; e.style.strokeDashoffset = L * (1 - ease(clamp((t - t0) / (t1 - t0)))); });
    types.forEach(({ e, text, t0, t1 }) => {
      const n = Math.floor(clamp((t - t0) / (t1 - t0)) * text.length + 1e-6);
      e.textContent = text.slice(0, n) + (n < text.length && t >= t0 - 0.3 ? '▍' : '');
    });
  };
})();
