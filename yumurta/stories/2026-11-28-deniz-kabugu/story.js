// Deniz kabuğunda neden deniz sesi var? Demek O Yüzden günlük Short (yumurta stili), 28 Kasım 2026.
// Bilgi: kabuğun içindeki boşluk bir rezonatör gibi çalışır; etraftaki uğultunun (rüzgâr, dalga, insan sesi) bazı
// frekanslarını içinde çınlatıp güçlendirir. Ses denizden ya da kanın akışından gelmez: ses geçirmeyen bir odada kabuk
// da susar; boş bir bardak ya da kulağa kapatılan avuç da aynı sesi verir. Kaynaklar SCRIPT.md'de.
// Tek set: SAHİL (güneş, deniz, kum, şemsiye, balıkçının kasası). Kahraman (sen) ve balıkçı amca.
// İskelet v1: kurulum (kabuğu bul) -> üç vuruş (kabuk, dev kabuk, boş bardak; amcanın kahkahası büyür) -> kırılma (amca
// susar; kabuk ve şişe şeması) -> döngü (son plan ilk planın kadrajı, kabuk yine kulakta).
import * as THREE from 'three';
import { woodTex, painted, flat, rng } from '/engine/src/paint.js';
import { Toon, PLUM, flap, blinkAt } from '/engine/src/toon.js';
import { CamPath, smoother } from '/engine/src/camera.js';
import { glow } from '/engine/src/fx.js';
import { Parcaciklar } from '/engine/src/parcacik.js';
import { kancaYazisi } from '/lib/kanca.js';

