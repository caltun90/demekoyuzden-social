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

TITLE = 'Nane ve acı biber'   # yatay formatta etiketin altinda gorunur
HOOK = 'Nane neden serinletir?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['NANE NEDEN', 'SERİNLETİR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 3.75                          # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['soğuk', 'değil.'], 1: ['sıcak', 'değil.'], 2: ['serinletir,', 'yakar?'], 3: ['alıcılar'], 4: ['üşüyoruz!'], 5: ['yanıyoruz!'], 6: ['mentol,', 'anahtar'], 7: ['serinlik'], 8: ['ferah'], 9: ['kapsaisin'], 10: ['yanlış', 'alarm'], 11: ['serinlemeye'], 12: ['zorlandı.'], 13: ['nobel', 'ödülü'], 14: ['ferahlatır,', 'yakar'], 15: ['demek', 'o', 'yüzden!']}


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

# ---------- video scenes ----------
LEAF = 0xFF5DBE8A
WASH_C = 0xFFDDEFF7
WASH_H = 0xFFFBE0D6

def brain(c, x, y, s=1.0):
    cloud(c, x, y, 330 * s, 215 * s, fill=WASH_P, w=10)
    for k, (dx, dy) in enumerate(((-170, -70), (10, -110), (170, -40), (-80, 50))):
        line(c, [(x + (dx - 70) * s, y + dy * s), (x + (dx - 25) * s, y + (dy - 34) * s), (x + (dx + 20) * s, y + (dy + 6) * s), (x + (dx + 70) * s, y + (dy - 26) * s)], CORAL, 8, amp=.8, curve=True)

def leaf(c, x, y, s=1.0):
    pts = [(x, y - 160 * s), (x + 84 * s, y - 70 * s), (x + 88 * s, y + 40 * s), (x, y + 150 * s), (x - 88 * s, y + 40 * s), (x - 84 * s, y - 70 * s)]
    line(c, pts, INK, max(5, 9 * s), closed=True, fill=LEAF, curve=True, amp=1.2)
    line(c, [(x, y - 118 * s), (x, y + 196 * s)], INK, max(4, 7 * s), amp=.8)
    for dy in (-56, 4, 64):
        for sd in (-1, 1):
            line(c, [(x, y + (dy + 22) * s), (x + sd * 50 * s, y + (dy - 22) * s)], INK, max(3, 5 * s), amp=.6)

def pepper(c, x, y, s=1.0):
    pts = [(x - 50 * s, y - 118 * s), (x + 44 * s, y - 122 * s), (x + 78 * s, y - 40 * s), (x + 66 * s, y + 66 * s), (x + 16 * s, y + 150 * s), (x - 66 * s, y + 196 * s),
           (x - 24 * s, y + 110 * s), (x - 16 * s, y + 30 * s), (x - 62 * s, y - 40 * s)]
    line(c, pts, INK, max(5, 9 * s), closed=True, fill=CORAL, curve=True, amp=1.2)
    st = [(x - 4 * s, y - 118 * s), (x - 16 * s, y - 168 * s), (x + 26 * s, y - 196 * s)]
    line(c, st, INK, max(8, 20 * s), amp=.4, curve=True); St.n -= 1
    line(c, st, LEAF, max(3, 8 * s), amp=.4, curve=True)
    line(c, [(x + 36 * s, y - 70 * s), (x + 44 * s, y - 10 * s), (x + 34 * s, y + 50 * s)], PAPER, max(4, 8 * s), alpha=.8, amp=.5, curve=True)

def flake(c, x, y, r, col=TEAL, w=6, alpha=1.0, rot=0.0):
    for i in range(3):
        a = math.pi * i / 3 + rot
        line(c, [(x - r * math.cos(a), y - r * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))], col, w, alpha=alpha, amp=.4)

def flame(c, x, y, s=1.0, t=0.0, alpha=1.0):
    k = 1 + .1 * math.sin(t * 11)
    p = skia.Path(); p.moveTo(x, y - 74 * s * k); p.cubicTo(x + 54 * s, y - 20 * s, x + 48 * s, y + 42 * s, x, y + 46 * s)
    p.cubicTo(x - 48 * s, y + 42 * s, x - 54 * s, y - 6 * s, x - 22 * s, y - 34 * s); p.cubicTo(x - 14 * s, y - 12 * s, x - 6 * s, y - 40 * s, x, y - 74 * s * k); p.close()
    c.drawPath(p, paint(CORAL, fill=True, alpha=alpha)); c.drawPath(p, paint(INK, max(3, 6 * s), alpha=alpha))
    c.drawCircle(x, y + 14 * s, 15 * s, paint(YEL, fill=True, alpha=alpha))

