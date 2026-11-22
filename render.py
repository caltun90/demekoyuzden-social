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

TITLE = 'Fiyatlar neden 9,99?'   # yatay formatta etiketin altinda gorunur
HOOK = 'Fiyatlar neden 9,99?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['FİYATLAR', 'NEDEN 9,99?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 10.3                          # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['kuruş'], 1: ['9,99'], 2: ['dokuz', 'lira'], 3: ['bir', 'kuruş'], 4: ['değilsin.'], 5: ['sol', 'basamak', 'etkisi.'], 6: ['soldan', 'sağa'], 7: ['ilk', 'rakamda'], 8: ['karar'], 9: ['deneylerle'], 10: ['2,99', '3,00.'], 11: ['büyük'], 12: ['3,59', '3,60?'], 13: ['çıkmadı.'], 14: ['soldaki', 'rakam'], 15: ['doksan', 'dokuzla'], 16: ['yukarı', 'yuvarla.'], 17: ['ucuz'], 18: ['demek', 'o', 'yüzden!']}


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
    s = '1 DAKİKADA PSİKOLOJİ'
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
def ybox(c, s, cx, cy, size=50, maxw=800, fill=YEL, fg=INK):
    """yaziya gore boyutlanan vurgu kutusu"""
    while tw(s, size) > maxw: size -= 2
    w = tw(s, size); h = size * 1.9
    box(c, cx - w / 2 - 34, cy - h / 2, cx + w / 2 + 34, cy + h / 2, r=28, w=8, fill=fill)
    txt(c, s, cx, cy + size * .36, size, fg)

def price(c, s, x, y, size, lead=1, ca=CORAL, cb=INK, hl=False, alpha=1.0):
    """fiyat yazisi, (x, y) ortasi; ilk `lead` karakter ca, gerisi cb renginde; hl: ilk kisma sari kutu. Ilk kismin orta x'ini dondurur"""
    a, b = s[:lead], s[lead:]
    wa, wb = tw(a, size), tw(b, size); x0 = x - (wa + wb) / 2; by = y + size * .36
    if hl: c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0 - 12, by - size * .84, x0 + wa + 10, by + size * .14), 16, 16), paint(YEL, fill=True, alpha=alpha))
    txt(c, a, x0, by, size, ca, align='l', alpha=alpha); txt(c, b, x0 + wa, by, size, cb, align='l', alpha=alpha)
    return x0 + wa / 2

def ptag(c, s, x, y, w, h, size, lead=1, ca=CORAL, cb=INK, hl=False, fill=PAPER):
    """fiyat etiketi: delikli kart + fiyat"""
    box(c, x - w / 2, y - h / 2, x + w / 2, y + h / 2, r=22, w=8, fill=fill)
    circ(c, x - w / 2 + 30, y - h / 2 + 30, 9, color=INK, w=5, fill=BG, amp=.4, n=8)
    return price(c, s, x + 8, y + 4, size, lead, ca, cb, hl)

def coin(c, x, y, r, lab='1 kr'):
    circ(c, x, y, r, color=INK, w=max(5, r * .1), fill=YEL, amp=.8, n=14)
    c.drawCircle(x, y, r * .78, paint(INK, max(3, r * .05), alpha=.35))
    txt(c, lab, x, y + r * .2, r * .58, INK)

