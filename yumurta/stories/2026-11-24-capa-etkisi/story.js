// Çapa etkisi: ilk duyduğun fiyat neden aklına takılır? Demek O Yüzden günlük Short (yumurta stili), 24 Kasım 2026.
// Bilgi: Tversky ve Kahneman (1974, Science): çarkıfelek 10 ya da 65'te durduruldu, sonra Afrika ülkelerinin BM'deki payı
// soruldu; ortanca tahmin 10 görenlerde yüzde 25, 65 görenlerde yüzde 45. Kaynaklar SCRIPT.md'de.
// Setler: PAZAR (x≈0) gündüz, tente + askılık + ampuller; DENEY (x≈200) çarkıfelek ve iki denek; DENİZ (x≈400) kesit:
// demir atmış tekne (benzetme).
import * as THREE from 'three';
import { stoneTex, woodTex, frizTex, painted, flat } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { beam, glow } from '/engine/src/fx.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-24-capa-etkisi';
export const FPS = 30;
export let DUR = 37.2;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;
const FONT = '"Arial Black", "Segoe UI Black", sans-serif';
let W, cast = {}, sets = {}, dyn = {};

function wordTimes(words) {
  const norm = s => s.toLocaleLowerCase('tr-TR').replace(/[^\p{L}\p{N}]/gu, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w); };
}
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus|Icosahedron|Cone/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function card(scene, w, h, draw, { pw = 512, hdr = null } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); draw(c.getContext('2d'), c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false, color: hdr || 0xffffff }));
  m.layers.set(1); m.renderOrder = 20; m.visible = false; scene.add(m); return m;
}

