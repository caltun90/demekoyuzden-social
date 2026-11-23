// Ayna: dizivanastudio pilotu (format A, akıllıca çözüm). Kurgu karakterler (Max, Sam); fikir: meşgul geçen bekleme daha kısa
// gelir (bekleme algısı). Setler: LOBİ (x≈0) akşam, sarkık lambalar (sıcak) + giriş camından mavi gün sonu; SOKAK (x≈200) gün batımı.
import * as THREE from 'three';
import { stoneTex, woodTex, carpetTex, wallTex, ciniTex, frizTex, painted, flat, rng } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';
import { holedWall, vistaMat, dayGardenTex, nightCityTex } from '/engine/src/vista.js';

export const NAME = 'ayna';
export const FPS = 30;
export let DUR = 36.1;
export const CUES = [];

const S = smoother;
const ramp = (t, a, b) => S((t - a) / (b - a));
const lerpN = (a, b, k) => a + (b - a) * k;
const V = (...a) => new THREE.Vector3(...a);
const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);
const DEG = Math.PI / 180;
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
    if (/Box|Cylinder|Extrude|Lathe|Torus|Sphere/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }
function card(scene, w, h, draw, { pw = 512, hdr = null } = {}) {
  const t = canvasTex(pw, Math.round(pw * h / w), draw);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false, color: hdr || 0xffffff }));
  m.layers.set(1); m.renderOrder = 20; m.visible = false; scene.add(m); return m;
}

