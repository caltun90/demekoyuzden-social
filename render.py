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

TITLE = 'Soğan ve Gözyaşı'   # yatay formatta etiketin altinda gorunur
HOOK = 'Soğan neden ağlatır?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['SOĞAN', 'NEDEN', 'AĞLATIR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 3.7                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['gözlerin', 'doldu.'], 1: ['neden'], 2: ['savunuyor.'], 3: ['karışır.'], 4: ['enzim,', 'gaz'], 5: ["2002'de"], 6: ['enzimi'],
      7: ['kendiliğinden'], 8: ['gözüne'], 9: ['tehlike'], 10: ['gözyaşıyla'], 11: ['yapmalı?'], 12: ['kör', 'fışkırtır.'],
      13: ['keskin', 'yavaş', 'az'], 14: ['yanar'], 15: ['demek', 'o', 'yüzden!']}


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

def tag(c, hook=True):
    s = '1 DAKİKADA BİLİM'
    size, cx, y0, hh = (46, W / 2, 128, 86) if FMT == 'v' else (40, 1510, 108, 76)
    w = tw(s, size)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 40, y0, cx + w / 2 + 40, y0 + hh), hh / 2, hh / 2), paint(INK, fill=True))
    txt(c, s, cx, y0 + hh / 2 + size * .36, size, BG)
    if FMT == 'h':
        txt(c, TITLE, cx, y0 + 150, 46, CORAL)
        line(c, [(cx - 150, y0 + 178), (cx, y0 + 173), (cx + 150, y0 + 180)], INK, 7, amp=1.2, curve=True)
    elif hook:
        hs = 60
        while tw(HOOK, hs) > 940: hs -= 2
        txt(c, HOOK, cx, 288, hs, CORAL)

def cover(c):
    """ilk kare (kapak): altyazi yerine dev kanca yazisi; platformlar kapak olarak bu kareyi kullanir"""
    cx, cy, maxw = (W / 2, 1410, 960) if FMT == 'v' else (1510, 610, 720)
    size = 150
    while max(tw(r, size) for r in COVER) > maxw: size -= 4
    step = size * 1.18
    y = cy - (len(COVER) - 1) * step / 2 + size * .36
    for i, r in enumerate(COVER):
        w = tw(r, size)
        if i == len(COVER) - 1:
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 18, y - size * .86, cx + w / 2 + 18, y + size * .2), 18, 18), paint(YEL, fill=True))
        txt(c, r, cx, y, size, INK)
        y += step

def L(i): return LN[i]['start'], LN[i]['end']
def cap_start(li, word, default):
    """altyazi parcasinin (icinde 'word' gecen) sesteki baslangici"""
    for cp in CAPS:
        if cp['line'] == li and any(word in w for w in cp['words']): return cp['a']
    return default

# ---------- scenes ----------
def pill(c, s, cx, cy, size=34, col=INK, fg=BG):
    w = tw(s, size); h = size * 1.7
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 26, cy - h / 2, cx + w / 2 + 26, cy + h / 2), h / 2, h / 2), paint(col, fill=True))
    txt(c, s, cx, cy + size * .36, size, fg)

def dashes(c, p0, p1, n=7, color=MUTE, w=6, alpha=1.0):
    for k in range(n):
        u0, u1 = k / n, (k + .55) / n
        line(c, [(lerp(p0[0], p1[0], u0), lerp(p0[1], p1[1], u0)), (lerp(p0[0], p1[0], u1), lerp(p0[1], p1[1], u1))], color, w, alpha=alpha, amp=.5)

def emark(c, x, y, size, t, color=CORAL, sc=1.0):
    with xf(c, x, y - size * .35, sc, 8 * math.sin(t * 5)):
        txt(c, '!', x, y, size, color)

def arrow(c, p0, p1, color=INK, w=7, prog=1.0, alpha=1.0):
    """duz ok; ucu cizgi bitince belirir"""
    line(c, [p0, p1], color, w, prog, alpha, amp=.8)
    if prog > .9:
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for d in (2.6, -2.6):
            line(c, [p1, (p1[0] + 26 * math.cos(a + d), p1[1] + 26 * math.sin(a + d))], color, w, alpha=alpha, amp=.5)

