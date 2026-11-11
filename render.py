import json, math, random, subprocess, sys, os
import skia
import numpy as np, soundfile as sf

# FMT=v -> 1080x1920 dikey (Reels/TikTok/Shorts), FMT=h -> 1920x1080 yatay (YouTube)
FMT = os.environ.get('FMT', 'v')
W, H = (1080, 1920) if FMT == 'v' else (1920, 1080)
FPS = 30
# yatay: dikey sahne cizimi (x 0-1080, y ART_Y0-ART_Y1) sola yerlesir, altyazi saga
ART_Y0, ART_Y1, ART_DX, ART_DY = 280, 1260, 40, 50
BG = 0xFFFAF3E6
PAPER = 0xFFFFFDF8
INK = 0xFF2B2A28
CORAL = 0xFFEF6A4C
TEAL = 0xFF2E9C8F
YEL = 0xFFFFD45E
MUTE = 0xFF948C7C
WASH_Y = 0xFFFFEFC4
WASH_T = 0xFFD9EFEA
WASH_P = 0xFFF6E3DA

FD = '/usr/share/fonts/truetype/google-fonts/'
TF = {k: skia.Typeface.MakeFromFile(FD + f) for k, f in
      dict(bold='Poppins-Bold.ttf', med='Poppins-Medium.ttf', reg='Poppins-Regular.ttf').items()}

D = json.load(open(os.path.join(os.path.dirname(__file__), 'voice/final.json')))
LN = D['lines']
TOTAL = D['total']
# scene start times
SC = {}
for l in LN:
    SC.setdefault(l['scene'], l['start'] - 0.28)
SC[1] = 0.0
SCENES = sorted(SC)
def scene_span(k):
    i = SCENES.index(k)
    return SC[k], (SC[SCENES[i + 1]] if i + 1 < len(SCENES) else TOTAL)

TITLE = 'Zeigarnik Etkisi'   # yatay formatta etiketin altinda gorunur
HL = {0: ['yarım'], 2: ['tek', 'sen', 'değilsin.'], 3: ['zeigarnik', 'etkisi.'], 5: ['yarıda', 'kesti.'],
      6: ['daha', 'iyi', 'hatırladı.'], 7: ['her', 'zaman', 'bulamadı.'], 8: ['dönmek', 'istiyor.'],
      9: ['açık', 'bir', 'sekme'], 10: ['kapanıyor,'], 11: ['planını', 'yaz.'], 13: ['net', 'bir', 'plan,'],
      15: ['açık', 'sekmeyi']}

# ---------- helpers ----------
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(u): u = clamp(u); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def back(u):
    u = clamp(u); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
def pop(t, a, d=0.28): return back(seg(t, a, a + d))

class St: boil = 0; n = 0
def rng():
    St.n += 1
    return random.Random(St.boil * 7919 + St.n * 104729)

def paint(color=INK, w=9, fill=False, alpha=1.0):
    p = skia.Paint(AntiAlias=True, Color=color)
    if fill:
        p.setStyle(skia.Paint.kFill_Style)
    else:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if alpha < 1: p.setAlphaf(clamp(alpha))
    return p

def wpath(pts, closed=False, amp=2.2, step=40, curve=False):
    r = rng()
    src = list(pts) + ([pts[0]] if closed else [])
    out = []
    for i in range(len(src) - 1):
        (x0, y0), (x1, y1) = src[i], src[i + 1]
        k = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for j in range(k):
            u = j / k
            out.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u))
    if not closed: out.append(src[-1])
    out = [(x + r.uniform(-amp, amp), y + r.uniform(-amp, amp)) for x, y in out]
    p = skia.Path()
    if curve and len(out) > 2:
        n = len(out)
        mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if closed:
            m = mid(out[-1], out[0]); p.moveTo(*m)
            for i in range(n):
                m = mid(out[i], out[(i + 1) % n]); p.quadTo(out[i][0], out[i][1], m[0], m[1])
            p.close()
        else:
            p.moveTo(*out[0])
            for i in range(1, n - 1):
                m = mid(out[i], out[i + 1]); p.quadTo(out[i][0], out[i][1], m[0], m[1])
            p.lineTo(*out[-1])
    else:
        p.moveTo(*out[0])
        for q in out[1:]: p.lineTo(*q)
        if closed: p.close()
    return p

def line(c, pts, color=INK, w=9, prog=1.0, alpha=1.0, amp=2.2, curve=False, closed=False, fill=None):
    if prog <= 0 or alpha <= 0: St.n += 1; return
    p = wpath(pts, closed=closed, amp=amp, curve=curve)
    if fill is not None: c.drawPath(p, paint(fill, fill=True, alpha=alpha))
    pa = paint(color, w, alpha=alpha)
    if prog < 1:
        pe = skia.TrimPathEffect.Make(0, clamp(prog))   # prog 1'e cok yakinsa None doner
        if pe is not None: pa.setPathEffect(pe)
    c.drawPath(p, pa)

def circ(c, cx, cy, rx, ry=None, color=INK, w=9, fill=None, alpha=1.0, prog=1.0, amp=1.8, n=14):
    ry = rx if ry is None else ry
    pts = [(cx + rx * math.cos(2 * math.pi * i / n - 1.2), cy + ry * math.sin(2 * math.pi * i / n - 1.2)) for i in range(n)]
    r = rng(); St.n -= 1
    p = wpath(pts, closed=True, amp=amp, step=999, curve=True)
    if fill is not None: c.drawPath(p, paint(fill, fill=True, alpha=alpha))
    if w > 0:
        pa = paint(color, w, alpha=alpha)
        if prog < 1:
            pe = skia.TrimPathEffect.Make(0, clamp(prog))
            if pe is not None: pa.setPathEffect(pe)
        c.drawPath(p, pa)

