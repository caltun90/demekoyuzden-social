// Yasak olan neden daha tatlı gelir? Demek O Yüzden günlük Short (yumurta stili), 27 Kasım 2026.
// Bilgi: bir seçeneğimiz yasaklanınca onu geri kazanma isteği doğar ve yasaklanan şey daha çekici gelir (psikolojik
// tepkisellik, Brehm 1966). Üniversite tuvaletlerinde sert yasak tabelası asılan duvarlara, yumuşak rica tabelası asılanlardan
// daha çok yazı yazıldı (Pennebaker ve Sanders, 1976). Kaynaklar SCRIPT.md'de.
// Tek set: MUTFAK (pencere ışığı, ada tezgâh, fanus altında pasta, kilitli dolap, kapı). Kahraman (sen) ve bigudili anne.
// İskelet v1: kurulum (pasta umurunda değil) -> üç vuruş (dokunma / not / kilit; annenin öfkesi büyür) -> kırılma (ışık yanar,
// anne ağzı açık kalır; tepkisellik + tabela deneyi) -> döngü (son plan ilk planın kadrajı: "Sakın dokunma").
import * as THREE from 'three';
import { stoneTex, woodTex, tileTex, painted, flat } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { beam, glow } from '/engine/src/fx.js';
import { Parcaciklar } from '/engine/src/parcacik.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-27-yasak-cazibesi';
export const FPS = 30;
export let DUR = 48;
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
const CREAM = '#fbf7ee', FONT = '"Arial Black", "Inter", sans-serif';
function label(c, txt, x, y, size, col, sw = .22) { c.font = `900 ${size}px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.lineJoin = 'round'; if (sw) { c.strokeStyle = PLUM; c.lineWidth = size * sw; c.strokeText(txt, x, y); } c.fillStyle = col; c.fillText(txt, x, y); }
function drawNote(c, w, h) {
  c.lineJoin = 'round'; c.fillStyle = '#ffe15a'; c.strokeStyle = PLUM; c.lineWidth = 12; c.beginPath(); c.roundRect(8, 8, w - 16, h - 16, 14); c.fill(); c.stroke();
  c.fillStyle = '#e8c83a'; c.beginPath(); c.moveTo(w - 8, h - 60); c.lineTo(w - 60, h - 8); c.lineTo(w - 8, h - 8); c.closePath(); c.fill(); c.stroke();
  label(c, 'DOKUNMA!', w / 2, h * .5, w * .145, '#e2463f', 0);
}
function drawCakeIcon(c, x, y, s) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = s * .07;
  c.fillStyle = '#f6efe0'; c.beginPath(); c.ellipse(x, y + s * .42, s * .62, s * .1, 0, 0, 6.29); c.fill(); c.stroke();
  c.fillStyle = '#f7a8c4'; c.beginPath(); c.roundRect(x - s * .45, y - s * .12, s * .9, s * .52, s * .06); c.fill(); c.stroke();
  c.fillStyle = '#ffffff'; c.beginPath(); c.moveTo(x - s * .47, y - s * .1);
  for (let i = 0; i < 5; i++) { const x0 = x - s * .47 + i * s * .188; c.quadraticCurveTo(x0 + s * .047, y + s * (.1 + (i % 2) * .08), x0 + s * .094, y - s * .02); c.quadraticCurveTo(x0 + s * .14, y + s * .06, x0 + s * .188, y - s * .1); }
  c.lineTo(x + s * .47, y - s * .22); c.quadraticCurveTo(x, y - s * .34, x - s * .47, y - s * .22); c.closePath(); c.fill(); c.stroke();
  c.fillStyle = '#e2463f'; c.beginPath(); c.arc(x, y - s * .36, s * .11, 0, 6.29); c.fill(); c.stroke();
}
function drawThought(c, w, h) {
  c.lineJoin = 'round'; c.strokeStyle = PLUM; c.lineWidth = 12; c.fillStyle = '#ffffff';
  const blob = () => { c.beginPath(); for (const [x, y, r] of [[.3, .36, .2], [.5, .28, .24], [.7, .36, .2], [.36, .5, .2], [.62, .52, .22]]) { c.moveTo(w * x + w * r, h * y); c.arc(w * x, h * y, w * r, 0, 6.29); } };
  blob(); c.stroke(); blob(); c.fill();
  for (const [x, y, r] of [[.3, .82, .05], [.2, .93, .03]]) { c.beginPath(); c.arc(w * x, h * y, w * r, 0, 6.29); c.fill(); c.stroke(); }
  drawCakeIcon(c, w * .5, h * .4, w * .36);
}
function drawX(c, w, h) { c.lineCap = 'round'; for (const [col, lw] of [[PLUM, .26], ['#e2463f', .15]]) { c.strokeStyle = col; c.lineWidth = w * lw; c.beginPath(); c.moveTo(w * .2, h * .2); c.lineTo(w * .8, h * .8); c.moveTo(w * .8, h * .2); c.lineTo(w * .2, h * .8); c.stroke(); } }
function drawMark(ch, col) { return (c, w, h) => label(c, ch, w / 2, h * .54, h * .84, col, .2); }
function padlock(c, x, y, s) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = s * .3; c.beginPath(); c.arc(x, y - s * .3, s * .3, Math.PI, 0); c.stroke();
  c.strokeStyle = '#c9cfe0'; c.lineWidth = s * .16; c.beginPath(); c.arc(x, y - s * .3, s * .3, Math.PI, 0); c.stroke();
  c.strokeStyle = PLUM; c.lineWidth = s * .08; c.fillStyle = '#e8b23e'; c.beginPath(); c.roundRect(x - s * .5, y - s * .3, s, s * .8, s * .12); c.fill(); c.stroke();
  c.fillStyle = PLUM; c.beginPath(); c.arc(x, y + s * .04, s * .1, 0, 6.29); c.fill(); c.fillRect(x - s * .04, y + s * .04, s * .08, s * .24);
}
function chain(c, x0, x1, y, r) { c.strokeStyle = PLUM; c.lineWidth = r * .9; c.beginPath(); c.moveTo(x0, y); c.lineTo(x1, y); c.stroke(); for (let x = x0, i = 0; x <= x1; x += r * 1.7, i++) { c.fillStyle = i % 2 ? '#aab3cc' : '#d8dcec'; c.lineWidth = r * .28; c.beginPath(); c.ellipse(x, y, r, r * .7, 0, 0, 6.29); c.fill(); c.stroke(); } }
function drawLock(c, w, h) { chain(c, w * .04, w * .96, h * .5, h * .11); padlock(c, w / 2, h * .56, h * .46); }
function drawWave(c, w, h) {
  c.lineCap = c.lineJoin = 'round';
  const path = () => { c.beginPath(); c.moveTo(w * .5, h * .94); c.bezierCurveTo(w * 1.05, h * .78, -w * .05, h * .62, w * .5, h * .48); c.bezierCurveTo(w * 1.05, h * .34, -w * .05, h * .2, w * .5, h * .06); };
  c.strokeStyle = PLUM; c.lineWidth = w * .3; path(); c.stroke(); c.strokeStyle = '#ffd0e4'; c.lineWidth = w * .17; path(); c.stroke();
}
function drawBigudi(c, w, h) {
  c.lineJoin = 'round'; c.strokeStyle = PLUM; c.lineWidth = 9;
  for (const [x, y, col] of [[.2, .62, '#ff8ab8'], [.5, .4, '#8adccc'], [.8, .62, '#ffd23a']]) { c.fillStyle = col; c.beginPath(); c.roundRect(w * x - w * .15, h * y - h * .26, w * .3, h * .52, h * .2); c.fill(); c.stroke();
    c.lineWidth = 5; for (const k of [-.07, 0, .07]) { c.beginPath(); c.moveTo(w * (x + k), h * y - h * .2); c.lineTo(w * (x + k), h * y + h * .2); c.stroke(); } c.lineWidth = 9; }
}
// "the freedom to choose": two buttons; a padlock comes down on one (lock 0..1), and that one catches fire (heat 0..1)
function drawChoice(c, w, h, lock, heat, ph) {
  c.lineJoin = c.lineCap = 'round'; c.fillStyle = CREAM; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 36); c.fill(); c.stroke();
  const y = h * .54, r = h * .27, xl = w * .28, xr = w * .72, pulse = 1 + heat * .1 * Math.sin(ph * 14);
  if (heat > 0) for (let i = 0; i < 9; i++) {      // flames round the forbidden button
    const a = -Math.PI / 2 + (i - 4) * .42, fl = r * (1.25 + .3 * Math.abs(Math.sin(ph * 11 + i * 1.7))) * (.6 + .4 * heat), bx = xl + Math.cos(a) * r * .9, by = y + Math.sin(a) * r * .9, tx = xl + Math.cos(a) * fl * 1.25, ty = y + Math.sin(a) * fl * 1.25 - r * .2;
    c.fillStyle = i % 2 ? '#ff8a2a' : '#ffd23a'; c.strokeStyle = PLUM; c.lineWidth = 7; c.globalAlpha = heat;
    c.beginPath(); c.moveTo(bx - r * .2, by); c.quadraticCurveTo(tx - r * .1, (by + ty) / 2, tx, ty); c.quadraticCurveTo(tx + r * .16, (by + ty) / 2, bx + r * .2, by); c.closePath(); c.fill(); c.stroke(); c.globalAlpha = 1;
  }
  c.lineWidth = 12; c.strokeStyle = PLUM;
  c.fillStyle = '#58b848'; c.beginPath(); c.arc(xl, y, r * pulse, 0, 6.29); c.fill(); c.stroke(); label(c, 'YE', xl, y + 4, r * .8 * pulse, '#ffffff', .18);
  c.fillStyle = '#9aa6c8'; c.beginPath(); c.arc(xr, y, r * .86, 0, 6.29); c.fill(); c.stroke(); label(c, 'YEME', xr, y + 4, r * .5, '#ffffff', .2);
  if (lock > 0) { const k = backOut(Math.min(1, lock)), yy = lerpN(-h * .3, y, k); c.save(); c.globalAlpha = Math.min(1, lock * 3); chain(c, xl - r * 1.25, xl + r * 1.25, yy, r * .16); padlock(c, xl, yy + r * .1, r * .62); c.restore(); }
}
function drawLabel(txt, col) { return (c, w, h) => { c.lineJoin = 'round'; c.fillStyle = col; c.strokeStyle = PLUM; c.lineWidth = 12; c.beginPath(); c.roundRect(8, 8, w - 16, h - 16, 26); c.fill(); c.stroke(); label(c, txt, w / 2, h * .54, h * .5, '#ffffff', .2); }; }
// the experiment: two walls, a polite sign and a harsh one; k = 0..1 fills them with scribbles (few / many)
function drawWalls(c, w, h, k) {
  c.lineJoin = c.lineCap = 'round';
  const cols = ['#e2463f', '#3f8fd8', '#58b848', '#b06ad8', '#ff8a2a', '#2a1a2c'];
  [[w * .03, '#5b8fe0', ['LÜTFEN', 'YAZMAYIN'], 2, 3], [w * .515, '#e2463f', ['KESİNLİKLE', 'YAZMAYIN!'], 14, 11]].forEach(([x0, col, txt, n, seed], side) => {
    const pw = w * .455, y0 = h * .04, ph = h * .92;
    c.fillStyle = '#eef3fb'; c.strokeStyle = PLUM; c.lineWidth = 12; c.beginPath(); c.roundRect(x0, y0, pw, ph, 24); c.fill(); c.stroke();
    c.save(); c.beginPath(); c.roundRect(x0, y0, pw, ph, 24); c.clip(); c.strokeStyle = '#cfd8ee'; c.lineWidth = 4;
    for (let y = y0 + ph * .36; y < y0 + ph; y += ph * .13) { c.beginPath(); c.moveTo(x0, y); c.lineTo(x0 + pw, y); c.stroke(); }
    for (let x = x0 + pw * .2; x < x0 + pw; x += pw * .2) { c.beginPath(); c.moveTo(x, y0 + ph * .36); c.lineTo(x, y0 + ph); c.stroke(); }
    // the scribbles
    const m = Math.round(n * k); let s = seed;
    const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
    for (let i = 0; i < n; i++) {
      const cx = x0 + pw * (.14 + rnd() * .72), cy = y0 + ph * (.44 + rnd() * .48), r = pw * (.05 + rnd() * .04), kind = Math.floor(rnd() * 4), col2 = cols[Math.floor(rnd() * cols.length)];
      if (i >= m) continue;
      c.strokeStyle = col2; c.lineWidth = 7; c.beginPath();
      if (kind === 0) { for (let j = 0; j <= 6; j++) c.lineTo(cx - r + j * r / 3, cy + (j % 2 ? -r : r) * .6); }
      else if (kind === 1) { c.arc(cx, cy, r * .7, 0, 6.29); c.moveTo(cx - r * .25, cy - r * .15); c.lineTo(cx - r * .25, cy - r * .1); c.moveTo(cx + r * .25, cy - r * .15); c.lineTo(cx + r * .25, cy - r * .1); c.moveTo(cx - r * .3, cy + r * .2); c.quadraticCurveTo(cx, cy + r * .5, cx + r * .3, cy + r * .2); }
      else if (kind === 2) { c.moveTo(cx, cy + r * .7); c.bezierCurveTo(cx - r * 1.4, cy - r * .3, cx - r * .3, cy - r, cx, cy - r * .3); c.bezierCurveTo(cx + r * .3, cy - r, cx + r * 1.4, cy - r * .3, cx, cy + r * .7); }
      else { for (let j = 0; j < 5; j++) { const a = j * 4 * Math.PI / 5 - Math.PI / 2; c.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r); } c.closePath(); }
      c.stroke();
    }
    c.restore();
    // the sign
    c.fillStyle = col; c.strokeStyle = PLUM; c.lineWidth = 10; c.beginPath(); c.roundRect(x0 + pw * .07, y0 + ph * .06, pw * .86, ph * .25, 16); c.fill(); c.stroke();
    const fs = pw * (side ? .118 : .13); label(c, txt[0], x0 + pw / 2, y0 + ph * .135, fs, '#ffffff', 0); label(c, txt[1], x0 + pw / 2, y0 + ph * .235, fs, '#ffffff', 0);
  });
}

// ---------------------------------------------------------------- MUTFAK
const CAKE = V(-.1, .96, -.3), HERO = { x: .5, z: -.95 }, ANNE = { x: -.66, z: -.98 };
const CUP = V(2.0, 0, -2.05), HN = { x: 1.3, z: -1.3 }, AC = { x: 1.25, z: -1.35 }, AD = { x: -1.45, z: -1.55 };
const WIN = V(-.2, 2.62, -2.36), DOOR = V(-1.75, 0, -2.36);
function buildMutfak(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 9), painted(tileTex({ a: '#f2ead8', b: '#8fc4c8', rep: [16, 12] })));
  fl.rotation.x = -Math.PI / 2; g.add(fl);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 5), painted(stoneTex({ base: '#aecbe8', seam: '#8fb0d6', bw: 64, bh: 64, rep: [12, 5] })));
  wall.position.set(0, 2.5, -2.4); g.add(wall);
  const dado = new THREE.Mesh(new THREE.BoxGeometry(12, .42, .05), painted(tileTex({ a: '#e8553a', b: '#f2ead8', rep: [28, 1] }))); dado.position.set(0, 1.25, -2.36); g.add(dado);
  for (const y of [1.02, 1.48]) { const m = new THREE.Mesh(new THREE.BoxGeometry(12, .05, .08), flat('#eef3fb')); m.position.set(0, y, -2.35); g.add(m); }
  const top = flat('#f6efe0');
  // the counter along the wall with jars, and the island in front
  const bc = new THREE.Mesh(new THREE.BoxGeometry(2.3, .9, .6), flat('#5b6ab8')); bc.position.set(.2, .45, -2.08); g.add(bc);
  const bt = new THREE.Mesh(new THREE.BoxGeometry(2.4, .06, .68), top); bt.position.set(.2, .93, -2.06); g.add(bt);
  for (const [x, col, hh] of [[-.6, '#e8b23e', .26], [-.3, '#d8483a', .2], [.7, '#f2ead8', .3], [1.0, '#58b848', .24]]) { const j = new THREE.Mesh(new THREE.CylinderGeometry(.09, .09, hh, 14), flat(col)); j.position.set(x, .96 + hh / 2, -2.1); g.add(j);
    const l = new THREE.Mesh(new THREE.CylinderGeometry(.095, .095, .04, 14), flat('#7a5644')); l.position.set(x, .98 + hh, -2.1); g.add(l); }
  const isl = new THREE.Mesh(new THREE.BoxGeometry(2.7, .9, .74), flat('#f0c455')); isl.position.set(.1, .45, -.3); g.add(isl);
  const it = new THREE.Mesh(new THREE.BoxGeometry(2.82, .06, .86), top); it.position.set(.1, .93, -.3); g.add(it);
  for (let i = 0; i < 4; i++) { const d = new THREE.Mesh(new THREE.BoxGeometry(.56, .62, .03), flat('#f6d57a')); d.position.set(-.9 + i * .67, .47, .08); g.add(d);
    const k = new THREE.Mesh(new THREE.BoxGeometry(.05, .14, .03), flat('#7a5644')); k.position.set(-.7 + i * .67, .6, .11); g.add(k); }
  // the window: the light of the set (dyn.pane goes dark at night)
  dyn.pane = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.2), new THREE.MeshBasicMaterial({ color: HDR(1.4, 1.22, .92) })); dyn.pane.position.copy(WIN); g.add(dyn.pane);
  const fr = flat('#f1ece2');
  for (const [w, h, x, y] of [[1.18, .09, 0, .64], [1.18, .12, 0, -.65], [.09, 1.36, -.55, 0], [.09, 1.36, .55, 0], [.05, 1.2, 0, 0], [1.0, .05, 0, .1]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .1), fr); b.position.set(WIN.x + x, WIN.y + y, WIN.z + .06); b.userData.noShadow = true; g.add(b); }
  // the door she stands in
  const door = new THREE.Mesh(new THREE.BoxGeometry(.96, 2.06, .06), flat('#3f9a8a')); door.position.set(DOOR.x, 1.03, DOOR.z + .02); g.add(door);
  for (const [w, h, x, y] of [[1.2, .1, 0, 2.11], [.1, 2.16, -.55, 1.08], [.1, 2.16, .55, 1.08]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, .12), fr); b.position.set(DOOR.x + x, y, DOOR.z + .05); b.userData.noShadow = true; g.add(b); }
  for (const y of [.62, 1.5]) { const p = new THREE.Mesh(new THREE.BoxGeometry(.62, .62, .03), flat('#58b8a6')); p.position.set(DOOR.x, y, DOOR.z + .065); p.userData.noShadow = true; g.add(p); }
  const knob = new THREE.Mesh(new THREE.SphereGeometry(.05, 12, 10), flat('#f0c455')); knob.position.set(DOOR.x + .36, 1.05, DOOR.z + .1); g.add(knob);
  // the cupboard the cake gets locked in
  const cb = new THREE.Mesh(new THREE.BoxGeometry(1.0, 2.0, .6), painted(woodTex({ base: '#b9824a', rep: [1, 2], vertical: true }))); cb.position.set(CUP.x, 1.0, CUP.z); g.add(cb);
  for (const s of [-1, 1]) { const d = new THREE.Mesh(new THREE.BoxGeometry(.44, 1.7, .04), flat('#e0a860')); d.position.set(CUP.x + s * .235, 1.05, CUP.z + .31); g.add(d);
    const pn = new THREE.Mesh(new THREE.BoxGeometry(.3, .62, .02), flat('#eebf82')); pn.position.set(CUP.x + s * .235, 1.42, CUP.z + .335); pn.userData.noShadow = true; g.add(pn);
    const pn2 = new THREE.Mesh(new THREE.BoxGeometry(.3, .62, .02), flat('#eebf82')); pn2.position.set(CUP.x + s * .235, .66, CUP.z + .335); pn2.userData.noShadow = true; g.add(pn2);
    const kb = new THREE.Mesh(new THREE.SphereGeometry(.035, 10, 8), flat('#2a2f52')); kb.position.set(CUP.x + s * .06, 1.05, CUP.z + .35); g.add(kb); }
  const crown = new THREE.Mesh(new THREE.BoxGeometry(1.1, .08, .68), flat('#8a5a34')); crown.position.set(CUP.x, 2.04, CUP.z); g.add(crown);
  // the cake on its plate, under a glass dome
  const cg = new THREE.Group(); cg.position.copy(CAKE); g.add(cg); dyn.cake = cg;
  const pl = new THREE.Mesh(new THREE.CylinderGeometry(.25, .18, .03, 30), flat('#fbf7ee')); pl.position.y = .015; cg.add(pl);
  const cbody = new THREE.Mesh(new THREE.CylinderGeometry(.17, .17, .14, 30), flat('#f7a8c4', { emissive: '#f7a8c4', emissiveIntensity: .5 })); cbody.position.y = .1; cg.add(cbody);
  const cream = new THREE.Mesh(new THREE.CylinderGeometry(.18, .18, .03, 30), flat('#ffffff', { emissive: '#ffffff', emissiveIntensity: .45 })); cream.position.y = .185; cg.add(cream);
  for (let k = 0; k < 8; k++) { const a = k / 8 * 6.283, b = new THREE.Mesh(new THREE.SphereGeometry(.03, 10, 8), flat('#ffffff', { emissive: '#ffffff', emissiveIntensity: .45 })); b.position.set(Math.cos(a) * .13, .21, Math.sin(a) * .13); b.userData.noShadow = true; cg.add(b); }
  const cherry = new THREE.Mesh(new THREE.SphereGeometry(.04, 12, 10), flat('#e2463f', { emissive: '#e2463f', emissiveIntensity: .5 })); cherry.position.y = .235; cg.add(cherry);
  const dg = new THREE.Group(); dg.position.copy(CAKE); g.add(dg); dyn.dome = dg;
  const glass = new THREE.Mesh(new THREE.SphereGeometry(.26, 28, 14, 0, 6.283, 0, Math.PI / 2), new THREE.MeshLambertMaterial({ color: '#dff0ff', transparent: true, opacity: .32, depthWrite: false })); glass.scale.y = 1.25; glass.position.y = .02; glass.userData.noShadow = true; dg.add(glass);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(.26, .012, 8, 36), flat('#c9d6ee')); rim.rotation.x = Math.PI / 2; rim.position.y = .03; rim.userData.noShadow = true; dg.add(rim);
  const dk = new THREE.Mesh(new THREE.SphereGeometry(.035, 12, 10), flat('#c9d6ee')); dk.position.y = .36; dk.userData.noShadow = true; dg.add(dk);
  const L = new THREE.Group();
  dyn.hemi = new THREE.HemisphereLight('#b9c6ff', '#8a7a9a', 1.5); L.add(dyn.hemi);
  const KEYP = V(-1.6, 3.0, -1.2); dyn.keyP = KEYP;
  const key = new THREE.SpotLight('#ffd9a0', 12, 13, 1.0, .6, 1.3); key.position.copy(KEYP); key.target.position.set(.6, .8, -.6); dyn.key = key;
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  dyn.fill = new THREE.DirectionalLight('#b9c8ff', .7); dyn.fill.position.set(2, 3, 6); dyn.fill.target.position.set(0, 1, -1); L.add(dyn.fill); L.add(dyn.fill.target);
  scene.add(L);
  shadows(g);
  dyn.beam = beam(scene, [WIN.x, WIN.y, WIN.z + .1], [.6, .6, .2], { r0: .5, r1: 1.5, color: '#ffe2a8', strength: .1 });
  dyn.glow = glow(scene, [WIN.x, WIN.y, WIN.z + .15], '#ffd28a', 1.5, .1);
}

// ---------------------------------------------------------------- CAST
export const LOOK = {
  kahraman: { hair: '#3a2a24', cloth: '#e8553a', collar: true, height: 1.7 },
  anne: { hair: '#8a3a2a', cloth: '#b06ad8', apron: true, collar: false, bodyW: 236, headW: 288, headH: 260, height: 1.74 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hook: { pos: [-.08, 1.5, 3.3], look: [-.08, 1.3, -.6], fov: 46 },
  cake: { pos: [0, 1.3, 1.25], look: [0, 1.1, -.3], fov: 40 },
  face: { pos: [.5, 1.52, .95], look: [.55, 1.5, -.95], fov: 40 },
  wide: { pos: [.2, 1.6, 4.2], look: [.2, 1.3, -1], fov: 50 },
  heroM: { pos: [.4, 1.5, 2.6], look: [.42, 1.4, -.9], fov: 46 },
  anne: { pos: [-.5, 1.52, 1.5], look: [-.72, 1.48, -.98], fov: 42 },
  two: { pos: [-.08, 1.52, 3.5], look: [-.08, 1.32, -.6], fov: 46 },
  two2: { pos: [-.08, 1.48, 3.05], look: [-.08, 1.3, -.6], fov: 46 },
  sniff: { pos: [.05, 1.5, 2.1], look: [.05, 1.38, -.6], fov: 44 },
  cup: { pos: [1.76, 1.5, 2.9], look: [1.8, 1.3, -1.6], fov: 46 },
  night: { pos: [1.52, 1.45, 2.5], look: [1.66, 1.32, -1.6], fov: 44 },
  door: { pos: [-1.2, 1.52, 1.0], look: [-1.45, 1.5, -1.55], fov: 42 },
  mech: { pos: [.45, 1.78, 2.75], look: [.45, 1.75, -.95], fov: 50 },
  mech2: { pos: [.45, 1.8, 2.65], look: [.45, 1.78, -.95], fov: 50 },
};
function cameraPath() {
  const t = W, endT = dyn.endT;
  const loopFov = 46 / Math.pow(1 - .1 / 100, Math.max(0, (endT - (t('sakın', 2) - .12)) * FPS));
  const keys = [
    // hook: the forbidden cake between them -> the cake -> his face
    { t: 0, ...SHOT.hook, creep: .4, drift: .03 },
    { t: t('neden') + .1, dur: .2, move: 'whip', ...SHOT.cake, creep: .34, drift: .02 },
    { t: t('tatlı') + .1, dur: .2, move: 'whip', ...SHOT.face, creep: .34, drift: .02 },
    { t: t('Bakın') + .16, dur: .3, move: 'whip', ...SHOT.wide, creep: .22, drift: .03 },
    { t: t('hiç') + .1, dur: .6, ...SHOT.heroM, creep: .2, drift: .02 },
    { t: t('Sonra') + .12, dur: .28, move: 'whip', ...SHOT.anne, creep: .3, drift: .02 },
    // three times, each bigger
    { t: t('bir', 2) + .1, dur: .28, move: 'whip', ...SHOT.two, creep: .2, drift: .02 },
    { t: t('annen', 2) + .1, dur: .5, ...SHOT.two2, creep: .2, drift: .015 },
    { t: t('sen') - .02, dur: .28, move: 'whip', ...SHOT.sniff, creep: .2, drift: .02 },
    { t: t('annen', 3) + .1, dur: .28, move: 'whip', ...SHOT.cup, creep: .2, drift: .02 },
    { t: t('gece') - .04, move: 'cut', ...SHOT.night, creep: .22, drift: .015 },
    // the turn: the light, mother in the door, the reason
    { t: t('annen', 4) + .08, dur: .26, move: 'whip', ...SHOT.door, creep: .34, drift: .02 },
    { t: t('Çünkü') + .12, dur: .28, move: 'whip', ...SHOT.mech, creep: .012, drift: .003 },
    { t: t('bir', 3) + .1, dur: .5, ...SHOT.mech2, creep: .012, drift: .003 },
    // "all right, eat it" -> an ordinary cake; and round again (the first frame)
    { t: t('annen', 5) + .1, dur: .28, move: 'whip', ...SHOT.two, creep: .16, drift: .02 },
    { t: t('sakın', 2) - .12, dur: .26, move: 'whip', ...SHOT.hook, fov: loopFov, creep: .1, drift: 0 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('dokunma') + .05, .45); cp.kick(t('not') + .08, .4); cp.kick(t('kilitliyor') + .1, .6); cp.kick(t('yanıyor') + .02, .8); cp.kick(t('özgürlüğün') + .05, .5); cp.kick(t('tutuşuyorsun') + .05, .45); cp.kick(t('dokunma', 2) + .05, .5);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  dyn.endT = ctx.words[ctx.words.length - 1].end + .45;
  DUR = Math.ceil(dyn.endT * FPS) / FPS;                    // no dead frames after the last word (loop)
  const { scene } = ctx;
  scene.background = new THREE.Color('#33407a');
  buildMutfak(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.note = card(scene, .3, .21, drawNote, { pw: 384 });
  dyn.lock = card(scene, .9, .4, drawLock, { pw: 512 });
  dyn.thought = card(scene, .74, .7, drawThought, { pw: 448 });
  dyn.cakeIcon = card(scene, .5, .5, (c, w, h) => drawCakeIcon(c, w / 2, h * .55, w * .72), { pw: 320 });
  dyn.x = card(scene, .42, .42, drawX, { pw: 256 });
  dyn.q = card(scene, .3, .36, drawMark('?', '#ffe15a'), { pw: 256 });
  dyn.bang = [0, 1].map(() => card(scene, .3, .4, drawMark('!', '#ff5a4a'), { pw: 256 }));
  dyn.waves = [0, 1, 2].map(() => card(scene, .13, .36, drawWave, { pw: 96 }));
  dyn.bigudi = card(scene, .5, .2, drawBigudi, { pw: 320 });
  dyn.choice = dynCard(scene, 1.4, .86, drawChoice, { pw: 768, steps: 30 });
  dyn.tepki = card(scene, 1.3, .3, drawLabel('TEPKİSELLİK', '#b06ad8'), { pw: 768 });
  dyn.walls = dynCard(scene, 1.5, 1.05, drawWalls, { pw: 900, steps: 28 });
  PF = new Parcaciklar(scene);
  PF.ekle('parilti', { t: W('pastada') - .05, pos: [CAKE.x, CAKE.y + .22, CAKE.z + .05], sure: 1.6, olcek: .8 });
  PF.ekle('duman', { t: W('kilitliyor') - .25, pos: [AC.x, 1.86, AC.z], sure: 1.4, olcek: .7 });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('neden') + .02, 'rise', { dur: .3 }); cue(W('tatlı') + .02, 'rise', { dur: .3 }); cue(W('tatlı') + .12, 'shimmer');
  cue(W('Bakın') + .02, 'whoosh'); cue(W('pasta'), 'lock'); cue(W('umurunda'), 'lock');
  cue(W('Sonra') + .02, 'whoosh'); cue(W('sakın'), 'lock'); cue(W('dokunma') + .05, 'boom');
  cue(W('bir', 2) + .02, 'whoosh'); cue(W('aklın'), 'rise', { dur: .4 }); cue(W('pastada'), 'shimmer');
  cue(W('annen', 2) + .02, 'whoosh'); cue(W('not') + .08, 'boom'); cue(W('sen') - .1, 'rise', { dur: .3 }); cue(W('kapağı') + .05, 'lock'); cue(W('kokluyorsun'), 'wind', { dur: .7 });
  cue(W('annen', 3) + .02, 'whoosh'); cue(W('dolaba'), 'lock'); cue(W('kilitliyor') + .1, 'boom'); cue(W('kilitliyor') - .2, 'simmer', { dur: 1.2 });
  cue(W('gece') - .04, 'cut'); cue(W('gece') + .1, 'wind', { dur: W('ışık') - W('gece') - .2 }); cue(W('tornavidayla'), 'lock'); cue(W('başındasın'), 'lock');
  cue(W('yanıyor') + .02, 'boom'); cue(W('annen', 4) + .02, 'rise', { dur: .3 }); cue(W('açık'), 'cut');
  cue(W('Çünkü') + .02, 'whoosh'); cue(W('pasta', 2), 'lock'); cue(W('değil', 2) + .02, 'cut'); cue(W('elinden'), 'rise', { dur: .35 }); cue(W('özgürlüğün') + .05, 'boom');
  cue(W('tepkisellik'), 'shimmer'); cue(W('yapamazsın'), 'lock'); cue(W('geri'), 'rise', { dur: .5 }); cue(W('yanıp'), 'simmer', { dur: W('tutuşuyorsun') + .6 - W('yanıp') }); cue(W('tutuşuyorsun') + .05, 'boom');
  cue(W('bir', 3) + .05, 'whoosh'); cue(W('lütfen'), 'lock'); cue(W('kesinlikle'), 'boom');
  cue(W('sonuç'), 'rise', { dur: .4 }); for (let k = 0; k < 7; k++) cue(W('en') + k * (W('yazıldı') - W('en')) / 7, 'lock'); cue(W('yazıldı') + .1, 'shimmer');
  cue(W('annen', 5) + .02, 'whoosh'); cue(W('ye') + .05, 'lock'); cue(W('sıradan'), 'cut');
  cue(W('ta'), 'rise', { dur: .5 }); cue(W('sakın', 2) - .15, 'whoosh'); cue(W('dokunma', 2) + .05, 'boom'); cue(W('dokunma', 2) + .2, 'shimmer');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'YASAK NEDEN TATLI GELİR?'); }

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
  for (const m of dyn.cards) { m.visible = false; m.quaternion.copy(cam.quaternion); m.material.color.setRGB(1, 1, 1); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const RT = V(1, 0, 0).applyQuaternion(cam.quaternion);
  const H = cast.kahraman, AN = cast.anne;
  // ---- the beats
  const tL2 = A('Bakın'), tL3 = A('Sonra'), tB1 = A('bir', 2), tB2 = A('annen', 2), tB3 = A('annen', 3), tNight = W('gece') - .04, tLight = W('yanıyor') + .02;
  const tDoor = W('annen', 4) - .05, tMech = A('Çünkü') - .02, tEnd = W('annen', 5) - .04, tLoop = W('sakın', 2) - .25;
  const hook = t < tL2, L2 = t >= tL2 && t < tL3, L3 = t >= tL3 && t < tB1, B1 = t >= tB1 && t < tB2, B2 = t >= tB2 && t < tB3, B3 = t >= tB3 && t < tNight;
  const night = t >= tNight && t < tMech, dark = night && t < tLight, mech = t >= tMech && t < tEnd, L12 = t >= tEnd && t < tLoop, loop = t >= tLoop;
  const forbidden = hook || loop;
  // ---- day / night
  const nk = dark ? 1 : 0, dim = [lerpN(1, .42, nk), lerpN(1, .48, nk), lerpN(1, .8, nk)];
  dyn.hemi.intensity = lerpN(1.5, .4, nk); dyn.key.intensity = lerpN(12, .8, nk); dyn.fill.intensity = lerpN(.7, .25, nk);
  dyn.pane.material.color.copy(dark ? HDR(.2, .3, .75) : night ? HDR(.16, .22, .5) : HDR(1.4, 1.22, .92)); dyn.beam.visible = dyn.glow.visible = !night;
  const grade = dark ? [.8, .88, 1.12] : [1.01, 1.0, 1.01], face = [1, .985, .97], tint = face.map((v, i) => v / grade[i] * dim[i]);
  const lit = { lit: -1, shade: COOL, rim: { color: WARM, a: dark ? .1 : .4 } };
  for (const m of dyn.cards) if (dark) m.material.color.setRGB(...dim);
  // ---- the cake: on the island under its dome, or locked away
  const away = t >= W('dolaba') - .1 && t < tEnd;
  dyn.cake.visible = !away; dyn.dome.visible = !away && !L12;
  const lift = B2 ? ramp(t, A('kapağı'), A('kapağı') + .3) : 0, drop = loop ? 1 - backOut((t - tLoop) / .25) : 0;
  dyn.dome.position.set(CAKE.x - lift * .3, CAKE.y + lift * .38 + drop * .5, CAKE.z); dyn.dome.rotation.z = lift * .35;
  const NOTE = V(CAKE.x + .2, CAKE.y + .13, CAKE.z + .32);
  if (hook) { popCard(dyn.note, -1, t, NOTE, 1, false); dyn.note.rotation.z = -.06 + Math.sin(t * 3) * .01; }
  if ((B2 || B3) && t > A('not') + .06 && !away) { popCard(dyn.note, A('not') + .06, t, NOTE.clone().add(V(-lift * .36, lift * .36, 0))); dyn.note.rotation.z += -.06 + lift * .35; }
  if (loop && t > W('dokunma', 2) - .1) { popCard(dyn.note, W('dokunma', 2) - .1, t, NOTE); dyn.note.rotation.z += -.06; }
  let focus = V(HERO.x, 1.45, HERO.z);
  // ---- the hero
  {
    let hx = HERO.x, hz = HERO.z;
    let hp = { expr: 'neutral', look: 0, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(1, A('neden'), A('umurunda'), A('sakın'), A('aklın'), A('kapağı'), A('dolaba'), A('yanıyor'), A('pasta', 2), A('elinden'), A('tepkisellik'), A('yanıp'), A('iki'), A('sert'), A('ye'), A('sıradan'), A('dokunma', 2)) };
    const want = { ...hp, expr: 'grin', look: -.75, lookY: -.3, gazeX: -1, gazeY: -.6, brow: 1, lean: -7, armL: [96, 22], armR: [40, -64] };
    if (hook) hp = t > A('tatlı') ? { ...want, look: -.25, lean: 0, armL: [58, -72], armR: [58, -72] } : want;
    if (L2) hp = t < A('hiç') ? { ...hp, expr: 'smile', look: .5, lid: .3, armR: [34, -92] } : { ...hp, expr: 'smug', look: .6, lookY: .2, lid: .5, armL: [58, -72], armR: [58, -72] };
    if (L3) hp = t < A('sakın') ? { ...hp, expr: 'neutral', look: -.7, brow: .3 } : { ...hp, expr: 'surprised', look: -.8, brow: 1, mouth: .3, lean: 3 };
    if (B1) { const k = ramp(t, A('aklın'), A('aklın') + .3); hp = { ...hp, expr: k > .5 ? 'grin' : 'surprised', look: -.8, lookY: -.3 * k, gazeX: -1, gazeY: -.6, brow: 1, lean: -6 * k, armL: [16 + 60 * k, 10 + 10 * k], mouth: .2 }; }
    if (B2) { const sn = t > A('kokluyorsun') ? Math.abs(Math.sin((t - A('kokluyorsun')) * 9)) : 0, go = ramp(t, A('sen'), A('sen') + .3);
      hp = t < A('sen') ? { ...hp, expr: 'worried', look: -.8, brow: .8 } : { ...hp, expr: t > A('kokluyorsun') ? 'smile' : 'grin', lid: t > A('kokluyorsun') ? .6 : 0, look: -.8, lookY: -.45, gazeX: -1, gazeY: -1, brow: .8, lean: -8 * go, bob: -sn * 8, armL: [100, 30], armR: [34, -92] }; }
    if (B3) hp = { ...hp, expr: t > A('kilitliyor') ? 'surprised' : 'worried', look: .85, gazeX: 1, brow: 1, mouth: t > A('kilitliyor') ? .4 : 0, sweat: t > A('kilitliyor') ? 1 : 0, armL: [58, -72], armR: [58, -72] };
    if (night) {
      hx = HN.x; hz = HN.z;
      const tip = Math.abs(Math.sin(t * 5.5)) * 3, caught = t >= tLight;
      hp = caught ? { ...hp, expr: 'surprised', look: t > tDoor ? -.85 : -.2, gazeX: -1, brow: 1, mouth: .5, sweat: 1, armL: [150, 24], armR: [150, 24], propR: 'pen', bob: Math.sin(t * 40) * 2 * Math.exp(-(t - tLight) * 3) }
        : { ...hp, expr: 'focused', look: .85, lookY: -.15, gazeX: 1, brow: .3, lid: .3, lean: 6, sweat: t > A('tornavidayla') ? .8 : 0, armL: [40, -64], armR: [92, 18 + 6 * Math.sin(t * 9)], propR: 'pen', bob: -tip };
    }
    if (mech) {
      hx = HERO.x - .05;
      const noCake = t > A('değil', 2) && t < A('elinden'), locked = t > A('elinden') + .25, hot = t > A('yapamazsın'), walls = t > W('bir', 3) + .1, res = t > A('sert');
      hp = { ...hp, expr: 'surprised', mouth: .12, look: -.1, lookY: .55, gazeY: 1, brow: .6 };
      if (t < A('pasta', 2)) hp = { ...hp, lookY: .1, gazeY: 0, expr: 'worried', brow: .8 };
      if (noCake) hp = { ...hp, expr: 'worried', brow: .9, armL: [58, -72], armR: [58, -72] };
      if (locked && !walls) hp = { ...hp, expr: hot ? 'angry' : 'worried', brow: hot ? -.4 : .8, mouth: hot ? .3 : .1, armL: hot ? [150, 24 + 8 * Math.sin(t * 16)] : [16, 10], armR: hot ? [150, 24 - 8 * Math.sin(t * 16)] : [16, 10], bob: hot ? Math.sin(t * 30) * 3 : 0 };
      if (walls) hp = res ? { ...hp, expr: 'laugh', laughMarks: .8, mouth: .5 + .5 * Math.abs(Math.sin(t * 12)), bob: -Math.abs(Math.sin(t * 12)) * 7, armR: [148, -128] } : { ...hp, expr: t > A('kesinlikle') ? 'grin' : 'surprised', brow: .9 };
    }
    if (L12) { const meh = t > A('pasta', 3); hp = meh ? { ...hp, expr: 'neutral', look: -.7, lookY: -.3, gazeX: -1, gazeY: -.6, lid: .55, brow: -.1, ...(t > A('sıradan') ? { armL: [58, -72], armR: [58, -72], look: -.2, lookY: 0 } : {}) } : { ...hp, expr: 'surprised', look: -.8, brow: 1, mouth: .3 }; }
    if (loop) hp = t < W('sakın', 2) - .02 ? { ...hp, expr: 'neutral', look: -.6, lid: .5 } : want;
    H.show(); H.place(hx, 0, hz, cam, tint); H.draw({ ...hp, ...lit }); H.castFrom(dyn.keyP);
    const head = V(hx, 1.49, hz);
    focus = V(hx, 1.45, hz);
    // beat 1: the cake moves into his head
    if (B1 && t > A('aklın')) { const s = popCard(dyn.thought, A('aklın'), t, head.clone().add(V(-.1, .68, 0)), 1); if (s) dyn.thought.position.y += Math.sin(t * 3) * .012; }
    // beat 2: the smell
    if (B2 && lift > .5) dyn.waves.forEach((m, i) => { const u = (t * .7 + i / 3) % 1; m.visible = true; m.position.set(CAKE.x + (i - 1) * .13, CAKE.y + .3 + u * .45, CAKE.z + .05); m.material.opacity = Math.sin(Math.PI * u); m.scale.setScalar(.75 + u * .6); });
    if (night && t >= tLight) popCard(dyn.bang[0], tLight, t, head.clone().add(V(.02, .55, 0)));
    if (night) focus = t > tDoor ? V(AD.x, 1.5, AD.z) : V(hx + .3, 1.3, hz);
    // the turn: not the cake, the freedom to choose
    if (mech) {
      const C = V(HERO.x - .05, 2.45, HERO.z), walls = t > W('bir', 3) + .1;
      if (t > A('pasta', 2) - .05 && t < A('elinden')) { popCard(dyn.cakeIcon, A('pasta', 2) - .05, t, C.clone().add(V(0, -.05, 0)), 1.5); if (t > A('değil', 2)) popCard(dyn.x, A('değil', 2), t, C.clone().add(V(0, -.05, .02)), 1.9); }
      if (t >= A('elinden') && !walls) {
        const lock = (t - (A('alınan') - .05)) / .3, heat = ramp(t, A('yapamazsın'), A('yanıp') + .3);
        dyn.choice.userData.set(Math.max(0, Math.min(1, lock)), heat, t);
        const s = popCard(dyn.choice, A('elinden'), t, C, 1.1, false); if (s) dyn.choice.rotation.z += Math.sin(t * 1.7) * .012 + heat * Math.sin(t * 38) * .006;
        if (t > A('tepkisellik') - .05) popCard(dyn.tepki, A('tepkisellik') - .05, t, C.clone().add(V(0, .72, .02)), 1.1, false);
      }
      if (walls) { dyn.walls.userData.set(ramp(t, A('en'), A('yazıldı') + .2)); const s = popCard(dyn.walls, W('bir', 3) + .1, t, C.clone().add(V(0, .08, 0)), 1.08, false); if (s) dyn.walls.rotation.z += Math.sin(t * 1.7) * .01; }
      focus = V(HERO.x, 1.7, HERO.z);
    }
  }
  // ---- mother: sterner each time; in the door she can only stare
  if (!L2 && !(night && t < tDoor - .15) && !mech && !(B2 && t > W('sen') - .16)) {
    let ax = ANNE.x, az = ANNE.z;
    let ap = { expr: 'neutral', look: .6, armL: [16, 10], armR: [16, 10], propR: 'spoon', blink: bl(2, A('neden'), A('sakın'), A('aklın'), A('not'), A('kilitliyor'), A('açık'), A('tamam'), A('sıradan'), A('dokunma', 2)) };
    const stern = { ...ap, expr: 'angry', look: .7, brow: -.5, armR: [138, 16 + 10 * Math.sin(t * 14)], armL: [58, -72] };
    if (hook) ap = stern;
    if (L3) { const k = backOut((t - tL3) / .3); ax = ANNE.x - (1 - k) * 1.2; const talk = t > A('sakın') - .04 && t < W('misafire') + .55;
      ap = t < A('söylüyor') ? { ...ap, expr: 'smile', look: .6 } : { ...ap, expr: 'focused', look: .7, brow: -.2, mouth: talk ? flap(env, t) : 0, armR: [128, 18 + 12 * Math.sin(t * 13)], armL: [58, -72] }; }
    if (B1) ap = { ...ap, expr: 'focused', look: .75, lid: .45, brow: -.2, armL: [58, -72], armR: [58, -72] };                       // 1: a narrow look
    if (B2) { const slap = t > A('not') && t < A('not') + .3; ap = { ...ap, expr: 'angry', look: .7, lookY: slap ? -.3 : 0, brow: -.5, lean: slap ? 6 : 0, armL: slap ? [96, 30] : [58, -72], armR: [138, 16 + 12 * Math.sin(t * 16)], bob: t > A('sen') ? Math.sin(t * 26) * 3 : 0, sweat: t > A('kapağı') ? 1 : 0, mouth: t > A('kapağı') ? .5 : 0 }; }   // 2: the note, the shaking spoon
    if (B3) { ax = AC.x; az = AC.z; const fume = t > A('kilitliyor') - .25; ap = { ...ap, expr: 'angry', look: fume ? -.6 : .8, brow: -.6, mouth: fume ? .45 : 0, tilt: fume ? Math.sin(t * 30) * 3 : 0, bob: fume ? Math.sin(t * 34) * 3 : 0, armL: fume ? [150, 24] : [96, 26], armR: [146, 14 + 14 * Math.sin(t * 18)] }; }   // 3: the padlock, smoke out of her head
    if (night) { ax = AD.x; az = AD.z; ap = { ...ap, expr: 'surprised', look: .8, gazeX: 1, brow: 1, mouth: .85, armL: [16, 10], armR: [16, 10], propR: undefined, blink: 0 }; }                 // the turn: silent, mouth open
    if (L12) { const talk = t > A('tamam') - .04 && t < W('ye') + .4; ap = { ...ap, expr: 'smile', look: .7, lid: .2, brow: .3, mouth: talk ? flap(env, t) : 0, armL: [58, -72], armR: [58, -72], propR: undefined }; }
    if (loop) { const talk = t > W('sakın', 2) - .04 && t < W('dokunma', 2) + .5; ap = t < W('sakın', 2) - .06 ? { ...ap, expr: 'smile', look: .7, lid: .2, propR: undefined } : { ...stern, mouth: talk ? flap(env, t) * .8 : 0 }; }
    AN.show(); AN.place(ax, 0, az, cam, tint); AN.draw({ ...ap, ...lit }); AN.castFrom(dyn.keyP);
    dyn.bigudi.visible = true; dyn.bigudi.material.opacity = 1; dyn.bigudi.scale.setScalar(1); dyn.bigudi.position.set(ax, 1.775 + (ap.bob || 0) * -.0019, az + .012); dyn.bigudi.rotation.z = -(ap.tilt || 0) * Math.PI / 180;
    if (L3 && t > A('dokunma')) popCard(dyn.bang[0], A('dokunma'), t, V(ax + .42, 2.02, az));
    if (L3 || (B2 && t < A('sen')) || (night && t > tDoor) || (L12 && t < A('pasta', 3))) focus = V(ax, 1.5, az);
    if (B3) { focus = V(CUP.x - .3, 1.3, CUP.z + .3); }
    if (night && t > A('açık')) popCard(dyn.q, A('açık'), t, V(ax + .27, 1.98, az));
  }
  // the padlock on the cupboard
  if (t > A('kilitliyor') + .08 && t < tMech) popCard(dyn.lock, A('kilitliyor') + .08, t, V(CUP.x, 1.08, CUP.z + .4), 1, t < tNight);
  if (hook && t > W('neden') + .05 && t < W('tatlı') + .05) focus = CAKE.clone().setY(1.15);
  const look = { focus: cam.position.distanceTo(focus), coc: 5, range: 2.6, sat: 1.24, lift: [.085, .085, .15], bloom: .85, vignette: dark ? .4 : .22 };
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
