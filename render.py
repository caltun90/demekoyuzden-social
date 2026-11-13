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

TITLE = 'Klavye Neden Karışık?'   # yatay formatta etiketin altinda gorunur
HOOK = 'Klavye neden karışık?'           # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['KLAVYE', 'NEDEN', 'KARIŞIK?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 8.5                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['klavyene'], 1: ['karmakarışık.'], 3: ['s', 'var.'], 4: ['alfabe', 'sırasında'], 5: ['bilgisayarda'], 6: ['daktiloda.'],
      7: ['1868:'], 9: ['alfabe', 'sırasındaydı.'], 10: ['değişti.'], 11: ['yaygın', 'anlatıya'], 12: ['takılan', 'harf', 'kollarını'],
      13: ['kyoto'], 14: ['ilk', 'kullanıcılardan'], 15: ['telgrafçılar.'], 16: ['tartışılıyor.'], 17: ['kesin'], 18: ['remington'],
      19: ['değişmedi.'], 20: ['orta', 'sıraya'], 22: ['izi'], 23: ['demek', 'o', 'yüzden!']}

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
    s = '1 DAKİKADA TARİH'
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
GY = 1090
ROWS = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM']
ROW_OFF = (0, .5, 1.5)
ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
PERM = list(range(26)); random.Random(11).shuffle(PERM)

def pill(c, s, cx, cy, size=34, col=INK, fg=BG):
    w = tw(s, size); h = size * 1.7
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 26, cy - h / 2, cx + w / 2 + 26, cy + h / 2), h / 2, h / 2), paint(col, fill=True))
    txt(c, s, cx, cy + size * .36, size, fg)

def key(c, x, y, kw, kh, ch, fill=PAPER, fg=INK, sc=1.0, rot=0.0, w=6):
    """tek klavye tusu (x, y: sol ust kose)"""
    with xf(c, x + kw / 2, y + kh / 2, sc, rot):
        box(c, x, y, x + kw, y + kh, r=kw * .2, w=w, fill=fill, amp=1.1)
        txt(c, ch, x + kw / 2, y + kh / 2 + kh * .19, kh * .52, fg)

def keyboard(c, x0, y0, kw, kh, gap, t, t0, hl=None, wob=0.0, lit=None, stag=.02):
    """Q klavye, 3 sira. hl: {harf: (dolgu, yazi)}; wob: tuslarin sallanmasi (0-1); lit: {harf: yandigi an}"""
    n = 0
    for r, row in enumerate(ROWS):
        for j, ch in enumerate(row):
            n += 1
            p = pop(t, t0 + n * stag, .22)
            if p <= 0: continue
            x = x0 + (ROW_OFF[r] + j) * (kw + gap); y = y0 + r * (kh + gap)
            f, fg = (hl or {}).get(ch, (PAPER, INK))
            if lit and ch in lit and t >= lit[ch]: p *= 1 + .18 * (1 - seg(t, lit[ch], lit[ch] + .25))
            key(c, x, y, kw, kh, ch, f, fg, p, wob * 8 * math.sin(t * 8 + n * 1.9))

def bursts(t0, t1, min_gap=.1):
    """satir icindeki ayri soylenen parcalarin (harflerin) baslangic anlari"""
    hop = .01; h = int(_SR * hop); x = _AU[int(t0 * _SR):int(t1 * _SR)]; n = len(x) // h
    rms = np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(axis=1) + 1e-12)
    v = rms > max(0.008, 0.07 * np.percentile(rms, 95))
    out, i, last = [], 0, -99
    while i < n:
        if v[i]:
            j = i
            while j < n and v[j]: j += 1
            if (i - last) * hop >= min_gap: out.append(t0 + i * hop)
            last = j; i = j
        else: i += 1
    return out