// ---------------------------------------------------------------- LOBİ (x = 0)
// 9 x 8 m, tavan 3.4. Arka duvar (z = -3.5): asansör kapısı ortada, kat göstergesi üstünde; sağında aynanın asılacağı yer.
// Sol duvar: posta kutuları. Ön sol: giriş camı (dışarıda gün sonu, mavi). Tavanda iki sarkık lamba (sıcak).
const EL = { x: 0, z: -3.5 }, MIR = { x: 1.55, y: 1.25, z: -3.44 };
function buildLobi(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(9, 8), painted(stoneTex({ base: '#d8d0c4', seam: '#8a7a6a', bw: 128, bh: 128, rep: [9, 8] }))); fl.rotation.x = -Math.PI / 2; g.add(fl);
  const rug = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 3.2), painted(carpetTex({ base: '#2f5ea8', band: '#e0b050', rep: [1, 1], rows: 1 }))); rug.rotation.x = -Math.PI / 2; rug.position.set(0, .005, -1.0); g.add(rug);
  const wall = painted(stoneTex({ base: '#c4d2e6', rep: [3, 1.2] })), wallB = painted(stoneTex({ base: '#c4d2e6', rep: [3, 1.2] }));
  const back = new THREE.Mesh(new THREE.PlaneGeometry(9, 3.4), wallB); back.position.set(0, 1.7, -3.5); g.add(back);
  const right = new THREE.Mesh(new THREE.PlaneGeometry(8, 3.4), wall); right.position.set(4.5, 1.7, .5); right.rotation.y = -Math.PI / 2; g.add(right);
  // left wall with the glass entrance (the cool light)
  const lw = holedWall(8, 3.4, [-1.6, 0, .4, 2.6], painted(stoneTex({ base: '#c4d2e6', rep: [1 / 2.6, 1 / 2.8] })));
  lw.position.set(-4.5, 0, .5); lw.rotation.y = Math.PI / 2; lw.castShadow = true; g.add(lw);
  const out = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 2.8), vistaMat(nightCityTex(), { yaw: Math.atan2(-4.9 - 1, .1 - 3), az: Math.PI / 2, el: [-6 * DEG, 30 * DEG], gain: 1.2 }));
  out.position.set(-4.9, 1.3, .1); out.rotation.y = Math.PI / 2; g.add(out);
  const fr = flat('#3a3040'); for (const [sy, sz, y, z] of [[.1, 2.1, 2.62, .1], [2.6, .1, 1.3, -.95], [2.6, .1, 1.3, 1.15], [2.6, .06, 1.3, .1]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(.16, sy, sz), fr); b.position.set(-4.45, y, z); g.add(b); }
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(9, 8), flat('#b8c0d8')); ceil.rotation.x = Math.PI / 2; ceil.position.y = 3.4; g.add(ceil);
  // wood wainscot on every wall (pattern on the big walls), proud of the wall
  const ws = painted(woodTex({ base: '#8f5a34', plank: 64, vertical: true, rep: [6, 1] })), rail = flat('#5e3a26');
  for (const [w, x, z, ry] of [[9, 0, -3.45, 0], [8, 4.45, .5, -Math.PI / 2]]) {
    const p = new THREE.Mesh(new THREE.PlaneGeometry(w, 1.0), ws); p.position.set(x, .5, z); p.rotation.y = ry; g.add(p);
    const r = new THREE.Mesh(new THREE.BoxGeometry(w, .06, .08), rail); r.position.set(x, 1.02, z); r.rotation.y = ry; g.add(r);
  }
  const friz = new THREE.Mesh(new THREE.PlaneGeometry(9, .3), painted(frizTex())); friz.position.set(0, 3.05, -3.44); g.add(friz);
  // the elevator: a steel frame, two doors, the floor indicator above, the call button
  const steel = flat('#aab4c4'), steelD = flat('#7a8496');
  const box = (sx, sy, sz, x, y, z, m) => { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), m); b.position.set(x, y, z); g.add(b); return b; };
  box(1.6, .14, .14, EL.x, 2.27, EL.z + .07, steelD); for (const s of [-1, 1]) box(.14, 2.27, .14, EL.x + s * .73, 1.135, EL.z + .07, steelD);
  dyn.doors = [-1, 1].map(s => box(.66, 2.2, .05, EL.x + s * .33, 1.1, EL.z + .04, steel));
  for (const d of dyn.doors) { const line = new THREE.Mesh(new THREE.BoxGeometry(.01, 2.2, .055), steelD); d.add(line); line.position.x = 0; }
  dyn.indC = document.createElement('canvas'); dyn.indC.width = 256; dyn.indC.height = 128;
  dyn.indT = new THREE.CanvasTexture(dyn.indC); dyn.indT.colorSpace = THREE.SRGBColorSpace;
  const ind = new THREE.Mesh(new THREE.PlaneGeometry(.5, .25), new THREE.MeshBasicMaterial({ map: dyn.indT, color: HDR(1.3, 1.2, 1.1) })); ind.position.set(EL.x, 2.58, EL.z + .03); g.add(ind);
  box(.56, .31, .03, EL.x, 2.58, EL.z + .01, flat('#2a2630'));
  box(.12, .2, .03, EL.x + .98, 1.15, EL.z + .02, steelD);
  dyn.btn = new THREE.Mesh(new THREE.CircleGeometry(.03, 16), new THREE.MeshBasicMaterial({ color: HDR(1.6, .9, .3) })); dyn.btn.position.set(EL.x + .98, 1.15, EL.z + .04); g.add(dyn.btn);
  // mailboxes on the left of the elevator, a potted plant, a bench
  const mb = flat('#c9963e'); for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) { const b = box(.28, .22, .1, -2.6 + c * .3, 1.45 + r * .25, EL.z + .05, mb); const s = box(.12, .015, .11, -2.6 + c * .3, 1.48 + r * .25, EL.z + .06, flat('#5e3a26')); }
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(.22, .17, .45, 20), flat('#c8663a')); pot.position.set(3.6, .225, -2.9); g.add(pot);
  for (const [dx, dy, r] of [[0, .75, .35], [-.15, 1.05, .25], [.12, 1.2, .22]]) { const b = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), flat('#3f9a48')); b.position.set(3.6 + dx, dy, -2.9); g.add(b); }
  const bench = box(1.4, .08, .45, -3.0, .45, -1.4, painted(woodTex({ base: '#8f5a34' }))); for (const s of [-1, 1]) box(.06, .45, .4, -3.0 + s * .6, .225, -1.4, flat('#3a3040'));
  // the mirror: hidden until Sam hangs it (a gold frame and a silvery sheen; drawn, it does not reflect)
  const mirT = canvasTex(256, 512, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#dfeaf6'); gr.addColorStop(.5, '#9fb4cc'); gr.addColorStop(1, '#c8d8ea');
    c.fillStyle = gr; c.fillRect(0, 0, w, h);
    c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineCap = 'round';
    for (const [x0, w0] of [[.15, 26], [.32, 10], [.62, 18]]) { c.lineWidth = w0; c.beginPath(); c.moveTo(w * x0, h * .95); c.lineTo(w * (x0 + .45), h * .05); c.stroke(); }
  });
  dyn.mirror = new THREE.Group(); dyn.mirror.position.set(MIR.x, MIR.y, MIR.z); g.add(dyn.mirror);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(.9, 2.1), new THREE.MeshBasicMaterial({ map: mirT, color: HDR(1.02, 1.02, 1.04) })); glass.position.z = .02; dyn.mirror.add(glass);
  const gold = flat('#e0b050'); for (const [sx, sy, x, y] of [[1.02, .08, 0, 1.09], [1.02, .08, 0, -1.09], [.08, 2.26, -.49, 0], [.08, 2.26, .49, 0]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, .06), gold); b.position.set(x, y, .02); dyn.mirror.add(b); }
  // lights: two pendant lamps (warm, visible), the cool evening through the glass door
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#a9b4f0', '#6a5a7a', 1.75));
  dyn.pend = [];
  for (const [x, z] of [[-1.3, -1.6], [1.3, -1.6]]) {
    const cord = new THREE.Mesh(new THREE.CylinderGeometry(.008, .008, .8, 4), flat('#2a2630')); cord.position.set(x, 3.0, z); cord.userData.noShadow = true; g.add(cord);
    const shade = new THREE.Mesh(new THREE.ConeGeometry(.26, .22, 24, 1, true), flat('#c9963e', { side: THREE.DoubleSide })); shade.position.set(x, 2.5, z); shade.userData.noShadow = true; g.add(shade);
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(.07, 12, 10), new THREE.MeshBasicMaterial({ color: HDR(2.2, 1.7, .8) })); bulb.position.set(x, 2.38, z); bulb.userData.noShadow = true; g.add(bulb);
    const pl = new THREE.PointLight('#ffc884', 3.6, 6, 1.5); pl.position.set(x, 2.3, z); pl.castShadow = true; pl.shadow.mapSize.set(1024, 1024); pl.shadow.bias = -.003; pl.shadow.radius = 4; L.add(pl);
    dyn.pend.push(V(x, 2.3, z));
  }
  const dusk = new THREE.DirectionalLight('#8aa0ff', 1.6); dusk.position.set(-9, 3, .5); dusk.target.position.set(0, 0, -1); dusk.castShadow = true; dusk.shadow.mapSize.set(1024, 1024);
  Object.assign(dusk.shadow.camera, { left: -6, right: 6, top: 5, bottom: -2, near: 1, far: 20 }); L.add(dusk); L.add(dusk.target);
  scene.add(L); sets.lobi = { g, L };
  shadows(g);
}
function drawIndicator(n, arrow) {
  const key = n + arrow; if (dyn.indK === key) return; dyn.indK = key;
  const c = dyn.indC.getContext('2d'); c.fillStyle = '#1a1420'; c.fillRect(0, 0, 256, 128);
  c.fillStyle = '#ff9a3a'; c.font = '900 92px "Arial Black", sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(String(n), 150, 68);
  if (arrow) { c.beginPath(); c.moveTo(60, 88); c.lineTo(90, 88); c.lineTo(75, 104); c.closePath(); c.moveTo(60, 40); c.fill(); }
  dyn.indT.needsUpdate = true;
}