def rrect_pts(x0, y0, x1, y1, r=24, k=5):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def box(c, x0, y0, x1, y1, r=24, color=INK, w=9, fill=None, alpha=1.0, prog=1.0, amp=2.0):
    line(c, rrect_pts(x0, y0, x1, y1, r), color, w, prog, alpha, amp, closed=True, fill=fill)

def wash(c, x0, y0, x1, y1, color, alpha=1.0, r=30):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r), paint(color, fill=True, alpha=alpha))

def font(size, kind='bold'): return skia.Font(TF[kind], size)
def tw(s, size, kind='bold'): return font(size, kind).measureText(s)
def txt(c, s, x, y, size, color=INK, kind='bold', align='c', alpha=1.0):
    f = font(size, kind); w = f.measureText(s)
    ox = x - w / 2 if align == 'c' else (x - w if align == 'r' else x)
    c.drawString(s, ox, y, f, paint(color, fill=True, alpha=alpha))

class xf:
    """scale/rotate around a point, optional group alpha"""
    def __init__(s, c, x, y, sc=1.0, rot=0.0, alpha=1.0): s.c, s.x, s.y, s.sc, s.rot, s.a = c, x, y, sc, rot, alpha
    def __enter__(s):
        if s.a < 1: s.c.saveLayerAlpha(None, int(clamp(s.a) * 255))
        else: s.c.save()
        s.c.translate(s.x, s.y); s.c.rotate(s.rot); s.c.scale(max(s.sc, 0.001), max(s.sc, 0.001)); s.c.translate(-s.x, -s.y)
    def __exit__(s, *a): s.c.restore()

# ---------- props ----------
def check(c, x, y, s=1.0, prog=1.0, color=TEAL):
    line(c, [(x - 28 * s, y), (x - 6 * s, y + 24 * s), (x + 34 * s, y - 30 * s)], color, 13 * s, prog, amp=1.2)
def cross(c, x, y, s=1.0, prog=1.0, color=CORAL):
    line(c, [(x - 26 * s, y - 26 * s), (x + 26 * s, y + 26 * s)], color, 13 * s, seg(prog, 0, .5), amp=1.2)
    line(c, [(x + 26 * s, y - 26 * s), (x - 26 * s, y + 26 * s)], color, 13 * s, seg(prog, .5, 1), amp=1.2)
def scissors(c, x, y, s=1.0, color=INK, alpha=1.0):
    w = max(5, 7 * s)
    line(c, [(x - 34 * s, y - 30 * s), (x + 16 * s, y + 14 * s)], color, w, alpha=alpha, amp=1)
    line(c, [(x + 34 * s, y - 30 * s), (x - 16 * s, y + 14 * s)], color, w, alpha=alpha, amp=1)
    circ(c, x - 26 * s, y + 26 * s, 13 * s, color=CORAL, w=w, alpha=alpha, amp=1, n=10)
    circ(c, x + 26 * s, y + 26 * s, 13 * s, color=CORAL, w=w, alpha=alpha, amp=1, n=10)
def parcel(c, x, y, s=1.0, alpha=1.0, fill=CORAL):
    h = 24 * s
    box(c, x - h, y - h, x + h, y + h, r=6 * s, w=max(4, 6 * s), fill=fill, alpha=alpha, amp=1)
    line(c, [(x - h, y - 4 * s), (x + h, y - 4 * s)], INK, max(3, 4 * s), alpha=alpha, amp=.8)
def qmark(c, x, y, size, t, color=CORAL, alpha=1.0, sc=1.0):
    with xf(c, x, y - size * .35, sc, 9 * math.sin(t * 5), alpha):
        txt(c, '?', x, y, size, color)
def cloud(c, cx, cy, rx, ry, tail=None, alpha=1.0, fill=PAPER, w=8):
    if tail:
        tx, ty = tail
        for u, r in ((.82, 9), (.62, 15)):
            circ(c, lerp(cx, tx, u), lerp(cy + ry * .6, ty, u), r, color=INK, w=w * .75, fill=fill, alpha=alpha, amp=1, n=9)
    n = 16
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1 + (0.09 if i % 2 == 0 else -0.05)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    St.n += 0
    p = wpath(pts, closed=True, amp=1.5, step=999, curve=True)
    c.drawPath(p, paint(fill, fill=True, alpha=alpha)); c.drawPath(p, paint(INK, w, alpha=alpha))
def speech(c, x0, y0, x1, y1, tail, fill=PAPER, w=8):
    tx, ty = tail
    mx = clamp(tx, x0 + 70, x1 - 70)
    pts = rrect_pts(x0, y0, x1, y1, 34)
    # insert tail on bottom edge
    k = 6 * 2
    pts = pts[:k] + [(mx + 34, y1), (tx, ty), (mx - 22, y1)] + pts[k:]
    line(c, pts, INK, w, closed=True, fill=fill, amp=1.6)
