// Theme "red-grain": our cast (the field figures, reused exactly; memory our-cast) drawn in cream, defined once.
// Load after runtime.js. Use <use class="fig" href="#work" transform="translate(x y) scale(1.25)"/>.
(function () {
  const d = document.createElement('div');
  d.innerHTML = `<svg width="0" height="0" style="position:absolute"><defs>
  <g id="stand"><circle cx="0" cy="-98" r="9"/><path d="M -9 -86 L 9 -86 L 7 -46 L -7 -46 Z M -5 -46 L -6 0 l -6 0 M 5 -46 L 6 0 l 6 0"/></g>
  <g id="think"><use href="#stand"/><path d="M -9 -84 L -12 -54 M 9 -84 L 13 -68 L 4 -90"/></g>
  <g id="point"><use href="#stand"/><path d="M -9 -84 L -12 -54 M 9 -84 L 44 -80 M 40 -84 l 6 4 l -6 3"/></g>
  <g id="work"><circle cx="-2" cy="-64" r="9"/><path d="M -9 -52 L 8 -52 L 11 -28 L -6 -28 Z M -4 -28 L -16 -12 L -8 0 l -6 0 M 8 -28 L 18 -12 L 12 0 l 6 0 M 7 -48 L 22 -36 M 16 -30 L 46 -30 M 22 -30 L 30 -50 L 52 -50 L 46 -30"/></g>
  </defs></svg>`;
  document.body.prepend(d.firstChild);
})();