// ---------------------------------------------------------------- SOKAK (x = 200): gün batımı
function buildSokak(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const sky = new THREE.Mesh(new THREE.PlaneGeometry(80, 30), new THREE.MeshBasicMaterial({ map: canvasTex(64, 256, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#3a4a9a'); gr.addColorStop(.55, '#c87a9a'); gr.addColorStop(.8, '#ffb46a'); gr.addColorStop(1, '#ffd08a'); c.fillStyle = gr; c.fillRect(0, 0, w, h); }) }));
  sky.position.set(0, 10, -22); g.add(sky);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(80, 8), painted(stoneTex({ base: '#5a5a7a', seam: '#3a3a5a', bw: 256, bh: 64, rep: [20, 2] }))); road.rotation.x = -Math.PI / 2; road.position.z = -5; g.add(road);
  const walk = new THREE.Mesh(new THREE.PlaneGeometry(80, 3), painted(stoneTex({ base: '#d8c8b0', seam: '#8a7a6a', bw: 128, bh: 128, rep: [40, 1.5] }))); walk.rotation.x = -Math.PI / 2; walk.position.set(0, .01, .2); g.add(walk);
  const curb = new THREE.Mesh(new THREE.BoxGeometry(80, .12, .2), flat('#b8a890')); curb.position.set(0, .06, -1.3); g.add(curb);
  // a row of houses across the road, trees and street lamps along the walk
  const R = rng(9), cols = ['#e9b07a', '#9ab8d8', '#e8d8a0', '#d88a7a', '#a8c8a0', '#c8a8d8'];
  for (let i = 0; i < 16; i++) {
    const w = 3 + R() * 1.5, h = 4 + R() * 4, x = -30 + i * 4.2;
    const tex = wallTex({ base: cols[i % 6], frame: '#4a4458', cols: 2, rows: [1, 2], night: false });
    const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, 3), painted(tex)); b.position.set(x, h / 2, -11); g.add(b);
    for (let r = 0; r < Math.floor(h / 1.6); r++) for (const dx of [-.7, .7]) { const win = new THREE.Mesh(new THREE.PlaneGeometry(.6, .8), new THREE.MeshBasicMaterial({ color: R() < .4 ? HDR(1.5, 1.1, .5) : new THREE.Color('#3a4a7a') })); win.position.set(x + dx, 1.4 + r * 1.6, -9.49); g.add(win); }
    const roof = new THREE.Mesh(new THREE.ConeGeometry(w * .75, 1.2, 4), flat('#8a3a3a')); roof.rotation.y = Math.PI / 4; roof.position.set(x, h + .6, -11); g.add(roof);
  }
  for (let i = 0; i < 12; i++) {
    const x = -24 + i * 4.5;
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(.08, .1, 1.6, 8), flat('#6a4a3a')); trunk.position.set(x, .8, -.9); g.add(trunk);
    const can = new THREE.Mesh(new THREE.SphereGeometry(.7, 16, 12), flat(i % 2 ? '#3f9a48' : '#5aa84a')); can.position.set(x, 2.1, -.9); g.add(can);
    if (i % 2 === 0) {
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(.04, .05, 3.2, 8), flat('#2a2630')); pole.position.set(x + 2.2, 1.6, -1.0); g.add(pole);
      const lamp = new THREE.Mesh(new THREE.SphereGeometry(.13, 12, 10), new THREE.MeshBasicMaterial({ color: HDR(2.6, 2.0, 1.0) })); lamp.position.set(x + 2.2, 3.25, -1.0); lamp.userData.noShadow = true; g.add(lamp);
    }
  }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#a6b4ff', '#7a6a8a', 1.8));
  const sun = new THREE.DirectionalLight('#ffb460', 3.4); sun.position.set(212, 6, -18); sun.target.position.set(200, 0, 0); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -14, right: 14, top: 8, bottom: -4, near: 1, far: 50 }); sun.shadow.bias = -.0006; sun.shadow.radius = 3; L.add(sun); L.add(sun.target);
  dyn.sSun = V(-12, -6, 18).normalize();
  scene.add(L); sets.sokak = { g, L };
  shadows(g);
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  sam: { hat: 'kulah', hatColor: '#3d5a8a', cloth: '#3a6a9a', apron: true, mustache: true, hair: '#3a2a24', height: 1.68 },
  max: { mustache: '#2a1c18', hair: '#2a2024', cloth: '#4a4a5a', buttons: '#e0b050', collar: true, height: 1.76, headW: 272, headH: 252 },
  muh1: { hat: 'kulah', hatColor: '#f2c23a', cloth: '#e07a2a', buttons: '#7a4a2a', height: 1.7 },
  muh2: { hat: 'kulah', hatColor: '#f2c23a', cloth: '#3a7ab8', pattern: 'stripes', height: 1.62, headW: 256, headH: 240 },
  k1: { hair: '#5a3a24', cloth: '#c8643a', pattern: 'stripes', height: 1.64 },
  k2: { hair: '#2a2024', cloth: '#6a3a7a', buttons: '#e0b050', height: 1.7, headW: 262, headH: 246 },
  k3: { hat: 'kulah', hatColor: '#b8323a', cloth: '#2d7466', height: 1.58 },
  a1: { hair: '#3a2a24', cloth: '#e0aa3e', collar: true, height: 1.66 },
  a2: { hair: '#6a3a24', mustache: true, cloth: '#3a7ab8', height: 1.72, headW: 262, headH: 246 },
};
// tenants wait in a loose arc in front of the elevator
const POS = { k1: [-1.2, 0, -2.2], k2: [-.45, 0, -1.75], k3: [.75, 0, -2.0], sam: [1.75, 0, -1.65], max: [-1.4, 0, .1], muh1: [-.4, 0, .25], muh2: [.35, 0, .45] };

