// Duş Fikri: Demek O Yüzden deneme Short'u (yumurta stili).
// Bilgi: Baird ve ark. 2012 (Psychological Science): zor bir yaratıcılık sorusuna ara verip basit bir iş yapanlar, zor iş
// yapanlara, dinlenenlere ve ara vermeyenlere göre aynı sorulara dönüşte belirgin biçimde daha iyi cevaplar buldu; bu grupta
// zihin gezinmesi daha fazlaydı. Kaynaklar SCRIPT.md'de.
// Setler: DUŞ (x≈200) sabah, mavi çini + yüksek pencereden güneş + fikir ampulü; OFİS (x≈0) gece, mavi oda + masa lambası.
import * as THREE from 'three';
import { stoneTex, woodTex, carpetTex, wallTex, ciniTex, frizTex, painted, flat, rng } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';
import { holedWall, vistaMat, nightCityTex, dayGardenTex } from '/engine/src/vista.js';

export const NAME = 'dus-fikri';
export const FPS = 30;
export let DUR = 24.5;
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
    if (/Box|Cylinder|Extrude|Lathe|Torus|Icosahedron/.test(o.geometry.type) && !o.userData.noShadow) o.castShadow = true;
  });
}
function card(scene, w, h, draw, { pw = 512, hdr = null, layer = 1 } = {}) {
  const c = document.createElement('canvas'); c.width = pw; c.height = Math.round(pw * h / w); draw(c.getContext('2d'), c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false, color: hdr || 0xffffff }));
  m.layers.set(layer); m.renderOrder = 20; m.visible = false; scene.add(m); return m;
}

