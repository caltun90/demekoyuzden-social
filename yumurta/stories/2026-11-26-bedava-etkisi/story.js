// Bedava olunca neden hemen kapıyorsun? Demek O Yüzden günlük Short (yumurta stili), 26 Kasım 2026.
// Bilgi: iki çikolata da paralıyken çoğunluk kaliteli olanı seçti; iki fiyat da aynı miktarda inip ucuz olan bedava olunca
// çoğunluk bedava olana döndü (Shampanier, Mazar ve Ariely, 2007, sıfır fiyat etkisi). Kaynaklar SCRIPT.md'de.
// Setler: MARKET (x≈0) raflar, sarkıt lamba, "BEDAVA" tabelalı stant, satıcı; DENEY (x≈200) masa, iki çikolata, fiyat
// etiketleri, araştırmacı ve gönüllü.
import * as THREE from 'three';
import { stoneTex, woodTex, tileTex, painted, flat } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { beam, glow } from '/engine/src/fx.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-26-bedava-etkisi';
export const FPS = 30;
export let DUR = 47;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lerpN = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;
let W, cast = {}, sets = {}, dyn = {}, smokes = {};

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
function card(scene, w, h, draw, { pw = 512, layer = 1 } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); draw(c.getContext('2d'), c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false }));
  m.layers.set(layer); m.renderOrder = 20; m.visible = false; scene.add(m); return m;
}
function dynCard(scene, w, h, draw, { pw = 512, steps = 30 } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); const g = c.getContext('2d');
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false }));
  m.layers.set(1); m.renderOrder = 20; m.visible = false; scene.add(m);
  let key = null;
  m.userData.set = (...v) => { const q = v.map(x => Math.round(x * steps) / steps), k = q.join(','); if (k === key) return; key = k; g.clearRect(0, 0, c.width, c.height); draw(g, c.width, c.height, ...q); t.needsUpdate = true; };
  return m;
}

