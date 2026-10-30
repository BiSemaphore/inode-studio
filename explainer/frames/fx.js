// Cinematic text and image effects for fast-cut videos (owner 2026-10-29, refs 86-88). Load after runtime.js.
// Every effect is a pure function of t, so renders stay deterministic. Text states change only on whole output frames
// (render/encode.js blends (2k-1)/60 and 2k/60 into frame k), so motion blur never mixes two texts; motion (punch, push)
// is not snapped, so it blurs naturally.
//   data-show="spec" [data-hide="spec"]      hard cut in / out (no fade), the default for everything in a fast edit
//   data-fx="flicker"   [data-fx-dur=0.35]   strobes on and off before it settles (a fixed pattern, 30 fps)
//   data-fx="scramble"  [data-fx-dur=0.5]    random characters resolve into the text, left to right
//   data-fx="typeon"    [data-fx-dur=0.4]    characters appear one by one
//   data-fx="glitch"    [data-fx-dur=0.3]    jitter plus a red and cyan split for a few frames
//   data-fx="punch"     [data-fx-from=1.3]   scales in from data-fx-from to 1 (ease out, 0.22 s)
//   data-fx="push"      [data-fx-to=1.08]    slow camera push from 1 to data-fx-to across its time on screen
//   data-fx="flash"                          a full white frame that fades out in 0.15 s (give it data-show)
// Several effects: data-fx="flicker punch". All start at data-show unless data-fx-at is given.
(function () {
  const T = window.T, clamp = (x) => Math.max(0, Math.min(1, x));
  const snap = (t) => Math.ceil(t * 30 - 1e-6) / 30;
  const out3 = (x) => 1 - Math.pow(1 - x, 3);
  const hash = (n) => { let x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const GLYPHS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&*+=/<>';
  const FLICK = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1];   // per-frame on/off pattern
  const els = [...document.querySelectorAll('[data-show]')].map((e) => {
    const show = T(e.dataset.show), hide = e.dataset.hide ? T(e.dataset.hide) : 1e9;
    const fx = (e.dataset.fx || '').split(/\s+/).filter(Boolean);
    const at = e.dataset.fxAt ? T(e.dataset.fxAt) : show;
    const dur = +(e.dataset.fxDur || ({ flicker: .35, scramble: .5, typeon: .4, glitch: .3 }[fx[0]] || .3));
    return { e, show, hide, fx, at, dur, text: e.textContent, seed: Math.round(show * 1000) };
  });
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => {
    const ts = snap(t);
    els.forEach((o) => {
      const { e, show, hide, fx, at, dur, text, seed } = o;
      const on = ts >= show && ts < hide;
      e.style.visibility = on ? 'visible' : 'hidden';
      if (!on) return;
      const k = Math.floor((ts - at) * 30 + 1e-6);           // frames since the effect started
      let op = 1, tr = '', sh = 'none', str = text;
      if (fx.includes('flicker') && ts < at + dur) op = FLICK[Math.max(0, k) % FLICK.length];
      if (fx.includes('scramble') && ts < at + dur) {
        const done = Math.floor(text.length * clamp((ts - at) / dur));
        str = [...text].map((c, i) => (i < done || c === ' ' ? c : GLYPHS[Math.floor(hash(seed + i * 7 + k) * GLYPHS.length)])).join('');
      }
      if (fx.includes('typeon')) str = text.slice(0, Math.ceil(text.length * clamp((ts - at) / dur)));
      if (fx.includes('glitch') && ts < at + dur) {
        const j = (hash(seed + k) - .5) * 28, jy = (hash(seed + k + 99) - .5) * 10;
        tr += ` translate(${j.toFixed(1)}px, ${jy.toFixed(1)}px)`;
        sh = `${(6 + hash(seed + k + 3) * 10).toFixed(1)}px 0 rgba(255,40,60,.85), ${(-6 - hash(seed + k + 5) * 10).toFixed(1)}px 0 rgba(0,220,255,.75)`;
      }
      if (fx.includes('punch')) { const from = +(e.dataset.fxFrom || 1.3); tr += ` scale(${(from + (1 - from) * out3(clamp((t - at) / .22))).toFixed(4)})`; }
      if (fx.includes('push')) { const to = +(e.dataset.fxTo || 1.08), end = Math.min(hide, window.TOTAL); tr += ` scale(${(1 + (to - 1) * clamp((t - show) / Math.max(.5, end - show))).toFixed(4)})`; }
      if (fx.includes('flash')) op = 1 - clamp((t - show) / .15);
      if (str !== e.textContent && !e.children.length) e.textContent = str;
      e.style.opacity = op; e.style.transform = tr.trim(); e.style.textShadow = sh;
    });
  });
})();
