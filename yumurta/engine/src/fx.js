// fx.js — things that are drawn, not lit: glows, smoke, wind ribbons, light shafts. All on layer 1 (no world ink).
import * as THREE from 'three';

// additive that does NOT write alpha (so the composite never darkens the world behind a glow)
export function addBlend(m) {
  m.blending = THREE.CustomBlending; m.blendEquation = THREE.AddEquation;
  m.blendSrc = THREE.SrcAlphaFactor; m.blendDst = THREE.OneFactor;
  m.blendSrcAlpha = THREE.ZeroFactor; m.blendDstAlpha = THREE.OneFactor;
  m.transparent = true; m.depthWrite = false; return m;
}

let _soft;
function softTex() {
  if (_soft) return _soft;
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.35, 'rgba(255,255,255,.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128); _soft = new THREE.CanvasTexture(c); return _soft;
}

export function glow(scene, pos, color = '#ffc070', size = .6, strength = .9) {
  const m = addBlend(new THREE.SpriteMaterial({ map: softTex(), color, opacity: strength }));
  const s = new THREE.Sprite(m); s.position.set(...pos); s.scale.setScalar(size); s.layers.set(1); scene.add(s); return s;
}

// --- smoke: many wisps, each a chain of soft points along a path(u, t) -> [x,y,z] ---
const SMOKE_V = `
attribute float aAlpha; attribute float aSize; varying float vA;
uniform float uScale; uniform float uNear;
void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); vA = aAlpha * smoothstep(uNear * 0.5, uNear, -mv.z); gl_PointSize = aSize * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`;
const SMOKE_F = `
uniform vec3 uColor; varying float vA;
void main(){ vec2 q = gl_PointCoord - 0.5; float d = length(q); float a = smoothstep(0.5, 0.0, d) * vA; if (a < 0.003) discard; gl_FragColor = vec4(uColor, a); }`;

export class Smoke {
  // wisps: [{ path:(u,t)=>[x,y,z], n, size, alpha, seed }]
  // additive: true = specks of light (dust in a beam, sparks) instead of smoke
  constructor(scene, { color = '#3b3442', maxPoints = 6000, H = 1920, additive = false, near = 0 } = {}) {      // near: fade out closer than this (m)
    this.geo = new THREE.BufferGeometry();
    this.pos = new Float32Array(maxPoints * 3); this.a = new Float32Array(maxPoints); this.s = new Float32Array(maxPoints);
    this.geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
    this.geo.setAttribute('aAlpha', new THREE.BufferAttribute(this.a, 1));
    this.geo.setAttribute('aSize', new THREE.BufferAttribute(this.s, 1));
    this.mat = new THREE.ShaderMaterial({ vertexShader: SMOKE_V, fragmentShader: SMOKE_F, transparent: true, depthWrite: false,
      uniforms: { uColor: { value: new THREE.Color(color) }, uScale: { value: H * .9 }, uNear: { value: near } } });
    if (additive) addBlend(this.mat);
    this.pts = new THREE.Points(this.geo, this.mat); this.pts.layers.set(1); this.pts.frustumCulled = false; scene.add(this.pts);
    this.max = maxPoints; this.wisps = [];
  }
  update(t) {
    let k = 0;
    for (const w of this.wisps) {
      if (w.on && !w.on(t)) continue;
      const n = w.n || 40, A = (w.alpha ?? .35) * (w.fade ? w.fade(t) : 1);
      for (let i = 0; i < n && k < this.max; i++) {
        const u = ((i / n) + t * (w.speed ?? .22) + (w.seed || 0) * .137) % 1;     // particles travel along the path
        const p = w.path(u, t, i);
        this.pos[k * 3] = p[0]; this.pos[k * 3 + 1] = p[1]; this.pos[k * 3 + 2] = p[2];
        this.a[k] = A * Math.sin(Math.PI * u) * (u < .12 ? u / .12 : 1);
        this.s[k] = (w.size ?? .25) * (.5 + u * 1.6);
        k++;
      }
    }
    for (let i = k; i < this.max; i++) this.a[i] = 0;
    this.geo.setDrawRange(0, k);
    this.geo.attributes.position.needsUpdate = this.geo.attributes.aAlpha.needsUpdate = this.geo.attributes.aSize.needsUpdate = true;
  }
}