TEARC = 0xFF6CC3B8
def onion(c, x, y, r, alpha=1.0, w=8):
    """sogan: uc + govde + katman cizgileri"""
    if alpha <= 0: return
    for dx in (-.16, 0, .16):
        line(c, [(x + dx * r * .5, y - r * .86), (x + dx * r * 2.2, y - r * 1.32)], INK, w * .8, alpha=alpha, amp=.8)
    circ(c, x, y, r * 1.06, r * .95, color=INK, w=w, fill=WASH_P, alpha=alpha, amp=1.4, n=14)
    for sd in (-1, 1):
        line(c, [(x + sd * r * .12, y - r * .8), (x + sd * r * .62, y), (x + sd * r * .12, y + r * .8)], CORAL, w * .7, alpha=alpha, amp=.8, curve=True)
    line(c, [(x, y - r * .78), (x, y + r * .78)], CORAL, w * .7, alpha=alpha, amp=.8)

def knife(c, x, y, ang=0.0, s=1.0, dull=False, alpha=1.0):
    """bicak: (x, y) sapin ucu, ang derece; dull = kor (kalin) bicak"""
    if alpha <= 0: return
    c.save(); c.translate(x, y); c.rotate(ang)
    line(c, [(0, 0), (70 * s, 0)], INK, 20 * s, alpha=alpha, amp=.6)
    e = 34 if dull else 22
    line(c, [(70 * s, -16 * s), (250 * s, -16 * s), ((244 if dull else 228) * s, e * s), (70 * s, e * s)], INK, 7 * s, alpha=alpha, closed=True, fill=PAPER, amp=.8)
    c.restore()

def tear(c, x, y, s=1.0, alpha=1.0):
    if alpha <= 0: return
    p = skia.Path(); p.moveTo(x, y - 18 * s)
    p.cubicTo(x + 14 * s, y + 2 * s, x + 9 * s, y + 13 * s, x, y + 13 * s)
    p.cubicTo(x - 9 * s, y + 13 * s, x - 14 * s, y + 2 * s, x, y - 18 * s)
    c.drawPath(p, paint(TEARC, fill=True, alpha=alpha)); c.drawPath(p, paint(INK, max(2.5, 3.5 * s), alpha=alpha))

def puff(c, x, y, r, alpha=1.0):
    """gaz bulutcugu"""
    if alpha <= 0: return
    circ(c, x, y, r, r * .8, color=CORAL, w=max(4, r * .16), fill=WASH_P, alpha=alpha, amp=1.2, n=9)

def wisp(c, x, y, h, t, ph=0.0, alpha=1.0, prog=1.0):
    line(c, [(x + 16 * math.sin(t * 3 + ph + k * 1.1), y - h * k / 6) for k in range(7)], CORAL, 7, prog, alpha, amp=.6, curve=True)

def dot(c, x, y, r, col):
    c.drawCircle(x, y, r, paint(col, fill=True)); c.drawCircle(x, y, r, paint(INK, 4))

def eye(c, x, y, rx, ry, look=(0, 0), w=10):
    p = skia.Path(); p.moveTo(x - rx, y); p.quadTo(x, y - ry * 2, x + rx, y); p.quadTo(x, y + ry * 2, x - rx, y); p.close()
    c.drawPath(p, paint(PAPER, fill=True))
    c.save(); c.clipPath(p, skia.ClipOp.kIntersect, True)
    ix, iy = x + look[0], y + look[1]
    c.drawCircle(ix, iy, ry * .84, paint(TEAL, fill=True)); c.drawCircle(ix, iy, ry * .4, paint(INK, fill=True))
    c.drawCircle(ix + ry * .26, iy - ry * .3, ry * .13, paint(PAPER, fill=True))
    c.restore()
    c.drawPath(p, paint(INK, w))
    for k in range(5):
        u = (k + 1) / 6; px = x - rx + 2 * rx * u; py = y - 4 * ry * u * (1 - u)
        line(c, [(px, py - 8), (px + (u - .5) * 44, py - 46)], INK, 7, amp=.6)

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1)
    gy = 1160
    wash(c, 60, 340, 1020, gy + 20, WASH_Y)
    ground(c, 60, 1020, gy)
    tg = cap_start(0, 'gözlerin', a1 - 1.2); tn = cap_start(1, 'neden', b1 - 1.4)
    cry = t > tg
    line(c, [(370, 985), (1010, 985)], INK, 11, amp=1.4)
    for x in (420, 960): line(c, [(x, 985), (x, gy)], INK, 9, amp=1.2)
    box(c, 450, 950, 910, 985, r=10, w=7, fill=YEL)
    onion(c, 650, 852, 100)
    for k in range(3):
        line(c, [(800 + k * 32, 946), (816 + k * 32, 902), (832 + k * 32, 946)], CORAL, 8, amp=.8, curve=True)
    wa = seg(t, a0 + .8, a0 + 1.3)
    for k, dx in enumerate((-46, 4, 54)): wisp(c, 650 + dx, 710, 150, t, k * 2.0, wa * .9, seg(t, a0 + .8 + k * .15, a0 + 1.5 + k * .15))
    chop = 0 if cry else math.sin(t * 10)
    pose = dict(STAND, aR=58, eR=96 + 10 * chop, lean=4)
    if cry: pose = mix(pose, dict(STAND, aR=44, eR=74, lean=-3, tilt=-4), seg(t, tg, tg + .25))
    def hold(p): knife(c, p[0] - 6, p[1] - 4, 44 if cry else 24 + 8 * chop, .8)
    me = fig(c, 235, gy, 1.02, 1, pose, 'sad' if cry else 'smile', hold=hold)
    hx, hy = me['head']
    if cry:
        for k in range(4):
            ph = ((t - tg) * 1.2 + k * .25) % 1.0
            tear(c, hx + (6 if k % 2 == 0 else 32) + (-8 if k % 2 == 0 else 8) * ph, hy + 14 + 150 * ph, .95, alpha=min(1, (t - tg) * 4) * (1 - ph ** 3))
    if t > b0 - .1:
        with xf(c, 330, 520, pop(t, b0 - .1, .35)):
            cloud(c, 330, 505, 240, 92, tail=(hx + 30, hy - 60))
            txt(c, 'Üzgün değilim ki!', 330, 521, 44, INK)
        if t > tn: qmark(c, 800, 620, 210, t, CORAL, 1.0, pop(t, tn, .3))

