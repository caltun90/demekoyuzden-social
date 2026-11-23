// camera.js — the measured camera of the style (STIL_KITABI §2):
//  * the camera never stands still: every hold creeps in (creep %/frame on the lens)
//  * moves between keys are smootherstep glides; 'whip' = a 5-8 frame dash rendered with motion blur
//  * 'cut' = a hard cut (use at most one or two per short)
//  * kicks = impact shakes that flip sign every frame and decay over 7 frames
import * as THREE from 'three';

export const smoother = x => x <= 0 ? 0 : x >= 1 ? 1 : x * x * x * (x * (x * 6 - 15) + 10);
const whipEase = x => x <= 0 ? 0 : x >= 1 ? 1 : (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

// keys: [{ t, pos:[x,y,z], look:[x,y,z], fov, roll?, move?:'glide'|'whip'|'cut', dur?, creep? }]
//   move/dur describe how the camera ARRIVES at this key (starting at t - dur).
export class CamPath {
  constructor(keys, { fps = 30, creep = .25, drift = .12 } = {}) { this.k = keys; this.fps = fps; this.creep = creep; this.drift = drift; this.kicks = []; }
  // holds also truck sideways (measured: the reference camera pans in ~86 % of frames)
  _drifted(a, i, t) {
    const p = new THREE.Vector3(...a.pos), L = new THREE.Vector3(...a.look);
    const right = L.clone().sub(p).cross(new THREE.Vector3(0, 1, 0)).normalize();
    const sp = (a.drift ?? this.drift) * (i % 2 ? -1 : 1) * Math.min(1, p.distanceTo(L) / 4);
    const off = right.multiplyScalar(sp * Math.max(0, t - a.t));
    this._lookOff = off.clone().multiplyScalar(.85);            // truck: the view slides, not only orbits
    return p.add(off);
  }
  kick(t, amp = 1) { this.kicks.push({ t, amp }); return this; }
  // returns { pos, look, fov, roll, speed01 } ; speed01 ~ how fast we are moving (for motion blur decisions)
  at(t) {
    const K = this.k;
    let i = 0; while (i + 1 < K.length && K[i + 1].t <= t) i++;
    const a = K[i], b = K[i + 1];
    let pos = this._drifted(a, i, t), look = new THREE.Vector3(...a.look).add(this._lookOff), fov = a.fov, roll = a.roll || 0, moving = 0;
    let holdStart = a.t;
    if (b && b.move !== 'cut') {
      const dur = b.dur ?? 1, t0 = b.t - dur;
      if (t >= t0) {
        pos = this._drifted(a, i, t0); look = new THREE.Vector3(...a.look).add(this._lookOff);
        const x = (t - t0) / dur, e = b.move === 'whip' ? whipEase(x) : smoother(x);
        if (b.move === 'whip' && pos.distanceTo(new THREE.Vector3(...b.pos)) > 30) {
          // whip PAN between two far sets: spin away inside set A, spin in inside set B (motion blur hides the swap)
          const first = x < .5, k = first ? (x / .5) ** 2 : ((1 - x) / .5) ** 2, ang = (first ? 1 : -1) * k * 75 * Math.PI / 180;
          const P = first ? pos : new THREE.Vector3(...b.pos), Lk = first ? look : new THREE.Vector3(...b.look);
          const d = Lk.clone().sub(P).applyAxisAngle(new THREE.Vector3(0, 1, 0), ang);
          return this._fin(t, P, P.clone().add(d), first ? this._crept(a, t0) : b.fov, 0, 1);
        }
        // creep accumulated during the hold continues smoothly into the glide
        const fa = this._crept(a, t0);
        pos.lerp(new THREE.Vector3(...b.pos), e); look.lerp(new THREE.Vector3(...b.look), e);
        fov = fa + (b.fov - fa) * e; roll = roll + ((b.roll || 0) - roll) * e;
        moving = b.move === 'whip' ? Math.sin(Math.PI * x) : 0;
        return this._fin(t, pos, look, fov, roll, moving);
      }
    }
    fov = this._crept(a, t);
    return this._fin(t, pos, look, fov, roll, moving);
  }
  _crept(a, t) { const c = a.creep ?? this.creep, f = Math.max(0, (t - a.t) * this.fps); return a.fov * Math.pow(1 - c / 100, f); }
  _fin(t, pos, look, fov, roll, moving) {
    let sx = 0, sy = 0;
    for (const k of this.kicks) {
      const f = Math.round((t - k.t) * this.fps);
      if (f >= 0 && f < 7) { const d = (1 - f / 7) * k.amp * .05 * (f % 2 ? -1 : 1); sx += d; sy += d * .6; }
    }
    return { pos, look, fov, roll: roll + sx * 20, shake: [sx, sy], moving };
  }
  apply(cam, t) {
    const s = this.at(t);
    cam.position.copy(s.pos); cam.position.x += s.shake[0]; cam.position.y += s.shake[1];
    cam.up.set(0, 1, 0); cam.lookAt(s.look);
    if (s.roll) cam.rotateZ(s.roll * Math.PI / 180);
    cam.fov = s.fov; cam.updateProjectionMatrix();
    return s;
  }
}
