// post.js — the look: ink lines on the 3D world, lens blur, character composite, bloom, grade.
// Pipeline per frame (all at output size):
//   1. world (layer 0)            -> rtWorld  (colour + depth texture; the shadow maps are refreshed here)
//   2. world normals (layer 0)    -> rtNormal
//   3. ink pass                   -> rtInk    (black lines from depth jumps + normal creases; 3.4 px near, 2.2 px far,
//                                               creases thinner: the widths measured on the reference, analiz/cizgi.md)
//   4. lens blur (depth based)    -> rtLens
//   5. characters (layer 1) over a depth-only copy of the world -> rtChars (premultiplied)
//   6. composite                  -> rtComp
//   7. bloom: everything BRIGHTER THAN WHITE glows (5 blurred levels; the three wide ones carry most of it and a soft
//      shoulder keeps the core from burning out, because the reference halo is broad and flat: still a third of its
//      strength 40 px from the lamp, analiz/isik.md)
//   8. composite + bloom + grade  -> screen
// Characters carry their own plum outline, so the world ink never touches them.
// The targets are half-float: a flame or a lamp glass is given a colour above 1 (HDR) and only those bloom;
// a white head (1, 1, 1) never does.
import * as THREE from 'three';

const FS_VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

const DEPTH_FN = `
uniform float near; uniform float far;
float linZ(float d){ float z = d * 2.0 - 1.0; return (2.0 * near * far) / (far + near - z * (far - near)); }
`;

const INK_FRAG = `
precision highp float;
varying vec2 vUv;
uniform sampler2D tColor; uniform sampler2D tDepth; uniform sampler2D tNormal;
uniform vec2 res; uniform vec3 inkColor; uniform float inkNear; uniform float inkFar; uniform float inkStrength;
uniform float depthThresh; uniform float normalThresh; uniform float fogInk;
${DEPTH_FN}
void main(){
  vec3 c = texture2D(tColor, vUv).rgb;
  float dc = texture2D(tDepth, vUv).x;
  float z = linZ(dc);
  if (dc >= 0.9999) { gl_FragColor = vec4(c, 1.0); return; }
  float w = mix(inkNear, inkFar, clamp((z - 4.0) / 60.0, 0.0, 1.0));
  vec2 px = w / res;
  vec3 nc = texture2D(tNormal, vUv).xyz * 2.0 - 1.0;
  float e = 0.0;
  for (int i = 0; i < 4; i++) {
    vec2 o = i == 0 ? vec2(px.x, 0.0) : i == 1 ? vec2(-px.x, 0.0) : i == 2 ? vec2(0.0, px.y) : vec2(0.0, -px.y);
    float dn = texture2D(tDepth, vUv + o).x;
    float zn = linZ(dn);
    float dz = (zn - z) / z;                      // only the NEAR side of a depth jump draws (no double lines)
    e = max(e, smoothstep(depthThresh, depthThresh * 2.2, dz));
    vec3 nn = texture2D(tNormal, vUv + o * 0.34).xyz * 2.0 - 1.0;   // a crease is drawn from both sides: a third of the reach each
    e = max(e, smoothstep(normalThresh, normalThresh + 0.25, 1.0 - dot(nc, nn)) * 0.85);
  }
  float far01 = clamp((z - 30.0) / 90.0, 0.0, 1.0);
  float k = e * inkStrength * (1.0 - far01 * fogInk);
  gl_FragColor = vec4(mix(c, inkColor, k), 1.0);
}`;

