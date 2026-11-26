// Kendi evinin kokusunu neden alamazsın? Demek O Yüzden günlük Short (yumurta stili), 26 Kasım 2026.
// Bilgi: gönüllülerin evine iki hafta boyunca aynı koku kondu; iki haftanın sonunda o kokuyu fark etme eşikleri yükseldi
// (Dalton ve Wysocki, 1996). Açıklama: koku alma uyumu; burun ve beyin değişmeyen kokuya verdiği yanıtı azaltır, yeni kokuya
// duyarlı kalır (Dalton, 2000). Kaynaklar SCRIPT.md'de.
// Setler: EV (x≈0) pencere ışığı, ada tezgâh (ocakta tencere, tabakta balık), buzdolabı, kapı; DENEY EVİ (x≈200) sarkıt lamba,
// masa, koku şişesi, takvim, gönüllü ve önlüklü araştırmacı.
import * as THREE from 'three';
import { stoneTex, woodTex, tileTex, painted, flat } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { Smoke, beam, glow } from '/engine/src/fx.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-26-ev-kokusu';
export const FPS = 30;
export let DUR = 35.5;
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
// one wavy "smell" line: plum underlay, coloured stroke
function drawWave(c, w, h, col) {
  c.lineCap = c.lineJoin = 'round';
  const path = () => { c.beginPath(); c.moveTo(w * .5, h * .94); c.bezierCurveTo(w * 1.05, h * .78, -w * .05, h * .62, w * .5, h * .48); c.bezierCurveTo(w * 1.05, h * .34, -w * .05, h * .2, w * .5, h * .06); };
  c.strokeStyle = PLUM; c.lineWidth = w * .3; path(); c.stroke();
  c.strokeStyle = col; c.lineWidth = w * .17; path(); c.stroke();
}
// a little house with its own smell (col) or with none (col = null)
function drawHouse(c, w, h, wall, roof, col) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = 14;
  const x0 = w * .18, x1 = w * .82, y0 = h * .56, y1 = h * .95;
  c.fillStyle = wall; c.beginPath(); c.rect(x0, y0, x1 - x0, y1 - y0); c.fill(); c.stroke();
  c.fillStyle = roof; c.beginPath(); c.moveTo(w * .08, y0 + 4); c.lineTo(w * .5, h * .3); c.lineTo(w * .92, y0 + 4); c.closePath(); c.fill(); c.stroke();
  c.fillStyle = '#7a4a2a'; c.beginPath(); c.roundRect(w * .43, h * .72, w * .14, y1 - h * .72, 6); c.fill(); c.stroke();
  c.fillStyle = '#ffe9a8'; c.lineWidth = 9; c.beginPath(); c.rect(w * .25, h * .66, w * .12, h * .12); c.fill(); c.stroke(); c.beginPath(); c.rect(w * .63, h * .66, w * .12, h * .12); c.fill(); c.stroke();
  if (col) for (const dx of [-.16, 0, .16]) { c.save(); c.translate(w * (.5 + dx) - w * .06, h * .02); drawWave(c, w * .12, h * .27, col); c.restore(); }
}
function drawMark(ch, col) {
  return (c, w, h) => { c.lineJoin = 'round'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .84}px "Arial Black", "Inter", sans-serif`;
    c.strokeStyle = PLUM; c.lineWidth = 36; c.strokeText(ch, w / 2, h * .54); c.fillStyle = col; c.fillText(ch, w / 2, h * .54); };
}
// the "volume" of the smell: label + five bars, lv of them lit
function drawMeter(c, w, h, lv) {
  c.lineJoin = c.lineCap = 'round';
  c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 30); c.fill(); c.stroke();
  c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .2}px "Arial Black", "Inter", sans-serif`; c.fillText('KOKU', w / 2, h * .22);
  for (let i = 0; i < 5; i++) {
    const bw = w * .12, x = w * .14 + i * w * .152, bh = h * (.14 + i * .095), y = h * .88 - bh, on = lv >= i + 1 ? 1 : lv > i ? lv - i : 0;
    c.fillStyle = '#d9d3e6'; c.lineWidth = 8; c.beginPath(); c.roundRect(x, y, bw, bh, 8); c.fill(); c.stroke();
    if (on > 0) { c.fillStyle = i > 2 ? '#58b848' : '#8fd05a'; c.beginPath(); c.roundRect(x, y + bh * (1 - on), bw, bh * on, 8); c.fill(); c.stroke(); }
  }
}
// the wall calendar of the experiment: day d
function drawCal(c, w, h, d) {
  c.lineJoin = c.lineCap = 'round';
  c.fillStyle = '#fbf7ee'; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 24); c.fill(); c.stroke();
  c.save(); c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 24); c.clip(); c.fillStyle = '#d8483a'; c.fillRect(0, 0, w, h * .3); c.restore();
  c.beginPath(); c.moveTo(10, h * .3); c.lineTo(w - 10, h * .3); c.stroke(); c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 24); c.stroke();
  c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#fbf7ee'; c.font = `900 ${h * .17}px "Arial Black", "Inter", sans-serif`; c.fillText('GÜN', w / 2, h * .175);
  c.fillStyle = PLUM; c.font = `900 ${h * .5}px "Arial Black", "Inter", sans-serif`; c.fillText(String(Math.round(d)), w / 2, h * .66);
}
// the hum of the fridge: three arcs
function drawHum(c, w, h) {
  c.lineCap = 'round';
  for (const [r, lw] of [[.3, .09], [.58, .09], [.86, .09]]) { for (const [col, k] of [[PLUM, 1.7], ['#ffe15a', 1]]) { c.strokeStyle = col; c.lineWidth = w * lw * k; c.beginPath(); c.arc(0, h / 2, w * r, -.75, .75); c.stroke(); } }
}