def bulb(c, x, y, s=1.0, alpha=1.0, t=0):
    circ(c, x, y, 34 * s, color=INK, w=7 * s, fill=YEL, alpha=alpha, amp=1.2, n=12)
    line(c, [(x - 14 * s, y + 38 * s), (x + 14 * s, y + 38 * s)], INK, 7 * s, alpha=alpha, amp=1)
    line(c, [(x - 10 * s, y + 50 * s), (x + 10 * s, y + 50 * s)], INK, 7 * s, alpha=alpha, amp=1)
    for i in range(5):
        a = math.radians(-160 + i * 35)
        r0, r1 = 50 * s, (66 + 5 * math.sin(t * 8 + i)) * s
        line(c, [(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], CORAL, 6 * s, alpha=alpha, amp=.8)
def burst(c, x, y, r0, r1, n=8, color=CORAL, w=7, alpha=1.0):
    for i in range(n):
        a = 2 * math.pi * i / n + .3
        line(c, [(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], color, w, alpha=alpha, amp=.8)

def door(c, x, gy, w=190, h=450, wall_top=None, leaf=True, color=INK, lw=11, prog=1.0, s=1.0):
    """frame from x..x+w standing on ground gy"""
    if wall_top is not None:
        line(c, [(x + w / 2, wall_top), (x + w / 2, gy - h)], color, lw * .8, prog)
    if leaf:
        lx = x + w
        d = 62 * s
        line(c, [(lx, gy - h), (lx + d, gy - h + 26 * s), (lx + d, gy + 22 * s), (lx, gy)], color, lw * .75, prog, fill=PAPER, closed=True)
        circ(c, lx + d - 18 * s, gy - h * .45, 6 * s, color=color, w=5 * s, fill=color, alpha=float(prog >= 1), n=8, amp=.5)
    line(c, [(x, gy), (x, gy - h), (x + w, gy - h), (x + w, gy)], color, lw, prog)

def fridge(c, x, gy, w=165, h=390, s=1.0, prog=1.0):
    box(c, x, gy - h, x + w, gy, r=16 * s, w=9 * s, fill=PAPER, prog=prog)
    line(c, [(x, gy - h * .62), (x + w, gy - h * .62)], INK, 7 * s, prog)
    line(c, [(x + 22 * s, gy - h * .82), (x + 22 * s, gy - h * .70)], INK, 7 * s, prog)
    line(c, [(x + 22 * s, gy - h * .52), (x + 22 * s, gy - h * .34)], INK, 7 * s, prog)
def sofa(c, x, gy, s=1.0):
    box(c, x, gy - 110 * s, x + 240 * s, gy - 30 * s, r=22 * s, w=8 * s, fill=PAPER)
    box(c, x - 26 * s, gy - 80 * s, x + 24 * s, gy, r=18 * s, w=8 * s, fill=PAPER)
    box(c, x + 216 * s, gy - 80 * s, x + 266 * s, gy, r=18 * s, w=8 * s, fill=PAPER)
    box(c, x + 16 * s, gy - 58 * s, x + 224 * s, gy - 6 * s, r=14 * s, w=8 * s, fill=PAPER)
def picture(c, x, y, w=150, h=110):
    box(c, x, y, x + w, y + h, r=8, w=7, fill=PAPER)
    line(c, [(x + 16, y + h - 20), (x + 52, y + 42), (x + 80, y + h - 34), (x + 104, y + 54), (x + w - 14, y + h - 20)], MUTE, 6, amp=1.2)
def lamp(c, x, y0, y1):
    line(c, [(x, y0), (x, y1)], INK, 6, amp=1)
    line(c, [(x - 46, y1 + 46), (x - 22, y1), (x + 22, y1), (x + 46, y1 + 46)], INK, 8, closed=True, fill=YEL, amp=1.2)

# ---------- character ----------
EXPR = dict(smile=('dot', 'smile'), confused=('wide', 'flat'), oh=('wide', 'o'), happy=('happy', 'smile'),
            sad=('dot', 'sad'), talk=('dot', 'o'), flat=('dot', 'flat'))
STAND = dict(aL=7, eL=12, aR=-7, eR=-1, tL=5, kL=5, tR=-5, kR=-5, lean=0, tilt=0)
FRONT = dict(aL=10, eL=6, aR=10, eR=6, tL=7, kL=5, tR=7, kR=5, lean=0, tilt=0)
def mix(p, q, u):
    u = smooth(u); ks = set(p) | set(q)
    return {k: lerp(p.get(k, 0), q.get(k, 0), u) for k in ks}
def walk_pose(ph, amp=27):
    s, co = math.sin(ph), math.cos(ph)
    return dict(tL=amp * s, kL=amp * s - 42 * max(0, co), tR=-amp * s, kR=-amp * s - 42 * max(0, -co),
                aL=-24 * s, eL=-24 * s + 16, aR=24 * s, eR=24 * s + 16, lean=4, tilt=0)

def fig(c, x, gy, s=1.0, face=1, pose=None, expr='smile', alpha=1.0, color=INK, hold=None):
    P = dict(FRONT if face == 0 else STAND); P.update(pose or {})
    TH, SHN, TO, UA, FA, HR = 88 * s, 88 * s, 160 * s, 74 * s, 70 * s, 48 * s
    lw = max(5.5, 10 * s)
    front = face == 0
    f = 1 if front else face
    def vec(a, side):
        r = math.radians(a)
        return ((math.sin(r) * side) if front else (math.sin(r) * face), math.cos(r))
    def add(p, v, L): return (p[0] + v[0] * L, p[1] + v[1] * L)
    kL = add((0, 0), vec(P['tL'], -1), TH); fL = add(kL, vec(P['kL'], -1), SHN)
    kR = add((0, 0), vec(P['tR'], 1), TH); fR = add(kR, vec(P['kR'], 1), SHN)
    drop = max(fL[1], fR[1])
    hip = (x, gy - drop)
    T = lambda p: (hip[0] + p[0], hip[1] + p[1])
    ln = math.radians(P['lean']); up = (math.sin(ln) * f, -math.cos(ln))
    neck = add(hip, up, TO); sh = add(hip, up, TO * .88)
    hl = math.radians(P['lean'] + P['tilt']); hup = (math.sin(hl) * f, -math.cos(hl))
    hc = add(neck, hup, HR + 2 * s)
    eL = add(sh, vec(P['aL'], -1), UA); hL = add(eL, vec(P['eL'], -1), FA)
    eR = add(sh, vec(P['aR'], 1), UA); hR = add(eR, vec(P['eR'], 1), FA)
    if alpha < 1: c.saveLayerAlpha(None, int(clamp(alpha) * 255))
    # back limbs
    line(c, [T((0, 0)), T(kL), T(fL)], color, lw, amp=1.4 * s + .4, curve=True)
    line(c, [sh, eL, hL], color, lw, amp=1.4 * s + .4, curve=True)
    line(c, [T((0, 0)), T(kR), T(fR)], color, lw, amp=1.4 * s + .4, curve=True)
    line(c, [hip, neck], color, lw, amp=1.2 * s + .3)
    circ(c, hc[0], hc[1], HR, color=color, w=lw, fill=PAPER, amp=1.3 * s + .3)
    eyes, mouth = EXPR[expr]
    if front: ex = [(-16 * s, -5 * s), (16 * s, -5 * s)]; mx = 0
    else: ex = [(face * 5 * s, -6 * s), (face * 29 * s, -6 * s)]; mx = face * 17 * s
    for dx, dy in ex:
        px, py = hc[0] + dx, hc[1] + dy
        if eyes == 'dot': c.drawCircle(px, py, 5.5 * s, paint(color, fill=True))
        elif eyes == 'wide':
            c.drawCircle(px, py, 9 * s, paint(color, 3.5 * s)); c.drawCircle(px, py - 2 * s, 4 * s, paint(color, fill=True))
        elif eyes == 'happy':
            line(c, [(px - 8 * s, py + 3 * s), (px, py - 6 * s), (px + 8 * s, py + 3 * s)], color, 5 * s, amp=.5, curve=True)
    px, py = hc[0] + mx, hc[1] + 21 * s
    if mouth == 'smile': line(c, [(px - 13 * s, py - 3 * s), (px, py + 7 * s), (px + 13 * s, py - 3 * s)], color, 5 * s, amp=.5, curve=True)
    elif mouth == 'sad': line(c, [(px - 11 * s, py + 5 * s), (px, py - 3 * s), (px + 11 * s, py + 5 * s)], color, 5 * s, amp=.5, curve=True)
    elif mouth == 'flat': line(c, [(px - 10 * s, py + 2 * s), (px + 10 * s, py + 1 * s)], color, 5 * s, amp=.5)
    elif mouth == 'o': c.drawCircle(px, py + 2 * s, 6.5 * s, paint(color, 4.5 * s))
    if hold: hold((hR[0], hR[1]))
    line(c, [sh, eR, hR], color, lw, amp=1.4 * s + .4, curve=True)
    if alpha < 1: c.restore()
    return dict(head=hc, hr=HR, handR=hR, handL=hL, top=(hc[0], hc[1] - HR), hip=hip)

def ground(c, x0, x1, y, prog=1.0, w=9): line(c, [(x0, y), (x1, y)], INK, w, prog, amp=1.6)

# ---------- captions ----------
def chunks(text):
    out, cur = [], []
    for wd in text.split():
        if cur and len(' '.join(cur + [wd])) > 19: out.append(cur); cur = []
        cur.append(wd)
        if wd[-1] in ',:' and len(' '.join(cur)) > 7: out.append(cur); cur = []
    if cur: out.append(cur)
    if len(out) > 1 and len(' '.join(out[-1])) < 6:
        tail = out.pop(); out[-1] = out[-1] + tail
    return out
# Altyazi parcalarinin zamanlamasi SESTEN cikarilir: hece (unlu) sayisi konusulan sureye dagitilir,
# sinirlar gercek duraklamalara oturtulur. Parca, sesi baslarken gelir (once degil).
VOWELS = set('aeıioöuüâîûAEIİOÖUÜÂÎÛ')
def syl(words): return max(1, sum(ch in VOWELS for ch in ''.join(words)))
_AU, _SR = sf.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice/final.wav'), dtype='float32')
if _AU.ndim > 1: _AU = _AU.mean(axis=1)
def chunk_times(t0, t1, ch):
    hop = 0.01; x = _AU[int(t0 * _SR):int(t1 * _SR)]; h = int(_SR * hop); n = len(x) // h
    if n < 3 or len(ch) == 1: return [t0] + [t1] * 0
    rms = np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(axis=1) + 1e-12)
    voiced = rms > max(0.008, 0.07 * np.percentile(rms, 95))
    cum = np.concatenate([[0], np.cumsum(voiced)]) * hop          # konusulan sure, zamana gore
    gaps, i = [], 0
    while i < n:
        if not voiced[i]:
            j = i
            while j < n and not voiced[j]: j += 1
            if (j - i) * hop >= 0.07 and i > 0 and j < n: gaps.append((i * hop, j * hop))
            i = j
        else: i += 1
    w = np.array([syl(c) + 0.12 * sum(ch_.isalpha() for ch_ in ''.join(c)) for c in ch], float)
    tgt = cum[-1] * np.cumsum(w)[:-1] / w.sum()
    starts = [t0]
    for k, v in enumerate(tgt):
        tb = np.searchsorted(cum, v) * hop                              # sinirin tahmini (sessizlik basi)
        # sadece ileri ya da cok yakin geri duraklamalara oturt; altyazi sesin ONUNE gecmesin
        near = [g for g in gaps if g[1] >= tb - 0.1 and g[0] <= tb + 0.4 and t0 + g[1] > starts[-1] + 0.25]
        on = (min(near, key=lambda g: abs(g[1] - tb))[1] - 0.04 if near else tb + 0.12)
        starts.append(max(starts[-1] + 0.25, t0 + on))
    return starts
CAPS = []
for n_, l in enumerate(LN):
    ch = chunks(l['text']); st = chunk_times(l['start'], l['end'], ch)
    nxt = LN[n_ + 1]['start'] if n_ + 1 < len(LN) else TOTAL
    for k, x in enumerate(ch):
        b = st[k + 1] if k + 1 < len(ch) else min(l['end'] + 0.22, nxt - 0.02)
        CAPS.append(dict(a=st[k], b=b, words=x, line=l['i']))
def wrap(words, f, sp, maxw):
    rows, cur = [], []
    for w_ in words:
        if cur and sum(f.measureText(x) for x in cur + [w_]) + sp * len(cur) > maxw: rows.append(cur); cur = []
        cur.append(w_)
    if cur: rows.append(cur)
    if len(rows) == 2 and len(rows[1]) == 1 and len(rows[0]) > 2: rows = [rows[0][:-1], rows[0][-1:] + rows[1]]
    return rows
def captions(c, t):
    for cp in CAPS:
        if cp['a'] <= t < cp['b']:
            if FMT == 'v': size, cxx, cy, maxw = 78, W / 2, 1380, 900
            else: size, cxx, cy, maxw = 80, 1510, 600, 700
            words = cp['words']; f = font(size); sp = f.measureText(' ') * 1.05
            rows = wrap(words, f, sp, maxw)
            sc = lerp(.88, 1, back(seg(t, cp['a'], cp['a'] + .14)))
            with xf(c, cxx, cy, sc, 0, seg(t, cp['a'], cp['a'] + .08)):
                y = cy + 26 - (len(rows) - 1) * 48
                for row in rows:
                    wd = [f.measureText(w) for w in row]; tot = sum(wd) + sp * (len(row) - 1); x = cxx - tot / 2
                    for w_, ww in zip(row, wd):
                        hl = w_.lower() in HL.get(cp['line'], [])
                        if hl:
                            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 10, y - 66, x + ww + 10, y + 22), 14, 14), paint(YEL, fill=True))
                        c.drawString(w_, x, y, f, paint(INK, fill=True))
                        x += ww + sp
                    y += 98
            return

