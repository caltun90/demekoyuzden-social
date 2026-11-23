// paint.js — hand-painted looking textures made in Canvas 2D (no image files).
// Every texture: a base colour, soft brush noise, and DARK painted seams (the "drawn" look of the style).
import * as THREE from 'three';

export function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

function canvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }
function tex(c, rep = [1, 1]) {
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); return t;
}
export const shade = (hex, k) => { const c = new THREE.Color(hex); c.multiplyScalar(k); return '#' + c.getHexString(); };
// The frame is shown without an sRGB encode (see post.js), so an UNLIT canvas colour comes out darker than it was painted.
// D('#rrggbb') returns the canvas colour that DISPLAYS as that hex. Use it for anything drawn on a MeshBasicMaterial.
export function D(hex, a = 1) {
  const n = parseInt(hex.slice(1), 16), f = v => Math.round(255 * Math.pow(v / 255, 1 / 2.2));
  return `rgba(${f(n >> 16)},${f(n >> 8 & 255)},${f(n & 255)},${a})`;
}

// brush noise: many soft translucent dabs of lighter/darker tones
function dabs(g, w, h, base, n, r, amt, seed) {
  const R = rng(seed);
  for (let i = 0; i < n; i++) {
    const k = 1 + (R() - .5) * amt;
    g.fillStyle = shade(base, k); g.globalAlpha = .25 + R() * .35;
    g.beginPath(); g.ellipse(R() * w, R() * h, r * (.4 + R()), r * (.2 + R() * .5), R() * 3.14, 0, 6.29); g.fill();
  }
  g.globalAlpha = 1;
}

// Stone blocks, painted the way the reference paints them (analiz/doku.md): flat blocks that differ a little in tone,
// THIN joints that are a dark tint of the stone (never black, lighter than the ink outline), a light lip under every
// joint and a dark one above it (the bevel), a few speckles and hairline cracks. Drawn at twice the asked size, so a
// joint is about 3 px wide on screen at working distance instead of a soft 10 px band.
export function stoneTex({ base = '#e8d9bf', seam, bw = 128, bh = 64, w = 512, h = 512, seed = 1, rep = [1, 1] } = {}) {
  const K = 2, W = w * K, H = h * K, BW = bw * K, BH = bh * K;
  const [c, g] = canvas(W, H); g.fillStyle = base; g.fillRect(0, 0, W, H);
  const R = rng(seed), joint = seam || shade(base, .42);
  for (let y = 0, row = 0; y < H; y += BH, row++) for (let x = (row % 2) * BW / 2 - BW; x < W; x += BW) {
    g.fillStyle = shade(base, .9 + R() * .2); g.fillRect(x, y, BW, BH);                         // each block its own tone
  }
  dabs(g, W, H, base, 700, 44, .1, seed);
  for (let y = 0, row = 0; y < H; y += BH, row++) {
    for (let x = (row % 2) * BW / 2 - BW; x < W; x += BW) {
      g.fillStyle = shade(base, 1.14); g.globalAlpha = .5; g.fillRect(x + 4, y + 4, BW - 6, 5); g.fillRect(x + 4, y + 4, 4, BH - 6);   // lit lips: top and left
      g.fillStyle = shade(base, .74); g.globalAlpha = .4; g.fillRect(x + 2, y + BH - 7, BW - 2, 5);                               // shaded lip: bottom
      g.globalAlpha = .5; g.fillStyle = shade(base, .7);
      for (let k = 0; k < 5; k++) { g.beginPath(); g.arc(x + R() * BW, y + R() * BH, 1.5 + R() * 2.5, 0, 6.29); g.fill(); }
      if (R() < .2) { g.strokeStyle = shade(base, .62); g.lineWidth = 2; g.globalAlpha = .6; let cx = x + BW * (.2 + R() * .6), cy = y + 6; g.beginPath(); g.moveTo(cx, cy);
        for (let k = 0; k < 4; k++) { cx += (R() - .5) * BW * .16; cy += BH * (.12 + R() * .1); g.lineTo(cx, cy); } g.stroke(); }
      g.globalAlpha = .9; g.fillStyle = joint; g.fillRect(x - 2, y, 4, BH);
    }
    g.globalAlpha = .9; g.fillStyle = joint; g.fillRect(0, y - 2, W, 4);
  }
  g.globalAlpha = 1; return tex(c, rep);
}