def typewriter(c, x, y, s=1.0, body=TEAL, paper=True):
    """daktilo, onden gorunum (x: orta, y: taban)"""
    w = max(4, 8 * s)
    if paper:
        box(c, x - 78 * s, y - 300 * s, x + 78 * s, y - 170 * s, r=6 * s, w=w * .8, fill=PAPER, amp=1)
        for k in range(3):
            yy = y - (272 - k * 28) * s
            line(c, [(x - 50 * s, yy), (x + (50 - 26 * (k == 2)) * s, yy)], MUTE, max(3, 5 * s), amp=.6)
    box(c, x - 170 * s, y - 196 * s, x + 170 * s, y - 150 * s, r=20 * s, w=w, fill=INK, amp=1)
    for sd in (-1, 1): circ(c, x + sd * 188 * s, y - 173 * s, 18 * s, color=INK, w=w, fill=PAPER, amp=.8, n=10)
    line(c, [(x - 140 * s, y - 150 * s), (x + 140 * s, y - 150 * s), (x + 185 * s, y), (x - 185 * s, y)], INK, w, closed=True, fill=body, amp=1.2)
    for r, n in enumerate((8, 9, 8)):
        yy = y - (112 - r * 38) * s; span = (112 + r * 20) * s
        for j in range(n):
            xx = x - span + 2 * span * j / (n - 1)
            c.drawCircle(xx, yy, 11 * s, paint(PAPER, fill=True)); c.drawCircle(xx, yy, 11 * s, paint(INK, max(2.5, 4 * s)))

def laptop(c, x, y, s=1.0):
    """dizustu bilgisayar (x: orta, y: taban)"""
    w = max(4, 8 * s)
    box(c, x - 125 * s, y - 170 * s, x + 125 * s, y - 20 * s, r=12 * s, w=w, fill=PAPER, amp=1.2)
    for k in range(3):
        yy = y - (130 - k * 34) * s
        line(c, [(x - 85 * s, yy), (x + (85 - 50 * (k == 2)) * s, yy)], MUTE, max(3, 6 * s), amp=.6)
    line(c, [(x - 125 * s, y - 20 * s), (x + 125 * s, y - 20 * s), (x + 160 * s, y), (x - 160 * s, y)], INK, w, closed=True, fill=PAPER, amp=1)

def phone(c, x, y, s=1.0):
    """telefon (x: orta, y: taban)"""
    box(c, x - 54 * s, y - 190 * s, x + 54 * s, y, r=16 * s, w=max(4, 7 * s), fill=PAPER, amp=1)
    for k in range(2):
        line(c, [(x - 30 * s, y - (152 - k * 26) * s), (x + (30 - 22 * k) * s, y - (152 - k * 26) * s)], MUTE, max(3, 5 * s), amp=.5)
    for r in range(3):
        for j in range(5 - (r == 2)):
            xx = x - 36 * s + j * 18 * s + (9 * s if r == 2 else 0); yy = y - 72 * s + r * 20 * s
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(xx - 6 * s, yy - 6 * s, xx + 6 * s, yy + 6 * s), 2, 2), paint(INK, fill=True))

def typebars(c, cx, cy, R, strike=None, jam=0.0):
    """daktilonun harf kollari: yay uzerinde durur, ortadaki baski noktasina vurur; jam: iki komsu kol takilir"""
    line(c, [(cx - 170, cy - 22), (cx + 170, cy - 22)], INK, 22, amp=1)
    n = 11
    for i in range(n):
        a = math.radians(22 + 136 * i / (n - 1))
        px, py = cx + R * math.cos(a), cy + R * math.sin(a)
        u, col = .32, INK
        if strike is not None and i == strike[0]: u = lerp(.32, .96, strike[1])
        if i in (5, 6) and jam > 0: u = lerp(.32, .9, jam); col = CORAL
        ex, ey = lerp(px, cx, u), lerp(py, cy, u)
        line(c, [(px, py), (ex, ey)], col, 9, amp=1)
        c.drawCircle(ex, ey, 14, paint(col, fill=True))
        c.drawCircle(px, py, 9, paint(PAPER, fill=True)); c.drawCircle(px, py, 9, paint(INK, 5))

