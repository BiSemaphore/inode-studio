// Kinetic type for any theme (owner 2026-10-29: more engaging). Load after runtime.js. Every effect is a pure function
// of t, like the rest of the frames kit, so renders stay deterministic.
//   data-count="518" data-count-at="w3:518" [data-count-dur="0.9"] [data-count-dec="1"]   number counts up from 0
//       (inside the element, the first #-run of digits is replaced; e.g. <span data-count="2.4" data-count-dec="1">2.4</span>)
//   data-k="pop"      scales in with a small overshoot at its data-at
//   data-k="letters"  builds a title letter by letter from its data-at (keeps <i> swaps)
//   data-grow="w3:complete," [data-grow-dur="0.6"]   a bar segment grows from the left
(function () {
  const T = window.T, clamp = (x) => Math.max(0, Math.min(1, x));
  const out = (x) => 1 - Math.pow(1 - x, 3);
  const back = (x) => { const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const counts = [...document.querySelectorAll('[data-count]')].map((e) => ({ e, to: +e.dataset.count, dec: +(e.dataset.countDec || 0),
    at: T(e.dataset.countAt || e.closest('[data-at]').dataset.at), dur: +(e.dataset.countDur || 0.9) }));
  const pops = [...document.querySelectorAll('[data-k="pop"]')].map((e) => ({ e, at: T(e.dataset.at) }));
  const grows = [...document.querySelectorAll('[data-grow]')].map((e) => ({ e, at: T(e.dataset.grow), dur: +(e.dataset.growDur || 0.6) }));
  const letters = [];
  document.querySelectorAll('[data-k="letters"]').forEach((e) => {
    const at = T(e.dataset.at), spans = [];
    const walk = (n) => [...n.childNodes].forEach((c) => {
      if (c.nodeType === 3) {
        const frag = document.createDocumentFragment();
        [...c.textContent].forEach((ch) => { const s = document.createElement('span'); s.textContent = ch; s.style.display = 'inline-block';
          if (ch === ' ') s.style.whiteSpace = 'pre'; frag.appendChild(s); spans.push(s); });
        n.replaceChild(frag, c);
      } else if (c.nodeType === 1) walk(c);
    });
    walk(e); letters.push({ spans, at });
  });
  (window.ON_FRAME = window.ON_FRAME || []).push((t) => {
    // numbers change only on whole output frames (1/30 s), so the two blended sub-frames of motion blur show the same
    // number (otherwise a count shows two numbers on top of each other)
    // 15 steps a second: render/encode.js blends (2k-1)/60 and 2k/60 into output frame k, and both land on the same
    // step; each number holds for 2 frames (calmer to read, and never a one-frame change)
    const tq = Math.ceil(t * 15 - 1e-6) / 15;
    counts.forEach(({ e, to, dec, at, dur }) => { const v = to * out(clamp((tq - at) / dur)); e.textContent = v.toFixed(dec); });
    pops.forEach(({ e, at }) => { const x = clamp((t - at) / 0.4); e.style.scale = String(x <= 0 ? 0.82 : 0.82 + 0.18 * back(x)); });
    grows.forEach(({ e, at, dur }) => { e.style.transformOrigin = '0 50%'; e.style.transform = `scaleX(${out(clamp((t - at) / dur))})`; });
    letters.forEach(({ spans, at }) => spans.forEach((s, i) => { const x = clamp((t - at - i * 0.035) / 0.28);
      s.style.opacity = out(x); s.style.transform = `translateY(${(1 - out(x)) * 0.35}em)`; }));
  });
})();