def scene2(c, t):
    a0, a1 = L(2); n0, n1 = L(3)
    fa = 1 - smooth(seg(t, n0 - .3, n0 - .05))
    if fa > .01:
        ts = cap_start(2, 'savunuyor', a1 - .9)
        with xf(c, 540, 800, 1, 0, fa):
            with xf(c, 430, 830, pop(t, a0 - .1, .35)):
                onion(c, 430, 830, 210, w=10)
                for sd in (-1, 1):
                    c.drawCircle(430 + sd * 62, 810, 13, paint(INK, fill=True))
                    line(c, [(430 + sd * 104, 750), (430 + sd * 34, 778)], INK, 9, amp=.6)
                line(c, [(390, 900), (430, 890), (470, 900)], INK, 8, amp=.6, curve=True)
            if t > ts:
                with xf(c, 770, 900, pop(t, ts, .35), 6):
                    line(c, [(650, 760), (890, 760), (890, 930), (770, 1060), (650, 930)], INK, 10, closed=True, fill=YEL, amp=1.2)
                    check(c, 768, 895, 1.7, seg(t, ts + .2, ts + .5), INK)
                with xf(c, 540, 430, pop(t, ts, .3)): pill(c, 'kendini savunuyor', 540, 430, 50, CORAL, PAPER)
    if t > n0 - .3:
        a = seg(t, n0 - .2, n0 + .1)
        tp = cap_start(3, 'parçalayınca', n0 + 1.0); tk = cap_start(3, 'karışır', n1 - .9)
        cut = seg(t, tp, tp + .35); mixu = smooth(seg(t, tk - .5, tk + .5))
        with xf(c, 540, 800, 1, 0, a):
            pill(c, 'soğan hücresi', 245, 420, 44, INK)
            box(c, 120, 500, 960, 1030, r=70, w=11, fill=PAPER)
            if mixu < 1: circ(c, 730, 765, 185, 195, color=TEAL, w=8, fill=WASH_T, alpha=1 - mixu, amp=1.4)
            R = random.Random(7)
            for k in range(9):
                x0, y0 = 730 + R.uniform(-115, 115), 765 + R.uniform(-125, 125); x1, y1 = R.uniform(190, 890), R.uniform(570, 960)
                dot(c, lerp(x0, x1, mixu) + 5 * math.sin(t * 3 + k), lerp(y0, y1, mixu) + 5 * math.cos(t * 2.6 + k), 20, YEL)
            for k in range(9):
                x0, y0 = R.uniform(180, 450), R.uniform(570, 960); x1, y1 = R.uniform(190, 890), R.uniform(570, 960)
                dot(c, lerp(x0, x1, mixu) + 5 * math.sin(t * 2.8 + k * 2), lerp(y0, y1, mixu) + 5 * math.cos(t * 3.1 + k), 18, CORAL)
            if cut > 0:
                line(c, [(506 + 12 * (-1) ** k, 505 + k * 58) for k in range(10)], INK, 8, seg(t, tp + .15, tp + .5), amp=1.0)
                knife(c, 506, lerp(325, 352, cut), 90, 1.0, alpha=cut)
            with xf(c, 300, 1100, 1): pill(c, 'kükürtlü madde', 300, 1100, 40, CORAL, PAPER)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(640, 1066, 820, 1134), 34, 34), paint(YEL, fill=True))
            txt(c, 'enzim', 730, 1114, 40, INK)
            if t > tk:
                with xf(c, 800, 420, pop(t, tk, .3), 3): pill(c, 'karıştı!', 800, 420, 50, TEAL, PAPER)

