// Beklerken zaman neden geçmek bilmez? Demek O Yüzden günlük Short (yumurta stili), 25 Kasım 2026.
// Bilgi: suyun kaynamasını beklemesi söylenen grup, aynı 240 saniyeyi diğer gruptan daha uzun tahmin etti (Cahoon ve
// Edmonds, 1980). Açıklama: beklerken dikkat zamanın kendisine kayar, süre uzamış gibi gelir (Zakay ve Block, dikkat kapısı
// modeli). Kaynaklar SCRIPT.md'de.
// Setler: MUTFAK (x≈0) pencere ışığı, ada tezgâh, ocakta kırmızı çaydanlık, duvar saati; DENEY ODASI (x≈200) sarkıt lamba,
// iki masa, iki ocak, iki denek ve kronometreli hoca.
import * as THREE from 'three';
import { stoneTex, woodTex, tileTex, painted, flat } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-25-beklerken-zaman';
export const FPS = 30;
export let DUR = 34.2;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lerpN = (a, b, k) => a + (b - a) * k;
const clamp01 = x => Math.max(0, Math.min(1, x));
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
function card(scene, w, h, draw, { pw = 512, hdr = null, layer = 1 } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); draw(c.getContext('2d'), c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false, color: hdr || 0xffffff }));
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
// a clock face: m = minutes (0..60, the long hand), s = seconds (0..60, the thin red hand), hr = the hour
function clockFace(g, cx, cy, R, m, s, hr = 4, thin = false) {
  g.lineCap = g.lineJoin = 'round';
  g.fillStyle = '#fbf7ee'; g.strokeStyle = PLUM; g.lineWidth = R * .13; g.beginPath(); g.arc(cx, cy, R * .9, 0, 6.29); g.fill(); g.stroke();
  if (!thin) { g.strokeStyle = '#e2463f'; g.lineWidth = R * .05; g.beginPath(); g.arc(cx, cy, R * .9, 0, 6.29); g.stroke(); }
  g.strokeStyle = PLUM;
  for (let k = 0; k < 12; k++) { const a = k / 12 * 6.283, r0 = R * (k % 3 ? .74 : .66); g.lineWidth = R * (k % 3 ? .03 : .06); g.beginPath(); g.moveTo(cx + Math.sin(a) * r0, cy - Math.cos(a) * r0); g.lineTo(cx + Math.sin(a) * R * .8, cy - Math.cos(a) * R * .8); g.stroke(); }
  const hand = (turn, len, wd, col) => { const a = turn * 6.283; g.strokeStyle = col; g.lineWidth = wd; g.beginPath(); g.moveTo(cx - Math.sin(a) * len * .12, cy + Math.cos(a) * len * .12); g.lineTo(cx + Math.sin(a) * len, cy - Math.cos(a) * len); g.stroke(); };
  hand((hr + m / 60) / 12, R * .42, R * .1, PLUM); hand(m / 60, R * .64, R * .07, PLUM);
  if (s >= 0) hand(s / 60, R * .7, R * .03, '#e2463f');
  g.fillStyle = PLUM; g.beginPath(); g.arc(cx, cy, R * .07, 0, 6.29); g.fill();
}
function drawClock(g, w, h, m, s) { clockFace(g, w / 2, h / 2, w / 2, m, s); }
function cloudPath(c, w, h) { c.beginPath(); for (let k = 0; k < 9; k++) { const a = k / 9 * 6.283; c.arc(w / 2 + Math.cos(a) * w * .3, h / 2 + Math.sin(a) * h * .26, w * .14, 0, 6.29); } }
// what the wait felt like: n clocks in a thought
function drawThought(c, w, h, n) {
  c.lineJoin = c.lineCap = 'round'; c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 14;
  cloudPath(c, w, h); c.stroke(); cloudPath(c, w, h); c.fill(); c.beginPath(); c.ellipse(w / 2, h / 2, w * .37, h * .31, 0, 0, 6.29); c.fill();
  const R = n > 1 ? h * .2 : h * .24;
  for (let i = 0; i < n; i++) clockFace(c, w / 2 + (i - (n - 1) / 2) * R * 1.9, h / 2 + (n > 1 ? (i % 2 ? .05 : -.05) * h : 0), R, [20, 40, 55][i] || 20, -1, 4 + i, true);
}
// the researcher's stopwatch: four minutes
function drawStopwatch(c, w, h) {
  c.lineJoin = c.lineCap = 'round'; const cx = w / 2, cy = h * .56, R = w * .4;
  c.fillStyle = '#e8b23e'; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(cx - w * .07, h * .03, w * .14, h * .12, 8); c.fill(); c.stroke();
  c.save(); c.translate(cx + R * .78, cy - R * .78); c.rotate(.78); c.beginPath(); c.roundRect(-w * .05, -h * .06, w * .1, h * .1, 6); c.fill(); c.stroke(); c.restore();
  c.fillStyle = '#e8b23e'; c.beginPath(); c.arc(cx, cy, R, 0, 6.29); c.fill(); c.stroke();
  c.fillStyle = '#fbf7ee'; c.lineWidth = 9; c.beginPath(); c.arc(cx, cy, R * .8, 0, 6.29); c.fill(); c.stroke();
  c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${w * .34}px "Arial Black", "Inter", sans-serif`; c.fillText('4', cx, cy - h * .05);
  c.font = `900 ${w * .115}px "Arial Black", "Inter", sans-serif`; c.fillStyle = '#c8323a'; c.fillText('DAKİKA', cx, cy + h * .14);
}

// ---------------------------------------------------------------- MUTFAK (x = 0)
const KET = V(-.38, .99, -.3), CROUCH = { x: .1, y: -.3, z: -.95 }, WORK = { x: .5, z: -.95 }, ANNE = { x: 1.04, z: -1.02 };
const CLOCK = V(1.15, 2.2, -2.33), WIN = V(-1.25, 2.2, -2.36), BOWL = V(WORK.x + .2, .96, -.52);
const SPOUT = V(KET.x + .27, KET.y + .3, KET.z);
function buildMutfak(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 9), painted(woodTex({ base: '#c08a5c', rep: [5, 4] })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 0); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 5), painted(stoneTex({ base: '#9fb4dc', seam: '#7f96c4', bw: 64, bh: 64, rep: [12, 5] })));
  wall.position.set(0, 2.5, -2.4); g.add(wall);
  const dado = new THREE.Mesh(new THREE.BoxGeometry(12, .42, .05), painted(tileTex({ a: '#5b8fe0', b: '#f2ead8', rep: [28, 1] }))); dado.position.set(0, 1.25, -2.36); g.add(dado);
  for (const y of [1.02, 1.48]) { const m = new THREE.Mesh(new THREE.BoxGeometry(12, .05, .08), flat('#eef3fb')); m.position.set(0, y, -2.35); g.add(m); }
  // the counter along the wall, the island in front of it
  const cab = flat('#3d6fa8'), top = flat('#f6efe0');
  const bc = new THREE.Mesh(new THREE.BoxGeometry(8, .9, .6), cab); bc.position.set(0, .45, -2.08); g.add(bc);
  const bt = new THREE.Mesh(new THREE.BoxGeometry(8.1, .06, .68), top); bt.position.set(0, .93, -2.06); g.add(bt);
  const isl = new THREE.Mesh(new THREE.BoxGeometry(2.9, .9, .74), flat('#2f8f9a')); isl.position.set(.3, .45, -.3); g.add(isl);
  const it = new THREE.Mesh(new THREE.BoxGeometry(3.02, .06, .86), top); it.position.set(.3, .93, -.3); g.add(it);
  for (let i = 0; i < 4; i++) { const d = new THREE.Mesh(new THREE.BoxGeometry(.58, .62, .03), flat('#3aa3ad')); d.position.set(-.75 + i * .7, .47, .08); g.add(d);
    const k = new THREE.Mesh(new THREE.BoxGeometry(.05, .14, .03), flat('#f1e2bd')); k.position.set(-.55 + i * .7, .6, .11); g.add(k); }
  // jars on the back counter (warm spots on the cool wall)
  for (const [x, col, hh] of [[-.2, '#e8b23e', .26], [.1, '#d8483a', .2], [.38, '#f2ead8', .3], [1.9, '#e8b23e', .22], [2.2, '#3f9a5c', .3]]) { const j = new THREE.Mesh(new THREE.CylinderGeometry(.09, .09, hh, 14), flat(col)); j.position.set(x, .96 + hh / 2, -2.1); g.add(j);
    const l = new THREE.Mesh(new THREE.CylinderGeometry(.095, .095, .04, 14), flat('#7a5644')); l.position.set(x, .98 + hh, -2.1); g.add(l); }
  // the window: the light of the set
  const pane = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.2), new THREE.MeshBasicMaterial({ color: HDR(1.75, 1.5, 1.05) })); pane.position.copy(WIN); g.add(pane);
  const fr = flat('#f1ece2');
  for (const [w, h, x, y] of [[1.18, .09, 0, .64], [1.18, .12, 0, -.65], [.09, 1.36, -.55, 0], [.09, 1.36, .55, 0], [.05, 1.2, 0, 0], [1.0, .05, 0, .1]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .1), fr); b.position.set(WIN.x + x, WIN.y + y, WIN.z + .06); b.userData.noShadow = true; g.add(b); }
  // the stove and the kettle
  const plate = new THREE.Mesh(new THREE.BoxGeometry(.62, .035, .52), flat('#3a4066')); plate.position.set(KET.x, .975, KET.z); g.add(plate);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.12, .014, 8, 24), flat('#20243f')); ring.rotation.x = Math.PI / 2; ring.position.set(KET.x, 1.0, KET.z); g.add(ring);
  dyn.flames = [];
  for (let k = 0; k < 10; k++) { const a = k / 10 * 6.283, f = new THREE.Mesh(new THREE.ConeGeometry(.022, .07, 6), new THREE.MeshBasicMaterial({ color: HDR(.55, 1.2, 3.4) })); f.position.set(KET.x + Math.cos(a) * .13, 1.03, KET.z + Math.sin(a) * .13); f.userData.noShadow = true; f.layers.set(1); g.add(f); dyn.flames.push(f); }
  const kg = new THREE.Group(); kg.position.set(KET.x, KET.y + .045, KET.z); g.add(kg); dyn.kettle = kg;
  const red = flat('#d8483a');
  const body = new THREE.Mesh(new THREE.SphereGeometry(.2, 28, 18), red); body.scale.set(1, .8, 1); body.position.y = .15; kg.add(body);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(.16, .17, .05, 24), flat('#a8343a')); base.position.y = .02; kg.add(base);
  dyn.lid = new THREE.Mesh(new THREE.CylinderGeometry(.09, .11, .035, 20), flat('#f1e2bd')); dyn.lid.position.y = .315; kg.add(dyn.lid);
  const knob = new THREE.Mesh(new THREE.SphereGeometry(.03, 12, 10), flat('#2a2f52')); knob.position.y = .03; dyn.lid.add(knob);
  const spout = new THREE.Mesh(new THREE.CylinderGeometry(.022, .04, .22, 12), red); spout.position.set(.21, .2, 0); spout.rotation.z = -.9; kg.add(spout);
  const handle = new THREE.Mesh(new THREE.TorusGeometry(.13, .017, 8, 22, Math.PI), flat('#2a2f52')); handle.position.y = .29; kg.add(handle);
  // the bowl the hero whisks later
  dyn.bowl = new THREE.Group(); dyn.bowl.position.copy(BOWL); g.add(dyn.bowl);
  const bw = new THREE.Mesh(new THREE.CylinderGeometry(.17, .1, .13, 22), flat('#fbf7ee')); bw.position.y = .065; dyn.bowl.add(bw);
  const yolk = new THREE.Mesh(new THREE.CylinderGeometry(.155, .155, .01, 22), flat('#f2c23a')); yolk.position.y = .128; yolk.userData.noShadow = true; dyn.bowl.add(yolk);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#b9c6ff', '#8a7a9a', 1.5));
  const KEYP = V(-2.0, 2.9, -1.7); dyn.keyP = KEYP;
  const key = new THREE.SpotLight('#ffd9a0', 12, 12, .95, .6, 1.3); key.position.copy(KEYP); key.target.position.set(.4, .8, -.5);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .7); fill.position.set(2, 3, 6); fill.target.position.set(0, 1, -1); L.add(fill); L.add(fill.target);
  dyn.fire = new THREE.PointLight('#6fa8ff', 0, 1.1, 1.8); dyn.fire.position.set(KET.x, 1.08, KET.z + .2); L.add(dyn.fire);
  scene.add(L); sets.mutfak = { g, L };
  shadows(g);
  dyn.aBeam = beam(scene, [WIN.x, WIN.y, WIN.z + .1], [.5, .6, .2], { r0: .5, r1: 1.5, color: '#ffe2a8', strength: .1 });
  dyn.aGlow = glow(scene, [WIN.x, WIN.y, WIN.z + .15], '#ffd28a', 1.9, .2);
}

// ---------------------------------------------------------------- DENEY ODASI (x = 200)
const D1 = { x: -.53, y: -.3, z: -.95 }, D2 = { x: .55, z: -.95 }, HOCA = { x: 0, z: -1.75 }, LAMP = V(200, 2.95, -.9);
function buildDeney(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 9), painted(stoneTex({ base: '#d2daf0', seam: '#a6b4d8', bw: 128, bh: 128, rep: [8, 6], seed: 4 })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 0); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 5), flat('#a3b0e2')); wall.position.set(0, 2.5, -2.7); g.add(wall);
  const lam = new THREE.Mesh(new THREE.BoxGeometry(12, 1.15, .06), painted(woodTex({ base: '#b58a66', rep: [6, 1], vertical: true }))); lam.position.set(0, .575, -2.66); g.add(lam);
  const rail = new THREE.Mesh(new THREE.BoxGeometry(12, .07, .1), flat('#f1ece2')); rail.position.set(0, 1.18, -2.64); g.add(rail);
  const band = new THREE.Mesh(new THREE.BoxGeometry(12, .3, .04), painted(tileTex({ a: '#f0c455', b: '#eef3fb', rep: [40, 1] }))); band.position.set(0, 2.55, -2.67); g.add(band);
  // the lamp over the tables
  const cord = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, 1.4, 6), flat('#2a2f52')); cord.position.set(0, LAMP.y + .85, LAMP.z); g.add(cord);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(.08, .3, .2, 22, 1, true), new THREE.MeshLambertMaterial({ color: '#2f8f9a', side: THREE.DoubleSide })); shade.position.set(0, LAMP.y + .1, LAMP.z); shade.userData.noShadow = true; g.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(.08, 14, 10), new THREE.MeshBasicMaterial({ color: HDR(2.7, 2.0, 1.0) })); bulb.position.set(0, LAMP.y, LAMP.z); g.add(bulb);
  // two tables, two hot plates, two pots
  dyn.coils = [];
  for (const x of [D1.x, D2.x]) {
    const tt = new THREE.Mesh(new THREE.BoxGeometry(.84, .06, .62), flat('#f6efe0')); tt.position.set(x, .8, -.32); g.add(tt);
    const ap = new THREE.Mesh(new THREE.BoxGeometry(.78, .12, .56), flat('#7a5a8a')); ap.position.set(x, .72, -.32); g.add(ap);
    for (const dx of [-.36, .36]) for (const dz of [-.25, .25]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.05, .68, .05), flat('#4a3a6a')); l.position.set(x + dx, .34, -.32 + dz); g.add(l); }
    const hp = new THREE.Mesh(new THREE.CylinderGeometry(.19, .2, .05, 22), flat('#3a4066')); hp.position.set(x, .855, -.32); g.add(hp);
    const coil = new THREE.Mesh(new THREE.TorusGeometry(.15, .014, 8, 24), new THREE.MeshBasicMaterial({ color: HDR(2.6, .9, .35) })); coil.rotation.x = Math.PI / 2; coil.position.set(x, .885, -.32); coil.userData.noShadow = true; g.add(coil); dyn.coils.push(coil);
    const pot = new THREE.Mesh(new THREE.CylinderGeometry(.15, .14, .2, 24), flat('#c3cde6')); pot.position.set(x, .99, -.32); g.add(pot);
    const water = new THREE.Mesh(new THREE.CylinderGeometry(.135, .135, .01, 24), flat('#8fc8ff')); water.position.set(x, 1.092, -.32); water.userData.noShadow = true; g.add(water);
    for (const sd of [-1, 1]) { const h = new THREE.Mesh(new THREE.BoxGeometry(.08, .025, .05), flat('#2a2f52')); h.position.set(x + sd * .18, 1.05, -.32); g.add(h); }
  }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#b3c0ff', '#7a7096', 1.35));
  const key = new THREE.SpotLight('#ffd49a', 11, 10, 1.05, .7, 1.3); key.position.set(200, LAMP.y, LAMP.z); key.target.position.set(200, 0, -.9);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .6); fill.position.set(201, 3, 6); fill.target.position.set(200, 1, -1); L.add(fill); L.add(fill.target);
  scene.add(L); sets.deney = { g, L };
  shadows(g);
  dyn.bBeam = beam(scene, LAMP.toArray(), [200, .1, -.9], { r0: .14, r1: 1.7, color: '#ffe2a8', strength: .12 });
  dyn.bGlow = glow(scene, LAMP.toArray(), '#ffc978', 1.1, .5);
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  kahraman: { hair: '#3a2a24', cloth: '#f09a32', collar: true, height: 1.7 },
  anne: { hair: '#8a3a2a', cloth: '#8a4aa8', apron: true, buttons: '#f1e2bd', bodyW: 240, headW: 284, headH: 258, height: 1.64 },
  hoca: { beard: '#e4e4ee', beardLen: .7, hair: '#d9d9e4', cloth: '#f2f3f8', clothDark: '#b9bdd6', buttons: '#8a96c0', pocket: true, headW: 268, height: 1.74 },
  denek1: { hair: '#6a3a24', cloth: '#c8643a', pattern: 'stripes', height: 1.66 },
  denek2: { hair: '#2a2024', mustache: '#2a2024', cloth: '#3f9a6a', buttons: '#e0b050', height: 1.66, headW: 262, headH: 244 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  stare: { pos: [-.2, 1.3, 1.85], look: [-.2, 1.2, -.6], fov: 44 },
  clock: { pos: [CLOCK.x - .12, 2.1, .25], look: [CLOCK.x, CLOCK.y - .06, CLOCK.z], fov: 36 },
  wide: { pos: [.3, 1.55, 3.4], look: [.3, 1.4, -1], fov: 50 },
  anne: { pos: [ANNE.x - .3, 1.5, ANNE.z + 2.3], look: [ANNE.x - .02, 1.47, ANNE.z], fov: 44 },
  lab: { pos: [200, 1.4, 3.3], look: [200, 1.28, -.8], fov: 48 },
  d1: { pos: [199.52, 1.25, 1.6], look: [199.42, 1.2, -.8], fov: 44 },
  work: { pos: [.35, 1.55, 3.6], look: [.35, 1.45, -1], fov: 50 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: the hero nose to nose with the kettle -> the clock that will not move -> his bored face
    { t: 0, ...SHOT.stare, creep: .34, drift: .03 },
    { t: t('zaman') + .12, dur: .22, move: 'whip', ...SHOT.clock, creep: .3, drift: .01 },
    { t: t('geçmek') + .16, dur: .22, move: 'whip', pos: [CROUCH.x + .08, 1.25, 1.1], look: [CROUCH.x, 1.2, CROUCH.z], fov: 40, creep: .34, drift: .02 },
    { t: t('Bakın,') + .16, dur: .3, move: 'whip', ...SHOT.wide, creep: .26, drift: .05 },
    { t: t('çaydanlıktan') + .15, dur: .75, ...SHOT.stare, creep: .3, drift: .03 },
    // the mother laughs
    { t: t('Annen') + .3, dur: .3, move: 'whip', ...SHOT.anne, creep: .3, drift: .04 },
    { t: t('Şaka') + .22, dur: .3, move: 'whip', ...SHOT.wide, creep: .24, drift: .03 },
    // the experiment
    { t: t('psikologlar') + .28, dur: .3, move: 'whip', ...SHOT.lab, creep: .2, drift: .03 },
    { t: t('gruba') + .5, dur: .7, pos: [199.72, 1.38, 2.85], look: [199.7, 1.26, -.8], fov: 47, creep: .2, drift: .01 },
    { t: t('diğer') + .4, dur: .7, pos: [200.3, 1.4, 2.85], look: [200.32, 1.3, -.8], fov: 47, creep: .2, drift: .01 },
    { t: t('Aynı') + .3, dur: .5, ...SHOT.lab, creep: .16, drift: .015 },
    { t: t('kaynamayı') + .25, dur: .28, move: 'whip', ...SHOT.d1, creep: .3, drift: .02 },
    { t: t('uzun') + .1, dur: .26, move: 'whip', pos: [200, 1.5, 3.5], look: [200, 1.42, -.8], fov: 48, creep: .12, drift: .01 },
    // back in the kitchen: where the attention goes
    { t: t('Çünkü') + .25, dur: .3, move: 'whip', ...SHOT.stare, creep: .26, drift: .02 },
    { t: t('zamana') + .5, dur: .65, pos: [.4, 1.45, 2.45], look: [.52, 1.5, -1.6], fov: 46, creep: .18, drift: 0 },
    { t: t('Tıpkı') + .22, dur: .28, move: 'whip', ...SHOT.clock, creep: .32, drift: .01 },
    // busy hands
    { t: t('Bir', 2) + .25, dur: .3, move: 'whip', ...SHOT.work, creep: .22, drift: .01 },
    { t: t('Yani') + .25, dur: .3, move: 'whip', pos: [.75, 1.55, 2.3], look: [.78, 1.5, -1], fov: 44, creep: .22, drift: .01 },
    { t: t('çaydanlığa') + .2, dur: .28, move: 'whip', pos: [-.2, 1.32, 1.85], look: [-.2, 1.22, -.6], fov: 44, creep: .26, drift: .02 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('koydun,') + .05, .4); cp.kick(t('uzun') + .3, .5); cp.kick(t('uçup') + .05, .5); cp.kick(t('çaydanlığa') + .45, .7);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .8) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#33407a');
  buildMutfak(scene); buildDeney(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.clock = dynCard(scene, .74, .74, drawClock, { steps: 20 });
  const board = (text, bg, fg) => (c, w, h) => {
    c.lineJoin = 'round'; c.fillStyle = bg; c.strokeStyle = PLUM; c.lineWidth = 16; c.beginPath(); c.roundRect(12, 12, w - 24, h - 24, 26); c.fill(); c.stroke();
    c.fillStyle = fg; c.font = `900 ${h * .52}px "Arial Black", "Inter", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, w / 2, h * .54);
  };
  dyn.bekle = card(scene, .7, .28, board('BEKLE!', '#fbf7ee', '#c8323a'));
  dyn.watch = card(scene, .62, .72, drawStopwatch);
  dyn.th3 = card(scene, 1.0, .6, (c, w, h) => drawThought(c, w, h, 3));
  dyn.th1 = card(scene, .62, .5, (c, w, h) => drawThought(c, w, h, 1));
  dyn.dots = [.04, .06, .04, .06].map(r => card(scene, r * 2, r * 2, (c, w) => { c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 60; c.beginPath(); c.arc(w / 2, w / 2, w * .38, 0, 6.29); c.fill(); c.stroke(); }, { pw: 128 }));
  dyn.nums = [1, 2, 3, 4, 5].map(n => card(scene, .2, .22, (c, w, h) => {
    c.lineJoin = 'round'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .8}px "Arial Black", "Inter", sans-serif`;
    c.strokeStyle = PLUM; c.lineWidth = 34; c.strokeText(String(n), w / 2, h * .54); c.fillStyle = '#ffe15a'; c.fillText(String(n), w / 2, h * .54);
  }, { pw: 256 }));
  // steam from the spout once the water boils, and thin steam over the pots
  smokes.steam = new Smoke(scene, { color: '#f4f7ff', maxPoints: 700, H: ctx.H, near: .3 });
  const boilK = t => ramp(t, W('zaman', 2) - .1, W('uçup') + .4);
  for (const s of [1, 2, 3]) smokes.steam.wisps.push({ n: 70, size: .2, alpha: .6, speed: .42, seed: s * 2, on: t => dyn.where === 'mutfak' && t > W('zaman', 2) - .1, fade: boilK,
    path: (u, t) => [SPOUT.x + u * (.3 + s * .08) + Math.sin(u * 7 + t * 3 + s) * .06 * u, SPOUT.y + u * (.75 + s * .12), SPOUT.z + Math.cos(u * 5 + s) * .08 * u] });
  for (const [x, s] of [[D1.x, 4], [D2.x, 7]]) smokes.steam.wisps.push({ n: 30, size: .1, alpha: .28, speed: .2, seed: s, on: () => dyn.where === 'deney',
    path: (u, t) => [200 + x + Math.sin(u * 6 + t * 1.5 + s) * .05, 1.1 + u * .5, -.32 + Math.cos(u * 4 + s) * .04] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .02, 'whoosh'); cue(W('psikologlar') + .12, 'whoosh'); cue(W('Çünkü') + .1, 'whoosh');
  for (let k = 0; k < 4; k++) cue(.1 + k * .5, 'lock'); cue(W('koydun,') + .05, 'cut'); cue(W('ayırmıyorsun.') - .2, 'simmer', { dur: 1.2 });
  cue(W('Annen') + .1, 'rise', { dur: .35 }); cue(W('Şaka') + .05, 'rise', { dur: .35 }); cue(W('beklemeleri') + .02, 'lock'); cue(W('dört') - .02, 'shimmer');
  cue(W('kaynamayı') + .08, 'rise', { dur: .35 }); cue(W('uzun') + .3, 'boom'); cue(W('her'), 'lock'); cue(W('saniyeyi') + .15, 'lock'); cue(W('tek'), 'lock'); cue(W('tek', 2), 'lock'); cue(W('sayıyorsun.') + .1, 'lock');
  cue(W('Tıpkı') + .05, 'rise', { dur: .35 }); for (let k = 0; k < 4; k++) cue(W('gözünü', 2) + k * .75, 'lock');
  cue(W('Bir', 2) + .08, 'rise', { dur: .35 }); cue(W('dalıncaysa'), 'stir', { dur: W('Yani') - W('dalıncaysa') }); cue(W('zaman', 2), 'wind', { dur: 1.3 }); cue(W('uçup') + .05, 'shimmer');
  cue(W('Yani') + .05, 'rise', { dur: .35 }); cue(W('zaman', 2) + .2, 'simmer', { dur: DUR - W('zaman', 2) - .3 }); cue(W('çaydanlığa') + .45, 'boom');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'ZAMAN NEDEN GEÇMEZ?'); }

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const COOL = '#d6d6f6', WARM = '#ffcf8a';
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos);
  if (wob) m.rotation.z = Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04;
  return s;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 100 ? 'deney' : 'mutfak';
  vis('mutfak', where === 'mutfak'); vis('deney', where === 'deney'); dyn.where = where;
  dyn.aBeam.visible = dyn.aGlow.visible = where === 'mutfak'; dyn.bBeam.visible = dyn.bGlow.visible = where === 'deney';
  for (const c of Object.values(cast)) c.hide();
  for (const m of [dyn.bekle, dyn.watch, dyn.th3, dyn.th1, ...dyn.dots, ...dyn.nums]) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  dyn.clock.visible = false;
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const RT = V(1, 0, 0).applyQuaternion(cam.quaternion), UP = V(0, 1, 0).applyQuaternion(cam.quaternion);
  let look, grade = [1, 1, 1], face = [1, .985, .97];
  if (where === 'mutfak') {
    grade = [1.01, 1.0, 1.01];
    const tint = face.map((v, i) => v / grade[i]);
    const H = cast.kahraman, M = cast.anne;
    const inHook = t < A('Bakın,'), inL2 = !inHook && t < A('Annen'), inL3 = t > A('Annen') && t < A('Şaka'), inL4 = t > A('Şaka') && t < A('Bir'), inL7 = t > A('Çünkü') - .3 && t < A('Tıpkı'), inL8 = t > A('Tıpkı') && t < A('Bir', 2), inL9 = t > A('Bir', 2) && t < A('Yani'), inL10 = t > A('Yani');
    // ---- the flame, the kettle, the lid that starts to dance when the water boils
    const fire = t > A('koydun,') || inHook, boil = ramp(t, W('zaman', 2), W('uçup') + .3);
    dyn.flames.forEach((f, i) => { f.visible = fire; const s = fire ? (inHook ? 1 : backOut((t - A('koydun,')) / .25)) * (.85 + .25 * Math.sin(t * 31 + i * 2.1)) : 0; f.scale.set(1, Math.max(.01, s), 1); });
    dyn.fire.intensity = fire ? .45 + .1 * Math.sin(t * 23) : 0;
    dyn.lid.position.y = .315 + boil * Math.abs(Math.sin(t * 34)) * .022; dyn.lid.rotation.z = boil * Math.sin(t * 29) * .1;
    dyn.kettle.rotation.z = boil * Math.sin(t * 41) * .012;
    // ---- the wall clock: it crawls while he stares, it races while he is busy
    let min = 12 + t * .02, sec = t * .35 % 60;
    if (inL8) { min = 12.4 + Math.sin(t * 37) * .12 * ramp(t, A('yelkovanın'), A('yelkovanın') + .3); sec = 21 + Math.sin(t * 9) * .5; }
    if (t > A('dalıncaysa')) { const k = t - A('dalıncaysa'), acc = k * k * 9; min = (12.4 + acc * 1.6) % 60; sec = (acc * 31) % 60; }
    dyn.clock.userData.set(min, sec); dyn.clock.visible = true; dyn.clock.position.copy(CLOCK); dyn.clock.quaternion.identity(); dyn.clock.scale.setScalar(1);
    // ---- the hero
    const endK = t > W('çaydanlığa') + .06;
    const crouch = inHook ? 1 : inL2 ? ramp(t, A('gözünü'), A('gözünü') + .45) : inL3 ? 1 : inL4 ? 1 - ramp(t, A('Şaka'), A('Şaka') + .3) : inL7 ? 1 - .5 * ramp(t, A('zamana') - .15, A('zamana') + .35) : inL8 ? .5 : inL10 && endK ? 1 : 0;
    const atWork = inL9 || (inL10 && !endK), slide = atWork ? 1 : 0;
    const hx = lerpN(CROUCH.x, WORK.x, slide), hy = CROUCH.y * crouch;
    const stare = { expr: 'focused', look: -.92, lookY: .12, gazeX: -1, brow: -.35, lid: .12, armL: [16, 10], armR: [16, 10] };
    let hp = { expr: 'neutral', look: -.2, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(1, A('koydun,'), A('gözünü'), A('"Baktıkça'), A('Şaka'), A('zamana'), A('dalıncaysa'), A('kaynasın'), A('çaydanlığa')) };
    if (inHook) hp = t < A('geçmek') ? { ...stare, blink: 0 } : { ...stare, expr: 'worried', lid: .5, look: -.6, brow: .2, sweat: 1, blink: bl(1) };
    if (inL2) hp = t < A('koydun,') ? { ...hp, look: -.6, lookY: .5, armL: [70, 20] } : t < A('gözünü') ? { ...hp, expr: 'smile', look: -.6, lookY: .5 } : { ...stare, blink: 0 };
    if (inL3) hp = t < A('"Baktıkça') ? { ...stare, blink: bl(1) } : { ...stare, expr: 'angry', look: .7, gazeX: 1, lookY: -.2, brow: -.5 };
    if (inL4) hp = { ...hp, expr: 'worried', look: .75, brow: .4, armR: [150, 28] };
    if (inL7) {
      const k = ramp(t, A('zamana') - .15, A('zamana') + .25), count = t > A('her');
      hp = { ...stare, look: lerpN(-.92, .7, k), lookY: lerpN(.12, -.55, k), gazeX: lerpN(-1, 1, k), gazeY: -k, expr: count ? 'worried' : 'focused', brow: count ? .5 : -.35, mouth: count ? flap(env, t) * .7 : 0, sweat: count ? 1 : 0, blink: bl(1, A('zamana')) };
    }
    if (inL9) { const w = t * 15; hp = { ...hp, expr: 'smile', look: .35, lookY: .6, gazeY: 1, brow: .3, propR: 'spoon', armR: [58 + Math.sin(w) * 9, -62 + Math.cos(w) * 12], armL: [40, -80], lean: 2 + Math.sin(w) * .8, bob: Math.sin(t * 7.5) * 2 }; }
    if (inL10) { const w = t * 15, see = t > A('kaynasın'); hp = see ? { ...hp, expr: t > A('çaydanlığa') ? 'grin' : 'surprised', look: -.85, lookY: .15, gazeX: -1, brow: 1, mouth: t > A('çaydanlığa') ? 0 : .5, propR: 'spoon', armR: [70, -40], armL: t > A('çaydanlığa') ? [150, 26] : [40, -80] }
      : { ...hp, expr: 'smile', look: .35, lookY: .6, gazeY: 1, propR: 'spoon', armR: [58 + Math.sin(w) * 9, -62 + Math.cos(w) * 12], armL: [40, -80], lean: 2 }; }
    if (inL10 && endK) hp = { ...stare, expr: 'grin', look: -.85, brow: .9, lid: 0, blink: bl(1, W('çaydanlığa') + .06) };
    H.show(); H.place(hx, hy, atWork ? WORK.z : CROUCH.z, cam, tint);
    H.draw({ ...hp, lit: -1, shade: COOL, rim: { color: WARM, a: .4 } }); H.castFrom(dyn.keyP);
    dyn.bowl.visible = atWork;
    // ---- the mother: apron, wooden spoon, knows everything
    const here = t > A('Annen') - .25;
    if (here && !inL7 && !inL8) {
      const enter = inL3 ? backOut((t - A('Annen') + .25) / .3) : 1;
      const laugh = (t > A('gülüyor:') - .1 && t < A('"Baktıkça') - .04) || (inL10 && t > A('çaydanlığa')), talk = t > A('"Baktıkça') - .04 && t < A('o!"') + .3;
      let mp = { expr: 'smug', look: -.6, armL: [16, 10], armR: [34, -104], propR: 'spoon', blink: bl(2, A('gülüyor:') - .1, A('"Baktıkça'), A('Şaka'), A('kaynasın'), A('çaydanlığa')) };
      if (laugh) mp = { ...mp, expr: 'laugh', laughMarks: .9, mouth: .5 + .5 * Math.abs(Math.sin(t * 13)), bob: -Math.abs(Math.sin(t * 13)) * 10, armL: [28, -100] };
      if (talk) mp = { ...mp, expr: 'smug', brow: .6, mouth: flap(env, t), armR: [142, 22 + 12 * Math.sin(t * 12)] };
      if (inL4) mp = { ...mp, expr: 'proud', lid: .15, look: -.5 };
      if (inL9) mp = { ...mp, expr: 'smile', look: -.5, lookY: .2 };
      if (inL10 && !laugh) mp = { ...mp, expr: t > A('kaynasın') ? 'proud' : 'smile', lid: t > A('kaynasın') ? .15 : 0, look: -.7, armR: t > A('kaynasın') ? [112, 14] : [34, -104] };
      M.show(); M.place(ANNE.x + (1 - enter) * 1.2, 0, ANNE.z, cam, tint);
      M.draw({ ...mp, lit: -1, shade: COOL, rim: { color: WARM, a: .4 } }); M.castFrom(dyn.keyP);
    }
    // ---- counting the seconds
    if (inL7) {
      const head = V(hx, 1.49 + hy, CROUCH.z), at = (r, u) => head.clone().addScaledVector(RT, r).addScaledVector(UP, u);
      [['her', 1, -.1, .4], ['saniyeyi', 1, .08, .54], ['tek', 1, .26, .58], ['tek', 2, .42, .5], ['sayıyorsun.', 1, .52, .34]].forEach(([w, n, r, u], i) => { const t0 = A(w, n) + (w === 'saniyeyi' ? .15 : w === 'sayıyorsun.' ? .1 : 0); const s = popCard(dyn.nums[i], t0, t, at(r, u), 1); if (s) dyn.nums[i].position.addScaledVector(UP, Math.sin((t - t0) * 3) * .012); });
    }
    const f = t > W('zaman') + .1 && t < W('geçmek') + .1 || inL8 ? CLOCK : inL3 ? V(ANNE.x, 1.45, ANNE.z) : atWork ? V(WORK.x, 1.45, WORK.z) : t > A('çaydanlığa') ? KET.clone().setY(1.15) : V(hx, 1.3, CROUCH.z);
    look = { focus: cam.position.distanceTo(f), coc: 5, range: 2.3, sat: 1.24, lift: [.085, .085, .15], bloom: .85, vignette: .22 };
  } else {
    // ---- the experiment: one group told to wait for the boil, the other told nothing
    grade = [1.0, .995, 1.02];
    const tint = face.map((v, i) => v / grade[i]);
    const told = t > A('beklemeleri'), after = t > A('Aynı'), felt = t > A('uzun');
    dyn.coils.forEach((c, i) => c.scale.setScalar(1 + .02 * Math.sin(t * 9 + i)));
    const R = cast.hoca, A1 = cast.denek1, A2 = cast.denek2;
    // the researcher
    let rp = { expr: 'smug', look: 0, armL: [16, 10], armR: [16, 10], blink: bl(3, A('Bir'), A('diğer'), A('Aynı'), A('uzun')) };
    if (t > A('Bir') && t < A('diğer')) rp = { ...rp, expr: told ? 'angry' : 'neutral', look: -.7, brow: told ? -.4 : .3, mouth: told ? .4 : 0, armL: [104, told ? 30 : 10] };
    if (t > A('diğer') && !after) rp = { ...rp, expr: 'neutral', look: .7, lid: .3, armR: [30, -96], armL: [30, -100] };
    if (after) rp = { ...rp, expr: felt ? 'surprised' : 'proud', look: felt ? -.5 : 0, brow: felt ? .9 : .2, armR: [150, 22] };
    if (!(t > W('kaynamayı') + .11 && t < W('uzun') - .03)) { R.show(); R.place(200 + HOCA.x, 0, HOCA.z, cam, tint);
      R.draw({ ...rp, lit: 1, shade: COOL, rim: { color: WARM, a: .4 } }); R.castFrom(LAMP); }
    // the one who waits: nose on the pot
    const jit = told ? Math.sin(t * 40) * .004 : 0;
    let p1 = { expr: 'neutral', look: .1, lookY: .5, armL: [16, 10], armR: [16, 10], blink: bl(4, A('beklemeleri'), A('kaynamayı'), A('uzun')) };
    if (told) p1 = { ...p1, expr: 'focused', lookY: .75, gazeY: 1, brow: -.4, lid: .1, blink: 0 };
    if (t > A('kaynamayı')) p1 = { ...p1, expr: 'worried', sweat: 1, brow: .5, lid: .35, blink: bl(4), mouth: felt ? .3 : 0 };
    const c1 = told ? ramp(t, A('beklemeleri'), A('beklemeleri') + .3) : 0;
    A1.show(); A1.place(200 + D1.x + jit, D1.y * c1, D1.z, cam, tint);
    A1.draw({ ...p1, lit: 1, shade: COOL, rim: { color: WARM, a: .42 } }); A1.castFrom(LAMP);
    // the one who was told nothing: whistling at the ceiling
    let p2 = { expr: 'neutral', look: -.1, lookY: .3, armL: [16, 10], armR: [16, 10], blink: bl(5, A('diğer'), A('hiçbir'), A('uzun')) };
    if (t > A('diğer')) p2 = { ...p2, expr: 'smile', look: .45, lookY: -.5, gazeY: -.6, brow: .4, mouth: t > A('hiçbir') ? (Math.floor(t * 6) % 2 ? .28 : .18) : 0, armL: [26, -150], armR: [26, -150], bob: Math.sin(t * 6) * 3 };
    A2.show(); A2.place(200 + D2.x, 0, D2.z, cam, tint);
    A2.draw({ ...p2, lit: -1, shade: COOL, rim: { color: WARM, a: .42 } }); A2.castFrom(LAMP);
    if (told && t < A('Aynı') + .1) popCard(dyn.bekle, A('beklemeleri'), t, V(200 + D1.x + .04, 1.82, D1.z));
    if (after && t < W('kaynamayı') + .25) { const s = popCard(dyn.watch, A('dört') - .12, t, V(200, 2.2, -1.4), 1.7); if (s) dyn.watch.rotation.z += Math.sin(t * 5) * .03; }
    if (felt) {
      const h1 = V(200 + D1.x, 1.49 + D1.y, D1.z), h2 = V(200 + D2.x, 1.49, D2.z), t0 = A('uzun');
      dyn.dots.slice(0, 2).forEach((m, i) => popCard(m, t0 + i * .08, t, h1.clone().addScaledVector(RT, .12 + i * .08).addScaledVector(UP, .32 + i * .13), 1, false));
      const s = popCard(dyn.th3, t0 + .18, t, h1.clone().addScaledVector(RT, .3).addScaledVector(UP, .82)); if (s) dyn.th3.position.y += Math.sin(t * 2) * .012;
      dyn.dots.slice(2).forEach((m, i) => popCard(m, t0 + .3 + i * .08, t, h2.clone().addScaledVector(RT, -.1 - i * .06).addScaledVector(UP, .32 + i * .13), 1, false));
      popCard(dyn.th1, t0 + .48, t, h2.clone().addScaledVector(RT, -.12).addScaledVector(UP, .82));
    }
    look = { focus: cam.position.distanceTo(V(200, 1.3, -.95)), coc: 4, range: 3.2, sat: 1.2, lift: [.085, .085, .15], bloom: .9, vignette: .22 };
  }
  for (const s of Object.values(smokes)) s.update(t);
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