export const NAME = '2026-11-28-deniz-kabugu';
export const FPS = 30;
export let DUR = 31.5;
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
const CREAM = '#fbf7ee', SEA = '#3f9fe0', SEAD = '#2a6fc0';
// a conch: the shell of the story (opening toward the lower left, the spire up and to the right)
function shellPath(c, x, y, r) {
  c.beginPath(); c.moveTo(x - r * .95, y + r * .35);
  c.bezierCurveTo(x - r * 1.0, y - r * .5, x - r * .3, y - r * .95, x + r * .35, y - r * .7);
  c.bezierCurveTo(x + r * .7, y - r * .58, x + r * .95, y - r * .75, x + r * 1.05, y - r * .98);
  c.bezierCurveTo(x + r * 1.08, y - r * .3, x + r * .9, y + r * .45, x + r * .25, y + r * .8);
  c.bezierCurveTo(x - r * .25, y + r * 1.02, x - r * .8, y + r * .85, x - r * .95, y + r * .35); c.closePath();
}
function drawShellAt(c, x, y, r) {
  c.lineJoin = c.lineCap = 'round'; c.strokeStyle = PLUM; c.lineWidth = r * .16;
  shellPath(c, x, y, r); c.fillStyle = '#ffd9b8'; c.fill();
  c.save(); shellPath(c, x, y, r); c.clip();
  c.fillStyle = '#ff9f8a'; for (let k = 0; k < 5; k++) { c.beginPath(); c.ellipse(x + r * (.95 - k * .3), y - r * (.8 - k * .22), r * .09, r * (.3 + k * .14), .62, 0, 6.29); c.fill(); }
  c.restore();
  // the mouth of the shell: a dark, rosy hollow
  c.beginPath(); c.ellipse(x - r * .42, y + r * .3, r * .4, r * .25, -.5, 0, 6.29); c.fillStyle = '#c8507a'; c.fill();
  c.beginPath(); c.ellipse(x - r * .36, y + r * .34, r * .25, r * .13, -.5, 0, 6.29); c.fillStyle = '#7a2a58'; c.fill();
  shellPath(c, x, y, r); c.stroke();
  c.lineWidth = r * .09; c.beginPath(); c.ellipse(x - r * .42, y + r * .3, r * .4, r * .25, -.5, 0, 6.29); c.stroke();
}
function drawShell(c, w, h) { drawShellAt(c, w * .5, h * .52, w * .4); }
function glassPath(c, x, y, r) { c.beginPath(); c.moveTo(x - r * .62, y - r); c.lineTo(x + r * .62, y - r); c.lineTo(x + r * .48, y + r); c.lineTo(x - r * .48, y + r); c.closePath(); }
function drawGlassAt(c, x, y, r) {
  c.lineJoin = c.lineCap = 'round'; glassPath(c, x, y, r); c.fillStyle = 'rgba(214,238,255,.92)'; c.fill();
  c.fillStyle = '#ffffff'; c.beginPath(); c.roundRect(x - r * .4, y - r * .7, r * .16, r * 1.3, r * .08); c.fill();
  c.strokeStyle = '#8fc2ea'; c.lineWidth = r * .08; c.beginPath(); c.moveTo(x - r * .5, y + r * .78); c.lineTo(x + r * .5, y + r * .78); c.stroke();
  c.strokeStyle = PLUM; c.lineWidth = r * .16; glassPath(c, x, y, r); c.stroke();
}
function drawGlass(c, w, h) { drawGlassAt(c, w * .5, h * .5, h * .4); }
function bottlePath(c, x, y, r) {
  c.beginPath(); c.moveTo(x - r * .16, y - r * 1.2); c.lineTo(x + r * .16, y - r * 1.2); c.lineTo(x + r * .16, y - r * .6);
  c.quadraticCurveTo(x + r * .5, y - r * .4, x + r * .5, y); c.lineTo(x + r * .5, y + r * .9); c.quadraticCurveTo(x + r * .5, y + r, x + r * .4, y + r); c.lineTo(x - r * .4, y + r);
  c.quadraticCurveTo(x - r * .5, y + r, x - r * .5, y + r * .9); c.lineTo(x - r * .5, y); c.quadraticCurveTo(x - r * .5, y - r * .4, x - r * .16, y - r * .6); c.closePath();
}
function drawBottleAt(c, x, y, r) {
  c.lineJoin = c.lineCap = 'round'; bottlePath(c, x, y, r); c.fillStyle = '#8fe0b4'; c.fill();
  c.fillStyle = '#d6ffe9'; c.beginPath(); c.roundRect(x - r * .36, y - r * .1, r * .13, r * .8, r * .06); c.fill();
  c.strokeStyle = PLUM; c.lineWidth = r * .13; bottlePath(c, x, y, r); c.stroke();
}
// waves: what he hears. big = the "whole ocean" (a tall curling wave and a tiny boat)
function drawWaves(big) {
  return (c, w, h) => {
    c.lineJoin = c.lineCap = 'round';
    const crest = (y, a, col, ph) => { c.beginPath(); c.moveTo(w * .04, h * .96); for (let i = 0; i <= 40; i++) { const x = w * (.04 + .92 * i / 40); c.lineTo(x, y + Math.sin(i / 40 * 6.283 * 2 + ph) * a); } c.lineTo(w * .96, h * .96); c.closePath(); c.fillStyle = col; c.fill(); c.strokeStyle = PLUM; c.lineWidth = w * .028; c.stroke(); };
    if (big) {
      c.beginPath(); c.moveTo(w * .06, h * .9); c.bezierCurveTo(w * .1, h * .3, w * .4, h * .04, w * .7, h * .12); c.bezierCurveTo(w * .92, h * .2, w * .9, h * .46, w * .72, h * .44);
      c.bezierCurveTo(w * .8, h * .34, w * .7, h * .26, w * .6, h * .32); c.bezierCurveTo(w * .46, h * .42, w * .5, h * .7, w * .94, h * .9); c.closePath();
      c.fillStyle = SEA; c.fill(); c.strokeStyle = PLUM; c.lineWidth = w * .028; c.stroke();
      c.fillStyle = '#ffffff'; for (const [x, y, r] of [[.7, .12, .05], [.8, .17, .045], [.86, .26, .04], [.84, .36, .035], [.76, .42, .03], [.6, .1, .04]]) { c.beginPath(); c.arc(w * x, h * y, w * r, 0, 6.29); c.fill(); c.stroke(); }
      c.fillStyle = '#e8553a'; c.beginPath(); c.moveTo(w * .7, h * .66); c.lineTo(w * .9, h * .66); c.lineTo(w * .86, h * .74); c.lineTo(w * .74, h * .74); c.closePath(); c.fill(); c.lineWidth = w * .018; c.stroke();
      c.fillStyle = '#ffffff'; c.beginPath(); c.moveTo(w * .8, h * .5); c.lineTo(w * .8, h * .65); c.lineTo(w * .9, h * .65); c.closePath(); c.fill(); c.stroke();
      crest(h * .8, h * .035, SEAD, 0);
    } else { crest(h * .42, h * .1, '#8fd0ff', 0); crest(h * .6, h * .09, SEA, 1.6); crest(h * .78, h * .07, SEAD, 3.4); }
  };
}
function drawMark(ch, col) {
  return (c, w, h) => { c.lineJoin = 'round'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .84}px "Arial Black", "Inter", sans-serif`;
    c.strokeStyle = PLUM; c.lineWidth = 36; c.strokeText(ch, w / 2, h * .54); c.fillStyle = col; c.fillText(ch, w / 2, h * .54); };
}
function drawCross(c, w, h) { c.lineCap = 'round'; for (const [lw, col] of [[w * .26, PLUM], [w * .15, '#ff4a3f']]) { c.strokeStyle = col; c.lineWidth = lw; c.beginPath(); c.moveTo(w * .2, h * .2); c.lineTo(w * .8, h * .8); c.moveTo(w * .8, h * .2); c.lineTo(w * .2, h * .8); c.stroke(); } }
// three arcs: a sound on its way
function arcs(c, x, y, r, dir, n, lw, col, a0 = .55) {
  c.lineCap = 'round';
  for (let k = 0; k < n; k++) { const rr = r * (.4 + k * .3); for (const [w2, cc] of [[lw * 2.1, PLUM], [lw, col]]) { c.strokeStyle = cc; c.lineWidth = w2; c.beginPath(); c.arc(x, y, rr, dir - a0, dir + a0); c.stroke(); } }
}
function drawArcs(c, w, h) { arcs(c, w * .12, h * .5, w * .78, 0, 3, w * .05, '#ffffff'); }
function drawGull(c, w, h) {
  c.lineJoin = c.lineCap = 'round';
  for (const [lw, col] of [[w * .13, PLUM], [w * .07, '#ffffff']]) { c.strokeStyle = col; c.lineWidth = lw; c.beginPath(); c.moveTo(w * .08, h * .5); c.quadraticCurveTo(w * .28, h * .12, w * .5, h * .56); c.quadraticCurveTo(w * .72, h * .12, w * .92, h * .5); c.stroke(); }
}
// the diagram of the story. kind 0: the hum around you goes into the shell, rings inside it and comes out bigger (p = how
// much bigger); 1: blowing over an empty bottle; 2: every hollow (shell, glass, bottle) rings; 3: a silent room, the shell
// is silent too (p = 1: nothing left). ph = time.
function drawMech(c, w, h, kind, p, ph) {
  c.lineJoin = c.lineCap = 'round';
  c.fillStyle = CREAM; c.strokeStyle = PLUM; c.lineWidth = 14; c.beginPath(); c.roundRect(10, 10, w - 20, h - 20, 36); c.fill(); c.stroke();
  const K = Math.round(kind), pul = .5 + .5 * Math.sin(ph * 14);
  const inner = (x, y, r, a) => { c.strokeStyle = '#ff7a2a'; c.lineWidth = r * .11; c.beginPath(); for (let i = 0; i <= 24; i++) { const u = i / 24; c.lineTo(x - r * .6 + u * r * 1.2, y + Math.sin(u * 6.283 * 1.5 + ph * 16) * r * .3 * a); } c.stroke(); };
  if (K === 0) {
    const sx = w * .5, sy = h * .56, r = h * .27;
    // the hum: small, thin arcs coming in from the left
    for (let i = 0; i < 3; i++) { const u = (ph * .9 + i / 3) % 1, x = lerpN(w * .06, w * .27, u); c.globalAlpha = Math.sin(Math.PI * u); arcs(c, x - h * .1, h * (.3 + i * .22), h * .13, 0, 2, h * .014, '#7fa0d8', .5); } c.globalAlpha = 1;
    drawShellAt(c, sx, sy, r);
    inner(sx + r * .12, sy - r * .1, r * .62, .5 + .5 * p);
    // what comes out: big arcs toward the ear on the right
    const big = lerpN(.5, 1, p);
    for (let i = 0; i < 2; i++) { const u = (ph * .9 + i / 2) % 1; c.globalAlpha = .35 + .65 * Math.sin(Math.PI * u); arcs(c, w * .6 + u * w * .05, sy, h * .34 * big, 0, 3, h * (.018 + .022 * p), '#ff7a2a', .62); } c.globalAlpha = 1;
    // the ear
    const ex = w * .9, ey = sy; c.fillStyle = '#ffffff'; c.strokeStyle = PLUM; c.lineWidth = h * .028;
    c.beginPath(); c.ellipse(ex, ey, h * .1, h * .17, 0, 0, 6.29); c.fill(); c.stroke();
    c.lineWidth = h * .022; c.beginPath(); c.arc(ex + h * .012, ey - h * .02, h * .075, 2.2, 5.2); c.stroke(); c.beginPath(); c.arc(ex + h * .02, ey + h * .03, h * .03, 1.6, 4.6); c.stroke();
  } else if (K === 1) {
    const bx = w * .5, by = h * .58, r = h * .3;
    drawBottleAt(c, bx, by, r); inner(bx, by + r * .4, r * .7, .6 + .4 * pul);
    // the breath across its mouth
    c.strokeStyle = '#7fa0d8'; c.lineWidth = h * .022;
    for (let i = 0; i < 3; i++) { const u = (ph * 1.6 + i / 3) % 1, x = lerpN(w * .1, bx - r * .3, u), y = by - r * 1.3 + (i - 1) * h * .045; c.globalAlpha = Math.sin(Math.PI * u); c.beginPath(); c.moveTo(x - w * .05, y); c.lineTo(x + w * .03, y); c.stroke(); } c.globalAlpha = 1;
    c.fillStyle = '#ffffff'; c.strokeStyle = PLUM; c.lineWidth = h * .026; c.beginPath(); c.ellipse(w * .1, by - r * 1.25, h * .09, h * .1, 0, 0, 6.29); c.fill(); c.stroke();
    c.beginPath(); c.ellipse(w * .155, by - r * 1.22, h * .022, h * .03, 0, 0, 6.29); c.fillStyle = PLUM; c.fill();
    // the note it sings
    for (let i = 0; i < 2; i++) { const u = (ph * .9 + i / 2) % 1; c.globalAlpha = .35 + .65 * Math.sin(Math.PI * u); arcs(c, w * .64 + u * w * .05, by - r * .5, h * .3, -.25, 3, h * .034, '#ff7a2a', .6); } c.globalAlpha = 1;
  } else if (K === 2) {
    const y = h * .6, r = h * .2;
    [[w * .2, 0], [w * .5, 1], [w * .8, 2]].forEach(([x, k]) => {
      const a = .5 + .5 * Math.sin(ph * 14 + k * 2.1);
      if (k === 0) drawShellAt(c, x, y, r); else if (k === 1) drawGlassAt(c, x, y, r); else drawBottleAt(c, x, y + r * .1, r * .95);
      inner(x + (k ? 0 : r * .1), y + (k === 2 ? r * .45 : k === 0 ? -r * .1 : 0), r * (k === 1 ? .6 : .55), .5 + .5 * a);
      arcs(c, x, y - r * (k === 2 ? 1.25 : 1.05), r * (.55 + .2 * a), -Math.PI / 2, 2, h * .024, '#ff7a2a', .7);
    });
  } else {
    // a room with padded walls: no sound gets in, and the shell falls silent
    const x0 = w * .14, y0 = h * .2, x1 = w * .86, y1 = h * .88;
    c.fillStyle = '#c9d2f2'; c.strokeStyle = PLUM; c.lineWidth = h * .028; c.beginPath(); c.roundRect(x0, y0, x1 - x0, y1 - y0, 14); c.fill(); c.stroke();
    c.fillStyle = '#8d9bd6'; c.lineWidth = h * .012;
    for (let i = 0; i < 10; i++) { const xa = lerpN(x0, x1, i / 10), xb = lerpN(x0, x1, (i + 1) / 10); for (const [yy, d] of [[y0, 1], [y1, -1]]) { c.beginPath(); c.moveTo(xa, yy); c.lineTo((xa + xb) / 2, yy + d * h * .075); c.lineTo(xb, yy); c.closePath(); c.fill(); c.stroke(); } }
    for (let i = 0; i < 6; i++) { const ya = lerpN(y0, y1, i / 6), yb = lerpN(y0, y1, (i + 1) / 6); for (const [xx, d] of [[x0, 1], [x1, -1]]) { c.beginPath(); c.moveTo(xx, ya); c.lineTo(xx + d * h * .075, (ya + yb) / 2); c.lineTo(xx, yb); c.closePath(); c.fill(); c.stroke(); } }
    // the hum stops at the wall
    for (const [x, d] of [[w * .015, 0], [w * .985, Math.PI]]) { c.globalAlpha = .9; arcs(c, x, h * .54, h * .12, d, 2, h * .014, '#7fa0d8', .5); } c.globalAlpha = 1;
    const sx = w * .5, sy = h * .58, r = h * .19;
    drawShellAt(c, sx, sy, r);
    if (p < 1) { c.globalAlpha = 1 - p; inner(sx + r * .12, sy - r * .1, r * .62, .5); arcs(c, sx + r * 1.2, sy, r * .8, 0, 2, h * .022, '#ff7a2a', .6); c.globalAlpha = 1; }
    else { c.fillStyle = PLUM; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `900 ${h * .12}px "Arial Black", sans-serif`; c.fillText('. . .', sx + r * 1.75, sy - r * .5); }
  }
}

// ---------------------------------------------------------------- SAHİL
const HP = { x: -.28, z: -.5 }, AP = { x: 1.12, z: -1.05 }, CRATE = V(.48, 0, -1.4), M = { x: -3.1, z: .2 };
const SUNPOS = V(-2.9, 5.6, -15.5), SUNDIR = V(2.0, -9, 6.6).normalize();
const SH1 = V(.02, .09, -.2), SH2 = V(.14, .16, -.25);
function canvasTex(w, h, draw, rep) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); }
  return t;
}
function buildSahil(scene) {
  const g = new THREE.Group(); scene.add(g);
  // sand: a pale warm flat with ripples and specks
  const sand = canvasTex(512, 512, (c, w, h) => {
    c.fillStyle = '#f6dfae'; c.fillRect(0, 0, w, h); const r = rng(7);
    for (let i = 0; i < 260; i++) { c.fillStyle = r() < .5 ? '#e6c88e' : '#fff0cc'; c.beginPath(); c.arc(r() * w, r() * h, 1.5 + r() * 2.5, 0, 6.29); c.fill(); }
    c.strokeStyle = '#e2c288'; c.lineWidth = 3; c.lineCap = 'round';
    for (let i = 0; i < 9; i++) { const x = r() * w, y = r() * h, l = 50 + r() * 70; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + l / 2, y - 10, x + l, y); c.stroke(); }
  }, [5, 4]);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(26, 14), painted(sand)); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 1); g.add(fl);
  // the sea: bands of blue with pale crests, a strip of foam that breathes on the shore
  const seaT = canvasTex(512, 512, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#2f7fd0'); gr.addColorStop(1, '#58c2ec'); c.fillStyle = gr; c.fillRect(0, 0, w, h); const r = rng(11);
    c.lineCap = 'round';
    for (let i = 0; i < 26; i++) { const y = (i + .5) / 26 * h, x = r() * w, l = 60 + r() * 120; c.strokeStyle = i % 3 ? '#9fdcff' : '#ffffff'; c.lineWidth = 2 + (y / h) * 4; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + l / 2, y - 7, x + l, y); c.stroke(); }
  }, [4, 1]);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(60, 14), new THREE.MeshBasicMaterial({ map: seaT })); sea.rotation.x = -Math.PI / 2; sea.position.set(0, .02, -10.4); g.add(sea);
  const wet = new THREE.Mesh(new THREE.PlaneGeometry(60, 1.1), flat('#d9c08a')); wet.rotation.x = -Math.PI / 2; wet.position.set(0, .012, -3.1); wet.userData.noShadow = true; g.add(wet);
  dyn.foam = new THREE.Mesh(new THREE.PlaneGeometry(60, .34), new THREE.MeshBasicMaterial({ color: '#ffffff' })); dyn.foam.rotation.x = -Math.PI / 2; dyn.foam.position.set(0, .03, -3.4); g.add(dyn.foam);
  // the sky, the sun (the light of the set), far hills, a sail
  const skyT = canvasTex(1024, 512, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#5f86d8'); gr.addColorStop(.62, '#a8cbf4'); gr.addColorStop(1, '#ffe9c8'); c.fillStyle = gr; c.fillRect(0, 0, w, h);
    const sx = (SUNPOS.x + 35) / 70 * w, sy = (16.5 - SUNPOS.y) / 18 * h, sg = c.createRadialGradient(sx, sy, 6, sx, sy, 150); sg.addColorStop(0, 'rgba(255,240,196,.95)'); sg.addColorStop(1, 'rgba(255,240,196,0)'); c.fillStyle = sg; c.fillRect(0, 0, w, h);
    const cloud = (x, y, s) => { c.fillStyle = '#ffffff'; c.beginPath(); for (let k = 0; k < 6; k++) c.arc(x + (k - 2.5) * s * .5, y + Math.sin(k * 2.1) * s * .14, s * (.4 + .1 * Math.sin(k * 3.3)), 0, 6.29); c.fill(); c.fillRect(x - s * 1.3, y, s * 2.6, s * .4); };
    cloud(590, 250, 26); cloud(640, 170, 20); cloud(400, 200, 18); cloud(520, 110, 16);
  });
  const sky = new THREE.Mesh(new THREE.PlaneGeometry(70, 18), new THREE.MeshBasicMaterial({ map: skyT })); sky.position.set(0, 7.5, -17.5); g.add(sky);
  const sun = new THREE.Mesh(new THREE.SphereGeometry(.7, 24, 16), new THREE.MeshBasicMaterial({ color: HDR(2.5, 2.0, 1.15) })); sun.position.copy(SUNPOS); g.add(sun);
  for (const [x, s, col] of [[-9, 3.2, '#6f9ad0'], [-5.4, 2.2, '#86aede'], [8.5, 3.6, '#6f9ad0'], [12, 2.4, '#86aede']]) { const hill = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), new THREE.MeshBasicMaterial({ color: col })); hill.scale.set(s * 1.9, s * .55, 1); hill.position.set(x, 0, -17); g.add(hill); }
  const boat = new THREE.Group(); boat.position.set(2.6, .12, -11.5); g.add(boat); dyn.boat = boat;
  const hull = new THREE.Mesh(new THREE.BoxGeometry(1.1, .26, .4), new THREE.MeshBasicMaterial({ color: '#e8553a' })); boat.add(hull);
  const sailS = new THREE.Shape(); sailS.moveTo(0, 0); sailS.lineTo(0, 1.25); sailS.lineTo(.72, 0); sailS.closePath();
  const sail = new THREE.Mesh(new THREE.ShapeGeometry(sailS), new THREE.MeshBasicMaterial({ color: '#ffffff', side: THREE.DoubleSide })); sail.position.set(-.1, .2, 0); boat.add(sail);
  // the beach umbrella and a towel (far left), cool rocks (far right)
  const UM = V(-7.4, 0, -1.6);
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(.035, .035, 2.3, 10), flat('#f1ece2')); pole.position.set(UM.x, 1.15, UM.z); pole.rotation.z = .08; g.add(pole);
  for (let k = 0; k < 8; k++) { const sl = new THREE.Mesh(new THREE.ConeGeometry(1.25, .5, 8, 1, false, k / 8 * 6.283, 6.283 / 8), flat(k % 2 ? '#e8553a' : '#f6efe0', { side: THREE.DoubleSide })); sl.position.set(UM.x - .1, 2.35, UM.z); sl.rotation.z = .08; g.add(sl); }
  const towel = new THREE.Mesh(new THREE.BoxGeometry(1.1, .03, 1.9), flat('#3fb6a8')); towel.position.set(UM.x + .3, .016, UM.z + .9); towel.rotation.y = .2; g.add(towel);
  for (const [x, z, r, col] of [[3.5, -2.3, .7, '#8a9cc8'], [4.5, -2.0, .46, '#a3b2d8'], [2.9, -2.6, .34, '#93a3cc'], [4.0, -1.3, .24, '#b3bfe0']]) { const p = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 0), flat(col)); p.position.set(x, r * .5, z); p.rotation.set(x, z, x * z); g.add(p); }
  // the fisherman's corner: a crate with his glass on it, a bucket, a rod stuck in the sand
  const cr = new THREE.Mesh(new THREE.BoxGeometry(.5, .46, .42), painted(woodTex({ base: '#c08a52', plank: 128 }))); cr.position.set(CRATE.x, .23, CRATE.z); cr.rotation.y = .15; g.add(cr);
  dyn.glass3 = new THREE.Mesh(new THREE.CylinderGeometry(.062, .05, .17, 16), new THREE.MeshBasicMaterial({ color: '#dff2ff' })); dyn.glass3.position.set(CRATE.x + .04, .55, CRATE.z + .02); g.add(dyn.glass3);
  const bk = new THREE.Mesh(new THREE.CylinderGeometry(.19, .15, .32, 18), flat('#3f6fb8')); bk.position.set(1.85, .16, -1.55); g.add(bk);
  const bh = new THREE.Mesh(new THREE.TorusGeometry(.17, .012, 6, 20, Math.PI), flat('#d8dcec')); bh.position.set(1.85, .32, -1.55); g.add(bh);
  const rodA = V(1.75, 0, -1.9), rodB = V(1.2, 2.5, -3.6), rd = rodB.clone().sub(rodA);
  const rod = new THREE.Mesh(new THREE.CylinderGeometry(.012, .026, rd.length(), 6), flat('#7a5644')); rod.position.copy(rodA).addScaledVector(rd, .5); rod.quaternion.setFromUnitVectors(V(0, 1, 0), rd.clone().normalize()); g.add(rod);
  const line = new THREE.Mesh(new THREE.CylinderGeometry(.004, .004, 2.5, 4), new THREE.MeshBasicMaterial({ color: '#f4f6ff' })); line.position.set(rodB.x, rodB.y - 1.25, rodB.z); g.add(line);
  // little shells and a starfish on the sand
  for (const [x, z, col] of [[-1.2, .3, '#ffb8a8'], [.9, .5, '#fff0d8'], [-.9, -1.3, '#ffd0c0'], [1.9, -.3, '#ffb8a8'], [-2.0, -.7, '#fff0d8'], [-3.9, -.4, '#ffd0c0'], [-2.5, .9, '#ffb8a8']]) { const s = new THREE.Mesh(new THREE.ConeGeometry(.05, .1, 7), flat(col)); s.position.set(x, .03, z); s.rotation.set(1.3, x * 3, 0); g.add(s); }
  const L = new THREE.Group();
  L.add(new THREE.HemisphereLight('#cfe0ff', '#f0d2a8', 1.5));
  const key = new THREE.DirectionalLight('#ffe2b0', 2.4); key.position.copy(V(0, 0, -.6).addScaledVector(SUNDIR, -11)); key.target.position.set(0, 0, -.6);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: .5, far: 24 }); key.shadow.bias = -.0006; key.shadow.normalBias = .02; key.shadow.radius = 3;
  L.add(key); L.add(key.target);
  const fill = new THREE.DirectionalLight('#b9c8ff', .7); fill.position.set(1.5, 3, 8); fill.target.position.set(0, 1, -2); L.add(fill); L.add(fill.target);
  scene.add(L);
  shadows(g);
  glow(scene, SUNPOS.toArray(), '#ffe2a0', 4.6, .36);
}

// ---------------------------------------------------------------- CAST
const HERO = { hair: '#3a2a24', cloth: '#e8553a', collar: true };
export const LOOK = {
  kahraman: { ...HERO, height: 1.7 },
  kahramanS: { ...HERO, body: 'sit', height: 1.2 },
  amca: { mustache: '#f1eef6', hair: '#dcdce8', hat: 'kulah', hatColor: '#2f4f9a', cloth: '#f2c23a', buttons: '#3a4066', pocket: true, bodyW: 236, headW: 286, headH: 258, height: 1.78 },
};

// ---------------------------------------------------------------- CAMERA
const SHOT = {
  hook: { pos: [-.02, 1.4, 1.95], look: [-.02, 1.33, -.5], fov: 46 },
  ear: { pos: [.12, 1.5, .5], look: [-.04, 1.46, -.5], fov: 40 },
  face: { pos: [-.46, 1.48, 1.35], look: [-.3, 1.44, -.5], fov: 40 },
  wide: { pos: [.3, 1.35, 4.2], look: [.3, 1.02, -1], fov: 50 },
  wideIn: { pos: [-.05, 1.36, 2.7], look: [-.08, 1.2, -.5], fov: 46 },
  amca: { pos: [1.4, 1.5, 1.55], look: [1.27, 1.47, -1.05], fov: 42 },
  two: { pos: [.4, 1.45, 4.3], look: [.4, 1.2, -1], fov: 50 },
  twoIn: { pos: [.42, 1.42, 3.7], look: [.42, 1.22, -1], fov: 48 },
  mech: { pos: [M.x, 1.3, 4.0], look: [M.x, 1.2, .2], fov: 46 },
  world: { pos: [.25, 1.6, 5.2], look: [.25, 1.45, -1], fov: 52 },
};
function cameraPath() {
  const t = W;
  const keys = [
    // hook: the shell on his ear -> the shell -> his face
    { t: 0, ...SHOT.hook, creep: .4, drift: .03 },
    { t: t('neden') + .1, dur: .2, move: 'whip', ...SHOT.ear, creep: .34, drift: .015 },
    { t: t('sesi') + .12, dur: .2, move: 'whip', ...SHOT.face, creep: .34, drift: .015 },
    { t: t('Bakın') + .16, dur: .3, move: 'whip', ...SHOT.wide, creep: .22, drift: .03 },
    { t: t('içinde') + .1, dur: .6, ...SHOT.wideIn, creep: .2, drift: .02 },
    // three tries, each one bigger
    { t: t('Balıkçı') + .1, dur: .28, move: 'whip', ...SHOT.amca, creep: .3, drift: .02 },
    { t: t('Daha') + .1, dur: .3, move: 'whip', ...SHOT.two, creep: .2, drift: .02 },
    { t: t('Sonra') + .1, dur: .6, ...SHOT.twoIn, creep: .14, drift: .012 },
    // the turn: the fisherman falls silent; the shell and the bottle
    { t: t('Çünkü') + .12, dur: .28, move: 'whip', ...SHOT.amca, creep: .34, drift: .02 },
    { t: t('kabuk', 3) - .04, dur: .3, move: 'whip', ...SHOT.mech, creep: .025, drift: .004 },
    // the world around him, and the loop: the first frame again
    { t: t('Yani') + .1, dur: .3, move: 'whip', ...SHOT.world, creep: .16, drift: .02 },
    { t: t('yine', 2) + .08, dur: .26, move: 'whip', ...SHOT.hook, fov: 48.2, creep: .1, drift: 0 },     // creeps in to the first frame's lens: the loop closes
  ];
  const cp = new CamPath(keys, { fps: FPS });
  cp.kick(t('dalgalar') + .05, .4); cp.kick(t('okyanus') + .05, .6); cp.kick(t('deniz', 4) + .05, .8); cp.kick(t('büyütüyor') + .05, .45); cp.kick(t('susar') + .08, .4); cp.kick(t('dünya') + .05, .45);
  return cp;
}

// ---------------------------------------------------------------- SETUP
export async function setup(ctx) {
  W = wordTimes(ctx.words);
  DUR = Math.ceil((ctx.words[ctx.words.length - 1].end + .45) * FPS) / FPS;      // no dead frames after the last word (loop)
  const { scene } = ctx;
  scene.background = new THREE.Color('#7f98d8');
  buildSahil(scene);
  for (const [k, l] of Object.entries(LOOK)) cast[k] = new Toon(l, scene);
  dyn.shell = card(scene, .3, .3, drawShell, { pw: 384 });
  dyn.shellBig = card(scene, .62, .62, drawShell, { pw: 512 });
  dyn.glass = card(scene, .2, .26, drawGlass, { pw: 256 });
  dyn.glassA = card(scene, .2, .26, drawGlass, { pw: 256 });
  dyn.waves = card(scene, .5, .4, drawWaves(false), { pw: 384 });
  dyn.ocean = card(scene, 1.0, .9, drawWaves(true), { pw: 640 });
  dyn.q = [0, 1].map(() => card(scene, .3, .36, drawMark('?', '#ffe15a'), { pw: 256 }));
  dyn.bang = card(scene, .3, .4, drawMark('!', '#ff5a4a'), { pw: 256 });
  dyn.cross = card(scene, .42, .42, drawCross, { pw: 256 });
  dyn.arcs = [0, 1, 2, 3, 4, 5].map(() => card(scene, .34, .34, drawArcs, { pw: 192 }));
  dyn.gull = card(scene, .6, .3, drawGull, { pw: 256 });
  dyn.mech = dynCard(scene, 1.5, 1.0, drawMech, { pw: 768, steps: 30 });
  PF = new Parcaciklar(scene);
  PF.ekle('toz', { t: W('bulup') + .02, pos: [SH1.x, 0, SH1.z + .1], olcek: .7 });
  PF.ekle('kivilcim', { t: W('dünya') + .05, pos: [HP.x + .5, 2.05, HP.z + .1] });
  dyn.cam = cameraPath();
  const cue = (t, type, extra = {}) => CUES.push({ t: +t.toFixed(3), type, ...extra });
  cue(W('neden') + .02, 'rise', { dur: .3 }); cue(W('sesi') + .04, 'rise', { dur: .3 });
  cue(W('Bakın') + .02, 'whoosh'); cue(W('kabuk'), 'lock'); cue(W('bulup') + .02, 'boom'); cue(W('kulağına'), 'rise', { dur: .35 }); cue(W('dalgalar') + .02, 'shimmer');
  cue(W('Balıkçı') + .02, 'whoosh'); cue(W('gülüyor'), 'lock'); cue(W('kalmış') + .1, 'lock');
  cue(W('Daha') + .02, 'whoosh'); cue(W('buluyorsun'), 'lock'); cue(W('koca'), 'rise', { dur: W('okyanus') - W('koca') }); cue(W('okyanus') + .05, 'boom');
  cue(W('Sonra') + .05, 'rise', { dur: .3 }); cue(W('bardağını'), 'lock'); cue(W('kulağına', 2), 'rise', { dur: .35 }); cue(W('yine') + .02, 'lock'); cue(W('deniz', 4) + .05, 'boom'); cue(W('deniz', 4) + .25, 'cut');
  cue(W('Çünkü') + .05, 'rise', { dur: .3 }); cue(W('gelmiyor') + .05, 'lock');
  cue(W('kabuk', 3) - .1, 'rise', { dur: .3 }); cue(W('uğultuyu'), 'wind', { dur: W('çınlatıp') - W('uğultuyu') }); cue(W('çınlatıp'), 'simmer', { dur: W('büyütüyor') + .5 - W('çınlatıp') }); cue(W('büyütüyor') + .05, 'boom');
  cue(W('Tıpkı') + .05, 'rise', { dur: .3 }); cue(W('üfleyince'), 'wind', { dur: W('gibi') - W('üfleyince') }); cue(W('her') + .02, 'lock'); cue(W('güçlendirir') + .1, 'shimmer');
  cue(W('Hiç') + .05, 'rise', { dur: .3 }); cue(W('odada'), 'lock'); cue(W('susar') + .08, 'cut');
  cue(W('Yani') + .02, 'whoosh'); cue(W('değil') + .05, 'lock'); cue(W('etrafındaki', 2), 'wind', { dur: W('dünya') - W('etrafındaki', 2) }); cue(W('dünya') + .05, 'shimmer');
  cue(W('Ama') + .05, 'lock'); cue(W('yine', 2) - .05, 'rise', { dur: .3 }); cue(W('tutuyorsun', 3) + .1, 'boom'); cue(W('tutuyorsun', 3) + .25, 'shimmer');
}

export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'KABUKTA NEDEN DENİZ SESİ?'); }

// ---------------------------------------------------------------- PER FRAME
const DAYB = '#dfdcf4', WARM = '#ffe2a0';
const EAR = [120, 84];                     // the arm that holds something to the ear
function popCard(m, at, t, pos, base = 1, wob = true) {
  const k = t - at; m.visible = k >= 0; if (!m.visible) return 0;
  const s = .15 + .85 * backOut(Math.min(1, k / .2)); m.scale.setScalar(base * s); m.position.copy(pos); m.material.opacity = 1;
  m.rotation.z = wob ? Math.sin(k * 30) * .25 * Math.exp(-k * 7) + Math.sin(k * 2.2) * .04 : 0;
  return s;
}
export function frame(t, ctx) {
  const { cam, env } = ctx;
  const cp = dyn.cam.apply(cam, t);
  PF.guncelle(t);
  for (const c of Object.values(cast)) c.hide();
  for (const m of dyn.cards) { m.visible = false; m.quaternion.copy(cam.quaternion); }
  const A = (w, n) => W(w, n) - 2 / FPS;
  const bl = (seed, ...swaps) => blinkAt(t, seed, swaps, FPS);
  const grade = [1.0, 1.0, 1.02], face = [1, .985, .97], tint = face.map((v, i) => v / grade[i]);
  const H = cast.kahraman, HS = cast.kahramanS, AM = cast.amca;
  const lit = { lit: -1, shade: DAYB, rim: { color: WARM, a: .3 } };
  dyn.foam.position.z = -3.42 + .1 * Math.sin(t * 1.5); dyn.boat.position.x = 2.6 - t * .02; dyn.boat.rotation.z = Math.sin(t * 1.3) * .04;
  // ---- the beats
  const hookEnd = A('Bakın'), tBend = A('kabuk'), tPick = W('bulup'), tEar1 = A('kulağına'), tWave1 = A('dalgalar');
  const tB2 = A('Daha'), tPick2 = A('buluyorsun'), tEar2 = A('bu'), tOcean = A('koca');
  const tB3 = A('Sonra'), tTake = A('bardağını'), tEar3 = A('kulağına', 2), tWave3 = A('yine'), tStun = A('deniz', 4);
  const tBreak = A('Çünkü'), tMech = W('kabuk', 3) - .18, tWorld = A('Yani') + .02, tBack = W('yine', 2) - .05;
  const hook = t < hookEnd, mech = t >= tMech && t < tWorld, loop = t >= tBack;
  let focus = V(HP.x, 1.4, HP.z);
  // ---- the hero (standing): the shell, the bigger shell, the glass
  if (!mech) {
    let hx = HP.x, hp = { expr: 'surprised', mouth: .22, look: -.25, lookY: .25, gazeX: -.4, gazeY: .6, brow: .9, armL: [16, 10], armR: EAR,
      blink: bl(1, A('neden'), A('sesi'), A('sahilde'), tBend, tEar1, tWave1, tB2, tOcean, tB3, tEar3, tStun, A('değil'), A('dünya'), A('Ama')) };
    let held = null, heldAt = 0, heldBase = 1;                    // what is on his ear
    const worldBeat = t >= tWorld && !loop;
    if (hook || loop) { held = dyn.shell; if (t > A('sesi') && hook) hp = { ...hp, expr: 'worried', mouth: .1, look: 0, lookY: 0, gazeX: .7, gazeY: 0, brow: 1 }; }
    else if (t < tB2) {                                            // beat 1: he finds a shell
      if (t < tBend) hp = { ...hp, expr: 'smile', mouth: 0, look: .3, lookY: -.4, gazeX: .3, gazeY: -1, brow: .3, armR: [16, 10] };
      else if (t < tEar1) { const k = ramp(t, tBend, tBend + .16) * (1 - ramp(t, tPick, tPick + .16)); hp = { ...hp, expr: 'grin', look: .35, lookY: -.6, gazeY: -1, brow: .6, lean: 26 * k, armR: [lerpN(16, 40, k), lerpN(10, -20, k)] }; }
      else { held = dyn.shell; heldAt = tEar1; hp = t < tWave1 ? { ...hp, expr: 'surprised', mouth: 0, look: -.2, lookY: .15, gazeX: -.3, gazeY: .5, brow: .5 } : { ...hp, expr: 'grin', look: -.1, lookY: .2, brow: 1, armL: [150, 24], bob: -Math.abs(Math.sin((t - tWave1) * 11)) * 6 * Math.exp(-(t - tWave1) * 2.2) }; }
    } else if (t < tB3) {                                          // beat 2: a bigger one: a whole ocean
      if (t < tPick2) hp = { ...hp, expr: 'smile', mouth: 0, look: .35, lookY: -.5, gazeY: -1, brow: .4, armR: [16, 10] };
      else if (t < tEar2) { const k = ramp(t, tPick2, tPick2 + .16) * (1 - ramp(t, tEar2 - .16, tEar2)); hp = { ...hp, expr: 'grin', look: .35, lookY: -.6, gazeY: -1, brow: .7, lean: 26 * k, armR: [lerpN(16, 40, k), lerpN(10, -20, k)], armL: [lerpN(16, 40, k), -20 * k] }; }
      else { held = dyn.shellBig; heldAt = tEar2; hp = t < tOcean ? { ...hp, expr: 'surprised', mouth: 0, look: -.2, lookY: .15, gazeX: -.3, gazeY: .5, brow: .5 } : { ...hp, expr: 'surprised', mouth: .55, look: -.1, lookY: .35, brow: 1, armL: [150, 26 + 10 * Math.sin(t * 22)], bob: Math.sin(t * 30) * 3, lean: -4 }; }
    } else if (t < tWorld) {                                       // beat 3: the fisherman's empty glass
      hx = lerpN(HP.x, HP.x + .22, ramp(t, tB3, tB3 + .3));
      if (t < tTake) hp = { ...hp, expr: 'smug', mouth: 0, look: .6, lookY: -.2, gazeX: .8, gazeY: -.5, brow: .5, lid: .25, armR: [16, 10] };
      else if (t < tEar3) { const k = ramp(t, tTake, tTake + .18); hp = { ...hp, expr: 'grin', look: .6, lookY: -.2, gazeX: .8, brow: .6, armR: [lerpN(16, 78, k), lerpN(10, 6, k)] }; }
      else { held = dyn.glass; heldAt = tEar3; hp = t < tWave3 ? { ...hp, expr: 'surprised', mouth: 0, look: -.2, lookY: .15, gazeX: -.3, gazeY: .5, brow: .5 } : { ...hp, expr: 'surprised', mouth: .5, look: .1, lookY: .1, gazeX: .6, brow: 1, armL: [150, 24], bob: t < tStun + .5 ? Math.sin(t * 30) * 3 : 0 }; }
    } else if (worldBeat) {                                        // the world around him
      held = dyn.shell; heldAt = tWorld - 1;
      hp = t < A('değil') ? { ...hp, expr: 'surprised', mouth: 0, look: -.3, lookY: .2, gazeX: -.3, gazeY: .5, brow: .5 } : t < A('dünya') ? { ...hp, expr: 'surprised', mouth: .3, look: Math.sin((t - A('değil')) * 5) * .6, lookY: .3, brow: 1 } : { ...hp, expr: 'grin', look: -.1, lookY: .3, brow: 1, armL: [150, 24] };
      if (t > A('Ama')) hp = { ...hp, expr: 'smug', mouth: 0, look: .3, lookY: 0, gazeX: .6, lid: .2, brow: .6, armL: [16, 10] };
    }
    H.show(); H.place(hx, 0, HP.z, cam, tint); H.draw({ ...hp, ...lit }); H.castFrom(SUNDIR, true);
    const hand = H.hand(1) || V(hx + .25, 1.45, HP.z), earP = V(hx + .34, 1.47, HP.z + .06);
    dyn.glass3.visible = t < tTake || t >= tWorld;
    if (held) {
      const big = held === dyn.shellBig, gl = held === dyn.glass;
      const p = earP.clone().add(V(big ? .13 : gl ? -.02 : .02, big ? .05 : .02, big ? .02 : 0));
      const s = popCard(held, hook || loop ? -1 : heldAt, t, p, hook ? 1 + .04 * Math.sin(t * 9) : 1, false);
      if (s) held.rotation.z = gl ? 1.35 : (hook ? Math.sin(t * 24) * .04 : 0);
    }
    // the shell on the sand, then in his hand
    if (!hook && t < tEar1 && t > A('sahilde')) { const up = ramp(t, tPick, tPick + .14); popCard(dyn.shell, A('sahilde'), t, t < tPick ? SH1 : SH1.clone().lerp(hand, up), 1, false); if (t < tPick) dyn.shell.rotation.z = .5; }
    if (t >= tB2 && t < tEar2) { const up = ramp(t, tPick2 + .1, tEar2); popCard(dyn.shellBig, tB2, t, SH2.clone().lerp(hand, up), lerpN(.8, 1, up), false); dyn.shellBig.rotation.z = .5 * (1 - up); }
    if (t >= tTake && t < tEar3) { const up = ramp(t, tTake + .12, tEar3); popCard(dyn.glass, -1, t, V(CRATE.x + .04, .57, CRATE.z + .04).lerp(hand, up), 1, false); dyn.glass.rotation.z = 1.35 * up; }
    // what he hears
    const wv = (at, pos, base) => { const s = popCard(dyn.waves, at, t, pos, base); if (s) { dyn.waves.position.y += Math.sin(t * 7) * .012; dyn.waves.rotation.z += Math.sin(t * 5) * .05; } };
    if (hook) wv(-1, earP.clone().add(V(.3, .1, .02)), .5 + .03 * Math.sin(t * 9));
    else if (loop) wv(tBack + .12, earP.clone().add(V(.3, .1, .02)), .5);
    else if (t >= tWave1 && t < tB2) wv(tWave1, V(hx + .6, 1.98, HP.z), .9);
    else if (t >= tWave3 && t < tWorld) wv(tWave3, V(hx + .1, 2.2, HP.z), 1.1);
    if (t >= tOcean && t < tB3) { const s = popCard(dyn.ocean, tOcean, t, V(hx + .52, 2.3, HP.z - .1), 1.0); if (s) { dyn.ocean.rotation.z += Math.sin(t * 4) * .03; dyn.ocean.position.y += Math.sin(t * 6) * .015; } }
    // "not the sea": the world's own hum comes to the shell from every side
    if (worldBeat) {
      if (t > A('deniz', 5) && t < A('etrafındaki', 2)) { wv(A('deniz', 5), V(hx + .72, 2.15, HP.z), .9); if (t > A('değil')) popCard(dyn.cross, A('değil'), t, V(hx + .72, 2.15, HP.z + .03), 1.2); }
      const gp = V(-1.3 + (t - tWorld) * .5, 2.75 + Math.sin(t * 3) * .05, -1.4);
      popCard(dyn.gull, tWorld, t, gp, 1, false); dyn.gull.scale.y = dyn.gull.scale.x * (.75 + .25 * Math.sin(t * 9));
      if (t > A('etrafındaki', 2) && t < A('Ama')) {
        const src = [gp, V(-1.3, .9, -1.6), V(AP.x, 1.55, AP.z), V(.3, 2.6, -1.2), V(-1.5, 1.9, -.6), V(1.3, .6, -.4)];
        dyn.arcs.forEach((m, i) => { const u = ((t - A('etrafındaki', 2)) * 1.5 + i / 6) % 1, p = src[i].clone().lerp(earP, u * .82); m.visible = true; m.position.copy(p); m.scale.setScalar(.55 + .5 * (1 - u)); m.material.opacity = Math.sin(Math.PI * u);
          const d = earP.clone().sub(src[i]).project(cam), o = src[i].clone().project(cam); m.rotation.z = Math.atan2(d.y - o.y, (d.x - o.x) * cam.aspect); });
      }
    }
    focus = V(hx, 1.4, HP.z);
  }
  // ---- the turn: he sits on the sand under the diagram, the shell still on his ear
  if (mech) {
    const kind = t < A('Tıpkı') ? 0 : t < A('her') ? 1 : t < A('Hiç') ? 2 : 3;
    let hp = { expr: 'surprised', mouth: .12, look: 0, lookY: .55, gazeY: 1, brow: .6, armL: [34, -96], armR: EAR, blink: bl(4, A('uğultuyu'), A('büyütüyor'), A('Tıpkı'), A('çıkan'), A('her'), A('güçlendirir'), A('Hiç'), A('susar')) };
    if (t > A('büyütüyor') && kind === 0) hp = { ...hp, brow: 1, mouth: .45, bob: Math.sin(t * 34) * 3 };
    if (kind === 1) hp = { ...hp, expr: 'smile', mouth: 0, brow: .8 };
    if (kind === 2) hp = { ...hp, expr: 'grin', brow: .9, armL: [150, 24] };
    if (kind === 3) hp = t < A('susar') ? { ...hp, expr: 'worried', brow: .7 } : { ...hp, expr: 'surprised', mouth: .35, brow: 1, lookY: .2, gazeX: .8, gazeY: 0 };
    HS.show(); HS.place(M.x, 0, M.z, cam, tint); HS.draw({ ...hp, ...lit }); HS.castFrom(SUNDIR, true);
    const earS = V(M.x + .3, .98, M.z + .06);
    popCard(dyn.shell, -1, t, earS, 1, false);
    if (kind === 3 && t > A('susar')) popCard(dyn.q[0], A('susar'), t, V(M.x + .58, 1.2, M.z + .02), .8);
    const p = kind === 0 ? ramp(t, A('çınlatıp'), A('büyütüyor') + .15) : kind === 3 ? ramp(t, A('kabuk', 4), A('susar') + .05) : 0;
    dyn.mech.userData.set(kind, p, t);
    const t0 = [tMech + .1, A('Tıpkı'), A('her'), A('Hiç')][kind];
    const s = popCard(dyn.mech, t0, t, V(M.x, 1.9, M.z), 1, false); if (s) dyn.mech.rotation.z = Math.sin(t * 1.7) * .012;
    focus = V(M.x, 1.3, M.z);
  }
  // ---- the fisherman: each time he laughs harder; at the turn he falls silent
  {
    let ap = { expr: 'smug', look: -.6, lid: .3, armL: [16, 10], armR: [16, 10], blink: bl(2, A('neden'), A('kabuk'), A('Balıkçı'), A('İçinde', 2), tB2, tOcean, tB3, tStun, tBreak, A('gelmiyor'), tWorld, A('Ama')) };
    const lf = (amp, sp = 12) => ({ expr: 'laugh', laughMarks: Math.min(1, amp), mouth: .5 + .5 * Math.abs(Math.sin(t * sp)), bob: -Math.abs(Math.sin(t * sp)) * 9 * amp });
    if (t >= hookEnd && t < A('Balıkçı')) ap = { ...ap, expr: t > tEar1 ? 'grin' : 'smug', look: -.7, lid: t > tEar1 ? 0 : .3, brow: t > tEar1 ? .5 : 0 };
    if (t >= A('Balıkçı') && t < tB2) { const talk = t > A('İçinde', 2) - .04 && t < W('kalmış') + .5; ap = { ...ap, ...lf(.5), look: -.5, armL: [100, 22 + 8 * Math.sin(t * 12)], ...(talk ? { expr: 'grin', mouth: flap(env, t), bob: 0, brow: .6 } : {}) }; }
    if (t >= tB2 && t < tB3) ap = t < tEar2 ? { ...ap, expr: 'grin', look: -.7, lid: 0, brow: .5 } : { ...ap, ...lf(.85, 13), look: -.7, armL: [100, 24], armR: [30, -100] };
    if (t >= tB3 && t < tStun) ap = { ...ap, ...lf(1.4, 15), look: -.7, tilt: Math.sin(t * 7) * 6, armL: [150, 26 + 16 * Math.sin(t * 15)], armR: [150, 26 - 16 * Math.sin(t * 15)] };
    if (t >= tStun && t < tWorld) ap = t < A('gelmiyor') ? { ...ap, expr: 'surprised', look: -.5, brow: 1, mouth: .35, lid: 0 } : { ...ap, expr: 'worried', look: .1, lookY: .3, gazeX: -.6, gazeY: .6, brow: .8, sweat: 1, lid: 0, mouth: .1, armL: [40, -64], armR: [40, -64] };
    if (t >= tWorld) ap = t < A('Ama') ? { ...ap, expr: 'worried', look: -.6, brow: .7, lid: 0, armL: [40, -64], armR: [40, -64] } : { ...ap, expr: 'surprised', mouth: .3, look: -.2, lookY: .3, gazeY: .6, brow: 1, lid: 0, armL: EAR };
    AM.show(); AM.place(AP.x, 0, AP.z, cam, tint); AM.draw({ ...ap, ...lit }); AM.castFrom(SUNDIR, true);
    if (t >= tStun && t < A('denizden')) popCard(dyn.q[1], tStun + .08, t, t < tBreak + .1 ? V(AP.x - .5, 2.0, AP.z + .02) : V(AP.x + .47, 2.0, AP.z + .02));
    if (t > A('gelmiyor') && t < tMech) { const s = popCard(dyn.waves, A('denizden'), t, V(AP.x + .47, 2.0, AP.z), .62); popCard(dyn.cross, A('gelmiyor'), t, V(AP.x + .47, 2.0, AP.z + .03), .8); }
    else if (t >= A('denizden') && t < tMech) popCard(dyn.waves, A('denizden'), t, V(AP.x + .47, 2.0, AP.z), .62);
    // the last gag: now he listens to his own glass
    if (t > A('Ama') && !loop) { const eh = AM.hand(-1) || V(AP.x - .3, 1.5, AP.z); popCard(dyn.glassA, A('Ama') + .1, t, eh.clone().add(V(-.06, .04, .02)), 1.1, false); dyn.glassA.rotation.z = -1.35; dyn.glass3.visible = false; }
    if ((t >= A('Balıkçı') && t < tB2) || (t >= tBreak && t < tMech)) focus = V(AP.x, 1.5, AP.z);
  }
  const look = { focus: cam.position.distanceTo(focus), coc: 4, range: 3.4, sat: 1.22, lift: [.1, .095, .15], bloom: .8, vignette: .18 };
  look.tint = grade;
  look.blur = cp.moving > .15 ? 12 : 0;
  return look;
}