def pole(c, x, y0, y1):
    """telgraf diregi"""
    line(c, [(x, y1), (x, y0)], INK, 11, amp=1.2)
    line(c, [(x - 56, y0 + 36), (x + 56, y0 + 36)], INK, 9, amp=1)
    for dx in (-44, 44): c.drawCircle(x + dx, y0 + 22, 10, paint(TEAL, fill=True))

def arrow(c, x0, x1, y, prog=1.0, color=INK, w=8):
    line(c, [(x0, y), (x1, y)], color, w, prog, amp=1)
    if prog >= 1: line(c, [(x1 - 20, y - 18), (x1, y), (x1 - 20, y + 18)], color, w, amp=.8)

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1); d0, d1 = L(2); e0, e1 = L(3); f0, f1 = L(4)
    KX, KY, KW, KH, KG = 90, 392, 81, 92, 10
    gy = 1140
    wash(c, 56, 352, 1024, 728, WASH_Y)
    ta = d0; tb = cap_start(3, 'B', e0); ts = cap_start(3, 'S', e0 + .8); tq = f0 + .15
    wob = smooth(seg(t, b0, b0 + .25)) * (1 - smooth(seg(t, b1 + .05, b1 + .3)))
    hl = {}
    if t >= ta: hl['A'] = (YEL, INK)
    if t >= ts: hl['S'] = (CORAL, PAPER)
    keyboard(c, KX, KY, KW, KH, KG, t, a0 - .25, hl, wob, lit={'A': ta, 'S': ts})
    look = smooth(seg(t, a0, a0 + .3)) * (1 - smooth(seg(t, d0 - .2, d0 + .1)))
    stuck = smooth(seg(t, f0 - .1, f0 + .3))
    pose = mix(FRONT, dict(FRONT, aR=150, eR=162, tilt=-4), look)                       # klavyeyi gosteriyor
    pose = mix(pose, dict(FRONT, aR=125, eR=205 + 5 * math.sin(t * 9), aL=14, eL=8, tilt=6), stuck)   # kafasini kasiyor
    ex = 'smile' if t < b0 else ('oh' if t < f0 - .1 else 'confused')
    c.drawOval(skia.Rect.MakeLTRB(90, gy - 14, 370, gy + 20), paint(0xFFEDE3D0, fill=True))
    fig(c, 230, gy, .9, 0, pose, ex)
    kx, ky, ks = 470, 806, 150                                                          # buyuk tuslar: A, (B degil) S
    pa = pop(t, ta, .3)
    if pa > 0: key(c, kx, ky, ks, ks, 'A', YEL, INK, pa, 0, 9)
    if t >= tb:
        mv = smooth(seg(t, ts - .15, ts + .15))
        bx = lerp(kx + ks + 30, kx + 2 * (ks + 30) + 10, mv)
        with xf(c, bx + ks / 2, ky + ks / 2, pop(t, tb, .3) * lerp(1, .72, mv)):
            key(c, bx, ky, ks, ks, 'B', PAPER, MUTE, 1, 0, 9)
            cp_ = seg(t, tb + .3, tb + .6)                                               # ince carpi: B okunur kalsin
            line(c, [(bx + 22, ky + 22), (bx + ks - 22, ky + ks - 22)], CORAL, 12, seg(cp_, 0, .5), amp=1.2)
            line(c, [(bx + ks - 22, ky + 22), (bx + 22, ky + ks - 22)], CORAL, 12, seg(cp_, .5, 1), amp=1.2)
    ps = pop(t, ts, .3)
    if ps > 0: key(c, kx + ks + 30, ky, ks, ks, 'S', CORAL, PAPER, ps, 0, 9)
    np_ = pop(t, tq, .3)
    if np_ > 0:
        with xf(c, 730, 1060, np_, -2): pill(c, 'NEDEN A-B-C DEĞİL?', 730, 1060, 42, INK, PAPER)
    qp = pop(t, tq + .2, .3)
    if qp > 0: qmark(c, 96, 925, 150, t, CORAL, sc=qp)

