// props.js — small 3D things built from code: an oil lamp a character can hold, the striped arch of a mosque.
// They live in the world layer, so they get ink lines, real light and real shadows like the rest of the set.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { D } from './paint.js';
import { addBlend } from './fx.js';

const HDR = (r, g, b) => new THREE.Color().setRGB(r, g, b);      // a colour above 1: it blooms (see post.js)

// ---------- kandil: an enamelled glass mosque lamp on three chains ----------
// profile of the glass, from the foot up to the flared mouth: [radius, y] in metres, y measured from the mouth (0) down
const KANDIL = [[0, -.172], [.03, -.172], [.036, -.16], [.022, -.146], [.05, -.118], [.064, -.085], [.056, -.05], [.036, -.03], [.034, -.022], [.056, 0]];
let _kGeo, _kTex, _fGeo, _hTex;
// the lamp's halo: broad and flat (the reference still shows a third of the lamp's light two lamp-radii away, analiz/isik.md)
function haloTex() {
  if (_hTex) return _hTex;
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  // Brightest in a ring just outside the glass (27 % of the radius), dimmer behind the lamp itself: the bloom already carries
  // the first 20 px, the ring holds the light up between 20 and 40 px, where ours used to fall away (analiz/isik.md).
  // The stops were fitted to the radial profile of the reference bulb; with the base light under it the sum still falls steadily.
  gr.addColorStop(0, 'rgba(255,255,255,.28)'); gr.addColorStop(.2, 'rgba(255,255,255,.34)'); gr.addColorStop(.285, 'rgba(255,255,255,1)'); gr.addColorStop(.45, 'rgba(255,255,255,.5)'); gr.addColorStop(.64, 'rgba(255,255,255,.14)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return _hTex = new THREE.CanvasTexture(c);
}
function kandilGeo() { return _kGeo ||= new THREE.LatheGeometry(KANDIL.map(([r, y]) => new THREE.Vector2(r, y)), 28); }
function flameGeo() { return _fGeo ||= new THREE.LatheGeometry([[0, 0], [.012, .006], [.016, .02], [.011, .042], [.004, .06], [0, .07]].map(([r, y]) => new THREE.Vector2(r, y)), 14); }
function kandilTex() {
  if (_kTex) return _kTex;
  const c = document.createElement('canvas'); c.width = 512; c.height = 256; const g = c.getContext('2d');
  // v runs along the profile: bottom of the canvas = foot, top = mouth. Blue-green glass, lit from inside, gold bands.
  const gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, D('#ffe9a8')); gr.addColorStop(.2, D('#58d0c8')); gr.addColorStop(.45, D('#ffd98a')); gr.addColorStop(.62, D('#ffb85a')); gr.addColorStop(.82, D('#1f8f98')); gr.addColorStop(1, D('#14506a'));
  g.fillStyle = gr; g.fillRect(0, 0, 512, 256);
  for (const [y, h, col] of [[14, 12, '#f0b846'], [84, 9, '#f0b846'], [176, 9, '#f0b846'], [226, 12, '#c8922e']]) { g.fillStyle = D(col); g.fillRect(0, y, 512, h); }
  for (let i = 0; i < 12; i++) {                                           // enamel medallions around the belly
    const x = (i + .5) * 512 / 12;
    g.fillStyle = D(i % 2 ? '#c8372f' : '#243a94'); g.beginPath(); g.ellipse(x, 132, 13, 22, 0, 0, 6.29); g.fill();
    g.fillStyle = D('#fff3c8'); g.beginPath(); g.arc(x, 132, 5, 0, 6.29); g.fill();
    g.fillStyle = D('#243a94'); g.beginPath(); g.arc(x + 21, 50, 5, 0, 6.29); g.fill();
  }
  _kTex = new THREE.CanvasTexture(c); _kTex.colorSpace = THREE.SRGBColorSpace; _kTex.wrapS = THREE.RepeatWrapping; return _kTex;
}
export const kandilParts = { geo: kandilGeo, flame: flameGeo, tex: kandilTex };

