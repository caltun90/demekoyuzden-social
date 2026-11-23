// Dilsizler: Lala Anlatıyor deneme Short'u (yumurta stili).
// Hikâye: Osmanlı sarayının iç kısmında (Enderun) padişahın yanında konuşmak ayıptı; emirler dilsizlerin işaret diliyle
// iletildi, dil saraya yayıldı, büyük ihtimalle ilk öğrenen padişah Genç Osman'dı (II. Osman). Kaynaklar SCRIPT.md'de.
// Setler: SARAY (x≈0) taht odası, gün batımı kafesli pencereden (sıcak anahtar) + mavi gölge dolgusu + iki kandil;
//         SOFRA (x≈200) mutfak, açık pencereden sabah güneşi.
import * as THREE from 'three';
import { stoneTex, woodTex, carpetTex, wallTex, ciniTex, frizTex, roundelTex, painted, flat, rng } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';
import { holedWall, vistaMat, dayGardenTex } from '/engine/src/vista.js';
import { kandil, voussoirArch } from '/engine/src/props.js';

export const NAME = 'dilsizler';
export const FPS = 30;
export let DUR = 28.5;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lerpN = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const DEG = Math.PI / 180;
const KIT_CAM = [200.3, 1.7, 1.5];
let W, cast = {}, sets = {}, dyn = {}, smokes = {};