def scene2(c, t):
    a0, a1 = L(5); b0, b1 = L(6)
    tx_ = cap_start(5, 'değil', a1 - .4); td = cap_start(6, 'yıl', b0 + .9)
    lp = pop(t, a0 - .1, .3)
    if lp > 0:
        dim = 1 - .55 * smooth(seg(t, td - .1, td + .3))
        with xf(c, 540, 560, lp, 0, dim): laptop(c, 540, 660, 1.15)
        cross(c, 540, 548, 2.3, seg(t, tx_, tx_ + .35))
    pp = pop(t, b0, .3)
    if pp > 0:
        with xf(c, 540, 762, pp): pill(c, 'YAKLAŞIK 150 YIL ÖNCE', 540, 762, 40, INK, PAPER)
    tp = pop(t, td - .1, .35)
    if tp > 0:
        c.drawOval(skia.Rect.MakeLTRB(540 - 270 * tp, 1184, 540 + 270 * tp, 1224), paint(0xFFEDE3D0, fill=True))
        with xf(c, 540, 1040, tp): typewriter(c, 540, 1200, 1.2)
        ba = seg(t, td + .2, td + .45)
        if ba > 0:
            for sd in (-1, 1): burst(c, 540 + sd * 330, 930, 26, 52, 6, CORAL, 7, ba)

