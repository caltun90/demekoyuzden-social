// Tüyler neden diken diken olur? Demek O Yüzden günlük Short (yumurta stili), 24 Kasım 2026.
// Bilgi: her tüyün dibinde küçük bir kas (arrector pili) var; soğukta sempatik sinirler bu kası kasar, tüy dikilir.
// Kürklü hayvanlarda kabaran kürk araya hava hapseder ve yalıtım yapar; insanda kürk kalmadığı için ısıtmaz. Kaynaklar SCRIPT.md'de.
// Setler: DURAK (x≈0) kış akşamı, mavi duvar + sokak lambası + sıcak pencereler; TÜY DİBİ (x≈200) deri üstünde dev tüyler,
// halat çeken "kas" işçileri ve "sinir" ikaz lambası (benzetme).
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat, rng } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-24-tuyler-diken-diken';
export const FPS = 30;
export let DUR = 35.4;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lerpN = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;
const spring = x => x <= 0 ? 0 : 1 - Math.exp(-7 * x) * Math.cos(20 * x);
let W, cast = {}, sets = {}, dyn = {}, smokes = {};

function wordTimes(words) {
  const norm = s => s.toLocaleLowerCase('tr-TR').replace(/[^\p{L}\p{N}]/gu, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w); };
}
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus|Icosahedron/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function card(scene, w, h, draw, { pw = 512, hdr = null, layer = 1 } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); draw(c.getContext('2d'), c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false, color: hdr || 0xffffff }));
  m.layers.set(layer); m.renderOrder = 20; m.visible = false; scene.add(m); return m;
}
// a card that is redrawn when its value changes (the drawing is cached, the position never is)
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
// the magnifier: skin with hairs. k = 0 hairs lie flat, k = 1 they stand and every hair sits on a goosebump
function drawLens(g, w, h, k) {
  g.lineCap = g.lineJoin = 'round';
  const cx = w * .46, cy = w * .46, r = w * .40;
  g.strokeStyle = PLUM; g.lineWidth = 46; g.beginPath(); g.moveTo(cx + r * .78, cy + r * .78); g.lineTo(w * .93, w * .93); g.stroke();
  g.strokeStyle = '#a8683a'; g.lineWidth = 26; g.beginPath(); g.moveTo(cx + r * .84, cy + r * .84); g.lineTo(w * .93, w * .93); g.stroke();
  g.save(); g.beginPath(); g.arc(cx, cy, r, 0, 6.29); g.clip();
  g.fillStyle = '#d6e8ff'; g.fillRect(0, 0, w, w);
  const ys = cy + r * .34, surf = () => { g.beginPath(); g.moveTo(0, ys + 16); g.quadraticCurveTo(cx, ys - 16, w, ys + 16); };
  surf(); g.lineTo(w, w); g.lineTo(0, w); g.closePath(); g.fillStyle = '#f6bda4'; g.fill();
  g.fillStyle = '#eaa58c'; for (let i = 0; i < 9; i++) { g.beginPath(); g.arc(cx - r + i * r * .26 + 14, ys + 62 + (i % 3) * 30, 6, 0, 6.29); g.fill(); }
  g.strokeStyle = PLUM; g.lineWidth = 10; surf(); g.stroke();
  const kk = Math.max(0, k), kb = Math.min(1, kk);
  for (let i = 0; i < 5; i++) {
    const x = cx - r * .7 + i * r * .35, y0 = ys - 8 + Math.abs(i - 2) * 4, bh = 30 * kb;
    if (bh > 1.5) { g.fillStyle = '#f6bda4'; g.strokeStyle = PLUM; g.lineWidth = 9; g.beginPath(); g.ellipse(x, y0 + 8, 36, bh, 0, Math.PI, 0); g.fill(); g.stroke(); g.fillRect(x - 31, y0 + 3, 62, 12); }
    const a = (70 - 64 * kk + (i % 2 ? 3 : -3)) * Math.PI / 180, L = r * (.6 + (i % 2) * .08), bx = x, by = y0 + 6 - bh * .85;
    g.strokeStyle = '#3a2420'; g.lineWidth = 15;
    g.beginPath(); g.moveTo(bx, by); g.quadraticCurveTo(bx + Math.sin(a) * L * .5, by - Math.cos(a) * L * .5 - 8 * (1 - kb), bx + Math.sin(a) * L, by - Math.cos(a) * L); g.stroke();
  }
  g.strokeStyle = 'rgba(255,255,255,.8)'; g.lineWidth = 13; g.beginPath(); g.arc(cx, cy, r * .78, Math.PI * 1.12, Math.PI * 1.42); g.stroke();
  g.restore();
  g.strokeStyle = PLUM; g.lineWidth = 34; g.beginPath(); g.arc(cx, cy, r, 0, 6.29); g.stroke();
  g.strokeStyle = '#f0c050'; g.lineWidth = 13; g.beginPath(); g.arc(cx, cy, r, 0, 6.29); g.stroke();
}
// the cat on the bench: puff 0 = sleek, 1 = fur fluffed up; happy 1 = eyes shut in bliss
function drawCat(g, w, h, puff, happy) {
  g.lineCap = g.lineJoin = 'round';
  const cx = w * .46, base = h * .93, fur = '#f2a44c', dk = '#cf7a2c', s = 1 + puff * .34;
  const blob = (x, y, rx, ry) => { g.beginPath(); const N = 44; for (let i = 0; i <= N; i++) { const a = i / N * 6.283, sp = 1 + (i % 2 ? .15 : -.03) * puff, px = x + Math.cos(a) * rx * sp, py = y + Math.sin(a) * ry * sp; i ? g.lineTo(px, py) : g.moveTo(px, py); } g.closePath(); };
  const tail = () => { g.beginPath(); g.moveTo(cx + w * .16, base - h * .07); g.quadraticCurveTo(cx + w * .43, base - h * .04, cx + w * .38, base - h * .36); };
  g.strokeStyle = PLUM; g.lineWidth = 50 + puff * 34; tail(); g.stroke(); g.strokeStyle = fur; g.lineWidth = 30 + puff * 34; tail(); g.stroke();
  g.fillStyle = fur; g.strokeStyle = PLUM; g.lineWidth = 12;
  const by = base - h * .23, brx = w * .19 * s, bry = h * .24 * (1 + puff * .1);
  blob(cx, by, brx, bry); g.fill(); g.stroke();
  g.save(); blob(cx, by, brx, bry); g.clip(); g.strokeStyle = dk; g.lineWidth = 12; for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(cx + brx * .45, by - bry * .5 + i * bry * .38); g.quadraticCurveTo(cx + brx * .8, by - bry * .4 + i * bry * .38, cx + brx * 1.1, by - bry * .55 + i * bry * .38); g.stroke(); }
  g.fillStyle = '#fff3e2'; g.beginPath(); g.ellipse(cx, by + bry * .25, brx * .5, bry * .6, 0, 0, 6.29); g.fill(); g.restore();
  for (const sd of [-1, 1]) { g.fillStyle = PLUM; g.beginPath(); g.ellipse(cx + sd * brx * .45, base - 8, 26, 13, 0, 0, 6.29); g.fill(); }
  const hy = base - h * .56 - puff * h * .03, hr = w * .165 * (1 + puff * .2);
  g.strokeStyle = PLUM; g.lineWidth = 12;
  for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(cx + sd * hr * 1.0, hy - hr * .3); g.lineTo(cx + sd * hr * .82, hy - hr * 1.4); g.lineTo(cx + sd * hr * .18, hy - hr * .82); g.closePath(); g.fillStyle = fur; g.fill(); g.stroke();
    g.fillStyle = '#f7c0b0'; g.beginPath(); g.moveTo(cx + sd * hr * .82, hy - hr * .55); g.lineTo(cx + sd * hr * .76, hy - hr * 1.1); g.lineTo(cx + sd * hr * .42, hy - hr * .78); g.closePath(); g.fill(); }
  g.fillStyle = fur; blob(cx, hy, hr * 1.14, hr * .96); g.fill(); g.stroke();
  g.save(); blob(cx, hy, hr * 1.14, hr * .96); g.clip(); g.strokeStyle = dk; g.lineWidth = 11; for (const dx of [-.3, 0, .3]) { g.beginPath(); g.moveTo(cx + dx * hr, hy - hr * 1.0); g.lineTo(cx + dx * hr * .8, hy - hr * .58); g.stroke(); } g.restore();
  g.strokeStyle = PLUM; g.fillStyle = PLUM; g.lineWidth = 10;
  for (const sd of [-1, 1]) {
    const ex = cx + sd * hr * .42, ey = hy - hr * .05;
    if (happy > .5) { g.beginPath(); g.moveTo(ex - hr * .2, ey + hr * .06); g.quadraticCurveTo(ex, ey - hr * .2, ex + hr * .2, ey + hr * .06); g.stroke(); }
    else { g.fillStyle = '#ffffff'; g.beginPath(); g.arc(ex, ey, hr * .23, 0, 6.29); g.fill(); g.stroke(); g.fillStyle = PLUM; g.beginPath(); g.arc(ex + 3, ey + 2, hr * .09, 0, 6.29); g.fill(); }
  }
  g.fillStyle = '#e06a74'; g.beginPath(); g.moveTo(cx - 11, hy + hr * .26); g.lineTo(cx + 11, hy + hr * .26); g.lineTo(cx, hy + hr * .4); g.closePath(); g.fill();
  g.lineWidth = 8; g.beginPath();
  if (happy > .5) { g.moveTo(cx - hr * .26, hy + hr * .46); g.quadraticCurveTo(cx - hr * .12, hy + hr * .62, cx, hy + hr * .44); g.quadraticCurveTo(cx + hr * .12, hy + hr * .62, cx + hr * .26, hy + hr * .46); }
  else { g.moveTo(cx - hr * .2, hy + hr * .6); g.quadraticCurveTo(cx - hr * .1, hy + hr * .5, cx, hy + hr * .6); g.quadraticCurveTo(cx + hr * .1, hy + hr * .7, cx + hr * .2, hy + hr * .6); }
  g.stroke();
  g.lineWidth = 5; for (const sd of [-1, 1]) for (const dy of [-.04, .12]) { g.beginPath(); g.moveTo(cx + sd * hr * .7, hy + hr * (.3 + dy)); g.lineTo(cx + sd * hr * 1.45, hy + hr * (.2 + dy * 2.2)); g.stroke(); }
}
function cloudPath(c, w, h) {
  c.beginPath(); for (let k = 0; k < 9; k++) { const a = k / 9 * 6.283; c.arc(w / 2 + Math.cos(a) * w * .3, h / 2 + Math.sin(a) * h * .28, w * .13, 0, 6.29); }
}
// the thought: the same hero with a thick coat of fur (full = 1), or the fur gone and a few tufts falling (full = 0)
function drawCloud(c, w, h, full) {
  c.lineJoin = c.lineCap = 'round'; c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 12;
  cloudPath(c, w, h); c.stroke(); cloudPath(c, w, h); c.fill(); c.beginPath(); c.ellipse(w / 2, h / 2, w * .37, h * .33, 0, 0, 6.29); c.fill();
  const cx = w / 2, cy = h * .52;
  if (full) {
    c.fillStyle = '#9a6238'; c.strokeStyle = PLUM; c.lineWidth = 9; c.beginPath();
    const N = 36; for (let i = 0; i <= N; i++) { const a = i / N * 6.283, sp = 1 + (i % 2 ? .16 : -.04), rx = w * .15 * sp, ry = h * .27 * sp; const px = cx + Math.cos(a) * rx, py = cy + h * .02 + Math.sin(a) * ry; i ? c.lineTo(px, py) : c.moveTo(px, py); }
    c.closePath(); c.fill(); c.stroke();
    c.fillStyle = '#ffffff'; c.beginPath(); c.ellipse(cx, cy - h * .09, w * .085, h * .1, 0, 0, 6.29); c.fill(); c.stroke();
    c.fillStyle = PLUM; for (const sd of [-1, 1]) { c.beginPath(); c.arc(cx + sd * w * .032, cy - h * .1, 6, 0, 6.29); c.fill(); }
    c.lineWidth = 6; c.beginPath(); c.moveTo(cx - w * .03, cy - h * .045); c.quadraticCurveTo(cx, cy - h * .015, cx + w * .03, cy - h * .045); c.stroke();
  } else {
    c.fillStyle = '#9a6238'; c.strokeStyle = PLUM; c.lineWidth = 7;
    for (const [dx, dy, r] of [[-.16, -.08, .9], [.02, .1, 1.1], [.17, -.04, .8], [-.05, -.14, .7], [.1, .14, .7]]) { c.save(); c.translate(cx + dx * w, cy + dy * h); c.rotate(dx * 9); c.beginPath(); c.moveTo(0, -16 * r); c.quadraticCurveTo(14 * r, 0, 0, 16 * r); c.quadraticCurveTo(-14 * r, 0, 0, -16 * r); c.fill(); c.stroke(); c.restore(); }
  }
}