def tag(c):
    s = '1 DAKİKADA PSİKOLOJİ'; size = 34; w = tw(s, size)
    cx, y0 = (W / 2, 196) if FMT == 'v' else (1510, 120)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 34, y0, cx + w / 2 + 34, y0 + 66), 33, 33), paint(INK, fill=True))
    txt(c, s, cx, y0 + 45, size, BG)
    if FMT == 'h':
        txt(c, TITLE, cx, y0 + 140, 46, CORAL)
        line(c, [(cx - 150, y0 + 168), (cx, y0 + 163), (cx + 150, y0 + 170)], INK, 7, amp=1.2, curve=True)

def L(i): return LN[i]['start'], LN[i]['end']
def cap_start(li, word, default):
    """altyazi parcasinin (icinde 'word' gecen) sesteki baslangici"""
    for cp in CAPS:
        if cp['line'] == li and any(word in w for w in cp['words']): return cp['a']
    return default

# ---------- scenes ----------
GY = 1090

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1)
    wash(c, 60, 330, 1020, 1100, WASH_T)
    circ(c, 170, 440, 46, color=INK, w=7, fill=YEL, n=12)
    for i, (sx, sy) in enumerate(((330, 400), (900, 390), (930, 600))):
        r = 11 + 4 * math.sin(t * 4 + i * 2)
        line(c, [(sx - r, sy), (sx + r, sy)], CORAL, 5, amp=.5)
        line(c, [(sx, sy - r), (sx, sy + r)], CORAL, 5, amp=.5)
    ground(c, 50, 1030, 1100)
    box(c, 110, 800, 172, 1100, r=14, w=9, fill=PAPER)                 # yatak basi
    for lx in (230, 900): line(c, [(lx, 1060), (lx, 1100)], INK, 9, amp=1)
    box(c, 150, 960, 965, 1062, r=20, w=9, fill=PAPER)                 # yatak
    box(c, 190, 900, 410, 966, r=28, w=8, fill=PAPER)                  # yastik
    hx, hy = 312, 866
    circ(c, hx, hy, 50, color=INK, w=9, fill=PAPER)
    ed = 3 * math.sin(t * 2.6)
    for dx in (-2, 24):
        c.drawCircle(hx + dx, hy - 6, 9, paint(INK, 3.5)); c.drawCircle(hx + dx + ed, hy - 9, 4, paint(INK, fill=True))
    line(c, [(hx + 4, hy + 22), (hx + 24, hy + 21)], INK, 5, amp=.5)
    box(c, 384, 900, 968, 1012, r=34, w=9, fill=WASH_P)                # yorgan
    p = pop(t, a0 + 1.5, .35)
    if p > 0:
        cx, cy = 560, 610
        pul = 1 + .03 * math.sin(t * 7)
        with xf(c, cx, cy, p * pul):
            cloud(c, cx, cy, 250, 135, tail=(hx + 34, hy - 58))
            txt(c, 'YARIM İŞ', cx, cy - 26, 50, INK)
            box(c, cx - 160, cy + 8, cx + 160, cy + 58, r=22, w=7, fill=PAPER)
            wash(c, cx - 153, cy + 15, cx - 10, cy + 51, CORAL, r=16)
            txt(c, '?', cx + 80, cy + 48, 40, MUTE)
    for i, x0 in enumerate((640, 770, 900)):
        pp = pop(t, b0 + i * .18, .25)
        if pp > 0:
            fade = 1 - .9 * smooth(seg(t, b0 + 1.3 + i * .25, b0 + 2.1 + i * .25))
            y0 = 830 - 34 * (1 - fade)
            with xf(c, x0, y0, pp, 0, fade):
                circ(c, x0, y0, 36, color=TEAL, w=0, fill=TEAL, n=12, amp=.8)
                check(c, x0, y0, .7, 1, PAPER)