def scene3(c, t):
    e0, e1 = L(4); y0_, y1_ = L(5); j0, j1 = L(6); o0, o1 = L(7)
    fa = 1 - smooth(seg(t, y0_ - .3, y0_ - .05))
    if fa > .01:
        tE = cap_start(4, 'enzim', e0); tz = cap_start(4, 'yaşartan', e0 + 1.8)
        with xf(c, 540, 800, 1, 0, fa):
            with xf(c, 230, 700, pop(t, e0 - .15, .35)):
                circ(c, 230, 700, 150, color=INK, w=9, fill=PAPER, amp=1.4)
                R = random.Random(3)
                for k in range(10): dot(c, 230 + R.uniform(-90, 90), 700 + R.uniform(-90, 90), 19, YEL if k % 2 else CORAL)
                txt(c, 'karışım', 230, 905, 40, MUTE, 'med')
            arrow(c, (410, 700), (600, 700), INK, 9, seg(t, tE, tE + .35))
            with xf(c, 505, 630, pop(t, tE, .3)):
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(415, 596, 595, 664), 34, 34), paint(YEL, fill=True))
                txt(c, 'enzim', 505, 644, 40, INK)
            if t > tz:
                for k, (dx, dy, r) in enumerate(((0, 60, 62), (-70, -20, 50), (70, -30, 54), (-10, -120, 46), (60, -180, 36), (-60, -200, 30))):
                    with xf(c, 810 + dx, 700 + dy, pop(t, tz + k * .08, .3)):
                        puff(c, 810 + dx + 8 * math.sin(t * 2 + k), 700 + dy - 10 * math.sin(t * 1.5 + k * 2), r)
                with xf(c, 800, 905, pop(t, tz + .3, .3)): txt(c, 'göz yaşartan gaz', 800, 905, 44, CORAL)
                tear(c, 800, 1010 + 14 * math.sin(t * 4), 2.2, alpha=seg(t, tz + .5, tz + .7))
    if t > y0_ - .3:
        a = seg(t, y0_ - .2, y0_ + .1)
        tk = cap_start(7, 'kendiliğinden', o0 + 1.0); ts = cap_start(7, 'sanılıyordu', o1 - .8)
        with xf(c, 540, 800, 1, 0, a):
            with xf(c, 540, 440, pop(t, y0_ - .1, .35)): txt(c, '2002', 540, 490, 150, CORAL)
            if t > j0 - .1:
                with xf(c, 540, 650, pop(t, j0 - .1, .35)):
                    box(c, 150, 565, 930, 735, r=30, w=8, fill=PAPER)
                    txt(c, 'Japon araştırmacılar', 540, 648, 60, INK)
                    txt(c, 'gazı üreten enzimi buldu', 540, 702, 34, MUTE, 'med')
            if t > o0 - .1:
                with xf(c, 540, 900, pop(t, o0 - .1, .3)): txt(c, 'eski düşünce:', 540, 860, 40, MUTE, 'med')
            if t > tk:
                with xf(c, 540, 950, pop(t, tk, .3)):
                    txt(c, 'kendiliğinden oluşuyor', 540, 955, 62, INK)
                line(c, [(170, 940), (540, 932), (910, 942)], CORAL, 11, seg(t, ts, ts + .35), amp=1.2, curve=True)
            if t > ts + .2:
                with xf(c, 540, 1110, pop(t, ts + .2, .35), -2):
                    box(c, 200, 1050, 880, 1170, r=28, w=8, fill=YEL)
                    txt(c, 'bir enzim üretiyor', 540, 1130, 58, INK)
                check(c, 890, 1040, 1.3, seg(t, ts + .5, ts + .8))

