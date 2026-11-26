// parcacik.js — three.quarks (MIT) parçacık efektleri, kare kare kesin.
// Video parça parça ve farklı makinelerde render edildiği için gerçek zamanlı simülasyon kullanılamaz: her efekt kendi
// başlangıç saatinden itibaren sabit 1/60 sn adımlarla ve tohumlu rastgele sayıyla yeniden hesaplanır. Böylece aynı t
// her makinede aynı kareyi verir (hareket bulanıklığı alt kareleri ve paralel parçalar dahil).
//
// Kullanım (story.js):
//   import { Parcaciklar } from '/engine/src/parcacik.js';
//   setup:  fx = new Parcaciklar(scene);
//           fx.ekle('konfeti', { t: W('kazandın'), pos: [0, 1.6, 0] });
//           fx.ekle('toz', { t: W('düştü') + .05, pos: [x, 0, z], olcek: 1.2 });
//           fx.ekle('kivilcim', { t: W('fikir'), pos: [x, 2.1, z] });          // ampul, fikir, "aha" anı
//           fx.ekle('parilti', { t: W('altın'), pos: [x, 1, z], sure: 2 });     // sürekli ışıltı (sure sn boyunca)
//           fx.ekle('duman', { t: W('yanan'), pos: [x, 1, z], sure: 3 });
//   frame:  fx.guncelle(t);      (story.frame(t) içinde, kamerayı ayarladıktan sonra)
// Seçenekler: t (başlangıç, sn), pos [x,y,z] (m), olcek (1), sure (sürekli efektlerde yayma süresi, sn),
//             renkler (['#hex', ...], yalnız konfeti/parilti), tohum (aynı yerde iki efekt farklı görünsün), yon ([x,y,z] fışkırma yönü)
// Parçacıklar layer 1'de çizilir (karakterlerle aynı katman; dünya mürekkep çizgisi almaz).
import * as THREE from 'three';
import {
  BatchedRenderer, ParticleSystem, RenderMode, ConstantValue, IntervalValue, ConstantColor, RandomColor, Vector4, Vector3,
  ConeEmitter, SphereEmitter, HemisphereEmitter, ApplyForce, ColorOverLife, SizeOverLife, RotationOverLife, Gradient,
  PiecewiseBezier, Bezier,
} from 'three.quarks';

const DT = 1 / 60;

