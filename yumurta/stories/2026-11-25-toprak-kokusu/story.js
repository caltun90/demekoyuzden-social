// Yağmurdan sonra toprak neden kokar? Demek O Yüzden günlük Short (yumurta stili), 25 Kasım 2026.
// Bilgi: koku yağmurdan değil topraktan gelir. Toprak bakterileri (Streptomyces) geosmin üretir; damla gözenekli toprağa
// çarpınca içinde hava kabarcıkları hapsolur, yükselip patlar ve minik damlacıkları (aerosol) havaya saçar. Kaynaklar SCRIPT.md'de.
// Setler: BAHÇE (x≈0) yaz yağmuru, alçak mavi taş duvar + bulut arasından güneş; TOPRAK (x≈200) karınca boyundan toprak,
// "bakteri" işçileri ve geosmin şişesi (benzetme), sağda (x≈204) düşen damla.
import * as THREE from 'three';
import { stoneTex, woodTex, painted, flat } from '/engine/src/paint.js';
import { Toon, Arm3D, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, glow } from '/engine/src/fx.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-25-toprak-kokusu';
export const FPS = 30;
export let DUR = 37.9;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lerpN = (a, b, k) => a + (b - a) * k;
const clamp01 = x => Math.max(0, Math.min(1, x));
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const backOut = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2;
const hash = (i, k) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
let W, cast = {}, sets = {}, dyn = {}, smokes = {};

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
// The raindrop on the soil. fall 0..1: the drop is still falling; a: seconds since it hit; trap 0..1: air bubbles caught
// under it; rise: seconds since the bubbles started to rise (they climb, burst at the top and throw tiny droplets up).
function drawDrop(g, w, h, fall, a, trap, rise) {
  g.lineCap = g.lineJoin = 'round';
  const cx = w / 2, base = h * .9, RX = w * .335, RY = h * .25, u = w / 512;
  if (fall < 1) {
    const r = w * .13, y = lerpN(-r, base - r * 1.1, fall * fall);
    g.strokeStyle = 'rgba(225,240,255,.8)'; g.lineWidth = 9 * u;
    for (const dx of [-.6, 0, .6]) { g.beginPath(); g.moveTo(cx + dx * r, y - r * 2.1); g.lineTo(cx + dx * r, y - r * (3.0 + (dx ? 0 : .7))); g.stroke(); }
    g.beginPath(); g.moveTo(cx, y - r * 1.75); g.quadraticCurveTo(cx + r * 1.15, y - r * .2, cx + r * .82, y + r * .5);
    g.arc(cx, y + r * .1, r * .92, .45, Math.PI - .45); g.quadraticCurveTo(cx - r * 1.15, y - r * .2, cx, y - r * 1.75); g.closePath();
    g.fillStyle = '#8fc8ff'; g.fill(); g.strokeStyle = PLUM; g.lineWidth = 11 * u; g.stroke();
    g.strokeStyle = 'rgba(255,255,255,.85)'; g.lineWidth = 9 * u; g.beginPath(); g.arc(cx, y + r * .1, r * .6, Math.PI * 1.05, Math.PI * 1.4); g.stroke();
    return;
  }
  const sq = 1 + .3 * Math.exp(-a * 7) * Math.cos(a * 22), rx = RX * sq, ry = RY / sq;
  // the wet patch and the splash
  g.fillStyle = 'rgba(84,46,30,.42)'; g.beginPath(); g.ellipse(cx, base + 5 * u, rx * 1.12, 15 * u, 0, 0, 6.29); g.fill();
  if (a < .4) {
    g.fillStyle = '#8fc8ff'; g.strokeStyle = PLUM; g.lineWidth = 6 * u;
    for (let i = 0; i < 6; i++) { const sd = i % 2 ? 1 : -1, k = a / .4, vx = (1.05 + (i >> 1) * .22) * sd, px = cx + vx * RX * (1 + k * .7), py = base - (Math.sin(k * Math.PI) * (.5 + (i >> 1) * .28)) * RY; g.beginPath(); g.arc(px, py, (11 - (i >> 1) * 2) * u * (1 - k * .5), 0, 6.29); g.fill(); g.stroke(); }
  }
  const dome = () => { g.beginPath(); g.ellipse(cx, base, rx, ry, 0, Math.PI, 0); g.closePath(); };
  const gr = g.createLinearGradient(0, base - ry, 0, base); gr.addColorStop(0, 'rgba(176,222,255,.86)'); gr.addColorStop(1, 'rgba(96,170,246,.86)');
  dome(); g.fillStyle = gr; g.fill();
  // bubbles
  const N = 6, P = 1.5, UP = .62, topAt = x => base - ry * Math.sqrt(Math.max(0, 1 - ((x - cx) / rx) ** 2));
  const bubble = (x, y, r, k = 1) => { g.fillStyle = 'rgba(255,255,255,.92)'; g.strokeStyle = PLUM; g.lineWidth = 6 * u; g.beginPath(); g.arc(x, y, r * k, 0, 6.29); g.fill(); g.stroke(); g.fillStyle = '#bfe2ff'; g.beginPath(); g.arc(x + r * .25 * k, y + r * .25 * k, r * .42 * k, 0, 6.29); g.fill(); };
  const bursts = [];
  if (trap > 0) for (let i = 0; i < N; i++) {
    const x0 = cx + (i - 2.5) * rx * .31, r = (15 + (i % 3) * 5) * u, y0 = base - r - 5 * u, yt = topAt(x0), ph = rise - i * .23;
    if (ph <= 0) { bubble(x0, y0, r, backOut(clamp01(trap * 1.6 - i * .1))); continue; }
    const c = ph % P, cyc = Math.floor(ph / P);
    if (c < UP) { const k = c / UP, e = k * k * (3 - 2 * k); bubble(x0 + Math.sin(c * 14 + i) * 5 * u, lerpN(y0, yt + r * .3, e), r); }
    else if (c > UP + .5) bubble(x0, y0, r, backOut((c - UP - .5) / .3));
    for (let q = 0; q <= Math.min(cyc, 1); q++) { const age = c - UP + q * P; if (age >= 0) bursts.push({ x: x0, y: yt, r, age, i }); }
  }
  g.save(); dome(); g.clip(); g.strokeStyle = 'rgba(255,255,255,.8)'; g.lineWidth = 12 * u; g.beginPath(); g.ellipse(cx, base, rx * .8, ry * .8, 0, Math.PI * 1.1, Math.PI * 1.36); g.stroke(); g.restore();
  dome(); g.strokeStyle = PLUM; g.lineWidth = 11 * u; g.stroke();
  // the bursts: a ring that opens, then droplets that carry the smell upward
  for (const b of bursts) {
    if (b.age < .26) { const k = b.age / .26; g.globalAlpha = 1 - k; g.strokeStyle = '#ffffff'; g.lineWidth = 7 * u; g.beginPath(); g.arc(b.x, b.y, b.r * (1 + k * 1.7), 0, 6.29); g.stroke();
      g.strokeStyle = PLUM; g.lineWidth = 5 * u; for (let j = 0; j < 5; j++) { const an = -Math.PI * (.15 + j * .175); g.beginPath(); g.moveTo(b.x + Math.cos(an) * b.r * (1.3 + k), b.y + Math.sin(an) * b.r * (1.3 + k)); g.lineTo(b.x + Math.cos(an) * b.r * (1.9 + k * 1.4), b.y + Math.sin(an) * b.r * (1.9 + k * 1.4)); g.stroke(); } g.globalAlpha = 1; }
    for (let j = 0; j < 3; j++) {
      const al = clamp01(1 - b.age / 2.3); if (al <= 0) continue;
      const x = b.x + (j - 1) * 20 * u * (1 + b.age) + Math.sin(b.age * 4 + j * 2 + b.i) * 16 * u * b.age, y = b.y - 10 * u - b.age * (150 + j * 34) * u;
      g.globalAlpha = al; g.fillStyle = '#d6f59a'; g.strokeStyle = '#4c7a2a'; g.lineWidth = 4 * u; g.beginPath(); g.arc(x, y, (7 + (j + b.i) % 3 * 2) * u, 0, 6.29); g.fill(); g.stroke();
    }
    g.globalAlpha = 1;
  }
}
// the neighbour's umbrella (the handle's foot is at the bottom centre of the card)
function drawUmbrella(c, w, h) {
  c.lineCap = c.lineJoin = 'round';
  const cx = w / 2, top = h * .06, rim = h * .36, R = w * .46;
  c.strokeStyle = PLUM; c.lineWidth = 22; c.beginPath(); c.moveTo(cx, rim - 10); c.lineTo(cx, h * .96); c.stroke();
  c.strokeStyle = '#a8683a'; c.lineWidth = 10; c.beginPath(); c.moveTo(cx, rim); c.lineTo(cx, h * .955); c.stroke();
  const canopy = () => { c.beginPath(); c.moveTo(cx - R, rim); c.quadraticCurveTo(cx - R * .95, top, cx, top); c.quadraticCurveTo(cx + R * .95, top, cx + R, rim);
    for (let i = 3; i >= 0; i--) { const x1 = cx - R + (i + 1) * R / 2, x0 = cx - R + i * R / 2; c.quadraticCurveTo((x0 + x1) / 2, rim - h * .07, x0, rim); } c.closePath(); };
  canopy(); c.fillStyle = '#e2463f'; c.fill();
  c.save(); canopy(); c.clip(); c.fillStyle = '#fbf3e2';
  for (const k of [-1, 1]) { c.beginPath(); c.moveTo(cx, top - 10); c.quadraticCurveTo(cx + k * R * .42, top + 20, cx + k * R * .5, rim + 10); c.lineTo(cx + k * R * 1.02, rim + 10); c.quadraticCurveTo(cx + k * R * .9, top + 6, cx, top - 10); c.closePath(); c.fill(); }
  c.fillStyle = 'rgba(60,20,60,.16)'; c.fillRect(cx + R * .2, 0, R, h); c.restore();
  canopy(); c.strokeStyle = PLUM; c.lineWidth = 14; c.stroke();
  c.fillStyle = PLUM; c.beginPath(); c.arc(cx, top - 4, 12, 0, 6.29); c.fill();
}
// a glass of soda: bubbles climb and burst above the rim (tau = seconds)
function drawGlass(g, w, h, tau) {
  g.lineCap = g.lineJoin = 'round';
  const cx = w / 2, top = h * .42, bot = h * .95, tw = w * .3, bw = w * .23;
  const body = () => { g.beginPath(); g.moveTo(cx - tw, top); g.lineTo(cx - bw, bot); g.lineTo(cx + bw, bot); g.lineTo(cx + tw, top); g.closePath(); };
  body(); g.fillStyle = 'rgba(235,246,255,.55)'; g.fill();
  g.save(); body(); g.clip(); g.fillStyle = '#ffd95a'; g.fillRect(0, top + h * .06, w, h); g.fillStyle = '#fff3b8'; g.fillRect(0, top + h * .06, w, h * .03);
  for (let i = 0; i < 9; i++) { const c = (tau * 1.5 + i * .37) % 1, x = cx + (hash(i, 1) - .5) * bw * 1.7, y = lerpN(bot - 10, top + h * .07, c); g.fillStyle = 'rgba(255,255,255,.95)'; g.beginPath(); g.arc(x + Math.sin(c * 9 + i) * 4, y, 5 + (i % 3) * 2.5, 0, 6.29); g.fill(); }
  g.restore(); body(); g.strokeStyle = PLUM; g.lineWidth = 12; g.stroke();
  for (let i = 0; i < 7; i++) {
    const c = (tau * 1.25 + i / 7) % 1, x = cx + (hash(i, 2) - .5) * tw * 1.7 + Math.sin(c * 6 + i) * 8, y = top - c * h * .4;
    g.globalAlpha = 1 - c; g.fillStyle = '#fff6c2'; g.strokeStyle = PLUM; g.lineWidth = 4; g.beginPath(); g.arc(x, y, 6 + (i % 2) * 3, 0, 6.29); g.fill(); g.stroke();
    if (c < .22) { g.strokeStyle = '#ffffff'; g.lineWidth = 5; g.beginPath(); g.arc(x, top - 4, 12 + c * 60, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); }
  }
  g.globalAlpha = 1;
}
// the perfume flask of the bacteria
function drawFlask(c, w, h) {
  c.lineCap = c.lineJoin = 'round';
  const cx = w * .46, by = h * .64, R = w * .36;
  const body = () => { c.beginPath(); c.moveTo(cx - w * .09, h * .2); c.lineTo(cx - w * .09, h * .34); c.quadraticCurveTo(cx - R * 1.15, h * .42, cx - R, by); c.quadraticCurveTo(cx - R, h * .96, cx, h * .96); c.quadraticCurveTo(cx + R, h * .96, cx + R, by); c.quadraticCurveTo(cx + R * 1.15, h * .42, cx + w * .09, h * .34); c.lineTo(cx + w * .09, h * .2); c.closePath(); };
  body(); c.fillStyle = '#eaf6ff'; c.fill();
  c.save(); body(); c.clip(); c.fillStyle = '#9be36a'; c.fillRect(0, h * .47, w, h); c.fillStyle = '#c8f59a'; c.fillRect(0, h * .47, w, h * .025);
  c.fillStyle = 'rgba(255,255,255,.75)'; for (const [x, y, r] of [[-.2, .56, 9], [.22, .53, 7], [.02, .9, 8], [-.24, .86, 6], [.25, .88, 7]]) { c.beginPath(); c.arc(cx + x * w, y * h, r, 0, 6.29); c.fill(); }
  c.restore(); body(); c.strokeStyle = PLUM; c.lineWidth = 14; c.stroke();
  // the cap and the squeeze bulb
  c.fillStyle = '#e8b23e'; c.beginPath(); c.roundRect(cx - w * .13, h * .1, w * .26, h * .11, 10); c.fill(); c.stroke();
  c.lineWidth = 16; c.strokeStyle = PLUM; c.beginPath(); c.moveTo(cx + w * .13, h * .15); c.quadraticCurveTo(w * .74, h * .1, w * .8, h * .2); c.stroke();
  c.lineWidth = 7; c.strokeStyle = '#e8b23e'; c.beginPath(); c.moveTo(cx + w * .13, h * .15); c.quadraticCurveTo(w * .74, h * .1, w * .8, h * .2); c.stroke();
  c.fillStyle = '#d8483a'; c.strokeStyle = PLUM; c.lineWidth = 12; c.beginPath(); c.ellipse(w * .84, h * .27, w * .11, h * .085, .3, 0, 6.29); c.fill(); c.stroke();
  c.beginPath(); c.moveTo(cx - w * .13, h * .15); c.lineTo(cx - w * .24, h * .15); c.stroke();
  // the label
  c.fillStyle = '#fbf7ee'; c.lineWidth = 9; c.beginPath(); c.roundRect(cx - R * .86, h * .6, R * 1.72, h * .2, 14); c.fill(); c.stroke();
  c.fillStyle = '#2f6a2a'; c.font = `900 ${w * .118}px "Arial Black", "Inter", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('GEOSMİN', cx, h * .705);
}

// ---------------------------------------------------------------- BAHÇE (x = 0): a summer afternoon, the first drops
const HERO = { x: -.3, z: -.7 }, KOMSU = { x: .6, z: -.85 }, HOCA = { x: -2.75, z: -1.05 };
const SPOT = V(.2, 0, .35), TRIPOD = V(-2.2, 0, -.6), SUNPOS = V(-2.6, 6.3, -13.1);
const SUNDIR = V(2.0, -9, 6.6).normalize();
function skyTex(storm) {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 512; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#5f7fc6'); gr.addColorStop(.6, '#a8c2ee'); gr.addColorStop(1, '#e6f0ff'); g.fillStyle = gr; g.fillRect(0, 0, 1024, 512);
  if (storm) {
    const sx = (SUNPOS.x + 30) / 60 * 1024, sy = (16.5 - SUNPOS.y) / 18 * 512;
    const sg = g.createRadialGradient(sx, sy, 6, sx, sy, 170); sg.addColorStop(0, 'rgba(255,240,196,.95)'); sg.addColorStop(1, 'rgba(255,240,196,0)'); g.fillStyle = sg; g.fillRect(0, 0, 1024, 512);
    const cloud = (x, y, s, col) => { g.fillStyle = col; g.beginPath(); for (let k = 0; k < 7; k++) g.arc(x + (k - 3) * s * .5, y + Math.sin(k * 2.1) * s * .16, s * (.42 + .1 * Math.sin(k * 3.3)), 0, 6.29); g.fill(); g.fillRect(x - s * 1.6, y, s * 3.2, s * .42); };
    cloud(430, 150, 40, '#7f93c4'); cloud(560, 228, 34, '#93a6d2'); cloud(505, 96, 28, '#8a9dcc'); cloud(455, 262, 24, '#aebde0'); cloud(590, 140, 30, '#7286b8'); cloud(520, 300, 20, '#b9c7e6'); cloud(600, 60, 26, '#7f93c4');
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function buildBahce(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(16, 10), painted(stoneTex({ base: '#c99668', seam: '#a8744c', bw: 128, bh: 128, rep: [9, 6], seed: 7 })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 0); g.add(fl);
  const sky = new THREE.Mesh(new THREE.PlaneGeometry(60, 18), new THREE.MeshBasicMaterial({ map: skyTex(true) })); sky.position.set(0, 7.5, -13.5); g.add(sky);
  const sun = new THREE.Mesh(new THREE.SphereGeometry(.62, 24, 16), new THREE.MeshBasicMaterial({ color: HDR(2.5, 2.0, 1.15) })); sun.position.copy(SUNPOS); g.add(sun);
  // the low garden wall: cool stone, a darker band, a pale cap, flower pots on it
  const wall = new THREE.Mesh(new THREE.BoxGeometry(16, 1.25, .3), painted(stoneTex({ base: '#8fa5d2', seam: '#6278ac', bw: 96, bh: 48, rep: [10, 1.4] }))); wall.position.set(0, .625, -2.85); g.add(wall);
  const band = new THREE.Mesh(new THREE.BoxGeometry(16, .34, .06), painted(stoneTex({ base: '#6f86b8', seam: '#51669a', bw: 128, bh: 128, rep: [18, 1] }))); band.position.set(0, .2, -2.67); g.add(band);
  const cap = new THREE.Mesh(new THREE.BoxGeometry(16, .09, .42), flat('#eef3fb')); cap.position.set(0, 1.29, -2.85); g.add(cap);
  for (const [px, col] of [[-2.2, '#e85a6a'], [-.95, '#f2c23a'], [1.25, '#e85a6a'], [2.5, '#f08a3a']]) {
    const pot = new THREE.Mesh(new THREE.CylinderGeometry(.15, .11, .22, 14), flat('#c9603c')); pot.position.set(px, 1.45, -2.82); g.add(pot);
    const leaf = new THREE.Mesh(new THREE.IcosahedronGeometry(.19, 1), flat('#3f9a5c')); leaf.position.set(px, 1.68, -2.82); g.add(leaf);
    for (const [dx, dy, dz] of [[-.1, .1, .08], [.11, .13, .05], [0, .2, .1]]) { const f = new THREE.Mesh(new THREE.IcosahedronGeometry(.06, 0), flat(col)); f.position.set(px + dx, 1.68 + dy, -2.82 + dz); g.add(f); }
  }
  // the hedge and two trees behind the wall
  for (let i = 0; i < 9; i++) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(.95 + (i % 3) * .14, 1), flat(i % 2 ? '#2f8a66' : '#3a9a6a')); b.position.set(-6 + i * 1.5, 1.05 + (i % 2) * .16, -4.3 - (i % 3) * .2); g.add(b); }
  for (const [tx, tz, s] of [[-3.3, -6.2, 1], [3.6, -6.8, 1.15]]) {
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(.16 * s, .22 * s, 3.2 * s, 10), flat('#7a5644')); tr.position.set(tx, 1.6 * s, tz); g.add(tr);
    const cr = new THREE.Mesh(new THREE.IcosahedronGeometry(1.6 * s, 1), flat('#2a7f6a')); cr.position.set(tx, 3.9 * s, tz); g.add(cr);
    const cr2 = new THREE.Mesh(new THREE.IcosahedronGeometry(1.1 * s, 1), flat('#36936f')); cr2.position.set(tx + .9 * s, 3.2 * s, tz + .3); g.add(cr2);
  }
  // the researcher's fast camera on a tripod, looking down at the soil
  const metal = flat('#3a4066'), head = V(TRIPOD.x, 1.02, TRIPOD.z);
  for (let k = 0; k < 3; k++) { const an = k / 3 * 6.283 + .5, foot = V(TRIPOD.x + Math.cos(an) * .34, 0, TRIPOD.z + Math.sin(an) * .34), d = head.clone().sub(foot), l = new THREE.Mesh(new THREE.CylinderGeometry(.018, .022, d.length(), 8), metal);
    l.position.copy(foot).addScaledVector(d, .5); l.quaternion.setFromUnitVectors(V(0, 1, 0), d.clone().normalize()); g.add(l); }
  const camG = new THREE.Group(); camG.position.copy(head); camG.position.y += .1; camG.rotation.order = 'YXZ'; camG.rotation.y = -1.05; camG.rotation.x = .55; g.add(camG);
  const body = new THREE.Mesh(new THREE.BoxGeometry(.2, .2, .32), flat('#4a5078')); camG.add(body);
  const lens = new THREE.Mesh(new THREE.CylinderGeometry(.075, .085, .16, 18), flat('#2a2f52')); lens.rotation.x = Math.PI / 2; lens.position.z = .24; camG.add(lens);
  const glass = new THREE.Mesh(new THREE.CylinderGeometry(.06, .06, .02, 18), new THREE.MeshBasicMaterial({ color: '#9fd0ff' })); glass.rotation.x = Math.PI / 2; glass.position.z = .325; glass.userData.noShadow = true; camG.add(glass);
  dyn.recMat = new THREE.MeshBasicMaterial({ color: '#7a2a2a' });
  const rec = new THREE.Mesh(new THREE.SphereGeometry(.024, 10, 8), dyn.recMat); rec.position.set(.06, .115, -.1); rec.userData.noShadow = true; camG.add(rec);
  dyn.camGrip = V(TRIPOD.x - .12, 1.16, TRIPOD.z - .1);
  // rain: thin streaks (layer 1, no ink)
  const rg = new THREE.CylinderGeometry(.006, .006, .26, 5), rm = new THREE.MeshBasicMaterial({ color: '#eaf4ff', transparent: true, opacity: .8, depthWrite: false });
  dyn.rain = new THREE.InstancedMesh(rg, rm, 300); dyn.rain.layers.set(1); dyn.rain.frustumCulled = false; scene.add(dyn.rain);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#cfe0ff', '#b89a90', 1.55));
  const key = new THREE.DirectionalLight('#ffe2b0', 2.5); key.position.copy(V(0, 0, -.6).addScaledVector(SUNDIR, -11)); key.target.position.set(0, 0, -.6);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: .5, far: 24 }); key.shadow.bias = -.0006; key.shadow.normalBias = .02; key.shadow.radius = 3;
  L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .75); fill.position.set(1.5, 3, 8); fill.target.position.set(0, 1, -2); L.add(fill); L.add(fill.target);
  scene.add(L); sets.bahce = { g, L };
  shadows(g);
  dyn.sunGlow = glow(scene, SUNPOS.toArray(), '#ffe2a0', 4.2, .38);
}

// ---------------------------------------------------------------- TOPRAK (x = 200): the soil, seen from an ant's height
const BAK = [{ x: -.82, z: -1.0 }, { x: .8, z: -1.35 }], ROCK = V(200, .5, -1.25), DROP = V(204.2, 1.2, -1.5);
const NOZZLE = V(200.27, 1.5, -1.2);
function buildToprak(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(34, 22), painted(stoneTex({ base: '#c08a5c', seam: '#9a6640', bw: 128, bh: 128, rep: [15, 10], seed: 5 })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(1, 0, -4); g.add(fl);
  const sky = new THREE.Mesh(new THREE.PlaneGeometry(70, 16), new THREE.MeshBasicMaterial({ map: skyTex(false) })); sky.position.set(2, 7.5, -14.5); g.add(sky);
  // the flat stone the flask stands on, pebbles, crumbs of soil, grass blades as tall as towers
  const rock = new THREE.Mesh(new THREE.CylinderGeometry(.5, .6, ROCK.y, 9), flat('#93a3cc')); rock.position.set(0, ROCK.y / 2, ROCK.z); g.add(rock);
  for (const [x, z, r, col] of [[-2.3, -3.4, .5, '#8a9cc8'], [2.2, -2.9, .36, '#a3b2d8'], [5.6, -3.6, .6, '#8a9cc8'], [2.9, -.4, .22, '#b3bfe0'], [-1.9, .2, .2, '#a3b2d8'], [6.2, -.6, .28, '#93a3cc'], [3.3, -4.6, .42, '#a3b2d8'],
    [-.5, -3.0, .3, '#a8744c'], [1.7, -4.1, .4, '#b07a50'], [4.6, -3.0, .26, '#a8744c'], [5.3, -1.9, .18, '#b07a50'], [3.2, -2.3, .16, '#a8744c']]) {
    const p = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 0), flat(col)); p.position.set(x, r * .45, z); p.rotation.set(x, z, x * z); g.add(p); }
  for (const [x, z, hh, lean] of [[-3.2, -6.5, 6.5, .12], [-1.2, -8, 7.5, -.08], [1.6, -7.2, 6.8, .1], [3.4, -8.4, 7.8, -.1], [5.4, -7, 6.4, .07], [7.2, -8, 7.2, -.12], [-5, -8, 7, .1], [2.6, -6.3, 5.2, -.14]]) {
    const b = new THREE.Mesh(new THREE.ConeGeometry(.42, hh, 5), flat(x % 2 > 1 ? '#3f9a5c' : '#2f8a66')); b.position.set(x, hh / 2, z); b.rotation.z = lean; b.scale.z = .35; g.add(b); }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#dfe6ff', '#c79aa8', 1.6));
  const sunDir = V(.55, -1, -.6).normalize(); dyn.bSun = sunDir;
  const sun = new THREE.DirectionalLight('#ffe1b0', 2.4); sun.position.copy(V(202, 0, -2).addScaledVector(sunDir, -11)); sun.target.position.set(202, 0, -2);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: .5, far: 26 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
  L.add(sun); L.add(sun.target);
  scene.add(L); sets.toprak = { g, L };
  shadows(g);
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  kahraman: { hair: '#3a2a24', cloth: '#f2c23a', collar: true, height: 1.7 },
  komsu: { mustache: '#5a4a48', hair: '#8a8088', hat: 'kulah', hatColor: '#3f6fb8', cloth: '#c8483a', buttons: '#f1e2bd', pocket: true, bodyW: 236, headW: 282, headH: 256, height: 1.78 },
  hoca: { beard: '#e4e4ee', beardLen: .7, hair: '#d9d9e4', cloth: '#f2f3f8', clothDark: '#b9bdd6', buttons: '#8a96c0', pocket: true, headW: 268, height: 1.72 },
  bak1: { mustache: '#2f5a24', hat: 'kulah', hatColor: '#e8b23e', cloth: '#6fbf4a', pocket: true, headW: 272, headH: 250, height: 1.5 },
  bak2: { beard: '#3f7a2e', beardLen: .6, hat: 'kulah', hatColor: '#e8b23e', cloth: '#58a83e', buttons: '#f1e2bd', headW: 262, height: 1.44 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hero: { pos: [HERO.x + .22, 1.5, HERO.z + 1.95], look: [HERO.x + .02, 1.46, HERO.z], fov: 44 },
  ground: { pos: [SPOT.x + .06, .3, SPOT.z + 1.1], look: [SPOT.x, .04, SPOT.z], fov: 40 },
  wide: { pos: [.14, 1.55, 3.4], look: [.14, 1.5, -1], fov: 50 },
  komsu: { pos: [KOMSU.x - .25, 1.58, KOMSU.z + 2.3], look: [KOMSU.x + .04, 1.6, KOMSU.z], fov: 44 },
  two: { pos: [.15, 1.52, 2.55], look: [.15, 1.47, -.8], fov: 46 },
  hoca: { pos: [-2.3, 1.44, 1.75], look: [-2.48, 1.32, -.9], fov: 46 },
  soil: { pos: [200.0, 1.3, 3.2], look: [200.0, 1.15, -1.2], fov: 48 },
  flask: { pos: [200.08, 1.12, 1.75], look: [200.02, .94, -1.25], fov: 42 },
  drop: { pos: [204.2, .55, 3.2], look: [204.2, .38, -1.5], fov: 46 },
  dropUp: { pos: [204.25, .62, 3.0], look: [204.2, .62, -1.5], fov: 46 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: the hero breathing the smell in -> a drop bursting on the soil -> the garden
    { t: 0, ...SHOT.hero, creep: .34, drift: .04 },
    { t: t('toprak') + .1, dur: .22, move: 'whip', ...SHOT.ground, creep: .3, drift: .015 },
    { t: t('Bakın,') + .16, dur: .3, move: 'whip', ...SHOT.wide, creep: .26, drift: .05 },
    { t: t('derin') + .3, dur: .7, pos: [HERO.x + .25, 1.5, HERO.z + 2.15], look: [HERO.x + .04, 1.46, HERO.z], fov: 44, creep: .3 },
    // the neighbour laughs
    { t: t('Yanındaki') + .3, dur: .3, move: 'whip', ...SHOT.komsu, creep: .3, drift: .04 },
    // "Aslında haklı": both of them, then down to the soil
    { t: t('Aslında') + .24, dur: .3, move: 'whip', ...SHOT.two, creep: .26, drift: .03 },
    { t: t('topraktan') + .16, dur: .26, move: 'whip', ...SHOT.ground, creep: .3, drift: .015 },
    // the bacteria and their flask
    { t: t('Toprakta') + .28, dur: .3, move: 'whip', ...SHOT.soil, creep: .25, drift: .04 },
    { t: t('geosmin') + .35, dur: .6, ...SHOT.flask, creep: .28, drift: .02 },
    // the researcher and the fast camera
    { t: t('Araştırmacılar') + .26, dur: .3, move: 'whip', ...SHOT.hoca, creep: .3, drift: .03 },
    // the drop
    { t: t('damla') + .2, dur: .3, move: 'whip', ...SHOT.drop, creep: .22, drift: .015 },
    { t: t('damlacıklar') + .5, dur: 1.0, ...SHOT.dropUp, creep: .2, drift: .01 },
    // the soda
    { t: t('Tıpkı') + .25, dur: .3, move: 'whip', pos: [KOMSU.x + .3, 1.56, KOMSU.z + 2.15], look: [KOMSU.x - .06, 1.52, KOMSU.z], fov: 44, creep: .3, drift: .03 },
    // the nose
    { t: t('Burnumuz') + .25, dur: .3, move: 'whip', pos: [HERO.x + .14, 1.5, HERO.z + 1.8], look: [HERO.x + .03, 1.47, HERO.z], fov: 42, creep: .32, drift: .02 },
    // "Yani": both of them, then the bacteria take a bow
    { t: t('Yani') + .25, dur: .3, move: 'whip', ...SHOT.two, creep: .2, drift: .02 },
    { t: t('topraktaki') + .22, dur: .3, move: 'whip', ...SHOT.soil, creep: .2, drift: .03 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('neden') + .02, .6); cp.kick(t('çarpınca,') + .1, .9); cp.kick(t('patlıyor') + .05, .5); cp.kick(t('çekti:') + .05, .35);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .8) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#7f98d0');
  buildBahce(scene); buildToprak(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.arm = new Arm3D(scene, cast.hoca);
  dyn.dropA = dynCard(scene, .44, .55, drawDrop);                 // the small drop of the hook, on the garden soil
  dyn.dropB = dynCard(scene, 2.4, 3.0, drawDrop, { pw: 640 });    // the big one, in the soil world
  dyn.umb = card(scene, 1.25, 1.5, drawUmbrella);
  dyn.glass = dynCard(scene, .3, .46, drawGlass, { pw: 256 });
  dyn.flask = card(scene, 1.0, 1.25, drawFlask);
  const board = (text, bg, fg) => (c, w, h) => {
    c.lineJoin = 'round'; c.fillStyle = bg; c.strokeStyle = PLUM; c.lineWidth = 16; c.beginPath(); c.roundRect(12, 12, w - 24, h - 24, 26); c.fill(); c.stroke();
    c.fillStyle = fg; c.font = `900 ${h * .5}px "Arial Black", "Inter", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(text, w / 2, h * .54);
  };
  dyn.bakTag = card(scene, .86, .27, board('BAKTERİ', '#fbf7ee', '#2f6a2a'));
  // "not the rain": a drop crossed out
  dyn.noRain = card(scene, .46, .46, (c, w) => {
    c.lineCap = c.lineJoin = 'round'; c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 20; c.beginPath(); c.arc(w / 2, w / 2, w * .43, 0, 6.29); c.fill(); c.stroke();
    c.fillStyle = '#8fc8ff'; c.lineWidth = 14; c.beginPath(); c.moveTo(w * .5, w * .2); c.quadraticCurveTo(w * .76, w * .52, w * .66, w * .66); c.arc(w * .5, w * .6, w * .17, .35, Math.PI - .35); c.quadraticCurveTo(w * .24, w * .52, w * .5, w * .2); c.closePath(); c.fill(); c.stroke();
    c.strokeStyle = '#e2463f'; c.lineWidth = 40; c.beginPath(); c.moveTo(w * .24, w * .24); c.lineTo(w * .76, w * .76); c.moveTo(w * .76, w * .24); c.lineTo(w * .24, w * .76); c.stroke();
  });
  // one tiny droplet of the smell, on its way to the nose
  dyn.mote = card(scene, .09, .09, (c, w) => { c.fillStyle = '#d6f59a'; c.strokeStyle = '#4c7a2a'; c.lineWidth = 26; c.beginPath(); c.arc(w / 2, w / 2, w * .34, 0, 6.29); c.fill(); c.stroke(); }, { pw: 128 });
  dyn.spark = card(scene, .3, .3, (c, w) => { c.strokeStyle = '#fff3a8'; c.lineCap = 'round'; c.lineWidth = 16; for (let k = 0; k < 8; k++) { const a = k / 8 * 6.283; c.beginPath(); c.moveTo(w / 2 + Math.cos(a) * w * .2, w / 2 + Math.sin(a) * w * .2); c.lineTo(w / 2 + Math.cos(a) * w * .44, w / 2 + Math.sin(a) * w * .44); c.stroke(); } }, { pw: 256, hdr: HDR(1.3, 1.25, 1.0) });
  // the smell: pale green wisps
  const nose = V(HERO.x + .05, 1.42, HERO.z + .2), nose2 = V(KOMSU.x - .05, 1.5, KOMSU.z + .2);
  smokes.scent = new Smoke(scene, { color: '#c4ec8c', maxPoints: 900, H: ctx.H, near: .35 });
  const wisp = (from, to, seed, on) => smokes.scent.wisps.push({ n: 70, size: .1, alpha: .55, speed: .3, seed, on,
    path: (u, t) => [lerpN(from.x, to.x, u) + Math.sin(u * 8 + t * 2.2 + seed) * .07 * Math.sin(Math.PI * u), lerpN(from.y, to.y, u), lerpN(from.z, to.z, u) + Math.cos(u * 6 + t * 1.6 + seed) * .04] });
  const heroSniff = t => dyn.where === 'bahce' && (t < W('Bakın,') || (t > W('derin') - .2 && t < W('Yanındaki') + .3) || t > W('Yani'));
  wisp(V(SPOT.x - .1, .05, SPOT.z - .2), nose, 1, heroSniff); wisp(V(HERO.x - .3, .05, HERO.z + .6), nose, 4, heroSniff);
  wisp(V(SPOT.x + .1, .05, SPOT.z - .3), nose2, 7, t => dyn.where === 'bahce' && t > W('Yani'));
  // rising from the soil (the two ground shots)
  for (const s of [2, 5, 9]) smokes.scent.wisps.push({ n: 50, size: .085, alpha: .55, speed: .34, seed: s, on: t => dyn.where === 'bahce' && ((t > W('toprak') && t < W('Bakın,') + .3) || (t > W('topraktan') && t < W('Toprakta') + .4)),
    path: (u, t) => [SPOT.x + (s - 5) * .05 + Math.sin(u * 7 + t * 2 + s) * .06 * u, .03 + u * .75, SPOT.z - .12 + Math.cos(u * 5 + s) * .05] });
  // puffs from the flask
  for (const s of [1, 2, 3]) smokes.scent.wisps.push({ n: 60, size: .22, alpha: .5, speed: .26, seed: s * 3, on: t => dyn.where === 'toprak' && t > W('geosmin') - .1,
    path: (u, t) => [NOZZLE.x - .28 - u * (.5 + s * .22) + Math.sin(u * 6 + t * 1.5 + s) * .1 * u, NOZZLE.y + .18 + u * (.9 + s * .3), NOZZLE.z + .1 + Math.cos(u * 4 + s) * .12 * u] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .02, 'whoosh'); cue(W('Toprakta') + .12, 'whoosh'); cue(W('damla') + .05, 'whoosh');
  cue(0, 'simmer', { dur: W('Toprakta') }); cue(W('neden') + .02, 'cut'); cue(W('derin') + .1, 'wind', { dur: 1.3 });
  cue(W('Yanındaki') + .1, 'rise', { dur: .35 }); cue(W('Aslında') + .05, 'rise', { dur: .35 }); cue(W('topraktan') + .02, 'shimmer');
  cue(W('geosmin') + .02, 'shimmer'); cue(W('Araştırmacılar') + .08, 'rise', { dur: .35 }); cue(W('çekti:') + .02, 'lock');
  cue(W('çarpınca,') + .1, 'boom'); cue(W('kabarcıkları'), 'simmer', { dur: W('Tıpkı') - W('kabarcıkları') }); cue(W('patlıyor') + .05, 'shimmer');
  cue(W('Tıpkı') + .05, 'rise', { dur: .35 }); cue(W('gazozdaki') + .1, 'simmer', { dur: W('Burnumuz') - W('gazozdaki') - .1 }); cue(W('Burnumuz') + .05, 'rise', { dur: .35 });
  cue(W('hemen') + .1, 'shimmer'); cue(W('Yani') + .05, 'rise', { dur: .35 }); cue(W('Yani') + .3, 'simmer', { dur: W('topraktaki') - W('Yani') }); cue(W('topraktaki') + .1, 'rise', { dur: .35 }); cue(W('bakterilerin') + .2, 'shimmer');
}