function wordTimes(words) {
  const norm = s => s.toLocaleLowerCase('tr-TR').replace(/[^\p{L}\p{N}]/gu, '');
  return (w, n = 1) => { let k = 0; for (const x of words) if (norm(x.word) === norm(w) && ++k === n) return x.start; throw new Error('word not found: ' + w); };
}
function shadows(g) {
  g.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;
    if (o.material.isMeshLambertMaterial) o.receiveShadow = true;
    if (/Box|Cylinder|Extrude|Lathe|Torus/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function gobo(draw, s = 512) {
  const c = document.createElement('canvas'); c.width = c.height = s; const g = c.getContext('2d');
  g.fillStyle = '#000'; g.fillRect(0, 0, s, s); draw(g, s);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function keySpot(color, intensity, pos, target, angle, { map, size = 2048, near = 1, far = 60, penumbra = .35 } = {}) {
  const l = new THREE.SpotLight(color, intensity, 0, angle, penumbra, 0);
  l.position.set(...pos); l.target.position.set(...target); l.castShadow = true;
  l.shadow.mapSize.set(size, size); l.shadow.camera.near = near; l.shadow.camera.far = far; l.shadow.bias = -.0006; l.shadow.normalBias = .03; l.shadow.radius = 3;
  if (map) l.map = map;
  return l;
}

// ---------------------------------------------------------------- SARAY: taht odası (x = 0)
// Oda 14 x 12 m, tavan 5.6 m. Taht (sedir) arka duvarın ortasında, çizgili kemerin altında. Sağ duvarda büyük kafesli
// pencere: dışarıda bahçe, içeri alçak akşam güneşi giriyor (kafes deseni yere ve dilsizlere düşüyor).
const WIN = { x: 6.5, z0: -2.6, z1: .6, y0: 1.0, y1: 3.4 };
const WIN_CAM = [2.6, 1.5, 1.6];
function buildSaray(scene) {
  const g = new THREE.Group(); scene.add(g);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(14, 12), painted(carpetTex({ base: '#a82c3a', band: '#d9a441', rep: [3, 3] })));
  floor.rotation.x = -Math.PI / 2; floor.position.z = 0; g.add(floor);
  // walls: pale blue-grey stone (the cool half of the frame); the sun patch turns them warm
  const wallM = (rx, ry) => painted(stoneTex({ base: '#c9d6e6', rep: [rx, ry] }));
  const back = new THREE.Mesh(new THREE.PlaneGeometry(14, 5.6), wallM(4, 2)); back.position.set(0, 2.8, -6); g.add(back);
  const left = new THREE.Mesh(new THREE.PlaneGeometry(12, 5.6), wallM(4, 2)); left.position.set(-7, 2.8, 0); left.rotation.y = Math.PI / 2; g.add(left);
  const front = new THREE.Mesh(new THREE.PlaneGeometry(14, 5.6), wallM(4, 2)); front.position.set(0, 2.8, 6); front.rotation.y = Math.PI; g.add(front);
  // right wall with the window: one piece with a hole, so the sun only enters through the opening
  const rw = holedWall(12, 5.6, [WIN.z0, WIN.y0, WIN.z1, WIN.y1], painted(stoneTex({ base: '#c9d6e6', rep: [1 / 3, 1 / 2.8] })));
  rw.position.set(WIN.x + .1, 0, 0); rw.rotation.y = -Math.PI / 2; rw.castShadow = true; g.add(rw);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(14, 12), painted(woodTex({ base: '#7a4a3a', plank: 96, rep: [3, 3] }))); ceil.rotation.x = Math.PI / 2; ceil.position.y = 5.6; g.add(ceil);
  for (const z of [-4.5, -1.5, 1.5, 4.5]) { const bm = new THREE.Mesh(new THREE.BoxGeometry(14, .2, .24), painted(woodTex({ base: '#5e3a30' }))); bm.position.set(0, 5.48, z); g.add(bm); }
  // pattern on every big wall: tile dado (proud of the wall), a gold strip, a painted frieze band up high
  const cini = ciniTex({ kind: 'lale' }), friz = frizTex(), yildiz = ciniTex({ kind: 'yildiz' });
  const tiled = (t, rx, ry) => { const c = t.clone(); c.repeat.set(rx, ry); c.needsUpdate = true; return painted(c); };
  const goldM = flat('#d9a441');
  const panel = (t, w, h, x, y, z, ry, mod) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), tiled(t, w / mod[0], h / mod[1])); m.position.set(x, y, z); m.rotation.y = ry; m.translateZ(.05); g.add(m); return m; };
  const strip = (w, h, d, x, y, z, ry = 0, mat = goldM) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); b.position.set(x, y, z); b.rotation.y = ry; g.add(b); return b; };
  for (const [w, x, z, ry] of [[14, 0, -6, 0], [12, -7, 0, Math.PI / 2], [14, 0, 6, Math.PI]]) {
    panel(cini, w, 1.1, x, .55, z, ry, [.46, .46]); strip(w, .08, .16, x, 1.14, z, ry);
    panel(friz, w, .9, x, 4.3, z, ry, [4, .9]); strip(w, .07, .18, x, 4.78, z, ry); strip(w, .07, .18, x, 3.82, z, ry);
  }
  // right wall: dado only below the window and around it
  for (const [z0, z1] of [[-6, WIN.z0 - .2], [WIN.z1 + .2, 6]]) { const w = z1 - z0, zc = (z0 + z1) / 2; panel(cini, w, 1.1, WIN.x, .55, zc, -Math.PI / 2, [.46, .46]); strip(w, .08, .16, WIN.x - .02, 1.14, zc, -Math.PI / 2); }
  panel(friz, 12, .9, WIN.x, 4.3, 0, -Math.PI / 2, [4, .9]);
  // window: casing proud of the wall, lattice bars, the garden outside
  const jamb = painted(woodTex({ base: '#8a5a3a', plank: 128 })), wc = (WIN.z0 + WIN.z1) / 2, wy = (WIN.y0 + WIN.y1) / 2;
  const box = (sx, sy, sz, x, y, z, m = jamb) => { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), m); b.position.set(x, y, z); g.add(b); return b; };
  box(.5, .14, WIN.z1 - WIN.z0 + .2, WIN.x + .1, WIN.y1 + .02, wc); box(.5, .14, WIN.z1 - WIN.z0 + .2, WIN.x + .1, WIN.y0 - .02, wc);
  for (const z of [WIN.z0 - .03, WIN.z1 + .03]) box(.5, WIN.y1 - WIN.y0, .14, WIN.x + .1, wy, z);
  const barM = flat('#4a3424');
  for (let k = 1; k < 6; k++) { const b = box(.06, WIN.y1 - WIN.y0, .06, WIN.x + .05, wy, WIN.z0 + k * (WIN.z1 - WIN.z0) / 6, barM); b.userData.noShadow = false; }
  for (let k = 1; k < 5; k++) box(.06, .06, WIN.z1 - WIN.z0, WIN.x + .05, WIN.y0 + k * (WIN.y1 - WIN.y0) / 5, wc, barM);
  const out = new THREE.Mesh(new THREE.PlaneGeometry(WIN.z1 - WIN.z0 + .3, WIN.y1 - WIN.y0 + .3),
    vistaMat(dayGardenTex(), { yaw: Math.atan2(WIN.x + .4 - WIN_CAM[0], wc - WIN_CAM[2]), az: Math.PI / 2, el: [-20 * DEG, 25 * DEG], gain: 1.15 }));
  out.position.set(WIN.x + .4, wy, wc); out.rotation.y = -Math.PI / 2; g.add(out);
  // the throne: a raised sedir under a striped arch, cushions, a round bolster, a tile panel behind
  const sedirM = painted(woodTex({ base: '#8f5a34' })), cushM = flat('#b8323a'), goldC = flat('#e0aa3e');
  box(4.2, .45, 1.9, 0, .225, -4.95, sedirM);
  box(4.0, .12, 1.7, 0, .51, -4.95, painted(carpetTex({ base: '#2f5ea8', band: '#e0b050', rep: [1, 1], rows: 1 })));
  for (const x of [-1.3, 0, 1.3]) { const c = box(1.15, .8, .26, x, .97, -5.72, cushM); c.rotation.x = -.12; }
  for (const x of [-1.9, 1.9]) { const b = new THREE.Mesh(new THREE.CylinderGeometry(.18, .18, 1.2, 20), goldC); b.rotation.x = Math.PI / 2; b.position.set(x, .76, -5.1); g.add(b); }
  panel(yildiz, 4.6, 2.6, 0, 2.35, -6, 0, [.6, .6]); strip(4.76, .08, .14, 0, 3.69, -6); for (const s of [-1, 1]) strip(.08, 2.7, .14, s * 2.34, 2.35, -6);
  const arch = voussoirArch({ span: 5.2, rise: 1.4, thick: .45, depth: .5, n: 15, bevel: .03 }); arch.position.set(0, 3.75, -5.75); g.add(arch);
  for (const s of [-1, 1]) { const col = new THREE.Mesh(new THREE.CylinderGeometry(.16, .2, 3.75, 16), painted(stoneTex({ base: '#e9d9b8', rep: [1, 2] }))); col.position.set(s * 2.6, 1.875, -5.6); g.add(col); }
  // two round medallions on the back wall
  const rdM = new THREE.MeshBasicMaterial({ map: roundelTex() });
  for (const s of [-1, 1]) { const rd = new THREE.Mesh(new THREE.CircleGeometry(.62, 48), rdM); rd.position.set(s * 4.8, 2.6, -5.93); g.add(rd); }
  // a low brass brazier (mangal) near the left wall: a warm point in the cool side
  const mg = new THREE.Mesh(new THREE.CylinderGeometry(.34, .24, .32, 24), flat('#c9963e')); mg.position.set(-4.6, .16, -3.4); g.add(mg);
  const coal = new THREE.Mesh(new THREE.CircleGeometry(.3, 24), new THREE.MeshBasicMaterial({ color: HDR(2.4, 1.0, .35) })); coal.rotation.x = -Math.PI / 2; coal.position.set(-4.6, .33, -3.4); g.add(coal);
  // lights
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#a9b2f2', '#6a5a86', 1.9));                           // cool fill: shade stays blue-violet
  const lattice = gobo((c, s) => {                                                          // the window with its lattice
    c.fillStyle = '#fff'; c.fillRect(s * .1, s * .14, s * .8, s * .72);
    c.fillStyle = '#000'; for (let k = 1; k < 6; k++) c.fillRect(s * (.1 + k * .8 / 6) - s * .012, 0, s * .024, s);
    for (let k = 1; k < 5; k++) c.fillRect(0, s * (.14 + k * .72 / 5) - s * .012, s, s * .024);
  });
  const sunDir = V(-1.0, -.5, -.18).normalize(); dyn.sunDir = sunDir;
  const sunT = V(2.2, 0, -1.2);
  const sun = keySpot('#ffc276', 10.5, sunT.clone().addScaledVector(sunDir, -16).toArray(), sunT.toArray(), .24, { map: lattice, near: 4, far: 40, penumbra: .12 });
  L.add(sun); L.add(sun.target);
  const mgL = new THREE.PointLight('#ff9a4a', 4, 5, 1.6); mgL.position.set(-4.6, .9, -3.4); L.add(mgL);
  scene.add(L); sets.saray = { g, L };
  shadows(g);
  dyn.beam = beam(scene, [WIN.x, wy, wc], V(WIN.x, wy, wc).addScaledVector(sunDir, 5.5).toArray(), { r0: 1.0, r1: 1.6, color: '#ffd89a', strength: .12 });
  // two hanging lamps (warm, glowing) left and right of the throne
  dyn.lamps = [];
  for (const x of [-3.4, 3.4]) {
    const k = kandil({ chain: 1.6, s: 1.6, light: 9, range: 7, decay: 1.3, halo: .5 }); k.position.set(x, 5.4, -3.6); scene.add(k); dyn.lamps.push(k);
    k.traverse(o => { if (o.isMesh) o.castShadow = false; });
  }
}