function mulberry32(a) {
  return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function withRandom(rng, fn) { const R = Math.random; Math.random = rng; try { fn(); } finally { Math.random = R; } }

const TEX = {};
function tex(kind) {
  if (TEX[kind]) return TEX[kind];
  const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  if (kind === 'yumusak') {
    const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.45, 'rgba(255,255,255,.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  } else if (kind === 'kare') {
    g.fillStyle = '#fff'; g.fillRect(14, 4, 36, 56);
  } else if (kind === 'yildiz') {
    g.fillStyle = '#fff'; g.beginPath();
    for (let k = 0; k < 8; k++) { const r = k % 2 ? 6 : 30, a = k * Math.PI / 4; g.lineTo(32 + Math.sin(a) * r, 32 - Math.cos(a) * r); }
    g.closePath(); g.fill();
    const gr = g.createRadialGradient(32, 32, 0, 32, 32, 14); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; TEX[kind] = t; return t;
}
const col = (hex, a = 1) => { const c = new THREE.Color(hex); return new Vector4(c.r, c.g, c.b, a); };
const v3 = hex => { const c = new THREE.Color(hex); return new Vector3(c.r, c.g, c.b); };
function mat(kind, additive) {
  return new THREE.MeshBasicMaterial({ map: tex(kind), transparent: true, depthWrite: false, side: THREE.DoubleSide,
    blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending });
}
const fadeOut = (hex, a0 = 1) => new ColorOverLife(new Gradient([[v3(hex), 0], [v3(hex), 1]], [[a0, 0], [a0, .7], [0, 1]]));

// Hazır efektler. s = ölçek. Her biri ParticleSystem parametreleri + emitter yönü döndürür.
const PRESET = {
  konfeti: (s, o) => ({
    duration: .2, looping: false, worldSpace: true,
    startLife: new IntervalValue(1.6, 2.6), startSpeed: new IntervalValue(3.5 * s, 6.5 * s), startSize: new IntervalValue(.035 * s, .07 * s),
    startRotation: new IntervalValue(0, 6.28),
    startColor: (o.renkler || ['#FF4D6D', '#FFC83D', '#3DD6FF', '#7CFF6B', '#B57BFF', '#FF9F43']).length > 1
      ? new RandomColor(col(o.renkler?.[0] || '#FF4D6D'), col(o.renkler?.[1] || '#3DD6FF')) : new ConstantColor(col(o.renkler[0])),
    emissionOverTime: new ConstantValue(0), emissionBursts: [{ time: 0, count: new ConstantValue(Math.round(120 * Math.min(2, s))), cycle: 1, interval: .01, probability: 1 }],
    shape: new ConeEmitter({ radius: .15 * s, angle: .55 }), material: mat('kare', false), renderMode: RenderMode.BillBoard,
    behaviors: [new ApplyForce(new Vector3(0, -1, 0), new ConstantValue(7 * s)), new RotationOverLife(new IntervalValue(-9, 9)),
      new ColorOverLife(new Gradient([[new Vector3(1, 1, 1), 0], [new Vector3(1, 1, 1), 1]], [[1, 0], [1, .75], [0, 1]]))],
    yukari: true, paletten: o.renkler || ['#FF4D6D', '#FFC83D', '#3DD6FF', '#7CFF6B', '#B57BFF', '#FF9F43'],
  }),
  toz: (s) => ({
    duration: .15, looping: false, worldSpace: true,
    startLife: new IntervalValue(.7, 1.3), startSpeed: new IntervalValue(.8 * s, 2 * s), startSize: new IntervalValue(.25 * s, .5 * s),
    startRotation: new IntervalValue(0, 6.28), startColor: new ConstantColor(col('#d8c7a8', .75)),
    emissionOverTime: new ConstantValue(0), emissionBursts: [{ time: 0, count: new ConstantValue(34), cycle: 1, interval: .01, probability: 1 }],
    shape: new HemisphereEmitter({ radius: .25 * s }), material: mat('yumusak', false), renderMode: RenderMode.BillBoard,
    behaviors: [new SizeOverLife(new PiecewiseBezier([[new Bezier(.6, 1.2, 1.7, 2.1), 0]])), new ApplyForce(new Vector3(0, -1, 0), new ConstantValue(1.2 * s)),
      fadeOut('#d8c7a8', .75)],
    yukari: true,
  }),
  kivilcim: (s) => ({
    duration: .1, looping: false, worldSpace: true,
    startLife: new IntervalValue(.35, .8), startSpeed: new IntervalValue(2.5 * s, 5 * s), startSize: new IntervalValue(.05 * s, .1 * s),
    startColor: new ConstantColor(col('#fff1a8')),
    emissionOverTime: new ConstantValue(0), emissionBursts: [{ time: 0, count: new ConstantValue(46), cycle: 1, interval: .01, probability: 1 }],
    shape: new SphereEmitter({ radius: .08 * s }), material: mat('yildiz', true), renderMode: RenderMode.BillBoard,
    behaviors: [new ApplyForce(new Vector3(0, -1, 0), new ConstantValue(5 * s)),
      new ColorOverLife(new Gradient([[v3('#fff6c2'), 0], [v3('#ffb02e'), .5], [v3('#ff5a1f'), 1]], [[1, 0], [1, .6], [0, 1]])),
      new SizeOverLife(new PiecewiseBezier([[new Bezier(1, .9, .6, 0), 0]]))],
  }),
  parilti: (s, o) => ({
    duration: o.sure ?? 2, looping: false, worldSpace: true,
    startLife: new IntervalValue(.5, 1.1), startSpeed: new IntervalValue(0, .25 * s), startSize: new IntervalValue(.08 * s, .2 * s),
    startRotation: new IntervalValue(0, .8), startColor: new ConstantColor(col((o.renkler && o.renkler[0]) || '#ffe9a6')),
    emissionOverTime: new ConstantValue(22), emissionBursts: [],
    shape: new SphereEmitter({ radius: .55 * s }), material: mat('yildiz', true), renderMode: RenderMode.BillBoard,
    behaviors: [new SizeOverLife(new PiecewiseBezier([[new Bezier(0, 1.3, 1.3, 0), 0]])), fadeOut('#ffffff', 1)],
  }),
  duman: (s, o) => ({
    duration: o.sure ?? 2.5, looping: false, worldSpace: true,
    startLife: new IntervalValue(1.4, 2.2), startSpeed: new IntervalValue(.35 * s, .7 * s), startSize: new IntervalValue(.35 * s, .6 * s),
    startRotation: new IntervalValue(0, 6.28), startColor: new ConstantColor(col('#5b5266', .55)),
    emissionOverTime: new ConstantValue(14), emissionBursts: [],
    shape: new ConeEmitter({ radius: .12 * s, angle: .25 }), material: mat('yumusak', false), renderMode: RenderMode.BillBoard,
    behaviors: [new SizeOverLife(new PiecewiseBezier([[new Bezier(.7, 1.3, 1.9, 2.4), 0]])), fadeOut('#5b5266', .55)],
    yukari: true,
  }),
};

export class Parcaciklar {
  constructor(scene) {
    this.scene = scene; this.batch = new BatchedRenderer(); this.batch.layers.set(1); scene.add(this.batch); this.list = [];
  }
  ekle(tur, o = {}) {
    const make = PRESET[tur]; if (!make) throw new Error('bilinmeyen efekt: ' + tur + ' (konfeti, toz, kivilcim, parilti, duman)');
    const s = o.olcek ?? 1, p = make(s, o); const { yukari, paletten } = p; delete p.yukari; delete p.paletten;
    if (paletten && paletten.length > 2) {     // konfeti: paletten her parçacığa rastgele bir renk (iki rengin karışımı değil)
      p.startColor = new ConstantColor(col('#ffffff'));
      p.behaviors.push({ type: 'PaletteColor', initialize: (pt) => { const c = new THREE.Color(paletten[Math.floor(Math.random() * paletten.length)]); pt.startColor.set(c.r, c.g, c.b, 1); pt.color.copy(pt.startColor); },
        update: () => {}, frameUpdate: () => {}, reset: () => {}, clone() { return this; }, toJSON: () => ({}) });
    }
    p.layers = new THREE.Layers(); p.layers.set(1);
    const sys = new ParticleSystem(p);
    const em = sys.emitter; em.position.set(...(o.pos || [0, 1, 0]));
    if (o.yon) { const d = new THREE.Vector3(...o.yon).normalize(); em.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), d); }
    else if (yukari) em.rotation.x = -Math.PI / 2;           // quarks yayıcıları +Z'ye fışkırır; yukarı çevir
    em.layers.set(1); this.scene.add(em); em.updateMatrixWorld(true); this.batch.addSystem(sys);
    const seed = (o.tohum ?? 0) * 7919 + Math.round((o.t || 0) * 1000) + this.list.length * 131 + 17;
    const life = (p.duration || 0) + 3.5;
    const e = { sys, t0: o.t || 0, seed, step: -1, rng: null, life, visible: true };
    sys.pause(); this.list.push(e); return e;
  }
  _reset(e) { e.sys.restart(); e.sys.pause(); e.rng = mulberry32(e.seed); e.step = 0; }
  guncelle(t) {
    for (const e of this.list) {
      const k = Math.floor((t - e.t0) / DT + 1e-6);
      const on = k >= 0 && (t - e.t0) < e.life;
      e.sys.emitter.visible = on;
      if (!on) { if (e.step !== -1) { e.sys.restart(); e.sys.pause(); e.sys.particleNum = 0; e.step = -1; } continue; }
      if (e.step < 0 || k < e.step) this._reset(e);
      withRandom(e.rng, () => { e.sys.play(); while (e.step < k) { e.sys.update(DT); e.step++; } e.sys.pause(); });
    }
    for (const b of this.batch.batches) b.update();          // yalnız çizim tamponları; simülasyon yukarıda yapıldı
  }
}