// Planks: flat boards, thin dark gaps (a dark tint of the wood), a lit lip on one side of each gap and a shaded one on
// the other, long soft grain strokes that never read as gaps, a butt joint with two nails on every board.
export function woodTex({ base = '#b07a45', seam, plank = 64, w = 512, h = 512, seed = 2, rep = [1, 1], vertical = false } = {}) {
  const K = 2, W = w * K, H = h * K, P = plank * K;
  const [c, g] = canvas(W, H); g.fillStyle = base; g.fillRect(0, 0, W, H);
  const R = rng(seed), gap = seam || shade(base, .36);
  for (let y = 0; y < H; y += P) {
    g.fillStyle = shade(base, .93 + R() * .14); g.fillRect(0, y, W, P);
    g.lineWidth = 2.5; g.lineCap = 'round';
    for (let k = 0; k < 7; k++) { const yy = y + 12 + R() * (P - 24), lite = R() < .4; g.strokeStyle = shade(base, lite ? 1.16 : .8); g.globalAlpha = lite ? .3 : .34;
      const x0 = R() * W * .5, len = W * (.3 + R() * .6); g.beginPath(); g.moveTo(x0, yy); g.bezierCurveTo(x0 + len * .3, yy + (R() - .5) * 12, x0 + len * .6, yy + (R() - .5) * 12, x0 + len, yy); g.stroke(); }
    g.globalAlpha = .45; g.fillStyle = shade(base, 1.2); g.fillRect(0, y + 5, W, 4);                 // lit lip under the gap
    g.globalAlpha = .35; g.fillStyle = shade(base, .68); g.fillRect(0, y + P - 9, W, 7);              // shaded lip above the next gap
    g.globalAlpha = .95; g.fillStyle = gap; g.fillRect(0, y - 2, W, 5);
    const x = R() * W; g.fillRect(x, y, 4, P);                                                         // the butt joint
    g.fillStyle = shade(base, .3); for (const dx of [-14, 14]) { g.beginPath(); g.arc(x + dx, y + P * .3, 3.5, 0, 6.29); g.arc(x + dx, y + P * .7, 3.5, 0, 6.29); g.fill(); }
  }
  g.globalAlpha = 1;
  const t = tex(c, rep); if (vertical) t.rotation = Math.PI / 2; return t;
}

// prayer-hall carpet: red field, a patterned border band on every prayer row, a niche with a hanging lamp for each place.
// Every motif is a flat colour with a thin dark outline (a dark tint of the field), so the floor carries as much drawing
// as the walls do.
export function carpetTex({ base = '#b8323a', band = '#d9a441', w = 512, h = 512, rows = 4, seed = 3, rep = [1, 1] } = {}) {
  const K = 3, [c, g] = canvas(w * K, h * K); g.scale(K, K); g.fillStyle = base; g.fillRect(0, 0, w, h); dabs(g, w, h, base, 500, 18, .1, seed);
  const dark = shade(base, .42), lite = shade(base, 1.45); g.lineJoin = g.lineCap = 'round';
  const rh = h / rows;
  g.strokeStyle = shade(base, .8); g.lineWidth = 1.2; g.globalAlpha = .7;      // a fine diamond weave over the whole field
  for (let k = -h; k < w + h; k += 32) { g.beginPath(); g.moveTo(k, 0); g.lineTo(k + h, h); g.moveTo(k, h); g.lineTo(k + h, 0); g.stroke(); }
  g.globalAlpha = 1;
  for (let i = 0; i < rows; i++) {
    const y = i * rh;
    g.fillStyle = shade(base, .62); g.fillRect(0, y, w, 16);                                   // the row's border: a dark strip, a zigzag, a gold line
    g.strokeStyle = lite; g.lineWidth = 1.6; g.beginPath(); for (let x = 0; x <= w; x += 8) g.lineTo(x, y + (x / 8 % 2 ? 4 : 12)); g.stroke();
    g.fillStyle = band; g.fillRect(0, y + 16, w, 4); g.fillStyle = dark; g.fillRect(0, y + 20, w, 1.6); g.fillRect(0, y - .8, w, 1.6);
    for (let x = 16; x < w; x += 64) {   // a niche for each place in the row
      const niche = () => { g.beginPath(); g.moveTo(x, y + rh - 12); g.lineTo(x, y + 48); g.quadraticCurveTo(x + 16, y + 26, x + 32, y + 48); g.lineTo(x + 32, y + rh - 12); g.closePath(); };
      niche(); g.fillStyle = shade(base, .84); g.fill(); g.strokeStyle = dark; g.lineWidth = 5; g.stroke(); g.strokeStyle = shade(band, .95); g.lineWidth = 2.4; g.stroke();
      g.strokeStyle = dark; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x + 16, y + 40); g.lineTo(x + 16, y + rh * .5); g.stroke();                  // the lamp's chain
      g.beginPath(); g.moveTo(x + 16, y + rh * .5); g.quadraticCurveTo(x + 24, y + rh * .6, x + 16, y + rh * .7); g.quadraticCurveTo(x + 8, y + rh * .6, x + 16, y + rh * .5); g.closePath();
      g.fillStyle = band; g.fill(); g.strokeStyle = dark; g.lineWidth = 1.4; g.stroke();
      g.beginPath(); for (let q = 0; q < 8; q++) { const an = q * Math.PI / 4, r = q % 2 ? 4 : 9; g.lineTo(x + 48 + Math.cos(an) * r, y + rh * .62 + Math.sin(an) * r); } g.closePath();    // a star between two niches
      g.fillStyle = lite; g.fill(); g.strokeStyle = dark; g.lineWidth = 1.4; g.stroke();
    }
  }
  const t = tex(c, rep); t.anisotropy = 16; return t;      // seen at a grazing angle in every wide shot: full anisotropic filtering keeps the thin lines steady
}