// ---------------------------------------------------------------- EV (x = 0)
const POT = V(-.62, .99, -.3), FISH = V(.8, .99, -.26), HERO = { x: .2, z: -.95 }, KOMSU = { x: 1.5, z: -1.02 }, FR = V(-2.75, 0, -2.02), EAR = { x: -1.98, z: -1.4 };
const WIN = V(-1.25, 2.2, -2.36), DOOR = V(2.3, 0, -2.36);
function buildEv(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 9), painted(woodTex({ base: '#c9935f', rep: [5, 4] })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 0); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 5), painted(stoneTex({ base: '#bfc3f4', seam: '#9da0dc', bw: 64, bh: 64, rep: [12, 5] })));
  wall.position.set(0, 2.5, -2.4); g.add(wall);
  const dado = new THREE.Mesh(new THREE.BoxGeometry(12, .42, .05), painted(tileTex({ a: '#e8b23e', b: '#f2ead8', rep: [28, 1] }))); dado.position.set(0, 1.25, -2.36); g.add(dado);
  for (const y of [1.02, 1.48]) { const m = new THREE.Mesh(new THREE.BoxGeometry(12, .05, .08), flat('#eef3fb')); m.position.set(0, y, -2.35); g.add(m); }
  // the counter along the wall, the island in front of it
  const top = flat('#f6efe0');
  const bc = new THREE.Mesh(new THREE.BoxGeometry(3.3, .9, .6), flat('#3f9a8a')); bc.position.set(-.55, .45, -2.08); g.add(bc);
  const bt = new THREE.Mesh(new THREE.BoxGeometry(3.4, .06, .68), top); bt.position.set(-.55, .93, -2.06); g.add(bt);
  const isl = new THREE.Mesh(new THREE.BoxGeometry(2.9, .9, .74), flat('#ee8a66')); isl.position.set(.3, .45, -.3); g.add(isl);
  const it = new THREE.Mesh(new THREE.BoxGeometry(3.02, .06, .86), top); it.position.set(.3, .93, -.3); g.add(it);
  for (let i = 0; i < 4; i++) { const d = new THREE.Mesh(new THREE.BoxGeometry(.58, .62, .03), flat('#f8a888')); d.position.set(-.75 + i * .7, .47, .08); g.add(d);
    const k = new THREE.Mesh(new THREE.BoxGeometry(.05, .14, .03), flat('#f1e2bd')); k.position.set(-.55 + i * .7, .6, .11); g.add(k); }
  for (const [x, col, hh] of [[-.2, '#e8b23e', .26], [.1, '#d8483a', .2], [.38, '#f2ead8', .3], [.8, '#5b8fe0', .24]]) { const j = new THREE.Mesh(new THREE.CylinderGeometry(.09, .09, hh, 14), flat(col)); j.position.set(x, .96 + hh / 2, -2.1); g.add(j);
    const l = new THREE.Mesh(new THREE.CylinderGeometry(.095, .095, .04, 14), flat('#7a5644')); l.position.set(x, .98 + hh, -2.1); g.add(l); }
  // the window: the light of the set
  const pane = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.2), new THREE.MeshBasicMaterial({ color: HDR(1.75, 1.5, 1.05) })); pane.position.copy(WIN); g.add(pane);
  const fr = flat('#f1ece2');
  for (const [w, h, x, y] of [[1.18, .09, 0, .64], [1.18, .12, 0, -.65], [.09, 1.36, -.55, 0], [.09, 1.36, .55, 0], [.05, 1.2, 0, 0], [1.0, .05, 0, .1]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .1), fr); b.position.set(WIN.x + x, WIN.y + y, WIN.z + .06); b.userData.noShadow = true; g.add(b); }
  // the front door the neighbour comes through
  const door = new THREE.Mesh(new THREE.BoxGeometry(.96, 2.06, .06), flat('#c8483a')); door.position.set(DOOR.x, 1.03, DOOR.z + .02); g.add(door);
  for (const [w, h, x, y] of [[1.2, .1, 0, 2.11], [.1, 2.16, -.55, 1.08], [.1, 2.16, .55, 1.08]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .12), fr); b.position.set(DOOR.x + x, y, DOOR.z + .05); b.userData.noShadow = true; g.add(b); }
  for (const y of [.62, 1.5]) { const p = new THREE.Mesh(new THREE.BoxGeometry(.62, .62, .03), flat('#de6a55')); p.position.set(DOOR.x, y, DOOR.z + .065); p.userData.noShadow = true; g.add(p); }
  const knob = new THREE.Mesh(new THREE.SphereGeometry(.05, 12, 10), flat('#f0c455')); knob.position.set(DOOR.x - .36, 1.05, DOOR.z + .1); g.add(knob);
  // the fridge that hums in the corner
  const fg = new THREE.Group(); fg.position.copy(FR); g.add(fg); dyn.fridge = fg;
  const fb = new THREE.Mesh(new THREE.BoxGeometry(.84, 1.92, .68), flat('#f7f9ff')); fb.position.y = .96; fg.add(fb);
  const seam = new THREE.Mesh(new THREE.BoxGeometry(.85, .025, .02), flat('#8a96c0')); seam.position.set(0, 1.3, .345); seam.userData.noShadow = true; fg.add(seam);
  for (const [y, h] of [[1.52, .3], [.95, .5]]) { const hd = new THREE.Mesh(new THREE.BoxGeometry(.05, h, .06), flat('#5b6aa8')); hd.position.set(.3, y, .37); fg.add(hd); }
  for (const [x, y, col] of [[-.2, 1.62, '#e2463f'], [-.02, 1.5, '#f0c455'], [-.22, 1.44, '#58b848']]) { const mg = new THREE.Mesh(new THREE.BoxGeometry(.1, .1, .02), flat(col)); mg.position.set(x, y, .35); mg.userData.noShadow = true; fg.add(mg); }
  // the hob and the pot on the island
  const plate = new THREE.Mesh(new THREE.BoxGeometry(.62, .035, .52), flat('#3a4066')); plate.position.set(POT.x, .975, POT.z); g.add(plate);
  dyn.flames = [];
  for (let k = 0; k < 10; k++) { const a = k / 10 * 6.283, f = new THREE.Mesh(new THREE.ConeGeometry(.024, .08, 6), new THREE.MeshBasicMaterial({ color: HDR(3.2, 1.3, .35) })); f.position.set(POT.x + Math.cos(a) * .16, 1.03, POT.z + Math.sin(a) * .16); f.userData.noShadow = true; f.layers.set(1); g.add(f); dyn.flames.push(f); }
  const pg = new THREE.Group(); pg.position.set(POT.x, POT.y + .01, POT.z); g.add(pg); dyn.pot = pg;
  const pb = new THREE.Mesh(new THREE.CylinderGeometry(.17, .16, .2, 24), flat('#4f86d8')); pb.position.y = .1; pg.add(pb);
  dyn.lid = new THREE.Mesh(new THREE.CylinderGeometry(.18, .18, .03, 24), flat('#f1e2bd')); dyn.lid.position.y = .215; pg.add(dyn.lid);
  const lk = new THREE.Mesh(new THREE.SphereGeometry(.03, 12, 10), flat('#2a2f52')); lk.position.y = .035; dyn.lid.add(lk);
  for (const sd of [-1, 1]) { const h = new THREE.Mesh(new THREE.BoxGeometry(.09, .025, .05), flat('#2a2f52')); h.position.set(sd * .2, .16, 0); pg.add(h); }
  // the fish on its plate
  const pl = new THREE.Mesh(new THREE.CylinderGeometry(.21, .15, .03, 26), flat('#fbf7ee')); pl.position.set(FISH.x, .975, FISH.z); g.add(pl);
  const fishG = new THREE.Group(); fishG.position.set(FISH.x, 1.035, FISH.z); fishG.rotation.y = .25; g.add(fishG);
  const fbody = new THREE.Mesh(new THREE.SphereGeometry(.1, 20, 14), flat('#c4dcf0')); fbody.scale.set(1.45, .5, .62); fishG.add(fbody);
  const tail = new THREE.Mesh(new THREE.ConeGeometry(.07, .11, 4), flat('#a8c8e8')); tail.rotation.z = -Math.PI / 2; tail.scale.z = .35; tail.position.x = -.17; fishG.add(tail);
  const eye = new THREE.Mesh(new THREE.SphereGeometry(.014, 8, 6), flat('#2a1a2c')); eye.position.set(.09, .028, .045); eye.userData.noShadow = true; fishG.add(eye);
  const lemon = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, .012, 14), flat('#f2d23a')); lemon.position.set(FISH.x + .11, .998, FISH.z + .1); lemon.userData.noShadow = true; g.add(lemon);
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#b9c6ff', '#8a7a9a', 1.5));
  const KEYP = V(-2.0, 2.9, -1.4); dyn.keyP = KEYP;
  const key = new THREE.SpotLight('#ffd9a0', 12, 12, .95, .6, 1.3); key.position.copy(KEYP); key.target.position.set(.5, .8, -.5);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .7); fill.position.set(2, 3, 6); fill.target.position.set(0, 1, -1); L.add(fill); L.add(fill.target);
  dyn.fire = new THREE.PointLight('#ff9a4a', 0, 1.3, 1.8); dyn.fire.position.set(POT.x, 1.1, POT.z + .2); L.add(dyn.fire);
  scene.add(L); sets.ev = { g, L };
  shadows(g);
  dyn.aBeam = beam(scene, [WIN.x, WIN.y, WIN.z + .1], [.5, .6, .2], { r0: .5, r1: 1.5, color: '#ffe2a8', strength: .1 });
  dyn.aGlow = glow(scene, [WIN.x, WIN.y, WIN.z + .15], '#ffd28a', 1.9, .2);
}