const LENS_FRAG = `
precision highp float;
varying vec2 vUv;
uniform sampler2D tColor; uniform sampler2D tDepth; uniform vec2 res;
uniform float focus; uniform float cocMax; uniform float range;
${DEPTH_FN}
const int N = 40;
// things NEARER than the focus blur faster and further (a near object at the frame's edge goes properly soft)
float coc(float z){ float d = z - focus; return clamp(abs(d) * (d < 0.0 ? 2.2 : 1.0) / max(range, 0.01), 0.0, d < 0.0 ? 1.7 : 1.0) * cocMax; }
void main(){
  float z = linZ(texture2D(tDepth, vUv).x);
  float r = coc(z);
  if (r < 0.6) { gl_FragColor = texture2D(tColor, vUv); return; }
  vec3 acc = vec3(0.0); float wsum = 0.0;
  for (int i = 0; i < N; i++) {
    float fi = float(i);
    float a = fi * 2.39996;                        // golden-angle spiral
    float rr = sqrt((fi + 0.5) / float(N));
    vec2 o = vec2(cos(a), sin(a)) * rr * r / res;
    float zs = linZ(texture2D(tDepth, vUv + o).x);
    float rs = coc(zs);
    float w = zs < z ? clamp(rs / max(r, 0.001), 0.0, 1.0) : 1.0; // sharp things in front don't bleed
    acc += texture2D(tColor, vUv + o).rgb * w; wsum += w;
  }
  gl_FragColor = vec4(acc / max(wsum, 0.001), 1.0);
}`;

const COMP_FRAG = `
precision highp float;
varying vec2 vUv;
uniform sampler2D tWorld; uniform sampler2D tChars;
void main(){
  vec3 w = texture2D(tWorld, vUv).rgb;
  vec4 ch = texture2D(tChars, vUv);
  gl_FragColor = vec4(w * (1.0 - ch.a) + ch.rgb, 1.0);
}`;

// bright pass: a 4x4 box downsample that keeps only what is above the threshold (soft knee)
const BRIGHT_FRAG = `
precision highp float;
varying vec2 vUv;
uniform sampler2D tColor; uniform vec2 texel; uniform float threshold; uniform float knee;
void main(){
  vec3 c = texture2D(tColor, vUv + texel * vec2(-1.0, -1.0)).rgb + texture2D(tColor, vUv + texel * vec2(1.0, -1.0)).rgb
         + texture2D(tColor, vUv + texel * vec2(-1.0, 1.0)).rgb + texture2D(tColor, vUv + texel * vec2(1.0, 1.0)).rgb;
  c = min(c * 0.25, vec3(12.0));
  float br = max(c.r, max(c.g, c.b));
  float soft = clamp(br - threshold + knee, 0.0, 2.0 * knee); soft = soft * soft / (4.0 * knee + 1e-4);
  gl_FragColor = vec4(c * max(soft, br - threshold) / max(br, 1e-4), 1.0);
}`;
const BLUR_FRAG = `
precision highp float;
varying vec2 vUv;
uniform sampler2D tColor; uniform vec2 dir;
void main(){
  vec3 c = texture2D(tColor, vUv).rgb * 0.227027;
  c += (texture2D(tColor, vUv + dir * 1.3846).rgb + texture2D(tColor, vUv - dir * 1.3846).rgb) * 0.316216;
  c += (texture2D(tColor, vUv + dir * 3.2308).rgb + texture2D(tColor, vUv - dir * 3.2308).rgb) * 0.070270;
  gl_FragColor = vec4(c, 1.0);
}`;

const FINAL_FRAG = `
precision highp float;
varying vec2 vUv;
uniform sampler2D tComp; uniform sampler2D tB0; uniform sampler2D tB1; uniform sampler2D tB2; uniform sampler2D tB3; uniform sampler2D tB4; uniform vec2 res;
uniform float sat; uniform vec3 lift; uniform vec3 gain; uniform float vignette; uniform float contrast;
uniform float flash; uniform vec3 tint; uniform float bloom;
void main(){
  vec3 c = texture2D(tComp, vUv).rgb;
  vec3 b = texture2D(tB0, vUv).rgb * 0.5 + texture2D(tB1, vUv).rgb * 0.8 + texture2D(tB2, vUv).rgb * 1.5 + texture2D(tB3, vUv).rgb * 2.6 + texture2D(tB4, vUv).rgb * 2.8;
  b /= 1.0 + 0.45 * max(b.r, max(b.g, b.b));       // shoulder: a wide halo without a burnt-out core
  c += b * bloom;
  c *= tint;
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(l), c, sat);
  c = (c - 0.5) * contrast + 0.5;
  c = lift + c * (gain - lift);                    // no pure black: the floor is the lift colour
  vec2 q = vUv - 0.5; q.x *= res.x / res.y;
  c *= 1.0 - vignette * smoothstep(0.35, 0.95, length(q) * 1.25);
  c = mix(c, vec3(1.0), flash);
  gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}`;