def scene1(c, t):
    h0, h1 = L(0); e0, e1 = L(1); d0, d1 = L(2); o0, o1 = L(3)
    tdo = cap_start(2, 'dokuz', d0 + .5); tku = cap_start(3, 'sadece', o0 + 1.3)
    gy = 1130
    wash(c, 60, 340, 1020, gy, WASH_Y)
    ground(c, 60, 1020, gy)
    intro = t < e0 - .1
    fx = 240
    if intro:
        me = fig(c, fx, gy, .95, 0, dict(FRONT, aR=12, eR=120, aL=10, eL=6), 'confused')
        qmark(c, me['top'][0] + 10, me['top'][1] - 26, 150, t, CORAL, 1.0, pop(t, h0 + .1, .3))
        u = max(0, t - .45)
        cy = 880 - 470 * abs(math.cos(u * 4.2)) * math.exp(-1.5 * u)
        with xf(c, 700, cy, 1, 10 * math.sin(t * 6)): coin(c, 700, cy, 105, '1 kr')
        burst(c, 700, 880, 150, 185 + 10 * math.sin(t * 12), n=10, color=CORAL, w=7, alpha=seg(t, .75, .9))
        with xf(c, 700, 1065, pop(t, h0 + .35, .3), -2): pill(c, 'bir kuruş', 700, 1065, 46, CORAL, PAPER)
        return
    think = t > tdo
    late = t > tku
    me = fig(c, fx, gy, .95, 0, dict(FRONT, aR=12, eR=120, aL=10, eL=6) if late else FRONT, 'oh' if late else ('happy' if think else 'smile'))
    tx, ty = 730, 600
    line(c, [(tx, 345), (tx - 4, 420), (tx, 476)], INK, 6, seg(t, e0 - .1, e0 + .1), amp=1)
    with xf(c, tx, 380, pop(t, e0 - .1, .35), 2.5 * math.sin(t * 2.4)):
        ptag(c, '9,99', tx, ty, 450, 250, 160, 1, CORAL, INK, hl=think and not late)
    if think:
        with xf(c, 250, 520, pop(t, tdo, .3)):
            cloud(c, 250, 510, 150, 82, tail=(fx + 4, me['top'][1] - 14))
            if late and t > tku + .35: txt(c, '10 lira?!', 250, 532, 60, CORAL)
            else: txt(c, '9 lira', 250, 534, 68, TEAL)
    if t > o0 - .05:
        y = 885
        with xf(c, 540, y, pop(t, o0 - .05, .3)): txt(c, '9,99', 540, y + 22, 62, INK)
        if late:
            with xf(c, 646, y, pop(t, tku, .25)): txt(c, '+', 646, y + 21, 60, INK)
            with xf(c, 722, y, pop(t, tku + .08, .3), 8 * math.sin(t * 6)): coin(c, 722, y, 46, '1 kr')
            with xf(c, 800, y, pop(t, tku + .2, .25)): txt(c, '=', 800, y + 21, 60, INK)
            with xf(c, 915, y, pop(t, tku + .3, .3) * (1 + .05 * math.sin(t * 9))): txt(c, '10,00', 915, y + 22, 62, CORAL)
            with xf(c, 735, 1030, pop(t, tku + .45, .3), -2): pill(c, 'sadece 1 kuruş eksik', 735, 1030, 40, INK)

def scene2(c, t):
    a0, a1 = L(4); n0, n1 = L(5)
    the = cap_start(4, 'hesap', a0 + .9); tso = cap_start(5, 'sol', n0 + 1.2)
    gy = 1010
    wash(c, 60, 340, 1020, gy, WASH_T)
    ground(c, 60, 1020, gy)
    named = t > tso
    with xf(c, 250, gy, pop(t, a0 - .15, .3)):
        fig(c, 250, gy, .85, 0, dict(FRONT, aR=104, eR=112) if named else FRONT, 'happy' if named else 'smile')
    with xf(c, 700, 560, pop(t, a0 - .05, .3)):
        x9 = price(c, '9,99', 700, 560, 200, 1, CORAL, MUTE if named else INK, hl=named)
    if t > the:
        with xf(c, 250, 480, pop(t, the, .3), -2): pill(c, 'sorun sende değil', 250, 480, 36, TEAL, PAPER)
    if named:
        arrow(c, (x9, 790), (x9, 690), INK, 8, seg(t, tso, tso + .25))
        with xf(c, x9 + 40, 835, pop(t, tso + .1, .3), -2): pill(c, 'soldaki rakam', x9 + 40, 835, 40, CORAL, PAPER)
    if t > n0 - .05:
        with xf(c, 540, 1105, pop(t, n0 - .05, .3)): pill(c, 'bunun bir adı var', 540, 1105, 40, INK)
    if named:
        with xf(c, 540, 1200, pop(t, tso, .35), -1.5): ybox(c, 'sol basamak etkisi', 540, 1200, 54, 760)