def membrane(c, x0, x1, y, prog=1.0):
    for dy in (-34, 34): line(c, [(x0, y + dy), (x1, y + dy)], MUTE, 10, prog, amp=1.2)

def receptor(c, x, y, col, fill, op=0.0, s=1.0, t=0.0):
    """zara gomulu kapi; op 0 kapali, 1 acik"""
    g = 5 * s + 34 * s * op
    for sd in (-1, 1):
        x0, x1 = x + sd * g, x + sd * (g + 64 * s)
        box(c, min(x0, x1), y - 86 * s, max(x0, x1), y + 86 * s, r=24 * s, w=max(5, 8 * s), fill=fill, amp=1)
    if op > .5:
        for k in range(3):
            ph = (t * 1.6 + k / 3) % 1
            c.drawCircle(x + 9 * s * math.sin(k * 2.1), y - 70 * s + 170 * s * ph, 9 * s, paint(col, fill=True, alpha=math.sin(math.pi * ph)))

def thermo(c, x, y, s=1.0, lvl=.5, col=CORAL):
    box(c, x - 17 * s, y - 120 * s, x + 17 * s, y + 60 * s, r=16 * s, w=max(4, 7 * s), fill=PAPER, amp=.6)
    circ(c, x, y + 78 * s, 32 * s, color=INK, w=max(4, 7 * s), fill=col, amp=.6, n=10)
    wash(c, x - 7 * s, y + 55 * s - 150 * s * lvl, x + 7 * s, y + 60 * s, col, r=5)

def key(c, x, y, s=1.0, col=TEAL):
    line(c, [(x, y - 14 * s), (x, y + 46 * s)], INK, max(5, 9 * s), amp=.4)
    for dy in (22, 42): line(c, [(x, y + dy * s), (x + 17 * s, y + dy * s)], INK, max(4, 7 * s), amp=.3)
    circ(c, x, y - 36 * s, 23 * s, color=INK, w=max(4, 7 * s), fill=col, amp=.5, n=10)

def mouse(c, x, y, s=1.0, d=1, t=0.0):
    line(c, [(x - d * 62 * s, y - 30 * s), (x - d * 112 * s, y - 52 * s + 9 * s * math.sin(t * 6)), (x - d * 156 * s, y - 26 * s)], INK, max(4, 6 * s), amp=.6, curve=True)
    for dx in (-36, 30): line(c, [(x + dx * s, y - 12 * s), (x + dx * s + 7 * s * math.sin(t * 14 + dx), y)], INK, max(4, 6 * s), amp=.3)
    circ(c, x, y - 48 * s, 72 * s, 42 * s, color=INK, w=max(5, 8 * s), fill=PAPER, amp=1, n=12)
    circ(c, x + d * 56 * s, y - 96 * s, 22 * s, color=INK, w=max(4, 7 * s), fill=WASH_P, amp=.6, n=9)
    circ(c, x + d * 72 * s, y - 54 * s, 36 * s, 30 * s, color=INK, w=max(5, 8 * s), fill=PAPER, amp=.8, n=10)
    c.drawCircle(x + d * 84 * s, y - 60 * s, 5 * s, paint(INK, fill=True))
    c.drawCircle(x + d * 108 * s, y - 50 * s, 7 * s, paint(CORAL, fill=True))

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1); q0, q1 = L(2)
    tsd = cap_start(0, 'soğuk', a0 + .7); tsc = cap_start(1, 'sıcak', b0 + .6)
    tse = cap_start(2, 'serinletir', q0 + 1.4); tya = cap_start(2, 'öbürü', q1 - 1.3)
    wash(c, 60, 340, 530, 960, WASH_C)
    with xf(c, 295, 610, pop(t, a0 - .05, .3), 7 * math.sin(t * 2.4)): leaf(c, 295, 600, 1.12)
    if t > a0:
        for k, (x, y) in enumerate(((130, 440), (465, 430), (125, 760), (470, 770))):
            with xf(c, x, y, pop(t, a0 + .07 * k, .25)): flake(c, x, y, 32 + 5 * math.sin(t * 3 + k), TEAL, 7, rot=t * .9 + k)
    if t > tsd:
        with xf(c, 295, 884, pop(t, tsd, .3), -4): pill(c, 'soğuk değil', 295, 884, 50, INK)
    if t > b0 - .15:
        wash(c, 550, 340, 1020, 960, WASH_H, seg(t, b0 - .15, b0 + .05))
        with xf(c, 785, 600, pop(t, b0 - .1, .3), -6 * math.sin(t * 2.4)): pepper(c, 790, 590, 1.05)
        for k, (x, y) in enumerate(((630, 460), (950, 470), (640, 770), (950, 760))):
            with xf(c, x, y, pop(t, b0 + .07 * k, .25)): flame(c, x, y, .56, t + k)
    if t > tsc:
        with xf(c, 785, 884, pop(t, tsc, .3), 4): pill(c, 'sıcak değil', 785, 884, 50, INK)
    if t > q0 - .1:
        with xf(c, 540, 1256, pop(t, q0 - .1, .3)):
            fig(c, 540, 1256, .6, 0, dict(FRONT, aL=62, eL=150, aR=62, eR=150), 'confused')
    if t > tse:
        with xf(c, 250, 1090, pop(t, tse, .3), -3): pill(c, 'serinletir?', 250, 1090, 50, TEAL, PAPER)
    if t > tya:
        with xf(c, 840, 1090, pop(t, tya, .3), 3): pill(c, 'yakar?', 840, 1090, 50, CORAL, PAPER)

