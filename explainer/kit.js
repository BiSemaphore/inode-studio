// Explainer kit: turns a list of timed ops into Web Animations on a whiteboard.
//
// The page defines window.STORY = { total, ops, cams, sentences, overlays }
// (written by explainer/build.py) and loads this file. Every op has `at`
// (seconds) and a `kind`. The board is a large world (#world) moved by a
// camera; subtitles, watermark and end card sit on the stage. All motion is
// Web Animations, so tools/record.js can seek any frame.
//
// House rules (explainer/README.md): lines draw themselves with no visible pen;
// nothing ever speeds up to catch the voice; rings are smooth; arrows always
// end in a head; dashed lines stay dashed; handwriting is written in one go.
(function () {
  const W = window.MOTION.width || 1920, H = window.MOTION.height || 1080;
  const NS = 'http://www.w3.org/2000/svg';
  // Colours are theme roles ("ink", "red", "accent", ...) resolved from the
  // CSS variables build.py writes from the theme; hex values pass through.
  const css = getComputedStyle(document.documentElement);
  const col = (v) => (v && !/^(#|rgb|hsl|transparent)/.test(v) ? css.getPropertyValue('--' + v).trim() || v : v);
  const INK = col('ink');
  const S = window.STORY;
  const ms = (s) => s * 1000;
  const world = document.getElementById('world');
  const svg = document.getElementById('board');
  const under = document.getElementById('under');
  const over = document.getElementById('over');
  const ink = document.getElementById('ink');
  const defs = document.getElementById('defs');
  const rc = rough.svg(svg);
  let uid = 0;
  // Motion language, shared by every component: one entrance per kind of thing,
  // short arcs (250-500 ms), nothing decorative. A theme may override via MOTION.motion.
  const T = Object.assign({ enter: 0.35, node: 0.4, packet: 0.8, pulse: 0.7, shake: 0.45, tone: 0.3, line: 0.12, note: 0.3 },
    window.MOTION.motion || {});
  const EASE_IN = 'cubic-bezier(.2,.9,.3,1)';

  function anim(el, frames, at, dur, easing = 'ease-in-out', fill = 'both') {
    return el.animate(frames, { delay: ms(at), duration: ms(Math.max(dur, 0.001)), fill, easing });
  }

  function setAttrs(el, attrs) {
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    return el;
  }

  // ---------- strokes ----------

  // Points along a path every `step` px, split where the path jumps.
  function runsOf(p, step = 4) {
    const L = p.getTotalLength();
    const runs = [];
    let run = [], prev = null;
    for (let l = 0; l <= L + 0.001; l += step) {
      const q = p.getPointAtLength(Math.min(l, L));
      if (prev && Math.hypot(q.x - prev.x, q.y - prev.y) > step * 3) { if (run.length > 1) runs.push(run); run = []; }
      run.push([q.x, q.y, Math.min(l, L)]);
      prev = q;
    }
    if (run.length > 1) runs.push(run);
    return runs;
  }

  // Relative time per point: a little slower into corners and at both ends,
  // as a steady hand would draw. Never sped up to catch anything.
  function pace(run) {
    const n = run.length, ts = [0];
    const len = run[n - 1][2] - run[0][2];
    let total = 0;
    for (let i = 1; i < n; i++) {
      const a = run[Math.max(0, i - 3)], b = run[i], c = run[Math.min(n - 1, i + 3)];
      let turn = Math.abs(Math.atan2(c[1] - b[1], c[0] - b[0]) - Math.atan2(b[1] - a[1], b[0] - a[0]));
      if (turn > Math.PI) turn = 2 * Math.PI - turn;
      const from = b[2] - run[0][2];
      const v = (0.55 + 0.45 * Math.min(1, from / 40, (len - from) / 40)) / (1 + 1.2 * turn);
      total += (b[2] - run[i - 1][2]) / Math.max(v, 0.1);
      ts.push(total);
    }
    return ts;
  }

  // Reveal a path along its own length by animating its dash offset.
  function reveal(p, kf, t0, span) {
    const L = Math.ceil(p.getTotalLength()) + 2;
    const frames = kf.map(([t, l]) => ({ strokeDashoffset: L - l, offset: (t - t0) / span }));
    frames[0].offset = 0;
    frames[frames.length - 1].offset = 1;
    frames.forEach((f, i) => { if (i && f.offset < frames[i - 1].offset) f.offset = frames[i - 1].offset; });
    p.style.strokeDasharray = `${L} ${L}`;
    anim(p, frames, t0, span, 'linear');
  }

  // A dashed path becomes its dashes, each a short solid path, so it can be
  // drawn with the same reveal and keeps its gaps. (No SVG masks anywhere:
  // large masks made Chrome drop parts of zoomed frames.)
  function explodeDashes(p) {
    const da = p.getAttribute('stroke-dasharray');
    if (!da) return [p];
    const [on, off] = da.split(/[ ,]+/).map(Number);
    const L = p.getTotalLength(), out = [];
    for (let l = 0; l < L; l += on + off) {
      const pts = [];
      for (let x = l; x <= Math.min(L, l + on); x += 3) { const q = p.getPointAtLength(x); pts.push(`${q.x.toFixed(1)} ${q.y.toFixed(1)}`); }
      if (pts.length < 2) continue;
      const c = p.cloneNode();
      c.removeAttribute('stroke-dasharray');
      c.setAttribute('d', 'M ' + pts.join(' L '));
      p.before(c);
      out.push(c);
    }
    p.remove();
    return out;
  }

  // Draw the paths' strokes one after another over `dur`; returns the end time.
  function drawPaths(paths, at, dur) {
    const items = paths.flatMap(explodeDashes).map((p) => ({ p, runs: runsOf(p) }));
    items.forEach((it) => (it.paces = it.runs.map(pace)));
    const nRuns = items.reduce((a, it) => a + it.runs.length, 0);
    const raw = items.reduce((a, it) => a + it.paces.reduce((b, ps) => b + ps[ps.length - 1], 0), 0) || 1;
    const gap = Math.min(0.08, (dur * 0.2) / Math.max(1, nRuns - 1));
    const k = (dur - (nRuns - 1) * gap) / raw;
    let t = at;
    for (const it of items) {
      const kf = [];
      it.runs.forEach((run, r) => {
        const ps = it.paces[r];
        run.forEach((q, i) => kf.push([t + ps[i] * k, q[2]]));
        t = kf[kf.length - 1][0] + gap;
      });
      if (kf.length) reveal(it.p, kf, kf[0][0], Math.max(1e-3, kf[kf.length - 1][0] - kf[0][0]));
    }
    return t - gap;
  }

  // One element per subpath: Chrome restarts a dash pattern at every subpath,
  // so revealing a multi-part path would start all its parts at once.
  function splitSubpaths(p) {
    const parts = p.getAttribute('d').split(/(?=M)/).filter((x) => x.trim());
    if (parts.length < 2) return [p];
    const out = parts.map((d) => { const c = p.cloneNode(); c.setAttribute('d', d); p.before(c); return c; });
    p.remove();
    return out;
  }

  // Outline first, then any hachure shading; solid fills fade in.
  function trace(g, at, dur, o = {}) {
    const paths = [...g.querySelectorAll('path')].flatMap(splitSubpaths);
    const stroked = paths.filter((p) => p.getAttribute('stroke') && p.getAttribute('stroke') !== 'none');
    const solid = paths.filter((p) => !stroked.includes(p));
    const hatch = o.fill && o.fillStyle === 'hachure' ? stroked.filter((p) => p.getAttribute('stroke') === o.fill) : [];
    const outline = stroked.filter((p) => !hatch.includes(p));
    const end = drawPaths(outline, at, hatch.length ? dur * 0.6 : dur);
    if (hatch.length) drawPaths(hatch, end + 0.05, dur * 0.5);
    solid.forEach((p) => anim(p, [{ opacity: 0 }, { opacity: 1 }], end - 0.05, 0.4));
    return end;
  }

  function roughOpts(o, i) {
    return {
      seed: o.seed || 11 + i, roughness: o.roughness ?? 1.0, bowing: o.bowing ?? 1.0,
      stroke: o.color || INK, strokeWidth: o.width || 2.8,
      fill: o.fill, fillStyle: o.fillStyle || 'solid', hachureGap: o.hachureGap || 14,
      fillWeight: o.fillWeight || 1.4, hachureAngle: o.hachureAngle ?? -41,
      strokeLineDash: o.dashed ? [16, 12] : undefined,
      disableMultiStroke: true, disableMultiStrokeFill: true,
    };
  }

  // A smooth hand-drawn loop: an ellipse that overshoots its start a little,
  // its radius growing slightly so the two ends do not sit on top of each other.
  function smoothLoop(cx, cy, rx, ry, turns = 1.08, start = -2.3) {
    const n = 64, pts = [];
    for (let k = 0; k <= n; k++) {
      const a = start + (k / n) * Math.PI * 2 * turns;
      const f = 1 + 0.06 * (k / n);
      pts.push([cx + Math.cos(a) * rx * f, cy + Math.sin(a) * ry * f]);
    }
    // Catmull-Rom through the points, as cubic Beziers.
    let d = `M ${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)}, ${c2[0].toFixed(1)} ${c2[1].toFixed(1)}, ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
    }
    return d;
  }

  function loopPath(d, o) {
    const p = setAttrs(document.createElementNS(NS, 'path'), {
      d, fill: 'none', stroke: o.color || col('accent'), 'stroke-width': o.width || 4,
      'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    });
    if (o.dashed) p.setAttribute('stroke-dasharray', '16 12');
    ({ over, under }[o.layer] || ink).appendChild(p);
    drawPaths([p], o.at, o.dur || 0.8);
  }

  // ---------- text ----------

  const MONO = css.getPropertyValue('--font-mono').trim().replace(/"/g, '') || 'Ubuntu Mono';
  const HAND = css.getPropertyValue('--font-hand').trim().replace(/"/g, '') || 'Virgil';
  const TITLE = css.getPropertyValue('--font-title').trim().replace(/"/g, '') || 'Overused Grotesk';

  function textEl(o) {
    const t = setAttrs(document.createElementNS(NS, 'text'), {
      x: o.x, y: o.y, 'font-family': o.font === 'mono' ? MONO : HAND, 'font-size': o.size || 40, fill: o.color || INK,
    });
    if (o.anchor) t.setAttribute('text-anchor', o.anchor);
    t.textContent = o.text;
    ({ under, ink }[o.layer] || over).appendChild(t);
    return t;
  }

  // Handwriting appears left to right in one steady pass.
  function write(o) {
    const t = textEl(o);
    if (o.times) return typeText(t, o.times);
    const dur = o.dur ?? Math.min(2.2, Math.max(0.5, o.text.length * 0.055));
    anim(t, [{ clipPath: 'inset(-40% 100% -40% 0%)' }, { clipPath: 'inset(-40% -2% -40% -2%)' }], o.at, dur, 'cubic-bezier(.3,.1,.4,1)');
  }

  // Characters appear at the given times; nothing shows before the first one.
  function typeFrames(n, times, t0) {
    const span = times[n - 1] - t0 + 0.001;
    const kf = [{ clipPath: 'inset(-30% 100% -30% -2%)', offset: 0, easing: 'step-end' }];
    // 4 ms early, so the frame sampled at exactly tm already shows the character.
    times.forEach((tm, k) => kf.push({ clipPath: `inset(-30% ${(100 * (n - k - 1)) / n}% -30% -2%)`, offset: Math.max(0, tm - 0.004 - t0) / span, easing: 'step-end' }));
    return { kf, span };
  }

  function typeText(t, times) {
    const t0 = times[0] - 0.05;
    const { kf, span } = typeFrames(times.length, times, t0);
    anim(t, kf, t0, span, 'linear');
  }

  // ---------- other marks ----------

  function marker(o) {
    const y = o.y + o.h / 2;
    const p = setAttrs(document.createElementNS(NS, 'path'), {
      d: `M ${o.x} ${y + 2} C ${o.x + o.w * 0.3} ${y - 1}, ${o.x + o.w * 0.7} ${y + 3}, ${o.x + o.w} ${y}`,
      stroke: o.color || col('highlight'), 'stroke-width': o.h, 'stroke-linecap': 'round', fill: 'none', opacity: 0.55,
    });
    under.appendChild(p);
    drawPaths([p], o.at, o.dur || 0.5);
  }

  function ring(o) {
    loopPath(smoothLoop(o.x + o.w / 2, o.y + o.h / 2, o.w / 2 + (o.pad ?? 22), o.h / 2 + (o.pad ?? 20)), o);
  }

  function ellipse(o) {
    loopPath(smoothLoop(o.x, o.y, o.w / 2, o.h / 2, o.turns ?? 1.0, -1.6), { ...o, width: o.width || 3 });
  }

  // HTML block in the world (terminal cards). Typed lines carry per-character times.
  function block(o) {
    const el = document.createElement('div');
    el.className = o.cls || '';
    Object.assign(el.style, { left: o.x + 'px', top: o.y + 'px', width: o.w + 'px' });
    if (o.h) el.style.height = o.h + 'px';
    el.innerHTML = o.html || '';
    world.appendChild(el);
    anim(el, [{ opacity: 0, transform: 'translateY(16px) scale(.98)' }, { opacity: 1, transform: 'none' }], o.at, 0.4, 'ease-out');
    for (const ln of o.lines || []) {
      const d = document.createElement('div');
      d.className = 'ln ' + (ln.cls || '');
      d.innerHTML = ln.html;
      el.querySelector('.body').appendChild(d);
      if (ln.times) {
        // One span per character, each shown on the frame of its key press
        // (4 ms early so that frame already has it). Works for wrapped lines.
        d.textContent = '';
        [...ln.text].forEach((ch, k) => {
          const c = document.createElement('span');
          c.textContent = ch;
          d.appendChild(c);
          anim(c, [{ visibility: 'hidden' }, { visibility: 'visible' }], Math.max(0, ln.times[k] - 0.004), 0.001, 'step-end');
        });
        d.style.visibility = 'visible';   // the characters control their own visibility
      } else {
        anim(d, [{ visibility: 'hidden' }, { visibility: 'visible' }], ln.at, 0.001, 'step-end');
      }
      for (const m of ln.marks || []) {
        anim(d, [{ textDecorationColor: 'transparent' }, { textDecorationColor: col(m.color) }], m.at, 0.25, 'ease-out');
      }
    }
  }

  // A labelled dot that pops in, optionally flying along a curve first.
  function dot(o) {
    const wrap = document.createElement('div');
    wrap.className = 'dotw';
    const inner = document.createElement('div');
    inner.className = 'dot';
    inner.style.background = o.color || INK;
    if (o.size) Object.assign(inner.style, { width: o.size + 'px', height: o.size + 'px', margin: `${-o.size / 2}px 0 0 ${-o.size / 2}px` });
    inner.innerHTML = o.glyph ? `<span>${o.glyph}</span>` : '';
    wrap.appendChild(inner);
    if (o.label) {
      const l = document.createElement('div');
      l.className = 'dlabel' + (o.labelLeft ? ' left' : '');
      l.textContent = o.label;
      inner.after(l);
    }
    world.appendChild(wrap);
    const fly = o.from ? o.fly || 1.1 : 0;
    if (o.from) {
      const [fx, fy] = o.from, [x, y] = [o.x, o.y];
      const cx = (fx + x) / 2 + (o.bend ?? 0), cy = Math.min(fy, y) - (o.lift ?? 220);
      wrap.style.offsetPath = `path("M ${fx} ${fy} Q ${cx} ${cy} ${x} ${y}")`;
      wrap.style.offsetRotate = '0deg';
      anim(wrap, [{ offsetDistance: '0%' }, { offsetDistance: '100%' }], o.at, fly, 'cubic-bezier(.45,0,.2,1)');
    } else {
      wrap.style.left = o.x + 'px';
      wrap.style.top = o.y + 'px';
    }
    anim(inner, [{ transform: 'scale(0)' }, { transform: 'scale(1.25)', offset: 0.6 }, { transform: 'scale(1)' }], o.at, 0.35, 'ease-out');
    const lab = wrap.querySelector('.dlabel');
    if (lab) anim(lab, [{ opacity: 0 }, { opacity: 1 }], o.at + fly + 0.15, 0.3);
  }

  // Bars standing for the numbers of a vector, growing one after another.
  function bars(o) {
    for (let k = 0; k < o.n; k++) {
      const h = o.heights[k];
      const r = setAttrs(document.createElementNS(NS, 'rect'), { x: o.x + k * (o.bw + o.gap), y: o.y - h, width: o.bw, height: h, rx: 2, fill: o.color || col('bars') });
      r.style.transformBox = 'fill-box';
      r.style.transformOrigin = '50% 100%';
      over.appendChild(r);
      anim(r, [{ transform: 'scaleY(0)' }, { transform: 'scaleY(1)' }], o.at + k * (o.step || 0.035), 0.25, 'cubic-bezier(.3,1.4,.5,1)');
    }
  }

  // Arrow: shaft, then a head aligned with the shaft's last direction. `gap`
  // stops the shaft short of the target so a dot there never covers the head.
  function arrow(o, i) {
    const [x1, y1] = o.from;
    let [x2, y2] = o.to;
    const a0 = Math.atan2(y2 - y1, x2 - x1);
    const len = Math.hypot(x2 - x1, y2 - y1);
    const mid = [(x1 + x2) / 2 + (o.bend || 0) * Math.sin(a0), (y1 + y2) / 2 - (o.bend || 0) * Math.cos(a0)];
    if (o.gap) {
      const ae = Math.atan2(y2 - mid[1], x2 - mid[0]);
      x2 -= o.gap * Math.cos(ae); y2 -= o.gap * Math.sin(ae);
    }
    const shaft = o.bend
      ? `M ${x1} ${y1} Q ${mid[0]} ${mid[1]} ${x2} ${y2}`
      : `M ${x1} ${y1} L ${x2} ${y2}`;
    const g = rc.path(shaft, roughOpts({ ...o, roughness: o.bend ? 0.5 : (o.roughness ?? 0.8) }, i));
    const ae = o.bend ? Math.atan2(y2 - mid[1], x2 - mid[0]) : a0;
    const k = o.head || Math.min(24, len * 0.3);
    const h1 = [x2 - k * Math.cos(ae - 0.5), y2 - k * Math.sin(ae - 0.5)];
    const h2 = [x2 - k * Math.cos(ae + 0.5), y2 - k * Math.sin(ae + 0.5)];
    const hd = rc.linearPath([h1, [x2, y2], h2], roughOpts({ ...o, dashed: false, roughness: 0.4 }, i + 1));
    ({ ink }[o.layer] || over).append(g, hd);
    const dur = o.dur || 0.6;
    const end = trace(g, o.at, dur * 0.78, o);
    trace(hd, end + 0.02, dur * 0.22, o);
  }

  // A rubber stamp: a bordered word that slams onto the frame, tilted.
  function stamp(o) {
    const el = document.createElement('div');
    el.className = 'stamp';
    el.textContent = o.text;
    Object.assign(el.style, { left: o.x + 'px', top: o.y + 'px', color: o.color || col('red'), borderColor: o.color || col('red'),
      fontSize: (o.size || 64) + 'px' });
    world.appendChild(el);
    const r = o.rotate ?? -8;
    anim(el, [{ opacity: 0, transform: `translate(-50%, -50%) rotate(${r}deg) scale(2.4)` },
      { opacity: 1, transform: `translate(-50%, -50%) rotate(${r}deg) scale(0.92)`, offset: 0.7 },
      { opacity: 1, transform: `translate(-50%, -50%) rotate(${r}deg) scale(1)` }], o.at, 0.28, 'cubic-bezier(.2,.8,.3,1)');
  }

  // ---------- clean motion-design pieces (theme "clean") ----------

  // A UI card: label, title, body. `states` swap its look and text later
  // ({at, tone, title, body}), as a cross-fading copy on top. `typeBody`
  // types the body character by character at `times`.
  function card(o) {
    const make = (st, z) => {
      const el = document.createElement('div');
      el.className = `card tone-${st.tone || 'neutral'}`;
      Object.assign(el.style, { left: o.x + 'px', top: o.y + 'px', width: o.w + 'px', zIndex: z });
      if (o.h) el.style.minHeight = o.h + 'px';
      el.innerHTML = (st.label ? `<div class="label">${st.label}</div>` : '') + (st.title ? `<div class="title">${st.title}</div>` : '') +
        (st.body !== undefined ? `<div class="body">${st.body}</div>` : '');
      world.appendChild(el);
      return el;
    };
    const base = make(o, 3);
    anim(base, [{ opacity: 0, transform: 'translateY(28px) scale(.96)' }, { opacity: 1, transform: 'none' }], o.at, 0.4, 'cubic-bezier(.2,.9,.3,1)');
    if (o.times) {
      const body = base.querySelector('.body');
      const text = body.textContent;
      body.textContent = '';
      [...text].forEach((ch, k) => {
        const c = document.createElement('span');
        c.textContent = ch;
        body.appendChild(c);
        anim(c, [{ visibility: 'hidden' }, { visibility: 'visible' }], Math.max(0, o.times[k] - 0.004), 0.001, 'step-end');
      });
    }
    (o.states || []).forEach((st, k) => {
      const el = make({ label: o.label, title: o.title, body: o.body, ...st }, 4 + k);
      anim(el, [{ opacity: 0, transform: 'scale(1.03)' }, { opacity: 1, transform: 'none' }], st.at, 0.25, 'ease-out');
    });
  }

  // A clean connector with an arrowhead, drawn from `from` to `to`.
  function flow(o) {
    const [x1, y1] = o.from, [x2, y2] = o.to;
    const a = Math.atan2(y2 - y1, x2 - x1), k = 18;
    const color = o.color || INK;
    const line = setAttrs(document.createElementNS(NS, 'path'), { d: `M ${x1} ${y1} L ${x2 - 6 * Math.cos(a)} ${y2 - 6 * Math.sin(a)}`,
      stroke: color, 'stroke-width': o.width || 5, 'stroke-linecap': 'round', fill: 'none' });
    const head = setAttrs(document.createElementNS(NS, 'path'), {
      d: `M ${x2 - k * Math.cos(a - 0.45)} ${y2 - k * Math.sin(a - 0.45)} L ${x2} ${y2} L ${x2 - k * Math.cos(a + 0.45)} ${y2 - k * Math.sin(a + 0.45)}`,
      stroke: color, 'stroke-width': o.width || 5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', fill: 'none' });
    ink.append(line, head);
    const L = Math.ceil(line.getTotalLength()) + 2, dur = o.dur || 0.35;
    line.style.strokeDasharray = `${L} ${L}`;
    anim(line, [{ strokeDashoffset: L }, { strokeDashoffset: 0 }], o.at, dur, 'cubic-bezier(.4,0,.2,1)');
    anim(head, [{ opacity: 0 }, { opacity: 1 }], o.at + dur * 0.85, 0.08, 'linear');
  }

  // ---------- components: architecture nodes, travelling packets, code ----------

  // A system node (client, API, DNS, database...): scales in, then reacts on cue.
  // events: [{at, kind: 'pulse' | 'fail' | 'ok'}]. fail shakes once and stays red,
  // ok turns green, pulse rings once (the node is doing work).
  function node(o) {
    const el = document.createElement('div');
    el.className = 'node' + (o.tone ? ' tone-' + o.tone : '');
    Object.assign(el.style, { left: o.x + 'px', top: o.y + 'px', width: o.w + 'px', height: o.h + 'px' });
    el.innerHTML = (o.icon ? `<div class="icon">${o.icon}</div>` : '') + `<div class="t">${o.title || ''}</div>` +
      (o.sub ? `<div class="s">${o.sub}</div>` : '');
    world.appendChild(el);
    anim(el, [{ opacity: 0, transform: 'scale(.9)' }, { opacity: 1, transform: 'none' }], o.at, T.node, EASE_IN);
    for (const ev of o.events || []) {
      if (ev.kind === 'pulse') {
        anim(el, [{ boxShadow: `0 0 0 0 ${col(ev.color || 'accent')}` }, { boxShadow: '0 0 0 22px transparent' }], ev.at, T.pulse, 'ease-out', 'none');
      } else if (ev.kind === 'fail') {
        anim(el, [{ transform: 'none' }, { transform: 'translateX(-14px)' }, { transform: 'translateX(12px)' }, { transform: 'translateX(-8px)' },
          { transform: 'translateX(4px)' }, { transform: 'none' }], ev.at, T.shake, 'ease-in-out', 'none');
        anim(el, [{}, { borderColor: col('red'), background: 'var(--bad-bg, #fdecec)' }], ev.at, T.tone, 'ease-out', 'forwards');
      } else if (ev.kind === 'ok') {
        anim(el, [{}, { borderColor: col('green'), background: 'var(--good-bg, #e9f9ef)' }], ev.at, T.tone, 'ease-out', 'forwards');
        anim(el, [{ transform: 'none' }, { transform: 'scale(1.04)' }, { transform: 'none' }], ev.at, T.tone + 0.1, 'ease-out', 'none');
      }
    }
  }

  // A message travelling from `from` to `to` (optionally curved by `bend`): a dot,
  // or a pill when it has a `label`. It fades in, travels, and fades out on arrival
  // unless `stay` keeps it at the destination.
  function packet(o) {
    const wrap = document.createElement('div');
    wrap.className = 'packetw';
    const p = document.createElement('div');
    p.className = 'packet' + (o.label ? '' : ' dotonly');
    p.style.background = o.color || col('accent');
    if (o.label) p.textContent = o.label;
    wrap.appendChild(p);
    world.appendChild(wrap);
    const [fx, fy] = o.from, [x, y] = o.to;
    const bend = o.bend || 0, a = Math.atan2(y - fy, x - fx);
    const cx = (fx + x) / 2 + bend * Math.sin(a), cy = (fy + y) / 2 - bend * Math.cos(a);
    wrap.style.offsetPath = `path("M ${fx} ${fy} Q ${cx} ${cy} ${x} ${y}")`;
    wrap.style.offsetRotate = '0deg';
    const dur = o.dur || T.packet;
    const kf = o.stay
      ? [{ offsetDistance: '0%', opacity: 0 }, { opacity: 1, offset: 0.12 }, { offsetDistance: '100%', opacity: 1 }]
      : [{ offsetDistance: '0%', opacity: 0 }, { opacity: 1, offset: 0.12 }, { opacity: 1, offset: 0.86 }, { offsetDistance: '100%', opacity: 0 }];
    // fill both: hidden before it departs, and (unless it stays) hidden after it arrives.
    anim(wrap, kf, o.at, dur, 'cubic-bezier(.45,0,.25,1)', 'both');
  }

  // Code card: a file tab, line numbers, simple syntax colours. Lines appear one
  // after another (or at `lineAt`), `marks` tint ranges (add / del / focus),
  // `spotlight` dims every other line, `notes` add a short line under a line.
  const KW = /^(func|return|if|else|for|range|const|let|var|def|class|import|from|package|type|struct|nil|true|false|None|True|False|async|await|try|catch|except|raise|throw|new|err|go|defer|while|in|not|and|or)$/;
  function highlight(src, lang) {
    const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const hash = /^(py|python|sh|bash|yaml|toml|rb)$/.test(lang || '');
    const re = hash ? /(#.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/g
      : /(\/\/.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`[^`]*`)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/g;
    let out = '', last = 0, m;
    while ((m = re.exec(src))) {
      out += esc(src.slice(last, m.index));
      const t = esc(m[0]);
      out += m[1] ? `<span class="tk-com">${t}</span>` : m[2] ? `<span class="tk-str">${t}</span>` : m[3] ? `<span class="tk-num">${t}</span>`
        : KW.test(m[4]) ? `<span class="tk-kw">${t}</span>` : t;
      last = re.lastIndex;
    }
    return out + esc(src.slice(last));
  }
  function code(o) {
    const el = document.createElement('div');
    el.className = 'code';
    Object.assign(el.style, { left: o.x + 'px', top: o.y + 'px', width: o.w + 'px' });
    el.innerHTML = `<div class="tab"><i></i><i></i><i></i><span class="file">${o.file || ''}</span>` +
      (o.lang ? `<span class="lang">${o.lang}</span>` : '') + '</div><div class="cbody"></div>';
    world.appendChild(el);
    anim(el, [{ opacity: 0, transform: 'translateY(24px)' }, { opacity: 1, transform: 'none' }], o.at, T.enter, EASE_IN);
    const body = el.querySelector('.cbody'), first = o.start || 1, rows = [];
    o.src.forEach((src, k) => {
      const ln = document.createElement('div');
      ln.className = 'cl';
      ln.innerHTML = `<span class="gut">${first + k}</span><span class="src">${highlight(src, o.lang) || ' '}</span>`;
      body.appendChild(ln);
      rows.push(ln);
      const t = (o.lineAt && o.lineAt[k] !== undefined) ? o.lineAt[k] : o.at + T.enter + k * T.line;
      anim(ln, [{ opacity: 0, transform: 'translateX(-10px)' }, { opacity: 1, transform: 'none' }], t, 0.18, 'ease-out');
      for (const n of (o.notes || []).filter((n) => n.line === first + k)) {
        const d = document.createElement('div');
        d.className = 'cnote' + (n.tone ? ' ' + n.tone : '');
        d.textContent = '↳ ' + n.text;
        body.appendChild(d);
        anim(d, [{ opacity: 0, transform: 'translateY(-6px)' }, { opacity: 1, transform: 'none' }], n.at, T.note, 'ease-out');
      }
    });
    const TINT = { add: 'rgba(46,160,67,.30)', del: 'rgba(248,81,73,.30)', focus: 'rgba(255,203,107,.20)' };
    for (const m of o.marks || []) {
      rows.slice(m.from - first, m.to - first + 1).forEach((r) =>
        anim(r, [{ background: 'transparent' }, { background: TINT[m.tone || 'focus'] }], m.at, T.tone, 'ease-out', 'forwards'));
    }
    if (o.spotlight) {
      const { at, from, to } = o.spotlight;
      rows.forEach((r, k) => {
        if (k + first < from || k + first > to) anim(r.querySelector('.src'), [{ opacity: 1 }, { opacity: 0.3 }], at, T.tone, 'ease-out', 'forwards');
      });
    }
  }

  // A padlock whose shackle snaps shut at `at`.
  function lock(o) {
    const s = o.size || 120, color = o.color || col('green');
    const g = document.createElementNS(NS, 'g');
    g.innerHTML = `<rect x="${-s * 0.42}" y="${-s * 0.05}" width="${s * 0.84}" height="${s * 0.62}" rx="${s * 0.1}" fill="${color}"/>
      <circle cx="0" cy="${s * 0.22}" r="${s * 0.07}" fill="#fff"/>`;
    const sh = setAttrs(document.createElementNS(NS, 'path'), { d: `M ${-s * 0.26} ${-s * 0.02} V ${-s * 0.24} A ${s * 0.26} ${s * 0.26} 0 0 1 ${s * 0.26} ${-s * 0.24} V ${-s * 0.02}`,
      stroke: color, 'stroke-width': s * 0.11, fill: 'none', 'stroke-linecap': 'round' });
    g.appendChild(sh);
    g.setAttribute('transform', `translate(${o.x} ${o.y})`);
    ink.appendChild(g);
    anim(g, [{ opacity: 0 }, { opacity: 1 }], o.at, 0.2, 'linear');
    anim(sh, [{ transform: `translateY(${-s * 0.22}px)` }, { transform: 'translateY(0)' }], o.at + 0.25, 0.18, 'cubic-bezier(.5,0,.9,.6)');
  }

  const kinds = {
    rect: (o, i) => { const g = rc.rectangle(o.x, o.y, o.w, o.h, roughOpts(o, i)); (o.layer === 'under' ? under : over).appendChild(g); trace(g, o.at, o.dur || 0.9, o); },
    line: (o, i) => { const g = rc.linearPath(o.pts, roughOpts(o, i)); (o.layer === 'ink' ? ink : over).appendChild(g); trace(g, o.at, o.dur || 0.5, o); },
    cylinder: (o, i) => {
      const { x, y, w, h } = o, ry = h * 0.12, dur = o.dur || 1.2;
      const top = rc.ellipse(x + w / 2, y, w, ry * 2, roughOpts({ ...o, fill: undefined }, i + 1));
      const body = rc.path(`M ${x} ${y} L ${x} ${y + h} A ${w / 2} ${ry} 0 0 0 ${x + w} ${y + h} L ${x + w} ${y}`, roughOpts(o, i));
      over.append(body, top);
      const end = trace(top, o.at, dur * 0.35, o);
      trace(body, end, dur * 0.65, o);
    },
    polygon: (o, i) => { const g = rc.polygon(o.pts, roughOpts(o, i)); ink.appendChild(g); trace(g, o.at, o.dur || 0.8, o); },
    write, marker, ring, ellipse, block, dot, bars, arrow, stamp, card, flow, lock, node, packet, code,
    cross: (o, i) => {
      const { x, y } = o, r = o.r || 40;
      const c = { ...o, color: o.color || col('red'), width: 6, roughness: 0.6, layer: 'ink' };
      kinds.line({ ...c, pts: [[x - r, y - r], [x + r, y + r]], dur: 0.25 }, i);
      kinds.line({ ...c, pts: [[x + r, y - r], [x - r, y + r]], at: o.at + 0.3, dur: 0.25 }, i + 1);
    },
    check: (o, i) => {
      const { x, y } = o, r = o.r || 26;
      kinds.line({ ...o, layer: 'ink', color: o.color || col('green'), width: 6, roughness: 0.5, pts: [[x - r, y], [x - r * 0.25, y + r * 0.8], [x + r * 1.2, y - r]], dur: 0.4 }, i);
    },
  };

  // ---------- camera, subtitles, overlays ----------

  function camera(cams) {
    const tf = (c) => {
      const z = Math.min(W / c.w, H / c.h);
      return `translate(${W / 2 - (c.x + c.w / 2) * z}px, ${H / 2 - (c.y + c.h / 2) * z - (c.lift || 0)}px) scale(${z})`;
    };
    const kf = [{ transform: tf(cams[0]), offset: 0 }];
    for (const c of cams.slice(1)) {
      kf.push({ transform: kf[kf.length - 1].transform, offset: c.at / S.total });
      kf.push({ transform: tf(c), offset: Math.min(1, (c.at + (c.dur || 1.2)) / S.total) });
    }
    kf.push({ transform: kf[kf.length - 1].transform, offset: 1 });
    kf.forEach((k) => (k.easing = 'cubic-bezier(.65,0,.35,1)'));
    world.animate(kf, { duration: ms(S.total), fill: 'both' });
  }

  // Subtitles build up as they are spoken: one line at a time, each word
  // appearing when it is said; the line clears when the next one starts.
  // Plain text on a dark band that grows with the words. No highlighting.
  function subtitles(lines) {
    const box = document.getElementById('subtitles');
    lines.forEach((words, k) => {
      const el = document.createElement('div');
      el.className = 'sub';
      const next = lines[k + 1];
      const t0 = words[0][1] - 0.04;
      const t1 = Math.min(words[words.length - 1][2] + 0.7, next ? next[0][1] - 0.04 : 1e9);
      words.forEach(([w, ws], i) => {
        const span = document.createElement('span');
        span.className = 'w' + (i === 0 ? ' first' : '') + (i === words.length - 1 ? ' last' : '');
        span.innerHTML = i < words.length - 1 ? w + ' ' : w;
        el.appendChild(span);
        // Visible from when the word is spoken until the line clears.
        const span0 = Math.max(0.001, t1 - t0), on = Math.max(0, ws - 0.03 - t0) / span0;
        anim(span, [{ visibility: 'hidden', offset: 0 }, { visibility: 'hidden', offset: on }, { visibility: 'visible', offset: Math.min(1, on + 0.0001) },
          { visibility: 'visible', offset: 1 }], t0, span0, 'linear', 'none');
      });
      box.appendChild(el);
    });
  }

  Promise.all([`40px "${HAND}"`, `40px "${MONO}"`, `600 40px "${TITLE}"`].map((f) => document.fonts.load(f))).then(() => {
    S.ops.forEach((o, i) => kinds[o.kind]({ ...o, color: col(o.color), fill: col(o.fill) }, i * 3));
    camera(S.cams);
    subtitles(S.lines);
    (S.overlays || []).forEach((o) => anim(document.getElementById(o.id),
      o.out ? [{ opacity: 1 }, { opacity: 0 }] : [{ opacity: 0 }, { opacity: 1 }], o.at, o.dur || 0.8, 'ease-out'));
    window.MOTION.ready = true;
  });
})();