def scene3(c, t):
    r0, r1 = L(6); b0, b1 = L(7); k0, k1 = L(8)
    tso = cap_start(6, 'soldan', r0 + .6); til = cap_start(7, 'ilk', b0 + .9); tfi = cap_start(7, 'fiyatın', b0 + 1.8)
    tka = cap_start(8, 'karar', k0 + 1.3)
    wash(c, 60, 340, 1020, 1100, WASH_P)
    first = t > til; done = t > tka
    with xf(c, 540, 510, pop(t, r0 - .15, .3)):
        price(c, '9,99', 540, 510, 210, 1, CORAL, MUTE if done else INK, hl=first, alpha=1.0)
    pr = smooth(seg(t, tso, r1 - .1))
    if t > tso:
        arrow(c, (300, 660), (lerp(300, 790, pr), 660), TEAL, 10, 1.0)
        with xf(c, 540, 725, pop(t, tso + .1, .3)): pill(c, 'soldan sağa', 540, 725, 40, TEAL, PAPER)
    if t > b0 - .1:
        bx, by = 250, 930
        with xf(c, bx, by, pop(t, b0 - .1, .3) * (1 + (.04 * math.sin(t * 9) if first else 0))):
            cloud(c, bx, by, 125, 100, fill=YEL if t > tfi else PAPER, w=9)
            line(c, [(bx + 5, by - 84), (bx - 15, by - 30), (bx + 12, by + 15), (bx - 5, by + 82)], INK, 6, curve=True, amp=1)
            for sd in (-1, 1):
                line(c, [(bx + sd * 94, by - 18), (bx + sd * 57, by - 38), (bx + sd * 42, by + 2)], MUTE, 6, curve=True, amp=.8)
                line(c, [(bx + sd * 88, by + 36), (bx + sd * 57, by + 50), (bx + sd * 37, by + 40)], MUTE, 6, curve=True, amp=.8)
    if t > tfi:
        with xf(c, 690, 930, pop(t, tfi, .3)):
            speech(c, 450, 850, 950, 1000, (402, 935))
            txt(c, '"9 lira gibi"', 700, 945, 58, CORAL)
    if done:
        with xf(c, 500, 1190, pop(t, tka, .35), -1.5): ybox(c, 'karar çoktan verildi', 500, 1190, 50, 640)
        check(c, 900, 1190, 1.5, seg(t, tka + .15, tka + .45))

def scene4(c, t):
    a0, a1 = L(9); p0, p1 = L(10); f0, f1 = L(11); q0, q1 = L(12); n0, n1 = L(13)
    tbu = cap_start(11, 'büyük', f0 + 1.4); tet = cap_start(13, 'etki', n0 + .8)
    wash(c, 60, 340, 1020, 1150, WASH_T)
    with xf(c, 540, 405, pop(t, a0 - .15, .3), -1.5): ybox(c, 'deney', 540, 405, 46, 300)
    ya, yb = 610, 950
    for k, (x, s, tk) in enumerate(((255, '2,99', p0 - .05), (825, '3,00', p0 + (p1 - p0) * .55))):
        if t > tk:
            with xf(c, x, ya, pop(t, tk, .3), (-2, 2)[k]): ptag(c, s, x, ya, 310, 180, 112, 1, CORAL, INK, hl=t > tbu)
    if t > f0 - .05:
        with xf(c, 540, 520, pop(t, f0 - .05, .3)): pill(c, '1 kuruş', 540, 520, 34, INK)
    if t > tbu:
        pr = seg(t, tbu, tbu + .3)
        arrow(c, (540, ya + 6), (lerp(540, 648, pr), ya + 6), CORAL, 13, 1.0); arrow(c, (540, ya + 6), (lerp(540, 432, pr), ya + 6), CORAL, 13, 1.0)
        with xf(c, 540, 760, pop(t, tbu + .1, .3), -2): pill(c, 'fark kocaman gibi!', 540, 760, 42, CORAL, PAPER)
    for k, (x, s, tk) in enumerate(((255, '3,59', q0 + .3), (825, '3,60', q0 + .3 + (q1 - q0) * .5))):
        if t > tk:
            with xf(c, x, yb, pop(t, tk, .3), (2, -2)[k]): ptag(c, s, x, yb, 310, 180, 112, 1, TEAL, INK, hl=False)
    if t > q1 - .3:
        with xf(c, 540, 860, pop(t, q1 - .3, .3)): pill(c, '1 kuruş', 540, 860, 34, INK)
    if t > tet:
        with xf(c, 540, yb, pop(t, tet, .3)): txt(c, '=', 540, yb + 38, 110, MUTE)
        with xf(c, 540, 1095, pop(t, tet + .1, .3), 2): pill(c, 'fark yok gibi', 540, 1095, 42, TEAL, PAPER)