// ---------------------------------------------------------------- DURAK (x = 0), kış akşamı
const HERO = { x: -.3, z: -.7 }, AMCA = { x: .58, z: -.85 }, CAT = { x: -1.05, y: .49, z: -1.72 };
const LENS = V(HERO.x + .3, 1.12, HERO.z + .24), LAMP = V(.95, 2.86, -1.5);
function buildDurak(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(14, 6), painted(stoneTex({ base: '#dce7f5', seam: '#a4b6d6', bw: 128, bh: 128, rep: [7, 3] })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, -1); g.add(fl);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(14, 9), flat('#55628f'));
  road.rotation.x = -Math.PI / 2; road.position.set(0, -.12, 6.45); g.add(road);
  const curb = new THREE.Mesh(new THREE.BoxGeometry(14, .16, .2), flat('#c6d3ea')); curb.position.set(0, -.06, 2.0); g.add(curb);
  // the building behind the stop: cool brick, a snowy ledge, warm windows high up (they glow: brighter than white)
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(14, 6), painted(stoneTex({ base: '#8fa5d2', seam: '#6278ac', bw: 96, bh: 40, rep: [7, 4] })));
  wall.position.set(0, 3, -2.7); g.add(wall);
  const dado = new THREE.Mesh(new THREE.BoxGeometry(14, .9, .08), painted(stoneTex({ base: '#6f86b8', seam: '#51669a', bw: 128, bh: 128, rep: [14, 1] }))); dado.position.set(0, .45, -2.66); g.add(dado);
  const ledge = new THREE.Mesh(new THREE.BoxGeometry(14, .1, .22), flat('#eef3fb')); ledge.position.set(0, 2.3, -2.6); g.add(ledge);
  const pane = new THREE.MeshBasicMaterial({ color: HDR(1.75, 1.2, .5) }), fr = flat('#f1ece2');
  for (const wx of [-2.6, -1.05, 1.3, 2.85]) {
    const p = new THREE.Mesh(new THREE.PlaneGeometry(.78, .98), pane); p.position.set(wx, 2.98, -2.64); g.add(p);
    for (const [w, h, x, y] of [[.94, .08, 0, .53], [.94, .1, 0, -.53], [.08, 1.1, -.43, 0], [.08, 1.1, .43, 0], [.05, .98, 0, 0], [.78, .05, 0, .08]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .1), fr); b.position.set(wx + x, 2.98 + y, -2.6); b.userData.noShadow = true; g.add(b); }
    const sn = new THREE.Mesh(new THREE.BoxGeometry(1.0, .06, .16), flat('#ffffff')); sn.position.set(wx, 2.42, -2.56); g.add(sn);
  }
  // the bench with a cushion of snow on its back
  const wood = painted(woodTex({ base: '#9a6a44' }));
  const seat = new THREE.Mesh(new THREE.BoxGeometry(1.0, .06, .38), wood); seat.position.set(CAT.x, .46, CAT.z); g.add(seat);
  const backr = new THREE.Mesh(new THREE.BoxGeometry(1.0, .32, .05), wood); backr.position.set(CAT.x, .82, CAT.z - .2); g.add(backr);
  const bsn = new THREE.Mesh(new THREE.BoxGeometry(1.02, .06, .09), flat('#ffffff')); bsn.position.set(CAT.x, 1.01, CAT.z - .2); g.add(bsn);
  for (const dx of [-.44, .44]) for (const dz of [-.15, .15]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.05, .46, .05), flat('#2f3350')); l.position.set(CAT.x + dx, .23, CAT.z + dz); g.add(l); }
  // the stop sign pole and the street lamp (the key light of the set)
  const metal = flat('#3a4066');
  const sp = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, 2.6, 10), flat('#c8d2e8')); sp.position.set(.12, 1.3, -2.3); g.add(sp);
  const lp = new THREE.Mesh(new THREE.CylinderGeometry(.045, .06, 3.0, 12), metal); lp.position.set(1.42, 1.5, -2.05); g.add(lp);
  const la = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, .78, 8), metal); la.position.set(1.18, 2.98, -1.77); la.rotation.set(Math.PI / 2, 0, 0); la.rotation.order = 'YXZ'; la.rotation.y = Math.atan2(LAMP.x - 1.42, LAMP.z + 2.05); g.add(la);
  const lh = new THREE.Mesh(new THREE.CylinderGeometry(.06, .2, .16, 20), flat('#2f8f9a')); lh.position.set(LAMP.x, LAMP.y + .12, LAMP.z); g.add(lh);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(.075, 14, 10), new THREE.MeshBasicMaterial({ color: HDR(2.6, 1.9, .9) })); bulb.position.copy(LAMP); g.add(bulb);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#9fb2ff', '#5a5c96', 1.75));
  const key = new THREE.SpotLight('#ffcf8a', 13, 9, .95, .6, 1.3); key.position.copy(LAMP); key.target.position.set(.05, 0, -.75);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const win = new THREE.PointLight('#ffc070', 2.2, 5, 1.5); win.position.set(0, 2.9, -2.1); L.add(win);
  const moon = new THREE.DirectionalLight('#a9bcff', .9); moon.position.set(-3, 5, 4); moon.target.position.set(0, 0, -1); L.add(moon); L.add(moon.target);
  scene.add(L); sets.durak = { g, L };
  shadows(g);
  dyn.aBeam = beam(scene, LAMP.toArray(), [.3, .1, -.8], { r0: .12, r1: 1.25, color: '#ffe2a8', strength: .13 });
  dyn.aGlow = glow(scene, LAMP.toArray(), '#ffc978', 1.0, .5);
}

