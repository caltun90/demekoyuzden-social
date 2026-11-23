// vista.js — what you see through a window, and walls that have one.
//  * holedWall: a wall with an opening in ONE piece, so the painted stones keep one size all around it
//  * vistaMat:  a painted panorama sampled by view direction (the parallax of a far landscape, no geometry outside)
//  * nightCityTex / dayGardenTex: two panoramas painted in Canvas 2D (no image files)
import * as THREE from 'three';
import { rng, D } from './paint.js';
export { D };          // D('#hex') = the canvas colour that DISPLAYS as that hex (the frame has no sRGB encode)

// The shape lies in local XY (x along the wall, centred; y up from the floor). hole = [x0, y0, x1, y1].
// uv = metres, so set the texture's repeat to 1 / (size of one texture tile in metres).
export function holedWall(w, h, [x0, y0, x1, y1], mat) {
  const sh = new THREE.Shape(); sh.moveTo(-w / 2, 0); sh.lineTo(w / 2, 0); sh.lineTo(w / 2, h); sh.lineTo(-w / 2, h); sh.closePath();
  const p = new THREE.Path(); p.moveTo(x0, y0); p.lineTo(x0, y1); p.lineTo(x1, y1); p.lineTo(x1, y0); p.closePath(); sh.holes.push(p);
  return new THREE.Mesh(new THREE.ShapeGeometry(sh), mat);
}

