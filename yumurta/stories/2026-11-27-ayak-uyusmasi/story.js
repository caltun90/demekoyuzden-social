// Ayağın neden uyuşur? Demek O Yüzden günlük Short (yumurta stili), 27 Kasım 2026.
// Bilgi: uzun süre üstüne oturunca bacaktaki sinir (ve onu besleyen ince damarlar) sıkışır, sinyal düzgün iletilemez;
// baskı kalkınca sinir yeniden çalışmaya başlar ve bir süre düzensiz sinyal yollar, beyin bunu karıncalanma ve iğnelenme
// olarak algılar (parestezi). Kaynaklar SCRIPT.md'de.
// Tek set: OTURMA ODASI (pencere ışığı, halı, yer sofrası, sedir, çay sehpası). Kahraman (sen) ve dede.
// İskelet v1: kurulum (sofra) -> üç vuruş (ayak yok, iğneler, yığılma; dedenin kahkahası büyür) -> kırılma (dede susar,
// sinir + hortum) -> döngü (son plan ilk planın kadrajı, yine ayağının üstünde).
import * as THREE from 'three';
import { stoneTex, woodTex, tileTex, carpetTex, painted, flat } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { beam, glow } from '/engine/src/fx.js';
import { Parcaciklar } from '/engine/src/parcacik.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-27-ayak-uyusmasi';
export const FPS = 30;
export let DUR = 33.5;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lerpN = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;
let W, PF, cast = {}, dyn = { cards: [] };

function wordTimes(words) {
  const norm = s => s.toLocaleLowerCase('tr-TR').replace(/[^\p{L}\p{N}]/gu, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w); };
}
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus|Icosahedron|Cone|Sphere/.test(o.geometry.type) && !o.userData.noShadow && o.material.isMeshLambertMaterial) o.castShadow = true;
  });
}
function card(scene, w, h, draw, { pw = 512 } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); draw(c.getContext('2d'), c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false }));
  m.layers.set(1); m.renderOrder = 20; m.visible = false; scene.add(m); dyn.cards.push(m); return m;
}
function dynCard(scene, w, h, draw, { pw = 512, steps = 30 } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); const g = c.getContext('2d');
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false }));
  m.layers.set(1); m.renderOrder = 20; m.visible = false; scene.add(m); dyn.cards.push(m);
  let key = null;
  m.userData.set = (...v) => { const q = v.map(x => Math.round(x * steps) / steps), k = q.join(','); if (k === key) return; key = k; g.clearRect(0, 0, c.width, c.height); draw(g, c.width, c.height, ...q); t.needsUpdate = true; };
  return m;
}