// ---------------------------------------------------------------- DUŞ (x = 200)
const SH = { x: 199.4, z: -1.3 };          // where the hero stands under the shower
function buildDus(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const tile = (o, rx, ry) => painted(ciniTex({ kind: 'yildiz', a: '#3f86d6', b: '#5ec2c8', c: '#f2f6fb', ...o, rep: [rx, ry] }));
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(5, 5), painted(stoneTex({ base: '#d9e4ee', seam: '#8a9ab4', bw: 64, bh: 64, rep: [6, 6] }))); fl.rotation.x = -Math.PI / 2; g.add(fl);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(5, 3), tile({}, 9, 5.4)); back.position.set(0, 1.5, -2.4); g.add(back);
  const left = new THREE.Mesh(new THREE.PlaneGeometry(5, 3), tile({}, 9, 5.4)); left.position.set(-1.6, 1.5, 0); left.rotation.y = Math.PI / 2; g.add(left);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(5, 5), flat('#e8eef6')); ceil.rotation.x = Math.PI / 2; ceil.position.y = 3; g.add(ceil);
  // right wall: a small high window with the morning outside
  const WZ = [-1.7, -.7], WY = [1.9, 2.6], wc = (WZ[0] + WZ[1]) / 2, wy = (WY[0] + WY[1]) / 2;
  const rw = holedWall(5, 3, [WZ[0], WY[0], WZ[1], WY[1]], painted(stoneTex({ base: '#cfe0ee', rep: [1 / 1.4, 1 / 1.4] })));
  rw.position.set(1.6, 0, 0); rw.rotation.y = -Math.PI / 2; rw.castShadow = true; g.add(rw);
  const out = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 1.0), vistaMat(dayGardenTex(), { yaw: Math.atan2(1.9 - .2, wc - 1.6), az: Math.PI / 2, el: [-5 * DEG, 30 * DEG], gain: 1.2 }));
  out.position.set(1.95, wy, wc); out.rotation.y = -Math.PI / 2; g.add(out);
  const jm = flat('#f4f6fa'); for (const [sy, sz, y, z] of [[.08, 1.1, WY[1] + .03, wc], [.08, 1.1, WY[0] - .03, wc], [.78, .08, wy, WZ[0] - .03], [.78, .08, wy, WZ[1] + .03]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(.3, sy, sz), jm); b.position.set(1.58, y, z); g.add(b); }
  // a painted band of tiles at shoulder height (pattern on the big walls)
  const band = new THREE.Mesh(new THREE.PlaneGeometry(5, .22), painted(frizTex({ rep: [3, 1] }))); band.position.set(0, 1.95, -2.35); g.add(band);
  // shower: pipe, arm, head; the tub rim in front; curtain on a rod (it hides the body)
  const chrome = flat('#b9c3d2');
  const pipe = new THREE.Mesh(new THREE.CylinderGeometry(.025, .025, 1.6, 10), chrome); pipe.position.set(SH.x - 200 - .55, 1.8, SH.z - .5); g.add(pipe);
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(.022, .022, .55, 10), chrome); arm.rotation.z = Math.PI / 2; arm.position.set(SH.x - 200 - .28, 2.58, SH.z - .5); g.add(arm);
  const head = new THREE.Mesh(new THREE.CylinderGeometry(.13, .05, .1, 20), chrome); head.position.set(SH.x - 200, 2.53, SH.z - .5); head.rotation.x = .35; g.add(head);
  dyn.showerHead = V(SH.x, 2.48, SH.z - .45);
  const tub = new THREE.Mesh(new THREE.BoxGeometry(1.9, .5, 1.0), flat('#f6f8fb')); tub.position.set(SH.x - 200, .25, SH.z - .35); g.add(tub);
  const rod = new THREE.Mesh(new THREE.CylinderGeometry(.015, .015, 2.0, 8), chrome); rod.rotation.z = Math.PI / 2; rod.position.set(SH.x - 200, 2.2, SH.z + .2); g.add(rod);
  const cc = document.createElement('canvas'); cc.width = 512; cc.height = 512; const cg = cc.getContext('2d');
  for (let i = 0; i < 8; i++) { cg.fillStyle = i % 2 ? '#f6f2ea' : '#f2b84a'; cg.fillRect(i * 64, 0, 64, 512); }
  cg.fillStyle = 'rgba(42,26,44,.18)'; for (let i = 0; i < 8; i++) cg.fillRect(i * 64 + 58, 0, 6, 512);
  const ct = new THREE.CanvasTexture(cc); ct.colorSpace = THREE.SRGBColorSpace; ct.wrapS = THREE.RepeatWrapping; ct.repeat.set(1.4, 1);
  const curtain = new THREE.Mesh(new THREE.PlaneGeometry(1.8, 1.25, 24, 1), new THREE.MeshLambertMaterial({ map: ct, side: THREE.DoubleSide }));
  const pos = curtain.geometry.attributes.position; for (let i = 0; i < pos.count; i++) pos.setZ(i, Math.sin(pos.getX(i) * 11) * .035);
  curtain.geometry.computeVertexNormals(); curtain.position.set(SH.x - 200, 1.12, SH.z + .2); g.add(curtain);
  // the rest of the curtain bunched up high, from the rod to the curtain top
  const cur2 = new THREE.Mesh(new THREE.PlaneGeometry(.35, 1.0), new THREE.MeshLambertMaterial({ map: ct, side: THREE.DoubleSide })); cur2.position.set(SH.x - 200 + .78, 2.0, SH.z + .2); g.add(cur2);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#cfdcff', '#8a90b8', 2.2));
  const sunDir = V(-1.2, -.55, .25).normalize(); dyn.dSun = sunDir;
  const sun = new THREE.DirectionalLight('#ffd08a', 3.4); sun.position.copy(V(201.6, 2.25, -1.2).addScaledVector(sunDir, -5)); sun.target.position.set(201.6, 2.25, -1.2);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: .5, far: 14 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
  L.add(sun); L.add(sun.target);
  dyn.bulbLight = new THREE.PointLight('#ffd66a', 0, 3, 1.6); L.add(dyn.bulbLight);
  scene.add(L); sets.dus = { g, L };
  shadows(g);
  dyn.dBeam = beam(scene, [201.6, 2.25, -1.2], V(201.6, 2.25, -1.2).addScaledVector(sunDir, 3.2).toArray(), { r0: .4, r1: .8, color: '#ffe2a8', strength: .14 });
}