def scene2(c, t):
    a0, a1 = L(3); s0, s1 = L(4); h0, h1 = L(5)
    tal = cap_start(3, 'sıcaklığı', a0 + 1.4)
    tso = cap_start(4, 'açılır', s0 + .8); tus = cap_start(4, 'Üşüyoruz', s1 - .8)
    thi = cap_start(5, 'açılır', h0 + 1.6); tyn = cap_start(5, 'Yanıyoruz', h1 - .8)
    my = 960
    membrane(c, 90, 990, my, seg(t, a0 - .1, a0 + .4))
    if t > a0 + .2:
        with xf(c, 300, my, pop(t, a0 + .2, .3)): receptor(c, 300, my, TEAL, WASH_C, smooth(seg(t, tso, tso + .3)), 1, t)
        with xf(c, 780, my, pop(t, a0 + .35, .3)): receptor(c, 780, my, CORAL, WASH_H, smooth(seg(t, thi, thi + .3)), 1, t)
    if t > a0 - .1:
        with xf(c, 540, 1190, pop(t, a0 - .1, .3)): pill(c, 'dilinde ve derinde', 540, 1190, 44, INK)
    if t > tal:
        with xf(c, 540, 386, pop(t, tal, .35), -1.5):
            box(c, 200, 334, 880, 438, r=30, w=9, fill=YEL)
            txt(c, 'sıcaklık alıcıları', 540, 408, 62, INK)
        with xf(c, 300, 1088, pop(t, tal + .1, .3)): pill(c, 'soğuk', 300, 1088, 40, TEAL, PAPER)
        with xf(c, 780, 1088, pop(t, tal + .2, .3)): pill(c, 'sıcak', 780, 1088, 40, CORAL, PAPER)
    if t > s0 - .1:
        with xf(c, 540, 720, pop(t, s0 - .1, .35), 5 * math.sin(t * 30) * (seg(t, tus, tus + .1) * (1 - seg(t, tus + .5, tus + .7)) + seg(t, tyn, tyn + .1) * (1 - seg(t, tyn + .5, tyn + .7)))):
            brain(c, 540, 720, .4)
        for k in range(3):
            ph = ((t - s0) * .9 + k / 3) % 1
            flake(c, 220 + 70 * k, 740 + 110 * ph, 20, TEAL, 6, alpha=math.sin(math.pi * ph), rot=t + k)
    if t > tso + .2: dashes(c, (330, 856), (440, 780), 5, TEAL, 7, seg(t, tso + .2, tso + .5))
    if t > tus:
        with xf(c, 250, 540, pop(t, tus, .3), -3):
            speech(c, 60, 490, 440, 594, (440, 650))
            txt(c, 'Üşüyoruz!', 250, 562, 56, TEAL)
    if t > h0 - .1:
        for k in range(3):
            with xf(c, 720 + 70 * k, 810, pop(t, h0 - .1 + .08 * k, .25)): flame(c, 720 + 70 * k, 810, .42, t + k)
    if t > thi + .2: dashes(c, (700, 800), (640, 770), 3, CORAL, 7, seg(t, thi + .2, thi + .5))
    if t > tyn:
        with xf(c, 830, 540, pop(t, tyn, .3), 3):
            speech(c, 640, 490, 1020, 594, (640, 650))
            txt(c, 'Yanıyoruz!', 830, 562, 56, CORAL)