// ---------------------------------------------------------------- SOFRA (x = 200): mutfak, kopya yapı + yer sofrası
function buildSofra(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(6, 6), painted(woodTex({ base: '#a8743e', rep: [2, 2] }))); fl.rotation.x = -Math.PI / 2; g.add(fl);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(6, 3.2), painted(ciniTex({ kind: 'yildiz', a: '#3f7fd6', b: '#35b3aa', c: '#e0604a', rep: [10, 16 / 3] }))); back.position.set(0, 1.6, -2.6); g.add(back);
  const left = new THREE.Mesh(new THREE.PlaneGeometry(6, 3.2), painted(stoneTex({ base: '#b9cde6', rep: [2, 1] }))); left.position.set(-3, 1.6, 0); left.rotation.y = Math.PI / 2; g.add(left);
  const top = new THREE.Mesh(new THREE.PlaneGeometry(6, 6), painted(woodTex({ base: '#7e5a50', plank: 128, rep: [1, 3] }))); top.rotation.x = Math.PI / 2; top.position.y = 3.2; g.add(top);
  const WZ = [-.9, .5], WY = [1.1, 2.3], wc = (WZ[0] + WZ[1]) / 2, wy = (WY[0] + WY[1]) / 2;
  const rw = holedWall(6, 3.2, [WZ[0], WY[0], WZ[1], WY[1]], painted(stoneTex({ base: '#b9cde6', rep: [1 / 2.1, 1 / 3.2] })));
  rw.position.set(2.6, 0, 0); rw.rotation.y = -Math.PI / 2; rw.castShadow = true; g.add(rw);
  const jamb = painted(woodTex({ base: '#a06a3a', plank: 128 })), X0 = 2.54, X1 = 2.96, xc = (X0 + X1) / 2, xd = X1 - X0;
  const box = (sx, sy, sz, x, y, z, m = jamb) => { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), m); b.position.set(x, y, z); g.add(b); return b; };
  box(xd, .13, WZ[1] - WZ[0] + .16, xc, WY[1] + .015, wc); box(xd, .13, WZ[1] - WZ[0] + .16, xc, WY[0] - .015, wc);
  for (const z of WZ) box(xd, WY[1] - WY[0] - .1, .13, xc, wy, z + Math.sign(z - wc) * .015);
  box(.4, .075, WZ[1] - WZ[0] + .4, 2.49, WY[0] + .03, wc, flat('#d8c8a6'));
  const out = new THREE.Mesh(new THREE.PlaneGeometry(WZ[1] - WZ[0] + .3, WY[1] - WY[0] + .3),
    vistaMat(dayGardenTex(), { yaw: Math.atan2(202.6 - KIT_CAM[0], wc - KIT_CAM[2]), az: Math.PI / 2, el: [-22 * DEG, 23 * DEG], gain: 1.12 }));
  out.position.set(2.92, wy, wc); out.rotation.y = -Math.PI / 2; g.add(out);
  const shelf = new THREE.Mesh(new THREE.BoxGeometry(1.6, .06, .35), painted(woodTex({}))); shelf.position.set(-.9, 2.1, -2.42); g.add(shelf);
  for (let i = 0; i < 4; i++) { const j = new THREE.Mesh(new THREE.CylinderGeometry(.11, .11, .26, 12), flat(['#d9a441', '#b8323a', '#3d86c9', '#6aa85a'][i])); j.position.set(-1.4 + i * .33, 2.26, -2.42); g.add(j); }
  // the floor table (sofra) with a tray of baklava and two glasses of tea
  const tbl = new THREE.Mesh(new THREE.CylinderGeometry(.62, .62, .05, 40), painted(woodTex({ base: '#c08a52' }))); tbl.position.set(0, .3, -.5); g.add(tbl);
  const leg = new THREE.Mesh(new THREE.CylinderGeometry(.34, .4, .28, 24), painted(woodTex({ base: '#8a5a34' }))); leg.position.set(0, .14, -.5); g.add(leg);
  const tray = new THREE.Mesh(new THREE.CylinderGeometry(.26, .26, .025, 32), flat('#d9a441')); tray.position.set(.12, .34, -.48); g.add(tray);
  for (let i = 0; i < 9; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.075, .03, .075), flat(i % 2 ? '#e8b04a' : '#d89a3a')); b.position.set(.12 + ((i % 3) - 1) * .085, .366, -.48 + (Math.floor(i / 3) - 1) * .085); b.rotation.y = .785; g.add(b); }
  for (const x of [-.32, .45]) { const gl2 = new THREE.Mesh(new THREE.CylinderGeometry(.035, .025, .09, 14), flat('#c8402a')); gl2.position.set(x, .37, -.62); g.add(gl2); }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#d4dcff', '#a096b8', 2.4));
  const sunDir = V(-2.15, -.62, -1.05).normalize(); dyn.kSun = sunDir;
  const sun = new THREE.DirectionalLight('#ffd89c', 3.6); sun.position.copy(V(202.6, 1.7, -.2).addScaledVector(sunDir, -6)); sun.target.position.set(202.6, 1.7, -.2);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -3.5, right: 3.5, top: 3.5, bottom: -3.5, near: .5, far: 16 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
  L.add(sun); L.add(sun.target);
  scene.add(L); sets.sofra = { g, L };
  shadows(g);
  dyn.kBeam = beam(scene, [202.75, 1.72, -.2], V(202.75, 1.72, -.2).addScaledVector(sunDir, 3.6).toArray(), { r0: .58, r1: .8, color: '#ffe9b8', strength: .13 });
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  padisah: { hat: 'sarik-big', beard: '#3a2a24', beardLen: .6, mustache: '#2a1c18', body: 'sit', cloth: '#7a2a5a', trim: '#e0aa3e', sash: '#e0aa3e', height: 1.2 },
  osman: { hat: 'sarik-big', mustache: '#4a3024', body: 'sit', cloth: '#2d7466', trim: '#e0aa3e', sash: '#b8323a', height: 1.16, headW: 250, headH: 236 },
  vezir: { hat: 'sarik', beard: '#ece6dc', beardLen: .7, mustache: '#d8d0c6', body: 'robe', cloth: '#2f5ea8', trim: '#e0aa3e', sash: '#b8323a', height: 1.72 },
  dilsiz1: { hat: 'kulah', hatColor: '#b8323a', cloth: '#3a6a9a', pattern: 'stripes', mustache: true, hair: '#3a2a24', height: 1.66 },
  dilsiz2: { hat: 'kulah', hatColor: '#d9a441', cloth: '#2d7466', buttons: '#7a4a2a', height: 1.6, headW: 262, headH: 246 },
  ic1: { hat: 'kulah', hatColor: '#3d5a8a', cloth: '#dba63e', buttons: '#7a4a2a', height: 1.5, headW: 250, headH: 238 },
  ic2: { hat: 'kulah', hatColor: '#6a3a7a', cloth: '#c8643a', pattern: 'stripes', height: 1.55 },
  ic3: { hat: 'kulah', hatColor: '#2d7466', cloth: '#e0aa3e', height: 1.48, headW: 256, headH: 240 },
  baba: { mustache: '#3a2a24', hair: '#3a2a24', body: 'sit', cloth: '#4a6a8a', height: 1.2 },
  cocuk: { hair: '#5a3a24', body: 'sit', cloth: '#e0aa3e', height: .9, headW: 270, headH: 252 },
};
const POS = {
  padisah: [0, .57, -4.85], osman: [0, .57, -4.85], vezir: [-1.85, 0, -3.55], dilsiz1: [2.35, 0, -1.5], dilsiz2: [3.35, 0, -.95],
  ic1: [-5.4, 0, -2.4], ic2: [-5.5, 0, -.9], ic3: [-5.4, 0, .6], konusan: [.95, 0, -1.15],
  baba: [199.72, 0, -.62], cocuk: [200.3, 0, -.36],
};