// The plane behind an opening is not textured by its UVs but by the direction camera -> pixel. So the painting
// slides behind the frame as the camera trucks, like a real far view.
//   yaw = the direction (atan2(x, z), radians) at the centre of the painting; az = its width; el = [bottom, top] (radians).
const VISTA_V = `varying vec3 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const VISTA_F = `
uniform sampler2D map; uniform float yaw; uniform float az; uniform vec2 el; uniform float gain; varying vec3 vW;
void main(){
  vec3 d = normalize(vW - cameraPosition);
  float a = atan(d.x, d.z) - yaw; a = atan(sin(a), cos(a));
  float e = asin(clamp(d.y, -1.0, 1.0));
  vec2 uv = vec2(0.5 - a / az, clamp((e - el.x) / (el.y - el.x), 0.002, 0.998));   // canvas right = screen right
  gl_FragColor = vec4(texture2D(map, uv).rgb * gain, 1.0);        // gain > 1: the bright parts of the view bloom
}`;
export function vistaMat(map, { yaw = 0, az = Math.PI / 2, el = [-.2, .6], gain = 1 } = {}) {
  map.wrapS = THREE.RepeatWrapping; map.wrapT = THREE.ClampToEdgeWrapping; map.anisotropy = 8;
  return new THREE.ShaderMaterial({ vertexShader: VISTA_V, fragmentShader: VISTA_F, uniforms: { map: { value: map }, yaw: { value: yaw }, az: { value: az }, el: { value: new THREE.Vector2(...el) }, gain: { value: gain } } });
}

// a panorama canvas with helpers in degrees: X(r) = right of the centre, Y(e) = elevation, s = px per degree
function pano(w, h, azDeg, el0, el1) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  return { c, g: c.getContext('2d'), w, h, s: w / azDeg, X: r => w * (.5 + r / azDeg), Y: e => h * (1 - (e - el0) / (el1 - el0)) };
}
const eachWrap = (P, r, fn) => { for (const k of [-1, 0, 1]) fn(P.X(r) + k * P.w); };   // draw at r and its copies, so the painting tiles
function finish(P) { const t = new THREE.CanvasTexture(P.c); t.colorSpace = THREE.SRGBColorSpace; return t; }
const INK = 'rgba(16,18,48,.8)';

// Night over old Istanbul, seen from a hill: roofs and cypresses below, water with a moon path, the far shore
// with a tower, a big moon just left of the centre. Width 90°, el = [-10°, 35°].
export function nightCityTex({ w = 4096, h = 2048, seed = 21 } = {}) {
  const P = pano(w, h, 90, -10, 35), { g, X, Y, s } = P, R = rng(seed);
  const H0 = 4.6;                                                   // far shore line (deg): raised, so a low window still shows water
  let gr = g.createLinearGradient(0, Y(35), 0, Y(H0));
  gr.addColorStop(0, D('#0c1250')); gr.addColorStop(.45, D('#1c2f8e')); gr.addColorStop(.8, D('#4257c4')); gr.addColorStop(1, D('#9a86dc'));
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 1500; i++) {                                   // stars
    const x = R() * w, e = H0 + 2 + R() * 30, big = R() < .05, r = (1.2 + R() * 2.2) * (big ? 2 : 1);
    g.globalAlpha = .35 + R() * .65; g.fillStyle = R() < .2 ? D('#ffe6b8') : D('#eef2ff'); g.beginPath(); g.arc(x, Y(e), r, 0, 6.29); g.fill();
    if (big) { g.lineWidth = 2; g.strokeStyle = g.fillStyle; g.beginPath(); g.moveTo(x - r * 3, Y(e)); g.lineTo(x + r * 3, Y(e)); g.moveTo(x, Y(e) - r * 3); g.lineTo(x, Y(e) + r * 3); g.stroke(); }
  }
  g.globalAlpha = 1;
  const MR = -1.5, ME = 11.2, mr = 2.0 * s;                          // the moon
  eachWrap(P, MR, x => {
    const halo = g.createRadialGradient(x, Y(ME), mr * .8, x, Y(ME), mr * 5.5); halo.addColorStop(0, 'rgba(214,226,255,.55)'); halo.addColorStop(.35, 'rgba(170,190,255,.2)'); halo.addColorStop(1, 'rgba(150,170,255,0)');
    g.fillStyle = halo; g.fillRect(x - mr * 6, Y(ME) - mr * 6, mr * 12, mr * 12);
    g.fillStyle = D('#fff6dc'); g.beginPath(); g.arc(x, Y(ME), mr, 0, 6.29); g.fill();
    g.save(); g.clip(); g.fillStyle = D('#e8dcbc'); for (const [dx, dy, rr] of [[-.35, -.25, .28], [.3, .15, .2], [-.1, .45, .16], [.45, -.4, .12], [-.55, .25, .1]]) { g.beginPath(); g.arc(x + dx * mr, Y(ME) + dy * mr, rr * mr, 0, 6.29); g.fill(); }
    g.restore(); g.strokeStyle = D('#2a2f6a'); g.lineWidth = 4; g.globalAlpha = .55; g.beginPath(); g.arc(x, Y(ME), mr, 0, 6.29); g.stroke(); g.globalAlpha = 1;
  });
  for (let i = 0; i < 16; i++) {                                     // thin night clouds, lit from above
    const r = -45 + R() * 90, e = 8 + R() * 18, len = (5 + R() * 9) * s, th = (.5 + R() * .7) * s;
    eachWrap(P, r, x => { for (let k = 0; k < 7; k++) { g.fillStyle = k < 4 ? D('#3a4cae') : D('#7f93e6'); g.globalAlpha = k < 4 ? .5 : .28; g.beginPath(); g.ellipse(x + (R() - .5) * len, Y(e) + (R() - .5) * th - (k < 4 ? 0 : th * .5), len * (.25 + R() * .3), th * (.5 + R() * .5), 0, 0, 6.29); g.fill(); } });
  }
  g.globalAlpha = 1;
  const hill = (base, top, col, k) => {                              // far shore: low hills
    g.fillStyle = col; g.beginPath(); g.moveTo(0, Y(base));
    for (let x = 0; x <= w; x += 8) { const a = x / w * Math.PI * 2; g.lineTo(x, Y(base + (top - base) * (.5 + .28 * Math.sin(a * 3 + k) + .16 * Math.sin(a * 7 + k * 2.1) + .06 * Math.sin(a * 23 + k)))); }
    g.lineTo(w, Y(base)); g.closePath(); g.fill();
  };
  hill(H0 - .3, H0 + 3.2, D('#3d4aa6'), 1.3); hill(H0 - .3, H0 + 2.0, D('#252f80'), 4.1);
  for (let i = 0; i < 700; i++) { g.fillStyle = D('#ffd88a'); g.globalAlpha = .5 + R() * .5; g.fillRect(R() * w, Y(H0 + R() * 1.3), 3 + R() * 3, 3 + R() * 3); }
  g.globalAlpha = 1;
  eachWrap(P, -4.1, x => {                                           // the tower on the far hill
    g.fillStyle = D('#1b2468'); g.strokeStyle = D('#0c1038'); g.lineWidth = 4; g.lineJoin = 'round';
    g.beginPath(); g.ellipse(x, Y(H0 + .6), 3.4 * s, 1.5 * s, 0, Math.PI, 0); g.fill();
    const bw = .42 * s; g.beginPath(); g.rect(x - bw, Y(H0 + 3.9), bw * 2, Y(H0 + .5) - Y(H0 + 3.9)); g.fill(); g.stroke();
    g.beginPath(); g.rect(x - bw * 1.25, Y(H0 + 3.95), bw * 2.5, .22 * s); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(x - bw * 1.05, Y(H0 + 4.1)); g.lineTo(x, Y(H0 + 5.5)); g.lineTo(x + bw * 1.05, Y(H0 + 4.1)); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = D('#ffd88a'); for (const e of [H0 + 3.4, H0 + 2.5, H0 + 1.6]) g.fillRect(x - 5, Y(e), 10, 14);
    for (let i = 0; i < 40; i++) { const dx = (R() - .5) * 6 * s, e = H0 + .15 + R() * 1.1 * (1 - Math.abs(dx) / (3.2 * s)); g.fillRect(x + dx, Y(e), 6, 7); }
  });
  // water with ripples and the moon path
  gr = g.createLinearGradient(0, Y(H0 - .2), 0, Y(-2)); gr.addColorStop(0, D('#4a62c8')); gr.addColorStop(1, D('#172266'));
  g.fillStyle = gr; g.fillRect(0, Y(H0 - .25), w, Y(-10) - Y(H0 - .25));
  for (let i = 0; i < 2600; i++) { const e = H0 - .3 - R() * 6.5, k = (H0 - e) / 6.5; g.strokeStyle = D('#8fa6f2'); g.globalAlpha = .1 + R() * .22; g.lineWidth = 2 + k * 3; const x = R() * w, l = (8 + R() * 40) * (.5 + k); g.beginPath(); g.moveTo(x, Y(e)); g.lineTo(x + l, Y(e)); g.stroke(); }
  eachWrap(P, MR, x => { for (let i = 0; i < 420; i++) { const k = R(), e = H0 - .3 - k * 6.2, sp = (.25 + k * 1.5) * s, l = (6 + R() * 26) * (.6 + k); g.strokeStyle = D('#fff2c4'); g.globalAlpha = (.35 + R() * .6) * (1 - k * .35); g.lineWidth = 2.5 + k * 4; const xx = x + (R() + R() - 1) * sp; g.beginPath(); g.moveTo(xx - l / 2, Y(e)); g.lineTo(xx + l / 2, Y(e)); g.stroke(); } });
  g.globalAlpha = 1;
  for (const [r, e, k] of [[-3.3, 2.9, 1], [1.2, 3.6, .7], [-12, 3.2, .8], [14, 2.6, 1], [25, 3.4, .7], [-27, 2.8, .9]]) eachWrap(P, r, x => {   // small boats with a lantern
    const u = s * .5 * k; g.fillStyle = D('#101848'); g.beginPath(); g.moveTo(x - u, Y(e)); g.quadraticCurveTo(x, Y(e) + u * .5, x + u, Y(e)); g.closePath(); g.fill();
    g.strokeStyle = D('#101848'); g.lineWidth = 3; g.beginPath(); g.moveTo(x, Y(e)); g.lineTo(x, Y(e) - u * 1.3); g.stroke();
    g.fillStyle = D('#b9c6f2'); g.beginPath(); g.moveTo(x + 2, Y(e) - u * 1.25); g.lineTo(x + u * .7, Y(e) - u * .15); g.lineTo(x + 2, Y(e) - u * .15); g.closePath(); g.fill();
    g.fillStyle = D('#ffcf7a'); g.beginPath(); g.arc(x - u * .5, Y(e) - 5, 4.5, 0, 6.29); g.fill();
  });
  // the near hill: roofs, a small mosque, cypresses (darkest, with warm windows)
  const near = D('#161c58'), ink = D('#090c30');
  g.lineJoin = 'round';
  for (let r = -45; r < 45; r += .9 + R() * 1.3) {
    const top = .4 + R() * 1.6, x = X(r), y = Y(top), ww = (.8 + R() * 1.4) * s;
    g.fillStyle = near; g.strokeStyle = ink; g.lineWidth = 4; g.beginPath(); g.rect(x, y, ww, Y(-10) - y); g.fill(); g.stroke();
    g.fillStyle = D('#2a2470'); g.beginPath(); g.moveTo(x - 6, y); g.lineTo(x + ww * .5, y - .45 * s); g.lineTo(x + ww + 6, y); g.closePath(); g.fill(); g.stroke();
    for (let k = 0; k < 3; k++) if (R() < .55) { g.fillStyle = D('#ffc86a'); g.fillRect(x + ww * (.18 + k * .28), y + .3 * s + (R() < .4 ? .5 * s : 0), .14 * s, .2 * s); }
  }
  const cypress = (r, top, wd) => eachWrap(P, r, x => { g.fillStyle = D('#0e1a46'); g.strokeStyle = ink; g.lineWidth = 4; g.beginPath(); g.moveTo(x, Y(top)); g.bezierCurveTo(x + wd * s, Y(top * .5), x + wd * s * .8, Y(-3), x, Y(-10)); g.bezierCurveTo(x - wd * s * .8, Y(-3), x - wd * s, Y(top * .5), x, Y(top)); g.fill(); g.stroke(); });
  for (let i = 0; i < 46; i++) cypress(-45 + R() * 90, 1.8 + R() * 3.2, .3 + R() * .25);
  for (const r of [-5.2, -2.6, 5.1]) cypress(r, 3.6 + R() * 1.4, .42);
  const mosque = (r, k) => eachWrap(P, r, x => {
    const u = s * k; g.fillStyle = near; g.strokeStyle = ink; g.lineWidth = 4;
    g.beginPath(); g.rect(x - 1.5 * u, Y(0) - 1.6 * u, 3 * u, 2 * u + Y(-10) - Y(0)); g.fill(); g.stroke();
    g.beginPath(); g.ellipse(x, Y(0) - 1.6 * u, 1.3 * u, 1.25 * u, 0, Math.PI, 0); g.closePath(); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(x, Y(0) - 2.85 * u); g.lineTo(x, Y(0) - 3.3 * u); g.stroke();
    const mx = x + 2.1 * u, mw = .17 * u, top = Y(0) - 6.4 * u;
    g.beginPath(); g.rect(mx - mw, top, mw * 2, Y(-10) - top); g.fill(); g.stroke();
    g.beginPath(); g.rect(mx - mw * 1.9, top + 1.5 * u, mw * 3.8, .22 * u); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(mx - mw * 1.3, top); g.lineTo(mx, top - 1.1 * u); g.lineTo(mx + mw * 1.3, top); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = D('#ffc86a'); for (let k2 = -1; k2 <= 1; k2++) g.fillRect(x + k2 * .8 * u - .1 * u, Y(0) - 1.1 * u, .2 * u, .42 * u);
  });
  mosque(2.2, 1.25); mosque(-22, .9); mosque(27, 1.0); mosque(-38, .8);
  return finish(P);
}

// A sunny day outside a kitchen window: heaped clouds, far blue mountains, a bay with sails, green hills with a
// village, and the garden right below (fence, flowers, a fruit tree). Horizon at 0°. Width 90°, el = [-22°, 23°].
export function dayGardenTex({ w = 4096, h = 2048, seed = 31 } = {}) {
  const P = pano(w, h, 90, -22, 23), { g, X, Y, s } = P, R = rng(seed);
  let gr = g.createLinearGradient(0, 0, 0, Y(0)); gr.addColorStop(0, D('#2a7de0')); gr.addColorStop(.55, D('#66b6f6')); gr.addColorStop(1, D('#d4f0ff'));
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  const cloud = (r, e, k) => eachWrap(P, r, x => {
    const u = s * k, y = Y(e), blobs = [[-2.2, 0, 1.1], [-1.1, -.8, 1.4], [.2, -1.3, 1.6], [1.5, -.7, 1.3], [2.5, 0, 1.0]];
    g.save(); g.beginPath(); g.rect(x - 5 * u, y - 4 * u, 10 * u, 4 * u + .3 * u); g.clip();
    g.fillStyle = INK; for (const [dx, dy, rr] of blobs) { g.beginPath(); g.arc(x + dx * u, y + dy * u, rr * u + 5, 0, 6.29); g.fill(); }
    g.fillStyle = D('#c6daf4'); for (const [dx, dy, rr] of blobs) { g.beginPath(); g.arc(x + dx * u, y + dy * u, rr * u, 0, 6.29); g.fill(); }
    g.fillStyle = D('#ffffff'); for (const [dx, dy, rr] of blobs) { g.beginPath(); g.arc(x + dx * u - .12 * u, y + dy * u - .24 * u, rr * u * .9, 0, 6.29); g.fill(); }
    g.restore(); g.strokeStyle = INK; g.lineWidth = 5; g.beginPath(); g.moveTo(x - 3.2 * u, y + .3 * u); g.lineTo(x + 3.4 * u, y + .3 * u); g.stroke();
  });
  for (const [r, e, k] of [[-9, 13, 1.5], [-1.5, 8.3, .55], [6, 7.6, .4], [15, 15, 1.7], [-24, 9, 1.2], [30, 8, 1.0], [-38, 15, 1.6], [40, 13, 1.3], [-3, 18.5, .9]]) cloud(r, e, k);
  const ridge = (base, top, col, k1, k2, line = true) => {
    const pts = [];
    for (let x = 0; x <= w; x += 8) { const a = x / w * Math.PI * 2; pts.push([x, Y(base + (top - base) * (.5 + .3 * Math.sin(a * k1 + k2) + .14 * Math.sin(a * (k1 * 2 + 1) + k2 * 1.7) + .06 * Math.sin(a * 19 + k2)))]); }
    g.fillStyle = col; g.beginPath(); g.moveTo(0, h); for (const p of pts) g.lineTo(p[0], p[1]); g.lineTo(w, h); g.closePath(); g.fill();
    if (line) { g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); }
    return x => pts[Math.max(0, Math.min(pts.length - 1, Math.round((((x % w) + w) % w) / 8)))][1];
  };
  ridge(0, 7.5, D('#a9c6f0'), 4, .6, false); ridge(0, 4.8, D('#5e90d2'), 5, 2.2);
  gr = g.createLinearGradient(0, Y(0), 0, Y(-4)); gr.addColorStop(0, D('#8fd8ee')); gr.addColorStop(1, D('#2f9fd6')); g.fillStyle = gr; g.fillRect(0, Y(.05), w, h);   // the bay
  for (let i = 0; i < 900; i++) { g.strokeStyle = '#ffffff'; g.globalAlpha = .25 + R() * .5; g.lineWidth = 3; const x = R() * w, e = -.2 - R() * 3.6; g.beginPath(); g.moveTo(x, Y(e)); g.lineTo(x + 10 + R() * 30, Y(e)); g.stroke(); }
  g.globalAlpha = 1; g.lineJoin = 'round';
  for (const [r, e, k] of [[-3.6, -1.3, 1], [8.5, -.7, .6], [-20, -1.0, .8], [24, -1.5, 1]]) eachWrap(P, r, x => {   // sails
    const u = s * .9 * k, y = Y(e); g.strokeStyle = INK; g.lineWidth = 4;
    g.fillStyle = D('#8a4a2a'); g.beginPath(); g.moveTo(x - u, y); g.lineTo(x + u, y); g.lineTo(x + u * .7, y + u * .32); g.lineTo(x - u * .7, y + u * .32); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = D('#ffffff'); g.beginPath(); g.moveTo(x - .05 * u, y - 1.7 * u); g.lineTo(x + u * .85, y - .12 * u); g.lineTo(x - .05 * u, y - .12 * u); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = D('#f3d9a0'); g.beginPath(); g.moveTo(x - .18 * u, y - 1.3 * u); g.lineTo(x - .18 * u, y - .12 * u); g.lineTo(x - .8 * u, y - .12 * u); g.closePath(); g.fill(); g.stroke();
  });
  // green hills, fields, a village
  const hA = ridge(-3.6, .6, D('#86cc6a'), 3, 1.1);
  for (let i = 0; i < 60; i++) { const x = X(-45 + R() * 90); g.fillStyle = [D('#b8dc6a'), D('#e3d868'), D('#6fbf5a')][i % 3]; g.globalAlpha = .7; const y = hA(x) + (.4 + R() * 1.6) * s, ww = (1.5 + R() * 2.5) * s; g.beginPath(); g.moveTo(x, y); g.lineTo(x + ww, y - .1 * s); g.lineTo(x + ww * .9, y + .55 * s); g.lineTo(x - ww * .1, y + .6 * s); g.closePath(); g.fill(); }
  g.globalAlpha = 1;
  const house = (x, y, u, roof) => {
    g.strokeStyle = INK; g.lineWidth = 4; g.fillStyle = D('#fbf4e4'); g.beginPath(); g.rect(x - u, y - u * 1.1, u * 2, u * 1.1); g.fill(); g.stroke();
    g.fillStyle = roof; g.beginPath(); g.moveTo(x - u * 1.25, y - u * 1.1); g.lineTo(x, y - u * 1.95); g.lineTo(x + u * 1.25, y - u * 1.1); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = D('#4a6fa8'); g.fillRect(x - u * .55, y - u * .8, u * .38, u * .42); g.fillRect(x + u * .2, y - u * .8, u * .38, u * .42);
  };
  const tree = (x, y, u, col = D('#3f9a48')) => { g.strokeStyle = INK; g.lineWidth = 4; g.fillStyle = D('#7a4a2a'); g.fillRect(x - u * .12, y - u * .9, u * .24, u * .9); g.fillStyle = col; g.beginPath(); g.arc(x, y - u * 1.5, u * .85, 0, 6.29); g.fill(); g.stroke(); g.fillStyle = D('#5cb85a'); g.beginPath(); g.arc(x - u * .22, y - u * 1.72, u * .42, 0, 6.29); g.fill(); };
  const cyp = (x, y, u) => { g.strokeStyle = INK; g.lineWidth = 4; g.fillStyle = D('#2f7a44'); g.beginPath(); g.moveTo(x, y - u * 3.2); g.bezierCurveTo(x + u * .7, y - u * 1.6, x + u * .5, y, x, y); g.bezierCurveTo(x - u * .5, y, x - u * .7, y - u * 1.6, x, y - u * 3.2); g.fill(); g.stroke(); };
  for (let i = 0; i < 70; i++) { const x = X(-45 + R() * 90), y = hA(x) + (.2 + R() * 1.4) * s; (R() < .4 ? cyp : tree)(x, y, (.32 + R() * .2) * s); }
  for (const [r, n] of [[5.2, 6], [-14, 4], [22, 5], [-32, 5], [38, 4]]) for (let i = 0; i < n; i++) { const x = X(r + (i - n / 2) * 1.15 + R() * .3), y = hA(x) + (.5 + (i % 2) * .7) * s; house(x, y, (.42 + R() * .12) * s, i % 3 === 1 ? D('#c8762e') : D('#d9553a')); }
  eachWrap(P, 7.4, x => {                                            // a small mosque over the village
    const u = s * .55, y = hA(x) + .1 * s; g.strokeStyle = INK; g.lineWidth = 4; g.fillStyle = D('#f6ead2');
    g.beginPath(); g.rect(x - 1.2 * u, y - 1.3 * u, 2.4 * u, 1.3 * u); g.fill(); g.stroke();
    g.fillStyle = D('#7fb6c8'); g.beginPath(); g.ellipse(x, y - 1.3 * u, 1.05 * u, .95 * u, 0, Math.PI, 0); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = D('#f6ead2'); g.beginPath(); g.rect(x + 1.5 * u, y - 4.2 * u, .3 * u, 4.2 * u); g.fill(); g.stroke();
    g.fillStyle = D('#7fb6c8'); g.beginPath(); g.moveTo(x + 1.4 * u, y - 4.2 * u); g.lineTo(x + 1.65 * u, y - 5.1 * u); g.lineTo(x + 1.9 * u, y - 4.2 * u); g.closePath(); g.fill(); g.stroke();
  });
  const hB = ridge(-8.5, -3.2, D('#5fb252'), 2, 3.4);
  for (let i = 0; i < 46; i++) { const x = X(-45 + R() * 90), y = hB(x) + (.3 + R() * 2.4) * s; (R() < .35 ? cyp : tree)(x, y, (.55 + R() * .35) * s, R() < .3 ? D('#4aa84a') : D('#3a9442')); }
  // the garden below the window
  gr = g.createLinearGradient(0, Y(-8), 0, h); gr.addColorStop(0, D('#58b04a')); gr.addColorStop(1, D('#3f8f3a')); g.fillStyle = gr; g.fillRect(0, Y(-8.4), w, h - Y(-8.4));
  g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); g.moveTo(0, Y(-8.4)); g.lineTo(w, Y(-8.4)); g.stroke();
  g.fillStyle = D('#e6d2a0'); g.beginPath(); for (let x = 0; x <= w; x += 16) g.lineTo(x, Y(-15 + Math.sin(x / w * 44) * 1.2) - .7 * s); for (let x = w; x >= 0; x -= 16) g.lineTo(x, Y(-15 + Math.sin(x / w * 44) * 1.2) + .7 * s); g.closePath(); g.fill(); g.stroke();
  for (let i = 0; i < 1400; i++) { const x = R() * w, e = -8.8 - R() * 13; g.strokeStyle = D(R() < .5 ? '#2f7a34' : '#7fcc5a'); g.globalAlpha = .7; g.lineWidth = 3; g.beginPath(); g.moveTo(x, Y(e)); g.lineTo(x + (R() - .5) * 10, Y(e) - (.18 + R() * .25) * s); g.stroke(); }
  g.globalAlpha = 1;
  for (let i = 0; i < 520; i++) { const x = R() * w, e = -9 - R() * 12.5, rr = (.1 + R() * .1) * s; g.fillStyle = [D('#f04a4a'), D('#ffd84a'), D('#ffffff'), D('#ff8ab8')][i % 4]; g.strokeStyle = INK; g.lineWidth = 2.5; g.beginPath(); g.arc(x, Y(e), rr, 0, 6.29); g.fill(); g.stroke(); g.fillStyle = D('#f4a020'); g.beginPath(); g.arc(x, Y(e), rr * .35, 0, 6.29); g.fill(); }
  g.fillStyle = D('#a8743e'); g.strokeStyle = INK; g.lineWidth = 4;                                   // fence
  for (const e of [-9.6, -11]) { g.beginPath(); g.rect(-9, Y(e), w + 18, .32 * s); g.fill(); g.stroke(); }
  for (let r = -45; r < 45; r += 2.25) { const x = X(r); g.beginPath(); g.moveTo(x - .22 * s, Y(-12.2)); g.lineTo(x - .22 * s, Y(-8.6)); g.lineTo(x, Y(-8.1)); g.lineTo(x + .22 * s, Y(-8.6)); g.lineTo(x + .22 * s, Y(-12.2)); g.closePath(); g.fill(); g.stroke(); }
  for (const r of [11.5, -34, 33]) eachWrap(P, r, x => {             // a fruit tree close to the window
    g.strokeStyle = INK; g.lineWidth = 6; g.fillStyle = D('#8a5a34');
    g.beginPath(); g.moveTo(x - .9 * s, h); g.quadraticCurveTo(x - .2 * s, Y(-6), x - .5 * s, Y(3)); g.lineTo(x + .5 * s, Y(3)); g.quadraticCurveTo(x + .4 * s, Y(-6), x + 1.1 * s, h); g.closePath(); g.fill(); g.stroke();
    const blobs = [[0, 8, 4.2], [-3.4, 6, 3], [3.4, 6.4, 3.1], [-1.8, 11, 3], [2.2, 11.4, 2.9], [0, 4.4, 2.6]];
    g.fillStyle = D('#2f8a3c'); for (const [dx, e, rr] of blobs) { g.beginPath(); g.arc(x + dx * s, Y(e), rr * s, 0, 6.29); g.fill(); g.stroke(); }
    for (const [dx, e, rr] of blobs) { g.beginPath(); g.arc(x + dx * s, Y(e), rr * s - 3, 0, 6.29); g.fill(); }
    g.fillStyle = D('#4fae4c'); for (const [dx, e, rr] of blobs) { g.beginPath(); g.arc(x + (dx - .5) * s, Y(e + .7), rr * s * .62, 0, 6.29); g.fill(); }
    for (let i = 0; i < 26; i++) { const a = R() * 6.28, d = R() * 4.6, fx = x + Math.cos(a) * d * s, fy = Y(8 + Math.sin(a) * d * .8); g.fillStyle = D('#ff8a2a'); g.lineWidth = 3; g.beginPath(); g.arc(fx, fy, .33 * s, 0, 6.29); g.fill(); g.stroke(); g.fillStyle = D('#ffc06a'); g.beginPath(); g.arc(fx - .1 * s, fy - .1 * s, .1 * s, 0, 6.29); g.fill(); }
  });
  return finish(P);
}