// ---------------------------------------------------------------- OFİS (x = 0), gece
const DESK = { x: 0, z: -1.0 };
function buildOfis(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), painted(carpetTex({ base: '#3a5a9a', band: '#e0b050', rep: [2, 2], rows: 2 }))); fl.rotation.x = -Math.PI / 2; g.add(fl);
  const wl = painted(wallTex({ base: '#b4c6e2', frame: '#4a4458', cols: 3, rows: [1], night: true }));
  // back wall with a big window onto the night city (the cool key of the room)
  const WX = [-.9, .9], WY = [1.1, 2.5];
  const bw = holedWall(8, 3.2, [WX[0], WY[0], WX[1], WY[1]], painted(stoneTex({ base: '#b4c6e2', rep: [1 / 2, 1 / 3.2] })));
  bw.position.set(0, 0, -2.6); g.add(bw);
  const city = new THREE.Mesh(new THREE.PlaneGeometry(2.1, 1.7), vistaMat(nightCityTex(), { yaw: 0, az: Math.PI / 2, el: [-8 * DEG, 30 * DEG], gain: 1.3 })); city.position.set(0, 1.8, -2.95); g.add(city);
  const fr = flat('#e8e2d6'); for (const [w, h, x, y] of [[1.96, .1, 0, WY[1] + .02], [1.96, .1, 0, WY[0] - .02], [.1, 1.5, WX[0] - .03, 1.8], [.1, 1.5, WX[1] + .03, 1.8], [.06, 1.4, 0, 1.8]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .2), fr); b.position.set(x, y, -2.55); g.add(b); }
  const left = new THREE.Mesh(new THREE.PlaneGeometry(8, 3.2), wl); left.position.set(-3, 1.6, 0); left.rotation.y = Math.PI / 2; g.add(left);
  const right = new THREE.Mesh(new THREE.PlaneGeometry(8, 3.2), wl); right.position.set(3, 1.6, 0); right.rotation.y = -Math.PI / 2; g.add(right);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), flat('#5a5a7a')); ceil.rotation.x = Math.PI / 2; ceil.position.y = 3.2; g.add(ceil);
  // a door on the left wall (the boss leans in there)
  const door = new THREE.Mesh(new THREE.BoxGeometry(.06, 2.1, 1.0), painted(woodTex({ base: '#8a5a3a', vertical: true }))); door.position.set(-2.93, 1.05, .4); door.rotation.y = -.9; door.position.z += .35; g.add(door);
  const df = flat('#e8e2d6'); for (const [h, z, y, d] of [[2.2, -.12, 1.1, .1], [2.2, 1.12, 1.1, .1], [.1, .5, 2.2, 1.34]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(.14, h, d), df); b.position.set(-2.95, y, z); g.add(b); }
  const gap = new THREE.Mesh(new THREE.PlaneGeometry(1.14, 2.1), flat('#ffd99a', { emissive: '#7a5a2a' })); gap.position.set(-2.99, 1.05, .5); gap.rotation.y = Math.PI / 2; g.add(gap);   // the lit corridor behind the door
  // desk, chair, papers, crumpled balls, the lamp
  const wood = painted(woodTex({ base: '#8f6444' }));
  const desk = new THREE.Mesh(new THREE.BoxGeometry(1.5, .06, .75), wood); desk.position.set(DESK.x, .76, DESK.z); g.add(desk);
  for (const [x, z] of [[-.68, -.32], [.68, -.32], [-.68, .32], [.68, .32]]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.05, .76, .05), wood); l.position.set(DESK.x + x, .38, DESK.z + z); g.add(l); }
  const paperM = flat('#f6f2e6');
  for (let i = 0; i < 4; i++) { const p = new THREE.Mesh(new THREE.BoxGeometry(.3, .004, .22), paperM); p.position.set(DESK.x - .25 + i * .04, .795 + i * .004, DESK.z + .05); p.rotation.y = i * .2 - .3; g.add(p); }
  const R = rng(7);
  dyn.balls = [];
  for (let i = 0; i < 9; i++) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(.055 + R() * .02, 0), paperM); b.position.set(DESK.x - 1.1 + R() * 2.2, .06, DESK.z + .3 + R() * 1.0); b.rotation.set(R() * 3, R() * 3, R() * 3); g.add(b); }
  for (let i = 0; i < 3; i++) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(.05, 0), paperM); b.position.set(DESK.x + .3 + i * .1, .82, DESK.z - .15 + i * .05); g.add(b); }
  const mug = new THREE.Mesh(new THREE.CylinderGeometry(.045, .04, .1, 16), flat('#d8573a')); mug.position.set(DESK.x + .55, .84, DESK.z - .1); g.add(mug);
  const lampBase = new THREE.Mesh(new THREE.CylinderGeometry(.08, .1, .03, 16), flat('#2a2630')); lampBase.position.set(DESK.x - .55, .805, DESK.z - .2); g.add(lampBase);
  const lampArm = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, .45, 8), flat('#2a2630')); lampArm.position.set(DESK.x - .55, 1.02, DESK.z - .2); lampArm.rotation.z = -.35; g.add(lampArm);
  const shade = new THREE.Mesh(new THREE.ConeGeometry(.1, .14, 20, 1, true), flat('#3d7a5a', { side: THREE.DoubleSide })); shade.position.set(DESK.x - .44, 1.22, DESK.z - .2); shade.rotation.z = .6; g.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(.035, 12, 10), new THREE.MeshBasicMaterial({ color: HDR(2.0, 1.6, .8) })); bulb.position.set(DESK.x - .41, 1.17, DESK.z - .2); bulb.userData.noShadow = true; g.add(bulb);
  // the keys (found at the end of the search), on the desk next to the mug
  const keys = new THREE.Group(); const gold = flat('#e0b050', { emissive: '#5a3a08' });
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.025, .006, 8, 20), gold); ring.rotation.x = Math.PI / 2; keys.add(ring);
  for (const [a, l] of [[.3, .09], [-.5, .08]]) { const sh = new THREE.Mesh(new THREE.BoxGeometry(l, .006, .016), gold); sh.position.set(Math.cos(a) * (.025 + l / 2), 0, Math.sin(a) * (.025 + l / 2)); sh.rotation.y = -a; keys.add(sh); }
  keys.position.set(DESK.x + .38, .8, DESK.z + .18); keys.visible = false; g.add(keys); dyn.keys = keys;
  // a wall clock above the door side (its hands spin through "saatlerce")
  const clockG = new THREE.Group(); clockG.position.set(-1.6, 2.35, -2.5); g.add(clockG);
  const face = new THREE.Mesh(new THREE.CircleGeometry(.24, 40), flat('#f6f2e6')); face.position.z = .02; clockG.add(face);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(.24, .025, 8, 40), flat('#2a2630')); rim.position.z = .02; clockG.add(rim);
  const hm = flat('#2a1a2c');
  dyn.hourH = new THREE.Mesh(new THREE.BoxGeometry(.025, .12, .01), hm); dyn.hourH.geometry.translate(0, .06, 0); dyn.hourH.position.z = .04; clockG.add(dyn.hourH);
  dyn.minH = new THREE.Mesh(new THREE.BoxGeometry(.016, .19, .01), hm); dyn.minH.geometry.translate(0, .095, 0); dyn.minH.position.z = .05; clockG.add(dyn.minH);
  // a long side table on the right for the experiment beat: hard task (papers) and easy task (a tower of cups)
  const tbl = new THREE.Mesh(new THREE.BoxGeometry(.6, .06, 1.8), wood); tbl.position.set(1.9, .76, .3); g.add(tbl);
  for (const [x, z] of [[1.64, -.55], [2.16, -.55], [1.64, 1.15], [2.16, 1.15]]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.05, .76, .05), wood); l.position.set(x, .38, z); g.add(l); }
  for (let i = 0; i < 6; i++) { const p = new THREE.Mesh(new THREE.BoxGeometry(.3, .004, .22), paperM); p.position.set(1.9, .795 + i * .006, -.2); p.rotation.y = i * .3; g.add(p); }
  dyn.cups = [];
  for (let i = 0; i < 6; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(.05, .04, .1, 14), flat(['#e0604a', '#3f86d6', '#e0b050', '#5ec2c8', '#e0604a', '#3f86d6'][i])); g.add(c); dyn.cups.push(c); }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#8a96ee', '#4a4070', 1.6));
  const lamp = new THREE.SpotLight('#ffcf8a', 9, 6, .9, .5, 1.4); lamp.position.set(DESK.x - .41, 1.17, DESK.z - .2); lamp.target.position.set(DESK.x + .2, .78, DESK.z + .4);
  lamp.castShadow = true; lamp.shadow.mapSize.set(1024, 1024); lamp.shadow.bias = -.002; lamp.shadow.radius = 4; L.add(lamp); L.add(lamp.target);
  const lp2 = new THREE.PointLight('#ffc888', 2.2, 3, 1.6); lp2.position.set(DESK.x - .41, 1.25, DESK.z - .1); L.add(lp2);
  const corr = new THREE.PointLight('#ffd08a', 3.5, 3.5, 1.6); corr.position.set(-2.6, 1.6, .5); L.add(corr);
  const exp = new THREE.PointLight('#ffc888', 5, 4, 1.5); exp.position.set(1.5, 2.4, .3); L.add(exp);
  const moon = new THREE.DirectionalLight('#9ab0ff', 1.4); moon.position.set(0, 3, -6); moon.target.position.set(0, 0, 0); L.add(moon); L.add(moon.target);
  scene.add(L); sets.ofis = { g, L };
  shadows(g);
  dyn.lampPos = V(DESK.x - .41, 1.17, DESK.z - .2);
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  kahraman: { hair: '#3a2a24', cloth: '#2d7466', collar: true, buttons: '#e0b050', height: 1.7 },
  patron: { mustache: '#2a1c18', hair: '#2a2024', cloth: '#5a5a6a', buttons: '#e0b050', height: 1.78, headW: 272, headH: 252 },
  denek1: { hair: '#6a3a24', cloth: '#c8643a', pattern: 'stripes', height: 1.62 },
  denek2: { hair: '#2a2024', cloth: '#6a3a7a', buttons: '#e0b050', height: 1.66, headW: 256, headH: 240 },
};
const POS = { kahraman_dus: [SH.x, .5, SH.z], kahraman: [DESK.x - .05, 0, DESK.z + .62], patron: [-2.55, 0, .55], denek1: [1.5, 0, -.25], denek2: [1.5, 0, .85] };