def lock_scene(c, t, a0, tkey, top, col, fill, label, prop):
    """sahne 3 ve 4 ortak: ustte bitki, molekul anahtar gibi aliciya oturur"""
    my, rx = 930, 400
    membrane(c, 80, 720, my, seg(t, a0 - .1, a0 + .3))
    with xf(c, 200, 520, pop(t, a0 - .1, .3), 5 * math.sin(t * 2.2)): prop(c, 200, 510, .72)
    with xf(c, 470, 420, pop(t, a0 + .1, .3), 3): pill(c, label, 470, 420, 46, col, PAPER)
    with xf(c, rx, my, pop(t, a0, .3)): receptor(c, rx, my, col, fill, smooth(seg(t, top, top + .3)), 1, t)
    u = smooth(seg(t, a0 + .5, tkey + .25))
    for k, (dx, dy) in enumerate(((0, 0), (-150, -90), (120, -150))):
        kx = lerp(250 + 60 * k, rx + dx * (1 - .0), u); ky = lerp(590 + 30 * k, my - 120 + dy, u)
        if k: ky += 8 * math.sin(t * 4 + k)
        with xf(c, kx, ky, pop(t, a0 + .3 + .12 * k, .25), (0, -24, 20)[k] * u): key(c, kx, ky, .8, col)
    return my, rx

def scene3(c, t):
    a0, a1 = L(6); b0, b1 = L(7); d0, d1 = L(8)
    tkey = cap_start(6, 'anahtar', a1 - 1.3); tac = cap_start(7, 'alıcı', b0 + 1.7); tbr = cap_start(7, 'beynin', b1 - 1.5)
    lock_scene(c, t, a0, tkey, tac, TEAL, WASH_C, 'mentol', leaf)
    if t > b0 - .1:
        with xf(c, 880, 520, pop(t, b0 - .1, .3)): thermo(c, 880, 500, 1.0, .5, CORAL)
        with xf(c, 850, 676, pop(t, b0 + .1, .3)): pill(c, 'sıcaklık aynı', 850, 676, 40, INK)
    if t > tbr - .2:
        with xf(c, 870, 990, pop(t, tbr - .2, .35)): brain(c, 870, 990, .36)
    if t > tbr:
        with xf(c, 860, 820, pop(t, tbr, .3), 3):
            speech(c, 730, 770, 1000, 866, (850, 902))
            txt(c, 'Serin!', 865, 838, 56, TEAL)
    if t > d0 - .1:
        p = pop(t, d0 - .1, .3)
        with xf(c, 250, 1160, p, -4):
            box(c, 110, 1118, 350, 1204, r=14, w=8, fill=PAPER)
            wash(c, 150, 1128, 250, 1194, WASH_C, r=8)
            box(c, 350, 1136, 392, 1186, r=8, w=7, fill=TEAL)
        with xf(c, 690, 1160, pop(t, d0 + .1, .3)): pill(c, 'ferahlık da bu yüzden', 690, 1160, 42, TEAL, PAPER)
        for k, (x, y) in enumerate(((440, 1110), (960, 1100))): flake(c, x, y, 20, TEAL, 6, alpha=seg(t, d0 + .2, d0 + .4), rot=t + k)

def scene4(c, t):
    a0, a1 = L(9); b0, b1 = L(10); d0, d1 = L(11)
    tkey = cap_start(9, 'sıcak', a1 - 1.5); tyl = cap_start(10, 'yanlış', b1 - 1.3); tvu = cap_start(11, 'vücudun', d1 - 1.6)
    lock_scene(c, t, a0, tkey, tkey + .3, CORAL, WASH_H, 'kapsaisin', pepper)
    if t > b0 - .1:
        sh = 6 * math.sin(t * 30) * seg(t, tyl, tyl + .1) * (1 - seg(t, tyl + .6, tyl + .8))
        with xf(c, 850, 560, pop(t, b0 - .1, .35), sh): brain(c, 850, 560, .4)
        with xf(c, 850, 400, pop(t, b0, .3)): pill(c, 'dilin yanmıyor', 850, 400, 40, INK)
    if t > tyl:
        with xf(c, 850, 740, pop(t, tyl, .35), -2):
            box(c, 690, 690, 1010, 790, r=26, w=8, fill=YEL)
            txt(c, 'yanlış alarm', 850, 757, 48, INK)
        for sd in (-1, 1):
            for an in (-22, 0, 22):
                r_ = math.radians(an); r1 = 196 + 8 * math.sin(t * 12 + an)
                line(c, [(850 + sd * 160 * math.cos(r_), 560 + 160 * math.sin(r_) * .6), (850 + sd * r1 * math.cos(r_), 560 + r1 * math.sin(r_) * .6)], CORAL, 7, amp=.6)
    if t > d0 - .1:
        with xf(c, 870, 1256, pop(t, d0 - .1, .3)):
            me = fig(c, 870, 1256, .56, 0, dict(FRONT, aR=30, eR=165, aL=10, eL=6), 'oh')
        hx, hy = me['head']
        for k, (dx, ph0) in enumerate(((-52, 0), (52, .5), (-66, .25))):
            ph = (t * 1.3 + ph0) % 1
            c.drawCircle(hx + dx, hy - 10 + 70 * ph, 8, paint(TEAL, fill=True, alpha=1 - ph))
    if t > tvu:
        with xf(c, 400, 1170, pop(t, tvu, .3), -2): pill(c, 'ter = serinleme çabası', 400, 1170, 42, TEAL, PAPER)