// ---------------------------------------------------------------- CAMERA
function cameraPath() {
  const t = W;
  const keys = [
    // hook: Sam carries the big mirror across the lobby; "ayna": the sheen flashes; "kurtardı": kick
    { t: 0, pos: [2.6, 1.45, -.2], look: [1.6, 1.3, -2.2], fov: 46, creep: .3, drift: .05 },
    { t: t('ayna') + .05, dur: .3, move: 'whip', pos: [2.75, 1.55, -.35], look: [1.5, 1.4, -2.5], fov: 44, creep: .32, drift: .03 },
    // "Bakın, binanın asansörü": the slow indicator, then the impatient tenants
    { t: t('Bakın,') + .3, dur: .3, move: 'whip', pos: [.05, 2.2, -1.9], look: [0, 2.5, -3.5], fov: 40, creep: .3, drift: .02 },
    { t: t('ve') + .2, dur: 1.0, pos: [.2, 1.5, 1.6], look: [-.2, 1.3, -2.4], fov: 50, creep: .26, drift: .06 },
    // "Yönetici Max mühendisleri çağırdı": Max and the engineers; "dev bir fatura": the receipt unrolls
    { t: t('Yönetici') + .3, dur: .3, move: 'whip', pos: [.1, 1.5, 3.4], look: [-.5, 1.25, .2], fov: 46, creep: .26, drift: .05 },
    { t: t('dev') + .1, dur: .5, pos: [-.6, 1.3, 2.4], look: [-.9, 1.1, .2], fov: 46, creep: .32 },
    // "Kapıcı Sam ise": whip to Sam
    { t: t('Kapıcı') + .3, dur: .3, move: 'whip', pos: [2.0, 1.45, .4], look: [1.75, 1.4, -1.65], fov: 42, creep: .3, drift: .04 },
    // "Herkes güldü": wide, everyone laughs
    { t: t('Herkes') + .2, dur: .3, move: 'whip', pos: [.3, 1.9, 3.9], look: [0, 1.2, -1.2], fov: 54, creep: .24, drift: .08 },
    // "Sam ... ayna astı": the mirror goes up beside the door
    { t: t('Sam', 2) + .3, dur: .4, move: 'whip', pos: [2.5, 1.5, -.6], look: [1.5, 1.35, -3.4], fov: 46, creep: .28, drift: .04 },
    // "Ertesi hafta": calm tenants in front of the mirror
    { t: t('Ertesi') + .2, dur: .9, pos: [3.0, 1.5, .3], look: [.8, 1.3, -2.4], fov: 48, creep: .26, drift: .06 },
    // "Asansör aynı hızdaydı": the indicator again; "saçını düzeltiyor": close on the tenants at the mirror
    { t: t('Asansör', 2) + .25, dur: .3, move: 'whip', pos: [.05, 2.2, -1.9], look: [0, 2.5, -3.5], fov: 40, creep: .3, drift: .02 },
    { t: t('insanlar') + .25, dur: .4, move: 'whip', pos: [2.2, 1.45, -.4], look: [1.0, 1.3, -2.4], fov: 44, creep: .3, drift: .04 },
    // "Çünkü yapacak bir şey olunca": the numbers fly by
    { t: t('Çünkü') + .3, dur: .9, pos: [.6, 1.7, -.6], look: [0, 2.2, -3.5], fov: 50, creep: .3 },
    // "Tıpkı sohbet ederken": the street, two friends walking and talking, tracking with them
    { t: t('Tıpkı'), move: 'cut', pos: [197.6, 1.25, 3.4], look: [197.8, 1.1, .1], fov: 46, creep: .2, drift: .0 },
    { t: t('gibi.') + .4, dur: t('gibi.') + .4 - t('Tıpkı'), pos: [203.0, 1.25, 3.4], look: [203.2, 1.1, .1], fov: 46, creep: .2, drift: .0 },
    // "Yani": back to Sam and his mirror
    { t: t('Yani') + .3, dur: .3, move: 'whip', pos: [2.3, 1.5, .4], look: [1.15, 1.35, -2.9], fov: 46, creep: .3, drift: .03 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('kurtardı.') + .03, .8); cp.kick(t('fatura.') + .05, .8); cp.kick(t('astı.') + .03, .6);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .7) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1a1f3a');
  buildLobi(scene); buildSokak(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.receipt = card(scene, .34, 1.6, (c, w, h) => {
    c.fillStyle = '#fbf7ee'; c.fillRect(0, 0, w, h); c.strokeStyle = PLUM; c.lineWidth = 10; c.strokeRect(5, 5, w - 10, h - 10);
    c.fillStyle = '#9a8ea8'; for (let y = 60; y < h - 140; y += 38) { c.fillRect(30, y, w * (.4 + ((y * 7) % 30) / 100), 10); c.fillRect(w - 110, y, 80, 10); }
    c.fillStyle = '#b8323a'; c.fillRect(30, h - 110, w - 60, 60);
  });
  dyn.sparkle = card(scene, .3, .3, (c, w) => { c.fillStyle = '#ffffff'; c.beginPath(); for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4, r = k % 2 ? w * .08 : w * .48; c.lineTo(w / 2 + Math.cos(a) * r, w / 2 + Math.sin(a) * r); } c.closePath(); c.fill(); }, { hdr: HDR(1.5, 1.45, 1.3) });
  dyn.zzz = card(scene, .5, .3, (c, w, h) => { c.strokeStyle = '#fff3c4'; c.lineWidth = 12; c.lineCap = 'round'; for (const [x, y] of [[.2, .7], [.5, .45], [.8, .2]]) { c.beginPath(); c.moveTo(w * (x - .08), h * (y - .1)); c.lineTo(w * (x + .08), h * (y - .1)); c.lineTo(w * (x - .08), h * (y + .1)); c.lineTo(w * (x + .08), h * (y + .1)); c.stroke(); } });
  smokes.motes = new Smoke(scene, { color: '#fff0d0', maxPoints: 300, H: ctx.H, additive: true, near: 2.0 });
  const hash = (i, k) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  smokes.motes.wisps.push({ n: 140, size: .008, alpha: .45, speed: .05, on: t => dyn.where === 'lobi',
    path: (u, t, i) => [(hash(i, 1) - .5) * 4 + Math.sin(t * .5 + i) * .05, 1.2 + (hash(i, 2) - .5) * 1.8 + (u - .5) * .4, -2 + (hash(i, 3) - .5) * 3] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .05, 'whoosh'); cue(W('Herkes') - .05, 'whoosh'); cue(W('Yani'), 'whoosh');
  cue(W('ayna') + .05, 'shimmer'); cue(W('kurtardı.') + .03, 'boom');
  cue(W('fatura.') - .3, 'scrape', { dur: .6 }); cue(W('fatura.') + .05, 'lock');
  cue(W('güldü:') - .1, 'laugh', { dur: 2.2 }); cue(W('astı.') + .03, 'lock'); cue(W('astı.') + .1, 'shimmer');
  cue(W('Tıpkı'), 'cut'); cue(W('Tıpkı'), 'wind', { dur: W('Yani') - W('Tıpkı') });
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const WARM = '#ffb45a', NIGHT = '#d6d1f2', DAY = '#e8e3f4';
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x < 100 ? 'lobi' : 'sokak'; dyn.where = where;
  vis('lobi', where === 'lobi'); vis('sokak', where === 'sokak');
  for (const c of Object.values(cast)) c.hide();
  for (const m of [dyn.receipt, dyn.sparkle, dyn.zzz]) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const tint = FACE[where].map((v, i) => v / GRADE[where][i]);
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const lit = { lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } };
  const P = (k, p = POS[k]) => { cast[k].show(); cast[k].place(...p, cam, tint); cast[k].castFrom(dyn.pend[p[0] < 0 ? 0 : 1]); };
  if (where === 'lobi') {
    // the indicator: crawls (6 -> 5 -> 4 ...) while they wait; flies through the numbers under "Çünkü"
    const fly = t > A('Çünkü') + .3 && t < A('Tıpkı');
    const n = fly ? 9 - Math.floor((t - A('Çünkü') - .3) * 6) % 9 : 7 - Math.floor(t / 5.5) % 6;
    drawIndicator(Math.max(1, n), true);
    const hung = t > A('astı.') - .05;
    const mirrorUp = ramp(t, A('kapısının') - .2, A('astı.'));
    const hookCarry = t < A('Bakın,') + .3;
    // the mirror: carried by Sam in the hook, hidden until he hangs it, then on the wall
    dyn.mirror.visible = hookCarry || t > A('Sam', 2) - .1;
    if (hookCarry) { dyn.mirror.position.set(MIR.x + .05, MIR.y - .02, -2.6); }
    else { dyn.mirror.position.set(MIR.x, lerpN(MIR.y - .25, MIR.y, mirrorUp), lerpN(-3.0, MIR.z, mirrorUp)); }
    // sparkle on the glass: hook "ayna" and "astı."
    for (const at of [A('ayna') + .05, A('astı.') + .03]) if (t > at && t < at + .5) {
      dyn.sparkle.visible = true; const k = (t - at) / .5; dyn.sparkle.scale.setScalar(.3 + Math.sin(Math.PI * k) * .9); dyn.sparkle.rotation.z = t * 3;
      dyn.sparkle.position.copy(dyn.mirror.position).add(V(-.22, .55, .1));
    }
    // tenants
    const calm = t > A('Ertesi') - .1, angry = t > A('ediyordu.') - .6 && t < A('Yönetici');
    const laugh = t > A('güldü:') - .05 && t < A('Sam', 2);
    ['k1', 'k2', 'k3'].forEach((k, i) => {
      const atMirror = calm && t < A('Tıpkı');
      const p = atMirror ? [[.9, 0, -2.55], [1.45, 0, -2.25], [2.05, 0, -2.5]][i] : POS[k];
      if ((t < A('Yönetici') || t > A('Herkes') - .2) && t < A('Yani')) {
        P(k, p);
        const fixHair = atMirror && t > A('saçını') - .2 && i === 0, outfit = atMirror && t > A('kıyafetine') - .2 && i === 2;
        const tap = !calm && !laugh ? Math.abs(Math.sin(t * 6 + i)) : 0;
        cast[k].draw({ expr: laugh ? 'laugh' : atMirror ? (fixHair ? 'smug' : 'smile') : angry ? 'angry' : 'worried', mouth: laugh ? .5 + .5 * Math.abs(Math.sin(t * 13 + i)) : angry ? flap(env, t) * .8 : 0,
          laughMarks: laugh ? .8 : 0, sweat: !calm && !laugh ? 1 : 0, look: atMirror ? .55 : angry ? -.6 : -.1, lookY: atMirror ? 0 : (i === 1 && !angry && !laugh ? .6 : -.25), brow: angry ? -.4 : laugh ? .5 : 0,
          blink: bl(10 + i, A('ediyordu.') - .6, A('güldü:'), A('Ertesi')), bob: laugh ? -Math.abs(Math.sin(t * 13 + i)) * 10 : -tap * 4,
          armR: fixHair ? [150 + 10 * Math.sin(t * 8), 120] : outfit ? [40, 90] : (i === 1 && !calm && !laugh ? [100, 120] : [18, 10]), armL: laugh ? [150, 20] : [18, 10], ...lit });
      }
    });
    // Sam: carries the mirror (hook), asks for it, hangs it, proud at the end
    if (hookCarry || (t > A('Kapıcı') - .2 && (t < A('Ertesi') || t > A('Yani')))) {
      const p = hookCarry ? [MIR.x + .05, 0, -2.25] : t > A('Yani') ? [MIR.x - .75, 0, -2.75] : t > A('Sam', 2) - .2 && t < A('Ertesi') ? [MIR.x - .65, 0, -2.6] : t > A('Ertesi') ? [-1.4, 0, -2.4] : POS.sam;
      P('sam', p);
      const ask = t > A('sadece') - .2 && t < A('Herkes'), proud = hookCarry || t > A('astı.') || t > A('Yani');
      cast.sam.draw({ expr: laugh ? 'smug' : ask ? 'smile' : proud ? 'proud' : 'focused', lid: laugh ? .3 : 0, brow: ask ? .7 : 0, look: hookCarry ? -.3 : .5, mouth: ask ? flap(env, t) * .6 : 0,
        blink: bl(1, A('Kapıcı'), A('Herkes'), A('astı.')), armR: ask ? [150, 20] : hookCarry ? [70, 60] : t > A('Sam', 2) && !hung ? [120, 50] : [18, 10], armL: hookCarry ? [70, 60] : [18, 10], ...lit });
    }
    // Max and the engineers (and Max laughing in the wide)
    if ((t > A('Yönetici') - .4 && t < A('Kapıcı')) || laugh) {
      for (const k of ['max', 'muh1', 'muh2']) P(k);
      const shock = t > A('fatura.') - .1;
      cast.max.draw({ expr: laugh ? 'laugh' : shock ? 'surprised' : 'focused', mouth: laugh ? .5 + .5 * Math.abs(Math.sin(t * 12)) : 0, laughMarks: laugh ? .9 : 0, sweat: shock && !laugh ? 1 : 0,
        look: .6, brow: shock ? 1 : 0, blink: bl(2, A('fatura.'), A('güldü:')), armR: laugh ? [150, 20] : [30, 70], armL: [18, 10], bob: laugh ? -Math.abs(Math.sin(t * 12)) * 12 : 0, ...lit });
      const talk1 = t > A('yeni') - .1 && t < A('dev');
      cast.muh1.draw({ expr: laugh ? 'grin' : talk1 ? 'smug' : 'proud', mouth: talk1 ? flap(env, t) * .7 : laugh ? .6 : 0, look: -.6, blink: bl(3, A('yeni'), A('güldü:')), propR: 'scroll', armR: [70, 40], armL: talk1 ? [120, 40] : [18, 10], ...lit });
      cast.muh2.draw({ expr: laugh ? 'laugh' : 'smug', look: -.5, mouth: laugh ? .5 + .5 * Math.abs(Math.sin(t * 13 + 2)) : 0, laughMarks: laugh ? .8 : 0, blink: bl(4, A('güldü:')), armR: [40, 60], armL: [18, 10], ...lit });
      // the receipt unrolls from the engineer's hand to the floor
      if (t > A('dev') - .2 && t < A('Kapıcı')) {
        const u = backOut(Math.min(1, (t - A('dev') + .2) / .55));
        dyn.receipt.visible = true; dyn.receipt.scale.set(1, Math.max(.05, u), 1);
        dyn.receipt.position.set(-.85, 1.3 - .8 * u, .55);
      }
    }
  } else {
    // two friends walking and talking along the sunset street; the walk feels short
    const u = Math.max(0, t - W('Tıpkı')), x = 197.0 + u * 2.4;
    const step = Math.abs(Math.sin(u * 9));
    for (const [k, dx, sd] of [['a1', 0, 21], ['a2', .55, 22]]) {
      cast[k].show(); cast[k].place(x + dx, 0, .1, cam, tint);
      const talk = k === 'a1' ? Math.sin(u * 2.2) > 0 : Math.sin(u * 2.2) <= 0;
      cast[k].draw({ expr: talk ? 'grin' : 'smile', mouth: talk ? flap(env, t) * .7 + .2 : 0, look: k === 'a1' ? .7 : -.7, blink: bl(sd), bob: -step * 8, lean: 3,
        armR: [18 + 20 * Math.sin(u * 9), 20], armL: [18 - 20 * Math.sin(u * 9), 20], lit: -1, shade: DAY, rim: { color: '#ffb46a', a: .45 } });
      cast[k].castFrom(dyn.sSun, true);
    }
  }
  for (const s of Object.values(smokes)) s.update(t);
  const focusOn = (p, coc, range) => ({ focus: cam.position.distanceTo(p), coc, range });
  let look;
  if (where === 'lobi') look = { ...focusOn(cam.position.clone().add(V(0, 0, -1).applyQuaternion(cam.quaternion).multiplyScalar(2.6)), 5, 2.2), sat: 1.3, lift: [.105, .095, .17], bloom: .85, vignette: .22 };
  else look = { focus: 3.3, coc: 4, range: 2, sat: 1.35, lift: [.11, .095, .15], bloom: .8, vignette: .2 };
  look.tint = GRADE[where];
  look.blur = cp.moving > .15 && where === 'lobi' ? 12 : 0;
  return look;
}
const GRADE = { lobi: [1.02, 1.0, .99], sokak: [1.04, .99, .96] };
const FACE = { lobi: [1, .985, .965], sokak: [1, .985, .96] };
