// Live preview: open piece.html?preview in Chrome. Plays the page with its
// soundtrack (audio.wav) and adds a scrubber; nothing is rendered to disk.
// Keys: space play/pause, left/right one frame, shift+left/right one second.
(function () {
  if (!/[?&]preview\b/.test(location.search)) return;
  const wait = setInterval(() => {
    if (!window.MOTION || !window.MOTION.ready) return;
    clearInterval(wait);
    start();
  }, 50);

  function start() {
    const M = window.MOTION, S = window.STORY, fps = M.fps, total = M.duration;
    const anims = () => document.getAnimations();
    const audio = new Audio('audio.wav');
    let t = 0, playing = false;

    // Fit the 1920x1080 stage into the window, player bar underneath.
    const stage = document.getElementById('stage');
    document.body.style.cssText = 'margin:0;background:#111;overflow:hidden;font:14px "Ubuntu Mono",monospace;color:#eee';
    const fit = () => {
      const k = Math.min(innerWidth / 1920, (innerHeight - 70) / 1080);
      stage.style.transformOrigin = '0 0';
      stage.style.transform = `translate(${(innerWidth - 1920 * k) / 2}px, 0) scale(${k})`;
    };
    addEventListener('resize', fit); fit();

    const bar = document.createElement('div');
    bar.style.cssText = 'position:fixed;left:0;right:0;bottom:0;height:62px;background:#000;display:flex;align-items:center;gap:14px;padding:0 16px;z-index:99';
    bar.innerHTML = `<button id="pp" style="width:70px;height:34px;font:inherit">play</button>
      <span id="tm" style="width:150px"></span>
      <div style="position:relative;flex:1;height:34px"><input id="sc" type="range" min="0" max="${total}" step="${1 / fps}" value="0" style="width:100%;height:34px;margin:0">
      <div id="ticks" style="position:absolute;left:0;right:0;top:0;height:6px;pointer-events:none"></div></div>
      <span id="bt" style="width:420px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#aaa"></span>`;
    document.body.appendChild(bar);
    const pp = bar.querySelector('#pp'), sc = bar.querySelector('#sc'), tm = bar.querySelector('#tm'), bt = bar.querySelector('#bt');
    (S.cams || []).forEach((c) => {                       // a tick per camera move = per scene
      const d = document.createElement('div');
      d.style.cssText = `position:absolute;top:0;width:2px;height:8px;background:#4dabf7;left:${(100 * c.at) / total}%`;
      bar.querySelector('#ticks').appendChild(d);
    });
    const lines = S.lines || [];

    function seek(s) {
      t = Math.max(0, Math.min(total, s));
      for (const a of anims()) { a.pause(); a.currentTime = t * 1000; }
      sc.value = t;
      const f = Math.round(t * fps);
      tm.textContent = `${t.toFixed(2)}s  f${f}`;
      const ln = [...lines].reverse().find((l) => l[0][1] <= t);
      bt.textContent = ln ? ln.map((w) => w[0]).join(' ').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&') : '';
    }
    function loop() {
      if (!playing) return;
      seek(audio.currentTime);
      if (t >= total) { toggle(); return; }
      requestAnimationFrame(loop);
    }
    function toggle() {
      playing = !playing;
      pp.textContent = playing ? 'pause' : 'play';
      if (playing) { audio.currentTime = t; audio.play(); loop(); } else audio.pause();
    }
    pp.onclick = toggle;
    sc.oninput = () => { if (playing) toggle(); seek(parseFloat(sc.value)); };
    addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); toggle(); }
      if (e.code === 'ArrowRight' || e.code === 'ArrowLeft') {
        if (playing) toggle();
        seek(t + (e.code === 'ArrowRight' ? 1 : -1) * (e.shiftKey ? 1 : 1 / fps));
      }
    });
    seek(0);
    window.__preview = { seek, toggle };
  }
})();
