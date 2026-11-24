// main.js — loads a story, exposes window.render(t) for frame-exact capture (no Remotion, no realtime clock).
// URL: /engine/index.html?story=is-odasi[&scale=0.5][&nocap=1]
import * as THREE from 'three';
import { Post } from './post.js';
import { groupWords, drawCaption } from './captions.js';

const q = new URLSearchParams(location.search);
const STORY = q.get('story') || 'is-odasi';
const SCALE = parseFloat(q.get('scale') || '1');
const base = `/stories/${STORY}/`;
const story = await import(base + 'story.js');
// ASPECT: '9:16' (Shorts, default) or '16:9' (long horizontal videos)
const LAND = story.ASPECT === '16:9';
const W = Math.round((LAND ? 1920 : 1080) * SCALE), H = Math.round((LAND ? 1080 : 1920) * SCALE);

const glc = document.getElementById('gl'), out = document.getElementById('out');
glc.width = W; glc.height = H; out.width = W; out.height = H;
const renderer = new THREE.WebGLRenderer({ canvas: glc, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;        // post.js refreshes the shadow maps once per frame, in the world pass
const g = out.getContext('2d');

const words = await (await fetch(base + (story.WORDS || 'voice/words.json'))).json();
const env = await (await fetch(base + (story.ENV || 'voice/env.json'))).json().catch(() => []);
const groups = groupWords(words.words);
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(50, W / H, .1, 400);
const ctx = { THREE, scene, cam, renderer, W, H, words: words.words, env, fps: story.FPS || 30 };
await story.setup(ctx);
const post = new Post(renderer, W, H);

function one(t) {
  const look = story.frame(t, ctx) || {};
  post.render(scene, cam, look);
  return look;
}
window.render = (t) => {
  const look = story.frame(t, ctx) || {};
  const n = look.blur ? Math.max(2, Math.round(look.blur)) : 1;
  if (n === 1) { post.render(scene, cam, look); g.globalAlpha = 1; g.drawImage(glc, 0, 0); }
  else {
    // motion blur: average sub-frames across the shutter (180°)
    for (let k = 0; k < n; k++) {
      const tk = t + ((k + .5) / n - .5) * (.5 / ctx.fps);
      one(tk); g.globalAlpha = 1 / (k + 1); g.drawImage(glc, 0, 0);
    }
    g.globalAlpha = 1;
  }
  if (!q.has('nocap') && look.captions !== false) drawCaption(g, groups, t, W, H, LAND ? { y: .86 } : {});
  if (story.overlay) story.overlay(g, t, ctx);
};
// render cost of one frame (sub-frames of motion blur), used by render.mjs --split to balance parallel parts
window.__cost = (t) => { const l = story.frame(t, ctx) || {}; return l.blur ? Math.max(2, Math.round(l.blur)) : 1; };
window.__meta = { DUR: story.DUR, FPS: story.FPS || 30, NAME: story.NAME || STORY, W, H, CUES: story.CUES || [] };
window.__ready = true;
if (!q.has('capture')) { const t0 = performance.now(); const loop = () => { window.render(((performance.now() - t0) / 1000) % story.DUR); requestAnimationFrame(loop); }; loop(); }