// wall: plaster with painted arched windows (dark frame lines + glowing panes)
export function wallTex({ base = '#efe2c8', frame = '#4a3a30', glass = '#9fc3e8', w = 1024, h = 512, cols = 3, seed = 4, rep = [1, 1], night = false, rows = [0, 1], ashlar = [28, 16] } = {}) {
  // drawn three times larger than asked (K), so the thin stone joints stay thin on a 30 m wall
  const K = 3, [c, g] = canvas(w * K, h * K); g.scale(K, K); g.fillStyle = base; g.fillRect(0, 0, w, h); dabs(g, w, h, base, 900, 30, .1, seed);
  const R = rng(seed + 40), bh2 = h / ashlar[1], bw2 = w / ashlar[0];                    // ashlar: thin joints, a dark TINT of the stone (lighter than ink)
  for (let y = 0, row = 0; y < h; y += bh2, row++) for (let x = (row % 2) * bw2 / 2 - bw2; x < w; x += bw2) {
    g.fillStyle = shade(base, .9 + R() * .2); g.globalAlpha = .75; g.fillRect(x, y, bw2, bh2);
    g.globalAlpha = .6; g.fillStyle = shade(base, 1.16); g.fillRect(x + 1, y + 1, bw2 - 2, 1.2); g.fillRect(x + .6, y + 1, 1, bh2 - 2); g.fillStyle = shade(base, .7); g.fillRect(x + 1, y + bh2 - 1.9, bw2 - 2, 1.4);
    g.globalAlpha = .5; g.fillStyle = shade(base, .74); for (let k = 0; k < 4; k++) { g.beginPath(); g.arc(x + R() * bw2, y + R() * bh2, .5 + R() * .7, 0, 6.29); g.fill(); }
    g.globalAlpha = .92; g.fillStyle = shade(base, .4); g.fillRect(x - .5, y, 1, bh2); g.fillRect(x, y - .5, bw2, 1);
  }
  g.globalAlpha = 1;
  g.strokeStyle = shade(base, .82); g.lineWidth = 6; g.beginPath(); g.moveTo(0, h * .52); g.lineTo(w, h * .52); g.stroke();
  const cw = w / cols;
  for (let i = 0; i < cols; i++) {
    for (const [y0, wh, ww] of [[h * .1, h * .3, cw * .36], [h * .62, h * .3, cw * .4]].filter((_, k) => rows.includes(k))) {
      const x = i * cw + (cw - ww) / 2;
      const arch = () => { g.beginPath(); g.moveTo(x, y0 + wh); g.lineTo(x, y0 + ww * .5); g.quadraticCurveTo(x, y0, x + ww / 2, y0 - ww * .12); g.quadraticCurveTo(x + ww, y0, x + ww, y0 + ww * .5); g.lineTo(x + ww, y0 + wh); g.closePath(); };
      arch(); const gr = g.createLinearGradient(0, y0, 0, y0 + wh);
      gr.addColorStop(0, shade(glass, night ? .55 : 1.1)); gr.addColorStop(1, shade(glass, night ? .35 : .85)); g.fillStyle = gr; g.fill();
      g.save(); arch(); g.clip(); g.strokeStyle = shade(frame, 1.2); g.lineWidth = 3;
      for (let k = 1; k < 4; k++) { g.beginPath(); g.moveTo(x + ww * k / 4, y0 - ww); g.lineTo(x + ww * k / 4, y0 + wh); g.stroke(); }
      for (let k = 1; k < 5; k++) { g.beginPath(); g.moveTo(x, y0 + wh * k / 5); g.lineTo(x + ww, y0 + wh * k / 5); g.stroke(); }
      g.restore(); arch(); g.strokeStyle = frame; g.lineWidth = 7; g.stroke();
    }
  }
  return tex(c, rep);
}