def scene2(c, t):
    a0, a1 = L(2); b0, b1 = L(3)
    gy = 1170; x = 540; s = 1.0
    tt = cap_start(3, 'Zeigarnik', b0 + 1.2)
    c.drawOval(skia.Rect.MakeLTRB(x - 170, gy - 16, x + 170, gy + 22), paint(0xFFEDE3D0, fill=True))
    shr = smooth(seg(t, a0, a0 + .35)) * (1 - smooth(seg(t, a1 - .2, a1 + .2)))
    pt = smooth(seg(t, tt - .1, tt + .3))
    pose = mix(FRONT, dict(FRONT, aL=38, eL=118, aR=38, eR=118, tilt=5), shr)
    pose = mix(pose, dict(FRONT, aR=152, eR=168 + 4 * math.sin(t * 6), aL=14, eL=8, tilt=-3), pt)
    ex = 'happy' if (t < a1 + .3 or t > tt) else 'smile'
    info = fig(c, x, gy, s, 0, pose, ex)
    fr = pop(t, a0 + .7, .3) * (1 - smooth(seg(t, tt - .5, tt - .15)))
    if fr > 0.01:
        for fx, fc in ((215, 1), (865, -1)):
            with xf(c, fx, gy, fr):
                fi = fig(c, fx, gy - 8, .62, fc, dict(STAND), 'flat')
                tx_, ty_ = fi['top']
                cloud(c, tx_ + fc * 16, ty_ - 92, 78, 50, tail=(tx_, ty_ - 6), w=6)
                txt(c, '...', tx_ + fc * 16, ty_ - 80, 56, CORAL)
    if t > tt:
        p = pop(t, tt, .35)
        with xf(c, 540, 460, lerp(.7, 1, p), 0, seg(t, tt, tt + .15)):
            txt(c, 'ZEIGARNIK', 540, 420, 112, INK)
            txt(c, 'ETKİSİ', 540, 540, 112, CORAL)
        line(c, [(290, 576), (420, 570), (560, 580), (790, 568)], INK, 10, seg(t, tt + .4, tt + .8), curve=True)
        txt(c, 'yarım kalan işin çekimi', 540, 634, 38, MUTE, 'med', alpha=seg(t, tt + .7, tt + 1.0))