def scene5(c, t):
    a0, a1 = L(14); e0, e1 = L(15); i0, i1 = L(16)
    tso = cap_start(14, 'soldaki', a0 + 1.2); tde = cap_start(14, 'değişince', a1 - 1.3)
    tdo = cap_start(15, 'doksan', e0 + 1.1); tyu = cap_start(16, 'yukarı', i1 - 1.1)
    wash(c, 60, 340, 1020, 1090, WASH_Y)
    with xf(c, 270, 500, pop(t, a0 - .15, .3)): price(c, '3,00', 270, 500, 130, 1, CORAL, INK, hl=t > tso)
    arrow(c, (440, 500), (640, 500), INK, 9, seg(t, a0 + .15, a0 + .5))
    with xf(c, 810, 500, pop(t, a0 + .3, .3)): price(c, '2,99', 810, 500, 130, 1, CORAL, INK, hl=t > tso)
    if t > tde:
        with xf(c, 540, 650, pop(t, tde, .3), -2): pill(c, 'soldaki rakam değişti', 540, 650, 42, CORAL, PAPER)
    for k, (x, s, r) in enumerate(((225, '4,99', '5'), (540, '19,99', '20'), (855, '99,99', '100'))):
        tk = e0 - .05 + .18 * k
        if t <= tk: continue
        with xf(c, x, 900, pop(t, tk, .3), (-3, 1, 3)[k]):
            ptag(c, s, x, 900, 270, 150, 74, len(s) - 2, INK, CORAL, hl=False)
        if t > tyu + .1 * k:
            with xf(c, x, 775, pop(t, tyu + .1 * k, .3)): pill(c, r + ' lira', x, 775, 38, TEAL, PAPER)
    if t > tdo:
        with xf(c, 540, 1035, pop(t, tdo, .3), 1.5): pill(c, 'hep 99 ile bitiyor', 540, 1035, 38, INK)
    if t > i0 + .1:
        with xf(c, 540, 1190, pop(t, i0 + .1, .35), -1.5): ybox(c, 'ipucu: yukarı yuvarla', 540, 1190, 50, 760)

def scene6(c, t):
    a0, a1 = L(17); d0, d1 = L(18); e0, e1 = L(19)
    tuc = cap_start(17, 'ucuz', a0 + 1.0)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_T)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    aha = t > d0 - .1
    line(c, [(215, 565), (212, 640), (215, 690)], INK, 6, amp=1)
    with xf(c, 215, 600, 1, 2.5 * math.sin(t * 2.4)): ptag(c, '9,99', 215, 770, 280, 160, 92, 1, CORAL, INK, hl=aha)
    if not aha:
        me = fig(c, 580, gy, .95, 0, dict(FRONT, aR=12, eR=120, aL=10, eL=6), 'happy' if t > tuc else 'confused')
    else:
        pose = mix(dict(FRONT, aR=20, eR=150, aL=10, eL=6), dict(FRONT, aR=10, eR=6, aL=148, eL=160 + 26 * math.sin(t * 9)), wv)
        me = fig(c, 580, gy, .95, 0, pose, 'happy')
    hx, hy = me['top']
    if not aha:
        qmark(c, hx + 10, hy - 30, 150, t, CORAL, 1.0, pop(t, a0 + .3, .3))
        if t > tuc:
            with xf(c, 850, 900, pop(t, tuc, .3), 4): pill(c, 'ucuz!', 850, 900, 50, CORAL, PAPER)
    else:
        with xf(c, 215, 920, pop(t, d0, .3), -2): pill(c, 'aslında 10 lira', 215, 920, 36, TEAL, PAPER)
    if d0 - .05 < t < e0 - .05:
        p = pop(t, d0 - .05, .35)
        with xf(c, 540, 430, lerp(.7, 1, p), 0, seg(t, d0 - .05, d0 + .1) * (1 - seg(t, e0 - .3, e0 - .08))):
            txt(c, 'Demek o yüzden!', 540, 452, 88, CORAL)
    if t > d0 - .05:
        with xf(c, hx + 170, hy - 30, pop(t, d0 - .05, .3)): bulb(c, hx + 170, hy - 30, .9, t=t)
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