def scene4(c, t):
    g0, g1 = L(8); s0, s1 = L(9); b0, b1 = L(10)
    gy = 1150
    tu = cap_start(8, 'gözüne', g1 - 1.0); tt = cap_start(9, 'tehlike', s1 - 1.0); ty = cap_start(10, 'gözyaşıyla', b0 + 1.0); ta = cap_start(10, 'atmaya', b1 - 1.2)
    ex, ey = 700, 740
    ground(c, 60, 420, gy, seg(t, g0 - .1, g0 + .3))
    with xf(c, 200, gy - 84, pop(t, g0 - .1, .35)): onion(c, 200, gy - 84, 84)
    with xf(c, ex, ey, pop(t, g0, .35)): eye(c, ex, ey, 250, 120, look=(-34 * seg(t, tu - .5, tu), 10))
    wsh = smooth(seg(t, ta, ta + .9))
    for k in range(6):
        ph = ((t - g0) * .42 + k / 6) % 1.0
        px = lerp(225, ex - 70, ph); py = lerp(gy - 200, ey + 10, ph) - 130 * math.sin(math.pi * ph)
        al = seg(t, g0 + .2 + k * .12, g0 + .5 + k * .12) * min(1, ph * 5) * (1 - seg(ph, .85, 1)) * (1 - wsh)
        puff(c, px, py, 27 + 7 * math.sin(k * 1.7), al)
    if t > s0 - .1:
        with xf(c, 250, 480, pop(t, s0 - .1, .35)):
            cloud(c, 250, 480, 150, 100, fill=WASH_P)
            line(c, [(165, 470), (212, 440), (250, 480), (292, 446), (335, 474)], CORAL, 7, amp=.8, curve=True)
            txt(c, 'beyin', 250, 540, 36, INK)
        line(c, [(ex - 250, ey - 8), (430, 670), (400, 610), (350, 590)], CORAL, 9, seg(t, s0 + .2, s0 + .7), amp=.8, curve=True)
        if t > tt:
            emark(c, 462, 500, 160, t, CORAL, pop(t, tt, .3))
            with xf(c, 720, 430, pop(t, tt, .3), 3): pill(c, 'tehlike!', 720, 430, 52, CORAL, PAPER)
    if t > ty:
        for k in range(5):
            ph = ((t - ty) * .9 + k * .2) % 1.0
            tear(c, ex - 150 + k * 75, ey + 112 + 250 * ph, 1.5, alpha=min(1, (t - ty) * 3) * (1 - ph ** 3))
    if t > ta:
        with xf(c, 700, 1195, pop(t, ta, .3)): pill(c, 'gözyaşı gazı yıkar', 700, 1195, 44, TEAL, PAPER)

def scene5(c, t):
    p0, p1 = L(11); k0, k1 = L(12); s0, s1 = L(13)
    tkb = cap_start(12, 'kör', k0 + 1.4); te = cap_start(12, 'ezer', tkb + .8); tf = cap_start(12, 'fışkırtır', k1 - .8)
    tks = cap_start(13, 'Keskin', s0); tyv = cap_start(13, 'yavaş', s0 + 1.2); taz = cap_start(13, 'az', s1 - 1.3)
    with xf(c, 540, 400, pop(t, p0 - .1, .35)): pill(c, 'ne yapmalı?', 540, 400, 54, INK)
    line(c, [(60, 1000), (1020, 1000)], INK, 10, seg(t, p0, p0 + .4), amp=1.4)
    for k, x in enumerate((290, 790)):
        with xf(c, x, 905, pop(t, p0 + .1 + k * .12, .35)): onion(c, x, 905, 95)
    if t > tkb - .1:
        dashes(c, (540, 500), (540, 1230), 9, MUTE, 6, seg(t, tkb - .1, tkb + .2))
        pr = smooth(seg(t, tkb + .2, te + .15))
        knife(c, 100, lerp(690, 775, pr) + (4 * math.sin(t * 30) if te < t < te + .5 else 0), 6, 1.05, dull=True, alpha=seg(t, tkb - .1, tkb + .1))
        with xf(c, 290, 1090, pop(t, tkb, .3), -2): pill(c, 'kör bıçak', 290, 1090, 50, CORAL, PAPER)
        if t > tf - .5:
            for k in range(11):
                ang = math.pi * (1.08 + .84 * k / 10); ph = ((t - tf) * 1.1 + k * .37) % 1.0
                r = 110 + 210 * ph
                tear(c, 290 + r * math.cos(ang), 900 + r * math.sin(ang) + 120 * ph * ph, .85 + .3 * (k % 3) / 2, alpha=seg(t, tf - .5, tf - .3) * (1 - ph ** 2))
        if t > tf + .3: cross(c, 290, 1190, 1.1, seg(t, tf + .3, tf + .6))
    if t > tks - .1:
        knife(c, 600, 745 + 22 * math.sin((t - tks) * 2.2), 6, 1.05, alpha=seg(t, tks - .1, tks + .1))
        with xf(c, 790, 1090, pop(t, tyv, .3), 2): pill(c, 'keskin + yavaş', 790, 1090, 50, TEAL, PAPER)
        if t > taz:
            for k in range(2):
                ph = ((t - taz) * .7 + k * .5) % 1.0
                tear(c, 790 + (-1) ** k * (120 + 60 * ph), 800 - 60 * ph + 90 * ph * ph, .8, alpha=1 - ph ** 2)
            check(c, 790, 1190, 1.2, seg(t, taz + .2, taz + .5))