def tasklist(c, cx, cy, done):
    for k in range(3):
        y = cy - 70 + k * 70
        box(c, cx - 132, y - 22, cx - 88, y + 22, r=8, w=6, fill=PAPER)
        line(c, [(cx - 62, y), (cx + 130, y)], MUTE, 7, amp=1)
        if k < done: check(c, cx - 108, y - 2, .55, 1, TEAL)

def card(c, cx, cy, w, h, title, col, content, sc=1.0, alpha=1.0, rot=0.0, hi=False):
    with xf(c, cx, cy, sc, rot, alpha):
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        box(c, x0, y0, x1, y1, r=26, w=10 if hi else 8, fill=PAPER, color=CORAL if hi else INK)
        wl = tw(title, 32)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - wl / 2 - 24, y0 - 28, cx + wl / 2 + 24, y0 + 28), 28, 28), paint(col, fill=True))
        txt(c, title, cx, y0 + 12, 32, PAPER)
        content(cx, cy)

def scene3(c, t):
    a0, _ = L(4); _, a1 = L(5); b0, b1 = L(6); d0, d1 = L(7); e0, e1 = L(8)
    al = seg(t, a0 - .1, a0 + .3)
    with xf(c, 540, 380, 1, 0, al):
        txt(c, 'Bluma Zeigarnik · 1927', 540, 372, 44, INK, 'bold')
        txt(c, 'Berlin Üniversitesi deneyleri', 540, 424, 32, MUTE, 'med')
    tk = cap_start(5, 'insanlara', a0 + 3.3)
    cut_t = cap_start(5, 'yarıda', a1 - 1.2)
    p1 = pop(t, tk, .3); p2 = pop(t, tk + .45, .3)
    hi = b0 + 1.6 <= t < d0
    def c1(cx, cy): tasklist(c, cx, cy + 14, 3)
    def c2(cx, cy):
        tasklist(c, cx, cy + 14, 1)
        cu = seg(t, cut_t, cut_t + .35)
        if cu > 0:
            line(c, [(cx - 165, cy - 18), (cx - 60, cy - 32), (cx + 40, cy - 12), (cx + 120, cy - 28)], CORAL, 9, cu, amp=1.5)
            if cu >= 1: scissors(c, cx + 150, cy - 26, .62)
    if p1 > 0: card(c, 290, 660, 380, 320, 'BİTEN İŞ', TEAL, c1, sc=p1)
    if p2 > 0: card(c, 790, 660, 380, 320, 'YARIM İŞ', CORAL, c2, sc=p2, hi=hi)
    th = cap_start(6, 'daha', b0 + 2.2)
    dim = 1 - .6 * seg(t, d0, d0 + .3)
    m = pop(t, th, .3)
    if m > 0:
        with xf(c, 790, 884, m, 0, dim): txt(c, 'daha iyi hatırlandı', 790, 896, 35, CORAL)
        with xf(c, 290, 884, m, 0, dim): txt(c, 'daha az hatırlandı', 290, 896, 35, MUTE)
    bn = pop(t, d0 + .3, .3)
    if bn > 0:
        with xf(c, 540, 985, bn, -1.5):
            box(c, 150, 940, 930, 1024, r=30, w=7, fill=PAPER, color=MUTE)
            txt(c, 'Sonraki deneyler: her zaman değil', 540, 996, 36, INK, 'med')
    # insanlar yarim ise geri donuyor
    w0 = cap_start(8, 'insanlar', e0 + 1.4)
    if t > e0 - .1:
        gy = 1238; ga = seg(t, e0 - .1, e0 + .3)
        ground(c, 110, 970, gy, ga, w=7)
        fu = smooth(seg(t, e1 - .9, e1 - .3))
        bx0, bx1, by0, by1 = 730, 930, 1150, 1200
        box(c, bx0, by0, bx1, by1, r=20, w=7, fill=PAPER, alpha=ga)
        wash(c, bx0 + 7, by0 + 7, lerp(bx0 + 95, bx1 - 7, fu), by1 - 7, TEAL if fu >= 1 else CORAL, ga, r=14)
        line(c, [(bx0 + 30, by1), (bx0 + 30, gy)], INK, 6, ga, amp=1); line(c, [(bx1 - 30, by1), (bx1 - 30, gy)], INK, 6, ga, amp=1)
        u = seg(t, w0, e1 - 1.0); x = lerp(190, 650, smooth(u)); ph = (x - 190) / 70 * math.pi
        if 0 < u < 1: pose = walk_pose(ph, 26)
        else: pose = mix(STAND, dict(STAND, aR=70, eR=96), seg(t, e1 - 1.0, e1 - .8))
        fig(c, x, gy, .42, 1, pose, 'happy' if fu >= 1 else 'smile', alpha=ga)
        ck = seg(t, e1 - .3, e1)
        if ck > 0: check(c, 960, 1130, .8, ck)