// --- wind ribbons: flat tubes along curves with travelling dashes ---
const RIB_V = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`;
const RIB_F = `
uniform float uT; uniform float uOn; uniform vec3 uColor; varying vec2 vUv;
void main(){
  float x = fract(vUv.x * 3.0 - uT * 0.55);
  float dash = smoothstep(0.0, 0.08, x) * smoothstep(0.62, 0.3, x);
  float edge = smoothstep(0.0, 0.25, vUv.y) * smoothstep(1.0, 0.75, vUv.y);
  float ends = smoothstep(0.0, 0.08, vUv.x) * smoothstep(1.0, 0.85, vUv.x);
  float grow = step(vUv.x, uOn);
  float a = dash * edge * ends * grow * 0.75;
  if (a < 0.01) discard;
  gl_FragColor = vec4(uColor, a);
}`;
export function ribbon(scene, points, { radius = .06, color = '#eaf7ff' } = {}) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
  const geo = new THREE.TubeGeometry(curve, 120, radius, 6, false);
  const mat = new THREE.ShaderMaterial({ vertexShader: RIB_V, fragmentShader: RIB_F, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    uniforms: { uT: { value: 0 }, uOn: { value: 0 }, uColor: { value: new THREE.Color(color) } } });
  const m = new THREE.Mesh(geo, mat); m.layers.set(1); scene.add(m); m.curve = curve; return m;
}

// --- light shaft: a long box with a soft additive gradient, from a window into the room ---
export function shaft(scene, from, to, width = 1.2, color = '#cfe4ff', strength = .18) {
  const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to), len = a.distanceTo(b);
  const c = document.createElement('canvas'); c.width = 8; c.height = 128; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 128); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 8, 128);
  const m = addBlend(new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), color, opacity: strength, side: THREE.DoubleSide }));
  const grp = new THREE.Group();
  for (let k = 0; k < 2; k++) { const p = new THREE.Mesh(new THREE.PlaneGeometry(width, len), m); p.rotation.y = k * Math.PI / 2; p.position.y = -len / 2; p.layers.set(1); grp.add(p); }
  grp.position.copy(a); grp.lookAt(b); grp.rotateX(-Math.PI / 2); grp.children.forEach(ch => ch.layers.set(1)); scene.add(grp); return grp;
}

// --- light beam: an open cone that is bright through its middle and vanishes at its silhouette (no hard edges),
//     strongest at the source and fading along its length. For moonlight through a window, a lamp's cone, a sun shaft.
const BEAM_V = `varying vec3 vN; varying vec3 vV; varying vec2 vUv;
void main(){ vUv = uv; vec4 mv = modelViewMatrix * vec4(position, 1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`;
const BEAM_F = `
uniform vec3 uColor; uniform float uStrength; uniform float uT; varying vec3 vN; varying vec3 vV; varying vec2 vUv;
void main(){
  float f = pow(abs(dot(normalize(vN), normalize(vV))), 1.8);
  float v = clamp(vUv.y, 0.0, 1.0);                                      // an interpolated -1e-8 would make pow() return NaN: a black pixel with a huge bloom
  float along = pow(v, 1.2) * smoothstep(1.0, 0.93, v);
  float streak = 0.74 + 0.26 * sin(vUv.x * 37.7 + sin(vUv.x * 12.6) * 2.0 + uT * 0.3);
  float a = f * along * streak * uStrength;
  if (a < 0.002) discard;
  gl_FragColor = vec4(uColor, a);
}`;
export function beam(scene, from, to, { r0 = .4, r1 = 1.6, color = '#bcd0ff', strength = .25 } = {}) {
  const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to), len = a.distanceTo(b);
  const geo = new THREE.CylinderGeometry(r0, r1, len, 40, 1, true);          // the +y end (v = 1) is the source
  const mat = addBlend(new THREE.ShaderMaterial({ vertexShader: BEAM_V, fragmentShader: BEAM_F, side: THREE.DoubleSide,
    uniforms: { uColor: { value: new THREE.Color(color) }, uStrength: { value: strength }, uT: { value: 0 } } }));
  const m = new THREE.Mesh(geo, mat); m.position.copy(a).lerp(b, .5);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), a.clone().sub(b).normalize());
  m.layers.set(1); m.renderOrder = 4; scene.add(m); return m;
}