// Dome inside, painted with its own light (use it on a MeshBasicMaterial). The canvas is the dome unrolled:
// x = around, y = from the crown (top row) down to the foot (bottom row), so a vertical stripe is a ray from the crown.
//   crown medallion + sunburst · a field of tall palmettes between gold ribs · a scroll band · rosettes ·
//   a ring of arched windows with striped arches (`windows` of them, glowing with the night outside) · cornice.
// Lamp light is painted in from below: warm at the foot, cool and deep toward the crown, gold catching the light.
// Every painted shape carries a thin dark outline (the style: flat colour first, then thin lines). Drawn at twice the
// size (K), so those lines stay crisp where the dome fills the frame.
export function domeTex({ w = 4096, h = 1536, windows = 28, glass = ['#2a3aa8', '#7f9cff'] } = {}) {
  const K = 2, [c, g] = canvas(w * K, h * K), Y = f => h * f, INK = D('#1a1230'); g.scale(K, K);
  const edge = (lw = 4) => { g.strokeStyle = INK; g.lineWidth = lw; g.stroke(); };
  const band = (f0, f1, col) => { g.fillStyle = col; g.fillRect(0, Y(f0), w, Y(f1) - Y(f0) + 1); };
  const line = (f, lw = 4, col = INK) => { g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); g.moveTo(0, Y(f)); g.lineTo(w, Y(f)); g.stroke(); };
  // crown: gold disc, then a sunburst of gold and deep blue rays
  band(0, .05, D('#f2c45a'));
  const rays = 32, rw = w / rays;
  for (let i = 0; i < rays; i++) { g.fillStyle = i % 2 ? D('#f0b846') : D('#243a94'); g.fillRect(i * rw, Y(.05), rw + 1, Y(.15) - Y(.05)); }
  for (let i = 0; i < rays; i++) { g.beginPath(); g.moveTo(i * rw, Y(.05)); g.lineTo(i * rw, Y(.15)); edge(3.5); }
  for (let i = 0; i < rays; i++) { g.fillStyle = D('#c8372f'); g.beginPath(); g.moveTo(i * rw + rw * .5, Y(.085)); g.lineTo(i * rw + rw * .82, Y(.15)); g.lineTo(i * rw + rw * .18, Y(.15)); g.closePath(); g.fill(); edge(3.5); }
  band(.15, .185, D('#b02c34'));
  for (let x = rw / 4; x < w; x += rw / 2) { g.fillStyle = D('#f6d27a'); g.beginPath(); g.ellipse(x, Y(.1675), rw * .09, Y(.011), 0, 0, 6.29); g.fill(); edge(3); }
  // the field: deep blue, 16 tall palmettes, gold ribs between them
  let gr = g.createLinearGradient(0, Y(.185), 0, Y(.5)); gr.addColorStop(0, D('#1b2c80')); gr.addColorStop(1, D('#2f55b6'));
  g.fillStyle = gr; g.fillRect(0, Y(.185), w, Y(.5) - Y(.185));
  const pal = 16, pw = w / pal;
  for (let i = 0; i < pal; i++) {
    const x = (i + .5) * pw, y0 = Y(.2), y1 = Y(.485), ym = y0 + (y1 - y0) * .62;
    const drop = (k, col) => { g.fillStyle = col; g.beginPath(); g.moveTo(x, y0 + (y1 - y0) * (1 - k) * .5);
      g.bezierCurveTo(x + pw * .1 * k, y0 + (y1 - y0) * .3, x + pw * .42 * k, ym - (y1 - y0) * .1, x + pw * .36 * k, ym + (y1 - ym) * .2 * k);
      g.quadraticCurveTo(x + pw * .22 * k, y1 - (1 - k) * (y1 - y0) * .2, x, y1 - (1 - k) * (y1 - y0) * .16);
      g.quadraticCurveTo(x - pw * .22 * k, y1 - (1 - k) * (y1 - y0) * .2, x - pw * .36 * k, ym + (y1 - ym) * .2 * k);
      g.bezierCurveTo(x - pw * .42 * k, ym - (y1 - y0) * .1, x - pw * .1 * k, y0 + (y1 - y0) * .3, x, y0 + (y1 - y0) * (1 - k) * .5); g.closePath(); g.fill(); edge(k > .7 ? 4 : 3.5); };
    drop(1, D('#f0b846')); drop(.88, D('#1fa3a8')); drop(.6, D('#f6d27a')); drop(.48, D('#c8372f'));
    g.fillStyle = D('#f6d27a'); g.beginPath(); g.ellipse(x, ym, pw * .05, (y1 - y0) * .05, 0, 0, 6.29); g.fill(); edge(3.5);
    g.fillStyle = D('#f0b846'); g.fillRect(i * pw - 9, Y(.185), 18, Y(.5) - Y(.185));                     // rib
    for (const s of [-9, 9]) { g.beginPath(); g.moveTo(i * pw + s, Y(.185)); g.lineTo(i * pw + s, Y(.5)); edge(3); }
    g.fillStyle = D('#c8372f'); for (const f of [.24, .32, .4, .46]) { g.beginPath(); g.ellipse(i * pw, Y(f), 20, 20 * h / w * 2.2, 0, 0, 6.29); g.fill(); edge(3); }
    for (const s of [-1, 1]) for (const [f, r] of [[.225, 13], [.47, 15]]) {                                // gold stars in the blue between the palmettes
      g.fillStyle = D('#f6d27a'); g.beginPath(); for (let q = 0; q < 8; q++) { const an = q * Math.PI / 4, rr = q % 2 ? r * .42 : r; g.lineTo(x + s * pw * .33 + Math.cos(an) * rr, Y(f) + Math.sin(an) * rr * 1.5); } g.closePath(); g.fill(); edge(2.5); }
  }
  // scroll band: cream, a running wave with curls
  band(.5, .585, D('#f1e3c2'));
  g.strokeStyle = D('#243a94'); g.lineWidth = 9; g.lineCap = 'round';
  const sw = w / 64, sy = Y(.5425), sa = Y(.024);
  g.beginPath(); for (let x = 0; x <= w; x += 8) { const y = sy + Math.sin(x / sw * Math.PI) * sa; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke();
  for (let i = 0; i < 64; i++) { g.fillStyle = i % 2 ? D('#c8372f') : D('#1fa3a8'); g.beginPath(); g.ellipse((i + .5) * sw, sy - (i % 2 ? -1 : 1) * sa * .25, sw * .2, sa * .5, 0, 0, 6.29); g.fill(); edge(3); }
  // rosettes on turquoise
  band(.585, .685, D('#1c8f98'));
  const rn = windows * 2, rsw = w / rn;
  for (let i = 0; i < rn; i++) { const x = (i + .5) * rsw, y = Y(.635), ry = Y(.036), rx = rsw * .34;
    g.fillStyle = D('#f0b846'); g.beginPath(); g.ellipse(x, y, rx, ry, 0, 0, 6.29); g.fill(); edge(3.5);
    g.fillStyle = D('#f8f0dc'); for (let k = 0; k < 8; k++) { const a = k / 8 * 6.283; g.beginPath(); g.ellipse(x + Math.cos(a) * rx * .58, y + Math.sin(a) * ry * .58, rx * .2, ry * .2, 0, 0, 6.29); g.fill(); }
    g.fillStyle = D('#c8372f'); g.beginPath(); g.ellipse(x, y, rx * .3, ry * .3, 0, 0, 6.29); g.fill(); edge(2.5); }
  band(.685, .715, D('#f0b846'));
  // the window ring
  band(.715, .955, D('#ead9b6'));
  const ww = w / windows;
  for (let i = 0; i < windows; i++) {
    const x = (i + .5) * ww, y0 = Y(.775), y1 = Y(.93), hw = ww * .25, top = y0 - hw * (h / w) * 3.2;
    const arch = (k) => { g.beginPath(); g.moveTo(x - hw * k, y1 + (k - 1) * 14); g.lineTo(x - hw * k, y0); g.bezierCurveTo(x - hw * k, top - (k - 1) * 60, x + hw * k, top - (k - 1) * 60, x + hw * k, y0); g.lineTo(x + hw * k, y1 + (k - 1) * 14); g.closePath(); };
    // striped arch around the window (clip a ring, fill red/white wedges)
    g.save(); arch(1.62); g.clip(); g.fillStyle = D('#f4ead4'); g.fillRect(x - ww, top - 200, ww * 2, y1 - top + 400);
    g.fillStyle = D('#c0343a'); for (let k = -5; k <= 5; k += 2) { const a = -Math.PI / 2 + k * .3; g.beginPath(); g.moveTo(x, y0 + 30); g.lineTo(x + Math.cos(a - .15) * ww, y0 + 30 + Math.sin(a - .15) * ww * 2.4); g.lineTo(x + Math.cos(a + .15) * ww, y0 + 30 + Math.sin(a + .15) * ww * 2.4); g.closePath(); g.fill(); }
    g.fillStyle = D('#ead9b6'); g.fillRect(x - ww, y0 + 30, ww * 2, y1 - y0 + 100);
    g.restore(); g.strokeStyle = INK; g.lineWidth = 3.5; arch(1.62); g.stroke();
    // glass
    arch(1); gr = g.createLinearGradient(0, top, 0, y1); gr.addColorStop(0, D(glass[1])); gr.addColorStop(1, D(glass[0])); g.fillStyle = gr; g.fill();
    g.save(); arch(1); g.clip(); g.strokeStyle = D('#16224f'); g.lineWidth = 3.5;
    for (let r = 0; r < 5; r++) for (let q = 0; q < 3; q++) { g.beginPath(); g.ellipse(x - hw * .66 + q * hw * .66, top + 40 + r * (y1 - top) / 4.6, hw * .31, (y1 - top) / 10, 0, 0, 6.29); g.stroke(); }
    g.restore(); g.strokeStyle = INK; g.lineWidth = 4.5; arch(1); g.stroke();
  }
  // cornice
  band(.955, 1, D('#f0b846'));
  g.fillStyle = D('#b02c34'); const zn = windows * 6, zw = w / zn; for (let i = 0; i < zn; i++) { g.beginPath(); g.moveTo(i * zw, Y(1)); g.lineTo((i + .5) * zw, Y(.965)); g.lineTo((i + 1) * zw, Y(1)); g.closePath(); g.fill(); edge(2.5); }
  for (const f of [.05, .15, .185, .5, .585, .685, .715, .955]) line(f, 4);          // painted lines stay 3-5 px on screen (analiz/doku.md)
  // painted light: warm from the lamps below, cool and deep toward the crown; the crown's gold catches a little of it
  g.globalCompositeOperation = 'multiply';
  gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#9a94d8'); gr.addColorStop(.16, '#8f8ad2'); gr.addColorStop(.5, '#c9bfe0'); gr.addColorStop(.74, '#ffeccc'); gr.addColorStop(1, '#ffdfae');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.globalCompositeOperation = 'screen';
  gr = g.createLinearGradient(0, 0, 0, Y(.2)); gr.addColorStop(0, 'rgba(255,196,110,.55)'); gr.addColorStop(1, 'rgba(255,196,110,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, Y(.2));
  g.globalCompositeOperation = 'source-over';
  const t = tex(c, [1, 1]); t.anisotropy = 8; return t;
}

// A round calligraphy-plate without writing: a twelve-fold star rosette in gold on deep green (unlit colours).
export function roundelTex({ s = 512, ground = '#12553f', gold = '#f0b846' } = {}) {
  const [c, g] = canvas(s, s), R = s / 2;
  g.clearRect(0, 0, s, s); g.translate(R, R);
  g.fillStyle = D('#3a2412'); g.beginPath(); g.arc(0, 0, R * .98, 0, 6.29); g.fill();
  g.fillStyle = D(gold); g.beginPath(); g.arc(0, 0, R * .9, 0, 6.29); g.fill();
  g.fillStyle = D(ground); g.beginPath(); g.arc(0, 0, R * .8, 0, 6.29); g.fill();
  g.strokeStyle = D(gold); g.lineWidth = s * .018; g.lineJoin = 'round';
  for (const [n, r0, r1] of [[12, .74, .42], [12, .4, .2]]) {
    g.beginPath(); for (let k = 0; k <= n * 2; k++) { const a = k / (n * 2) * 6.283 - Math.PI / 2, r = R * (k % 2 ? r1 : r0); k ? g.lineTo(Math.cos(a) * r, Math.sin(a) * r) : g.moveTo(Math.cos(a) * r, Math.sin(a) * r); } g.closePath(); g.stroke();
  }
  for (let k = 0; k < 12; k++) { const a = k / 12 * 6.283; g.fillStyle = D(gold); g.beginPath(); g.arc(Math.cos(a) * R * .6, Math.sin(a) * R * .6, R * .035, 0, 6.29); g.fill(); }
  g.fillStyle = D(gold); g.beginPath(); g.arc(0, 0, R * .12, 0, 6.29); g.fill();
  g.fillStyle = D('#c8372f'); g.beginPath(); g.arc(0, 0, R * .06, 0, 6.29); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}

export function tileTex({ a = '#2f7fb8', b = '#f2ead8', ink = '#1f2a44', w = 256, h = 256, rep = [1, 1] } = {}) {
  const [c, g] = canvas(w, h); g.fillStyle = b; g.fillRect(0, 0, w, h);
  g.fillStyle = a; g.strokeStyle = ink; g.lineWidth = 3;
  for (const [x, y] of [[64, 64], [192, 192], [192, 64], [64, 192]]) {
    g.beginPath(); for (let k = 0; k < 8; k++) { const an = k * Math.PI / 4, r = k % 2 ? 22 : 46; g.lineTo(x + Math.cos(an) * r, y + Math.sin(an) * r); } g.closePath(); g.fill(); g.stroke();
  }
  g.strokeStyle = shade(b, .7); g.lineWidth = 4; g.strokeRect(0, 0, w, h); g.beginPath(); g.moveTo(w / 2, 0); g.lineTo(w / 2, h); g.moveTo(0, h / 2); g.lineTo(w, h / 2); g.stroke();
  return tex(c, rep);
}

// Glazed wall tiles with a repeating pattern. One repeat = one pattern cell (two tiles by two).
// A plain wall reads as empty in this style however fine its masonry is: what the eye (and the fine-detail measure,
// analiz/doku.md) responds to is PATTERN: flat colour shapes with thin dark outlines on a light ground.
//   kind 'lale'    a pointed medallion with a flower in it, rosettes on the corners   (a dado, a panel)
//   kind 'yildiz'  eight-pointed stars, small diamonds between them                   (a kitchen wall, a surround)
// a / b / c = the three glaze colours. Keep them LIGHT to mid-toned: a dark blue reads as a hole in the wall at night,
// and a dark fill merges with its own outline into one fat stroke. The drawing should be carried by the thin outlines.
export function ciniTex({ kind = 'lale', ground = '#f4eee0', a = '#5b8fe0', b = '#3fbcae', c = '#e8603f', ink = '#1b2a5c', s = 512, rep = [1, 1], seed = 21 } = {}) {
  const [cv, g] = canvas(s, s), u = s / 512;
  g.fillStyle = ground; g.fillRect(0, 0, s, s); dabs(g, s, s, ground, 90, 46 * u, .05, seed);
  g.lineJoin = g.lineCap = 'round'; g.scale(u, u);
  const paint = (col, w = 5) => { g.fillStyle = col; g.fill(); if (w) { g.strokeStyle = ink; g.lineWidth = w; g.stroke(); } };
  const star = (x, y, r0, r1, n = 8, rot = 0) => { g.beginPath(); for (let k = 0; k < n * 2; k++) { const an = rot + k * Math.PI / n, r = k % 2 ? r1 : r0; g.lineTo(x + Math.cos(an) * r, y + Math.sin(an) * r); } g.closePath(); };
  const leaf = (x, y, len, wid, rot) => { g.save(); g.translate(x, y); g.rotate(rot); g.beginPath(); g.moveTo(0, -len); g.quadraticCurveTo(wid, 0, 0, len); g.quadraticCurveTo(-wid, 0, 0, -len); g.closePath(); g.restore(); };
  const disc = (x, y, r) => { g.beginPath(); g.arc(x, y, r, 0, 6.29); };
  const ogee = (k) => { g.beginPath(); g.moveTo(256, 256 - 232 * k); g.bezierCurveTo(256 + 40 * k, 256 - 120 * k, 256 + 176 * k, 256 - 96 * k, 256 + 176 * k, 256);
    g.bezierCurveTo(256 + 176 * k, 256 + 96 * k, 256 + 40 * k, 256 + 120 * k, 256, 256 + 232 * k); g.bezierCurveTo(256 - 40 * k, 256 + 120 * k, 256 - 176 * k, 256 + 96 * k, 256 - 176 * k, 256);
    g.bezierCurveTo(256 - 176 * k, 256 - 96 * k, 256 - 40 * k, 256 - 120 * k, 256, 256 - 232 * k); g.closePath(); };
  if (kind === 'yildiz') {
    star(256, 256, 244, 132, 8, 0); paint(a, 6);
    star(256, 256, 150, 84, 8, Math.PI / 8); paint(ground, 4);
    disc(256, 256, 44); paint(c, 4); disc(256, 256, 15); paint(ground, 0);
    for (const [x, y] of [[0, 0], [512, 0], [0, 512], [512, 512]]) { star(x, y, 92, 92 * .7071, 2, 0); paint(b, 5); disc(x, y, 24); paint(ground, 4); }   // diamonds where four cells meet
    for (let k = 0; k < 8; k++) { const an = k * Math.PI / 4 + Math.PI / 8; disc(256 + Math.cos(an) * 196, 256 + Math.sin(an) * 196, 9); paint(c, 0); }
  } else {
    ogee(1); paint(a, 6); ogee(.85); paint(ground, 4);
    leaf(222, 322, 58, 26, .55); paint(b, 4); leaf(290, 322, 58, 26, -.55); paint(b, 4);
    g.beginPath(); g.moveTo(256, 372); g.lineTo(256, 250); g.strokeStyle = ink; g.lineWidth = 5; g.stroke();
    star(256, 214, 62, 30, 6, Math.PI / 6); paint(c, 4); disc(256, 214, 15); paint(ground, 3);
    for (const [x, y] of [[0, 0], [512, 0], [0, 512], [512, 512]]) { disc(x, y, 98); paint(b, 5); star(x, y, 74, 36, 8, 0); paint(ground, 4); disc(x, y, 22); paint(c, 3); }
    for (const [x, y, r] of [[0, 256, 0], [512, 256, 0], [256, 0, Math.PI / 2], [256, 512, Math.PI / 2]]) { leaf(x, y, 64, 24, r); paint(a, 4); }
  }
  g.strokeStyle = shade(ground, .58); g.lineWidth = 2.5; g.globalAlpha = .7;                // the joints between the four tiles
  g.beginPath(); for (const v of [0, 256, 512]) { g.moveTo(v, 0); g.lineTo(v, 512); g.moveTo(0, v); g.lineTo(512, v); } g.stroke();
  g.globalAlpha = 1; const t = tex(cv, rep); t.anisotropy = 8; return t;
}

// A painted band for the middle of a tall wall: two interlaced ribbons, a flower or a pair of leaves in every loop,
// a gold edge above and below. One repeat = four loops (use rep = [length / (4 * height), 1]).
// The ribbons are LIGHT with a thin dark edge: four long thin lines run the whole length of the wall.
export function frizTex({ ground = '#f1e6c8', a = '#f0c455', b = '#8adccc', c = '#e8603f', gold = '#e8b23e', ink = '#1b2a5c', w = 1024, h = 256, rep = [1, 1], seed = 23 } = {}) {
  const [cv, g] = canvas(w, h); g.fillStyle = ground; g.fillRect(0, 0, w, h); dabs(g, w, h, ground, 120, 40, .05, seed);
  g.lineJoin = g.lineCap = 'round';
  const wave = (ph, col, lw) => { g.beginPath(); for (let x = -8; x <= w + 8; x += 8) { const y = h / 2 + Math.sin(x / 256 * Math.PI * 2 + ph) * h * .25; x < 0 ? g.moveTo(x, y) : g.lineTo(x, y); } g.strokeStyle = col; g.lineWidth = lw; g.stroke(); };
  for (const ph of [0, Math.PI]) { wave(ph, ink, 23); wave(ph, ph ? b : a, 14.5); }
  for (let i = 0; i < 8; i++) {                                               // the loops: flower, leaves, flower, ...
    const x = 64 + i * 128, y = h / 2; g.strokeStyle = ink;
    if (i % 2) { for (const s of [-1, 1]) { g.save(); g.translate(x + s * 15, y); g.rotate(s * .5); g.beginPath(); g.moveTo(0, -30); g.quadraticCurveTo(15, 0, 0, 30); g.quadraticCurveTo(-15, 0, 0, -30); g.closePath(); g.restore(); g.fillStyle = b; g.fill(); g.lineWidth = 3.5; g.stroke(); } }
    else { g.beginPath(); for (let k = 0; k < 12; k++) { const an = k * Math.PI / 6, r = k % 2 ? 15 : 33; g.lineTo(x + Math.cos(an) * r, y + Math.sin(an) * r); } g.closePath(); g.fillStyle = c; g.fill(); g.lineWidth = 3.5; g.stroke();
      g.beginPath(); g.arc(x, y, 8, 0, 6.29); g.fillStyle = ground; g.fill(); }
    g.beginPath(); g.arc(x - 64, y, 9, 0, 6.29); g.fillStyle = gold; g.fill(); g.lineWidth = 3; g.stroke();     // a gold stud on every crossing
  }
  for (const y of [0, h - 30]) {                                              // edges: gold, a red dash line, ink on both sides
    g.fillStyle = gold; g.fillRect(0, y, w, 30); g.fillStyle = c; for (let x = 8; x < w; x += 32) g.fillRect(x, y + 11, 16, 8);
    g.fillStyle = ink; g.fillRect(0, y ? y - 2 : 28, w, 4);
  }
  const t = tex(cv, rep); t.anisotropy = 8; return t;
}

// soot-blackened plaster: dark violet-blue (never pure black) with scraped lighter strokes
export function sootTex({ base = '#211b2c', w = 512, h = 512, seed = 9, scraped = 0, rep = [1, 1] } = {}) {
  const [c, g] = canvas(w, h); g.fillStyle = base; g.fillRect(0, 0, w, h); dabs(g, w, h, base, 700, 28, .5, seed);
  const R = rng(seed + 7);
  g.strokeStyle = '#4b4058'; g.lineWidth = 10; g.lineCap = 'round';
  for (let i = 0; i < 26 * scraped; i++) { const x = R() * w, y = R() * h; g.globalAlpha = .5; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 40 + R() * 60, y + (R() - .5) * 20); g.stroke(); }
  g.globalAlpha = 1; return tex(c, rep);
}

export function flat(color, opts = {}) { return new THREE.MeshLambertMaterial({ color, ...opts }); }
export function painted(map, opts = {}) { return new THREE.MeshLambertMaterial({ map, ...opts }); }