// ---------------------------------------------------------------- drawings
const FONT = '"Arial Black", "Inter", sans-serif';
function star(c, cx, cy, R, r, n = 12) { c.beginPath(); for (let k = 0; k < n * 2; k++) { const a = k / (n * 2) * 6.283 - 1.57, q = k % 2 ? r : R; c.lineTo(cx + Math.cos(a) * q, cy + Math.sin(a) * q); } c.closePath(); }
// a starburst with a text: the price that shouts
const burst = (text, bg, fg, k = .34) => (c, w, h) => {
  c.lineJoin = 'round'; c.fillStyle = bg; c.strokeStyle = PLUM; c.lineWidth = w * .035; star(c, w / 2, h / 2, w * .47, w * .38); c.fill(); c.stroke();
  c.fillStyle = fg; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${w * k}px ${FONT}`; c.fillText(text, w / 2, h * .53);
};
// the sign over the stand
function drawSign(c, w, h) {
  c.lineJoin = 'round'; c.fillStyle = '#e2463f'; c.strokeStyle = PLUM; c.lineWidth = 16; c.beginPath(); c.roundRect(12, 12, w - 24, h - 24, 30); c.fill(); c.stroke();
  c.strokeStyle = '#ffe9a8'; c.lineWidth = 6; c.beginPath(); c.roundRect(34, 34, w - 68, h - 68, 18); c.stroke();
  c.fillStyle = '#fff6d8'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .5}px ${FONT}`; c.fillText('BEDAVA', w / 2, h * .54);
}
// a key ring with a little heart tag
function drawKey(c, w, h) {
  c.lineJoin = c.lineCap = 'round';
  for (const [col, lw] of [[PLUM, w * .13], ['#c9d2e8', w * .06]]) { c.strokeStyle = col; c.lineWidth = lw; c.beginPath(); c.arc(w * .5, h * .22, w * .2, 0, 6.29); c.stroke(); c.beginPath(); c.moveTo(w * .5, h * .38); c.lineTo(w * .5, h * .5); c.stroke(); }
  const heart = () => { c.beginPath(); c.moveTo(w * .5, h * .95); c.bezierCurveTo(w * .02, h * .7, w * .16, h * .42, w * .5, h * .58); c.bezierCurveTo(w * .84, h * .42, w * .98, h * .7, w * .5, h * .95); c.closePath(); };
  c.fillStyle = '#ff5a7a'; c.strokeStyle = PLUM; c.lineWidth = w * .06; heart(); c.fill(); c.stroke();
  c.fillStyle = 'rgba(255,255,255,.7)'; c.beginPath(); c.ellipse(w * .36, h * .66, w * .06, w * .04, -.6, 0, 6.29); c.fill();
}
// the drawer at home: already full of them
function drawDrawer(c, w, h) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = 14;
  c.fillStyle = '#fbf7ee'; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 40); c.fill(); c.stroke();
  c.fillStyle = '#8a5a3a'; c.beginPath(); c.roundRect(w * .1, h * .5, w * .8, h * .38, 14); c.fill(); c.stroke();
  c.fillStyle = '#f0c455'; c.beginPath(); c.roundRect(w * .42, h * .66, w * .16, h * .07, 8); c.fill(); c.stroke();
  c.fillStyle = '#5a3a28'; c.beginPath(); c.moveTo(w * .14, h * .5); c.lineTo(w * .2, h * .3); c.lineTo(w * .8, h * .3); c.lineTo(w * .86, h * .5); c.closePath(); c.fill(); c.stroke();
  const cols = ['#ff5a7a', '#58b848', '#3f86d6', '#f0c455', '#b06ad8'];
  for (let i = 0; i < 10; i++) {
    const x = w * (.2 + (i % 5) * .15), y = h * (i < 5 ? .2 : .34), r = w * .045;
    c.strokeStyle = PLUM; c.lineWidth = 12; c.beginPath(); c.arc(x, y - r * 1.6, r * .7, 0, 6.29); c.stroke(); c.strokeStyle = '#c9d2e8'; c.lineWidth = 5; c.stroke();
    c.strokeStyle = PLUM; c.lineWidth = 7; c.fillStyle = cols[(i * 3) % 5]; c.beginPath(); c.roundRect(x - r, y - r * .7, r * 2, r * 2.2, 8); c.fill(); c.stroke();
  }
}
// a price tag: n cents; n = 0 is free
function drawTag(c, w, h, n) {
  c.lineJoin = c.lineCap = 'round'; const free = n < .5;
  c.fillStyle = free ? '#ffe15a' : '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 14;
  c.beginPath(); c.moveTo(w * .22, 12); c.lineTo(w - 12, 12); c.lineTo(w - 12, h - 12); c.lineTo(w * .22, h - 12); c.lineTo(12, h / 2); c.closePath(); c.fill(); c.stroke();
  c.fillStyle = PLUM; c.beginPath(); c.arc(w * .17, h / 2, w * .035, 0, 6.29); c.fill();
  c.fillStyle = free ? '#c8323a' : PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .6}px ${FONT}`; c.fillText(String(Math.round(n)) + '¢', w * .6, h * .54);
}
// how many chose it: n little egg heads
function drawVotes(c, w, h, n) {
  c.lineJoin = c.lineCap = 'round'; n = Math.round(n);
  for (let i = 0; i < n; i++) {
    const x = w / 2 + (i - (n - 1) / 2) * w * .3, y = h * .52, r = w * .13;
    c.fillStyle = '#ffffff'; c.strokeStyle = PLUM; c.lineWidth = w * .028; c.beginPath(); c.ellipse(x, y, r * 1.05, r, 0, 0, 6.29); c.fill(); c.stroke();
    c.fillStyle = PLUM; for (const s of [-1, 1]) { c.beginPath(); c.arc(x + s * r * .32, y - r * .1, r * .13, 0, 6.29); c.fill(); }
    c.lineWidth = w * .018; c.beginPath(); c.arc(x, y + r * .2, r * .34, .3, 2.84); c.stroke();
  }
}
// the scale in the head: tilt -1..1
function drawScale(c, w, h, tilt) {
  c.lineJoin = c.lineCap = 'round';
  c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 44); c.fill(); c.stroke();
  const cx = w / 2, cy = h * .3, L = w * .3, a = tilt * .32, dx = Math.cos(a) * L, dy = Math.sin(a) * L;
  c.lineWidth = 16; c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx, h * .8); c.moveTo(cx - w * .14, h * .82); c.lineTo(cx + w * .14, h * .82); c.stroke();
  c.beginPath(); c.moveTo(cx - dx, cy - dy); c.lineTo(cx + dx, cy + dy); c.stroke();
  for (const [s, col, txt] of [[-1, '#f0c455', '₺'], [1, '#ff5a7a', '♥']]) {
    const px = cx + s * dx, py = cy + s * dy;
    c.lineWidth = 7; c.beginPath(); c.moveTo(px, py); c.lineTo(px - w * .09, py + h * .22); c.moveTo(px, py); c.lineTo(px + w * .09, py + h * .22); c.stroke();
    c.lineWidth = 12; c.fillStyle = '#c9d2e8'; c.beginPath(); c.moveTo(px - w * .12, py + h * .22); c.quadraticCurveTo(px, py + h * .36, px + w * .12, py + h * .22); c.closePath(); c.fill(); c.stroke();
    c.fillStyle = col; c.lineWidth = 8; c.beginPath(); c.arc(px, py + h * .15, w * .055, 0, 6.29); c.fill(); c.stroke();
    c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${w * .06}px ${FONT}`; c.fillText(txt, px, py + h * .155);
  }
  c.fillStyle = '#e2463f'; c.lineWidth = 10; c.beginPath(); c.arc(cx, cy, w * .035, 0, 6.29); c.fill(); c.stroke();
}
// the buffet plate: a pile n levels high
function drawPlate(c, w, h, n) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; n = Math.round(n);
  const cols = ['#f0c455', '#e2463f', '#58b848', '#c8843a', '#ff8ab8', '#f0c455', '#8a5a3a'];
  for (let i = 0; i < n; i++) {
    const y = h * .84 - i * h * .105, rw = w * (.34 - i * .035);
    c.fillStyle = cols[i % cols.length]; c.lineWidth = 10; c.beginPath(); c.ellipse(w / 2 + (i % 2 ? .03 : -.03) * w, y, rw, h * .07, (i % 2 ? .06 : -.06), 0, 6.29); c.fill(); c.stroke();
  }
  c.fillStyle = '#fbf7ee'; c.lineWidth = 13; c.beginPath(); c.moveTo(w * .04, h * .86); c.quadraticCurveTo(w / 2, h * 1.04, w * .96, h * .86); c.lineTo(w * .78, h * .95); c.lineTo(w * .22, h * .95); c.closePath(); c.fill(); c.stroke();
}
function drawMark(ch, col) {
  return (c, w, h) => { c.lineJoin = 'round'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .84}px ${FONT}`;
    c.strokeStyle = PLUM; c.lineWidth = 36; c.strokeText(ch, w / 2, h * .54); c.fillStyle = col; c.fillText(ch, w / 2, h * .54); };
}

// ---------------------------------------------------------------- MARKET (x = 0)
const HERO = { x: -.42, z: -.8 }, SAT = { x: .64, z: -1.0 }, STAND = V(.56, .98, -.3), BASKET = V(.18, .98, -.28), SIGN = V(.56, .47, .05), LAMPA = V(.1, 3.05, -.5);
function buildMarket(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(14, 10), painted(stoneTex({ base: '#d8def2', seam: '#a9b4d8', bw: 128, bh: 128, rep: [9, 6] }))); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 1); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(14, 6), flat('#9cc8dc')); wall.position.set(0, 3, -2.7); g.add(wall);
  const band = new THREE.Mesh(new THREE.BoxGeometry(14, .34, .05), painted(tileTex({ a: '#e2463f', b: '#f2ead8', rep: [36, 1] }))); band.position.set(0, 3.25, -2.66); g.add(band);
  // shelves full of boxes along the wall
  const cols = ['#e8b23e', '#e2463f', '#58b848', '#3f86d6', '#f2ead8', '#b06ad8', '#f09a32', '#2f8f9a'];
  for (const [y, k] of [[.55, 0], [1.25, 3], [1.95, 5]]) {
    const sh = new THREE.Mesh(new THREE.BoxGeometry(8.4, .07, .5), flat('#f1ece2')); sh.position.set(0, y, -2.42); g.add(sh);
    for (let i = 0; i < 22; i++) { const bw = .22 + ((i * 7 + k) % 3) * .05, bh = .3 + ((i * 5 + k) % 4) * .07; const b = new THREE.Mesh(new THREE.BoxGeometry(bw, bh, .3), flat(cols[(i * 3 + k) % cols.length])); b.position.set(-4 + i * .38 + .1, y + .035 + bh / 2, -2.45); g.add(b); }
  }
  for (const x of [-4.2, 0, 4.2]) { const up = new THREE.Mesh(new THREE.BoxGeometry(.09, 2.75, .52), flat('#8a96c0')); up.position.set(x, 1.375, -2.42); g.add(up); }
  // the promo stand, its sign, the basket on its corner
  const st = new THREE.Mesh(new THREE.BoxGeometry(1.2, .92, .62), flat('#f06a5a')); st.position.set(STAND.x, .46, STAND.z); g.add(st);
  const stt = new THREE.Mesh(new THREE.BoxGeometry(1.3, .06, .74), flat('#d6cfc2')); stt.position.set(STAND.x, .95, STAND.z); g.add(stt);
  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(.2, .13, .12, 22), flat('#3f86d6')); bowl.position.set(STAND.x + .3, 1.04, STAND.z); g.add(bowl);
  [['#ff5a7a', -.07, .03], ['#f0c455', .06, -.04], ['#58b848', .0, .08], ['#b06ad8', .09, .07], ['#ff5a7a', -.1, -.06]].forEach(([col, dx, dz], i) => { const k = new THREE.Mesh(new THREE.BoxGeometry(.07, .05, .09), flat(col)); k.position.set(STAND.x + .3 + dx, 1.11 + (i % 2) * .02, STAND.z + dz); k.rotation.y = i; g.add(k); });
  const bk = new THREE.Group(); bk.position.copy(BASKET); g.add(bk);
  const bkb = new THREE.Mesh(new THREE.BoxGeometry(.4, .2, .28), flat('#58b848')); bkb.position.y = .1; bk.add(bkb);
  const bkr = new THREE.Mesh(new THREE.BoxGeometry(.44, .035, .32), flat('#3f9a3a')); bkr.position.y = .21; bk.add(bkr);
  const bkh = new THREE.Mesh(new THREE.TorusGeometry(.17, .016, 8, 20, Math.PI), flat('#2a2f52')); bkh.position.y = .22; bk.add(bkh);
  // the lamp over the stand
  const cord = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, 1.6, 6), flat('#2a2f52')); cord.position.set(LAMPA.x, LAMPA.y + .95, LAMPA.z); cord.userData.noShadow = true; g.add(cord);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(.08, .32, .22, 22, 1, true), new THREE.MeshLambertMaterial({ color: '#f0c455', side: THREE.DoubleSide })); shade.position.set(LAMPA.x, LAMPA.y + .1, LAMPA.z); shade.userData.noShadow = true; g.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(.08, 14, 10), new THREE.MeshBasicMaterial({ color: HDR(2.7, 2.0, 1.0) })); bulb.position.copy(LAMPA); g.add(bulb);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#c9d6ff', '#8a80a8', 1.55));
  const key = new THREE.SpotLight('#ffd9a0', 8, 11, 1.05, .7, 1.3); key.position.copy(LAMPA); key.target.position.set(.1, 0, -.7);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .7); fill.position.set(2, 3, 6); fill.target.position.set(0, 1, -1); L.add(fill); L.add(fill.target);
  scene.add(L); sets.market = { g, L };
  shadows(g);
  dyn.aBeam = beam(scene, LAMPA.toArray(), [.1, .1, -.6], { r0: .14, r1: 1.8, color: '#ffe2a8', strength: .1 });
  dyn.aGlow = glow(scene, LAMPA.toArray(), '#ffc978', 1.1, .45);
}

// ---------------------------------------------------------------- DENEY (x = 200)
const HOCA = { x: 0, z: -1.05 }, DL = { x: -.84, z: -.95 }, DR = { x: .8, z: -.95 }, LAMP = V(200, 2.95, -.7), CF = V(199.6, .83, -.3), CP = V(200.4, .83, -.3);
function buildDeney(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 9), painted(woodTex({ base: '#c9935f', rep: [5, 4] })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 0); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 5), painted(stoneTex({ base: '#b9b4ee', seam: '#9892d6', bw: 96, bh: 48, rep: [7, 5], seed: 3 }))); wall.position.set(0, 2.5, -2.7); g.add(wall);
  const lam = new THREE.Mesh(new THREE.BoxGeometry(12, .95, .06), flat('#5b6aa8')); lam.position.set(0, .475, -2.66); g.add(lam);
  const rail = new THREE.Mesh(new THREE.BoxGeometry(12, .07, .1), flat('#f1ece2')); rail.position.set(0, .98, -2.64); g.add(rail);
  const band = new THREE.Mesh(new THREE.BoxGeometry(12, .3, .04), painted(tileTex({ a: '#58b8a8', b: '#eef3fb', rep: [40, 1] }))); band.position.set(0, 2.72, -2.67); g.add(band);
  const cord = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, 1.4, 6), flat('#2a2f52')); cord.position.set(0, LAMP.y + .85, LAMP.z); cord.userData.noShadow = true; g.add(cord);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(.08, .3, .2, 22, 1, true), new THREE.MeshLambertMaterial({ color: '#2f8f9a', side: THREE.DoubleSide })); shade.position.set(0, LAMP.y + .1, LAMP.z); shade.userData.noShadow = true; g.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(.08, 14, 10), new THREE.MeshBasicMaterial({ color: HDR(2.7, 2.0, 1.0) })); bulb.position.set(0, LAMP.y, LAMP.z); g.add(bulb);
  // the table with its cloth
  const tt = new THREE.Mesh(new THREE.BoxGeometry(1.7, .06, .7), flat('#d6cfc2')); tt.position.set(0, .8, -.3); g.add(tt);
  const ap = new THREE.Mesh(new THREE.BoxGeometry(1.62, .3, .62), flat('#e2463f')); ap.position.set(0, .63, -.3); g.add(ap);
  for (const dx of [-.76, .76]) for (const dz of [-.27, .27]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.06, .5, .06), flat('#4a3a6a')); l.position.set(dx, .25, -.3 + dz); g.add(l); }
  // the fine chocolate: a gold wrapped truffle on a stand; the plain one: a small brown drop on a saucer
  dyn.cf = new THREE.Group(); dyn.cf.position.set(CF.x - 200, CF.y, CF.z); g.add(dyn.cf);
  const ped = new THREE.Mesh(new THREE.CylinderGeometry(.13, .16, .1, 22), flat('#f1e2bd')); ped.position.y = .05; dyn.cf.add(ped);
  const tr = new THREE.Mesh(new THREE.SphereGeometry(.105, 22, 16), flat('#f0b83a')); tr.position.y = .2; dyn.cf.add(tr);
  const rb = new THREE.Mesh(new THREE.TorusGeometry(.106, .014, 8, 26), flat('#e2463f')); rb.rotation.x = Math.PI / 2; rb.position.y = .2; dyn.cf.add(rb);
  const bow = new THREE.Mesh(new THREE.SphereGeometry(.03, 10, 8), flat('#e2463f')); bow.position.set(0, .31, 0); dyn.cf.add(bow);
  dyn.cp = new THREE.Group(); dyn.cp.position.set(CP.x - 200, CP.y, CP.z); g.add(dyn.cp);
  const sau = new THREE.Mesh(new THREE.CylinderGeometry(.13, .1, .025, 22), flat('#eef3fb')); sau.position.y = .012; dyn.cp.add(sau);
  const drop = new THREE.Mesh(new THREE.ConeGeometry(.07, .12, 18), flat('#9a5a34')); drop.position.y = .085; dyn.cp.add(drop);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#b3c0ff', '#7a7096', 1.35));
  const key = new THREE.SpotLight('#ffd49a', 8, 10, 1.05, .7, 1.3); key.position.set(200, LAMP.y, LAMP.z); key.target.position.set(200, 0, -.8);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .6); fill.position.set(201, 3, 6); fill.target.position.set(200, 1, -1); L.add(fill); L.add(fill.target);
  scene.add(L); sets.deney = { g, L };
  shadows(g);
  dyn.bBeam = beam(scene, LAMP.toArray(), [200, .1, -.7], { r0: .14, r1: 1.7, color: '#ffe2a8', strength: .12 });
  dyn.bGlow = glow(scene, LAMP.toArray(), '#ffc978', 1.1, .5);
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  kahraman: { hair: '#3a2a24', cloth: '#3f86d6', collar: true, height: 1.7 },
  satici: { mustache: '#2a1c18', hair: '#2a2024', hat: 'kulah', hatColor: '#e2463f', cloth: '#f0e6cf', pattern: 'stripes', apron: true, bodyW: 236, headW: 284, headH: 256, height: 1.78 },
  hoca: { beard: '#e4e4ee', beardLen: .7, hair: '#d9d9e4', cloth: '#f2f3f8', clothDark: '#b9bdd6', buttons: '#8a96c0', pocket: true, headW: 268, height: 1.74 },
  denek: { hair: '#6a3a24', cloth: '#f09a32', pattern: 'stripes', height: 1.64, headW: 262, headH: 246 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hook: { pos: [.25, 1.5, 3.5], look: [.25, 1.42, -.9], fov: 50 },
  sign: { pos: [.14, 1.62, .9], look: [.14, 1.72, -.6], fov: 40 },
  face: { pos: [HERO.x + .12, 1.5, 1.2], look: [HERO.x, 1.5, HERO.z], fov: 40 },
  two: { pos: [.25, 1.5, 3.55], look: [.25, 1.42, -.9], fov: 50 },
  seller: { pos: [SAT.x - .36, 1.56, 1.95], look: [SAT.x - .1, 1.56, SAT.z], fov: 44 },
  hero: { pos: [HERO.x + .1, 1.5, 2.25], look: [HERO.x + .04, 1.62, HERO.z], fov: 44 },
  lab: { pos: [200, 1.5, 3.7], look: [200, 1.45, -.8], fov: 55 },
  labIn: { pos: [200, 1.48, 3.45], look: [200, 1.46, -.8], fov: 50 },
  fine: { pos: [199.68, 1.3, 1.45], look: [199.6, 1.15, -.3], fov: 40 },
  plain: { pos: [200.32, 1.3, 1.45], look: [200.4, 1.15, -.3], fov: 40 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: both hands on the free thing -> the sign -> his greedy face
    { t: 0, ...SHOT.hook, creep: .14, drift: .006 },
    { t: t('neden') + .02, dur: .2, move: 'whip', ...SHOT.sign, creep: .34, drift: .02 },
    { t: t('hemen') + .12, dur: .2, move: 'whip', ...SHOT.face, creep: .34, drift: .02 },
    { t: t('Bakın,') + .16, dur: .3, move: 'whip', ...SHOT.two, creep: .03, drift: .005 },
    { t: t('Stanttaki') + .1, dur: .3, move: 'whip', ...SHOT.seller, creep: .2, drift: .03 },
    { t: t('Eve') + .08, dur: .3, move: 'whip', ...SHOT.hero, creep: .08, drift: .02 },
    // the experiment
    { t: t('Araştırmacılar') + .2, dur: .3, move: 'whip', ...SHOT.lab, creep: .06, drift: .015 },
    { t: t('biri') + .05, dur: .26, move: 'whip', ...SHOT.fine, creep: .2, drift: .015 },
    { t: t('öbürü') + .05, dur: .26, move: 'whip', ...SHOT.plain, creep: .2, drift: .015 },
    { t: t('İkisi') + .05, dur: .3, move: 'whip', ...SHOT.lab, creep: .05, drift: .012 },
    { t: t('sıradan', 2) + .05, dur: .26, move: 'whip', ...SHOT.plain, creep: .2, drift: .015 },
    { t: t('Bu') + .1, dur: .3, move: 'whip', ...SHOT.lab, creep: .04, drift: .012 },
    // back at the stand: the sum in the head, and what zero does to it
    { t: t('Çünkü') + .2, dur: .3, move: 'whip', ...SHOT.hero, creep: .05, drift: .015 },
    { t: t('Yani') + .2, dur: .3, move: 'whip', ...SHOT.two, creep: .03, drift: .005 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(.02, .4); cp.kick(t('götür!"') + .05, .45); cp.kick(t('on') + .05, .45); cp.kick(t('bedava', 3) + .1, .6); cp.kick(t('koştu.') + .05, .5); cp.kick(t('duruyor;') + .05, .5); cp.kick(t('sıfır') + .1, .7);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .8) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#33407a');
  buildMarket(scene); buildDeney(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.sign = card(scene, 1.36, .5, drawSign, { pw: 768 });
  dyn.key = card(scene, .3, .42, drawKey, { pw: 256 });
  dyn.zero = card(scene, .5, .5, burst('0 ₺', '#ffe15a', '#c8323a'));
  dyn.big0 = card(scene, .9, .9, burst('0', '#ffe15a', '#c8323a', .52), { pw: 640 });
  dyn.drawer = card(scene, .95, .8, drawDrawer, { pw: 640 });
  dyn.x10 = card(scene, .42, .42, burst('x10', '#ff8ab8', PLUM, .3));
  dyn.tagF = dynCard(scene, .4, .23, drawTag, { steps: 1, pw: 384 }); dyn.tagP = dynCard(scene, .4, .23, drawTag, { steps: 1, pw: 384 });
  dyn.votF = dynCard(scene, 1.1, .42, drawVotes, { steps: 1, pw: 512 }); dyn.votP = dynCard(scene, 1.1, .42, drawVotes, { steps: 1, pw: 512 });
  dyn.minus = [0, 1].map(() => card(scene, .3, .3, burst('-1', '#8fe89a', '#1f6a3a', .36), { pw: 256 }));
  dyn.eq = card(scene, .3, .3, drawMark('=', '#ffe15a'), { pw: 256 });
  dyn.scale = dynCard(scene, .86, .74, drawScale, { steps: 12 });
  dyn.plate = dynCard(scene, .6, .8, drawPlate, { steps: 1, pw: 384 });
  dyn.q = card(scene, .3, .36, drawMark('?', '#ffe15a'), { pw: 256 });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .02, 'whoosh'); cue(W('Araştırmacılar') + .1, 'whoosh'); cue(W('Çünkü') + .1, 'whoosh');
  cue(W('neden'), 'rise', { dur: .3 }); cue(W('hemen') + .08, 'rise', { dur: .3 }); cue(.02, 'lock');
  cue(W('anahtarlık,'), 'shimmer'); cue(W('bedava', 2), 'lock'); cue(W('sepete') + .1, 'cut');
  cue(W('Stanttaki') + .02, 'rise', { dur: .35 }); cue(W('götür!"') + .05, 'boom'); cue(W('Eve'), 'rise', { dur: .35 }); cue(W('çekmeceye'), 'scrape', { dur: .5 }); cue(W('on') + .05, 'boom');
  cue(W('iki'), 'lock'); cue(W('biri'), 'rise', { dur: .3 }); cue(W('pahalı,'), 'shimmer'); cue(W('öbürü'), 'rise', { dur: .3 }); cue(W('ucuz.'), 'lock');
  cue(W('İkisi'), 'rise', { dur: .3 }); cue(W('kaliteli', 2), 'lock'); cue(W('seçti.'), 'lock');
  cue(W('birer'), 'lock'); cue(W('sent'), 'lock'); cue(W('aynı'), 'shimmer'); cue(W('sıradan', 2), 'rise', { dur: .3 }); cue(W('bedava', 3) + .1, 'boom');
  cue(W('Bu'), 'rise', { dur: .35 }); cue(W('çoğunluk'), 'wind', { dur: W('koştu.') - W('çoğunluk') }); cue(W('koştu.') + .05, 'boom');
  cue(W('hesap'), 'lock'); cue(W('değer'), 'lock'); cue(W('değmez'), 'lock'); cue(W('duruyor;') + .05, 'boom'); cue(W('kaybedecek'), 'shimmer');
  cue(W('Tıpkı'), 'rise', { dur: .35 }); for (const [w, n] of [['tabağı', 1], ['bir', 5], ['kez', 2], ['daha', 1], ['doldurman', 1]]) cue(W(w, n), 'lock');
  cue(W('Yani') + .1, 'rise', { dur: .35 }); cue(W('sıfır') + .1, 'boom'); cue(W('istetti.'), 'shimmer');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'BEDAVAYI NEDEN HEMEN KAPARIZ?'); }

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
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
  const where = cam.position.x > 100 ? 'deney' : 'market';
  vis('market', where === 'market'); vis('deney', where === 'deney'); dyn.where = where;
  dyn.aBeam.visible = dyn.aGlow.visible = where === 'market'; dyn.bBeam.visible = dyn.bGlow.visible = where === 'deney';
  for (const c of Object.values(cast)) c.hide();
  for (const m of [dyn.sign, dyn.key, dyn.zero, dyn.big0, dyn.drawer, dyn.x10, dyn.tagF, dyn.tagP, dyn.votF, dyn.votP, ...dyn.minus, dyn.eq, dyn.scale, dyn.plate, dyn.q]) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const RT = V(1, 0, 0).applyQuaternion(cam.quaternion), UP = V(0, 1, 0).applyQuaternion(cam.quaternion);
  let look, grade = [1, 1, 1], face = [1, .985, .97];
  if (where === 'market') {
    grade = [1.01, 1.0, 1.01];
    const tint = face.map((v, i) => v / grade[i]);
    const H = cast.kahraman, K = cast.satici;
    const inHook = t < A('Bakın,'), inL2 = !inHook && t < A('Stanttaki'), inL3 = t >= A('Stanttaki') && t < A('Eve'), inL4 = t >= A('Eve') && t < A('Araştırmacılar') + .4;
    const inL11 = t > A('Çünkü') - .3 && t < A('Bedava', 5), inL12 = t >= A('Bedava', 5) && t < A('Tıpkı'), inL13 = t >= A('Tıpkı') && t < A('Yani') + .16, inL14 = t >= A('Yani') + .16;
    // the sign stands over the stand, a real board on its poles
    dyn.sign.visible = true; dyn.sign.quaternion.identity(); dyn.sign.position.copy(SIGN); dyn.sign.scale.setScalar(.8); dyn.sign.material.opacity = 1;
    const head = V(HERO.x, 1.49, HERO.z), at = (r, u) => head.clone().addScaledVector(RT, r).addScaledVector(UP, u);
    const mid = V(.12, 1.72, -.6);
    // ---- the hero
    let hp = { expr: 'neutral', look: 0, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(1, A('hemen'), A('hiç'), A('anahtarlık,'), A('sepete'), A('orada'), A('hesap'), A('duruyor;'), A('doyduğun'), A('istemedin;'), A('sıfır')) };
    if (inHook) hp = t < A('hemen') ? { ...hp, expr: 'grin', look: .7, lookY: -.3, gazeX: 1, gazeY: -.6, brow: 1, lean: 8, armL: [150, 20], armR: [128, 24], bob: Math.sin(t * 24) * 3 }
      : { ...hp, expr: 'grin', look: .2, brow: .9, armL: [150, 24], armR: [150, 24], bob: Math.sin(t * 24) * 3 };
    if (inL2) {
      const want = t > A('anahtarlık,'), free = t > A('bedava', 2), got = t > A('sepete') + .25;
      hp = !want ? { ...hp, expr: t > A('hiç') ? 'smug' : 'neutral', look: .5, lid: t > A('hiç') ? .3 : 0, armL: t > A('hiç') ? [30, -100] : [16, 10], armR: t > A('hiç') ? [30, -96] : [16, 10] }
        : !free ? { ...hp, expr: 'neutral', look: .7, lookY: -.3, gazeY: -.5, brow: .3 }
        : { ...hp, expr: got ? 'grin' : 'surprised', look: .7, lookY: got ? 0 : -.3, brow: 1, mouth: got ? 0 : .5, armR: got ? [16, 10] : [128, 24], armL: got ? [150, 24] : [16, 10] };
    }
    if (inL3) hp = { ...hp, expr: 'grin', look: .8, gazeX: 1, brow: .8 };
    if (inL4) {
      const home = t > A('orada'), ten = t > A('on');
      hp = { ...hp, expr: ten ? 'worried' : home ? 'surprised' : 'smile', look: .1, lookY: -.5, gazeY: -1, brow: ten ? .8 : home ? 1 : .3, sweat: ten ? 1 : 0, armR: home ? [16, 10] : [150, 22], armL: ten ? [58, -72] : [16, 10], ...(ten ? { armR: [58, -72] } : {}) };
    }
    if (inL11) {
      const calc = t > A('hesap');
      hp = { ...hp, expr: calc ? 'focused' : 'neutral', look: .1, lookY: calc ? -.45 : 0, gazeY: calc ? -1 : 0, brow: calc ? -.2 : .2, lid: calc ? .2 : 0, armR: calc ? [148, -128] : [16, 10], tilt: calc ? Math.sin(t * 5) * 4 : 0 };
    }
    if (inL12) {
      const stop = t > A('duruyor;');
      hp = { ...hp, expr: stop ? 'grin' : 'surprised', look: .15, lookY: -.4, gazeY: -1, brow: 1, mouth: stop ? 0 : .5, armL: stop ? [150, 24] : [16, 10], armR: stop ? [150, 24] : [16, 10], bob: stop ? Math.sin(t * 20) * 3 : 0 };
    }
    if (inL13) {
      const full = t > A('doyduğun'), more = t > A('tabağı');
      hp = { ...hp, expr: more ? 'grin' : full ? 'worried' : 'smile', look: .2, lookY: more ? .3 : 0, gazeY: more ? .8 : 0, brow: more ? .9 : .4, sweat: full ? 1 : 0, lid: full && !more ? .4 : 0, armL: [44, -86], armR: [44, -84] };
    }
    if (inL14) {
      const doubt = t > A('aslında') && t < A('sıfır'), zero = t >= A('sıfır');
      hp = zero ? { ...hp, expr: 'surprised', look: .5, lookY: -.5, gazeX: .6, gazeY: -1, brow: 1, mouth: .5, armL: [58, -72], armR: [58, -72] }
        : { ...hp, expr: doubt ? 'worried' : 'neutral', look: .45, lookY: .35, gazeX: 1, gazeY: 1, brow: doubt ? .7 : .2, armR: [64, -78] };
    }
    H.show(); H.place(HERO.x, 0, HERO.z, cam, tint);
    H.draw({ ...hp, lit: 1, shade: COOL, rim: { color: WARM, a: .4 } }); H.castFrom(LAMPA);
    // ---- the seller behind his stand
    if (!inL4 && !inL11 && !inL12 && !inL13) {
      const talk = t > A('"Buyur') - .04 && t < A('götür!"') + .45, laugh = inL14 && t > A('sıfır') + .2;
      let kp = { expr: 'smug', look: -.6, lid: .3, armL: [16, 10], armR: [16, 10], blink: bl(2, A('anahtarlık,'), A('sırıtıyor:'), A('"Buyur'), A('para'), A('sıfır')) };
      if (inHook) kp = { ...kp, expr: 'grin', lid: 0, brow: .5, armL: [112, 30] };
      if (inL2 && t > A('anahtarlık,') && t < A('sepete') + .3) kp = { ...kp, expr: 'grin', lid: 0, brow: .6, armL: [112, 30] };
      if (inL3) kp = { ...kp, expr: t > A('sırıtıyor:') ? 'grin' : 'smug', lid: .2, brow: .5, look: -.5 };
      if (talk) kp = { ...kp, expr: 'grin', lid: 0, brow: .8, look: -.55, mouth: flap(env, t), armL: [104, 28 + 10 * Math.sin(t * 12)], armR: t > A('para') ? [104, 28 + 10 * Math.sin(t * 12 + 1)] : [16, 10], bob: Math.sin(t * 9) * 2 };
      if (inL14 && !laugh) kp = { ...kp, expr: 'smug', lid: .35, look: -.65 };
      if (laugh) kp = { ...kp, expr: 'laugh', lid: 0, laughMarks: .9, look: -.5, mouth: .5 + .5 * Math.abs(Math.sin(t * 13)), bob: -Math.abs(Math.sin(t * 13)) * 10, armL: [28, -100], armR: [150, 22] };
      K.show(); K.place(SAT.x, 0, SAT.z, cam, tint);
      K.draw({ ...kp, lit: -1, shade: COOL, rim: { color: WARM, a: .4 } }); K.castFrom(LAMPA);
    }
    // ---- the key ring nobody needs, and the price that sells it
    if (inHook && t < A('hemen') + .2) { popCard(dyn.key, -1, t, mid.clone().add(V(.02, -.1 + Math.sin(t * 9) * .02, 0)), 1.5, false); popCard(dyn.zero, -1, t, mid.clone().add(V(.2, -.36, .02)), .72, false); dyn.zero.rotation.z += Math.sin(t * 7) * .08; }
    if (inL2 && t > A('anahtarlık,')) {
      const fly = ramp(t, A('sepete'), A('sepete') + .32), p0 = mid.clone().add(V(.05, -.05, 0)), p1 = BASKET.clone().add(V(0, .2, 0));
      if (fly < 1) { const s = popCard(dyn.key, A('anahtarlık,'), t, p0.lerp(p1, fly), 1.5 * (1 - .55 * fly)); dyn.key.position.y += Math.sin(Math.PI * fly) * .25; }
      if (t > A('bedava', 2) && fly < .05) { popCard(dyn.zero, A('bedava', 2), t, mid.clone().add(V(.2, -.36, .02)), .72); }
    }
    if (inL3 && t > A('para')) popCard(dyn.zero, A('para'), t, V(SAT.x - .36, 2.2, SAT.z + .1), .75);
    if (inL4) { if (t > A('çekmeceye')) popCard(dyn.drawer, A('çekmeceye'), t, at(.04, .7), .95); else popCard(dyn.key, -1, t, at(.34, .42), 1.1, false); if (t > A('on')) popCard(dyn.x10, A('on'), t, at(.4, .3), .95); }
    // ---- the sum in the head; then zero stops it
    if (inL11 && t > A('hesap')) { const sw = t > A('değer') ? Math.sin((t - A('değer')) * 5.2) : Math.sin((t - A('hesap')) * 4) * .4; dyn.scale.userData.set(sw); popCard(dyn.scale, A('hesap'), t, at(.04, .7), .9, false); }
    if (inL12) {
      const stop = t > A('duruyor;');
      if (!stop) { dyn.scale.userData.set(0); popCard(dyn.scale, -1, t, at(.04, .7), .9, false); dyn.scale.position.addScaledVector(RT, Math.sin(t * 60) * .006); }
      popCard(dyn.zero, A('Bedava', 5), t, stop ? at(.04, .72) : at(.42, .3), stop ? 1.4 : .8); if (stop) dyn.zero.rotation.z += Math.sin(t * 5) * .06;
    }
    // ---- the buffet plate
    if (inL13) {
      const lv = 2 + [['tabağı', 1], ['bir', 5], ['kez', 2], ['daha', 1], ['doldurman', 1]].filter(([w, n]) => t > A(w, n)).length;
      dyn.plate.userData.set(lv); const s = popCard(dyn.plate, A('açık'), t, at(.05, .74), 1, false); if (s) dyn.plate.rotation.z += Math.sin(t * 3) * .03;
    }
    // ---- he did not want it; the zero did
    if (inL14) {
      if (t < A('sıfır')) popCard(dyn.key, A('o'), t, at(.36, .26), 1.2);
      else { const s = popCard(dyn.big0, A('sıfır'), t, V(.08, 2.3, -.7), .85); dyn.big0.rotation.z += Math.sin(t * 4) * .06; popCard(dyn.key, -1, t, at(.36, .26), 1.2, false); }
      if (t > A('istemedin;') && t < A('sıfır')) popCard(dyn.q, A('istemedin;'), t, at(-.02, .52));
    }
    const f = t > W('neden') + .1 && t < W('hemen') + .1 ? SIGN : inL3 ? V(SAT.x, 1.5, SAT.z) : V(HERO.x, 1.45, HERO.z);
    look = { focus: cam.position.distanceTo(f), coc: 4, range: 2.8, sat: 1.24, lift: [.085, .085, .15], bloom: .85, vignette: .22 };
  } else {
    // ---- the experiment: two chocolates, two prices; then one cent off both
    grade = [1.0, .995, 1.02];
    const tint = face.map((v, i) => v / grade[i]);
    const R = cast.hoca, D = cast.denek;
    const put = t > A('iki'), tagF = t > A('pahalı,'), tagP = t > A('ucuz.'), choose = t > A('kaliteli', 2), cut = t > A('birer'), same = t > A('aynı'), free = t > A('bedava', 3), run = t > A('çoğunluk'), ran = t > A('koştu.') - .1, before = t > A('Oysa');
    for (const [m, t0] of [[dyn.cf, A('iki')], [dyn.cp, A('iki') + .12]]) { m.visible = t > t0; if (m.visible) m.scale.setScalar(.2 + .8 * backOut((t - t0) / .22)); }
    dyn.cp.position.y = CP.y + (free ? Math.abs(Math.sin((t - A('bedava', 3)) * 9)) * .05 * Math.exp(-(t - A('bedava', 3)) * 2) : 0);
    const closeF = t > W('biri') + .15 && t < W('öbürü') + .15, closeP = (t > W('öbürü') + .15 && t < W('İkisi') + .15) || (t > W('sıradan', 2) + .15 && t < W('Bu') + .2);
    // the researcher behind the table
    let rp = { expr: 'smug', look: 0, armL: [16, 10], armR: [16, 10], blink: bl(3, A('iki'), A('biri'), A('öbürü'), A('İkisi'), A('birer'), A('aynı'), A('bedava', 3), A('koştu.'), A('Oysa')) };
    if (put && t < A('İkisi')) rp = { ...rp, expr: 'proud', armL: [70, 24], armR: [70, 24], lookY: .3 };
    if (choose && !cut) rp = { ...rp, expr: 'smile', look: -.5, brow: .3 };
    if (cut && !free) rp = { ...rp, expr: same ? 'proud' : 'focused', lookY: .3, brow: same ? .4 : -.2, armL: same ? [16, 10] : [84, 30], armR: same ? [16, 10] : [84, 30] };
    if (free && !run) rp = { ...rp, expr: 'smug', look: .5, lid: .3 };
    if (run) rp = { ...rp, expr: ran ? 'surprised' : 'neutral', look: .7, gazeX: 1, brow: ran ? 1 : .3, mouth: ran ? .4 : 0 };
    if (before) rp = { ...rp, expr: 'worried', look: .6, brow: .7, mouth: 0, armL: [58, -72], armR: [58, -72] };
    if (!closeF && !closeP) { R.show(); R.place(200 + HOCA.x, 0, HOCA.z, cam, tint);
      R.draw({ ...rp, lit: 1, shade: COOL, rim: { color: WARM, a: .4 } }); R.castFrom(LAMP); }
    // the volunteer: first to the fine one, then running to the free one
    const k = run ? ramp(t, A('çoğunluk'), A('koştu.') - .05) : 0, dx = lerpN(DL.x, DR.x, k), moving = k > .02 && k < .98;
    let dp = { expr: 'neutral', look: .4, armL: [16, 10], armR: [16, 10], blink: bl(4, A('İkisi'), A('kaliteli', 2), A('birer'), A('bedava', 3), A('çoğunluk'), A('koştu.'), A('Oysa')) };
    if (choose && !cut) dp = { ...dp, expr: 'smile', look: .6, lookY: .4, gazeY: 1, brow: .5, armR: [84, 30] };
    if (cut && !free) dp = { ...dp, expr: 'neutral', look: .6, lookY: .2 };
    if (free && !run) dp = { ...dp, expr: 'surprised', look: .8, gazeX: 1, brow: 1, mouth: .5 };
    if (moving) dp = { ...dp, expr: 'grin', look: .9, brow: 1, lean: 12, armL: [60 + Math.sin(t * 22) * 40, -40], armR: [60 - Math.sin(t * 22) * 40, -40], bob: Math.abs(Math.sin(t * 22)) * 8 };
    if (ran) dp = { ...dp, expr: 'grin', look: -.6, lookY: .4, gazeX: -1, gazeY: 1, brow: 1, lean: 0, armL: [128, 24], armR: [150, 24], bob: Math.sin(t * 18) * 3 };
    const dShow = t > A('İkisi') - .2 && !closeP;
    if (dShow) { const enter = backOut((t - A('İkisi') + .2) / .3); D.show(); D.place(200 + dx - (1 - Math.min(1, enter)) * 1.2, 0, DL.z, cam, tint);
      D.draw({ ...dp, lit: k > .5 ? -1 : 1, shade: COOL, rim: { color: WARM, a: .42 } }); D.castFrom(LAMP); }
    // tags and votes
    const pf = V(CF.x - .02, 1.31, CF.z), pp = V(CP.x + .02, 1.31, CP.z);
    if (tagF) { dyn.tagF.userData.set(cut ? 14 : 15); popCard(dyn.tagF, A('pahalı,'), t, closeF ? V(CF.x + .02, 1.33, CF.z) : pf, closeF ? .8 : 1, false); if (cut) dyn.tagF.rotation.z += Math.sin((t - A('birer')) * 30) * .2 * Math.exp(-(t - A('birer')) * 7); }
    if (tagP) { dyn.tagP.userData.set(cut ? 0 : 1); const pop = free ? 1 + .25 * Math.exp(-(t - A('bedava', 3)) * 3) : 1; popCard(dyn.tagP, A('ucuz.'), t, closeP ? V(CP.x - .02, 1.3, CP.z) : pp, (closeP ? .8 : 1) * pop, false); if (cut) dyn.tagP.rotation.z += Math.sin((t - A('sent')) * 30) * .2 * Math.exp(-Math.max(0, t - A('sent')) * 7); }
    if (cut && !same) { popCard(dyn.minus[0], A('birer'), t, pf.clone().add(V(0, .25, 0)), .7); popCard(dyn.minus[1], A('sent'), t, pp.clone().add(V(0, .25, 0)), .7); }
    if (same && !free) popCard(dyn.eq, A('aynı'), t, V(200, 1.02, -.2), 1);
    if (choose && !closeP && !closeF) {
      const nf = !run ? Math.min(3, 1 + Math.floor((t - A('kaliteli', 2)) / .25)) : ran ? 1 : 3, np = !run ? (t > A('seçti.') ? 1 : 0) : ran ? Math.min(3, 1 + Math.floor((t - A('koştu.') + .1) / .2)) : 1;
      if (cut && !run) { dyn.votF.userData.set(0); dyn.votP.userData.set(0); }
      else { dyn.votF.userData.set(nf); dyn.votP.userData.set(np); popCard(dyn.votF, A('kaliteli', 2), t, V(CF.x - .14, 2.1, -.5), 1, false); popCard(dyn.votP, A('kaliteli', 2), t, V(CP.x + .14, 2.1, -.5), 1, false); }
    }
    look = { focus: cam.position.distanceTo(closeF ? CF : closeP ? CP : V(200, 1.3, -.95)), coc: 4, range: 3.2, sat: 1.2, lift: [.085, .085, .15], bloom: .9, vignette: .22 };
  }
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