// ---------------------------------------------------------------- DENEY EVİ (x = 200)
const D1 = { x: -.5, z: -.95 }, HOCA = { x: .58, z: -.98 }, LAMP = V(200, 2.95, -.9), BOT = V(200.04, .83, -.3);
function buildDeney(scene) {
  const g = new THREE.Group(); g.position.x = 200; scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 9), painted(stoneTex({ base: '#d2daf0', seam: '#a6b4d8', bw: 128, bh: 128, rep: [8, 6], seed: 4 })));
  fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 0); g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 5), flat('#8fc4c8')); wall.position.set(0, 2.5, -2.7); g.add(wall);
  const lam = new THREE.Mesh(new THREE.BoxGeometry(12, 1.15, .06), painted(woodTex({ base: '#b58a66', rep: [6, 1], vertical: true }))); lam.position.set(0, .575, -2.66); g.add(lam);
  const rail = new THREE.Mesh(new THREE.BoxGeometry(12, .07, .1), flat('#f1ece2')); rail.position.set(0, 1.18, -2.64); g.add(rail);
  const band = new THREE.Mesh(new THREE.BoxGeometry(12, .3, .04), painted(tileTex({ a: '#f0c455', b: '#eef3fb', rep: [40, 1] }))); band.position.set(0, 2.62, -2.67); g.add(band);
  // the lamp over the table
  const cord = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, 1.4, 6), flat('#2a2f52')); cord.position.set(0, LAMP.y + .85, LAMP.z); g.add(cord);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(.08, .3, .2, 22, 1, true), new THREE.MeshLambertMaterial({ color: '#c8483a', side: THREE.DoubleSide })); shade.position.set(0, LAMP.y + .1, LAMP.z); shade.userData.noShadow = true; g.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(.08, 14, 10), new THREE.MeshBasicMaterial({ color: HDR(2.7, 2.0, 1.0) })); bulb.position.set(0, LAMP.y, LAMP.z); g.add(bulb);
  // the table and the scent bottle
  const tt = new THREE.Mesh(new THREE.BoxGeometry(1.1, .06, .66), flat('#f6efe0')); tt.position.set(.04, .8, -.3); g.add(tt);
  const ap = new THREE.Mesh(new THREE.BoxGeometry(1.02, .12, .58), flat('#7a5a8a')); ap.position.set(.04, .72, -.3); g.add(ap);
  for (const dx of [-.48, .48]) for (const dz of [-.26, .26]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.05, .68, .05), flat('#4a3a6a')); l.position.set(.04 + dx, .34, -.3 + dz); g.add(l); }
  const bg = new THREE.Group(); bg.position.set(BOT.x - 200, BOT.y, BOT.z); g.add(bg); dyn.bottle = bg;
  const bb = new THREE.Mesh(new THREE.CylinderGeometry(.085, .1, .2, 20), flat('#b06ad8')); bb.position.y = .1; bg.add(bb);
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(.04, .05, .07, 14), flat('#f1e2bd')); neck.position.y = .235; bg.add(neck);
  for (const [rz, rx] of [[.28, 0], [-.3, .1], [.05, -.3]]) { const st = new THREE.Mesh(new THREE.CylinderGeometry(.008, .008, .34, 6), flat('#7a5644')); st.position.y = .4; st.rotation.z = rz; st.rotation.x = rx; st.position.x = -rz * .16; bg.add(st); }
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
  kahraman: { hair: '#3a2a24', cloth: '#e8553a', collar: true, height: 1.7 },
  komsu: { mustache: '#4a3a38', hair: '#6a5a58', hat: 'kulah', hatColor: '#2f8f6a', cloth: '#e0aa3e', buttons: '#7a4a2a', pocket: true, bodyW: 238, headW: 284, headH: 256, height: 1.76 },
  hoca: { beard: '#e4e4ee', beardLen: .7, hair: '#d9d9e4', cloth: '#f2f3f8', clothDark: '#b9bdd6', buttons: '#8a96c0', pocket: true, headW: 268, height: 1.74 },
  denek: { hair: '#6a3a24', cloth: '#3f9a6a', pattern: 'stripes', height: 1.66, headW: 262, headH: 246 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hook: { pos: [.62, 1.34, 2.0], look: [.62, 1.3, -.6], fov: 44 },
  fish: { pos: [FISH.x + .05, 1.78, .72], look: [FISH.x, 1.05, FISH.z], fov: 40 },
  face: { pos: [HERO.x + .1, 1.5, 1.05], look: [HERO.x, 1.5, HERO.z], fov: 40 },
  solo: { pos: [.2, 1.6, 3.4], look: [.2, 1.5, -1], fov: 50 },
  two: { pos: [.86, 1.55, 3.4], look: [.86, 1.42, -1], fov: 50 },
  komsu: { pos: [.98, 1.5, 1.95], look: [1.32, 1.44, -1.02], fov: 46 },
  lab: { pos: [200.04, 1.42, 3.5], look: [200.04, 1.36, -.8], fov: 48 },
  labIn: { pos: [200.04, 1.4, 2.8], look: [200.04, 1.42, -.8], fov: 46 },
  meter: { pos: [HERO.x + .04, 1.41, 2.25], look: [HERO.x, 1.41, HERO.z], fov: 44 },
  fridge: { pos: [-1.7, 1.38, 1.7], look: [-2.36, 1.3, -1.8], fov: 46 },
  pot: { pos: [-.2, 1.36, 2.4], look: [-.2, 1.3, -.6], fov: 44 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: sniffing over the fish -> the fish that plainly smells -> his blank face
    { t: 0, ...SHOT.hook, creep: .34, drift: .03 },
    { t: t('kokusunu') + .1, dur: .2, move: 'whip', ...SHOT.fish, creep: .34, drift: .02 },
    { t: t('neden') + .12, dur: .2, move: 'whip', ...SHOT.face, creep: .34, drift: .02 },
    { t: t('Bakın,') + .16, dur: .3, move: 'whip', ...SHOT.solo, creep: .24, drift: .04 },
    { t: t('ama') + .1, dur: .7, pos: [.2, 1.56, 2.9], look: [.2, 1.56, -1], fov: 48, creep: .22, drift: .02 },
    // the neighbour at the door
    { t: t('Kapıdan') + .1, dur: .3, move: 'whip', ...SHOT.komsu, creep: .28, drift: .03 },
    { t: t('Sen') - .08, dur: .3, move: 'whip', ...SHOT.two, creep: .13, drift: .02 },
    // the experiment
    { t: t('Araştırmacılar') + .2, dur: .3, move: 'whip', ...SHOT.lab, creep: .2, drift: .03 },
    { t: t('gönüllülerin') + .3, dur: .8, ...SHOT.labIn, creep: .1, drift: .01 },
    { t: t('iki', 2) + .1, dur: .6, ...SHOT.lab, creep: .16, drift: .015 },
    { t: t('gönüllüler') + .1, dur: .7, ...SHOT.labIn, creep: .1, drift: .01 },
    // back home: the nose turns the volume down
    { t: t('Çünkü') + .2, dur: .3, move: 'whip', ...SHOT.meter, creep: .1, drift: .02 },
    { t: t('Tıpkı') + .14, dur: .28, move: 'whip', ...SHOT.fridge, creep: .28, drift: .02 },
    // a new smell gets through at once
    { t: t('Böylece') + .2, dur: .3, move: 'whip', ...SHOT.pot, creep: .1, drift: .02 },
    { t: t('Yani') + .2, dur: .3, move: 'whip', ...SHOT.two, creep: .1, drift: .015 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('pişmiş!"') + .05, .45); cp.kick(t('yok.') + .05, .4); cp.kick(t('zor') + .1, .45); cp.kick(t('hemen', 2) + .02, .6); cp.kick(t('alıştı.') + .1, .6);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .8) * FPS) / FPS;
  const { scene } = ctx;
  scene.background = new THREE.Color('#33407a');
  buildEv(scene); buildDeney(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  const waves = (n, col) => Array.from({ length: n }, () => card(scene, .13, .36, (c, w, h) => drawWave(c, w, h, col), { pw: 96 }));
  dyn.fishW = waves(4, '#9be05a'); dyn.botW = waves(4, '#e58af0');
  dyn.houses = [['#f2c9d8', '#c8483a', '#ff8ab8'], ['#cfe6f7', '#3f6fb8', '#b98a5a'], ['#f6efc8', '#3f9a5c', '#9be05a']].map(([a, b, c2]) => card(scene, .5, .56, (c, w, h) => drawHouse(c, w, h, a, b, c2), { pw: 384 }));
  dyn.mine = card(scene, .62, .7, (c, w, h) => drawHouse(c, w, h, '#f7e3c0', '#e8553a', null), { pw: 448 });
  dyn.q = [0, 1].map(() => card(scene, .3, .36, drawMark('?', '#ffe15a'), { pw: 256 }));
  dyn.bang = card(scene, .3, .4, drawMark('!', '#ff5a4a'), { pw: 256 });
  dyn.meter = dynCard(scene, .86, .62, drawMeter, { steps: 4 });
  dyn.cal = dynCard(scene, .6, .66, drawCal, { steps: 1, pw: 384 });
  dyn.hum = [card(scene, .8, .32, drawMark('BZZZ', '#ffe15a'), { pw: 512 }), card(scene, .34, .44, drawHum, { pw: 256 })];
  // dark smoke from the pot that burns
  smokes.burn = new Smoke(scene, { color: '#4a4258', maxPoints: 700, H: ctx.H, near: .3 });
  const burnK = t => ramp(t, W('yanan') - .1, W('yanan') + .5) * (1 - ramp(t, W('Yani') - .1, W('Yani') + .3));
  for (const s of [1, 2, 3]) smokes.burn.wisps.push({ n: 90, size: .36, alpha: .6, speed: .4, seed: s * 2, on: t => dyn.where === 'ev' && t > W('yanan') - .1 && t < W('Yani') + .3, fade: burnK,
    path: (u, t) => [POT.x + (s - 2) * .06 + Math.sin(u * 7 + t * 3 + s) * .2 * u, POT.y + .22 + u * (1.0 + s * .12), POT.z + Math.cos(u * 5 + s) * .08 * u] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('Bakın,') + .02, 'whoosh'); cue(W('Araştırmacılar') + .1, 'whoosh'); cue(W('Çünkü') + .1, 'whoosh');
  cue(W('kokusunu') + .05, 'rise', { dur: .3 }); cue(W('neden') + .08, 'rise', { dur: .3 });
  cue(W('misafirliğe') + .1, 'lock'); cue(W('her'), 'lock'); cue(W('kendine'), 'lock'); cue(W('seninki'), 'shimmer');
  cue(W('Kapıdan') + .02, 'rise', { dur: .35 }); cue(W('pişmiş!"') + .05, 'boom'); cue(W('Sen') - .1, 'rise', { dur: .35 });
  cue(W('kokluyorsun,'), 'lock'); cue(W('kokluyorsun,', 2), 'lock'); cue(W('yok.') + .05, 'cut');
  cue(W('evine') + .1, 'lock'); cue(W('iki'), 'shimmer'); for (let k = 0; k < 6; k++) cue(W('hafta') + k * .2, 'lock');
  cue(W('zor') + .1, 'boom');
  cue(W('burnun'), 'lock'); cue(W('beynin,'), 'lock'); cue(W('sesini') - .1, 'wind', { dur: W('kısıyor.') + .5 - W('sesini') });
  cue(W('Tıpkı') + .05, 'rise', { dur: .35 }); cue(W('buzdolabının'), 'simmer', { dur: W('duymaman') - W('buzdolabının') });
  cue(W('Böylece') + .1, 'rise', { dur: .35 }); cue(W('yanan') - .05, 'simmer', { dur: W('Yani') - W('yanan') }); cue(W('hemen', 2) + .02, 'boom');
  cue(W('Yani') + .1, 'rise', { dur: .35 }); cue(W('kokuyor;') + .05, 'shimmer'); cue(W('alıştı.') + .1, 'boom');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'KENDİ EVİN NEDEN KOKMAZ?'); }