// ---------------------------------------------------------------- drawings
const burst = (text, fill, ink) => (c, w, h) => {
  c.lineJoin = 'round'; c.fillStyle = fill; c.strokeStyle = PLUM; c.lineWidth = 20; c.beginPath();
  for (let k = 0; k < 28; k++) { const a = k / 28 * 6.283 - .1, r = k % 2 ? w * .37 : w * .46; c.lineTo(w / 2 + Math.cos(a) * r, h / 2 + Math.sin(a) * r * (h / w)); }
  c.closePath(); c.fill(); c.stroke();
  c.fillStyle = ink; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${w * .25}px ${FONT}`; c.fillText(text, w / 2, h * .46);
  c.font = `900 ${w * .12}px ${FONT}`; c.fillText('TL', w / 2, h * .68);
};
function drawAnchor(c, w, h) {
  c.lineJoin = c.lineCap = 'round';
  const path = () => { c.beginPath(); c.arc(w / 2, h * .13, w * .085, 0, 6.29);
    c.moveTo(w / 2, h * .22); c.lineTo(w / 2, h * .86); c.moveTo(w * .3, h * .33); c.lineTo(w * .7, h * .33);
    c.moveTo(w * .15, h * .6); c.quadraticCurveTo(w * .18, h * .9, w / 2, h * .87); c.quadraticCurveTo(w * .82, h * .9, w * .85, h * .6);
    c.moveTo(w * .06, h * .67); c.lineTo(w * .15, h * .54); c.lineTo(w * .25, h * .66); c.moveTo(w * .75, h * .66); c.lineTo(w * .85, h * .54); c.lineTo(w * .94, h * .67); };
  c.strokeStyle = PLUM; c.lineWidth = w * .135; path(); c.stroke(); c.strokeStyle = '#c3cfe8'; c.lineWidth = w * .07; path(); c.stroke();
}
function drawJacket(c, w, h) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = 9;
  c.beginPath(); c.arc(w / 2, h * .07, w * .05, Math.PI * .9, Math.PI * 2.3); c.stroke(); c.beginPath(); c.moveTo(w / 2 + w * .04, h * .1); c.lineTo(w / 2, h * .16); c.stroke();
  const body = () => { c.beginPath(); c.moveTo(w * .36, h * .16); c.lineTo(w * .2, h * .22); c.lineTo(w * .04, h * .62); c.lineTo(w * .17, h * .67); c.lineTo(w * .27, h * .42); c.lineTo(w * .25, h * .94);
    c.lineTo(w * .75, h * .94); c.lineTo(w * .73, h * .42); c.lineTo(w * .83, h * .67); c.lineTo(w * .96, h * .62); c.lineTo(w * .8, h * .22); c.lineTo(w * .64, h * .16); c.closePath(); };
  c.fillStyle = '#b06a3a'; c.lineWidth = 13; body(); c.fill(); c.stroke();
  c.save(); body(); c.clip(); c.fillStyle = '#8a4e28'; c.fillRect(w * .66, 0, w, h); c.fillRect(0, h * .86, w, h); c.restore(); c.lineWidth = 13; body(); c.stroke();
  c.fillStyle = '#e8d2a8'; c.lineWidth = 9; for (const s of [-1, 1]) { c.beginPath(); c.moveTo(w / 2, h * .3); c.lineTo(w / 2 + s * w * .15, h * .15); c.lineTo(w / 2 + s * w * .2, h * .3); c.closePath(); c.fill(); c.stroke(); }
  c.beginPath(); c.moveTo(w / 2, h * .3); c.lineTo(w / 2, h * .94); c.stroke();
  for (const s of [-1, 1]) { c.beginPath(); c.roundRect(w / 2 + s * w * .13 - w * .06, h * .62, w * .12, h * .1, 8); c.stroke(); }
  c.fillStyle = '#f0c050'; for (const y of [.42, .56, .7]) { c.beginPath(); c.arc(w / 2 + w * .035, h * y, 9, 0, 6.29); c.fill(); c.stroke(); }
}
function cloudPath(c, w, h) { c.beginPath(); for (let k = 0; k < 9; k++) { const a = k / 9 * 6.283; c.arc(w / 2 + Math.cos(a) * w * .3, h / 2 + Math.sin(a) * h * .28, w * .13, 0, 6.29); } }
const bubble = (text, chip, chipCol) => (c, w, h) => {
  c.lineJoin = 'round'; c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 16;
  c.beginPath(); c.roundRect(14, 14, w - 28, h * .74, 56); c.fill(); c.stroke();
  c.beginPath(); c.moveTo(w * .42, h * .76 + 6); c.lineTo(w * .5, h * .97); c.lineTo(w * .6, h * .76 + 6); c.fill(); c.stroke(); c.fillRect(w * .42 - 6, h * .7, w * .2, h * .08);
  c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .4}px ${FONT}`; c.fillText(text, w * .6, h * .41);
  c.fillStyle = chipCol; c.lineWidth = 10; c.beginPath(); c.arc(w * .2, h * .4, h * .2, 0, 6.29); c.fill(); c.stroke();
  c.fillStyle = chipCol === '#3f86d6' ? '#ffffff' : PLUM; c.font = `900 ${h * .2}px ${FONT}`; c.fillText(chip, w * .2, h * .41);
};
function wheelTex() {
  const c = document.createElement('canvas'); c.width = c.height = 1024; const g = c.getContext('2d'), R = 512;
  const nums = [10, 40, 85, 25, 70, 5, 65, 30, 95, 50, 15, 80], cols = ['#e8503f', '#f6f1e4', '#3f86d6', '#f0c050'];
  for (let i = 0; i < 12; i++) {
    const a = -Math.PI / 2 + i * Math.PI / 6;
    g.fillStyle = cols[i % 4]; g.beginPath(); g.moveTo(R, R); g.arc(R, R, R - 8, a - Math.PI / 12, a + Math.PI / 12); g.closePath(); g.fill(); g.strokeStyle = PLUM; g.lineWidth = 8; g.stroke();
    g.save(); g.translate(R, R); g.rotate(i * Math.PI / 6); g.fillStyle = i % 4 === 0 || i % 4 === 2 ? '#ffffff' : PLUM; g.font = `900 108px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(nums[i]), 0, -R * .7); g.restore();
  }
  g.strokeStyle = PLUM; g.lineWidth = 18; g.beginPath(); g.arc(R, R, R - 10, 0, 6.29); g.stroke();
  g.fillStyle = '#f0c050'; g.beginPath(); g.arc(R, R, 74, 0, 6.29); g.fill(); g.lineWidth = 12; g.stroke();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
function drawBoat(c, w, h) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = 11;
  c.beginPath(); c.moveTo(w * .56, h * .62); c.lineTo(w * .56, h * .08); c.stroke();
  c.fillStyle = '#f0c050'; c.beginPath(); c.moveTo(w * .56, h * .08); c.lineTo(w * .8, h * .16); c.lineTo(w * .56, h * .25); c.closePath(); c.fill(); c.stroke();
  c.fillStyle = '#f6f1e4'; c.beginPath(); c.roundRect(w * .5, h * .42, w * .28, h * .24, 10); c.fill(); c.stroke();
  c.fillStyle = '#9fd4ff'; c.beginPath(); c.arc(w * .64, h * .53, h * .06, 0, 6.29); c.fill(); c.stroke();
  // the sailor: an egg head with a blue cap
  c.fillStyle = '#ffffff'; c.beginPath(); c.ellipse(w * .3, h * .46, w * .1, h * .14, 0, 0, 6.29); c.fill(); c.stroke();
  c.fillStyle = '#3f6fb8'; c.beginPath(); c.ellipse(w * .3, h * .35, w * .1, h * .06, 0, Math.PI, 0); c.fill(); c.stroke(); c.beginPath(); c.moveTo(w * .2, h * .35); c.lineTo(w * .44, h * .35); c.stroke();
  c.fillStyle = PLUM; for (const s of [-1, 1]) { c.beginPath(); c.arc(w * .31 + s * w * .035, h * .46, 6, 0, 6.29); c.fill(); }
  c.lineWidth = 6; c.beginPath(); c.moveTo(w * .28, h * .53); c.quadraticCurveTo(w * .31, h * .56, w * .35, h * .53); c.stroke();
  c.lineWidth = 12; const hull = () => { c.beginPath(); c.moveTo(w * .05, h * .62); c.lineTo(w * .95, h * .62); c.quadraticCurveTo(w * .9, h * .95, w * .74, h * .95); c.lineTo(w * .24, h * .95); c.quadraticCurveTo(w * .1, h * .92, w * .05, h * .62); c.closePath(); };
  c.fillStyle = '#e8503f'; hull(); c.fill(); c.save(); hull(); c.clip(); c.fillStyle = '#f6f1e4'; c.fillRect(0, h * .7, w, h * .07); c.restore(); hull(); c.stroke();
}

// ---------------------------------------------------------------- PAZAR (x = 0), gündüz
const HERO = { x: -.45, z: -.75 }, SAT = { x: .55, z: -.9 }, JKT = V(.05, 1.52, -1.55);
function buildPazar(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(14, 10), painted(stoneTex({ base: '#d3daee', seam: '#9da9cc', bw: 96, bh: 96, rep: [9, 6] }))); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 1); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(14, 6), painted(stoneTex({ base: '#8fc3d4', seam: '#6a9fb4', bw: 128, bh: 48, rep: [6, 4] }))); wall.position.set(0, 3, -3.0); g.add(wall);
  const dado = new THREE.Mesh(new THREE.BoxGeometry(14, .85, .08), painted(stoneTex({ base: '#5f98b0', seam: '#467a92', bw: 128, bh: 128, rep: [14, 1] }))); dado.position.set(0, .42, -2.96); g.add(dado);
  for (const wx of [-2.4, -.8, .9, 2.5]) {            // windows with red shutters, high on the wall
    const p = new THREE.Mesh(new THREE.PlaneGeometry(.6, .9), flat('#cfe6ff')); p.position.set(wx, 3.5, -2.96); g.add(p);
    for (const s of [-1, 1]) { const sh = new THREE.Mesh(new THREE.BoxGeometry(.3, .96, .05), flat('#d8573a')); sh.position.set(wx + s * .47, 3.5, -2.94); sh.userData.noShadow = true; g.add(sh); }
    const sill = new THREE.Mesh(new THREE.BoxGeometry(1.3, .07, .14), flat('#f1ece2')); sill.position.set(wx, 3.0, -2.92); g.add(sill);
  }
  // the clothes rack and the awning over it
  const metal = flat('#4a4f78'), bar = new THREE.Mesh(new THREE.CylinderGeometry(.025, .025, 2.9, 8), metal); bar.rotation.z = Math.PI / 2; bar.position.set(.05, 2.05, -1.6); g.add(bar);
  for (const x of [-1.38, 1.48]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, 2.05, 8), metal); p.position.set(x, 1.02, -1.6); g.add(p); }
  [['#e0604a', -1.1], ['#3f86d6', -.72], ['#f0c050', .82], ['#5ec2c8', 1.2]].forEach(([col, x], i) => {
    const b = new THREE.Mesh(new THREE.BoxGeometry(.32, .6 + (i % 2) * .1, .04), flat(col)); b.position.set(x, 1.66 - (i % 2) * .05, -1.6); b.rotation.y = (i - 1.5) * .12; g.add(b);
  });
  const ac = document.createElement('canvas'); ac.width = 512; ac.height = 128; const ag = ac.getContext('2d');
  for (let i = 0; i < 8; i++) { ag.fillStyle = i % 2 ? '#f6f1e4' : '#e8503f'; ag.fillRect(i * 64, 0, 64, 128); }
  const at = new THREE.CanvasTexture(ac); at.colorSpace = THREE.SRGBColorSpace;
  const awn = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 1.7), new THREE.MeshLambertMaterial({ map: at, side: THREE.DoubleSide })); awn.rotation.x = -Math.PI / 2 + .3; awn.position.set(.05, 2.86, -2.15); awn.castShadow = true; g.add(awn);
  const val = new THREE.Mesh(new THREE.PlaneGeometry(3.4, .22), new THREE.MeshLambertMaterial({ map: at, side: THREE.DoubleSide })); val.position.set(.05, 2.52, -1.36); g.add(val);
  for (const x of [-1.6, 1.7]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, 2.62, 8), flat('#f1ece2')); p.position.set(x, 1.31, -1.36); g.add(p); }
  const bm = new THREE.MeshBasicMaterial({ color: HDR(2.5, 1.9, .9) });
  dyn.bulbs = [-1.15, -.55, .05, .65, 1.25].map(x => { const b = new THREE.Mesh(new THREE.SphereGeometry(.05, 12, 8), bm); b.position.set(x, 2.33 - Math.cos((x - .05) * 1.2) * .06, -1.33); g.add(b); return b; });
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#dfe8ff', '#9a8fb8', 1.85));
  const sunDir = V(.5, -1, -.8).normalize(); dyn.aSun = sunDir;
  const sun = new THREE.DirectionalLight('#ffe0a8', 2.5); sun.position.copy(V(0, 0, -1).addScaledVector(sunDir, -9)); sun.target.position.set(0, 0, -1);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5, near: .5, far: 22 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
  L.add(sun); L.add(sun.target);
  const bl = new THREE.PointLight('#ffc878', 2.4, 4, 1.5); bl.position.set(.05, 2.25, -1.3); L.add(bl);
  scene.add(L); sets.pazar = { g, L };
  shadows(g);
}

// ---------------------------------------------------------------- DENEY (x = 200): the wheel and the two subjects
const WH = V(199.7, 1.75, -1.6), HOCA = { x: 200.55, z: -1.3 }, D1 = { x: 202.64, z: -1.2 }, D2 = { x: 203.36, z: -1.2 };
const LAMPB = [V(200.1, 2.86, -1.0), V(203.0, 2.7, -1.5)];
function buildDeney(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(14, 8), painted(stoneTex({ base: '#dfe3f4', seam: '#a9aed6', bw: 128, bh: 128, rep: [9, 5], seed: 8 }))); fl.rotation.x = -Math.PI / 2; fl.position.set(201.5, 0, 0); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(14, 5), painted(stoneTex({ base: '#8d8fd6', seam: '#6a6cb4', bw: 160, bh: 64, rep: [5, 3], seed: 9 }))); wall.position.set(201.5, 2.5, -2.5); g.add(wall);
  const band = new THREE.Mesh(new THREE.PlaneGeometry(14, .34), painted(frizTex({ rep: [7, 1] }))); band.position.set(201.5, .95, -2.45); g.add(band);
  const base = new THREE.Mesh(new THREE.BoxGeometry(14, .16, .1), flat('#f1ece2')); base.position.set(201.5, .08, -2.44); g.add(base);
  // the wheel of fortune on its stand
  const wood = painted(woodTex({ base: '#8f6444' }));
  const post = new THREE.Mesh(new THREE.BoxGeometry(.12, 1.8, .08), wood); post.position.set(WH.x, .9, WH.z - .12); g.add(post);
  const foot = new THREE.Mesh(new THREE.BoxGeometry(.8, .08, .45), wood); foot.position.set(WH.x, .04, WH.z - .1); g.add(foot);
  dyn.wheel = new THREE.Group(); dyn.wheel.position.copy(WH); g.add(dyn.wheel);
  const rim = new THREE.Mesh(new THREE.CylinderGeometry(.535, .535, .07, 48), flat('#5a3a28')); rim.rotation.x = Math.PI / 2; rim.position.z = -.04; dyn.wheel.add(rim);
  const face = new THREE.Mesh(new THREE.CircleGeometry(.5, 64), new THREE.MeshBasicMaterial({ map: wheelTex() })); face.position.z = .005; dyn.wheel.add(face);
  const ptr = new THREE.Mesh(new THREE.ConeGeometry(.075, .2, 3), flat('#e8503f', { emissive: '#5a1010' })); ptr.rotation.z = Math.PI; ptr.position.set(WH.x, WH.y + .56, WH.z + .04); g.add(ptr);
  const bm = new THREE.MeshBasicMaterial({ color: HDR(2.6, 2.0, 1.0) });
  for (const p of LAMPB) {
    const cord = new THREE.Mesh(new THREE.CylinderGeometry(.01, .01, 1.6, 6), flat('#3a3058')); cord.position.set(p.x, p.y + .9, p.z); cord.userData.noShadow = true; g.add(cord);
    const shd = new THREE.Mesh(new THREE.ConeGeometry(.2, .16, 20, 1, true), flat('#e8503f', { side: THREE.DoubleSide })); shd.position.set(p.x, p.y + .1, p.z); shd.userData.noShadow = true; g.add(shd);
    const b = new THREE.Mesh(new THREE.SphereGeometry(.06, 12, 8), bm); b.position.copy(p); b.userData.noShadow = true; g.add(b);
  }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#b9c2ff', '#6a6096', 1.55));
  [[LAMPB[0], V(199.9, 1.2, -1.5)], [LAMPB[1], V(203.0, 1.0, -1.2)]].forEach(([p, tg]) => {
    const sp = new THREE.SpotLight('#ffd9a0', 13, 9, .9, .55, 1.3); sp.position.copy(p); sp.target.position.copy(tg);
    sp.castShadow = true; sp.shadow.mapSize.set(1024, 1024); sp.shadow.bias = -.002; sp.shadow.radius = 4; L.add(sp); L.add(sp.target);
  });
  const fill = new THREE.DirectionalLight('#aab8ff', .8); fill.position.set(201, 3, 5); fill.target.position.set(201.5, 1, -1); L.add(fill); L.add(fill.target);
  scene.add(L); sets.deney = { g, L };
  shadows(g);
  dyn.bBeams = [beam(scene, LAMPB[0].toArray(), [200.3, .2, -.9], { r0: .1, r1: 1.0, color: '#ffe2a8', strength: .05 }), beam(scene, LAMPB[1].toArray(), [203.0, .2, -1.2], { r0: .1, r1: 1.2, color: '#ffe2a8', strength: .1 })];
}

// ---------------------------------------------------------------- DENİZ (x = 400): a cut through the sea
const SEA = { x: 400, surf: 2.6, bed: 1.0, z: -1.5 };
function buildDeniz(scene) {
  const g = new THREE.Group(); scene.add(g);
  const c = document.createElement('canvas'); c.width = 896; c.height = 1024; const q = c.getContext('2d'), w = 896, h = 1024, vs = .469 * h, vb = .72 * h;
  let gr = q.createLinearGradient(0, 0, 0, vs); gr.addColorStop(0, '#6fb8f2'); gr.addColorStop(1, '#e6f5ff'); q.fillStyle = gr; q.fillRect(0, 0, w, vs);
  q.fillStyle = '#ffffff'; for (const [x, y, r] of [[150, 190, 60], [230, 200, 44], [690, 300, 50], [760, 310, 36]]) { q.beginPath(); q.ellipse(x, y, r * 1.5, r * .6, 0, 0, 6.29); q.fill(); }
  gr = q.createLinearGradient(0, vs, 0, vb); gr.addColorStop(0, '#49b4e0'); gr.addColorStop(1, '#2458a8'); q.fillStyle = gr; q.fillRect(0, vs, w, vb - vs);
  q.fillStyle = 'rgba(255,255,255,.1)'; for (const x of [120, 380, 640]) { q.beginPath(); q.moveTo(x, vs); q.lineTo(x + 90, vs); q.lineTo(x - 40, vb); q.lineTo(x - 170, vb); q.closePath(); q.fill(); }
  q.fillStyle = '#ecd6a2'; q.beginPath(); q.moveTo(0, vb + 8); for (let x = 0; x <= w; x += 64) q.quadraticCurveTo(x + 32, vb - 10 + (x / 64 % 2) * 16, x + 64, vb + 6); q.lineTo(w, h); q.lineTo(0, h); q.closePath(); q.fill();
  q.strokeStyle = PLUM; q.lineWidth = 4; q.stroke();
  q.strokeStyle = '#2f9a6a'; q.lineWidth = 9; q.lineCap = 'round'; for (const x of [90, 130, 720, 770, 810]) { q.beginPath(); q.moveTo(x, vb + 10); q.quadraticCurveTo(x + 18, vb - 40, x - 6, vb - 80 - (x % 50)); q.stroke(); }
  q.strokeStyle = '#ffffff'; q.lineWidth = 7; q.beginPath(); q.moveTo(0, vs); for (let x = 0; x <= w; x += 56) q.quadraticCurveTo(x + 28, vs - 9, x + 56, vs); q.stroke();
  const bt = new THREE.CanvasTexture(c); bt.colorSpace = THREE.SRGBColorSpace; bt.anisotropy = 8;
  const back = new THREE.Mesh(new THREE.PlaneGeometry(7, 8), new THREE.MeshBasicMaterial({ map: bt })); back.position.set(SEA.x, 2.4, -3); g.add(back);
  const sun = new THREE.Mesh(new THREE.CircleGeometry(.26, 40), new THREE.MeshBasicMaterial({ color: HDR(2.6, 2.1, 1.0) })); sun.position.set(SEA.x + .72, 3.7, -2.9); g.add(sun);
  const L = new THREE.Group(); L.add(new THREE.HemisphereLight('#ffffff', '#9ab0d0', 2));
  scene.add(L); sets.deniz = { g, L };
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  kahraman: { hair: '#3a2a24', cloth: '#2d7466', collar: true, buttons: '#e0b050', height: 1.7 },
  satici: { mustache: '#2a1c18', hair: '#2a2024', hat: 'kulah', hatColor: '#3f6fb8', cloth: '#f0e6cf', pattern: 'stripes', apron: true, bodyW: 232, headW: 282, headH: 256, height: 1.78 },
  hoca: { beard: '#d9d9e4', beardLen: .7, hair: '#d9d9e4', cloth: '#f2f3f8', clothDark: '#b9bdd6', buttons: '#8a96c0', pocket: true, headW: 268, height: 1.74 },
  denek1: { hair: '#6a3a24', cloth: '#c8643a', pattern: 'stripes', height: 1.62 },
  denek2: { hair: '#2a2024', cloth: '#6a3a7a', buttons: '#e0b050', height: 1.66, headW: 256, headH: 240 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  seller: { pos: [SAT.x - .25, 1.55, SAT.z + 2.3], look: [SAT.x - .22, 1.5, SAT.z], fov: 44 },
  heroTag: { pos: [HERO.x + .22, 1.42, HERO.z + 2.2], look: [HERO.x + .2, 1.38, HERO.z], fov: 44 },
  two: { pos: [.05, 1.5, 2.95], look: [.05, 1.45, -.82], fov: 46 },
  heroCloud: { pos: [HERO.x + .8, 1.56, HERO.z + 2.42], look: [HERO.x + .1, 1.56, HERO.z], fov: 43 },
  b1: { pos: [200.1, 1.6, 2.35], look: [200.1, 1.6, -1.5], fov: 44 },
  b2: { pos: [203.0, 1.55, 2.25], look: [203.0, 1.55, -1.2], fov: 40 },
  wheel: { pos: [199.72, 1.56, 1.0], look: [199.72, 1.56, -1.6], fov: 40 },
  sea: { pos: [SEA.x, 2.4, 4.3], look: [SEA.x, 2.4, -2], fov: 34.5 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: the seller and his first price -> the hero, the price hooked on him -> the stall
    { t: 0, ...SHOT.seller, creep: .32, drift: .03 },
    { t: t('neden') + .14, dur: .24, move: 'whip', ...SHOT.heroTag, creep: .3, drift: .02 },
    { t: t('Bakın,') + .14, dur: .3, move: 'whip', ...SHOT.two, creep: .16, drift: 0 },
    { t: t('Sonra') + .25, dur: .3, move: 'whip', ...SHOT.seller, creep: .28, drift: .02 },
    { t: t('Birden') + .25, dur: .3, move: 'whip', ...SHOT.two, creep: .16, drift: 0 },
    { t: t('çünkü') + .25, dur: .3, move: 'whip', ...SHOT.heroCloud, creep: .08, drift: .012 },
    // the experiment
    { t: t('Ünlü') + .28, dur: .3, move: 'whip', ...SHOT.b1, creep: .14, drift: 0 },
    { t: t('sonra', 2) + .25, dur: .32, move: 'whip', ...SHOT.b2, creep: .14, drift: 0 },
    { t: t('Çark') + .2, dur: .3, move: 'whip', ...SHOT.wheel, creep: .25, drift: 0 },
    { t: t('tahminler') + .2, dur: .3, move: 'whip', ...SHOT.b2, creep: .14, drift: 0 },
    { t: t('altmış') + .04, dur: .28, move: 'whip', ...SHOT.wheel, creep: .25, drift: 0 },
    { t: t('yüzde', 2) + .2, dur: .3, move: 'whip', ...SHOT.b2, creep: .14, drift: 0 },
    // "Çünkü beynin": the hero on his anchor rope
    { t: t('Çünkü', 2) + .25, dur: .3, move: 'whip', pos: [-.1, 1.5, 3.05], look: [-.1, 1.45, -.82], fov: 46, creep: .05, drift: 0 },
    // the anchored boat
    { t: t('Tıpkı') + .25, dur: .3, move: 'whip', ...SHOT.sea, creep: .12, drift: 0 },
    { t: t('Yani') + .25, dur: .3, move: 'whip', ...SHOT.two, creep: .16, drift: 0 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(.02, .5); cp.kick(t('takılır?') + .22, .7); cp.kick(t('"Üç') + .05, .5); cp.kick(t('çapa') + .22, .9);
  cp.kick(t('on') + .14, .5); cp.kick(t('altmış') + .16, .5); cp.kick(t('uzaklaşamıyor.') + .5, .8);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .8) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1c2444');
  buildPazar(scene); buildDeney(scene); buildDeniz(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.b3 = card(scene, .46, .46, burst('3000', '#ffd84a', '#c8323a'));
  dyn.b2 = card(scene, .46, .46, burst('2000', '#8fe89a', '#1f6a3a'));
  dyn.strike = card(scene, .46, .46, (c, w) => { c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = 58; c.beginPath(); c.moveTo(w * .14, w * .8); c.lineTo(w * .86, w * .2); c.stroke(); c.strokeStyle = '#e8303a'; c.lineWidth = 32; c.stroke(); });
  dyn.anchor = card(scene, .34, .4, drawAnchor);
  dyn.jacket = card(scene, .62, .74, drawJacket);
  dyn.cloud = card(scene, .74, .52, (c, w, h) => {
    c.lineJoin = 'round'; c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 12; cloudPath(c, w, h); c.stroke(); cloudPath(c, w, h); c.fill(); c.beginPath(); c.ellipse(w / 2, h / 2, w * .37, h * .33, 0, 0, 6.29); c.fill();
    c.fillStyle = '#c8323a'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .36}px ${FONT}`; c.fillText('3000', w / 2, h * .47); c.font = `900 ${h * .16}px ${FONT}`; c.fillText('TL', w / 2, h * .72);
  });
  dyn.dots = [.045, .07].map(r => card(scene, r * 2, r * 2, (c, w) => { c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 60; c.beginPath(); c.arc(w / 2, w / 2, w * .38, 0, 6.29); c.fill(); c.stroke(); }));
  dyn.board = card(scene, 1.0, .46, (c, w, h) => {
    c.lineJoin = 'round'; c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 24); c.fill(); c.stroke();
    c.fillStyle = '#3a3a7a'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .24}px ${FONT}`; c.fillText('Afrika ülkeleri', w / 2, h * .32);
    c.fillStyle = '#c8323a'; c.fillText("BM'nin % kaçı?", w / 2, h * .68);
  }, { pw: 768 });
  dyn.say25 = card(scene, .56, .4, bubble('%25', '10', '#e8503f'));
  dyn.say45 = card(scene, .56, .4, bubble('%45', '65', '#3f86d6'));
  dyn.boat = card(scene, .9, .7, drawBoat);
  dyn.waves = [0, 1, 2].map(() => card(scene, .6, .2, (c, w, h) => { c.lineCap = 'round'; c.strokeStyle = '#ffffff'; c.lineWidth = 16; c.beginPath(); c.moveTo(w * .05, h * .85); c.quadraticCurveTo(w * .35, -h * .5, w * .7, h * .5); c.quadraticCurveTo(w * .82, h * .85, w * .95, h * .6); c.stroke(); }, { pw: 256 }));
  dyn.fish = card(scene, .26, .16, (c, w, h) => { c.lineJoin = 'round'; c.fillStyle = '#f0a040'; c.strokeStyle = PLUM; c.lineWidth = 12; c.beginPath(); c.ellipse(w * .42, h / 2, w * .3, h * .3, 0, 0, 6.29); c.fill(); c.stroke(); c.beginPath(); c.moveTo(w * .7, h / 2); c.lineTo(w * .94, h * .18); c.lineTo(w * .94, h * .82); c.closePath(); c.fill(); c.stroke(); c.fillStyle = PLUM; c.beginPath(); c.arc(w * .28, h * .42, 9, 0, 6.29); c.fill(); });
  dyn.rope = new THREE.Mesh(new THREE.CylinderGeometry(.014, .014, 1, 8), new THREE.MeshBasicMaterial({ color: '#f1e2bd' })); dyn.rope.layers.set(1); dyn.rope.renderOrder = 19; scene.add(dyn.rope);
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .02, 'whoosh'); cue(W('Ünlü') + .12, 'whoosh'); cue(W('Tıpkı') + .1, 'whoosh');
  cue(.02, 'shimmer'); cue(W('takılır?') + .2, 'lock'); cue(W('"Üç') + .02, 'shimmer'); cue(W('Sonra') + .08, 'rise', { dur: .35 }); cue(W('iki') + .02, 'shimmer');
  cue(W('Birden') + .05, 'rise', { dur: .35 }); cue(W('çünkü') + .05, 'rise', { dur: .35 }); cue(W('çapa') + .2, 'boom'); cue(W('çapa') + .22, 'lock');
  cue(W('çarkıfelek'), 'scrape', { dur: 1.05 }); cue(W('çarkıfelek') + 1.07, 'lock'); cue(W('sonra', 2) + .05, 'rise', { dur: .35 });
  cue(W('Çark') - .05, 'scrape', { dur: .4 }); cue(W('on') + .12, 'lock'); cue(W('yirmi'), 'shimmer');
  cue(W('altmış') - .25, 'scrape', { dur: .4 }); cue(W('altmış') + .15, 'lock'); cue(W('kırk'), 'shimmer');
  cue(W('Çünkü', 2) + .05, 'rise', { dur: .35 }); cue(W('ondan'), 'stir', { dur: W('uzaklaşamıyor.') + .5 - W('ondan') }); cue(W('uzaklaşamıyor.') + .5, 'boom');
  cue(W('Tıpkı') + .3, 'wind', { dur: W('Yani') - W('Tıpkı') - .3 }); cue(W('Tıpkı') + .3, 'simmer', { dur: W('Yani') - W('Tıpkı') - .4 });
  cue(W('Yani') + .05, 'rise', { dur: .35 }); cue(W('ilk', 3), 'shimmer');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'İLK FİYAT NEDEN TAKILIR?'); }

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const SUNC = '#ffe2a0', WARM = '#ffb45a', DAYS = '#e6def2', NIGHT = '#d6d1f2';
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos);
  m.rotation.z = wob ? Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04 : 0;
  return s;
}
// something heavy dropping from above and swinging to rest
function dropCard(m, at, t, pos, base = 1, from = 1.1) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return;
  const f = Math.min(1, k / .2); m.scale.setScalar(base); m.position.copy(pos); m.position.y += (1 - f) * (1 - f) * from;
  m.rotation.z = k > .2 ? Math.sin((k - .2) * 15) * .32 * Math.exp(-(k - .2) * 4) : 0;
}
function ropeBetween(m, a, b) {
  const d = b.clone().sub(a), len = d.length(); m.position.copy(a).addScaledVector(d, .5); m.scale.set(1, len, 1);
  m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); m.visible = true;
}
function wheelAngle(t) {
  const P = Math.PI, stop = (T, A, k, d) => t > T - d && t <= T ? A - k * (T - t) ** 2 : null;
  const T1 = W('çarkıfelek') + 1.07, T2 = W('on') + .12, T3 = W('altmış') + .15;
  if (t <= T1) return stop(T1, 3 * P / 6 + 4 * P, 9, 1.1) ?? 0;
  if (t <= T2) return stop(T2, 6 * P, 16, .9) ?? 3 * P / 6;
  if (t <= T3) return stop(T3, 9 * P, 16, .9) ?? 0;
  return P;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 300 ? 'deniz' : cam.position.x > 100 ? 'deney' : 'pazar';
  for (const k of ['pazar', 'deney', 'deniz']) vis(k, where === k);
  for (const b of dyn.bBeams) b.visible = where === 'deney';
  for (const c of Object.values(cast)) c.hide();
  for (const m of [dyn.b3, dyn.b2, dyn.strike, dyn.anchor, dyn.jacket, dyn.cloud, ...dyn.dots, dyn.board, dyn.say25, dyn.say45, dyn.boat, ...dyn.waves, dyn.fish]) { m.visible = false; m.quaternion.copy(cam.quaternion); m.rotation.z = 0; m.material.opacity = 1; }
  dyn.rope.visible = false;
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const RT = V(1, 0, 0).applyQuaternion(cam.quaternion), UP = V(0, 1, 0).applyQuaternion(cam.quaternion);
  const tint = [1, .99, .98];
  let look;
  if (where === 'pazar') {
    const H = cast.kahraman, U = cast.satici;
    const hook1 = t < W('neden') + .02, hook2 = !hook1 && t < W('Bakın,') + .02;
    const L2 = t >= W('Bakın,') + .02 && t < W('Sonra') + .12, L3 = t >= W('Sonra') + .12 && t < W('Birden') + .12, L4 = t >= W('Birden') + .12 && t < W('çünkü') + .12;
    const L5 = t >= W('çünkü') + .12 && t < W('Ünlü') + .2, L8 = t > W('Çünkü', 2) && t < W('Tıpkı') + .2, L10 = t > W('Yani');
    // ---- the seller
    let up = { expr: 'smug', look: -.6, armL: [16, 10], armR: [16, 10], blink: bl(2, A('neden'), A('"Üç'), A('Sonra'), A('"Ama'), A('Birden'), A('ilk', 3), A('oyunu')) };
    if (hook1) up = { ...up, expr: 'proud', brow: .8, look: -.35, mouth: .55 + .35 * Math.abs(Math.sin(t * 16)), armL: [128, 14], armR: [26, -96] };
    if (L2 && t > A('"Üç') && t < A('diyor.') + .25) up = { ...up, expr: 'proud', brow: .8, mouth: flap(env, t), armL: [118, 12], armR: [26, -96] };
    if (L3) { const laugh = t < A('"Ama') - .03; up = laugh ? { ...up, expr: 'laugh', laughMarks: .9, mouth: .5 + .5 * Math.abs(Math.sin(t * 13)), bob: -Math.abs(Math.sin(t * 13)) * 10, armR: [28, -100], armL: [150, 20] } : { ...up, expr: 'smug', brow: .6, mouth: t < A('olur!"') + .45 ? flap(env, t) : 0, armL: [100, 14], armR: [26, -96] }; }
    if (L4 || L8) up = { ...up, expr: 'smug', lid: .1, armL: [30, -100 + 8 * Math.sin(t * 8)], armR: [30, -100 - 8 * Math.sin(t * 8)] };
    if (L10) { const lg = t > A('oyunu'); up = lg ? { ...up, expr: 'laugh', laughMarks: .9, mouth: .5 + .5 * Math.abs(Math.sin(t * 13)), bob: -Math.abs(Math.sin(t * 13)) * 9, armL: [150, 18], armR: [28, -100] } : { ...up, expr: 'smug', look: -.3, brow: .7, armL: t > A('ilk', 3) ? [150, 18] : [16, 10], armR: [28, -100] }; }
    U.show(); U.place(SAT.x, 0, SAT.z, cam, tint); U.draw({ ...up, lit: -1, shade: DAYS, rim: { color: SUNC, a: .3 } }); U.castFrom(dyn.aSun, true);
    // ---- the hero
    let hx = HERO.x, hp = { expr: 'neutral', look: .5, armL: [14, 8], armR: [14, 8], blink: bl(1, A('takılır?'), A('lira!"'), A('Birden'), A('çünkü'), A('çapa'), A('ondan'), A('uzaklaşamıyor.') + .5, A('Yani')) };
    if (hook2) hp = t < A('takılır?') + .2 ? { ...hp, expr: 'surprised', look: .7, brow: 1, mouth: .6 } : { ...hp, expr: 'worried', look: .6, lookY: -.2, mouth: 0, sweat: 1 };
    if (L2) hp = t < A('"Üç') ? { ...hp, expr: 'smile', look: .7, armR: t > A('ceket') - .2 ? [84, 14] : [14, 8], mouth: t > A('ceket') && t < A('ve') ? flap(env, t) * .7 : 0 } : { ...hp, expr: 'surprised', look: .6, lookY: -.5, brow: 1, mouth: .7, armL: [40, 120], armR: [40, 120] };
    if (L3) hp = { ...hp, expr: 'worried', look: .8 };
    if (L4) hp = t < A('geliyor,') + .5 ? { ...hp, expr: 'grin', look: .5, lookY: -.3, armL: [150, 20], armR: [150, 20], bob: -Math.abs(Math.sin(t * 9)) * 8 } : { ...hp, expr: 'smile', look: .4, lookY: -.4 };
    if (L5) hp = t < A('çapa') + .2 ? { ...hp, expr: t > A('aklın') ? 'neutral' : 'smile', look: .45, lookY: -.75, gazeY: -1, brow: .6 } : { ...hp, expr: 'surprised', look: .45, lookY: -.7, brow: 1, mouth: .6 };
    let pullK = 0;
    if (L8) {
      const snap = W('uzaklaşamıyor.') + .5;
      pullK = t < snap ? ramp(t, A('ondan') - .1, A('ondan') + .5) : Math.exp(-(t - snap) * 9) * Math.cos((t - snap) * 22);
      hx = HERO.x - .03 * pullK;
      hp = t < A('ondan') - .1 ? { ...hp, expr: 'worried', look: .5, lookY: -.6, gazeY: -1 } : t < snap ? { ...hp, expr: 'angry', look: -.8, sweat: 1, mouth: .3 + .2 * Math.abs(Math.sin(t * 18)), lean: -4 * pullK + Math.sin(t * 40) * .6, armL: [82, 14], armR: [-56, -18] } : { ...hp, expr: 'worried', look: .2, lookY: -.3, mouth: .4, lean: -4 * pullK, sweat: 1 };
    }
    if (L10) hp = { ...hp, expr: 'smile', look: .35, armR: [96, -60], armL: [20, 10], bob: 0 };
    H.show(); H.place(hx, 0, HERO.z, cam, tint); H.draw({ ...hp, lit: -1, shade: DAYS, rim: { color: SUNC, a: .3 } }); H.castFrom(dyn.aSun, true);
    // ---- the jacket: on the rack, in the end in the hero's hand
    dyn.jacket.visible = true;
    if (L10) { const hd = H.hand(1); dyn.jacket.position.copy(hd).addScaledVector(UP, -.2).addScaledVector(RT, .04); dyn.jacket.position.z += .03; dyn.jacket.scale.setScalar(.72); dyn.jacket.rotation.z = Math.sin(t * 3) * .04; }
    else { dyn.jacket.position.copy(JKT); dyn.jacket.scale.setScalar(1); }
    // ---- the prices
    if (hook1) { popCard(dyn.b3, -.3, t, V(SAT.x - .5, 1.63, SAT.z + .05), 1 + .05 * Math.sin(t * 12)); }
    if (hook2) { popCard(dyn.b3, W('neden') + .1, t, V(HERO.x + .47, 1.74, HERO.z + .05), .72); dropCard(dyn.anchor, A('takılır?'), t, V(HERO.x + .47, 1.42, HERO.z + .06), .82, .9); }
    if (L2) popCard(dyn.b3, A('"Üç') - .02, t, V(.05, 2.4, -1.0), 1.15);
    if (L3) { dyn.b3.visible = true; dyn.b3.position.set(SAT.x - .5, 1.98, SAT.z + .05); dyn.b3.scale.setScalar(.85); popCard(dyn.strike, A('"Ama'), t, V(SAT.x - .5, 1.98, SAT.z + .06), .85, false); popCard(dyn.b2, A('iki'), t, V(SAT.x - .52, 1.5, SAT.z + .05), 1.05); }
    if (L4) { dyn.b3.visible = dyn.strike.visible = true; dyn.b3.position.set(-.22, 2.42, -1.0); dyn.strike.position.set(-.22, 2.42, -.99); dyn.b3.scale.setScalar(.8); dyn.strike.scale.setScalar(.8); dyn.b2.visible = true; dyn.b2.position.set(.34, 2.36, -1.0); dyn.b2.scale.setScalar(1.1 + .06 * Math.sin(t * 9)); }
    if (L5) {
      const head = V(HERO.x, 1.49, HERO.z), at2 = (r, u) => head.clone().addScaledVector(RT, r).addScaledVector(UP, u), t0 = A('aklın') - .1;
      dyn.dots.forEach((m, i) => popCard(m, t0 + i * .1, t, at2(.2 + i * .1, .3 + i * .12), 1, false));
      const s = popCard(dyn.cloud, t0 + .22, t, at2(.3, .7)); if (s) dyn.cloud.position.y += Math.sin(t * 2) * .012;
      dropCard(dyn.anchor, A('çapa'), t, at2(.3, .36).add(V(0, 0, .02)), .9, 1.0);
    }
    if (L8) {
      const ap = V(.05, 2.05, -1.0); dyn.b3.visible = true; dyn.b3.position.set(.05, 2.47, -1.0); dyn.b3.scale.setScalar(1.05);
      dyn.anchor.visible = true; dyn.anchor.position.copy(ap); dyn.anchor.scale.setScalar(1); dyn.anchor.rotation.z = -.5 * pullK;
      ropeBetween(dyn.rope, ap.clone().add(V(-.05 * pullK, -.17, .01)), H.toWorld(0, 500).add(V(0, 0, .03)));
    }
    if (L10) {
      dyn.b2.visible = true; dyn.b2.position.set(HERO.x + .02, 2.2, HERO.z); dyn.b2.scale.setScalar(.9);
      if (t > A('ilk', 3)) { const hd = U.hand(-1); if (hd) popCard(dyn.anchor, A('ilk', 3), t, hd.add(V(-.02, .2, .03)), 1.0); }
    }
    for (const b of dyn.bulbs) b.visible = true;
    const f = hook1 || L3 ? V(SAT.x, 1.5, SAT.z) : V(HERO.x, 1.5, HERO.z);
    look = { focus: cam.position.distanceTo(f), coc: 4, range: 2.6, sat: 1.3, lift: [.1, .095, .15], bloom: .6, vignette: .18 };
  } else if (where === 'deney') {
    dyn.wheel.rotation.z = wheelAngle(t);
    const Ho = cast.hoca, d1 = cast.denek1, d2 = cast.denek2;
    const push = t > A('çarkıfelek') - .25 && t < A('çarkıfelek') + .3;
    Ho.show(); Ho.place(HOCA.x, 0, HOCA.z, cam, tint);
    Ho.draw({ expr: t > A('çevrildi,') + .5 ? 'proud' : 'focused', look: -.75, lookY: -.2, armL: push ? [120, 6] : [22, 12], armR: [20, 10], lean: push ? -4 : 0, blink: bl(3, A('çarkıfelek'), A('çevrildi,') + .5), lit: -1, shade: NIGHT, rim: { color: WARM, a: .4 } });
    Ho.castFrom(LAMPB[0]);
    const q = t < A('Çark'), s25 = t > A('yirmi'), s45 = t > A('kırk');
    d1.show(); d1.place(D1.x, 0, D1.z, cam, tint);
    d1.draw({ expr: q ? 'worried' : s25 ? 'proud' : 'focused', look: q ? .2 : s45 ? .7 : .1, lookY: q ? -.7 : 0, gazeY: q ? -1 : 0, brow: q ? .6 : 0, armR: q ? [150, -50] : s25 && !s45 ? [150, 20] : [16, 10], armL: [16, 10], mouth: s25 && t < A('beşte,') + .4 ? .5 + .3 * Math.sin(t * 20) : 0,
      blink: bl(4, A('Çark'), A('yirmi'), A('kırk')), lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } });
    d2.show(); d2.place(D2.x, 0, D2.z, cam, tint);
    d2.draw({ expr: q ? 'worried' : s45 ? 'proud' : s25 ? 'surprised' : 'neutral', look: q ? -.2 : s45 ? -.1 : -.7, lookY: q ? -.7 : 0, gazeY: q ? -1 : 0, brow: q ? .6 : 0, armL: q ? [40, 150] : s45 ? [150, 20] : [16, 10], armR: [16, 10], mouth: s45 && t < A('beşte', 2) + .4 ? .5 + .3 * Math.sin(t * 20) : 0,
      blink: bl(5, A('Çark'), A('yirmi'), A('kırk')), lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } });
    d1.castFrom(LAMPB[1]); d2.castFrom(LAMPB[1]);
    if (q && t > A('insanlara') - .05) popCard(dyn.board, A('insanlara') - .05, t, V(203.0, 2.3, -1.15), 1, true);
    if (s25) popCard(dyn.say25, A('yirmi'), t, V(D1.x - .02, 2.02, D1.z + .05), 1.1);
    if (s45) popCard(dyn.say45, A('kırk'), t, V(D2.x + .02, 2.02, D2.z + .05), 1.1);
    const f = cam.position.x > 201.5 ? V(203, 1.45, -1.2) : V(WH.x, WH.y, WH.z);
    look = { focus: cam.position.distanceTo(f), coc: 4, range: 2.4, sat: 1.25, lift: [.1, .095, .18], bloom: .8, vignette: .22 };
  } else {
    // ---- the boat circles its anchor: a wave carries it off, the rope brings it back
    const t0 = W('Tıpkı'), ph = (t - t0) * 2.0, bx = SEA.x + .38 * Math.sin(ph) + .1 * ramp(t, A('dalga'), A('dalga') + .4) * Math.sin(ph * 2.3);
    const by = SEA.surf + .33 + .05 * Math.sin(ph * 2.1 + 1);
    dyn.boat.visible = true; dyn.boat.position.set(bx, by, SEA.z); dyn.boat.rotation.z = -.1 * Math.cos(ph) + .04 * Math.sin(ph * 2.1);
    const ap = V(SEA.x, SEA.bed + .16, SEA.z);
    dyn.anchor.visible = true; dyn.anchor.position.copy(ap); dyn.anchor.scale.setScalar(1.25); dyn.anchor.rotation.z = 2.75;
    ropeBetween(dyn.rope, ap.clone().add(V(.08, .2, -.01)), V(bx - .12, by - .3, SEA.z - .01));
    dyn.waves.forEach((m, i) => { const u = ((t - t0) * .32 + i / 3) % 1; m.visible = true; m.position.set(SEA.x - 1.3 + u * 2.6, SEA.surf + .04 + .03 * Math.sin(u * 20), SEA.z + .05); m.material.opacity = Math.sin(Math.PI * u); m.scale.setScalar(.7 + .5 * Math.sin(Math.PI * u)); });
    dyn.fish.visible = true; dyn.fish.position.set(SEA.x + .9 - ((t - t0) * .22) % 2.0, 1.75 + .05 * Math.sin(t * 3), SEA.z + .2);
    look = { focus: 5.8, coc: 0, range: 9, sat: 1.3, lift: [.09, .09, .14], bloom: .7, vignette: .15 };
  }
  look.tint = [1, 1, 1];
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