def scene4(c, t):
    a0, a1 = L(9); b0, b1 = L(10)
    x0, y0, x1, y1 = 130, 520, 950, 1080
    wp = pop(t, a0 - .05, .35)
    tab_t = cap_start(9, 'açık', a0 + 1.6)
    fill_u = smooth(seg(t, b0 + .05, b0 + .7))
    close = smooth(seg(t, b0 + .9, b0 + 1.35))
    tp = pop(t, tab_t, .3) * (1 - close)
    tcx, tcy = x0 + 420, y0 + 52
    with xf(c, 540, 800, lerp(.9, 1, wp), 0, seg(t, a0 - .05, a0 + .15)):
        box(c, x0, y0, x1, y1, r=28, w=10, fill=PAPER)
        line(c, [(x0, y0 + 92), (x1, y0 + 92)], INK, 8, amp=1.2)
        box(c, x0 + 30, y0 + 24, x0 + 250, y0 + 92, r=16, w=6, fill=BG, color=MUTE)
        check(c, x0 + 72, y0 + 58, .5, 1, TEAL); txt(c, 'bitti', x0 + 106, y0 + 70, 32, MUTE, 'med', align='l')
        for i in range(3): c.drawCircle(x1 - 50 - i * 34, y0 + 56, 9, paint(MUTE, fill=True))
        if tp > 0.01:
            wob = (1 - fill_u) * 2.5 * math.sin(t * 15)
            with xf(c, tcx, tcy, tp, wob):
                box(c, x0 + 272, y0 + 14, x0 + 568, y0 + 92, r=16, w=8, fill=WASH_Y, color=CORAL)
                txt(c, 'yarım iş', x0 + 298, y0 + 68, 36, INK, align='l')
                cross(c, x0 + 530, y0 + 54, .36, 1, INK)
        ca = seg(t, tab_t + .2, tab_t + .6)
        if ca > 0:
            done = fill_u >= 1
            txt(c, 'bitti!' if done else 'yarım kalan iş', 540, 760, 52, TEAL if done else INK, alpha=ca)
            box(c, 230, 810, 850, 890, r=36, w=8, fill=PAPER, alpha=ca)
            wash(c, 240, 820, lerp(540, 840, fill_u), 880, TEAL if done else CORAL, ca, r=28)
            if done: check(c, 540, 985, 1.3, seg(t, b0 + .7, b0 + 1.0))
    # gerginlik cizgileri
    ten = seg(t, tab_t + .3, tab_t + .6) * (1 - fill_u)
    if ten > 0:
        for k in (0, .5):
            v = (t * 1.1 + k) % 1
            burst(c, tcx + 10, tcy, 190 + 30 * v, 216 + 40 * v, 12, CORAL, 7, (1 - v) * ten)
    if close >= 1:
        v = seg(t, b0 + 1.35, b0 + 1.9)
        if v < 1: burst(c, tcx + 10, tcy, 30 + 60 * v, 54 + 80 * v, 8, TEAL, 7, 1 - v)

def scene5(c, t):
    a0, a1 = L(11); b0, b1 = L(12); d0, d1 = L(13)
    wash(c, 60, 440, 1020, GY, WASH_Y)
    ground(c, 50, 1030, GY)
    np_t = cap_start(11, 'planını', a0 + 2.0) - .5
    tip = smooth(seg(t, np_t, np_t + .4))
    pose = mix(STAND, dict(STAND, aR=66, eR=104, tilt=-3), tip)
    ex = 'happy' if t > d0 + .4 else 'smile'
    info = fig(c, 235, GY, .9, 1, pose, ex)
    hx, hy = info['top']
    bl = pop(t, a0 + .35, .3) * (1 - seg(t, b0 - .25, b0 - .05))
    if bl > 0:
        with xf(c, hx + 10, hy - 110, bl): bulb(c, hx + 10, hy - 110, 1.15, t=t)
    npp = pop(t, np_t, .35)
    if npp > 0:
        nx0, ny0, nx1, ny1 = 470, 500, 980, 1010
        with xf(c, 725, 755, npp, -2):
            box(c, nx0, ny0, nx1, ny1, r=22, w=9, fill=PAPER)
            wash(c, nx0 + 6, ny0 + 6, nx1 - 6, ny0 + 98, CORAL, r=16)
            txt(c, 'PLAN', 725, ny0 + 70, 52, PAPER)
            rows = [('Ne zaman?', 'Sabah 10:00', b0 + .05), ('Nerede?', 'Masamda', cap_start(12, 'nerede', b0 + .8))]
            for k, (q, a, tq) in enumerate(rows):
                y = ny0 + 190 + k * 170
                al = seg(t, tq, tq + .2)
                txt(c, q, nx0 + 42, y, 36, MUTE, 'med', align='l', alpha=al)
                n = int(len(a) * seg(t, tq + .3, tq + .9) + .001)
                txt(c, a[:n], nx0 + 42, y + 62, 52, INK, align='l')
                line(c, [(nx0 + 42, y + 80), (nx1 - 42, y + 80)], MUTE, 5, alpha=al, amp=1)
            ck = seg(t, d0 + .5, d0 + .9)
            if ck > 0:
                circ(c, nx1 - 16, ny0 + 8, 46, color=TEAL, w=0, fill=TEAL, n=12, amp=.8)
                check(c, nx1 - 18, ny0 + 10, .85, ck, PAPER)
    rl = seg(t, d0 + .9, d0 + 1.2)
    if rl > 0:
        for i, (dx, dy) in enumerate(((-120, 0), (120, -30), (-70, -100), (60, -120))):
            r = (14 + 5 * math.sin(t * 6 + i)) * rl
            line(c, [(hx + dx - r, hy + dy), (hx + dx + r, hy + dy)], TEAL if i % 2 else CORAL, 7, amp=.6)
            line(c, [(hx + dx, hy + dy - r), (hx + dx, hy + dy + r)], TEAL if i % 2 else CORAL, 7, amp=.6)