def scene3(c, t):
    a0, a1 = L(7); b0, b1 = L(8); i0, i1 = L(9); j0, j1 = L(10); g0, g1 = L(11); h0, h1 = L(12)
    al = seg(t, a0 - .1, a0 + .3)
    with xf(c, 540, 380, 1, 0, al):
        txt(c, 'Sholes · 1868', 540, 376, 48, INK)
        txt(c, 'ilk daktilo modelleri', 540, 428, 32, MUTE, 'med')
    gone = 1 - smooth(seg(t, g0 - .25, g0))
    tp = pop(t, a0 + .15, .35)
    if tp > 0 and gone > 0.01:                                 # daktilo (kisi cizilmez)
        with xf(c, 540, 1000, tp, 0, gone):
            c.drawOval(skia.Rect.MakeLTRB(300, 1136, 780, 1172), paint(0xFFEDE3D0, fill=True))
            typewriter(c, 540, 1150, 1.05)
    for i, ch in enumerate(ALPHA):                             # alfabe sirasindaki tuslar, sonra karisiyor
        p = pop(t, i0 - .2 + i * .028, .24)
        if p <= 0: continue
        mv = smooth(seg(t, j0 + .1 + i * .02, j0 + 1.3 + i * .02))
        s0, s1 = i, PERM[i]
        x = lerp(89 + (s0 % 13) * 70, 89 + (s1 % 13) * 70, mv)
        y = lerp(484 + (s0 // 13) * 82, 484 + (s1 // 13) * 82, mv) - 26 * math.sin(math.pi * mv) * (1 if i % 2 else -1)
        key(c, x, y, 62, 72, ch, PAPER, INK, p, 10 * math.sin(math.pi * mv) * (1 if i % 2 else -1), 5)
    tl = cap_start(9, 'alfabe', i0)
    la = seg(t, tl + .2, tl + .45) * (1 - seg(t, j0 + .2, j0 + .45))
    if la > 0:
        txt(c, 'alfabe sırasında', 520, 716, 40, TEAL, alpha=la)
        if la >= 1: check(c, 520 + tw('alfabe sırasında', 40) / 2 + 44, 702, .7, seg(t, tl + .45, tl + .7))
    lb = seg(t, j0 + .5, j0 + .75) * (1 - seg(t, g0 - .3, g0 - .1))
    if lb > 0: txt(c, 'harflerin yeri değişti', 540, 716, 40, CORAL, alpha=lb)
    if t > g0 - .1:                                            # yaygin anlati: takilan harf kollari
        gp = pop(t, g0 - .05, .3)
        with xf(c, 540, 706, gp): pill(c, 'YAYGIN ANLATI', 540, 706, 38, INK, PAPER)
        fa = seg(t, g0 + .2, g0 + .5)
        tk = cap_start(12, 'takılan', h0 + 1.0) + .35
        tz = cap_start(12, 'ayırmaktı', h1 - .8)
        strike = None
        if h0 <= t < tk:
            k = int((t - h0) / .22); strike = ((2, 8, 4, 9, 1, 7, 3)[k % 7], math.sin(math.pi * (((t - h0) / .22) % 1)))
        jam = clamp(pop(t, tk, .2)) if t >= tk else 0
        with xf(c, 540, 860, 1, 0, fa): typebars(c, 540, 862, 285, strike, jam)
        if jam > 0:
            burst(c, 540, 884, 36, 66 + 6 * math.sin(t * 10), 9, CORAL, 7, seg(t, tk, tk + .15))
            with xf(c, 790, 800, pop(t, tk + .1, .3), 5): txt(c, 'takıldı!', 800, 808, 48, CORAL)
        za = seg(t, tz, tz + .25)
        if za > 0: txt(c, 'amaç: bu kolları ayırmak', 540, 1222, 40, INK, alpha=za)

def scene4(c, t):
    a0, a1 = L(13); b0, b1 = L(14); d0, d1 = L(15); e0, e1 = L(16)
    al = seg(t, a0 - .1, a0 + .3)
    with xf(c, 540, 380, 1, 0, al):
        txt(c, 'Kyoto Üniversitesi', 540, 376, 48, INK)
        txt(c, "Yasuoka ve Yasuoka'nın araştırması", 540, 428, 32, MUTE, 'med')
    ti = cap_start(14, 'ilk', b0 + .7)
    dg = 1 - smooth(seg(t, ti - .35, ti - .1))
    dp = pop(t, a0 + .3, .35)
    if dp > 0 and dg > 0.01:                                   # arastirma makalesi (kisi cizilmez)
        with xf(c, 540, 740, dp, -3, dg):
            box(c, 360, 520, 720, 980, r=18, w=8, fill=PAPER)
            txt(c, "QWERTY'nin", 540, 606, 44, INK); txt(c, 'öncesi', 540, 660, 44, CORAL)
            for k in range(5): line(c, [(410, 730 + k * 46), (670 - 80 * (k == 4), 730 + k * 46)], MUTE, 7, amp=.8)
    if t >= ti - .1:
        pp = pop(t, ti, .3)
        if pp > 0:
            with xf(c, 540, 520, pp): pill(c, 'İLK KULLANICILAR', 540, 520, 40, TEAL, PAPER)
        gy = 1000
        op = pop(t, ti + .15, .35)
        if op > 0:
            typing = t >= d0
            with xf(c, 620, 900, op):
                c.drawOval(skia.Rect.MakeLTRB(400, gy - 12, 600, gy + 16), paint(0xFFEDE3D0, fill=True))
                line(c, [(565, 872), (915, 872)], INK, 10, amp=1.2)                    # masa
                line(c, [(605, 876), (605, gy)], INK, 9, amp=1); line(c, [(877, 876), (877, gy)], INK, 9, amp=1)
                typewriter(c, 735, 866, .62)
                fig(c, 500, gy, .75, 1, dict(STAND, aR=58, eR=96 + (7 * math.sin(t * 15) if typing else 0), aL=50, eL=92 - (7 * math.sin(t * 15) if typing else 0)),
                    'smile' if typing else 'flat')
        ma = seg(t, d0 - .1, d0 + .25)                          # Mors kodu telden geliyor
        if ma > 0:
            with xf(c, 150, 800, 1, 0, ma):
                pole(c, 140, 610, gy)
                line(c, [(0, 660), (96, 632)], INK, 5, amp=1, curve=True)
                line(c, [(184, 632), (300, 688), (452, 716)], INK, 5, amp=1, curve=True)
            for k in range(6):
                u = (t * .32 + k / 6) % 1
                x = lerp(196, 446, u); y = 632 + 84 * (1 - (1 - u) ** 2) - 24
                aa = ma * min(1, u * 8, (1 - u) * 8)
                if k % 3 == 1: line(c, [(x - 15, y - 4), (x + 15, y + 4)], CORAL, 11, alpha=aa, amp=.3)
                else: c.drawCircle(x, y, 8, paint(CORAL, fill=True, alpha=aa))
            txt(c, 'Mors kodu', 268, 800, 36, CORAL, alpha=seg(t, d0 + .2, d0 + .45))
            ty = cap_start(15, 'döken', d0 + 1.2) - .2
            for k, ch in enumerate('ABC'):
                lp = pop(t, ty + k * .22, .28)
                if lp > 0:
                    with xf(c, 681 + k * 56, 648, lp): txt(c, ch, 681 + k * 56, 662, 46, TEAL)
            txt(c, 'yazı', 900, 660, 36, TEAL, alpha=seg(t, ty + .6, ty + .85))
        if t > e0 - .1:                                        # iki aciklama: kesin degil
            tt = cap_start(16, 'tartışılıyor', e1 - .9)
            p1 = pop(t, e0, .3); p2 = pop(t, e0 + .35, .3)
            if p1 > 0:
                with xf(c, 268, 1130, p1, -2): pill(c, 'TAKILAN KOLLAR', 268, 1130, 34, INK, PAPER)
            if p2 > 0:
                with xf(c, 818, 1130, p2, 2): pill(c, 'TELGRAFÇILAR', 818, 1130, 34, TEAL, PAPER)
            qp = pop(t, tt - .1, .3)
            if qp > 0: qmark(c, 548, 1172, 128, t, CORAL, sc=qp)

def scene5(c, t):
    a0, a1 = L(17); b0, b1 = L(18); d0, d1 = L(19)
    hp = pop(t, a0, .35)
    if hp > 0:
        with xf(c, 500, 400, lerp(.7, 1, hp), 0, seg(t, a0, a0 + .15)): txt(c, 'Kesin olan', 500, 426, 76, INK)
        check(c, 500 + tw('Kesin olan', 76) / 2 + 66, 400, 1.1, seg(t, a0 + .3, a0 + .6))
    tr = cap_start(18, 'Remington', b0 + .6); ty = cap_start(18, 'yayıldı', b1 - .6)
    tp = pop(t, b0 - .1, .35)
    if tp > 0:
        with xf(c, 540, 680, tp): typewriter(c, 540, 812, .9, body=CORAL)
    rp = pop(t, tr, .3)
    if rp > 0:
        with xf(c, 540, 866, rp): pill(c, 'REMINGTON · 1874', 540, 866, 38, INK, PAPER)
    for k, (mx, my) in enumerate(((150, 620), (930, 620), (150, 750), (930, 750), (150, 880), (930, 880))):   # yayiliyor
        mp = pop(t, ty - .1 + k * .1, .28)
        if mp > 0:
            with xf(c, mx, my - 45, mp): typewriter(c, mx, my, .3, body=CORAL)
    t2 = cap_start(19, 've', d0 + .9); t3 = cap_start(19, 'değişmedi', d1 - .7)
    by = 1150
    for k, (dx, tt, name) in enumerate(((200, d0, 'daktilo'), (540, t2, 'bilgisayar'), (880, t3, 'telefon'))):   # ayni dizilim, bugune kadar
        p = pop(t, tt, .3)
        if p <= 0: continue
        with xf(c, dx, by - 80, p):
            if k == 0: typewriter(c, dx, by, .5, body=CORAL)
            elif k == 1: laptop(c, dx, by, .78)
            else: phone(c, dx, by, .8)
        txt(c, name, dx, by + 52, 30, MUTE, 'med', alpha=seg(t, tt + .15, tt + .35))
        with xf(c, dx, 956, pop(t, tt + .15, .28)): pill(c, 'QWERTY', dx, 956, 28, YEL, INK)
        if k: arrow(c, dx - 220, dx - 130, by - 76, seg(t, tt - .15, tt + .1), TEAL)

LET_T = bursts(*L(21))
if len(LET_T) != 7: LET_T = [lerp(L(21)[0], L(21)[1], k / 7.6) for k in range(7)]

def scene6(c, t):
    a0, a1 = L(20); b0, b1 = L(21); d0, d1 = L(22); e0, e1 = L(23); f0, f1 = L(24)
    KX, KY, KW, KH, KG = 115, 548, 76, 84, 10
    gy = 1245
    lit = {ch: LET_T[k] for k, ch in enumerate('DFGHJKL')}
    hl = {ch: (YEL, INK) for ch in lit if t >= lit[ch]}
    ra = smooth(seg(t, a0, a0 + .3))
    if ra > 0: wash(c, 96, KY + KH + KG - 10, 984, KY + 2 * KH + KG + 10, WASH_T, ra, r=24)      # orta sira
    keyboard(c, KX, KY, KW, KH, KG, t, a0 - .3, hl, lit=lit)
    pa = pop(t, a0, .3) * (1 - smooth(seg(t, e0 - .35, e0 - .1)))
    if pa > 0.01:
        with xf(c, 540, 440, pa): pill(c, 'Q KLAVYE · ORTA SIRA', 540, 440, 40, TEAL, PAPER)
    CW, CG, SY = 84, 10, 868
    SX = (1080 - (9 * CW + 8 * CG)) / 2
    for j, ch in enumerate('DEFGHIJKL'):                       # alfabe seridi: D E F G H I J K L
        p = pop(t, d0 - .1 + j * .04, .25)
        if p <= 0: continue
        miss = ch in 'EI'
        on = not miss and t >= d0 + .4 + j * .07
        key(c, SX + j * (CW + CG), SY, CW, 80, ch, YEL if on else PAPER, MUTE if miss else INK, p)
    la = seg(t, d0 + .3, d0 + .55)
    if la > 0:
        txt(c, 'eski alfabe', 255, 1080, 38, TEAL, alpha=la); txt(c, 'sırasının izi', 255, 1128, 38, TEAL, alpha=la)
    lb = seg(t, d0 + 1.2, d0 + 1.45)
    if lb > 0:
        txt(c, 'E ve I', 835, 1080, 36, MUTE, 'med', alpha=lb); txt(c, 'üst sırada', 835, 1128, 36, MUTE, 'med', alpha=lb)
    look = smooth(seg(t, a0, a0 + .3)) * (1 - smooth(seg(t, e0 - .3, e0 - .05)))
    ah = clamp(pop(t, e0 - .05, .3)) * (1 - smooth(seg(t, f0 - .15, f0 + .15)))
    wv = smooth(seg(t, f0 - .1, f0 + .3))
    pose = mix(FRONT, dict(FRONT, aR=150, eR=165, tilt=-4), look)
    pose = mix(pose, dict(FRONT, aL=150, eL=166, aR=150, eR=166), ah)
    pose = mix(pose, dict(FRONT, aR=148, eR=160 + 26 * math.sin(t * 9), aL=12, eL=8), wv)
    c.drawOval(skia.Rect.MakeLTRB(440, gy - 10, 640, gy + 12), paint(0xFFEDE3D0, fill=True))
    fig(c, 540, gy, .6, 0, pose, 'oh' if t < e0 - .1 else 'happy')
    if e0 - .05 < t < f0 - .05:
        p = pop(t, e0 - .05, .35)
        with xf(c, 540, 430, lerp(.7, 1, p), 0, seg(t, e0 - .05, e0 + .1) * (1 - seg(t, f0 - .3, f0 - .08))):
            txt(c, 'Demek o yüzden!', 540, 452, 88, CORAL)
    if t > f0 - .1:
        p = pop(t, f0 - .1, .35)
        with xf(c, 540, 400, lerp(.7, 1, p), 0, seg(t, f0 - .1, f0 + .1)):
            txt(c, 'Bir sonraki videoda', 540, 380, 74, INK)
            txt(c, 'görüşürüz!', 540, 482, 92, CORAL)
        line(c, [(310, 516), (440, 509), (600, 521), (770, 511)], INK, 9, seg(t, f0 + .4, f0 + .9), curve=True)

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
                              '-c:v', 'libx264', '-crf', '17', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            frame(surface, fi / FPS, k)
            p.stdin.write(surface.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.replace(tmp, out); print('scene', k, f1 - f0, 'frames')
        else: sys.exit(1)
