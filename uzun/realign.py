"""Kaydi duraklamalardan kucuk parcalara boler, her parcayi yaziya doker, parcalari satirlara metin benzerligiyle (DP) dagitir.
Sonucu voice/cuts.json'a yazar (ses.py segments() bunu okur).  SYNC_MODEL=gemini-3.1-flash-lite python3 realign.py g1 g2 ...
"""
import sys, os, json, re, difflib
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))   # deponun kokundeki sync.py
import sync
from senaryo import GROUPS, LINES
from ses import silences, norm

SR = 24000


def run(name):
    x, sr = sf.read(f'voice/raw_{name}.wav', dtype='float32')
    g = silences(x, 0.12)
    total = len(x) / sr
    lead = g[0][1] if g and g[0][0] < 0.05 else 0.0
    trail = g[-1][0] if g and g[-1][1] > total - 0.05 else total
    inner = [s for s in g if s[0] > lead + 0.05 and s[1] < trail - 0.05]
    bounds = [lead] + [(a + b) / 2 for a, b in inner] + [trail]
    pieces = list(zip(bounds[:-1], bounds[1:]))
    clips = [x[int(a * sr):int(b * sr)] for a, b in pieces]
    cache = f'voice/pieces_{name}.json'
    if os.path.exists(cache) and json.load(open(cache))['n'] == len(pieces):
        txt = json.load(open(cache))['txt']
    else:
        import time
        for _try in range(4):
            try:
                out = sync.transcribe(clips, sr); break
            except SystemExit as e:
                print('yeniden deneniyor:', str(e)[:80]); time.sleep(15)
        else:
            raise SystemExit('yazi dokumu yapilamadi')
        got = dict((int(m.group(1)), m.group(2).strip()) for m in re.finditer(r'Parca\s*(\d+)\s*:\s*(.*)', out))
        txt = [got.get(i, '') for i in range(len(pieces))]
        json.dump(dict(n=len(pieces), txt=txt), open(cache, 'w'), ensure_ascii=False)
    ids = GROUPS[name]['ids']; L, P = len(ids), len(pieces)
    target = [norm(LINES[i].get('say') or LINES[i]['text']) for i in ids]
    pn = [norm(t) for t in txt]
    INF = 1e9
    # dp[i][j]: ilk i satir, ilk j parca kullanildi
    dp = np.full((L + 1, P + 1), INF); arg = np.zeros((L + 1, P + 1), dtype=int); dp[0][0] = 0
    for i in range(1, L + 1):
        for j in range(i, P + 1):
            best, bk = INF, -1
            for k in range(max(i - 1, j - 14), j):
                if dp[i - 1][k] >= INF: continue
                cand = ' '.join(pn[k:j])
                c = 1 - difflib.SequenceMatcher(None, target[i - 1], cand).ratio()
                if dp[i - 1][k] + c < best: best, bk = dp[i - 1][k] + c, k
            dp[i][j], arg[i][j] = best, bk
    j = P; cuts = []
    for i in range(L, 0, -1):
        k = arg[i][j]; cuts.append((k, j)); j = k
    cuts = cuts[::-1]
    res = [pieces[a][0] for a, _ in cuts] + [pieces[cuts[-1][1] - 1][1]]
    for (a, b), i in zip(cuts, ids):
        r = difflib.SequenceMatcher(None, norm(LINES[i].get('say') or LINES[i]['text']), norm(' '.join(txt[a:b]))).ratio()
        print(('OK ' if r > 0.8 else 'XX ') + f'{i:4s} {r:.2f} | ' + ' '.join(txt[a:b])[:110])
    return [round(float(v), 3) for v in res]


if __name__ == '__main__':
    cuts = json.load(open('voice/cuts.json')) if os.path.exists('voice/cuts.json') else {}
    for name in sys.argv[1:]:
        cuts[name] = run(name)
        json.dump(cuts, open('voice/cuts.json', 'w'))