// ---------------------------------------------------------------- drawings
const CREAM = '#fbf7ee';
function sockPath(c, w, h) {
  c.beginPath(); c.moveTo(w * .26, h * .1); c.lineTo(w * .56, h * .1); c.lineTo(w * .58, h * .5);
  c.quadraticCurveTo(w * .95, h * .56, w * .93, h * .76); c.quadraticCurveTo(w * .9, h * .92, w * .66, h * .91); c.lineTo(w * .36, h * .91);
  c.quadraticCurveTo(w * .18, h * .9, w * .22, h * .68); c.closePath();
}
// a striped sock: the foot of the story. mode 'z' = asleep (Z z), 'ghost' = "as if it were not there"
function drawSock(mode) {
  return (c, w, h) => {
    c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = w * .035;
    if (mode === 'ghost') { c.setLineDash([w * .06, w * .06]); c.globalAlpha = .4; c.fillStyle = '#ffffff'; sockPath(c, w, h); c.fill(); c.globalAlpha = 1; c.lineWidth = w * .05; c.strokeStyle = '#ffffff'; sockPath(c, w, h); c.stroke(); c.setLineDash([]); return; }
    c.fillStyle = CREAM; sockPath(c, w, h); c.fill();
    c.save(); sockPath(c, w, h); c.clip();
    c.fillStyle = '#e2463f'; c.fillRect(0, h * .1, w, h * .11); c.fillRect(w * .76, h * .5, w * .3, h * .5); c.fillRect(0, h * .74, w * .34, h * .3);
    c.fillStyle = '#3f8fd8'; c.fillRect(0, h * .27, w, h * .05); c.fillRect(0, h * .37, w, h * .05);
    c.restore(); sockPath(c, w, h); c.stroke();
    if (mode === 'z') for (const [ch, x, y, s] of [['Z', .78, .3, .26], ['z', .9, .13, .17]]) {
      c.font = `900 ${h * s}px "Arial Black", "Inter", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.lineWidth = w * .06; c.strokeStyle = PLUM; c.strokeText(ch, w * x, h * y); c.fillStyle = '#ffe15a'; c.fillText(ch, w * x, h * y);
    }
  };
}
// pins that point at the middle of the card
function drawNeedles(c, w, h) {
  c.lineCap = 'round';
  for (let k = 0; k < 9; k++) {
    const a = k / 9 * 6.283 + .2, r0 = w * (.2 + (k % 2) * .05), r1 = w * .44, x0 = w / 2 + Math.cos(a) * r0, y0 = h / 2 + Math.sin(a) * r0, x1 = w / 2 + Math.cos(a) * r1, y1 = h / 2 + Math.sin(a) * r1;
    c.strokeStyle = PLUM; c.lineWidth = w * .05; c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
    c.strokeStyle = '#eef3fb'; c.lineWidth = w * .022; c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
    c.fillStyle = k % 3 ? '#ff5a4a' : '#ffe15a'; c.strokeStyle = PLUM; c.lineWidth = w * .016; c.beginPath(); c.arc(x1, y1, w * .042, 0, 6.29); c.fill(); c.stroke();
  }
}
function drawMark(ch, col) {
  return (c, w, h) => { c.lineJoin = 'round'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .84}px "Arial Black", "Inter", sans-serif`;
    c.strokeStyle = PLUM; c.lineWidth = 36; c.strokeText(ch, w / 2, h * .54); c.fillStyle = col; c.fillText(ch, w / 2, h * .54); };
}
function star(c, x, y, r, col) {
  c.beginPath(); for (let k = 0; k < 10; k++) { const a = k * Math.PI / 5 - Math.PI / 2, rr = k % 2 ? r * .45 : r; c.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } c.closePath();
  c.fillStyle = col; c.strokeStyle = PLUM; c.lineWidth = r * .28; c.lineJoin = 'round'; c.stroke(); c.fill();
}
function drawStars(c, w, h) { star(c, w * .2, h * .6, w * .13, '#ffe15a'); star(c, w * .5, h * .34, w * .16, '#ffe15a'); star(c, w * .8, h * .6, w * .13, '#ffffff'); }
// the wall clock of "a whole hour": a = turns of the minute hand
function drawClock(c, w, h, a) {
  c.lineCap = 'round'; c.fillStyle = CREAM; c.strokeStyle = PLUM; c.lineWidth = w * .06; c.beginPath(); c.arc(w / 2, h / 2, w * .44, 0, 6.29); c.fill(); c.stroke();
  for (let k = 0; k < 12; k++) { const q = k / 12 * 6.283; c.lineWidth = w * .025; c.beginPath(); c.moveTo(w / 2 + Math.cos(q) * w * .34, h / 2 + Math.sin(q) * w * .34); c.lineTo(w / 2 + Math.cos(q) * w * .38, h / 2 + Math.sin(q) * w * .38); c.stroke(); }
  const hand = (q, len, lw, col) => { c.strokeStyle = col; c.lineWidth = lw; c.beginPath(); c.moveTo(w / 2, h / 2); c.lineTo(w / 2 + Math.sin(q) * len, h / 2 - Math.cos(q) * len); c.stroke(); };
  hand(a * 6.283 / 12 + 1, w * .2, w * .06, PLUM); hand(a * 6.283, w * .31, w * .045, '#e2463f');
  c.fillStyle = PLUM; c.beginPath(); c.arc(w / 2, h / 2, w * .04, 0, 6.29); c.fill();
}
function brainPath(c, x, y, r) {
  c.beginPath();
  for (const [dx, dy, k] of [[-.55, .05, .55], [-.3, -.38, .52], [.15, -.45, .56], [.55, -.15, .52], [.5, .3, .46], [.05, .38, .5], [-.35, .36, .44]]) { c.moveTo(x + (dx + k) * r, y + dy * r); c.arc(x + dx * r, y + dy * r, k * r, 0, 6.29); }
}
function drawBrainAt(c, x, y, r) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = r * .22; brainPath(c, x, y, r); c.stroke();
  c.fillStyle = '#f7a8c4'; brainPath(c, x, y, r); c.fill();
  c.strokeStyle = '#d9648e'; c.lineWidth = r * .09;
  c.beginPath(); c.moveTo(x - r * .1, y - r * .8); c.bezierCurveTo(x + r * .25, y - r * .4, x - r * .3, y, x + r * .05, y + r * .7); c.stroke();
  c.beginPath(); c.moveTo(x - r * .7, y - r * .1); c.quadraticCurveTo(x - r * .45, y - r * .3, x - r * .25, y - r * .05); c.moveTo(x + r * .3, y - r * .1); c.quadraticCurveTo(x + r * .55, y - r * .35, x + r * .8, y - r * .05);
  c.moveTo(x - r * .6, y + r * .35); c.quadraticCurveTo(x - r * .4, y + r * .15, x - r * .2, y + r * .4); c.moveTo(x + r * .3, y + r * .35); c.quadraticCurveTo(x + r * .5, y + r * .15, x + r * .7, y + r * .35); c.stroke();
}
function drawBrain(c, w, h) { drawBrainAt(c, w / 2, h / 2, w * .34); }
// the diagram of the story: a line that carries something (kind 0: the nerve, foot -> brain; kind 1: a garden hose, tap -> spout),
// a weight that squeezes it (p = 0..1), what flows in it (ph = time), and the jumble of signals after it opens (chaos = 0..1)
function drawPinch(c, w, h, kind, p, ph, chaos) {
  const hose = kind > .5; c.lineJoin = c.lineCap = 'round';
  c.fillStyle = CREAM; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 36); c.fill(); c.stroke();
  const y0 = h * .66, lw = h * .13, xa = w * .2, xb = w * .8, xm = w * .5, sg = w * .075;
  const dip = x => p * lw * .82 * Math.exp(-(((x - xm) / sg) ** 2));
  // the line: squeezed thin under the weight
  c.beginPath(); for (let i = 0; i <= 48; i++) { const x = lerpN(xa, xb, i / 48); c.lineTo(x, y0 - lw / 2 + dip(x)); } for (let i = 48; i >= 0; i--) { const x = lerpN(xa, xb, i / 48); c.lineTo(x, y0 + lw / 2); } c.closePath();
  c.fillStyle = hose ? '#58b848' : '#ffd23a'; c.fill(); c.lineWidth = 9; c.stroke();
  // what flows: dots that stop at the squeeze
  const col = hose ? '#3fb6ff' : '#ff7a2a', n = 6, open = p < .45;
  for (let i = 0; i < n; i++) {
    const u = (ph * .95 + i / n) % 1; if (!open && u > .44) continue;
    const x = hose ? lerpN(xa + 14, xb - 14, u) : lerpN(xb - 14, xa + 14, u), k = open ? 1 : Math.min(1, (.44 - u) / .08 + .25);
    c.fillStyle = col; c.strokeStyle = PLUM; c.lineWidth = 5; c.globalAlpha = Math.max(0, Math.min(1, k)); c.beginPath(); c.arc(x, y0 + (open ? 0 : 0), lw * .26, 0, 6.29); c.fill(); c.stroke(); c.globalAlpha = 1;
  }
  if (chaos > 0) {            // the nerve wakes up: signals of every kind, all at once, out of order
    const cols = ['#ff5a4a', '#3fc6ff', '#9be05a', '#ff8ad0', '#ffffff', '#b06ad8'];
    for (let i = 0; i < 16; i++) {
      const sp = .7 + (i * 37 % 10) / 6, dir = i % 3 ? 1 : -1, u = ((ph * sp * dir + i * .173) % 1 + 1) % 1, x = lerpN(xb - 14, xa + 14, u);
      const y = y0 + Math.sin(ph * 19 + i * 2.3) * lw * .34; c.globalAlpha = chaos;
      c.fillStyle = cols[i % cols.length]; c.strokeStyle = PLUM; c.lineWidth = 5; c.beginPath(); c.arc(x, y, lw * (.16 + (i % 4) * .04), 0, 6.29); c.fill(); c.stroke();
    }
    c.strokeStyle = '#ff5a4a'; c.lineWidth = 9;
    for (let i = 0; i < 4; i++) { const x = lerpN(xa + 40, xb - 40, ((i * .29 + Math.floor(ph * 9) * .37) % 1)), yy = y0 - lw * 1.05; c.beginPath(); c.moveTo(x - 14, yy - 34); c.lineTo(x + 8, yy - 14); c.lineTo(x - 8, yy - 4); c.lineTo(x + 14, yy + 18); c.stroke(); }
    c.globalAlpha = 1;
  }
  // the two ends
  if (hose) {
    c.fillStyle = '#9aa6c8'; c.strokeStyle = PLUM; c.lineWidth = 9; c.beginPath(); c.roundRect(w * .07, y0 - lw * 1.5, w * .1, lw * 2.4, 10); c.fill(); c.stroke();
    c.beginPath(); c.roundRect(w * .045, y0 - lw * 2.05, w * .15, lw * .5, 8); c.fillStyle = '#e2463f'; c.fill(); c.stroke();
    c.fillStyle = '#e8b23e'; c.beginPath(); c.roundRect(xb - 6, y0 - lw * .72, w * .07, lw * 1.44, 6); c.fill(); c.stroke();
    if (open) for (let i = 0; i < 3; i++) { const u = (ph * 1.6 + i / 3) % 1; c.fillStyle = '#3fb6ff'; c.globalAlpha = 1 - u; c.beginPath(); c.arc(xb + w * .08 + u * w * .06, y0 + u * u * h * .2, lw * .2, 0, 6.29); c.fill(); c.stroke(); c.globalAlpha = 1; }
  } else {
    const sh = chaos > 0 ? Math.sin(ph * 40) * 5 * chaos : 0;
    drawBrainAt(c, w * .115 + sh, y0 - lw * .1, w * .075);
    c.save(); c.translate(xb - w * .01, y0 - h * .19); const sw = w * .17, s2 = h * .34; c.lineWidth = 8; c.strokeStyle = PLUM; c.fillStyle = CREAM; sockPath(c, sw, s2); c.fill();
    c.save(); sockPath(c, sw, s2); c.clip(); c.fillStyle = '#e2463f'; c.fillRect(0, s2 * .1, sw, s2 * .11); c.fillRect(sw * .76, s2 * .5, sw * .3, s2 * .5); c.restore(); sockPath(c, sw, s2); c.stroke(); c.restore();
  }
  // the weight: someone sitting on it (nerve) or a boot standing on it (hose)
  const wy = lerpN(h * .1, y0 - lw / 2 + lw * .7 * p, Math.min(1, p * 1.25 + .0)), up = 1 - p;
  if (hose) {
    const bx = xm - w * .1, by = wy - h * .3 - up * h * .06; c.fillStyle = '#5b4a8a'; c.strokeStyle = PLUM; c.lineWidth = 10;
    c.beginPath(); c.moveTo(bx, by); c.lineTo(bx + w * .1, by); c.lineTo(bx + w * .11, by + h * .17); c.quadraticCurveTo(bx + w * .25, by + h * .19, bx + w * .25, by + h * .3); c.lineTo(bx - w * .01, by + h * .3); c.closePath(); c.fill(); c.stroke();
    c.fillStyle = PLUM; c.beginPath(); c.roundRect(bx - w * .02, by + h * .28, w * .28, h * .045, 8); c.fill();
  } else {
    const bw = w * .3, bh = h * .34, by = wy - bh - up * h * .08; c.fillStyle = '#e8553a'; c.strokeStyle = PLUM; c.lineWidth = 10;
    c.beginPath(); c.moveTo(xm - bw * .34, by); c.lineTo(xm + bw * .34, by); c.bezierCurveTo(xm + bw * .62, by + bh * .4, xm + bw * .62, by + bh, xm, by + bh); c.bezierCurveTo(xm - bw * .62, by + bh, xm - bw * .62, by + bh * .4, xm - bw * .34, by); c.closePath(); c.fill(); c.stroke();
    c.strokeStyle = '#b53a26'; c.lineWidth = 7; c.beginPath(); c.moveTo(xm - bw * .2, by + 4); c.lineTo(xm, by + bh * .3); c.lineTo(xm + bw * .2, by + 4); c.stroke();
  }
  if (p > .75) { c.strokeStyle = '#e2463f'; c.lineWidth = 10; for (const s of [-1, 1]) for (const a of [.35, .8]) { c.beginPath(); c.moveTo(xm + s * w * .2, y0 - lw * a * 1.2 + lw * .4); c.lineTo(xm + s * w * .25, y0 - lw * a * 2.2 + lw * .6); c.stroke(); } }
}