// sign language: a hand-shape every ~0.28 s, eased between (shoulder, elbow) pairs held in front of the chest
const SIGNS = [[62, 96], [92, 70], [118, 40], [70, 120], [104, 92], [84, 60], [130, 70], [56, 110]];
function sign(t, seed, on = 1, rate = 3.6) {
  if (on <= 0) return null;
  const u = t * rate + seed * 1.7, i = Math.floor(u), f = S(Math.min(1, (u - i) * 1.6));
  const a = SIGNS[(i * 3 + seed) % SIGNS.length], b = SIGNS[((i + 1) * 3 + seed) % SIGNS.length];
  const c = SIGNS[(i * 5 + seed * 2 + 1) % SIGNS.length], d = SIGNS[((i + 1) * 5 + seed * 2 + 1) % SIGNS.length];
  const R = [lerpN(a[0], b[0], f), lerpN(a[1], b[1], f)], Lh = [lerpN(c[0], d[0], f) * .9, lerpN(c[1], d[1], f)];
  const rest = [18, 10];
  return { armR: [lerpN(rest[0], R[0], on), lerpN(rest[1], R[1], on)], armL: [lerpN(rest[0], Lh[0], on), lerpN(rest[1], Lh[1], on)] };
}

// ---------------------------------------------------------------- CAMERA
function cameraPath() {
  const t = W;
  const keys = [
    // hook 1: the page who is about to speak, close; the sultan blurred behind him
    { t: 0, pos: [1.75, 1.42, .55], look: [.75, 1.45, -1.6], fov: 44, creep: .3, drift: .04 },
    // hook 2 "konuşmak": whip onto the sultan's glare
    { t: t('konuşmak') + .1, dur: .3, move: 'whip', pos: [.55, 1.25, -2.25], look: [0, 1.38, -4.85], fov: 40, creep: .34, drift: .03 },
    // "Bakın": pull back wide, the whole silent room, the sun through the lattice
    { t: t('Bakın,') + .35, dur: .3, move: 'whip', pos: [-2.6, 2.7, 4.6], look: [.9, 1.2, -3.0], fov: 56, creep: .22, drift: .08 },
    { t: t('sessizlik') + .2, dur: 1.6, pos: [-3.6, 1.8, 2.4], look: [-5.4, 1.3, -.8], fov: 50, creep: .26 },          // the pages along the wall, mute
    // "Peki": the vizier, puzzled
    { t: t('Peki') + .25, dur: .9, pos: [-.9, 1.5, -1.2], look: [-1.85, 1.45, -3.55], fov: 44, creep: .3 },
    // "Cevap: dilsizler." whip to the two mutes in the sunlight
    { t: t('dilsizler.') - .05, dur: .3, move: 'whip', pos: [2.25, 1.45, 1.55], look: [2.85, 1.35, -1.25], fov: 46, creep: .3, drift: .05 },
    { t: t('kendilerine') + .4, dur: 1.3, pos: [3.7, 1.25, .9], look: [2.75, 1.4, -1.35], fov: 40, creep: .28 },       // signing close
    // "Bu dil öyle yayıldı": wide, the signs spread along the pages
    { t: t('dil') + .3, dur: 1.1, pos: [-2.3, 1.75, 2.6], look: [-5.4, 1.2, -1.0], fov: 50, creep: .24, drift: .08 },
    // "Büyük ihtimalle ilk öğrenen padişah, Genç Osman'dı": low angle push onto the young sultan, signing
    { t: t('Büyük') + .3, dur: .3, move: 'whip', pos: [.15, 1.0, -2.75], look: [0, 1.4, -4.85], fov: 46, creep: .32, drift: .04 },
    // "Padişah, kimsenin duymasını ...": the sultan signs to a mute, the vizier strains to hear
    { t: t('padişah', 2) + .3, dur: .9, pos: [-.05, 1.4, .45], look: [0, 1.15, -4.2], fov: 46, creep: .26 },
    // "Tıpkı": cut to the family table
    { t: t('Tıpkı'), move: 'cut', pos: [200.02, 1.1, 2.05], look: [200.0, .7, -.5], fov: 46, creep: .26, drift: .05 },
    { t: t('bakışla') - .1, dur: .45, pos: [200.02, .95, .6], look: [199.72, .95, -.62], fov: 38, creep: .34 },        // the look
    { t: t('"yeter"') + .25, dur: .3, move: 'whip', pos: [200.62, .85, .5], look: [200.3, .8, -.36], fov: 38, creep: .3 },  // the child freezes
    // "Yani": back to the throne, the sultan's finger on his lips, push in
    { t: t('Yani') + .3, dur: .3, move: 'whip', pos: [.3, 1.3, -2.7], look: [0, 1.3, -4.85], fov: 44, creep: .3 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('ayıptı.') + .03, .8); cp.kick(t('dilsizler.') + .05, .7); cp.kick(t('"yeter"') + .03, .7);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .7) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1a1f3a');
  buildSaray(scene); buildSofra(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  cast.konusan = new Toon({ ...LOOK.ic1, hatColor: '#c8643a', cloth: '#3a7ab8' }, scene);
  // dust in the sun beam, and in the kitchen light
  smokes.motes = new Smoke(scene, { color: '#fff0d0', maxPoints: 500, H: ctx.H, additive: true, near: 2.4 });
  const hash = (i, k) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  const motes = (n, c, sz, on) => smokes.motes.wisps.push({ n, size: .008, alpha: .5, speed: .05, on,
    path: (u, t, i) => [c[0] + (hash(i, 1) - .5) * sz[0] + Math.sin(t * .5 + i) * .06, c[1] + (hash(i, 2) - .5) * sz[1] + (u - .5) * .5, c[2] + (hash(i, 3) - .5) * sz[2] + Math.cos(t * .4 + i * 2) * .06] });
  motes(220, [4.2, 1.8, -1.0], [4.5, 3.0, 3.5], t => t < W('Tıpkı'));
  motes(90, [201.4, 1.4, -.6], [2.4, 1.6, 1.6], t => t >= W('Tıpkı') && t < W('Yani'));
  motes(220, [4.2, 1.8, -1.0], [4.5, 3.0, 3.5], t => t >= W('Yani'));
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .05, 'whoosh'); cue(W('dilsizler.') - .35, 'whoosh'); cue(W('Yani'), 'whoosh');
  cue(W('konuşmak') - .2, 'rise', { dur: .3 }); cue(W('ayıptı.') + .03, 'boom');
  cue(W('dilsizler.') + .05, 'lock'); cue(W('Büyük'), 'rise', { dur: .3 });
  cue(W('Tıpkı'), 'cut'); cue(W('"yeter"') + .03, 'lock'); cue(W('hiç') - .1, 'shimmer');
  cue(0, 'lamps', { dur: W('Tıpkı') });
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const WARM = '#ffb45a', NIGHT = '#d6d1f2', DAY = '#e8e3f4';
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x < 100 ? 'saray' : 'sofra';
  vis('saray', where === 'saray'); vis('sofra', where === 'sofra');
  dyn.beam.visible = where === 'saray'; dyn.kBeam.visible = where === 'sofra';
  dyn.lamps.forEach(k => { k.visible = where === 'saray'; k.flicker(t); });
  dyn.beam.material.uniforms.uT.value = t;
  for (const c of Object.values(cast)) c.hide();
  const A = (w, n) => W(w, n) - 2 / FPS;
  const tint = FACE[where].map((v, i) => v / GRADE[where][i]);
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const P = (k, s = 1, pitch = 0) => { cast[k].show(); cast[k].place(...POS[k], cam, tint, s, pitch); };
  const sunlit = { lit: 1, shade: NIGHT, rim: { color: WARM, a: .38 } };
  if (where === 'saray') {
    const osman = t > A('Büyük') && t < A('padişah', 2) + .2;
    const finale = t > A('Yani');
    // the sultan (or young Osman) on the throne
    const sul = osman ? 'osman' : 'padisah'; P(sul);
    const glare = t > A('konuşmak') && t < A('Bakın,') + .4;
    const hush = finale ? ramp(t, A('Yani') + .2, A('Yani') + .6) : 0;
    const sgOs = osman ? sign(t, 2, ramp(t, A('ilk') - .2, A('ilk') + .2)) : null;
    const sgPad = !osman && t > A('padişah', 2) && t < A('Tıpkı') ? sign(t, 5, ramp(t, A('kimsenin') - .2, A('kimsenin') + .1), 3.0) : null;
    cast[sul].draw({ expr: glare ? 'angry' : osman ? 'smile' : finale ? 'smug' : sgPad ? 'focused' : 'proud', lid: glare ? .35 : finale ? .25 : 0, brow: glare ? -.6 : 0,
      look: sgPad ? .7 : glare ? .25 : 0, lookY: glare ? .1 : 0, blink: bl(1, A('konuşmak'), A('Bakın,'), A('Yani')),
      ...(sgOs || sgPad || (hush > 0 ? sign(t, 7, hush, 1.6) : { armR: [16, 10], armL: [16, 10] })), ...sunlit, lit: 1 });
    cast[sul].castFrom(dyn.sunDir, true);
    // the vizier beside the throne
    cast.vezir.show(); cast.vezir.place(...(t > A('padişah', 2) - .1 && t < A('Tıpkı') ? [-.8, 0, -3.95] : POS.vezir), cam, tint);
    const puzzled = t > A('Peki') && t < A('dilsizler.');
    const strain = t > A('kimsenin') && t < A('Tıpkı');
    const learnV = t > A('saraydaki') && t < A('Büyük') ? sign(t, 3, ramp(t, A('saraydaki'), A('saraydaki') + .3)) : null;
    cast.vezir.draw({ expr: puzzled ? 'worried' : strain ? 'surprised' : learnV ? 'smile' : 'neutral', look: strain ? .8 : puzzled ? .3 : .2, lookY: puzzled ? .2 : 0,
      brow: puzzled ? .7 : 0, blink: bl(2, A('Peki'), A('dilsizler.'), A('kimsenin')), lean: strain ? 6 : 0,
      ...(learnV || (strain ? { armR: [150, 120], armL: [18, 10] } : { armR: [26, 60], armL: [18, 10], propR: 'scroll' })), ...sunlit });
    cast.vezir.castFrom(dyn.sunDir, true);
    // the two mutes in the sun
    for (const [k, seed] of [['dilsiz1', 1], ['dilsiz2', 4]]) {
      cast[k].show();
      const near = k === 'dilsiz1' && t > A('padişah', 2) - .1 && t < A('Tıpkı');
      cast[k].place(...(near ? [.6, 0, -3.6] : POS[k]), cam, tint);
      const show = t > A('dilsizler.') - .1;
      const talking = t > A('Sarayda') && t < A('dil') + .6;
      const toSultan = near;
      const sg = talking ? sign(t + (k === 'dilsiz2' ? .9 : 0), seed, ramp(t, A('Sarayda'), A('Sarayda') + .3)) : null;
      const hello = show && !talking && t < A('Sarayda') ? { armR: [150, 30], armL: [18, 10] } : null;
      cast[k].draw({ expr: toSultan ? 'focused' : show ? (talking ? 'smile' : 'proud') : 'neutral', look: k === 'dilsiz1' ? (toSultan ? -.6 : .5) : -.5,
        blink: bl(seed + 3, A('dilsizler.'), A('Sarayda')), brow: hello ? .6 : 0, bob: hello ? -Math.abs(Math.sin((t - A('dilsizler.')) * 9)) * 8 : 0,
        ...(sg || hello || (toSultan ? { armR: [40, 40], armL: [18, 10] } : { armR: [18, 10], armL: [18, 10] })), ...sunlit });
      cast[k].castFrom(dyn.sunDir, true);
    }
    // the pages along the wall: still and mute, then one after another they sign too
    ['ic1', 'ic2', 'ic3'].forEach((k, i) => {
      P(k);
      const t0 = A('yayıldı') + .35 * i, sg = t > t0 && t < A('Büyük') ? sign(t, 6 + i, ramp(t, t0, t0 + .3)) : null;
      cast[k].draw({ expr: sg ? 'smile' : 'neutral', look: .6, blink: bl(10 + i, t0), ...(sg || { armR: [16, 10], armL: [16, 10] }), lit: 1, shade: NIGHT, rim: { color: WARM, a: .2 } });
      cast[k].castFrom(dyn.sunDir, true);
    });
    // hook: the page who opens his mouth, then covers it
    if (t < A('Bakın,') + .4) {
      P('konusan');
      const talk = t < A('konuşmak') + .15, caught = t > A('ayıptı.') - .05;
      const cover = ramp(t, A('ayıptı.') - .05, A('ayıptı.') + .12);
      cast.konusan.draw({ mouth: talk ? .4 + .45 * Math.abs(Math.sin(t * 13)) : 0, expr: caught ? 'worried' : talk ? 'smug' : 'surprised', sweat: caught ? 1 : 0,
        look: -.55, lookY: 0, brow: caught ? .8 : .2, blink: bl(14, A('konuşmak'), A('ayıptı.')),
        armR: [lerpN(30, 112, cover), lerpN(40, 132, cover)], armL: [lerpN(60, 20, cover), lerpN(30, 10, cover)], ...sunlit });
      cast.konusan.castFrom(dyn.sunDir, true);
    }
  } else {
    // the family at the floor table: the child reaches for the baklava, the father's look stops him
    P('baba'); P('cocuk', .9);
    const look = t > A('bakışla') - .1, stop = t > A('"yeter"');
    cast.baba.draw({ expr: look ? 'angry' : 'smile', lid: look ? .3 : 0, brow: look ? -.4 : 0, look: look ? .9 : .4, gazeX: look ? .8 : 0, blink: bl(20, A('bakışla') - .1),
      armR: [22, 40], armL: [22, 40], lit: 1, shade: DAY, rim: { color: '#ffe2a0', a: .35 } });
    const reach = stop ? 1 - ramp(t, A('"yeter"'), A('"yeter"') + .25) : ramp(t, A('sofrada') - .2, A('babanın') + .4);
    cast.cocuk.draw({ expr: stop ? 'worried' : 'grin', sweat: stop ? 1 : 0, look: stop ? -.85 : .2, lookY: stop ? 0 : .4, brow: stop ? .8 : 0, blink: bl(21, A('"yeter"')),
      armL: [lerpN(20, 82, reach), lerpN(10, 18, reach)], armR: [18, 10], lean: -4 * reach, lit: 1, shade: DAY, rim: { color: '#ffe2a0', a: .35 } });
    cast.baba.castFrom(dyn.kSun, true); cast.cocuk.castFrom(dyn.kSun, true);
  }
  for (const s of Object.values(smokes)) s.update(t);
  // ---- look per set / beat
  const focusOn = (p, coc, range) => ({ focus: cam.position.distanceTo(p), coc, range });
  let look;
  if (where === 'saray') {
    if (t < W('konuşmak')) look = focusOn(V(...POS.konusan).setY(1.45), 7, 1.6);
    else if (t < W('Bakın,') + .2) look = focusOn(V(0, 1.4, -4.85), 7, 2.0);
    else if (t < W('Peki')) look = { focus: 6, coc: 2, range: 8 };
    else if (t < W('dilsizler.') - .2) look = focusOn(V(...POS.vezir).setY(1.5), 6, 2.0);
    else if (t < W('dil') - .2) look = focusOn(V(2.85, 1.4, -1.25), 6, 2.0);
    else if (t < W('Büyük')) look = { focus: 7, coc: 1.5, range: 8 };
    else look = focusOn(V(0, 1.3, -4.6), 6, 2.4);
    Object.assign(look, { sat: 1.22, lift: [.105, .092, .17], bloom: .85, vignette: .22 });
  } else look = { ...focusOn(V(200, .8, -.5), 6, 1.8), sat: 1.45, lift: [.098, .09, .15], bloom: .7, vignette: .2 };
  look.tint = GRADE[where];
  look.blur = cp.moving > .15 ? 16 : 0;
  look.flash = t >= W('Tıpkı') && t < W('Tıpkı') + 2 / FPS ? .35 : 0;
  return look;
}
const GRADE = { saray: [1.02, .99, 1.0], sofra: [1.03, 1.0, .95] };
const FACE = { saray: [1, .985, .965], sofra: [1, 1, .985] };