def scene5(c, t):
    a0, a1 = L(12); n0, n1 = L(13)
    tfa = cap_start(12, 'fareler', a0 + 2.2); tay = cap_start(12, 'ayırt', a1 - 1.6)
    with xf(c, 540, 420, pop(t, a0 - .1, .3)): pill(c, 'soğuk alıcısı olmayan fare', 540, 420, 44, INK)
    py = 860
    with xf(c, 540, py, pop(t, a0, .3)):
        box(c, 110, py, 530, py + 56, r=14, w=8, fill=WASH_C)
        box(c, 550, py, 970, py + 56, r=14, w=8, fill=WASH_Y)
    if t > a0 + .2:
        with xf(c, 320, py + 116, pop(t, a0 + .2, .3)): pill(c, 'serin', 320, py + 116, 40, TEAL, PAPER)
        with xf(c, 760, py + 116, pop(t, a0 + .3, .3)): pill(c, 'ılık', 760, py + 116, 40, CORAL, PAPER)
        flake(c, 180, py + 116, 20, TEAL, 6, rot=t)
    if t > tfa - .3:
        w_ = (t - tfa) * 1.5
        mx = 540 + 250 * math.sin(w_); d = 1 if math.cos(w_) >= 0 else -1
        with xf(c, mx, py, pop(t, tfa - .3, .3)): mouse(c, mx, py - 4, 1.0, d, t)
        if t > tay: qmark(c, mx, py - 140, 100, t, CORAL, 1.0, pop(t, tay, .3))
    if t > tay:
        with xf(c, 540, 545, pop(t, tay, .35), -1.5):
            box(c, 170, 494, 910, 596, r=28, w=8, fill=YEL)
            txt(c, 'ayırt etmekte zorlandı', 540, 563, 54, INK)
    if t > n0 - .1:
        p = pop(t, n0 - .1, .35)
        with xf(c, 250, 1160, p, 6 * math.sin(t * 3)):
            for sd in (-1, 1): line(c, [(250 + sd * 22, 1110), (250 + sd * 46, 1050)], TEAL, 22, amp=.5)
            circ(c, 250, 1176, 66, color=INK, w=9, fill=YEL, amp=1, n=14)
            burst(c, 250, 1176, 20, 38, 8, INK, 5)
        with xf(c, 660, 1140, pop(t, n0 + .1, .3)):
            txt(c, 'Nobel Ödülü', 660, 1160, 72, INK)
            txt(c, '2021', 660, 1236, 60, CORAL)

def scene6(c, t):
    a0, a1 = L(14); d0, d1 = L(15); e0, e1 = L(16)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_T)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    aha = t > d0 - .1
    tac = cap_start(14, 'acı', a0 + 1.6)
    pose = dict(FRONT, aR=20, eR=150, aL=10, eL=6, tilt=-6 if not aha else 0)
    pose = mix(pose, dict(FRONT, aR=10, eR=6, aL=148, eL=160 + 26 * math.sin(t * 9)), wv)
    me = fig(c, 540, gy, .95, 0, pose, 'confused' if not aha else 'happy')
    hx, hy = me['top']
    if not aha:
        with xf(c, 225, 800, pop(t, a0, .3), 6 * math.sin(t * 2.4)): leaf(c, 225, 800, .62)
        for k, (x, y) in enumerate(((120, 690), (330, 700))): flake(c, x, y, 22, TEAL, 6, alpha=seg(t, a0 + .1, a0 + .3), rot=t + k)
        if t > tac:
            with xf(c, 850, 790, pop(t, tac, .3), -6 * math.sin(t * 2.4)): pepper(c, 850, 790, .6)
            for k, (x, y) in enumerate(((760, 690), (950, 700))):
                with xf(c, x, y, pop(t, tac + .1, .25)): flame(c, x, y, .4, t + k)
        if t > a0 + .5: qmark(c, hx - 20, hy - 30, 150, t, CORAL, 1.0, pop(t, a0 + .5, .3))
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