def scene6(c, t):
    a0, a1 = L(14); d0, d1 = L(15); e0, e1 = L(16)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_Y)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    aha = t > d0 - .1
    pose = dict(FRONT, aR=64, eR=118, aL=10, eL=6, tilt=-6 if not aha else 0)
    pose = mix(pose, dict(FRONT, aR=64, eR=118, aL=148, eL=160 + 26 * math.sin(t * 9)), wv)
    def hold(p): onion(c, p[0] + 12, p[1] - 50, 46, w=5)
    me = fig(c, 540, gy, .95, 0, pose, 'sad' if not aha else 'happy', hold=hold)
    hx, hy = me['top']; cx_, cy_ = me['head']
    if not aha:
        for k in range(4):
            ph = ((t - a0) * 1.1 + k * .25) % 1.0
            tear(c, cx_ + (-16 if k % 2 == 0 else 16) * (1 + .5 * ph), cy_ + 12 + 130 * ph, .9, alpha=min(1, (t - a0) * 4) * (1 - ph ** 3))
        if t > a0 + .5: qmark(c, hx - 150, hy + 30, 150, t, CORAL, 1.0, pop(t, a0 + .5, .3))
    if d0 - .05 < t < e0 - .05:
        p = pop(t, d0 - .05, .35)
        with xf(c, 540, 430, lerp(.7, 1, p), 0, seg(t, d0 - .05, d0 + .1) * (1 - seg(t, e0 - .3, e0 - .08))):
            txt(c, 'Demek o yüzden!', 540, 452, 88, CORAL)
    if t > d0 - .05:
        with xf(c, hx - 170, hy - 30, pop(t, d0 - .05, .3)): bulb(c, hx - 170, hy - 30, .9, t=t)
    if t > e0 - .1:
        p = pop(t, e0 - .1, .35)
        with xf(c, 540, 400, lerp(.7, 1, p), 0, seg(t, e0 - .1, e0 + .1)):
            txt(c, 'Bir sonraki videoda', 540, 380, 74, INK)
            txt(c, 'görüşürüz!', 540, 482, 92, CORAL)
        line(c, [(310, 516), (440, 509), (600, 521), (770, 511)], INK, 9, seg(t, e0 + .4, e0 + .9), curve=True)


DRAW = {1: scene1, 2: scene2, 3: scene3, 4: scene4, 5: scene5, 6: scene6}

def frame(surface, t, k):
    c = surface.getCanvas()
    St.boil = int(t * FPS) // 5; St.n = 0
    c.clear(BG)
    a, b = scene_span(k)
    cov = k == SCENES[0] and t < COVER_T          # kapak: sesten onceki ilk kareler
    td = COVER_AT if cov else t
    if FMT == 'v': DRAW[k](c, td)
    else:
        c.save(); c.translate(ART_DX, ART_DY - ART_Y0); c.clipRect(skia.Rect.MakeLTRB(0, ART_Y0, 1080, ART_Y1))
        DRAW[k](c, td); c.restore()
    tag(c, hook=not cov)
    if cov: cover(c)
    else: captions(c, t)
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
                              '-c:v', 'libx264', '-crf', os.environ.get('CRF', '24'), '-preset', os.environ.get('PRESET', 'medium'), '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            frame(surface, fi / FPS, k)
            p.stdin.write(surface.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.replace(tmp, out); print('scene', k, f1 - f0, 'frames')
        else: sys.exit(1)