// Returns a Group whose ORIGIN is the ring a hand holds; the lamp hangs `chain` metres below it.
//   .flameAt(v)  world position of the flame tip (for smoke)      .flicker(t)  call every frame
//   .light       a warm PointLight at the flame (set castShadow if this lamp is the key light)
//   halo         0..1: a broad soft glow around the glass (a sprite on layer 1), for the lamps the camera comes close to
export function kandil({ chain = .2, s = 1, light = 5, range = 7, decay = 1.6, halo = 0 } = {}) {
  const g = new THREE.Group(), brass = new THREE.MeshLambertMaterial({ color: '#e0a83c', emissive: '#7a5210' });
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.017, .005, 8, 18), brass); ring.rotation.y = Math.PI / 2; g.add(ring);
  const body = new THREE.Group(); body.position.y = -chain; body.scale.setScalar(s); g.add(body);
  const glass = new THREE.Mesh(kandilGeo(), new THREE.MeshBasicMaterial({ map: kandilTex(), color: HDR(1.25, 1.2, 1.1), side: THREE.DoubleSide })); glass.castShadow = true; body.add(glass);
  for (let k = 0; k < 3; k++) {                                            // three chains from the shoulder of the glass to the ring
    const a = k / 3 * Math.PI * 2 + .5, p0 = new THREE.Vector3(Math.cos(a) * .058 * s, -chain - .052 * s, Math.sin(a) * .058 * s), p1 = new THREE.Vector3(0, -.016, 0);
    const len = p0.distanceTo(p1), c = new THREE.Mesh(new THREE.CylinderGeometry(.0026, .0026, len, 5), brass);
    c.position.copy(p0).lerp(p1, .5); c.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), p1.clone().sub(p0).normalize()); g.add(c);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(.008 * s, 8, 6), brass); eye.position.copy(p0); g.add(eye);
  }
  const flame = new THREE.Mesh(flameGeo(), new THREE.MeshBasicMaterial({ color: HDR(3.4, 2.1, .62) })); flame.position.y = -.012; body.add(flame);
  const core = new THREE.Mesh(flameGeo(), new THREE.MeshBasicMaterial({ color: HDR(4.2, 3.7, 2.4) })); core.scale.setScalar(.52); core.position.y = -.008; body.add(core);
  const pl = new THREE.PointLight('#ffb060', light, range, decay); pl.position.y = .05; body.add(pl);
  let hs = null;
  if (halo) { hs = new THREE.Sprite(addBlend(new THREE.SpriteMaterial({ map: haloTex(), color: '#ffb25c', opacity: halo }))); hs.position.y = -.075; hs.scale.setScalar(.62); hs.layers.set(1); body.add(hs); }
  g.light = pl; g.flame = flame; g.body = body; g.halo = hs; g.haloK = 1;      // haloK: turn the halo down in a close-up (it is a real size in the world, so it fills the frame there)
  g.flameAt = (v = new THREE.Vector3()) => flame.localToWorld(v.set(0, .07, 0));
  g.flicker = t => { const f = 1 + .14 * Math.sin(t * 31) * Math.sin(t * 17) + .06 * Math.sin(t * 53); flame.scale.set(1, f, 1); flame.rotation.z = .1 * Math.sin(t * 9.3); core.scale.set(.52, .52 * f, .52); pl.intensity = light * (.92 + .08 * f); if (hs) hs.material.opacity = halo * g.haloK * (.9 + .1 * f); };
  return g;
}

// ---------- the striped arch (alternating red and white stones) ----------
// Local frame: x along the span (centred), y up from the springing line, z = depth (centred).
// Every stone has a chamfered edge (`bevel` metres wide, twice as deep), so two stones meet in a V groove. The ink pass
// draws a line in every groove: the joints of the arch are real geometry, not paint, and stay thin at any distance.
export function voussoirArch({ span = 8, rise = 3, thick = .7, depth = 1, n = 17, colors = ['#b8323a', '#f1e7d2'], bevel = .035 } = {}) {
  const lists = [[], []], P = (a, r) => [(span / 2 + r) * Math.cos(a), (rise + r) * Math.sin(a)];
  for (let k = 0; k < n; k++) {
    const a0 = Math.PI * k / n, a1 = Math.PI * (k + 1) / n, sh = new THREE.Shape(), st = 3;
    for (let i = 0; i <= st; i++) { const [x, y] = P(a0 + (a1 - a0) * i / st, 0); i ? sh.lineTo(x, y) : sh.moveTo(x, y); }
    for (let i = st; i >= 0; i--) { const [x, y] = P(a0 + (a1 - a0) * i / st, thick); sh.lineTo(x, y); }
    sh.closePath();
    const bt = bevel * 2, geo = bevel ? new THREE.ExtrudeGeometry(sh, { depth: depth - 2 * bt, bevelEnabled: true, bevelThickness: bt, bevelSize: bevel, bevelOffset: -bevel, bevelSegments: 1 })
      : new THREE.ExtrudeGeometry(sh, { depth, bevelEnabled: false });
    geo.translate(0, 0, -depth / 2 + (bevel ? bt : 0));
    lists[k % 2].push(geo);
  }
  const g = new THREE.Group();
  lists.forEach((list, i) => { if (!list.length) return; const m = new THREE.Mesh(mergeGeometries(list), new THREE.MeshLambertMaterial({ color: colors[i] })); m.castShadow = m.receiveShadow = true; g.add(m); });
  return g;
}
// The wall above an arch: a rectangle (width × height, bottom edge on the springing line) with the arch cut out of it.
export function spandrel({ width, height, span, rise, thick = .7, mat }) {
  const sh = new THREE.Shape(), rx = span / 2 + thick * .5, ry = rise + thick * .5;
  const a0 = Math.acos(Math.min(1, width / 2 / rx));                       // where the cut meets the side edges
  sh.moveTo(-width / 2, ry * Math.sin(a0));
  for (let i = 1; i <= 40; i++) { const a = Math.PI - a0 - (Math.PI - 2 * a0) * i / 40; sh.lineTo(rx * Math.cos(a), ry * Math.sin(a)); }
  sh.lineTo(width / 2, height); sh.lineTo(-width / 2, height); sh.closePath();
  const m = new THREE.Mesh(new THREE.ShapeGeometry(sh, 24), mat); m.castShadow = m.receiveShadow = true; return m;
}