// ---------------------------------------------------------------- TÜY DİBİ (x = 200): the skin, seen from an ant's height
const HAIRS = [{ x: -.1, z: -1.0, len: 2.2, r: .085 }, { x: 1.4, z: -3.6, len: 2.1, r: .08 }, { x: -1.7, z: -4.7, len: 2.3, r: .08 }, { x: 2.5, z: -5.6, len: 2.2, r: .075 }, { x: -2.9, z: -6.6, len: 2.3, r: .075 }, { x: .5, z: -7.4, len: 2.3, r: .07 }];
const HAZ = .9;                 // the hairs lie toward screen right and away from the camera (azimuth, rad)
const KAS = [{ x: -.75, z: -1.0 }, { x: .95, z: -3.6 }];
const BEACON = V(200.5, 2.62, -2.6);
function buildDeri(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), painted(stoneTex({ base: '#ffdccb', seam: '#f0b29c', bw: 128, bh: 128, rep: [14, 9], seed: 5 })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, -4); g.add(fl);
  const bc = document.createElement('canvas'); bc.width = 64; bc.height = 512; const bg = bc.getContext('2d');
  const gr = bg.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#5f86d8'); gr.addColorStop(.55, '#a9c6f2'); gr.addColorStop(1, '#eaf2ff'); bg.fillStyle = gr; bg.fillRect(0, 0, 64, 512);
  const bt = new THREE.CanvasTexture(bc); bt.colorSpace = THREE.SRGBColorSpace;
  const sky = new THREE.Mesh(new THREE.PlaneGeometry(60, 16), new THREE.MeshBasicMaterial({ map: bt })); sky.position.set(0, 7.5, -13.5); g.add(sky);
  // hairs: tapered poles hinged at the root; each has a goosebump that swells under it
  dyn.hairs = HAIRS.map(hh => {
    const piv = new THREE.Group(); piv.position.set(hh.x, 0, hh.z); g.add(piv);
    const geo = new THREE.CylinderGeometry(hh.r * .28, hh.r, hh.len, 14); geo.translate(0, hh.len / 2, 0);
    const m = new THREE.Mesh(geo, flat('#4a3028')); piv.add(m);
    const bump = new THREE.Mesh(new THREE.SphereGeometry(.42, 24, 12, 0, 6.283, 0, Math.PI / 2), flat('#ffdccb')); bump.position.set(hh.x, 0, hh.z); bump.receiveShadow = true; g.add(bump);
    return { ...hh, piv, bump };
  });
  // the "nerve": an alarm lamp on a post, with its name on a board
  const post = new THREE.Mesh(new THREE.CylinderGeometry(.04, .05, 2.5, 10), flat('#5a4a7a')); post.position.set(BEACON.x - 200, 1.25, BEACON.z); g.add(post);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(.16, .16, .06, 20), flat('#3a3058')); cap.position.set(BEACON.x - 200, 2.5, BEACON.z); g.add(cap);
  dyn.beaconMat = new THREE.MeshBasicMaterial({ color: '#8a90b8' });
  const lampB = new THREE.Mesh(new THREE.SphereGeometry(.14, 18, 12), dyn.beaconMat); lampB.position.set(BEACON.x - 200, BEACON.y, BEACON.z); lampB.userData.noShadow = true; g.add(lampB);
  // ropes from the workers' hands to the hairs
  dyn.ropes = KAS.map(() => { const r = new THREE.Mesh(new THREE.CylinderGeometry(.013, .013, 1, 8), flat('#f1e2bd')); r.userData.noShadow = true; scene.add(r); return r; });
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#dfe6ff', '#c79aa8', 1.7));
  const sunDir = V(.55, -1, -.6).normalize(); dyn.bSun = sunDir;
  const sun = new THREE.DirectionalLight('#ffe1b0', 2.3); sun.position.copy(V(200, 0, -2).addScaledVector(sunDir, -9)); sun.target.position.set(200, 0, -2);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: .5, far: 22 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
  L.add(sun); L.add(sun.target);
  dyn.beaconLight = new THREE.PointLight('#ffd66a', 0, 6, 1.4); dyn.beaconLight.position.copy(BEACON); L.add(dyn.beaconLight);
  scene.add(L); sets.deri = { g, L };
  shadows(g);
  dyn.beaconGlow = glow(scene, BEACON.toArray(), '#ffd066', 1.3, 0);
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  kahraman: { hair: '#3a2a24', cloth: '#f09a32', collar: true, height: 1.7 },
  amca: { mustache: '#6a5a58', hair: '#8a8088', hat: 'kulah', hatColor: '#c23a40', cloth: '#3d7a5a', buttons: '#e0b050', pocket: true, bodyW: 236, headW: 282, headH: 256, height: 1.78 },
  kas1: { mustache: '#2a1c18', hat: 'kulah', hatColor: '#e8b23e', cloth: '#d8483a', pocket: true, headW: 272, headH: 250, height: 1.5 },
  kas2: { beard: '#4a3028', beardLen: .62, hat: 'kulah', hatColor: '#e8b23e', cloth: '#d8483a', headW: 262, height: 1.46 },
};
const POS = { kahraman: [HERO.x, 0, HERO.z], amca: [AMCA.x, 0, AMCA.z], kas1: [200 + KAS[0].x, 0, KAS[0].z], kas2: [200 + KAS[1].x, 0, KAS[1].z] };

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hero: { pos: [HERO.x + .2, 1.42, HERO.z + 1.95], look: [HERO.x + .02, 1.38, HERO.z], fov: 44 },
  lens: { pos: [LENS.x + .03, LENS.y + .03, LENS.z + 1.37], look: [LENS.x, LENS.y - .035, LENS.z], fov: 36 },
  wide: { pos: [.12, 1.55, 3.4], look: [.12, 1.55, -1], fov: 50 },
  deriWide: { pos: [199.85, 1.42, 3.1], look: [199.85, 1.42, -1], fov: 50 },
  deriKas: { pos: [199.45, 1.24, 1.2], look: [199.25, 1.2, -1], fov: 42 },
  deriPull: { pos: [199.42, 1.24, 1.45], look: [199.2, 1.2, -1], fov: 44 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: the hero shivering under the lamp -> the magnifier on his arm, hairs springing up -> the whole stop
    { t: 0, ...SHOT.hero, creep: .34, drift: .04 },
    { t: t('tüylerin') + .14, dur: .24, move: 'whip', ...SHOT.lens, creep: .3, drift: .015 },
    { t: t('Bakın,') + .14, dur: .3, move: 'whip', ...SHOT.wide, creep: .26, drift: .05 },
    { t: t('kolundaki') + .35, dur: .7, pos: [HERO.x + .25, 1.4, HERO.z + 2.2], look: [HERO.x + .05, 1.35, HERO.z], fov: 44, creep: .3 },
    { t: t('ayağa') + .1, dur: .25, move: 'whip', ...SHOT.lens, creep: .3, drift: .015 },
    // the uncle laughs
    { t: t('Yanındaki') + .3, dur: .3, move: 'whip', pos: [AMCA.x - .22, 1.5, AMCA.z + 2.0], look: [AMCA.x, 1.47, AMCA.z], fov: 44, creep: .3, drift: .04 },
    // "Oysa": back on the hero
    { t: t('Oysa') + .22, dur: .3, move: 'whip', pos: [HERO.x + .12, 1.42, HERO.z + 1.85], look: [HERO.x + .02, 1.37, HERO.z], fov: 42, creep: .34, drift: .03 },
    // "Her tüyün dibinde": the skin world
    { t: t('Her') + .28, dur: .3, move: 'whip', ...SHOT.deriWide, creep: .25, drift: .04 },
    { t: t('minicik') + .35, dur: .6, ...SHOT.deriKas, creep: .3, drift: .03 },
    { t: t('sinirlerin') + .4, dur: .55, pos: [199.55, 1.5, 2.6], look: [199.95, 1.47, -2.6], fov: 48, creep: .22, drift: .015 },
    { t: t('kaslar') + .25, dur: .3, move: 'whip', ...SHOT.deriPull, creep: .3, drift: .02 },
    { t: t('tüyler', 2) + .2, dur: .3, move: 'whip', ...SHOT.deriWide, creep: .28, drift: .04 },
    // "Kürklü hayvanlarda": the cat on the bench
    { t: t('Kürklü') + .3, dur: .3, move: 'whip', pos: [CAT.x - .22, 1.0, CAT.z + 2.7], look: [CAT.x, .92, CAT.z], fov: 39, creep: .28, drift: .03 },
    // "Tıpkı şişme montun": the uncle and his coat
    { t: t('Tıpkı') + .25, dur: .3, move: 'whip', pos: [AMCA.x + .42, 1.5, AMCA.z + 2.1], look: [AMCA.x - .04, 1.42, AMCA.z], fov: 44, creep: .3, drift: .04 },
    // "Bizde ise": the hero and the fur that is gone
    { t: t('Bizde') + .25, dur: .3, move: 'whip', pos: [HERO.x + .8, 1.56, HERO.z + 2.42], look: [HERO.x + .1, 1.56, HERO.z], fov: 43, creep: .1, drift: .015 },
    { t: t('sadece') + .25, dur: .25, move: 'whip', ...SHOT.lens, creep: .3, drift: .015 },
    // "Yani": both of them
    { t: t('Yani') + .25, dur: .3, move: 'whip', pos: [.08, 1.45, 3.0], look: [.08, 1.4, -.78], fov: 46, creep: .12, drift: 0 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('diken') + .05, .6); cp.kick(t('ayağa') + .25, .5); cp.kick(t('dikiliyor.') + .12, .9); cp.kick(t('kabaran') + .1, .5);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .8) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1c2444');
  buildDurak(scene); buildDeri(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.lens = dynCard(scene, .4, .4, drawLens);
  dyn.cat = dynCard(scene, .8, .8, drawCat, { steps: 20 });
  dyn.catGlow = glow(scene, [CAT.x, CAT.y + .4, CAT.z - .05], '#ff9c4a', 1.5, 0);
  dyn.stop = card(scene, .5, .5, (c, w) => {
    c.lineJoin = 'round'; c.fillStyle = '#2f6fd0'; c.strokeStyle = PLUM; c.lineWidth = 22; c.beginPath(); c.roundRect(w * .08, w * .08, w * .84, w * .84, 60); c.fill(); c.stroke();
    c.strokeStyle = '#ffffff'; c.lineWidth = 12; c.beginPath(); c.roundRect(w * .15, w * .15, w * .7, w * .7, 40); c.stroke();
    c.fillStyle = '#ffffff'; c.font = `900 ${w * .52}px "Arial Black", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('D', w / 2, w * .53);
  });
  const board = (text, bg, fg) => (c, w, h) => {
    c.lineJoin = 'round'; c.fillStyle = bg; c.strokeStyle = PLUM; c.lineWidth = 16; c.beginPath(); c.roundRect(12, 12, w - 24, h - 24, 26); c.fill(); c.stroke();
    c.fillStyle = fg; c.font = `900 ${h * .56}px "Arial Black", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, w / 2, h * .54);
  };
  dyn.sinir = card(scene, .62, .26, board('SİNİR', '#fbf7ee', '#5a4a7a'));
  dyn.kasTag = card(scene, .46, .26, board('KAS', '#fbf7ee', '#c8323a'));
  dyn.dots = [.045, .07].map(r => card(scene, r * 2, r * 2, (c, w) => { c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 60; c.beginPath(); c.arc(w / 2, w / 2, w * .38, 0, 6.29); c.fill(); c.stroke(); }));
  dyn.cloudFur = card(scene, .7, .5, (c, w, h) => drawCloud(c, w, h, 1));
  dyn.cloudGone = card(scene, .7, .5, (c, w, h) => drawCloud(c, w, h, 0));
  // the fur that is no longer there: a dashed fluffy outline around the hero
  dyn.ghost = card(scene, 1.0, 1.9, (c, w, h) => {
    c.lineJoin = c.lineCap = 'round'; c.strokeStyle = '#fff3d6'; c.lineWidth = 17; c.setLineDash([30, 24]); c.beginPath();
    const N = 60; for (let i = 0; i <= N; i++) { const a = i / N * 6.283, sp = 1 + (i % 2 ? .07 : -.03), px = w / 2 + Math.cos(a) * w * .4 * sp, py = h * .5 + Math.sin(a) * h * .44 * sp; i ? c.lineTo(px, py) : c.moveTo(px, py); }
    c.closePath(); c.stroke(); c.globalAlpha = .16; c.fillStyle = '#fff3d6'; c.fill();
  }, { hdr: HDR(1.25, 1.15, .95) });
  dyn.air = [0, 1, 2, 3, 4, 5].map(() => card(scene, .09, .09, (c, w) => { c.strokeStyle = '#eaf6ff'; c.lineWidth = 50; c.beginPath(); c.arc(w / 2, w / 2, w * .34, 0, 6.29); c.stroke(); }, { pw: 128 }));
  const hash = (i, k) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  // snow at the stop (always), and in the skin world once the cold arrives
  smokes.snow = new Smoke(scene, { color: '#ffffff', maxPoints: 700, H: ctx.H, near: .5 });
  smokes.snow.wisps.push({ n: 330, size: .03, alpha: .95, speed: .11, on: () => dyn.where === 'durak',
    path: (u, t, i) => [-3.2 + hash(i, 1) * 6.6 + Math.sin(t * .8 + i) * .12, 3.9 - u * 4.0, -2.5 + hash(i, 2) * 4.4] });
  smokes.snow.wisps.push({ n: 260, size: .034, alpha: .95, speed: .13, on: () => dyn.where === 'deri', fade: t => ramp(t, W('Soğukta') - .1, W('Soğukta') + .5),
    path: (u, t, i) => [197 + hash(i, 3) * 6.4 + Math.sin(t * .8 + i) * .12 + u * .5, 4.0 - u * 4.1, -5 + hash(i, 4) * 6.6] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .02, 'whoosh'); cue(W('Her') + .12, 'whoosh'); cue(W('Kürklü') + .14, 'whoosh');
  cue(0, 'wind', { dur: W('Yanındaki') }); cue(W('diken') + .02, 'shimmer'); cue(W('ayağa') + .15, 'shimmer');
  cue(W('Yanındaki') + .1, 'rise', { dur: .35 }); cue(W('Oysa') + .02, 'rise', { dur: .35 }); cue(W('Soğukta'), 'wind', { dur: 2.2 });
  cue(W('emir') - .02, 'lock'); cue(W('kaslar') + .05, 'scrape', { dur: W('tüyler', 2) - W('kaslar') }); cue(W('dikiliyor.') + .12, 'boom');
  cue(W('kabaran') + .05, 'shimmer'); cue(W('Tıpkı') + .05, 'rise', { dur: .35 }); cue(W('Bizde') + .05, 'rise', { dur: .35 });
  cue(W('gitti,') + .05, 'cut'); cue(W('refleks') - .1, 'shimmer'); cue(W('Yani') + .05, 'rise', { dur: .35 }); cue(W('Yani') + .3, 'wind', { dur: DUR - W('Yani') - .3 });
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'TÜYLER NEDEN DİKEN DİKEN?'); }

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const WARM = '#ffb45a', NIGHT = '#d3d0f4', DAYB = '#e6def2';
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos);
  if (wob) m.rotation.z = Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04;
  return s;
}
function ropeBetween(m, a, b) {
  const d = b.clone().sub(a), len = d.length(); m.position.copy(a).addScaledVector(d, .5); m.scale.set(1, len, 1);
  m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); m.visible = true;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 100 ? 'deri' : 'durak';
  vis('durak', where === 'durak'); vis('deri', where === 'deri'); dyn.where = where;
  dyn.aBeam.visible = dyn.aGlow.visible = where === 'durak';
  for (const c of Object.values(cast)) c.hide();
  for (const m of [dyn.lens, dyn.cat, dyn.stop, dyn.sinir, dyn.kasTag, ...dyn.dots, dyn.cloudFur, dyn.cloudGone, dyn.ghost, ...dyn.air]) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  for (const r of dyn.ropes) r.visible = false;
  dyn.catGlow.material.opacity = 0; dyn.beaconGlow.material.opacity = 0; dyn.beaconLight.intensity = 0;
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const RT = V(1, 0, 0).applyQuaternion(cam.quaternion), UP = V(0, 1, 0).applyQuaternion(cam.quaternion);
  let look, grade = [1, 1, 1], face = [1, .985, .97];
  if (where === 'durak') {
    grade = [1.0, .99, 1.02];
    const tint = face.map((v, i) => v / grade[i]);
    const H = cast.kahraman, U = cast.amca;
    dyn.stop.visible = true; dyn.stop.position.set(.12, 2.62, -2.27);
    const inL3 = t > A('Yanındaki') && t < A('Oysa'), inL4 = t > A('Oysa') && t < A('Her'), inL8 = t > A('Tıpkı') && t < A('Bizde'), inL9 = t > A('Bizde') && t < A('Yani'), inL10 = t > A('Yani');
    // ---- the hero: thin T-shirt, shivering
    const sh = Math.sin(t * 52) * .007, teeth = Math.floor(t * 15) % 2 ? .34 : 0;
    const armsHug = [[34 + Math.sin(t * 46) * 3, -118], [34 - Math.sin(t * 46) * 3, -112]];
    let hp = { expr: 'worried', mouth: teeth, look: .15, lookY: 0, armL: armsHug[0], armR: armsHug[1], lean: Math.sin(t * 52) * .9, blink: bl(1, A('ayağa'), A('Oysa'), A('vücudun'), A('gitti,'), A('kabartmaya')) };
    if (t > A('kolundaki') && t < A('Yanındaki')) hp = { ...hp, look: .55, lookY: .75, gazeY: 1, expr: t > A('ayağa') ? 'surprised' : 'worried', brow: t > A('ayağa') ? 1 : 0, mouth: t > A('ayağa') ? .6 : teeth };
    if (inL3) hp = { ...hp, look: .85, expr: 'worried', mouth: teeth };
    if (inL4) hp = t < A('vücudun') ? { ...hp, expr: 'angry', look: .85, mouth: 0, brow: -.4 } : { ...hp, expr: 'surprised', look: .5, lookY: .7, gazeY: 1, brow: .8, mouth: .5 };
    if (inL8) hp = { ...hp, expr: 'angry', look: .9, mouth: teeth * .6 };
    if (inL9) hp = t < A('gitti,') ? { ...hp, expr: 'neutral', look: .45, lookY: -.75, gazeY: -1, brow: .7, mouth: 0 } : { ...hp, expr: 'worried', look: .3, lookY: t < A('geriye') ? -.6 : .5, mouth: teeth };
    if (inL10) hp = t < A('kabartmaya') ? { ...hp, look: .1, mouth: teeth } : { ...hp, expr: 'smile', look: .1, sweat: 1, mouth: 0, armR: [150, 20], armL: armsHug[0] };
    H.show(); H.place(HERO.x + sh, 0, HERO.z, cam, tint);
    H.draw({ ...hp, lit: 1, shade: NIGHT, rim: { color: WARM, a: .42 } }); H.castFrom(LAMP);
    // ---- the uncle: fat coat, red cap, never cold
    const laugh = (t > A('amca') - .1 && t < A('"Evladım,') - .04) || (inL10 && t > A('olmayan')), talk = t > A('"Evladım,') - .04 && t < A('giyinseydin!"') + .75;
    let up = { expr: 'smug', look: -.6, armL: [16, 10], armR: [16, 10], blink: bl(2, A('amca') - .1, A('"Evladım,'), A('Oysa'), A('Tıpkı'), A('olmayan')) };
    if (laugh) up = { ...up, expr: 'laugh', laughMarks: .9, mouth: .5 + .5 * Math.abs(Math.sin(t * 13)), bob: -Math.abs(Math.sin(t * 13)) * 10, armR: [28, -100], armL: [150, 20] };
    if (talk) up = { ...up, expr: 'smug', brow: .6, mouth: flap(env, t), armL: [96, 12], armR: [28, -95] };
    if (inL8) up = { ...up, expr: 'proud', look: -.25, lid: .15, armL: [30, -98 + 9 * Math.sin(t * 9)], armR: [30, -98 - 9 * Math.sin(t * 9)] };
    U.show(); U.place(AMCA.x, 0, AMCA.z, cam, tint);
    U.draw({ ...up, lit: 1, shade: NIGHT, rim: { color: WARM, a: .45 } }); U.castFrom(LAMP);
    // ---- the magnifier on his arm
    const lensOn = (t > A('tüylerin') - .02 && t < W('Bakın,') - .02) || (t > A('ayağa') - .22 && t < W('Yanındaki') + .16) || (t > W('sadece') + .1 && t < W('Yani') + .1);
    if (lensOn) {
      const at = t < 3 ? A('tüylerin') - .02 : t < 10 ? A('ayağa') - .22 : W('sadece') + .1;
      const k = t < 3 ? spring((t - A('diken')) * 1.0) : t < 10 ? spring(t - A('ayağa')) : 1 + .04 * Math.sin(t * 20);
      dyn.lens.userData.set(k); popCard(dyn.lens, at, t, LENS, 1, false);
    }
    // ---- the cat on the bench
    const puff = backOut((t - A('kabaran')) / .28), happy = t > A('hava') ? 1 : 0;
    dyn.cat.userData.set(puff, happy); dyn.cat.visible = true;
    dyn.cat.position.set(CAT.x + (puff < .5 ? Math.sin(t * 50) * .006 : 0), CAT.y + .4 + (puff > .5 ? Math.sin(t * 2.4) * .006 : 0), CAT.z);
    if (t > A('kabaran')) dyn.catGlow.material.opacity = .34 * ramp(t, A('sıcağı') - .2, A('sıcağı') + .5);
    if (t > A('araya') && t < A('Tıpkı')) dyn.air.forEach((m, i) => {
      const u = ((t - A('araya')) * .9 + i / 6) % 1, a = i / 6 * 6.283 + 1, r = .62 - u * .42;
      m.visible = true; m.position.set(CAT.x, CAT.y + .36, CAT.z + .02).addScaledVector(RT, Math.cos(a) * r).addScaledVector(UP, Math.sin(a) * r * .8 + .05); m.scale.setScalar(1 - u * .5); m.material.opacity = Math.sin(Math.PI * u);
    });
    // ---- the fur that is gone
    if (inL9 && t < W('sadece') + .12) {
      const head = V(HERO.x, 1.49, HERO.z), at2 = (r, u) => head.clone().addScaledVector(RT, r).addScaledVector(UP, u), t0 = A('kalın');
      dyn.dots.forEach((m, i) => popCard(m, t0 + i * .1, t, at2(.2 + i * .1, .3 + i * .12), 1, false));
      const gone = t > A('gitti,');
      const m = gone ? dyn.cloudGone : dyn.cloudFur; const s = popCard(m, gone ? A('gitti,') : t0 + .22, t, at2(.3, .68));
      if (s) m.position.y += Math.sin(t * 2) * .015;
    }
    if (inL10 && t > A('olmayan')) { const s = popCard(dyn.ghost, A('olmayan'), t, V(HERO.x, .93, HERO.z - .02), 1, false); dyn.ghost.material.opacity = .65 + .3 * Math.sin(t * 7); dyn.ghost.scale.set(s * (1 + .03 * Math.sin(t * 9)), s, 1); }
    const f = lensOn ? LENS : inL3 || inL8 ? V(AMCA.x, 1.5, AMCA.z) : t > A('Kürklü') && t < A('Tıpkı') ? V(CAT.x, .9, CAT.z) : V(HERO.x, 1.5, HERO.z);
    look = { focus: cam.position.distanceTo(f), coc: lensOn ? 7 : 5, range: lensOn ? .5 : 1.9, sat: 1.3, lift: [.1, .1, .19], bloom: .85, vignette: .22 };
  } else {
    // ---- the skin: hairs lying -> the cold comes -> the nerve gives the order -> the muscles pull -> the hairs stand
    const cold = ramp(t, A('Soğukta') - .1, A('Soğukta') + .6);
    grade = [lerpN(1.03, .93, cold), lerpN(1.0, .98, cold), lerpN(.97, 1.09, cold)];
    const tint = face.map((v, i) => v / grade[i]);
    const up = backOut((t - A('tüyler', 2) - .08) / (W('dikiliyor.') + .16 - A('tüyler', 2) - .08));
    const strain = ramp(t, A('kaslar'), A('kasılıyor') + .1) * (1 - ramp(t, A('tüyler', 2), A('tüyler', 2) + .2));
    dyn.hairs.forEach((h, i) => {
      const lean = (lerpN(60 - i * 2, 4, up) + strain * Math.sin(t * 30 + i) * 1.5) * Math.PI / 180;
      h.piv.rotation.set(0, HAZ, -lean); h.lean = lean;
      const bs = Math.max(.02, up); h.bump.scale.set(.8 + .2 * bs, .55 * bs, .8 + .2 * bs);
    });
    const order = t > A('emir') && t < A('tüyler', 2) + .4, fl = order ? .55 + .45 * Math.sin((t - A('emir')) * 24) : 0;
    dyn.beaconMat.color.copy(order ? HDR(1.2 + 1.8 * fl, .9 + 1.3 * fl, .3 + .3 * fl) : new THREE.Color('#8a90b8'));
    dyn.beaconLight.intensity = order ? 1.8 * fl : 0; dyn.beaconGlow.material.opacity = order ? .55 * fl : 0;
    dyn.sinir.visible = true; dyn.sinir.position.set(BEACON.x, BEACON.y - .52, BEACON.z + .06);
    const shiver = cold * (1 - ramp(t, A('emir'), A('emir') + .2));
    [['kas1', 0, 3], ['kas2', 1, 4]].forEach(([name, i, seed]) => {
      const K = cast[name], p = POS[name], pull = t > A('kaslar') - i * .06, done = up > .9;
      const sx = Math.sin(t * 52 + i) * .006 * shiver;
      K.show(); K.place(p[0] + sx - (pull && !done ? .03 * strain : 0), 0, p[2], cam, tint);
      let d = { expr: 'neutral', lid: .5, look: .2, armL: [14, 8], armR: [14, 8], blink: bl(seed, A('Soğukta'), A('emir'), A('kaslar'), A('dikiliyor.')) };
      if (t > A('Soğukta')) d = { ...d, expr: 'worried', lid: 0, armL: [34, -116], armR: [34, -112], lean: Math.sin(t * 52) * .8, mouth: Math.floor(t * 15) % 2 ? .3 : 0 };
      if (t > A('emir')) d = { ...d, expr: 'surprised', look: .75, lookY: -.6, brow: 1, mouth: .6, armL: [20, 10], armR: [20, 10], lean: 0 };
      if (pull) d = { ...d, expr: 'angry', look: .6, lookY: 0, brow: -.3, mouth: .25 + .2 * Math.abs(Math.sin(t * 20)), sweat: 1, armR: [78, 12], armL: [-62, -16], lean: -5 * strain - 1 };
      if (done) d = { ...d, expr: 'proud', mouth: 0, sweat: 0, look: .5, lookY: -.3, armR: [70, 20], armL: [16, 10], lean: -2 };
      K.draw({ ...d, lit: -1, shade: DAYB, rim: { color: '#ffe2a0', a: .28 } }); K.castFrom(dyn.bSun, true);
      const h = dyn.hairs[i], at = 1.12, hp = V(200 + h.x + Math.sin(h.lean) * at * Math.cos(HAZ), Math.cos(h.lean) * at, h.z - Math.sin(h.lean) * at * Math.sin(HAZ)), hand = K.hand(1);
      if (hand && t > A('kaslar') - .3 - i * .06) ropeBetween(dyn.ropes[i], hand, hp);
    });
    if (t > A('kas') && t < A('sinirlerin') + .2) popCard(dyn.kasTag, A('kas'), t, V(POS.kas1[0], 1.5, POS.kas1[2]).addScaledVector(UP, .34).addScaledVector(RT, -.02));
    const f = t > A('sinirlerin') + .1 && t < A('kaslar') ? V(199.9, 1.7, -1.8) : V(199.25, 1.2, -1);
    look = { focus: cam.position.distanceTo(f), coc: 4, range: 3.4, sat: 1.16, lift: [.1, .095, .16], bloom: .8, vignette: .18 };
  }
  for (const s of Object.values(smokes)) s.update(t);
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
