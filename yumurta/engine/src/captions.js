// captions.js — one word (or a short pair) at a time, synced to the voice (STIL_KITABI §6).
// White, heavy, dark stroke + soft shadow, centred at 70 % of the height.
export function groupWords(words) {
  const out = [];
  for (let i = 0; i < words.length; i++) {
    const w = words[i], n = words[i + 1];
    const bare = w.word.replace(/[^\p{L}\p{N}]/gu, '');
    if (n && bare.length <= 3 && !/[.,:;!?"]$/.test(w.word) && (w.word + ' ' + n.word).length <= 14) {
      out.push({ text: w.word + ' ' + n.word, start: w.start, end: n.end }); i++;
    } else out.push({ text: w.word, start: w.start, end: w.end });
  }
  for (let i = 0; i < out.length; i++) out[i].until = out[i + 1] ? out[i + 1].start : out[i].end + .4;
  return out;
}

export function drawCaption(g, groups, t, W, H, { font = '"Segoe UI Black", "Arial Black", sans-serif', size = 74, y = .70 } = {}) {
  const c = groups.find(c => t >= c.start - .02 && t < c.until);
  if (!c) return;
  const text = c.text.replace(/^"|"$/g, '').replace(/"/g, '');
  const age = t - c.start, pop = age < .07 ? 1.06 - age / .07 * .06 : 1;
  const s = size * Math.min(W, H) / 1080 * pop;
  g.save();
  g.font = `900 ${s}px ${font}`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.miterLimit = 2;
  g.shadowColor = 'rgba(10,6,20,.55)'; g.shadowBlur = s * .18; g.shadowOffsetY = s * .06;
  g.strokeStyle = '#140c1c'; g.lineWidth = s * .2; g.strokeText(text, W / 2, H * y);
  g.shadowColor = 'transparent'; g.fillStyle = '#ffffff'; g.fillText(text, W / 2, H * y);
  g.restore();
}