// ---------------------------------------------------------------- CAMERA
function cameraPath() {
  const t = W;
  const keys = [
    // hook: the face in the steam, eyes shut, humming -> "duşta": pull back, the bulb pops on
    { t: 0, pos: [SH.x + .25, 1.95, SH.z + 1.25], look: [SH.x, 1.85, SH.z], fov: 42, creep: .3, drift: .04 },
    { t: t('duşta') + .25, dur: .35, move: 'whip', pos: [SH.x + .9, 1.65, SH.z + 2.6], look: [SH.x, 1.95, SH.z], fov: 50, creep: .28, drift: .05 },
    // "Bakın, masada saatlerce": whip to the night office, the clock, the stuck hero
    { t: t('Bakın,') + .3, dur: .3, move: 'whip', pos: [.55, 1.55, 1.85], look: [-.2, 1.25, -1.2], fov: 50, creep: .26, drift: .06 },
    { t: t('gelmiyor.') + .05, dur: .5, pos: [.25, 1.25, .95], look: [DESK.x - .05, 1.15, DESK.z + .62], fov: 44, creep: .3 },
    // "Patron gülüyor": the boss in the doorway
    { t: t('Patron') + .3, dur: .3, move: 'whip', pos: [-1.0, 1.55, 2.2], look: [-2.5, 1.5, .55], fov: 44, creep: .3, drift: .04 },
    // "Oysa bilim tersini söylüyor": back on the hero, push in
    { t: t('Oysa') + .2, dur: .35, move: 'whip', pos: [.1, 1.35, 1.25], look: [DESK.x - .05, 1.3, DESK.z + .62], fov: 40, creep: .34 },
    // "Bir deneyde": the side table, hard task vs. easy task
    { t: t('deneyde,') + .2, dur: .35, move: 'whip', pos: [-1.45, 1.5, .3], look: [1.5, 1.3, .3], fov: 46, creep: .26, drift: .05 },
    { t: t('döndüklerinde') + .2, dur: .9, pos: [-.95, 1.5, 1.05], look: [1.5, 1.3, .85], fov: 46, creep: .3 },
    // "Tıpkı aradığın anahtarın": the hero searches, gives up, the keys right in front of him
    { t: t('Tıpkı') + .25, dur: .35, move: 'whip', pos: [.6, 1.45, 1.3], look: [DESK.x, 1.05, DESK.z + .3], fov: 48, creep: .26, drift: .05 },
    { t: t('karşına') + .15, dur: .5, pos: [.62, 1.15, -.35], look: [DESK.x + .38, .8, DESK.z + .18], fov: 36, creep: .3 },
    // "Yani": back to the shower, the bulb glowing
    { t: t('Yani') + .3, dur: .3, move: 'whip', pos: [SH.x + .8, 2.05, SH.z + 2.4], look: [SH.x, 2.1, SH.z], fov: 46, creep: .32, drift: .04 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('duşta') + .1, .7); cp.kick(t('gelir', 2) + .03, .6); cp.kick(t('döndüklerinde') + .3, .6);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .7) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#1a1f3a');
  buildDus(scene); buildOfis(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  // the idea bulb (a drawn card, brighter than white so it blooms) and its burst
  const bulbCard = (c, w, h) => {
    c.lineJoin = c.lineCap = 'round';
    c.fillStyle = '#ffe07a'; c.strokeStyle = PLUM; c.lineWidth = 18;
    c.beginPath(); c.arc(w / 2, h * .38, w * .3, Math.PI * .8, Math.PI * .2); c.lineTo(w * .62, h * .7); c.lineTo(w * .38, h * .7); c.closePath(); c.fill(); c.stroke();
    c.fillStyle = '#fff6c8'; c.beginPath(); c.ellipse(w * .42, h * .3, w * .07, h * .1, -.5, 0, 6.29); c.fill();
    c.fillStyle = '#9aa6b8'; c.beginPath(); c.roundRect(w * .37, h * .72, w * .26, h * .14, 10); c.fill(); c.stroke();
    c.strokeStyle = '#d89a2a'; c.lineWidth = 9; c.beginPath(); c.moveTo(w * .43, h * .66); c.lineTo(w * .46, h * .42); c.lineTo(w * .5, h * .5); c.lineTo(w * .54, h * .42); c.lineTo(w * .57, h * .66); c.stroke();
  };
  dyn.bulbs = [card(scene, .3, .39, bulbCard, { hdr: HDR(1.08, 1.04, .95) }), card(scene, .2, .26, bulbCard, { hdr: HDR(1.08, 1.04, .95) })];
  dyn.bursts = [0, 1].map(() => card(scene, .9, .9, (c, w) => {
    c.strokeStyle = '#fff3c4'; c.lineCap = 'round'; c.lineWidth = 16;
    for (let k = 0; k < 12; k++) { const a = k / 12 * 6.283 + .2, r0 = w * (.3 + (k % 2) * .03), r1 = w * (.44 + (k % 2) * .05); c.beginPath(); c.moveTo(w / 2 + Math.cos(a) * r0, w / 2 + Math.sin(a) * r0); c.lineTo(w / 2 + Math.cos(a) * r1, w / 2 + Math.sin(a) * r1); c.stroke(); }
  }, { hdr: HDR(1.15, 1.1, .95) }));
  // thought bubbles for the wandering mind: three dots, then a cloud with doodles (a fish, a star, a paper plane)
  dyn.thought = [.05, .08, .12].map(r => card(scene, r * 2, r * 2, (c, w) => { c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 18; c.beginPath(); c.arc(w / 2, w / 2, w * .42, 0, 6.29); c.fill(); c.stroke(); }));
  dyn.cloud = card(scene, .62, .44, (c, w, h) => {
    c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 12; c.lineJoin = 'round';
    c.beginPath(); for (let k = 0; k < 9; k++) { const a = k / 9 * 6.283; c.arc(w / 2 + Math.cos(a) * w * .3, h / 2 + Math.sin(a) * h * .28, w * .12, 0, 6.29); } c.fill();
    c.beginPath(); c.ellipse(w / 2, h / 2, w * .36, h * .32, 0, 0, 6.29); c.fill();
    c.lineWidth = 9; c.strokeStyle = '#3f86d6'; c.beginPath(); c.ellipse(w * .3, h * .52, w * .07, h * .06, 0, 0, 6.29); c.moveTo(w * .37, h * .52); c.lineTo(w * .42, h * .45); c.lineTo(w * .42, h * .59); c.closePath(); c.stroke();   // fish
    c.strokeStyle = '#e0b050'; c.beginPath(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, r = k % 2 ? w * .03 : w * .07; c.lineTo(w * .52 + Math.cos(a) * r, h * .42 + Math.sin(a) * r); } c.closePath(); c.stroke();   // star
    c.strokeStyle = '#e0604a'; c.beginPath(); c.moveTo(w * .62, h * .62); c.lineTo(w * .76, h * .5); c.lineTo(w * .66, h * .56); c.closePath(); c.stroke();          // plane
  });
  dyn.sparkle = card(scene, .12, .12, (c, w) => { c.fillStyle = '#fff6c8'; c.beginPath(); for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4, r = k % 2 ? w * .1 : w * .48; c.lineTo(w / 2 + Math.cos(a) * r, w / 2 + Math.sin(a) * r); } c.closePath(); c.fill(); }, { hdr: HDR(1.6, 1.5, 1.2) });
  // water and steam in the shower
  smokes.water = new Smoke(scene, { color: '#d6ecff', maxPoints: 900, H: ctx.H, additive: true, near: .8 });
  const hash = (i, k) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  smokes.water.wisps.push({ n: 320, size: .016, alpha: .75, speed: 1.5, on: t => dyn.where === 'dus',
    path: (u, t, i) => { const h = dyn.showerHead, a = hash(i, 1) * 6.283, r = .05 + hash(i, 2) * .2 * (.4 + u); return [h.x + Math.cos(a) * r * 1.3, h.y - u * 2.0, h.z + .3 * u + Math.sin(a) * r * .5]; } });
  smokes.steam = new Smoke(scene, { color: '#eae6f0', maxPoints: 500, H: ctx.H, near: .6 });
  smokes.steam.wisps.push({ n: 70, size: .35, alpha: .16, speed: .05, on: t => dyn.where === 'dus',
    path: (u, t, i) => [SH.x - .6 + hash(i, 1) * 1.6 + Math.sin(t * .3 + i) * .2, 1.4 + u * 1.4 + hash(i, 2) * .3, SH.z - .8 + hash(i, 3) * .9] });
  smokes.motes = new Smoke(scene, { color: '#fff0d0', maxPoints: 300, H: ctx.H, additive: true, near: 2.0 });
  smokes.motes.wisps.push({ n: 120, size: .008, alpha: .5, speed: .05, on: t => dyn.where === 'dus',
    path: (u, t, i) => [200.9 + (hash(i, 1) - .5) * 1.8 + Math.sin(t * .5 + i) * .05, 1.6 + (hash(i, 2) - .5) * 1.4 + (u - .5) * .4, -1.1 + (hash(i, 3) - .5) * 1.2] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .05, 'whoosh'); cue(W('deneyde,') - .05, 'whoosh'); cue(W('Yani'), 'whoosh');
  cue(0, 'simmer', { dur: W('Bakın,') + .2 }); cue(W('duşta') + .05, 'shimmer'); cue(W('Patron') + .1, 'whoosh');
  cue(W('saatlerce'), 'scrape', { dur: .9 }); cue(W('gelir', 2) + .03, 'lock'); cue(W('döndüklerinde') + .3, 'shimmer');
  cue(W('karşına') + .1, 'shimmer'); cue(W('Yani') + .2, 'simmer', { dur: DUR - W('Yani') - .2 });
}

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const WARM = '#ffb45a', NIGHT = '#d6d1f2', DAY = '#e8e3f4';
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos);
  if (wob) m.rotation.z = Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04;
  return s;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 100 ? 'dus' : 'ofis';
  vis('dus', where === 'dus'); vis('ofis', where === 'ofis'); dyn.dBeam.visible = where === 'dus';
  dyn.where = where;
  for (const c of Object.values(cast)) c.hide();
  for (const m of [...dyn.bulbs, ...dyn.bursts, ...dyn.thought, dyn.cloud, dyn.sparkle]) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const tint = FACE[where].map((v, i) => v / GRADE[where][i]);
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const H = cast.kahraman;
  dyn.bulbLight.intensity = 0;
  if (where === 'dus') {
    H.show(); H.place(...POS.kahraman_dus, cam, tint);
    const idea = t > A('duşta') + .05, end = t > A('Yani');
    H.draw({ expr: idea ? (end ? 'smile' : 'surprised') : 'smug', lid: idea ? 0 : .85, brow: idea && !end ? 1 : .2, look: .15, lookY: idea && !end ? -.6 : 0,
      mouth: !idea ? .25 + .2 * Math.sin(t * 9) : 0, blink: bl(1, A('duşta') + .05, A('Yani')),
      armR: idea && !end ? [150, 30] : [70 + 10 * Math.sin(t * 4), 120], armL: [60 - 10 * Math.sin(t * 4), 110], lit: 1, shade: DAY, rim: { color: '#ffe2a0', a: .3 } });
    H.castFrom(dyn.dSun, true);
    const bp = V(SH.x + .05, 2.62, SH.z + .15);
    const at = end ? A('Yani') + .25 : A('duşta') + .05, s = popCard(dyn.bulbs[0], at, t, bp);
    popCard(dyn.bursts[0], at, t, bp.clone().add(V(0, 0, -.01)), 1, false); if (t - at > .25) dyn.bursts[0].visible = false; else dyn.bursts[0].material.opacity = 1 - (t - at) / .25;
    dyn.bulbLight.position.copy(bp); dyn.bulbLight.intensity = s * .45;
  } else {
    // the hero at the desk
    const search = t > A('aradığın') && t < A('karşına') + .1, gave = t > A('bıraktığında') - .1;
    const stuck = t < A('Oysa');
    const smugSci = t > A('Oysa') && t < A('deneyde,');
    if (t < A('deneyde,') || t > A('Tıpkı')) {
      H.show(); H.place(...POS.kahraman, cam, tint);
      const sr = search && !gave ? Math.sin((t - A('aradığın')) * 7) : 0;
      H.draw({ expr: gave ? (t > A('karşına') + .1 ? 'surprised' : 'neutral') : search ? 'worried' : stuck ? (t > A('Patron') ? 'angry' : 'worried') : smugSci ? 'smug' : 'neutral',
        sweat: stuck && t > A('saatlerce') ? 1 : 0, look: search ? sr * .9 : stuck ? (t > A('Patron') ? -.8 : .2) : .1, lookY: stuck && t < A('Patron') ? .7 : gave ? .6 : 0, gazeY: gave ? 1 : 0,
        brow: smugSci ? .7 : t > A('karşına') + .1 ? 1 : 0, lid: smugSci ? .3 : 0, blink: bl(2, A('Patron'), A('Oysa'), A('aradığın'), A('karşına') + .1),
        armR: search && !gave ? [60 + 30 * sr, 50] : gave && t < A('karşına') ? [80, 120] : stuck ? [20 + 15 * Math.abs(Math.sin(t * 3)), 140] : [22, 30], armL: gave && t < A('karşına') ? [80, 120] : stuck ? [40, 150] : [22, 30],
        lit: -1, shade: NIGHT, rim: { color: WARM, a: .45 } });
      H.castFrom(dyn.lampPos);
    }
    // the boss in the doorway
    if (t > A('Patron') - .4 && t < A('Oysa') + .2) {
      const P = cast.patron; P.show(); P.place(...POS.patron, cam, tint);
      const talk = t > A('"Biraz') - .05 && t < A('gelir', 2) + .4, laugh = !talk;
      P.draw({ mouth: talk ? flap(ctx.env, t) : .5 + .5 * Math.abs(Math.sin(t * 13)), expr: talk ? 'smug' : 'laugh', laughMarks: laugh ? .9 : 0, look: .7, brow: talk ? .6 : 0,
        blink: bl(3, A('"Biraz')), armR: talk ? [95, 20] : [30, 60], armL: [laugh ? 150 : 20, laugh ? 20 : 10], bob: laugh ? -Math.abs(Math.sin(t * 13)) * 10 : 0,
        lit: -1, shade: NIGHT, rim: { color: '#ffd08a', a: .5 } });
      P.castFrom(V(-2.6, 1.6, .5));
    }
    // the experiment: hard task (sweats over papers) vs. easy task (stacks cups, mind wanders, then the idea)
    const ex = t > A('deneyde,') - .4 && t < A('Tıpkı') + .3;
    dyn.cups.forEach((c, i) => {
      const built = ex ? Math.min(6, Math.floor((t - A('zor')) * 3.2)) : 6;
      const up = i < built; c.visible = where === 'ofis';
      c.position.set(1.9 + (up ? 0 : .12), up ? .84 + i * .095 : .84, up ? .9 : .55 + i * .08);
    });
    if (ex) {
      const D1 = cast.denek1, D2 = cast.denek2;
      D1.show(); D1.place(...POS.denek1, cam, tint); D2.show(); D2.place(...POS.denek2, cam, tint);
      const back = t > A('geri') + .1;
      D1.draw({ expr: back ? 'worried' : 'focused', sweat: 1, look: .7, lookY: .7, gazeY: 1, blink: bl(4, A('geri') + .1), armR: [40 + 8 * Math.sin(t * 9), 120], armL: [30, 130], lean: 4,
        lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } });
      D2.draw({ expr: back ? 'grin' : 'smile', look: back ? .7 : .5, lookY: back ? .5 : -.2, lid: back ? 0 : .4, blink: bl(5, A('geri') + .1),
        armR: back ? [150, 30] : [55 + 15 * Math.sin(t * 5), 70], armL: [25, 40], lit: 1, shade: NIGHT, rim: { color: WARM, a: .4 } });
      D1.castFrom(V(1.5, 2.4, .3)); D2.castFrom(V(1.5, 2.4, .3));
      const head2 = V(POS.denek2[0], 1.5, POS.denek2[2]);
      if (back) {
        const bp = head2.clone().add(V(0, .62, 0)), at = A('döndüklerinde') + .3;
        popCard(dyn.bulbs[1], at, t, bp); popCard(dyn.bursts[1], at, t, bp.clone().add(V(0, 0, -.01)), .55, false);
        if (t - at > .25) dyn.bursts[1].visible = false; else dyn.bursts[1].material.opacity = 1 - (t - at) / .25;
      }
      // the wandering mind (before the return, and again under "zihnin ... gezinmesi")
      const wander = (t > A('basit') && t < A('geri')) || (t > A('zihnin') - .1 && t < A('Tıpkı'));
      if (wander) {
        const t0 = t > A('zihnin') - .1 ? A('zihnin') - .1 : A('basit');
        const RT = V(1, 0, 0).applyQuaternion(cam.quaternion), UP = V(0, 1, 0).applyQuaternion(cam.quaternion);
        const at2 = (r, u) => head2.clone().addScaledVector(RT, r).addScaledVector(UP, u);
        dyn.thought.forEach((m, i) => { popCard(m, t0 + i * .12, t, at2(-.24 - i * .1, .2 + i * .13), 1, false); });
        const cl = popCard(dyn.cloud, t0 + .4, t, at2(-.5, .44));
        if (cl) dyn.cloud.position.y += Math.sin(t * 2) * .02;
      }
    }
    // the keys: hidden under the papers until the hero stops searching
    dyn.keys.visible = t > A('bıraktığında') - .2;
    if (t > A('karşına')) { const at = A('karşına'); popCard(dyn.sparkle, at, t, V(DESK.x + .4, .86, DESK.z + .2), 1, false); dyn.sparkle.rotation.z = t * 2; }
    // the clock spins through "saatlerce"
    const spin = ramp(t, A('saatlerce') - .1, A('gelmiyor.') + .2) * 30;
    dyn.minH.rotation.z = -spin * 6.283 - 1.2; dyn.hourH.rotation.z = -spin * 6.283 / 12 - 2.4;
  }
  for (const s of Object.values(smokes)) s.update(t);
  const focusOn = (p, coc, range) => ({ focus: cam.position.distanceTo(p), coc, range });
  let look;
  if (where === 'dus') look = { ...focusOn(V(SH.x, 1.9, SH.z), 6, 1.6), sat: 1.35, lift: [.1, .095, .16], bloom: .6, vignette: .18 };
  else {
    const f = t > A('Patron') && t < A('Oysa') ? V(...POS.patron).setY(1.5) : t > A('deneyde,') && t < A('Tıpkı') ? V(1.5, 1.4, .4) : t > A('karşına') ? V(DESK.x + .38, .8, DESK.z + .18) : V(...POS.kahraman).setY(1.2);
    look = { ...focusOn(f, 6, 1.8), sat: 1.25, lift: [.105, .095, .18], bloom: .9, vignette: .22 };
  }
  look.tint = GRADE[where];
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
const GRADE = { dus: [1.0, 1.0, 1.0], ofis: [1.01, .99, 1.01] };
const FACE = { dus: [1, .99, .98], ofis: [1, .985, .97] };