// ---------------------------------------------------------------- OTURMA ODASI
const SEAT = { x: -.2, z: -1.05 }, DEDE = { x: -1.15, z: -1.05 }, SOF = V(-.68, 0, -.42);
const P0 = { x: .25, z: -.45 }, P1 = { x: .5, z: -.05 }, P2 = { x: .78, z: .3 }, M = { x: .55, z: .2 };
const WIN = V(-1.55, 2.25, -2.36), TEA = V(1.55, 0, -1.55);
function buildOda(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 9), painted(woodTex({ base: '#c9935f', rep: [5, 4] })));
  fl.rotation.x = -Math.PI / 2; g.add(fl);
  const rug = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 3.4), painted(carpetTex({ base: '#b8323a', band: '#e0b050', rep: [1, 1], rows: 2 }))); rug.rotation.x = -Math.PI / 2; rug.position.set(0, .006, -.2); g.add(rug);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 5), painted(stoneTex({ base: '#b9c4f2', seam: '#98a4dc', bw: 64, bh: 64, rep: [12, 5] })));
  wall.position.set(0, 2.5, -2.4); g.add(wall);
  const dado = new THREE.Mesh(new THREE.BoxGeometry(12, .42, .05), painted(tileTex({ a: '#3f9a8a', b: '#f2ead8', rep: [28, 1] }))); dado.position.set(0, 1.3, -2.36); g.add(dado);
  for (const y of [1.07, 1.53]) { const m = new THREE.Mesh(new THREE.BoxGeometry(12, .05, .08), flat('#eef3fb')); m.position.set(0, y, -2.35); g.add(m); }
  // the window: the light of the set
  const pane = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.2), new THREE.MeshBasicMaterial({ color: HDR(1.75, 1.5, 1.05) })); pane.position.copy(WIN); g.add(pane);
  const fr = flat('#f1ece2');
  for (const [w, h, x, y] of [[1.18, .09, 0, .64], [1.18, .12, 0, -.65], [.09, 1.36, -.55, 0], [.09, 1.36, .55, 0], [.05, 1.2, 0, 0], [1.0, .05, 0, .1]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .1), fr); b.position.set(WIN.x + x, WIN.y + y, WIN.z + .06); b.userData.noShadow = true; g.add(b); }
  for (const s of [-1, 1]) { const cu = new THREE.Mesh(new THREE.BoxGeometry(.3, 1.6, .06), flat('#e8553a')); cu.position.set(WIN.x + s * .74, WIN.y - .05, WIN.z + .1); g.add(cu); }
  // the sedir along the wall, with cushions
  const sd = new THREE.Mesh(new THREE.BoxGeometry(3.2, .42, .8), flat('#3f6fb8')); sd.position.set(1.3, .21, -1.98); g.add(sd);
  const sb = new THREE.Mesh(new THREE.BoxGeometry(3.2, .5, .2), flat('#345a9c')); sb.position.set(1.3, .66, -2.26); g.add(sb);
  for (const [x, col] of [[.2, '#f0c455'], [1.0, '#e8553a'], [1.8, '#f2ead8'], [2.5, '#3f9a8a']]) { const cs = new THREE.Mesh(new THREE.BoxGeometry(.52, .44, .16), flat(col)); cs.position.set(x, .68, -2.1); cs.rotation.x = -.22; g.add(cs); }
  // the little table with the teapot he never reaches
  const tt = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .04, 28), painted(woodTex({ base: '#c08a52' }))); tt.position.set(TEA.x, .5, TEA.z); g.add(tt);
  const tl = new THREE.Mesh(new THREE.CylinderGeometry(.05, .16, .5, 12), painted(woodTex({ base: '#8a5a34' }))); tl.position.set(TEA.x, .25, TEA.z); g.add(tl);
  const kb = new THREE.Mesh(new THREE.SphereGeometry(.15, 20, 14), flat('#d8dcec')); kb.scale.y = .82; kb.position.set(TEA.x, .64, TEA.z); g.add(kb);
  const kt = new THREE.Mesh(new THREE.SphereGeometry(.1, 16, 12), flat('#f2ead8')); kt.scale.y = .85; kt.position.set(TEA.x, .82, TEA.z); g.add(kt);
  const sp = new THREE.Mesh(new THREE.CylinderGeometry(.02, .035, .2, 8), flat('#d8dcec')); sp.rotation.z = -1.0; sp.position.set(TEA.x + .19, .68, TEA.z); g.add(sp);
  const kn = new THREE.Mesh(new THREE.SphereGeometry(.025, 8, 6), flat('#2a2f52')); kn.position.set(TEA.x, .92, TEA.z); g.add(kn);
  // the floor table: cloth, low round table, tray, bread, olives, two glasses of tea
  const cloth = new THREE.Mesh(new THREE.CircleGeometry(.98, 40), painted(tileTex({ a: '#f2ead8', b: '#f0c455', rep: [9, 9] }))); cloth.rotation.x = -Math.PI / 2; cloth.position.set(SOF.x, .012, SOF.z); g.add(cloth);
  const tbl = new THREE.Mesh(new THREE.CylinderGeometry(.56, .56, .05, 40), painted(woodTex({ base: '#c08a52' }))); tbl.position.set(SOF.x, .3, SOF.z); g.add(tbl);
  const leg = new THREE.Mesh(new THREE.CylinderGeometry(.3, .36, .28, 24), painted(woodTex({ base: '#8a5a34' }))); leg.position.set(SOF.x, .14, SOF.z); g.add(leg);
  const tray = new THREE.Mesh(new THREE.CylinderGeometry(.46, .46, .025, 36), flat('#d8dcec')); tray.position.set(SOF.x, .338, SOF.z); g.add(tray);
  for (const [dx, dz, r, col] of [[-.2, .1, .11, '#f6efe0'], [.2, .12, .1, '#f6efe0'], [0, -.2, .12, '#f6efe0']]) { const pl = new THREE.Mesh(new THREE.CylinderGeometry(r, r * .8, .025, 20), flat(col)); pl.position.set(SOF.x + dx, .363, SOF.z + dz); g.add(pl); }
  for (let i = 0; i < 5; i++) { const o = new THREE.Mesh(new THREE.SphereGeometry(.02, 8, 6), flat(i % 2 ? '#3a4a2a' : '#2a2a3a')); o.position.set(SOF.x - .2 + Math.cos(i * 1.3) * .05, .39, SOF.z + .1 + Math.sin(i * 1.3) * .05); o.userData.noShadow = true; g.add(o); }
  const bread = new THREE.Mesh(new THREE.SphereGeometry(.1, 16, 10), flat('#e0a858')); bread.scale.set(1.3, .45, .9); bread.position.set(SOF.x, .41, SOF.z - .2); g.add(bread);
  const ch = new THREE.Mesh(new THREE.BoxGeometry(.1, .05, .08), flat('#fbf7ee')); ch.position.set(SOF.x + .2, .4, SOF.z + .12); g.add(ch);
  for (const dx of [-.3, .34]) { const gl = new THREE.Mesh(new THREE.CylinderGeometry(.034, .024, .09, 14), flat('#c8402a')); gl.position.set(SOF.x + dx, .395, SOF.z - .08); g.add(gl);
    const sa = new THREE.Mesh(new THREE.CylinderGeometry(.055, .055, .012, 16), flat('#f6efe0')); sa.position.set(SOF.x + dx, .352, SOF.z - .08); sa.userData.noShadow = true; g.add(sa); }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#b9c6ff', '#8a7a9a', 1.5));
  const KEYP = V(-2.4, 3.0, -.9); dyn.keyP = KEYP;
  const key = new THREE.SpotLight('#ffd9a0', 13, 13, 1.0, .6, 1.3); key.position.copy(KEYP); key.target.position.set(.1, .5, -.4);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .7); fill.position.set(2, 3, 6); fill.target.position.set(0, 1, -1); L.add(fill); L.add(fill.target);
  scene.add(L);
  shadows(g);
  beam(scene, [WIN.x, WIN.y, WIN.z + .1], [-.4, .3, .3], { r0: .5, r1: 1.6, color: '#ffe2a8', strength: .1 });
  glow(scene, [WIN.x, WIN.y, WIN.z + .15], '#ffd28a', 1.9, .2);
}