export class Post {
  constructor(renderer, W, H) {
    this.r = renderer; this.W = W; this.H = H;
    const mk = (depth) => {
      const rt = new THREE.WebGLRenderTarget(W, H, { samples: depth ? 0 : 0, type: THREE.HalfFloatType });
      if (depth) { rt.depthTexture = new THREE.DepthTexture(W, H); rt.depthTexture.type = THREE.UnsignedIntType; }
      return rt;
    };
    this.rtWorld = mk(true); this.rtNormal = mk(true); this.rtInk = mk(false); this.rtLens = mk(false);
    this.rtChars = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
    this.rtChars.depthTexture = new THREE.DepthTexture(W, H); this.rtChars.depthTexture.type = THREE.UnsignedIntType;
    this.rtComp = mk(false);
    // bloom chain: W/4 ... W/64 (two targets per level: blur across, then down)
    this.bl = [4, 8, 16, 32, 64].map(d => { const w = Math.max(2, Math.round(W / d)), h = Math.max(2, Math.round(H / d));
      const t = () => new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, depthBuffer: false }); return { w, h, a: t(), b: t() }; });
    this.normalMat = new THREE.MeshNormalMaterial();
    this.depthOnly = new THREE.MeshBasicMaterial({ colorWrite: false });
    this.fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const quad = (frag, uniforms) => {
      const m = new THREE.ShaderMaterial({ vertexShader: FS_VERT, fragmentShader: frag, uniforms, depthTest: false, depthWrite: false });
      const s = new THREE.Scene(); s.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), m)); return { m, s };
    };
    const res = new THREE.Vector2(W, H);
    this.ink = quad(INK_FRAG, {
      tColor: { value: null }, tDepth: { value: null }, tNormal: { value: null }, res: { value: res },
      near: { value: .1 }, far: { value: 400 }, inkColor: { value: new THREE.Color('#0b0a0c') },
      inkNear: { value: 3.4 * W / 1080 }, inkFar: { value: 2.2 * W / 1080 }, inkStrength: { value: .95 },
      depthThresh: { value: .022 }, normalThresh: { value: .3 }, fogInk: { value: .45 },
    });
    this.lens = quad(LENS_FRAG, {
      tColor: { value: null }, tDepth: { value: null }, res: { value: res }, near: { value: .1 }, far: { value: 400 },
      focus: { value: 5 }, cocMax: { value: 0 }, range: { value: 6 },
    });
    this.comp = quad(COMP_FRAG, { tWorld: { value: null }, tChars: { value: null } });
    this.bright = quad(BRIGHT_FRAG, { tColor: { value: null }, texel: { value: new THREE.Vector2(1 / W, 1 / H) }, threshold: { value: 1.0 }, knee: { value: .12 } });
    this.blur = quad(BLUR_FRAG, { tColor: { value: null }, dir: { value: new THREE.Vector2() } });
    this.final = quad(FINAL_FRAG, {
      tComp: { value: null }, tB0: { value: null }, tB1: { value: null }, tB2: { value: null }, tB3: { value: null }, tB4: { value: null }, res: { value: res }, bloom: { value: .9 },
      sat: { value: 1.12 }, lift: { value: new THREE.Vector3(.055, .045, .09) }, gain: { value: new THREE.Vector3(1, 1, 1) },
      vignette: { value: .22 }, contrast: { value: 1.06 }, flash: { value: 0 }, tint: { value: new THREE.Vector3(1, 1, 1) },
    });
  }
  // look: { focus, coc (px at 1080 wide), range, sat, lift:[r,g,b], vignette, flash, tint:[r,g,b], bloom, bloomAt (threshold) }
  render(scene, cam, look = {}) {
    const r = this.r, sx = this.W / 1080;
    cam.layers.set(0);
    // shadow casters that exist only for the shadow maps (a character's silhouette card): on for the world pass, off after it
    const so = scene.userData.shadowOnly || [], was = so.map(o => o.visible);
    r.shadowMap.needsUpdate = true;
    r.setRenderTarget(this.rtWorld); r.clear(); r.render(scene, cam);
    so.forEach(o => { o.visible = false; });
    const bg = scene.background; scene.background = null; const fog = scene.fog; scene.fog = null;
    scene.overrideMaterial = this.normalMat;
    r.setRenderTarget(this.rtNormal); r.setClearColor(0x8080ff, 1); r.clear(); r.render(scene, cam);
    // characters: depth of the world first (no colour), then layer 1 on a transparent target
    scene.overrideMaterial = this.depthOnly;
    r.setRenderTarget(this.rtChars); r.setClearColor(0x000000, 0); r.clear(); r.render(scene, cam);
    scene.overrideMaterial = null; scene.fog = fog;
    cam.layers.set(1); r.autoClear = false; r.render(scene, cam); r.autoClear = true; cam.layers.set(0);
    scene.background = bg; r.setClearColor(0x000000, 1);
    so.forEach((o, i) => { o.visible = was[i]; });

    const iu = this.ink.m.uniforms;
    iu.tColor.value = this.rtWorld.texture; iu.tDepth.value = this.rtWorld.depthTexture; iu.tNormal.value = this.rtNormal.texture;
    iu.near.value = cam.near; iu.far.value = cam.far;
    if (look.ink != null) iu.inkStrength.value = look.ink;
    r.setRenderTarget(this.rtInk); r.render(this.ink.s, this.fsCam);

    const lu = this.lens.m.uniforms;
    lu.tColor.value = this.rtInk.texture; lu.tDepth.value = this.rtWorld.depthTexture; lu.near.value = cam.near; lu.far.value = cam.far;
    lu.focus.value = look.focus ?? 5; lu.cocMax.value = (look.coc ?? 0) * sx; lu.range.value = look.range ?? 6;
    r.setRenderTarget(this.rtLens); r.render(this.lens.s, this.fsCam);

    const cu = this.comp.m.uniforms; cu.tWorld.value = this.rtLens.texture; cu.tChars.value = this.rtChars.texture;
    r.setRenderTarget(this.rtComp); r.render(this.comp.s, this.fsCam);
    // bloom: bright pass into level 0, then each level = the level above blurred across and down (a free downsample)
    const bu = this.bright.m.uniforms, ku = this.blur.m.uniforms, B = this.bl;
    bu.tColor.value = this.rtComp.texture; bu.threshold.value = look.bloomAt ?? 1.0;
    r.setRenderTarget(B[0].b); r.render(this.bright.s, this.fsCam);
    ku.tColor.value = B[0].b.texture; ku.dir.value.set(1 / B[0].w, 0); r.setRenderTarget(B[0].a); r.render(this.blur.s, this.fsCam);
    ku.tColor.value = B[0].a.texture; ku.dir.value.set(0, 1 / B[0].h); r.setRenderTarget(B[0].b); r.render(this.blur.s, this.fsCam);
    ku.tColor.value = B[0].b.texture; ku.dir.value.set(1 / B[0].w, 0); r.setRenderTarget(B[0].a); r.render(this.blur.s, this.fsCam);
    for (let i = 1; i < B.length; i++) {
      ku.tColor.value = B[i - 1].a.texture; ku.dir.value.set(1 / B[i].w, 0); r.setRenderTarget(B[i].b); r.render(this.blur.s, this.fsCam);
      ku.tColor.value = B[i].b.texture; ku.dir.value.set(0, 1 / B[i].h); r.setRenderTarget(B[i].a); r.render(this.blur.s, this.fsCam);
    }
    const fu = this.final.m.uniforms;
    fu.tComp.value = this.rtComp.texture; fu.tB0.value = B[0].a.texture; fu.tB1.value = B[1].a.texture; fu.tB2.value = B[2].a.texture; fu.tB3.value = B[3].a.texture; fu.tB4.value = B[4].a.texture;
    fu.bloom.value = look.bloom ?? .9;
    fu.sat.value = look.sat ?? 1.12; fu.vignette.value = look.vignette ?? .22; fu.flash.value = look.flash ?? 0;
    fu.contrast.value = look.contrast ?? 1.06;
    const L = look.lift ?? [.055, .045, .09]; fu.lift.value.set(...L);
    const T = look.tint ?? [1, 1, 1]; fu.tint.value.set(...T);
    r.setRenderTarget(null); r.render(this.final.s, this.fsCam);
  }
}