// ---------------------------------------------------------------- PER FRAME
const vis = (set, on) => { sets[set].g.visible = on; sets[set].L.visible = on; };
const COOL = '#d6d6f6', WARM = '#ffcf8a';
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos); m.material.opacity = 1;
  if (wob) m.rotation.z = Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04;
  return s;
}
// smell lines that rise from a point and fade, over and over
function stink(pool, t, P, k, RT, spread = .13, rise = .46) {
  pool.forEach((m, i) => {
    const u = (t * .62 + i / pool.length) % 1, dx = (i - (pool.length - 1) / 2) * spread;
    m.visible = k > .01; if (!m.visible) return;
    m.position.copy(P).addScaledVector(RT, dx + Math.sin(u * 6.283 + i) * .015); m.position.y += .1 + u * rise;
    m.material.opacity = Math.sin(Math.PI * u) * k; m.scale.setScalar(.75 + u * .6);
  });
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  const where = cam.position.x > 100 ? 'deney' : 'ev';
  vis('ev', where === 'ev'); vis('deney', where === 'deney'); dyn.where = where;
  dyn.aBeam.visible = dyn.aGlow.visible = where === 'ev'; dyn.bBeam.visible = dyn.bGlow.visible = where === 'deney';
  for (const c of Object.values(cast)) c.hide();
  for (const m of [...dyn.fishW, ...dyn.botW, ...dyn.houses, dyn.mine, ...dyn.q, dyn.bang, dyn.meter, dyn.cal, ...dyn.hum]) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const RT = V(1, 0, 0).applyQuaternion(cam.quaternion), UP = V(0, 1, 0).applyQuaternion(cam.quaternion);
  let look, grade = [1, 1, 1], face = [1, .985, .97];
  if (where === 'ev') {
    grade = [1.01, 1.0, 1.01];
    const tint = face.map((v, i) => v / grade[i]);
    const H = cast.kahraman, K = cast.komsu;
    const inHook = t < A('Bakın,'), inL2 = !inHook && t < A('Kapıdan'), inL3 = t >= A('Kapıdan') && t < A('Sen') - .1, inL4 = t >= A('Sen') - .1 && t < A('Araştırmacılar') + .4;
    const inL7 = t > A('Çünkü') - .3 && t < A('Tıpkı') + .1, inL8 = t >= A('Tıpkı') + .1 && t < A('Böylece') + .16, inL9 = t >= A('Böylece') + .16 && t < A('Yani') + .16, inL10 = t >= A('Yani') + .16;
    // ---- the fish smells all the time; the pot only burns in the example
    const burn = inL9 ? ramp(t, A('yanan'), A('yanan') + .3) : 0;
    dyn.flames.forEach((f, i) => { f.visible = burn > 0; f.scale.set(1, Math.max(.01, burn * (.9 + .5 * Math.abs(Math.sin(t * 27 + i * 2.1)))), 1); });
    dyn.fire.intensity = burn * (.3 + .06 * Math.sin(t * 23));
    dyn.lid.position.y = .215 + burn * Math.abs(Math.sin(t * 31)) * .03; dyn.lid.rotation.z = burn * Math.sin(t * 27) * .12;
    dyn.pot.rotation.z = burn * Math.sin(t * 41) * .015;
    const pulse = inL10 && t > A('kokuyor;') ? 1 + .5 * Math.exp(-(t - A('kokuyor;')) * 2.5) : 1;
    stink(dyn.fishW, t, FISH.clone().setY(1.05), 1, RT, .13 * pulse, .46 * pulse);
    // ---- the fridge hums
    const humming = inL8;
    dyn.fridge.position.x = FR.x + (humming ? Math.sin(t * 70) * .004 : 0); dyn.fridge.rotation.z = humming ? Math.sin(t * 55) * .004 : 0;
    // ---- the hero
    const atEar = inL8;
    const hx = atEar ? EAR.x : HERO.x + (inHook ? .12 : 0), hz = atEar ? EAR.z : HERO.z;
    const head = V(hx, 1.49, hz), at = (r, u) => head.clone().addScaledVector(RT, r).addScaledVector(UP, u);
    const sniff = (t0, n = 2) => { const k = (t - t0) * 5; return k > 0 && k < n ? Math.abs(Math.sin(k * Math.PI)) : 0; };
    let hp = { expr: 'neutral', look: 0, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(1, A('neden'), A('ama'), A('hiçbir'), A('burnun'), A('sesini'), A('yanan'), A('hemen', 2), A('kokuyor;'), A('alıştı.')) };
    if (inHook) {
      const s = sniff(0, 3);
      hp = t < A('neden') ? { ...hp, expr: 'worried', look: .7, lookY: .4, gazeX: 1, gazeY: .6, brow: .7, lean: 7, bob: -s * 9, armL: [20, 14], armR: [44, -70] }
        : { ...hp, expr: 'worried', look: .15, lookY: -.1, brow: .7, armL: [58, -72], armR: [58, -72] };
    }
    if (inL2) {
      const mine = t > A('seninki');
      hp = t < A('ama') ? { ...hp, expr: 'smile', look: 0, lookY: -.55, gazeY: -1, brow: .5, armR: [150, 20] }
        : { ...hp, expr: mine ? 'worried' : 'neutral', lookY: -.5, gazeY: -1, brow: mine ? .7 : .2, armL: mine ? [58, -72] : [16, 10], armR: mine ? [58, -72] : [16, 10] };
    }
    if (inL3) hp = { ...hp, expr: t > A('"Sizde') ? 'surprised' : 'smile', look: .8, gazeX: 1, brow: t > A('"Sizde') ? .9 : .2, mouth: t > A('balık') ? .35 : 0 };
    if (inL4) {
      const s = Math.max(sniff(A('kokluyorsun,'), 1.6), sniff(A('kokluyorsun,', 2), 1.6)), none = t > A('hiçbir');
      hp = none ? { ...hp, expr: 'worried', look: .4, brow: .8, armL: [58, -72], armR: [58, -72] }
        : { ...hp, expr: 'focused', look: .75, lookY: .4, gazeX: 1, gazeY: .5, lid: .3, brow: .2, lean: 6, bob: -s * 10 };
    }
    if (inL7) {
      const nose = t > A('burnun') && t < A('beynin,'), brain = t >= A('beynin,') && t < A('hep'), down = t > A('sesini');
      hp = { ...hp, expr: down ? 'smug' : 'neutral', look: .1, lookY: down ? -.3 : 0, gazeY: down ? -1 : 0, lid: down ? .3 : 0, brow: nose || brain ? .5 : 0, armR: nose ? [148, -128] : brain ? [164, -40] : [16, 10], armL: down ? [150, 20] : [16, 10] };
    }
    if (inL8) {
      const deaf = t > A('duymaman');
      hp = deaf ? { ...hp, expr: 'smile', look: .3, brow: .4, armL: [58, -72], armR: [58, -72] }
        : { ...hp, expr: 'focused', look: -.8, gazeX: -1, lean: -7, brow: .4, armL: [150, -130], armR: [16, 10] };
    }
    if (inL9) {
      const smell = t > A('hemen', 2);
      hp = smell ? { ...hp, expr: 'surprised', look: -.85, lookY: .2, gazeX: -1, brow: 1, mouth: .55, sweat: 1, armL: [150, 24], armR: [150, 24], bob: Math.sin(t * 22) * 3 }
        : { ...hp, expr: 'smile', look: .5, lookY: -.2, brow: .2, lid: .2, armL: [30, -100], armR: [30, -96] };
    }
    if (inL10) {
      const fin = t > A('alıştı.');
      hp = { ...hp, expr: fin ? 'grin' : t > A('sadece') ? 'smile' : 'worried', look: t > A('sadece') ? .1 : .6, brow: .6, armL: [58, -72], armR: fin ? [148, -128] : [58, -72] };
    }
    const fishShot = t > W('kokusunu') + .2 && t < W('neden') + .22;
    if (!fishShot) { H.show(); H.place(hx, 0, hz, cam, tint); }
    H.draw({ ...hp, lit: -1, shade: COOL, rim: { color: WARM, a: .4 } }); H.castFrom(dyn.keyP);
    // ---- the neighbour: nose first through the door
    const here = t > A('Kapıdan') - .2;
    if (here && !inL7 && !inL8 && !inL9) {
      const enter = inL3 ? backOut((t - A('Kapıdan') + .2) / .32) : 1;
      const talk = t > A('"Sizde') - .04 && t < A('pişmiş!"') + .45;
      const laugh = (inL4 && t > A('yok.') - .1) || (inL10 && t > A('alıştı.') - .05);
      const sn = Math.max(sniff(A('komşuysa'), 2), 0);
      let kp = { expr: 'smile', look: -.6, armL: [16, 10], armR: [16, 10], blink: bl(2, A('komşuysa'), A('hemen'), A('"Sizde'), A('Sen'), A('yok.'), A('kokuyor;'), A('alıştı.')) };
      if (inL3 && t > A('komşuysa')) kp = { ...kp, expr: 'focused', lookY: -.3, brow: .5, lid: .3, bob: -sn * 9 };
      if (inL3 && t > A('hemen')) kp = { ...kp, expr: 'worried', brow: -.3, lid: .1, look: -.7, armR: [152, -132], sweat: 1 };
      if (talk) kp = { ...kp, expr: 'angry', brow: -.4, look: -.75, mouth: flap(env, t), armL: [100, 26 + 12 * Math.sin(t * 13)], armR: [152, -132] };
      if (inL4 && !laugh) kp = { ...kp, expr: 'smug', look: -.7, lid: .3, armR: [152, -132] };
      if (inL10 && !laugh) kp = { ...kp, expr: 'worried', look: -.65, brow: -.2, armR: [152, -132], armL: [100, 26 + 10 * Math.sin(t * 9)] };
      if (laugh) kp = { ...kp, expr: 'laugh', laughMarks: .9, look: -.5, mouth: .5 + .5 * Math.abs(Math.sin(t * 13)), bob: -Math.abs(Math.sin(t * 13)) * 10, armL: [28, -100], armR: [152, -132] };
      K.show(); K.place(KOMSU.x + (1 - enter) * 1.3, 0, KOMSU.z, cam, tint);
      K.draw({ ...kp, lit: -1, shade: COOL, rim: { color: WARM, a: .4 } }); K.castFrom(dyn.keyP);
    }
    // ---- every house has a smell of its own; his seems to have none
    if (inL2) {
      const gone = t > A('seninki') - .08;
      if (!gone) [['misafirliğe', -.52, .58], ['her', 0, .82], ['kendine', .52, .58]].forEach(([w, r, u], i) => { const s = popCard(dyn.houses[i], A(w) + (i ? 0 : .1), t, at(r, u), .9); if (s) dyn.houses[i].position.addScaledVector(UP, Math.sin(t * 2.4 + i) * .012); });
      else { popCard(dyn.mine, A('seninki') - .08, t, at(0, .74)); popCard(dyn.q[0], A('hiç'), t, at(.42, .98)); }
    }
    if (inL4 && t > A('hiçbir')) popCard(dyn.q[0], A('hiçbir'), t, at(.05, .5));
    // ---- the volume of the smell goes down
    if (inL7 && t > A('burnun') - .1) {
      const lv = lerpN(5, 1, ramp(t, A('önemsiz'), A('kısıyor.') + .25));
      dyn.meter.userData.set(lv); const s = popCard(dyn.meter, A('burnun') - .1, t, at(0, .62), .85, false); if (s) dyn.meter.rotation.z += Math.sin(t * 2) * .02;
    }
    // ---- the hum he no longer hears
    if (inL8) {
      const k = 1 - ramp(t, A('süre'), A('duymaman') + .1), src = V(FR.x + .12, 2.22, FR.z + .4);
      dyn.hum.forEach((m, i) => { m.visible = k > .02; m.position.copy(src).addScaledVector(RT, i * .62); m.position.y += Math.sin(t * 40 + i) * .008; m.material.opacity = k; m.scale.setScalar((1 + .08 * Math.sin(t * 18 + i * 2)) * (.55 + .45 * k)); m.rotation.z += Math.sin(t * 36) * .03; });
      if (t > A('duymaman')) popCard(dyn.q[1], A('duymaman'), t, at(.05, .5));
    }
    if (inL9 && t > A('hemen', 2)) popCard(dyn.bang, A('hemen', 2), t, at(.02, .52));
    const f = t > W('kokusunu') + .1 && t < W('neden') + .1 ? FISH.clone().setY(1.1) : inL3 ? V(KOMSU.x, 1.5, KOMSU.z) : inL8 ? V(EAR.x, 1.4, EAR.z) : V(hx, 1.4, hz);
    look = { focus: cam.position.distanceTo(f), coc: 5, range: 2.4, sat: 1.24, lift: [.085, .085, .15], bloom: .85, vignette: .22 };
  } else {
    // ---- the experiment: the same smell in the volunteer's home for two weeks
    grade = [1.0, .995, 1.02];
    const tint = face.map((v, i) => v / grade[i]);
    const R = cast.hoca, D = cast.denek;
    const placed = t > A('evine'), smell = t > A('kokuyu'), later = t > A('iki', 2), ask = t > A('gönüllüler'), none = t > A('zor');
    dyn.bottle.visible = placed; if (placed) dyn.bottle.scale.setScalar(.2 + .8 * backOut((t - A('evine')) / .22));
    stink(dyn.botW, t, BOT.clone().setY(BOT.y + .34), smell ? ramp(t, A('kokuyu'), A('kokuyu') + .3) : 0, RT, .12, .5);
    // the researcher
    let rp = { expr: 'smug', look: -.3, armL: [16, 10], armR: [16, 10], blink: bl(3, A('gönüllülerin'), A('iki'), A('iki', 2), A('gönüllüler'), A('zor')) };
    if (t > A('gönüllülerin') && !later) rp = { ...rp, expr: placed ? 'proud' : 'neutral', look: -.6, lookY: .4, brow: .3, armL: placed && t < A('iki') ? [84, 30] : [16, 10], armR: t > A('iki') ? [150, 22] : [16, 10] };
    if (later) rp = { ...rp, expr: ask ? 'focused' : 'neutral', look: -.7, brow: ask ? .6 : 0, mouth: ask && !none ? .3 : 0, armL: ask ? [96, 28] : [16, 10] };
    if (none) rp = { ...rp, expr: 'surprised', look: -.6, brow: 1, mouth: .4, armL: [96, 28], armR: [150, 22] };
    R.show(); R.place(200 + HOCA.x, 0, HOCA.z, cam, tint);
    R.draw({ ...rp, lit: -1, shade: COOL, rim: { color: WARM, a: .4 } }); R.castFrom(LAMP);
    // the volunteer: day one he notices, day fourteen he does not
    let dp = { expr: 'neutral', look: .4, lookY: .2, armL: [16, 10], armR: [16, 10], blink: bl(4, A('evine'), A('kokuyu'), A('iki', 2), A('gönüllüler'), A('zor')) };
    if (smell && !later) dp = { ...dp, expr: 'surprised', look: .7, lookY: .5, gazeX: 1, gazeY: 1, brow: 1, mouth: .4, armL: [150, 24], armR: [150, 24] };
    if (later) dp = { ...dp, expr: 'neutral', look: -.3, lookY: -.3, lid: .5, brow: -.1, armL: [30, -100], armR: [30, -96] };
    if (ask) dp = { ...dp, expr: 'focused', look: .6, lookY: .5, gazeX: 1, gazeY: 1, lid: .3, brow: .3, lean: 5, bob: -Math.abs(Math.sin((t - A('gönüllüler')) * 9)) * 7 };
    if (none) dp = { ...dp, expr: 'worried', look: .5, lookY: 0, lid: 0, brow: .8, lean: 0, bob: 0, armL: [58, -72], armR: [58, -72] };
    D.show(); D.place(200 + D1.x, 0, D1.z, cam, tint);
    D.draw({ ...dp, lit: 1, shade: COOL, rim: { color: WARM, a: .42 } }); D.castFrom(LAMP);
    // the calendar: day 1 -> day 14
    if (t > A('iki') - .1) {
      const day = t < A('hafta') ? 1 : Math.min(14, 1 + Math.floor((t - A('hafta')) / (W('koydular.') + .3 - W('hafta')) * 13));
      dyn.cal.userData.set(day); const s = popCard(dyn.cal, A('iki') - .1, t, V(200.04, 2.2, -1.5), 1.25, false); if (s) dyn.cal.rotation.z += Math.sin(t * 2) * .03;
    }
    if (none) popCard(dyn.q[0], A('zor'), t, V(200 + D1.x + .05, 1.45 + .5, D1.z));
    look = { focus: cam.position.distanceTo(V(200, 1.3, -.95)), coc: 4, range: 3.2, sat: 1.2, lift: [.085, .085, .15], bloom: .9, vignette: .22 };
  }
  for (const s of Object.values(smokes)) s.update(t);
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