// ---------------------------------------------------------------- CAST
const HERO = { hair: '#3a2a24', cloth: '#e8553a', collar: true };
export const LOOK = {
  kahraman: { ...HERO, height: 1.7 },
  kahramanS: { ...HERO, body: 'sit', height: 1.2 },
  dede: { mustache: '#f1eef6', hair: '#dcdce8', hat: 'kulah', hatColor: '#6a4a9a', body: 'sit', cloth: '#3f8f7a', buttons: '#f0c455', sash: '#e0aa3e', headW: 286, headH: 258, height: 1.26 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hook: { pos: [-.38, 1.0, 3.3], look: [-.38, .85, -1], fov: 46 },
  hookFace: { pos: [-.12, 1.08, .9], look: [-.2, 1.04, -1.05], fov: 40 },
  hookFoot: { pos: [.3, .62, 1.15], look: [.28, .4, -.8], fov: 40 },
  wide: { pos: [-.4, 1.6, 4.6], look: [-.4, 1.05, -1], fov: 50 },
  wideIn: { pos: [-.3, 1.1, 3.0], look: [-.25, .85, -1], fov: 46 },
  walkA: { pos: [-.2, 1.35, 5.0], look: [-.22, .95, -.6], fov: 50 },
  dede: { pos: [-.95, 1.05, 1.5], look: [-1.15, 1.0, -1.05], fov: 42 },
  walkB: { pos: [-.12, 1.3, 5.0], look: [-.14, .9, -.4], fov: 50 },
  walkC: { pos: [-.36, 1.15, 5.2], look: [-.38, .62, -.3], fov: 50 },
  mech: { pos: [.55, 1.3, 4.0], look: [.55, 1.2, .2], fov: 46 },
  brain: { pos: [.55, 1.25, 2.9], look: [.55, 1.22, .2], fov: 44 },
  up: { pos: [-.15, 1.4, 5.0], look: [-.18, 1.0, -.3], fov: 50 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: on his foot at the floor table -> his face -> the foot
    { t: 0, ...SHOT.hook, creep: .4, drift: .03 },
    { t: t('neden') + .1, dur: .2, move: 'whip', ...SHOT.hookFace, creep: .34, drift: .02 },
    { t: t('uyuşur') + .14, dur: .2, move: 'whip', ...SHOT.hookFoot, creep: .34, drift: .02 },
    { t: t('Bakın') + .16, dur: .3, move: 'whip', ...SHOT.wide, creep: .22, drift: .03 },
    { t: t('ayağının') + .1, dur: .7, ...SHOT.wideIn, creep: .2, drift: .02 },
    // three tries, each one worse
    { t: t('Çay') + .12, dur: .3, move: 'whip', ...SHOT.walkA, creep: .2, drift: .02 },
    { t: t('Deden') + .1, dur: .28, move: 'whip', ...SHOT.dede, creep: .3, drift: .02 },
    { t: t('adım') - .05, dur: .3, move: 'whip', ...SHOT.walkB, creep: .2, drift: .02 },
    { t: t('daha') + .1, dur: .6, ...SHOT.walkC, creep: .1, drift: .006 },
    // the turn: grandpa falls silent, the nerve and the hose
    { t: t('Çünkü') + .12, dur: .28, move: 'whip', ...SHOT.dede, creep: .34, drift: .02 },
    { t: t('üstüne') - .02, dur: .3, move: 'whip', ...SHOT.mech, creep: .025, drift: .004 },
    { t: t('Beynin') + .1, dur: .5, ...SHOT.brain, creep: .08, drift: .008 },
    // the loop: up again, and back on the very same foot (the first frame)
    { t: t('Geçince') + .1, dur: .28, move: 'whip', ...SHOT.up, creep: .2, drift: .02 },
    { t: t('yine') + .08, dur: .26, move: 'whip', ...SHOT.hook, creep: .1, drift: 0 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('yok') + .05, .4); cp.kick(t('iğne') + .02, .45); cp.kick(t('ortasına') + .12, .9); cp.kick(t('sıkıştı') + .05, .5); cp.kick(t('karmakarışık') + .05, .45); cp.kick(t('oturuyorsun', 2) + .1, .5);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .45) * FPS) / FPS;      // no dead frames after the last word (loop)
  const { scene } = ctx;
  scene.background = new THREE.Color('#33407a');
  buildOda(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.sockZ = card(scene, .46, .5, drawSock('z'), { pw: 384 });
  dyn.sock = card(scene, .4, .44, drawSock(''), { pw: 320 });
  dyn.ghost = card(scene, .4, .44, drawSock('ghost'), { pw: 320 });
  dyn.q = [0, 1].map(() => card(scene, .3, .36, drawMark('?', '#ffe15a'), { pw: 256 }));
  dyn.bang = card(scene, .3, .4, drawMark('!', '#ff5a4a'), { pw: 256 });
  dyn.needles = [0, 1, 2, 3].map(() => card(scene, .42, .42, drawNeedles, { pw: 320 }));
  dyn.stars = card(scene, .7, .4, drawStars, { pw: 384 });
  dyn.clock = dynCard(scene, .5, .5, drawClock, { pw: 320, steps: 24 });
  dyn.brain = card(scene, .62, .56, drawBrain, { pw: 448 });
  dyn.pinch = dynCard(scene, 1.4, .95, drawPinch, { pw: 768, steps: 30 });
  PF = new Parcaciklar(scene);
  PF.ekle('toz', { t: W('ortasına') + .12, pos: [P2.x - .8, 0, P2.z + .1], olcek: 1.3 });
  PF.ekle('kivilcim', { t: W('iğne', 2) + .05, pos: [M.x + .2, 1.72, M.z + .1] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('neden') + .02, 'rise', { dur: .3 }); cue(W('uyuşur') + .05, 'rise', { dur: .3 });
  cue(W('Bakın') + .02, 'whoosh'); cue(W('bir'), 'lock'); cue(W('ayağının') + .05, 'shimmer');
  cue(W('Çay') + .02, 'whoosh'); cue(W('kalkıyorsun'), 'rise', { dur: .35 }); cue(W('yok') + .05, 'cut');
  cue(W('Deden') + .02, 'rise', { dur: .3 }); cue(W('uyuşmuş') + .05, 'lock');
  cue(W('adım') - .1, 'whoosh'); cue(W('atıyorsun'), 'lock'); cue(W('binlerce'), 'lock'); cue(W('iğne') + .02, 'boom'); cue(W('batıyor'), 'lock');
  cue(W('daha'), 'lock'); cue(W('bacağın'), 'wind', { dur: W('halının') - W('bacağın') }); cue(W('halının') + .1, 'rise', { dur: .4 }); cue(W('ortasına') + .12, 'boom'); cue(W('yığılıyorsun') + .1, 'shimmer');
  cue(W('Çünkü') + .05, 'cut'); cue(W('değil') + .05, 'lock');
  cue(W('üstüne') - .1, 'whoosh'); cue(W('oturunca'), 'rise', { dur: .4 }); cue(W('sıkıştı') + .05, 'boom');
  cue(W('Tıpkı') + .05, 'rise', { dur: .3 }); cue(W('basılan') + .1, 'lock'); cue(W('geçemiyor') + .1, 'cut');
  cue(W('Kalkınca') + .05, 'rise', { dur: .35 }); cue(W('çalışmaya'), 'lock'); cue(W('karmakarışık'), 'simmer', { dur: W('yolluyor') + .5 - W('karmakarışık') }); cue(W('karmakarışık') + .05, 'boom');
  cue(W('Beynin') + .05, 'lock'); cue(W('iğne', 2) + .05, 'shimmer'); cue(W('sanıyor') + .1, 'lock');
  cue(W('Geçince') + .02, 'whoosh'); cue(W('yine') - .05, 'whoosh'); cue(W('oturuyorsun', 2) + .1, 'boom'); cue(W('oturuyorsun', 2) + .25, 'shimmer');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'AYAĞIN NEDEN UYUŞUR?'); }

// ---------------------------------------------------------------- PER FRAME
const COOL = '#d6d6f6', WARM = '#ffcf8a';
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos); m.material.opacity = 1;
  if (wob) m.rotation.z = Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04;
  return s;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  PF.guncelle(t);
  for (const c of Object.values(cast)) c.hide();
  for (const m of dyn.cards) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const grade = [1.01, 1.0, 1.01], face = [1, .985, .97], tint = face.map((v, i) => v / grade[i]);
  const H = cast.kahraman, HS = cast.kahramanS, D = cast.dede;
  const lit = { lit: -1, shade: COOL, rim: { color: WARM, a: .4 } };
  const hop = (t0, d = .26) => { const k = (t - t0) / d; return k > 0 && k < 1 ? Math.sin(Math.PI * k) : 0; };
  // ---- the beats
  const tRise = A('kalkıyorsun'), tS1 = A('atıyorsun'), tS2 = A('daha'), tWob = A('bacağın'), tFall = A('halının') + .12, tHit = W('ortasına') + .12;
  const tBreak = A('Çünkü'), tMech = tBreak + .16, tUp = A('Geçince') + .02, tBack = W('yine') - .05, tSit = A('oturuyorsun', 2);
  const hookEnd = A('Bakın');
  const seated1 = t < tRise, standing = t >= tRise && t < tMech, mech = t >= tMech && t < tUp, up = t >= tUp && t < tBack, seated2 = t >= tBack;
  let focus = V(SEAT.x, 1.0, SEAT.z);
  // ---- the hero, seated at the floor table (first and last frames are the same picture)
  if (seated1 || seated2) {
    let hp = { expr: 'neutral', look: 0, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(1, A('neden'), A('saattir'), A('ayağının'), A('oturuyorsun', 2)) };
    const worry = { ...hp, expr: 'worried', look: .5, lookY: -.45, gazeX: 1, gazeY: -1, brow: .7, sweat: .9, armL: [20, 14], armR: [40, -64] };
    if (t < hookEnd) hp = t > A('neden') && t < A('uyuşur') ? { ...worry, look: .1, lookY: -.1, gazeX: 0, gazeY: 0, mouth: .3 } : worry;
    else if (seated1) hp = t < A('ayağının') ? { ...hp, expr: 'smile', look: -.4, lid: .2, brow: .2, armL: [34, -96], armR: [30, -92] } : { ...worry, sweat: ramp(t, A('ayağının'), A('ayağının') + .4) };
    else hp = t < tSit + .12 ? { ...hp, expr: 'grin', look: -.3, brow: .5, armL: [34, -96], armR: [30, -92] } : worry;
    const plop = seated2 ? -Math.abs(Math.sin((t - tSit) * 14)) * 10 * Math.exp(-Math.max(0, t - tSit) * 6) * (t > tSit ? 1 : 0) : 0;
    HS.show(); HS.place(SEAT.x, 0, SEAT.z, cam, tint); HS.draw({ ...hp, bob: plop, ...lit }); HS.castFrom(dyn.keyP);
    // the foot he sits on: asleep
    const FOOT = V(SEAT.x + .48, .34, SEAT.z + .28);
    if (t < hookEnd) { popCard(dyn.sockZ, -1, t, FOOT, 1 + .05 * Math.sin(t * 9)); dyn.sockZ.rotation.z = Math.sin(t * 26) * .05; }
    else if (seated1 && t > A('ayağının')) popCard(dyn.sockZ, A('ayağının'), t, FOOT);
    else if (seated2 && t > tSit + .1) { popCard(dyn.sockZ, tSit + .1, t, FOOT); }
    // "for an hour": the clock races
    if (seated1 && t > A('bir') - .05 && t < tRise) { dyn.clock.userData.set(ramp(t, A('bir'), A('üstünde')) * 1); const s = popCard(dyn.clock, A('bir') - .05, t, V(-.68, 1.72, -1.2), 1.1, false); if (s) dyn.clock.rotation.z += Math.sin(t * 2.4) * .04; }
    focus = t > W('uyuşur') + .04 && t < hookEnd ? FOOT : V(SEAT.x, 1.0, SEAT.z);
  }
  // ---- the hero on his feet: no foot, pins, rubber leg, down he goes
  if (standing || up) {
    let hx, hz, hy = 0, sc = 1, rot = 0;
    if (up) { hx = M.x; hz = M.z; }
    else if (t < tS1) { const k = ramp(t, tRise, tRise + .3); hx = lerpN(SEAT.x, P0.x, k); hz = lerpN(SEAT.z, P0.z, k); sc = .78 + .22 * backOut((t - tRise) / .3); }
    else { const k1 = ramp(t, tS1, tS1 + .26), k2 = ramp(t, tS2, tS2 + .26); hx = lerpN(lerpN(P0.x, P1.x, k1), P2.x, k2); hz = lerpN(lerpN(P0.z, P1.z, k1), P2.z, k2); hy = (hop(tS1) + hop(tS2)) * .09; }
    if (!up && t >= tFall) { const fk = Math.min(1, (t - tFall) / (tHit - tFall)); rot = 88 * fk * fk; hy = .25 * fk; if (t >= tHit) rot = 88 - 8 * Math.exp(-(t - tHit) * 7) * Math.abs(Math.sin((t - tHit) * 16)); }
    const noFoot = t > A('ayağın', 2) && t < A('Deden'), pins = t >= tS1 + .2 && t < tS2, wob = t >= tWob && t < tFall, down = t >= tHit;
    let hp = { expr: 'smile', look: .6, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(3, A('ayağın', 2), A('yok'), A('binlerce'), A('bacağın'), A('yığılıyorsun')) };
    if (up) hp = { ...hp, expr: 'grin', look: -.2, brow: .6, armL: [150, 24], armR: [150, 24], bob: -Math.abs(Math.sin((t - tUp) * 10)) * 5 };
    else if (t < A('ayağın', 2)) hp = { ...hp, expr: 'smile', look: .7, armR: [96, 22] };
    else if (t < tS1) hp = { ...hp, expr: noFoot ? 'surprised' : 'worried', look: .3, lookY: -.55, gazeY: -1, brow: 1, mouth: .35, sweat: t > A('yok') ? 1 : 0, armL: [60, -70], armR: [60, -70], lean: Math.sin(t * 5) * 2 };
    else if (t < tS2) hp = { ...hp, expr: pins ? 'surprised' : 'worried', look: .3, lookY: -.4, gazeY: -1, brow: 1, mouth: pins ? .6 : .2, sweat: 1, armL: [150, 28 + 14 * Math.sin(t * 24)], armR: [150, 28 - 14 * Math.sin(t * 24)], bob: pins ? Math.sin(t * 34) * 5 : 0, lean: pins ? Math.sin(t * 17) * 4 : 0 };
    else if (!down) { const g2 = ramp(t, tWob, tWob + .5); hp = { ...hp, expr: 'worried', look: .2, lookY: -.3, brow: .9, mouth: .5, sweat: 1, armL: [130 + 30 * Math.sin(t * 15), 30], armR: [130 - 30 * Math.sin(t * 15), 30], lean: wob ? Math.sin((t - tWob) * 13) * 13 * g2 : 0, tilt: wob ? Math.sin((t - tWob) * 13 + 1) * 8 * g2 : 0, bob: wob ? Math.abs(Math.sin((t - tWob) * 13)) * 12 * g2 : 0 }; }
    else hp = { ...hp, expr: 'worried', look: 0, lookY: .2, brow: .4, mouth: .25, lid: .5, sweat: 1, armL: [150, 30], armR: [40, 10] };
    H.show(); H.place(hx, hy, hz, cam, tint, sc); H.mesh.rotation.z = rot * Math.PI / 180;
    H.draw({ ...hp, ...lit }); H.castFrom(dyn.keyP); if (rot > 1) { H.caster.rotation.copy(H.mesh.rotation); H.shadow.visible = false; }
    const foot = V(hx + .12, .1, hz + .05);
    // beat 1: the foot is "not there"
    if (noFoot) { popCard(dyn.ghost, A('ayağın', 2), t, foot.clone().add(V(.06, .16, .05)), 1.25, false); dyn.ghost.material.opacity = .75 + .25 * Math.sin(t * 16); if (t > A('yok')) popCard(dyn.q[0], A('yok'), t, foot.clone().add(V(.34, .5, .05))); }
    // beat 2: a thousand pins
    if (pins) {
      [['binlerce', .26, .1], ['iğne', -.2, .22], ['batıyor', .16, .46], ['batıyor', -.14, .6]].forEach(([w, dx, dy], i) => { const s = popCard(dyn.needles[i], A(w) + (i === 3 ? .12 : 0), t, foot.clone().add(V(dx * 1.3, dy * 1.2, .06 + i * .01)), 1.15 + .15 * Math.sin(t * 30 + i * 2)); if (s) dyn.needles[i].rotation.z = t * (i % 2 ? 3 : -3) + i; });
      if (t > A('iğne')) popCard(dyn.bang, A('iğne'), t, V(hx + .1, 1.5 + .62, hz));
    }
    // beat 3: flat on the carpet, stars round his head
    if (down && !up) { const s = popCard(dyn.stars, tHit + .1, t, V(hx - 1.22, .74, hz + .05), .8, false); if (s) { dyn.stars.rotation.z = Math.sin(t * 6) * .25; dyn.stars.position.x += Math.sin(t * 5) * .06; } }
    focus = V(hx - (down && !up ? .7 : 0), down && !up ? .4 : 1.2, hz);
  }
  // ---- the turn: he sits up on the carpet under the diagram
  if (mech) {
    const inBrain = t > A('Beynin'), aha = t > A('sanıyor');
    let hp = { expr: 'neutral', look: 0, lookY: .55, gazeY: 1, brow: .7, lid: 0, armL: [34, -96], armR: [30, -92], blink: bl(4, A('oturunca'), A('sıkıştı'), A('Tıpkı'), A('geçemiyor'), A('Kalkınca'), A('karmakarışık'), A('Beynin'), A('sanıyor')) };
    if (t > A('sıkıştı') && t < A('Tıpkı')) hp = { ...hp, expr: 'surprised', brow: 1, mouth: .4 };
    if (t > A('geçemiyor') && t < A('Kalkınca')) hp = { ...hp, expr: 'worried', brow: .7 };
    if (t > A('karmakarışık') && !inBrain) hp = { ...hp, expr: 'surprised', brow: 1, mouth: .5, bob: Math.sin(t * 34) * 3 };
    if (inBrain) hp = aha ? { ...hp, expr: 'grin', lookY: .1, gazeY: 0, brow: .8, armR: [148, -128] } : { ...hp, expr: 'surprised', lookY: .5, brow: 1, mouth: .4, armL: [150, 24], armR: [150, 24], bob: t > A('iğne', 2) ? Math.sin(t * 34) * 3 : 0 };
    HS.show(); HS.place(M.x, 0, M.z, cam, tint); HS.draw({ ...hp, ...lit }); HS.castFrom(dyn.keyP);
    if (!inBrain && t > W('üstüne') - .1) {
      const hose = t > A('Tıpkı') + .1 && t < A('Kalkınca');
      let p, chaos = 0;
      if (t < A('Tıpkı') + .1) p = ramp(t, A('oturunca'), A('oturunca') + .4);
      else if (hose) p = ramp(t, A('basılan'), A('basılan') + .3);
      else { p = 1 - ramp(t, A('Kalkınca') + .05, A('Kalkınca') + .4); chaos = ramp(t, A('karmakarışık') - .05, A('karmakarışık') + .25); }
      dyn.pinch.userData.set(hose ? 1 : 0, p, t, chaos);
      const t0 = hose ? A('Tıpkı') + .1 : t < A('Kalkınca') ? W('üstüne') - .1 : A('Kalkınca');
      const s = popCard(dyn.pinch, t0, t, V(M.x, 1.86, M.z), 1, false); if (s) dyn.pinch.rotation.z += Math.sin(t * 1.7) * .012 + (chaos > 0 ? Math.sin(t * 40) * .008 : 0);
    }
    if (inBrain) {
      const s = popCard(dyn.brain, A('Beynin'), t, V(M.x - .12, 1.66, M.z), 1 + (t > A('karmaşayı') ? .04 * Math.sin(t * 30) : 0)); if (s && t > A('karmaşayı')) dyn.brain.rotation.z += Math.sin(t * 34) * .04;
      if (t > A('karmaşayı') && t < A('iğne', 2)) popCard(dyn.q[0], A('karmaşayı'), t, V(M.x + .3, 1.82, M.z));
      if (t > A('iğne', 2)) { const n = popCard(dyn.needles[0], A('iğne', 2), t, V(M.x + .32, 1.74, M.z + .02), .9); if (n) dyn.needles[0].rotation.z = Math.sin(t * 3) * .3; }
    }
    focus = V(M.x, 1.2, M.z);
  }
  // ---- grandpa: each time he laughs harder; at the turn he falls silent
  {
    let dp = { expr: 'smug', look: .6, lid: .3, armL: [16, 10], armR: [16, 10], blink: bl(2, A('neden'), A('saattir'), A('yok'), A('Deden'), A('binlerce'), A('bacağın'), A('Çünkü'), A('değil'), A('yine'), A('oturuyorsun', 2)) };
    const lf = (amp, sp = 12) => ({ expr: 'laugh', laughMarks: Math.min(1, amp), mouth: .5 + .5 * Math.abs(Math.sin(t * sp)), bob: -Math.abs(Math.sin(t * sp)) * 9 * amp });
    if (t >= hookEnd && seated1) dp = { ...dp, expr: 'smile', look: .5, lid: .1, armR: [34, -92] };
    if (t >= tRise && t < A('Deden')) dp = { ...dp, expr: t > A('yok') ? 'grin' : 'smile', look: .75, lid: 0, brow: .4 };
    if (t >= A('Deden') && t < tS1 - .2) { const talk = t > A('ayağın', 3) - .04 && t < A('uyuşmuş') + .5; dp = { ...dp, ...lf(.5), look: .7, armR: [100, 22 + 8 * Math.sin(t * 12)], ...(talk ? { expr: 'grin', mouth: flap(env, t), bob: 0 } : {}) }; }
    if (t >= tS1 - .2 && t < tS2) dp = { ...dp, ...lf(.8, 13), look: .75, armL: [30, -100], armR: [100, 24] };
    if (t >= tS2 && t < tBreak + .2) dp = { ...dp, ...lf(1.4, 15), look: .7, tilt: Math.sin(t * 7) * 6, armL: [150, 26 + 16 * Math.sin(t * 15)], armR: [150, 26 - 16 * Math.sin(t * 15)] };
    if (t >= tBreak + .2 && t < tUp) dp = t < A('değil') ? { ...dp, expr: 'surprised', look: .5, brow: 1, mouth: .3, lid: 0 } : { ...dp, expr: 'worried', look: .2, lookY: -.55, gazeY: -1, brow: .8, sweat: 1, lid: 0, armL: [40, -64], armR: [40, -64] };
    if (up) dp = { ...dp, expr: 'smile', look: .7, lid: .1 };
    if (seated2) dp = t < tSit + .12 ? { ...dp, expr: 'surprised', look: .6, brow: 1, mouth: .3, lid: 0 } : dp;
    D.show(); D.place(DEDE.x, 0, DEDE.z, cam, tint); D.draw({ ...dp, ...lit }); D.castFrom(dyn.keyP);
    if (t > A('değil') && t < A('üstüne') + .1) popCard(dyn.q[1], A('değil'), t, V(DEDE.x + .3, 1.42, DEDE.z + .02));
    if ((t >= A('Deden') && t < tS1 - .2) || (t >= tBreak && t < tMech + .3)) focus = V(DEDE.x, 1.05, DEDE.z);
  }
  const look = { focus: cam.position.distanceTo(focus), coc: 5, range: 2.6, sat: 1.24, lift: [.085, .085, .15], bloom: .85, vignette: .22 };
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
