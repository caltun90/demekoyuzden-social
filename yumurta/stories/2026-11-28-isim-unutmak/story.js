// Yeni tanıştığın kişinin adını neden hemen unutursun? Demek O Yüzden günlük Short (yumurta stili), 28 Kasım 2026.
// Bilgi: "Baker/baker" (fırıncı) paradoksu. Yabancı yüzlerle eşlenen aynı kelime meslek olarak verilince, soyadı olarak
// verildiğinden daha iyi hatırlanır (McWeeny, Young, Hay ve Ellis 1987). Açıklama: meslek kelimesi bir sürü bilgiye
// bağlanır (ekmek, un, fırın); isim ise keyfi bir etikettir, tutunacak bağı azdır (Cohen 1990). Kaynaklar SCRIPT.md'de.
// Tek set: DÜĞÜN SALONU (ampul dizisi, pasta, balonlar). Kahraman (sen), teyze, üç davetli (Selim, ikinci adam, fırıncı).
// İskelet v1: kurulum (teyze tanıştırıyor) -> üç vuruş (Selim uçtu, iki kere söylenen ad uçtu, "fırıncıyım" kaldı; teyzenin
// tepkisi büyür, üçüncüde şaşırıp susar) -> kırılma (fırıncı kelimesi tutunur, isim tutunmaz; çivisiz tablo; deney) ->
// döngü (fırıncı senin adını sorar; son plan ilk planın kadrajı).
import * as THREE from 'three';
import { stoneTex, woodTex, tileTex, carpetTex, painted, flat } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { glow } from '/engine/src/fx.js';
import { Parcaciklar } from '/engine/src/parcacik.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-28-isim-unutmak';
export const FPS = 30;
export let DUR = 47.3;
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
const CREAM = '#fbf7ee', RED = '#e2463f', YEL = '#f2c23a';
const FONT = '"Arial Black", "Segoe UI Black", "Inter", sans-serif';
// a name tag ("BEN ...") : red for a name, yellow for the word that sticks
function tagAt(c, x, y, tw, th, text, col, ta = 1) {
  c.save(); c.translate(x, y); c.lineJoin = c.lineCap = 'round';
  c.fillStyle = col; c.strokeStyle = PLUM; c.lineWidth = th * .07; c.beginPath(); c.roundRect(-tw / 2, -th / 2, tw, th, th * .16); c.fill(); c.stroke();
  c.fillStyle = '#ffffff'; c.beginPath(); c.roundRect(-tw * .43, -th * .14, tw * .86, th * .52, th * .08); c.fill();
  c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = col === YEL ? PLUM : '#ffffff'; c.font = `900 ${th * .2}px ${FONT}`; c.fillText('BEN', 0, -th * .3);
  if (text && ta > 0) { c.globalAlpha = ta; c.fillStyle = PLUM; let fs = th * .34; c.font = `900 ${fs}px ${FONT}`; const m = c.measureText(text).width; if (m > tw * .78) { fs *= tw * .78 / m; c.font = `900 ${fs}px ${FONT}`; } c.fillText(text, 0, th * .13); }
  c.restore();
}
function drawTag(text, col) { return (c, w, h) => tagAt(c, w / 2, h / 2, w * .92, h * .9, text, col); }
function drawMark(ch, col) {
  return (c, w, h) => { c.lineJoin = 'round'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .84}px ${FONT}`;
    c.strokeStyle = PLUM; c.lineWidth = 36; c.strokeText(ch, w / 2, h * .54); c.fillStyle = col; c.fillText(ch, w / 2, h * .54); };
}
// teyze's hairdo: a big curly bun that sits on her head
function drawBun(c, w, h) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = w * .035; c.fillStyle = '#b04a9a';
  const blob = () => { c.beginPath(); for (let k = 0; k <= 9; k++) { const a = Math.PI + k / 9 * Math.PI, x = w * .5 + Math.cos(a) * w * .43, y = h * .82 + Math.sin(a) * h * .5; c.arc(x, y, w * .1, 0, 6.29); } c.arc(w * .5, h * .3, w * .2, 0, 6.29); c.rect(w * .1, h * .5, w * .8, h * .36); };
  blob(); c.stroke(); blob(); c.fill();
  c.strokeStyle = '#d87ac0'; c.lineWidth = w * .022; for (const [x, y, r] of [[.3, .55, .08], [.52, .32, .09], [.7, .58, .08], [.5, .68, .07]]) { c.beginPath(); c.arc(w * x, h * y, w * r, .4, 3.6); c.stroke(); }
  c.fillStyle = '#ffe15a'; c.strokeStyle = PLUM; c.lineWidth = w * .02; c.beginPath(); c.arc(w * .76, h * .36, w * .05, 0, 6.29); c.fill(); c.stroke();
}
function breadAt(c, x, y, r) {
  c.lineJoin = c.lineCap = 'round'; c.fillStyle = '#e8a858'; c.strokeStyle = PLUM; c.lineWidth = r * .14; c.beginPath(); c.ellipse(x, y, r, r * .58, -.12, 0, 6.29); c.fill(); c.stroke();
  c.strokeStyle = '#b06a2a'; c.lineWidth = r * .1; for (const d of [-.45, 0, .45]) { c.beginPath(); c.moveTo(x + d * r - r * .12, y - r * .28); c.lineTo(x + d * r + r * .12, y + r * .2); c.stroke(); }
}
function sackAt(c, x, y, r) {
  c.lineJoin = c.lineCap = 'round'; c.fillStyle = '#f6efe0'; c.strokeStyle = PLUM; c.lineWidth = r * .14;
  c.beginPath(); c.moveTo(x - r * .5, y - r * .7); c.quadraticCurveTo(x, y - r * .45, x + r * .5, y - r * .7); c.quadraticCurveTo(x + r * .95, y + r * .2, x + r * .7, y + r * .85); c.lineTo(x - r * .7, y + r * .85); c.quadraticCurveTo(x - r * .95, y + r * .2, x - r * .5, y - r * .7); c.closePath(); c.fill(); c.stroke();
  c.beginPath(); c.moveTo(x - r * .5, y - r * .7); c.lineTo(x - r * .62, y - r * 1.0); c.lineTo(x + r * .62, y - r * 1.0); c.lineTo(x + r * .5, y - r * .7); c.fill(); c.stroke();
  c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${r * .62}px ${FONT}`; c.fillText('UN', x, y + r * .2);
}
function ovenAt(c, x, y, r, ph) {
  c.lineJoin = c.lineCap = 'round'; c.fillStyle = '#b9c2e6'; c.strokeStyle = PLUM; c.lineWidth = r * .14; c.beginPath(); c.roundRect(x - r, y - r * .85, r * 2, r * 1.7, r * .2); c.fill(); c.stroke();
  c.fillStyle = '#3a2a4a'; c.beginPath(); c.roundRect(x - r * .68, y - r * .3, r * 1.36, r * .95, r * .12); c.fill(); c.stroke();
  const f = 1 + .12 * Math.sin(ph * 18); c.fillStyle = '#ff7a2a'; c.beginPath(); c.moveTo(x - r * .34, y + r * .58); c.quadraticCurveTo(x - r * .4, y, x, y - r * .22 * f); c.quadraticCurveTo(x + r * .4, y, x + r * .34, y + r * .58); c.closePath(); c.fill();
  c.fillStyle = '#ffe15a'; c.beginPath(); c.ellipse(x, y + r * .36, r * .14, r * .2 * f, 0, 0, 6.29); c.fill();
  c.fillStyle = PLUM; for (const d of [-.5, 0, .5]) { c.beginPath(); c.arc(x + d * r, y - r * .58, r * .09, 0, 6.29); c.fill(); }
}
function faceAt(c, x, y, r) {
  c.fillStyle = '#ffffff'; c.strokeStyle = PLUM; c.lineWidth = r * .12; c.beginPath(); c.ellipse(x, y, r, r * .92, 0, 0, 6.29); c.fill(); c.stroke();
  c.fillStyle = PLUM; for (const d of [-.3, .3]) { c.beginPath(); c.arc(x + d * r, y - r * .05, r * .1, 0, 6.29); c.fill(); }
  c.lineWidth = r * .08; c.beginPath(); c.arc(x, y + r * .3, r * .22, .3, 2.84); c.stroke();
}
function tick(c, x, y, r, ok) {
  c.lineCap = c.lineJoin = 'round';
  for (const [lw, col] of [[r * .5, PLUM], [r * .26, ok ? '#4ac86a' : '#ff4a3f']]) { c.strokeStyle = col; c.lineWidth = lw; c.beginPath(); if (ok) { c.moveTo(x - r * .6, y); c.lineTo(x - r * .15, y + r * .5); c.lineTo(x + r * .7, y - r * .55); } else { c.moveTo(x - r * .5, y - r * .5); c.lineTo(x + r * .5, y + r * .5); c.moveTo(x + r * .5, y - r * .5); c.lineTo(x - r * .5, y + r * .5); } c.stroke(); }
}
// the diagram. kind 0: "fırıncı" holds on to bread, flour, an oven (a = how many, b = grip); 1: "Selim" holds on to nothing and
// slides off (a = fall, b = the name fades); 2: a picture on a wall with no nail (a = fall); 3: the experiment: the same word as
// a job and as a surname (a = the job is remembered, b = the surname is forgotten); 4: the name of the effect. ph = time.
function drawMech(c, w, h, kind, a, b, ph) {
  c.lineJoin = c.lineCap = 'round';
  c.fillStyle = CREAM; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 36); c.fill(); c.stroke();
  const K = Math.round(kind), tw = w * .34, th = h * .3, spots = [[w * .2, h * .72], [w * .5, h * .78], [w * .8, h * .72]];
  if (K === 0) {
    const tx = w * .5, ty = h * .25, n = a * 3;
    spots.forEach(([x, y], i) => { const k = Math.max(0, Math.min(1, n - i)); if (k <= 0) return;
      for (const [lw, col] of [[h * (.03 + .03 * b), PLUM], [h * (.012 + .018 * b), b > .5 ? '#4ac86a' : '#ff9a3a']]) { c.strokeStyle = col; c.lineWidth = lw; c.beginPath(); c.moveTo(tx + (i - 1) * tw * .3, ty + th * .45); c.lineTo(lerpN(tx, x, k), lerpN(ty + th * .45, y - h * .14, k)); c.stroke(); }
      c.save(); c.translate(x, y); c.scale(k, k); if (i === 0) breadAt(c, 0, 0, h * .13); else if (i === 1) sackAt(c, 0, 0, h * .12); else ovenAt(c, 0, 0, h * .12, ph); c.restore(); });
    tagAt(c, tx, ty + Math.sin(ph * 12) * h * .006 * b, tw * (1 + .05 * b), th * (1 + .05 * b), 'FIRINCI', YEL);
  } else if (K === 1) {
    c.setLineDash([h * .03, h * .03]); c.strokeStyle = '#b9b2c6'; c.lineWidth = h * .014;
    spots.forEach(([x, y]) => { c.beginPath(); c.arc(x, y, h * .12, 0, 6.29); c.stroke(); }); c.setLineDash([]);
    c.fillStyle = '#b9b2c6'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .13}px ${FONT}`; spots.forEach(([x, y]) => c.fillText('?', x, y + h * .01));
    const e = a * a, y = lerpN(h * .25, h * .76, e);
    c.save(); c.translate(w * .5 + e * w * .04, y); c.rotate(e * .38 + (a > 0 && a < 1 ? Math.sin(ph * 30) * .03 : 0)); tagAt(c, 0, 0, tw, th, 'SELİM', RED, 1 - b); c.restore();
    if (a > .05 && a < 1) { c.strokeStyle = '#b9b2c6'; c.lineWidth = h * .014; for (const d of [-.12, 0, .12]) { c.beginPath(); c.moveTo(w * (.5 + d), y - th * .75); c.lineTo(w * (.5 + d), y - th * 1.1); c.stroke(); } }
  } else if (K === 2) {
    c.save(); c.beginPath(); c.roundRect(24, 24, w - 48, h - 48, 26); c.clip(); c.fillStyle = '#c9d6f6'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#b6c6ee'; for (let x = 0; x < w; x += w / 9) c.fillRect(x, 0, w / 18, h); c.fillStyle = '#8a6a4a'; c.fillRect(0, h * .9, w, h * .1); c.restore();
    // where the nail should have been
    c.setLineDash([h * .025, h * .025]); c.strokeStyle = PLUM; c.lineWidth = h * .012; c.beginPath(); c.arc(w * .5, h * .14, h * .05, 0, 6.29); c.stroke(); c.setLineDash([]);
    c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .07}px ${FONT}`; c.fillText('?', w * .5, h * .145);
    const e = a * a, y = lerpN(h * .4, h * .7, e), fw = w * .34, fh = h * .4;
    c.save(); c.translate(w * .5, y); c.rotate(e * .3 + (a >= 1 ? Math.sin(ph * 26) * .02 * Math.exp(-0) : 0));
    c.fillStyle = '#e8b23e'; c.strokeStyle = PLUM; c.lineWidth = h * .022; c.beginPath(); c.roundRect(-fw / 2, -fh / 2, fw, fh, 8); c.fill(); c.stroke();
    c.fillStyle = '#9fd0ff'; c.beginPath(); c.rect(-fw * .4, -fh * .38, fw * .8, fh * .76); c.fill(); c.lineWidth = h * .012; c.stroke();
    c.save(); c.beginPath(); c.rect(-fw * .4, -fh * .38, fw * .8, fh * .76); c.clip(); c.fillStyle = '#4aa86a'; c.beginPath(); c.moveTo(-fw * .5, fh * .4); c.lineTo(-fw * .12, -fh * .1); c.lineTo(fw * .12, fh * .2); c.lineTo(fw * .28, 0); c.lineTo(fw * .5, fh * .4); c.fill();
    c.fillStyle = '#ffe15a'; c.beginPath(); c.arc(fw * .22, -fh * .2, fh * .09, 0, 6.29); c.fill(); c.restore(); c.restore();
    if (a > .05 && a < 1) { c.strokeStyle = PLUM; c.lineWidth = h * .012; for (const d of [-.13, 0, .13]) { c.beginPath(); c.moveTo(w * (.5 + d), y - fh * .62); c.lineTo(w * (.5 + d), y - fh * .9); c.stroke(); } }
  } else if (K === 3) {
    c.strokeStyle = '#d8d0e0'; c.lineWidth = h * .01; c.beginPath(); c.moveTo(w * .5, h * .1); c.lineTo(w * .5, h * .9); c.stroke();
    c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .085}px ${FONT}`; c.fillText('MESLEK', w * .26, h * .14); c.fillText('SOYADI', w * .74, h * .14);
    faceAt(c, w * .26, h * .38, h * .13); faceAt(c, w * .74, h * .38, h * .13);
    breadAt(c, w * .1, h * .4, h * .07);
    tagAt(c, w * .26, h * .72, tw * .95, th * .95, 'FIRINCI', YEL); tagAt(c, w * .74, h * .72, tw * .95, th * .95, b > .5 ? '? ? ?' : 'FIRINCI', RED);
    if (a > .5) tick(c, w * .42, h * .52, h * .09 * (1 + .06 * Math.sin(ph * 10)), true);
    if (b > .5) tick(c, w * .9, h * .52, h * .08 * (1 + .06 * Math.sin(ph * 10)), false);
  } else {
    breadAt(c, w * .5, h * .25, h * .15);
    c.textAlign = 'center'; c.textBaseline = 'middle'; c.lineJoin = 'round';
    [['FIRINCI', h * .56, '#f2a03a'], ['PARADOKSU', h * .78, '#e2463f']].forEach(([s, y, col]) => { let fs = h * .2; c.font = `900 ${fs}px ${FONT}`; const m = c.measureText(s).width; if (m > w * .8) { fs *= w * .8 / m; c.font = `900 ${fs}px ${FONT}`; } c.strokeStyle = PLUM; c.lineWidth = fs * .22; c.strokeText(s, w / 2, y); c.fillStyle = col; c.fillText(s, w / 2, y); });
  }
}

// ---------------------------------------------------------------- DÜĞÜN SALONU
const HP = { x: 0, z: -.5 }, GP = { x: 1.05, z: -.55 }, TP = { x: -.64, z: -1.25 }, CAKE = V(.52, 0, -1.95);
const KEYP = V(-2.4, 3.2, -.2);
function buildSalon(scene) {
  const g = new THREE.Group(); scene.add(g);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(14, 10), painted(woodTex({ base: '#c9935f', rep: [6, 4] }))); fl.rotation.x = -Math.PI / 2; g.add(fl);
  const rug = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 7), painted(carpetTex({ base: '#b8323a', band: '#e0b050', rep: [1, 2], rows: 2 }))); rug.rotation.x = -Math.PI / 2; rug.position.set(.5, .006, .6); g.add(rug);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(14, 6), painted(stoneTex({ base: '#b9c4f2', seam: '#a2aee4', bw: 64, bh: 64, rep: [14, 6] }))); wall.position.set(0, 3, -2.4); g.add(wall);
  const dado = new THREE.Mesh(new THREE.BoxGeometry(14, .42, .05), painted(tileTex({ a: '#d8589a', b: '#f2ead8', rep: [32, 1] }))); dado.position.set(0, 1.0, -2.36); g.add(dado);
  for (const y of [.77, 1.23]) { const m = new THREE.Mesh(new THREE.BoxGeometry(14, .05, .08), flat('#eef3fb')); m.position.set(0, y, -2.35); g.add(m); }
  // drapes on both sides
  for (const [x, col] of [[-1.75, '#8a4ab0'], [2.45, '#8a4ab0']]) for (let k = 0; k < 4; k++) { const d = new THREE.Mesh(new THREE.CylinderGeometry(.11, .14, 4.2, 10), flat(k % 2 ? col : '#9a5ac0')); d.position.set(x + k * .2, 2.1, -2.22); g.add(d); }
  // a string of bulbs: the light of the set
  dyn.bulbs = [];
  for (let i = 0; i <= 12; i++) { const u = i / 12, x = lerpN(-1.6, 2.9, u), y = 3.05 - Math.sin(u * Math.PI) * .32;
    const bl = new THREE.Mesh(new THREE.SphereGeometry(.07, 12, 10), new THREE.MeshBasicMaterial({ color: HDR(2.3, 1.75, .9) })); bl.position.set(x, y - .1, -2.15); g.add(bl); dyn.bulbs.push(bl);
    if (i < 12) { const u2 = (i + 1) / 12, x2 = lerpN(-1.6, 2.9, u2), y2 = 3.05 - Math.sin(u2 * Math.PI) * .32, d = V(x2 - x, y2 - y, 0); const wr = new THREE.Mesh(new THREE.CylinderGeometry(.008, .008, d.length(), 4), flat('#3a3a5a')); wr.position.set((x + x2) / 2, (y + y2) / 2, -2.15); wr.quaternion.setFromUnitVectors(V(0, 1, 0), d.clone().normalize()); wr.userData.noShadow = true; g.add(wr); } }
  // the wedding cake on its table
  const tb = new THREE.Mesh(new THREE.CylinderGeometry(.42, .46, .78, 28), flat('#f6f1f8')); tb.position.set(CAKE.x, .39, CAKE.z); g.add(tb);
  [[.27, '#fff6ee'], [.2, '#ffd0de'], [.13, '#fff6ee']].forEach(([r, col], i) => { const t = new THREE.Mesh(new THREE.CylinderGeometry(r, r, .17, 28), flat(col)); t.position.set(CAKE.x, .78 + .085 + i * .17, CAKE.z); g.add(t);
    const bd = new THREE.Mesh(new THREE.TorusGeometry(r, .02, 6, 28), flat('#e8553a')); bd.rotation.x = Math.PI / 2; bd.position.set(CAKE.x, .78 + i * .17 + .02, CAKE.z); bd.userData.noShadow = true; g.add(bd); });
  const top = new THREE.Mesh(new THREE.SphereGeometry(.05, 10, 8), flat('#e2463f')); top.position.set(CAKE.x, 1.34, CAKE.z); g.add(top);
  // balloons
  for (const [x, y, z, col] of [[-1.25, 2.3, -2.0, '#ff6a8a'], [-1.0, 2.55, -2.05, '#ffd23a'], [-.78, 2.25, -2.0, '#4ac8c0'], [1.95, 2.4, -2.0, '#ffd23a'], [2.2, 2.2, -2.05, '#ff6a8a']]) {
    const b = new THREE.Mesh(new THREE.SphereGeometry(.17, 16, 12), flat(col)); b.scale.y = 1.18; b.position.set(x, y, z); g.add(b);
    const s = new THREE.Mesh(new THREE.CylinderGeometry(.004, .004, y - .2, 4), new THREE.MeshBasicMaterial({ color: '#f4f6ff' })); s.position.set(x, (y - .2) / 2, z); g.add(s); }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#b9c6ff', '#8a7a9a', 1.5));
  const key = new THREE.SpotLight('#ffd9a0', 15, 14, 1.0, .6, 1.3); key.position.copy(KEYP); key.target.position.set(.4, .6, -.8);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0015; key.shadow.radius = 4; L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .7); fill.position.set(2, 3, 6); fill.target.position.set(0, 1, -1); L.add(fill); L.add(fill.target);
  scene.add(L);
  shadows(g);
  for (const i of [2, 6, 10]) glow(scene, [dyn.bulbs[i].position.x, dyn.bulbs[i].position.y, -2.1], '#ffd28a', 1.3, .2);
}

// ---------------------------------------------------------------- CAST
const HERO = { hair: '#3a2a24', cloth: '#3a4a9a', collar: true, buttons: '#f0c455' };
export const LOOK = {
  kahraman: { ...HERO, height: 1.7 },
  teyze: { hair: '#b04a9a', cloth: '#d8488a', buttons: '#fbf2d8', bodyW: 230, headW: 280, headH: 254, height: 1.6 },
  selim: { mustache: '#3a2a24', hair: '#3a2a24', cloth: '#3f8f7a', buttons: '#f1e2bd', height: 1.74 },
  ikinci: { beard: '#6a4a3a', beardLen: .6, hair: '#6a4a3a', cloth: '#e8873a', pocket: true, height: 1.8 },
  firinci: { mustache: '#3a2a24', hair: '#3a2a24', hat: 'cook', cloth: '#f2c23a', apron: true, bodyW: 232, headW: 278, headH: 254, height: 1.76 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hook: { pos: [.16, 1.4, 1.95], look: [.16, 1.33, -.5], fov: 46 },
  faceUp: { pos: [-.14, 1.56, 1.9], look: [0, 1.56, -.5], fov: 40 },
  guest: { pos: [1.15, 1.5, 1.7], look: [1.08, 1.47, -.55], fov: 42 },
  guestF: { pos: [1.15, 1.62, 2.15], look: [1.08, 1.6, -.55], fov: 42 },
  face: { pos: [-.14, 1.48, 1.35], look: [0, 1.44, -.5], fov: 40 },
  wide: { pos: [.3, 1.55, 4.9], look: [.3, 1.25, -1], fov: 50 },
  two: { pos: [.3, 1.42, 3.9], look: [.3, 1.24, -.6], fov: 48 },
  twoIn: { pos: [.34, 1.42, 3.45], look: [.34, 1.27, -.6], fov: 48 },
  twoR: { pos: [.5, 1.44, 3.9], look: [.42, 1.26, -.6], fov: 48 },
  teyze: { pos: [-.5, 1.42, 1.45], look: [-.6, 1.4, -1.25], fov: 42 },
  mech: { pos: [.3, 1.72, 4.5], look: [.3, 1.72, -.5], fov: 46 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: the handshake and the empty name tag -> the man who just said it -> your face
    { t: 0, ...SHOT.hook, creep: .4, drift: .02 },
    { t: t('söyledi') + .08, dur: .2, move: 'whip', ...SHOT.guest, creep: .34, drift: .015 },
    { t: t('Unuttun') + .1, dur: .2, move: 'whip', ...SHOT.face, creep: .34, drift: .015 },
    { t: t('Bakın') + .16, dur: .3, move: 'whip', ...SHOT.wide, creep: .2, drift: .03 },
    { t: t('teyzen') + .1, dur: .8, ...SHOT.two, creep: .16, drift: .02 },
    // three guests
    { t: t('Ben') - .08, dur: .26, move: 'whip', ...SHOT.guest, creep: .3, drift: .015 },
    { t: t('Üç') + .08, dur: .26, move: 'whip', ...SHOT.faceUp, creep: .3, drift: .015 },
    { t: t('Teyzen', 2) + .08, dur: .28, move: 'whip', ...SHOT.teyze, creep: .3, drift: .015 },
    { t: t('İkinci') + .1, dur: .3, move: 'whip', ...SHOT.two, creep: .16, drift: .02 },
    { t: t('sen') + .1, dur: .6, ...SHOT.twoIn, creep: .14, drift: .012 },
    { t: t('Üçüncü') + .1, dur: .3, move: 'whip', ...SHOT.twoR, creep: .16, drift: .02 },
    { t: t('Ben', 2) - .08, dur: .26, move: 'whip', ...SHOT.guestF, creep: .3, drift: .015 },
    { t: t('İşte') + .08, dur: .28, move: 'whip', ...SHOT.twoIn, creep: .16, drift: .015 },
    // the turn: why the word sticks and the name does not
    { t: t('Çünkü') + .1, dur: .3, move: 'whip', ...SHOT.mech, creep: .02, drift: .004 },
    // the loop: the baker asks for YOUR name; the first frame again
    { t: t('Gecenin') + .1, dur: .3, move: 'whip', ...SHOT.guestF, creep: .3, drift: .015 },
    { t: t('adın') + .06, dur: .24, move: 'whip', ...SHOT.hook, fov: 47.2, creep: .1, drift: 0 },
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('Unuttun') + .12, .5); cp.kick(t('uçmuş') + .05, .5); cp.kick(t('uçuyor') + .05, .7); cp.kick(t('fırıncıyım') + .05, .5); cp.kick(t('unutmuyorsun') + .1, .6); cp.kick(t('tutunuyor') + .05, .4); cp.kick(t('düşüyor') + .12, .6); cp.kick(t('unutuldu') + .05, .4); cp.kick(t('neydi') + .05, .5);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .45) * FPS) / FPS;      // no dead frames after the last word (loop)
  const { scene } = ctx;
  scene.background = new THREE.Color('#33407a');
  buildSalon(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  const T = (text, col) => card(scene, .44, .32, drawTag(text, col), { pw: 384 });
  dyn.tagQ = T('? ? ?', RED); dyn.tagS = [T('SELİM', RED), T('SELİM', RED)]; dyn.tagH = [T('HAKAN', RED), T('HAKAN', RED), T('HAKAN', RED)]; dyn.tagF = T('FIRINCI', YEL);
  dyn.bun = card(scene, .56, .4, drawBun, { pw: 384 });
  dyn.q = [0, 1].map(() => card(scene, .3, .36, drawMark('?', '#ffe15a'), { pw: 256 }));
  dyn.bang = card(scene, .3, .4, drawMark('!', '#ff5a4a'), { pw: 256 });
  dyn.bread = card(scene, .4, .28, (c, w, h) => breadAt(c, w / 2, h / 2, w * .4), { pw: 256 });
  dyn.mech = dynCard(scene, 1.8, 1.2, drawMech, { pw: 900, steps: 30 });
  PF = new Parcaciklar(scene);
  PF.ekle('konfeti', { t: W('unutmuyorsun') + .1, pos: [HP.x, 1.3, HP.z - .4], olcek: .8 });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('söyledi') + .02, 'rise', { dur: .3 }); cue(W('Unuttun') + .05, 'boom');
  cue(W('Bakın') + .02, 'whoosh'); cue(W('düğündesin'), 'shimmer'); cue(W('tanıştırıyor'), 'lock');
  cue(W('İlk') + .02, 'rise', { dur: .3 }); cue(W('sıkıyor'), 'lock'); cue(W('Selim') + .02, 'lock');
  cue(W('Üç') + .02, 'whoosh'); cue(W('adı'), 'wind', { dur: W('uçmuş') - W('adı') }); cue(W('uçmuş') + .05, 'cut');
  cue(W('Teyzen', 2) + .02, 'rise', { dur: .3 }); cue(W("Selim'di") + .05, 'lock');
  cue(W('İkinci') + .02, 'whoosh'); cue(W('iki'), 'lock'); cue(W('kere'), 'lock'); cue(W('tekrar'), 'lock'); cue(W('yine'), 'wind', { dur: W('uçuyor') + .3 - W('yine') }); cue(W('uçuyor') + .05, 'boom');
  cue(W('Üçüncü') + .05, 'rise', { dur: .3 }); cue(W('söylemiyor'), 'lock'); cue(W('fırıncıyım') + .05, 'boom');
  cue(W('İşte') + .02, 'rise', { dur: .3 }); cue(W('unutmuyorsun') + .1, 'shimmer');
  cue(W('Çünkü') + .02, 'whoosh'); cue(W('ekmek'), 'lock'); cue(W('un'), 'lock'); cue(W('fırın'), 'lock'); cue(W('tutunuyor') + .05, 'boom');
  cue(W('Selim', 2) + .02, 'rise', { dur: .3 }); cue(W('tutunmuyor'), 'wind', { dur: .6 }); cue(W('etiket') + .05, 'cut');
  cue(W('Tıpkı') + .05, 'rise', { dur: .3 }); cue(W('tablo'), 'lock'); cue(W('yok'), 'rise', { dur: W('düşüyor') - W('yok') }); cue(W('düşüyor') + .12, 'boom');
  cue(W('deneyde') - .05, 'rise', { dur: .3 }); cue(W('meslek'), 'lock'); cue(W('soyadı'), 'lock'); cue(W('kaldı') + .05, 'shimmer'); cue(W('unutuldu') + .05, 'cut');
  cue(W('Adı', 2) + .05, 'rise', { dur: .35 }); cue(W('paradoksu') + .05, 'boom');
  cue(W('Gecenin') + .02, 'rise', { dur: .3 }); cue(W('Senin') + .02, 'lock'); cue(W('adın') + .02, 'rise', { dur: .25 }); cue(W('neydi') + .08, 'boom'); cue(W('neydi') + .2, 'shimmer');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'ADINI NEDEN UNUTURSUN?'); }

// ---------------------------------------------------------------- PER FRAME
const COOL = '#d6d6f6', WARM = '#ffcf8a';
const SHAKE = [78, 6];
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos); m.material.opacity = 1;
  m.rotation.z = wob ? Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04 : 0;
  return s;
}
// a tag that flies off like a bird from t0 on
function flyOff(m, t, t0, dir = 1) {
  const k = t - t0; if (k <= 0) return;
  m.position.x += dir * k * k * 2.4; m.position.y += k * 2.2 + Math.sin(k * 26) * .05; m.rotation.z = dir * -k * 1.6 + Math.sin(k * 30) * .2; m.scale.multiplyScalar(Math.max(.2, 1 - k * .9)); m.material.opacity = Math.max(0, 1 - k * 1.5); if (k > .66) m.visible = false;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  PF.guncelle(t);
  for (const c of Object.values(cast)) c.hide();
  for (const m of dyn.cards) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const grade = [1.01, 1.0, 1.01], face = [1, .985, .97], tint = face.map((v, i) => v / grade[i]);
  const H = cast.kahraman, TZ = cast.teyze;
  const lit = { lit: -1, shade: COOL, rim: { color: WARM, a: .4 } };
  const hop = (t0, d = .26) => { const k = (t - t0) / d; return k > 0 && k < 1 ? Math.sin(Math.PI * k) : 0; };
  // ---- the beats
  const hookEnd = A('Bakın'), tG1 = A('İlk'), tName1 = A('Selim'), tGone1 = A('adı'), tFly1 = W('uçmuş') - .12, tTz = A('Teyzen', 2);
  const tG2 = A('İkinci') - .05, tFly2 = W('uçuyor') - .1, tG3 = A('Üçüncü') - .05, tBaker = A('fırıncıyım'), tKeep = A('İşte');
  const tMech = W('Çünkü') - .1, tEnd = A('Gecenin'), tBack = W('adın') - .04;
  const hook = t < hookEnd, mech = t >= tMech && t < tEnd, loop = t >= tBack;
  const kind = t < A('Selim', 2) ? 0 : t < A('Tıpkı') ? 1 : t < W('bir', 5) - .1 ? 2 : t < A('Adı', 2) ? 3 : 4;
  let focus = V(HP.x, 1.4, HP.z);
  // ---- who stands in front of you
  const guest = hook || (t >= tG1 && t < tG2) ? 'selim' : t >= tG2 && t < tG3 ? 'ikinci' : t >= tG3 ? 'firinci' : null;
  const gIn = guest === 'selim' ? (hook ? -9 : tG1) : guest === 'ikinci' ? tG2 : tG3;
  const gx = guest ? lerpN(2.6, GP.x, ramp(t, gIn, gIn + .3)) : 9;
  const shaking = hook || loop || (t > tG1 + .25 && t < tGone1) || (t > tG2 + .25 && t < A('sen')) || (t > tG3 + .25 && t < A('Ben', 2) + .2);
  const shk = shaking ? Math.sin(t * 22) * 5 : 0;
  // ---- the hero
  {
    let hp = { expr: 'worried', mouth: .12, look: .5, lookY: 0, gazeX: .6, brow: .9, sweat: .9, armL: [16, 10], armR: [SHAKE[0] + shk, SHAKE[1]],
      blink: bl(1, A('söyledi'), A('Unuttun'), A('teyzen'), tG1, tName1, tGone1, tFly1, tG2, A('sen'), tFly2, tG3, tBaker, tKeep, tMech, A('Selim', 2), A('Tıpkı'), A('düşüyor'), A('Meslek', 2), A('soyadı', 2), tEnd) };
    const smile = { ...hp, expr: 'smile', mouth: 0, sweat: 0, brow: .4, gazeX: .5 };
    if (hook) { if (t > A('Unuttun')) hp = { ...hp, expr: 'surprised', mouth: .3, look: 0, gazeX: 0, brow: 1, sweat: 1, armR: [16, 10] }; }
    else if (loop) hp = hp;
    else if (t < tG1) hp = { ...smile, look: t < A('teyzen') ? .2 : -.3, gazeX: t < A('teyzen') ? .3 : -.6, armR: [16, 10], expr: t > A('herkesle') ? 'worried' : 'smile', sweat: t > A('herkesle') ? .6 : 0 };
    else if (t < tGone1) hp = shaking ? { ...smile, expr: 'grin' } : { ...smile, armR: [16, 10] };
    else if (t < tTz) hp = t < tFly1 ? { ...hp, expr: 'worried', look: .1, lookY: .4, gazeX: 0, gazeY: .8, armR: [16, 10], sweat: ramp(t, tGone1, tGone1 + .4) } : { ...hp, expr: 'surprised', mouth: .45, look: .3, lookY: .5, gazeX: .6, gazeY: .8, brow: 1, armR: [150, 24], armL: [150, 24] };
    else if (t < tG2) hp = { ...hp, look: -.5, gazeX: -.7, armR: [16, 10], expr: t > A("Selim'di") ? 'grin' : 'worried', sweat: t > A("Selim'di") ? 0 : 1 };
    else if (t < tG3) {
      if (t < A('sen')) hp = shaking ? { ...smile, expr: 'grin' } : { ...smile, armR: [16, 10] };
      else if (t < tFly2) hp = { ...smile, expr: 'grin', mouth: t > A('tekrar') - .05 && t < A('yine') ? flap(env, t) : 0, brow: .8, armR: [120, 60] };
      else hp = { ...hp, expr: 'surprised', mouth: .5, look: .2, lookY: .5, gazeY: .8, brow: 1, sweat: 1, armR: [150, 24 + 10 * Math.sin(t * 24)], armL: [150, 24 - 10 * Math.sin(t * 24)] };
    }
    else if (t < tKeep) hp = shaking ? { ...smile, expr: 'worried', sweat: .7 } : t < tBaker ? { ...hp, armR: [16, 10], expr: 'worried', lookY: .1 } : { ...smile, expr: 'surprised', mouth: .3, brow: 1, armR: [16, 10] };
    else if (t < tMech) hp = { ...smile, expr: 'grin', look: .1, lookY: .2, brow: 1, armR: [150, 24], armL: [150, 24], bob: -Math.abs(Math.sin((t - tKeep) * 10)) * 6 };
    else if (mech) {
      hp = { ...smile, expr: 'surprised', mouth: .1, look: .1, lookY: .6, gazeX: 0, gazeY: 1, brow: .6, armR: [16, 10] };
      if (kind === 0 && t > A('tutunuyor')) hp = { ...hp, expr: 'grin', brow: 1 };
      if (kind === 1) hp = { ...hp, expr: t > A('tutunmuyor') ? 'worried' : 'surprised', brow: .8, sweat: t > A('tutunmuyor') ? .8 : 0 };
      if (kind === 2) hp = { ...hp, expr: t > A('düşüyor') + .1 ? 'surprised' : 'worried', mouth: t > A('düşüyor') + .1 ? .45 : .1, brow: 1 };
      if (kind === 3) hp = { ...hp, expr: t > A('kaldı') && t < A('soyadı', 2) ? 'grin' : 'surprised', brow: .8 };
      if (kind === 4) hp = { ...hp, expr: 'grin', lookY: .5, brow: 1, armR: [148, -128] };
    }
    else hp = { ...smile, expr: t > A('Senin') ? 'worried' : 'smile', sweat: t > A('Senin') ? 1 : 0, brow: t > A('Senin') ? 1 : .4 };
    H.show(); H.place(HP.x, 0, HP.z, cam, tint); H.draw({ ...hp, ...lit }); H.castFrom(KEYP);
    // the name on its tag: there, then gone
    const over = V(HP.x + .02, 2.02, HP.z + .02);
    if (hook && t < A('söyledi') + .2 || loop) { const s = popCard(dyn.tagQ, loop ? tBack + .1 : -1, t, V(HP.x + .47, 1.6, HP.z + .04), hook ? .85 + .03 * Math.sin(t * 9) : .85, !hook); if (s && hook) dyn.tagQ.rotation.z = Math.sin(t * 20) * .05; }
    if (t >= tGone1 && t < tTz) { popCard(dyn.tagS[0], tGone1, t, over, .95); flyOff(dyn.tagS[0], t, tFly1); if (t > tFly1 + .25) popCard(dyn.q[0], tFly1 + .25, t, over.clone().add(V(0, -.05, 0))); }
    if (t >= A('tekrar') && t < tG3) { popCard(dyn.tagH[2], A('tekrar'), t, over, .95); flyOff(dyn.tagH[2], t, tFly2 + .1, -1); if (t > tFly2 + .4) popCard(dyn.q[0], tFly2 + .4, t, over.clone().add(V(0, -.05, 0))); }
    if (t >= tKeep && t < tMech) { const s = popCard(dyn.tagF, tKeep, t, over, 1.05); if (s) dyn.tagF.position.y += -Math.abs(Math.sin((t - tKeep) * 10)) * .0; }
    focus = V(HP.x, 1.4, HP.z);
  }
  // ---- the guests: Selim, the man who says it twice, the baker
  if (guest) {
    const G = cast[guest]; let gp = { expr: 'smile', look: -.6, lookY: 0, armL: [SHAKE[0] - shk, SHAKE[1]], armR: [16, 10], blink: bl(5, A('söyledi'), tG1, tName1, tG2, A('kere'), tFly2, tG3, tBaker, tKeep, tMech, A('tutunuyor'), tEnd, A('Senin')) };
    if (!shaking) gp = { ...gp, armL: [16, 10] };
    if (guest === 'selim') {
      if (hook) gp = { ...gp, expr: 'grin', brow: .5 };
      else { const talk = t > A('Ben') - .03 && t < W('Selim') + .45; gp = { ...gp, expr: talk ? 'grin' : 'smile', mouth: talk ? flap(env, t) : 0, look: t > A('Ben') && t < tGone1 ? -.3 : -.6, armR: talk ? [120, 60] : [16, 10], brow: talk ? .6 : 0 }; if (t > tTz) gp = { ...gp, expr: 'smug', lid: .3 }; }
    } else if (guest === 'ikinci') {
      const talk = t > A('adını', 2) && t < A('sen'); gp = { ...gp, expr: talk ? 'grin' : 'smile', mouth: talk ? .3 + .5 * Math.abs(Math.sin(t * 13)) : 0, brow: talk ? .7 : 0, armR: talk ? [130, 40 + 10 * Math.sin(t * 13)] : [16, 10] };
      if (t > tFly2 + .1) gp = { ...gp, expr: 'worried', mouth: 0, brow: .8, look: -.5 };
    } else {
      const talk1 = t > A('Ben', 2) - .03 && t < W('fırıncıyım') + .6, talk2 = t > A('Senin') - .03 && t < W('neydi') + .3;
      gp = { ...gp, expr: talk1 || talk2 ? 'grin' : 'smile', mouth: talk1 || talk2 ? flap(env, t) : 0, look: talk1 ? -.25 : -.6, brow: talk1 || talk2 ? .7 : 0, armR: talk1 ? [150, 24] : [16, 10] };
      if (t >= tKeep && t < tMech) gp = { ...gp, expr: 'proud', mouth: 0, armR: [150, 24] };
      if (mech) gp = { ...gp, expr: kind === 0 || kind === 4 ? 'proud' : 'smile', look: -.2, lookY: .6, gazeY: 1, armL: [16, 10], armR: [16, 10] };
      if (t >= tEnd && !talk2) gp = { ...gp, expr: 'smile', look: -.6, brow: .3 };
      if (talk2) gp = { ...gp, armL: shaking ? gp.armL : [96, 20], brow: 1 };
    }
    G.show(); G.place(gx, hop(gIn + .3, .2) * .05, GP.z, cam, tint); G.draw({ ...gp, ...lit }); G.castFrom(KEYP);
    const gOver = V(GP.x + .02, 2.1, GP.z + .02);
    if (hook && t > A('söyledi') + .1 && t < A('Unuttun') + .12) { popCard(dyn.tagS[1], A('söyledi') + .1, t, V(GP.x + .3, 1.66, GP.z + .03), .7); }
    if (guest === 'selim' && !hook && t >= tName1 && t < tGone1) popCard(dyn.tagS[1], tName1, t, gOver.clone().add(V(0, -.04, 0)), .9);
    if (guest === 'ikinci') { [['iki', -.2, .0], ['kere', .22, .16]].forEach(([w, dx, dy], i) => { if (t < A(w)) return; popCard(dyn.tagH[i], A(w), t, gOver.clone().add(V(dx - .12, dy + .06, i * .01)), .8); flyOff(dyn.tagH[i], t, tFly2 + i * .08, i ? 1 : -1); }); }
    if (guest === 'firinci' && t >= tBaker && t < tKeep) { popCard(dyn.tagF, tBaker, t, V(GP.x + .02, 2.33, GP.z + .02), .9); popCard(dyn.bread, tBaker + .12, t, V(GP.x + .34, 1.98, GP.z + .03), .72); }
    if (guest === 'firinci' && t > W('neydi') - .05 && !loop) popCard(dyn.q[1], W('neydi') - .05, t, V(GP.x - .42, 2.0, GP.z + .02));
    if ((t >= A('Ben') - .1 && t < tGone1) || (t >= A('Ben', 2) - .1 && t < tKeep) || (t >= tEnd && !loop) || (hook && t > A('söyledi') && t < A('Unuttun'))) focus = V(GP.x, 1.5, GP.z);
  }
  // ---- teyze: a whisper, then despair, then silence
  {
    let tp = { expr: 'smile', look: .5, lookY: 0, armL: [16, 10], armR: [16, 10], blink: bl(3, A('teyzen'), tG1, tGone1, tTz, A("Selim'di"), tG2, tFly2, tG3, tBaker, tKeep, tMech, A('Tıpkı'), tEnd) };
    if (t >= hookEnd && t < tG1) tp = { ...tp, expr: 'grin', look: t < A('herkesle') ? .3 : .7, brow: .6, armR: [130, 30 + 12 * Math.sin(t * 9)], armL: [40, -30] };
    if (t >= tG1 && t < tGone1) tp = { ...tp, expr: 'proud', look: .6 };
    if (t >= tGone1 && t < tG2) { const talk = t > A("Selim'di") - .03 && t < W("Selim'di") + .55; tp = { ...tp, expr: talk ? 'grin' : 'smug', lid: talk ? 0 : .3, mouth: talk ? flap(env, t) : 0, look: .7, lookY: .1, brow: talk ? .6 : -.1, armR: t > tTz ? [120, 84] : [16, 10] }; }
    if (t >= tG2 && t < tFly2) tp = { ...tp, expr: t > A('sen') ? 'worried' : 'smile', look: .5, brow: t > A('sen') ? .7 : .2 };
    if (t >= tFly2 && t < tG3) tp = { ...tp, expr: 'angry', brow: -.6, look: .4, lookY: -.2, sweat: 1, mouth: .2, armL: [150, -128], armR: [150, -128], bob: Math.sin(t * 28) * 3 };
    if (t >= tG3 && t < tBaker) tp = { ...tp, expr: 'angry', brow: -.4, look: .6, lid: .2, armL: [40, -64], armR: [40, -64] };
    if (t >= tBaker && t < tMech) tp = { ...tp, expr: 'surprised', mouth: t > tKeep ? .35 : .15, look: .5, brow: 1 };
    if (mech) tp = { ...tp, expr: 'surprised', mouth: .1, look: .3, lookY: .6, gazeY: 1, brow: .7 };
    if (t >= tEnd) tp = { ...tp, expr: t > A('Senin') ? 'grin' : 'smile', look: .6, brow: .5 };
    const tzx = hook || loop ? -1.7 : TP.x; TZ.show(); TZ.place(tzx, 0, TP.z, cam, tint); TZ.draw({ ...tp, ...lit }); TZ.castFrom(KEYP);
    const turn = tp.look || 0, bobY = -(tp.bob || 0) * TZ.px;
    popCard(dyn.bun, -1, t, V(tzx + turn * .02, 1.6 + .12 + bobY, TP.z + .012), 1, false);
    if (t >= A("Selim'di") && t < tG2) popCard(dyn.tagS[0], A("Selim'di"), t, V(TP.x + .34, 2.14, TP.z + .03), .8);
    if (t >= tBaker + .3 && t < tMech) popCard(dyn.q[1], tKeep + .15, t, V(TP.x + .2, 2.12, TP.z + .03), .85);
    if (t >= tTz && t < tG2) focus = V(TP.x, 1.4, TP.z);
  }
  // ---- the diagram above their heads
  if (mech) {
    let a = 0, b = 0;
    if (kind === 0) { a = t < A('ekmek') ? 0 : t < A('un') ? ramp(t, A('ekmek'), A('ekmek') + .2) / 3 : t < A('fırın') ? (1 + ramp(t, A('un'), A('un') + .2)) / 3 : (2 + ramp(t, A('fırın'), A('fırın') + .2)) / 3; b = ramp(t, A('tutunuyor'), A('tutunuyor') + .25); }
    if (kind === 1) { a = ramp(t, A('tutunmuyor'), A('tutunmuyor') + .55); b = ramp(t, A('boş'), A('boş') + .3); }
    if (kind === 2) a = ramp(t, A('yok'), W('düşüyor') + .12);
    if (kind === 3) { a = t > A('kaldı') ? 1 : 0; b = t > A('unutuldu') ? 1 : 0; }
    dyn.mech.userData.set(kind, a, b, t);
    const t0 = [tMech + .12, A('Selim', 2), A('Tıpkı'), W('bir', 5) - .1, A('Adı', 2)][kind];
    const s = popCard(dyn.mech, t0, t, V(.3, 2.84, -.3), 1, false); if (s) dyn.mech.rotation.z = Math.sin(t * 1.7) * .01;
    focus = V(.3, 1.6, HP.z);
  }
  const look = { focus: cam.position.distanceTo(focus), coc: 5, range: 2.8, sat: 1.24, lift: [.085, .085, .15], bloom: .85, vignette: .22 };
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