export function overlay(g, t, ctx) {
  kancaYazisi(g, t, ctx.W, ctx.H, 'TOPRAK NEDEN KOKAR?');
  // the fast camera's viewfinder over the drop shots
  const a = W('damla') + .3, b = W('Tıpkı') + .1;
  if (t > a && t < b) {
    const w = ctx.W, h = ctx.H, u = w / 1080, x0 = w * .07, x1 = w * .93, y0 = h * .1, y1 = h * .655, L = 70 * u;
    g.save(); g.lineCap = 'round'; g.lineJoin = 'round'; g.globalAlpha = Math.min(1, (t - a) / .15, (b - t) / .15);
    for (const pass of [0, 1]) {
      g.strokeStyle = pass ? '#ffffff' : '#140c1c'; g.lineWidth = (pass ? 9 : 19) * u;
      for (const [x, y, sx, sy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x0, y1, 1, -1], [x1, y1, -1, -1]]) { g.beginPath(); g.moveTo(x + sx * L, y); g.lineTo(x, y); g.lineTo(x, y + sy * L); g.stroke(); }
    }
    g.font = `900 ${46 * u}px "Segoe UI Black", "Arial Black", "Inter", sans-serif`; g.textBaseline = 'middle'; g.textAlign = 'left';
    const ty = y0 + 62 * u;
    g.strokeStyle = '#140c1c'; g.lineWidth = 12 * u; g.strokeText('AĞIR ÇEKİM', x0 + 96 * u, ty); g.fillStyle = '#ffffff'; g.fillText('AĞIR ÇEKİM', x0 + 96 * u, ty);
    if (Math.floor(t * 2.5) % 2 === 0) { g.fillStyle = '#ff4338'; g.strokeStyle = '#140c1c'; g.lineWidth = 7 * u; g.beginPath(); g.arc(x0 + 54 * u, ty, 17 * u, 0, 6.29); g.fill(); g.stroke(); }
    g.restore();
  }
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const DAYB = '#dfdcf4', WARM = '#ffe2a0';
const M4 = new THREE.Matrix4(), Q4 = new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), V(.08, -1, .03).normalize()), ONE = V(1, 1, 1);
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos);
  if (wob) m.rotation.z = Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04;
  return s;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 100 ? 'toprak' : 'bahce';
  vis('bahce', where === 'bahce'); vis('toprak', where === 'toprak'); dyn.where = where;
  dyn.sunGlow.visible = dyn.rain.visible = where === 'bahce';
  for (const c of Object.values(cast)) c.hide();
  dyn.arm.hide();
  for (const m of [dyn.dropA, dyn.dropB, dyn.umb, dyn.glass, dyn.flask, dyn.bakTag, dyn.noRain, dyn.mote, dyn.spark]) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const RT = V(1, 0, 0).applyQuaternion(cam.quaternion), UP = V(0, 1, 0).applyQuaternion(cam.quaternion);
  let look, grade = [1, 1, 1], face = [1, .99, .975];
  if (where === 'bahce') {
    grade = [1.0, 1.0, 1.03];
    const tint = face.map((v, i) => v / grade[i]);
    // ---- rain
    for (let i = 0; i < 300; i++) {
      const fallen = (t * 6.5 + hash(i, 3) * 4.6) % 4.6;
      M4.compose(V(-3.6 + hash(i, 1) * 7.2 + fallen * .08, 4.4 - fallen, -2.6 + hash(i, 2) * 5.2), Q4, ONE); dyn.rain.setMatrixAt(i, M4);
    }
    dyn.rain.instanceMatrix.needsUpdate = true;
    const H = cast.kahraman, K = cast.komsu, R = cast.hoca;
    const inHook = t < A('Bakın,'), inL2 = !inHook && t < A('Yanındaki'), inL3 = t > A('Yanındaki') && t < A('Aslında'), inL4 = t > A('Aslında') && t < A('Toprakta');
    const inL6 = t > A('Araştırmacılar') && t < W('damla') + .3, inL8 = t > A('Tıpkı') && t < A('Burnumuz'), inL9 = t > A('Burnumuz') && t < A('Yani'), inL10 = t > A('Yani');
    // ---- the hero: breathing the smell in
    const breath = inHook ? .5 + .5 * Math.sin(t * 5) : ramp(t, A('derin'), A('nefes') + .25);
    const sniff = { expr: 'smile', blink: 1, look: .12, lookY: -.42, brow: .5, bob: -9 * breath, lean: -2.5 * breath, armL: [18, 8], armR: [18, 8] };
    let hp = { expr: 'neutral', look: .1, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(1, A('damlalar'), A('derin'), A('"Yağmurun'), A('haklı,'), A('koku'), A('hemen'), A('yakalıyor.')) };
    if (inHook) hp = sniff;
    if (inL2) hp = t < A('damlalar') ? { ...hp, look: .05, lookY: -.3 } : t < A('derin') ? { ...hp, expr: 'surprised', lookY: -.75, gazeY: -1, brow: .8, mouth: .4, armR: [104, -24] } : sniff;
    if (inL3) hp = t < A('"Yağmurun') ? { ...hp, look: .85, expr: 'neutral', brow: .5 } : { ...hp, look: .85, expr: 'worried', sweat: 1, armR: [150, 30] };
    if (inL4) hp = t < A('koku') ? { ...hp, look: .85, expr: 'surprised', brow: .9, mouth: .35 } : { ...hp, look: .45, lookY: .8, gazeY: 1, expr: 'neutral', brow: .6, armR: [70, 26] };
    if (inL9) hp = t < A('hemen') ? { ...hp, expr: 'neutral', look: .3, lookY: .2, gazeX: .6, gazeY: .5, brow: .3 } : t < A('yakalıyor.') ? { ...hp, expr: 'surprised', look: .15, brow: 1, mouth: .5 } : { ...sniff, bob: -6 };
    if (inL10) hp = { ...sniff, bob: -8 * (.5 + .5 * Math.sin((t - A('Yani')) * 4)), lean: -2 };
    H.show(); H.place(HERO.x, 0, HERO.z, cam, tint);
    H.draw({ ...hp, lit: -1, shade: DAYB, rim: { color: WARM, a: .3 } }); H.castFrom(SUNDIR, true);
    // ---- the neighbour: fat mustache, blue cap, umbrella
    const laugh = t > A('komşu') - .1 && t < A('"Yağmurun') - .04, talk = t > A('"Yağmurun') - .04 && t < A('olur?"') + .42;
    let kp = { expr: 'smug', look: -.6, armL: [16, 10], armR: [38, -122], blink: bl(2, A('komşu') - .1, A('"Yağmurun'), A('haklı,'), A('topraktan'), A('patlayıp'), A('gıdıklaması'), A('Yani')) };
    if (laugh) kp = { ...kp, expr: 'laugh', laughMarks: .9, mouth: .5 + .5 * Math.abs(Math.sin(t * 13)), bob: -Math.abs(Math.sin(t * 13)) * 10, armL: [28, -100] };
    if (talk) kp = { ...kp, expr: 'smug', brow: .6, mouth: flap(env, t), armL: [100, 14] };
    if (inL4) kp = t < A('koku') ? { ...kp, expr: 'proud', look: -.3, lid: .15, armL: [30, -98] } : t < A('topraktan') ? { ...kp, expr: 'surprised', look: -.5, brow: .9, mouth: .3 } : { ...kp, expr: 'surprised', look: -.4, lookY: .8, gazeY: 1, brow: 1, mouth: .45 };
    if (inL8) {
      const tick = t > A('patlayıp'), giggle = t > A('gıdıklaması');
      kp = { ...kp, look: -.25, lookY: .25, armL: [52, -128], expr: giggle ? 'laugh' : tick ? 'surprised' : 'smile', brow: tick ? 1 : .3, mouth: giggle ? .4 + .4 * Math.abs(Math.sin(t * 15)) : tick ? .3 : 0, laughMarks: giggle ? .8 : 0, bob: giggle ? -Math.abs(Math.sin(t * 15)) * 7 : 0, lean: tick && !giggle ? -3 : 0 };
    }
    if (inL10) kp = { ...kp, expr: 'smile', blink: t > A('kokladığın') ? 1 : kp.blink, look: -.35, lookY: -.35, brow: .5, bob: -7 * (.5 + .5 * Math.sin((t - A('Yani')) * 4 + 1.4)), armL: [18, 8] };
    K.show(); K.place(KOMSU.x, 0, KOMSU.z, cam, tint);
    K.draw({ ...kp, lit: -1, shade: DAYB, rim: { color: WARM, a: .3 } }); K.castFrom(SUNDIR, true);
    const hr = K.hand(1);
    if (hr) { dyn.umb.visible = true; dyn.umb.position.copy(hr).addScaledVector(UP, .69).addScaledVector(RT, .02); dyn.umb.position.z -= .02; dyn.umb.rotation.z = .05 + (kp.bob || 0) * -.004; }
    if (inL8) { const hl = K.hand(-1); if (hl) { dyn.glass.userData.set(t - A('Tıpkı')); dyn.glass.visible = true; dyn.glass.position.copy(hl).addScaledVector(UP, .22).addScaledVector(RT, -.01); dyn.glass.position.z += .03; dyn.glass.scale.setScalar(1.35 * backOut((t - A('Tıpkı')) / .2)); } }
    // ---- the researcher behind the fast camera
    R.show(); R.place(HOCA.x, 0, HOCA.z, cam, tint, 1, .12);
    const shot = t > A('çekti:');
    R.draw({ expr: shot ? 'grin' : 'focused', look: .7, lookY: .5, gazeY: .8, brow: shot ? .8 : -.2, armL: shot ? [150, 24] : [20, 10], noArmR: true, lean: 3, blink: bl(3, A('çekti:')), lit: -1, shade: DAYB, rim: { color: WARM, a: .3 } }); R.castFrom(SUNDIR, true);
    if (inL6) dyn.arm.set(1, dyn.camGrip, { tint });
    dyn.recMat.color.copy(inL6 && Math.floor(t * 5) % 2 ? HDR(3.2, .5, .4) : new THREE.Color('#7a2a2a'));
    // ---- the drop on the garden soil (the hook), and the smell rising from the same spot later
    if (t < W('Bakın,') + .3) {
      const hit = W('neden') + .02, fl = clamp01((t - (hit - .3)) / .3), a = Math.max(0, t - hit);
      dyn.dropA.userData.set(fl, a, a > .08 ? 1 : 0, a - .18); dyn.dropA.visible = t > hit - .3; dyn.dropA.position.set(SPOT.x, .22, SPOT.z);
    } else if (t > A('topraktan') - .3 && t < W('Toprakta') + .4) {
      dyn.dropA.userData.set(1, 3, 1, t - A('topraktan') + 1.2); dyn.dropA.visible = true; dyn.dropA.position.set(SPOT.x, .22, SPOT.z);
    }
    // ---- "not the rain"
    if (inL4 && t > A('yağmurdan', 2) && t < W('topraktan') + .16) popCard(dyn.noRain, A('yağmurdan', 2), t, V(.15, 2.05, -.8));
    // ---- one tiny droplet is enough for the nose
    if (inL9) {
      const k = clamp01((t - A('Burnumuz') - .25) / (A('hemen') - A('Burnumuz') - .25)), tgt = V(HERO.x + .05, 1.43, HERO.z + .14), from = tgt.clone().addScaledVector(RT, .52).addScaledVector(UP, -.34);
      if (k < 1) { dyn.mote.visible = true; dyn.mote.position.copy(from).lerp(tgt, k * k * (3 - 2 * k)).addScaledVector(UP, Math.sin(k * 9) * .03); }
      else { const s = (t - A('hemen')) / .45; if (s < 1) { dyn.spark.visible = true; dyn.spark.position.copy(tgt); dyn.spark.scale.setScalar(.5 + s * 1.2); dyn.spark.material.opacity = 1 - s; dyn.spark.rotation.z = s; } }
    }
    const ground = (t > W('toprak') + .1 && t < W('Bakın,') + .1) || (t > W('topraktan') + .12 && t < W('Toprakta') + .2);
    const f = ground ? SPOT.clone().setY(.1) : inL3 || inL8 ? V(KOMSU.x, 1.5, KOMSU.z) : inL6 ? V(TRIPOD.x - .2, 1.2, TRIPOD.z - .2) : V(HERO.x, 1.5, HERO.z);
    look = { focus: cam.position.distanceTo(f), coc: ground ? 7 : 5, range: ground ? .7 : 2.2, sat: 1.28, lift: [.09, .09, .16], bloom: .85, vignette: .2 };
  } else {
    // ---- the soil: the bacteria and their flask; the drop, the bubbles, the droplets
    grade = [1.02, 1.0, .99];
    const tint = face.map((v, i) => v / grade[i]);
    const end = t > A('topraktaki');
    dyn.flask.visible = true; dyn.flask.position.set(ROCK.x, ROCK.y + .625, ROCK.z + .02);
    const pump = Math.sin(t * 9);
    [['bak1', 0, 5], ['bak2', 1, 6]].forEach(([name, i, seed]) => {
      const B = cast[name], p = BAK[i];
      let d = i === 0
        ? { expr: 'focused', look: .7, lookY: -.1, armR: [112 + pump * 7, -18 - pump * 14], armL: [18, 10], lean: 2 + pump * 1.2, blink: bl(seed, A('bakteriler,'), A('geosmin'), A('topraktaki')) }
        : { expr: 'proud', look: -.5, lid: .15, armL: [128, 34], armR: [24, -96], blink: bl(seed, A('bakteriler,'), A('kokulu'), A('topraktaki')) };
      if (t > A('bakteriler,') && t < A('geosmin')) d = { ...d, expr: i ? 'grin' : 'smile', look: i ? -.2 : .3 };
      if (i === 1 && t > A('kokulu') && !end) d = { ...d, expr: 'smile', blink: 1, lookY: -.4, look: -.55, bob: -6 * (.5 + .5 * Math.sin(t * 5)), armL: [18, 8], armR: [18, 8] };
      if (end) d = { ...d, expr: i ? 'grin' : 'proud', look: i ? -.25 : .25, lookY: 0, mouth: 0, armL: i ? [156, 26 + 14 * Math.sin(t * 10)] : [18, 10], armR: i ? [24, -96] : [112 + pump * 7, -18 - pump * 14], bob: i ? -Math.abs(Math.sin(t * 6)) * 6 : 0 };
      B.show(); B.place(200 + p.x, 0, p.z, cam, tint);
      B.draw({ ...d, lit: -1, shade: DAYB, rim: { color: WARM, a: .28 } }); B.castFrom(dyn.bSun, true);
    });
    if (t > A('bakteriler,') && t < W('geosmin') + .3) popCard(dyn.bakTag, A('bakteriler,'), t, V(200 + BAK[0].x + .38, 2.02, BAK[0].z));
    // the big drop
    if (cam.position.x > 202) {
      const hit = W('çarpınca,') + .1, fl = clamp01((t - (hit - .42)) / .42), a = Math.max(0, t - hit);
      dyn.dropB.userData.set(fl, a, clamp01((t - A('kabarcıkları')) / .5), Math.max(0, t - A('yükselip')));
      dyn.dropB.visible = t > hit - .42; dyn.dropB.position.copy(DROP);
    }
    const f = cam.position.x > 202 ? DROP.clone().setY(.5) : V(200, 1.1, -1.2);
    look = { focus: cam.position.distanceTo(f), coc: 4, range: 3.4, sat: 1.2, lift: [.1, .095, .15], bloom: .8, vignette: .18 };
  }
  for (const s of Object.values(smokes)) s.update(t);
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