def scene6(c, t):
    a0, a1 = L(14); b0, b1 = L(15); d0, d1 = L(16)
    wash(c, 60, 540, 1020, GY, WASH_T)
    ground(c, 50, 1030, GY)
    shr = smooth(seg(t, a0 + .1, a0 + .5)) * (1 - smooth(seg(t, a1 - .3, a1 + .1)))
    wv = smooth(seg(t, d0 - .1, d0 + .3))
    pose = mix(FRONT, dict(FRONT, aL=38, eL=118, aR=38, eR=118, tilt=6), shr)
    pose = mix(pose, dict(FRONT, aR=148, eR=160 + 26 * math.sin(t * 9), aL=12, eL=8), wv)
    ex = 'confused' if t < a1 - .5 else 'happy'
    info = fig(c, 540, GY, .92, 0, pose, ex)
    hx, hy = info['top']
    q = pop(t, a0 + .1, .3) * (1 - smooth(seg(t, a1 - .7, a1 - .4)))
    if q > 0: qmark(c, hx + 210, hy - 20, 170, t, CORAL, sc=q)
    nb = pop(t, b0 - .05, .3) * (1 - smooth(seg(t, d0 - .2, d0 + .1)))
    if nb > 0.01:
        cx, cy = 262, 690
        with xf(c, cx, cy, nb):
            cloud(c, cx, cy, 185, 115, tail=(hx - 46, hy + 14))
            cl = smooth(seg(t, b0 + 1.5, b0 + 1.9))
            if cl < .98:
                with xf(c, cx, cy, 1 - cl):
                    box(c, cx - 150, cy - 42, cx + 150, cy + 42, r=16, w=8, fill=WASH_Y, color=CORAL)
                    txt(c, 'yarım iş', cx - 124, cy + 14, 38, INK, align='l')
                    cross(c, cx + 112, cy, .4, 1, INK)
            else:
                sp = pop(t, b0 + 1.9, .3)
                if sp > 0.05:
                    check(c, cx, cy, 1.3 * sp, 1, TEAL)
                    burst(c, cx, cy, 70 * sp, 96 * sp, 8, TEAL, 7, 1)
    if t > d0 - .1:
        p = pop(t, d0 - .1, .35)
        with xf(c, 540, 400, lerp(.7, 1, p), 0, seg(t, d0 - .1, d0 + .1)):
            txt(c, 'Bir sonraki videoda', 540, 372, 74, INK)
            txt(c, 'görüşürüz!', 540, 474, 92, CORAL)
        line(c, [(310, 508), (440, 501), (600, 513), (770, 503)], INK, 9, seg(t, d0 + .4, d0 + .9), curve=True)

DRAW = {1: scene1, 2: scene2, 3: scene3, 4: scene4, 5: scene5, 6: scene6}

def frame(surface, t, k):
    c = surface.getCanvas()
    St.boil = int(t * FPS) // 5; St.n = 0
    c.clear(BG)
    a, b = scene_span(k)
    if FMT == 'v': DRAW[k](c, t)
    else:
        c.save(); c.translate(ART_DX, ART_DY - ART_Y0); c.clipRect(skia.Rect.MakeLTRB(0, ART_Y0, 1080, ART_Y1))
        DRAW[k](c, t); c.restore()
    tag(c)
    captions(c, t)
    # soft fade in/out at scene edges
    f = min(seg(t, a, a + .16), 1.0 if k == SCENES[-1] else 1 - seg(t, b - .12, b))
    if k == 1: f = 1 - seg(t, b - .12, b) if t > 1 else 1
    if k == SCENES[-1] and t > TOTAL - .35: f = 1 - seg(t, TOTAL - .35, TOTAL)
    if f < 1: c.drawRect(skia.Rect.MakeWH(W, H), paint(BG, fill=True, alpha=1 - f))

def scene_of(t):
    k = SCENES[0]
    for s in SCENES:
        if t >= SC[s]: k = s
    return k

if __name__ == '__main__':
    surface = skia.Surface(W, H)
    if sys.argv[1] == 'still':
        for ts in sys.argv[3:]:
            t = float(ts); frame(surface, t, scene_of(t))
            surface.makeImageSnapshot().save(f'{sys.argv[2]}/f_{t:06.2f}.png', skia.kPNG)
    elif sys.argv[1] == 'scene':
        k = int(sys.argv[2]); a, b = scene_span(k)
        f0, f1 = round(a * FPS), round(b * FPS)
        os.makedirs(f'scenes_{FMT}', exist_ok=True)
        tmp, out = f'scenes_{FMT}/tmp_s{k}.mp4', f'scenes_{FMT}/s{k}.mp4'
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-crf', '17', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            frame(surface, fi / FPS, k)
            p.stdin.write(surface.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.replace(tmp, out); print('scene', k, f1 - f0, 'frames')
        else: sys.exit(1)
