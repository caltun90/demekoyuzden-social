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

TITLE = 'Sahne Işığı Etkisi'   # yatay formatta etiketin altinda gorunur
HOOK = 'Herkes sana mı bakıyor?'        # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['HERKES SANA', 'MI BAKIYOR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 3.9                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['herkes', 'sana', 'bakıyor.'], 1: ['lekede'], 3: ['tek', 'sen', 'değilsin.'], 4: ['sahne', 'ışığı', 'etkisi.'],
      7: ['utandırıcı', 'bir', 'tişörtle'], 10: ['yaklaşık', 'yarısı'], 11: ['dörtte', 'bir'],
      12: ['sahnenin', 'ortasındayız.'], 14: ['sanıyoruz.'], 15: ['kendi', 'derdiyle'], 16: ['şunu', 'sor.'],
      17: ['hatırlıyor', 'musun?'], 18: ['hayır.'], 19: ['hatırlamıyor.'], 22: ['bunu', 'hatırla.'], 23: ['çok', 'daha', 'az']}

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
GY = 1090
COFFEE = 0xFF9A6A48
SHIRT_ARMS = dict(aL=55, eL=10, aR=55, eR=10)

def shirt(c, nx, ny, s=1.0, fill=PAPER, alpha=1.0, color=INK):
    """tisort; (nx, ny) yaka ortasi, govde ny+150*s'e kadar iner"""
    pts = [(-18, 0), (0, 14), (18, 0), (44, 6), (78, 50), (58, 68), (42, 48), (42, 150), (-42, 150), (-42, 48), (-58, 68), (-78, 50), (-44, 6)]
    line(c, [(nx + x * s, ny + y * s) for x, y in pts], color, max(4.5, 8 * s), alpha=alpha, amp=1.0 * s + .3, closed=True, fill=fill)

def stain(c, x, y, s=1.0, alpha=1.0):
    circ(c, x, y, 20 * s, 15 * s, color=COFFEE, w=0, fill=COFFEE, alpha=alpha, amp=2.2 * s, n=9)
    c.drawCircle(x + 23 * s, y + 15 * s, 5 * s, paint(COFFEE, fill=True, alpha=alpha))
    c.drawCircle(x - 15 * s, y + 23 * s, 4 * s, paint(COFFEE, fill=True, alpha=alpha))

def eye(c, x, y, s=1.0, tx=None, ty=None, op=1.0, alpha=1.0, color=INK):
    if alpha <= 0.01: return
    if op < .3:
        line(c, [(x - 30 * s, y), (x, y + 9 * s), (x + 30 * s, y)], color, 6 * s, alpha=alpha, amp=.6, curve=True)
        return
    circ(c, x, y, 34 * s, 21 * s * op, color=color, w=6 * s, fill=PAPER, alpha=alpha, amp=.8, n=12)
    dx = dy = 0
    if tx is not None:
        d = math.hypot(tx - x, ty - y) or 1; dx, dy = (tx - x) / d * 12 * s, (ty - y) / d * 6 * s
    c.drawCircle(x + dx, y + dy, 10 * s * min(1, op), paint(color, fill=True, alpha=alpha))

def spot(c, x0, y0, cx, gy, rx, alpha=1.0, hw=26):
    """sahne isigi konisi: (x0, y0) lambadan yerdeki (cx, gy) elipsine"""
    if alpha <= 0.01: return
    p = skia.Path(); p.moveTo(x0 - hw, y0); p.lineTo(x0 + hw, y0); p.lineTo(cx + rx, gy); p.lineTo(cx - rx, gy); p.close()
    c.drawPath(p, paint(YEL, fill=True, alpha=.36 * alpha))
    c.drawOval(skia.Rect.MakeLTRB(cx - rx, gy - rx * .13, cx + rx, gy + rx * .13), paint(YEL, fill=True, alpha=.8 * alpha))

def lampbox(c, x, y, s=1.0, alpha=1.0):
    box(c, x - 44 * s, y - 38 * s, x + 44 * s, y, r=10 * s, w=max(4, 7 * s), fill=INK, alpha=alpha)

def fig_shirt(c, x, gy, s=1.0, pose=None, expr='smile', fill=PAPER, hold=None, deco=None):
    P = dict(SHIRT_ARMS); P.update(pose or {})
    info = fig(c, x, gy, s, 0, P, expr, hold=hold)
    nx, ny = info['hip'][0], info['hip'][1] - 160 * s
    shirt(c, nx, ny, s, fill)
    if deco: deco(nx, ny + 76 * s)
    info['chest'] = (nx, ny + 76 * s)
    return info

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1)
    ts = cap_start(0, 'döküldü', a0 + 1.0) + .3
    te = cap_start(0, 'herkes', a0 + 2.2)
    wash(c, 60, 330, 1020, 1100, WASH_T)
    so = smooth(seg(t, te - .1, te + .25)) * (1 - .4 * smooth(seg(t, b0, b0 + .4)))
    spot(c, 540, 372, 540, GY, 250, so)
    lampbox(c, 540, 374)
    ground(c, 50, 1030, GY)
    spill = smooth(seg(t, ts - .5, ts - .1))
    sp = pop(t, ts, .3)
    ex = 'smile' if t < ts - .2 else ('oh' if t < te + .3 else 'sad')
    def cup(h):
        hx_, hy_ = h
        with xf(c, hx_, hy_, 1, -62 * spill):
            box(c, hx_ - 27, hy_ - 66, hx_ + 27, hy_ + 2, r=8, w=7, fill=PAPER)
            line(c, [(hx_ + 27, hy_ - 50), (hx_ + 50, hy_ - 44), (hx_ + 50, hy_ - 22), (hx_ + 27, hy_ - 14)], INK, 6, amp=.8, curve=True)
            wash(c, hx_ - 20, hy_ - 59, hx_ + 20, hy_ - 44, COFFEE, r=5)
    def deco(x, y):
        if sp > 0:
            with xf(c, x + 4, y, sp): stain(c, x + 4, y, 1.5)
    info = fig_shirt(c, 540, GY, 1.0, dict(aR=70, eR=120), ex, hold=cup, deco=deco)
    cx_, cy_ = info['chest']; hR = info['handR']
    for i in range(3):
        u = seg(t, ts - .32 + i * .07, ts + i * .07)
        if 0 < u < 1:
            c.drawCircle(lerp(hR[0] - 46, cx_ + 8, u), lerp(hR[1] - 52, cy_, u) - 46 * math.sin(math.pi * u), 8, paint(COFFEE, fill=True))
    hx, hy = info['top']
    ef = 1 - smooth(seg(t, b0 - .1, b0 + .3))
    for i, (ex_, ey_) in enumerate(((150, 640), (265, 860), (140, 1010), (930, 640), (835, 880), (940, 1020))):
        p = pop(t, te + .05 + i * .08, .25)
        if p > 0 and ef > 0.01:
            with xf(c, ex_, ey_, p, 0, ef): eye(c, ex_, ey_, 1.15, 540, 800)
    cl = pop(t, b0 + .1, .35)
    if cl > 0:
        cx, cy = 262, 520
        with xf(c, cx, cy, cl):
            cloud(c, cx, cy, 185, 125, tail=(hx - 40, hy + 4))
            shirt(c, cx, cy - 78, 1.0, PAPER)
            stain(c, cx + 4, cy - 2, 1.45 * (1 + .14 * math.sin(t * 7)))

def scene2(c, t):
    a0, a1 = L(2)[0], L(3)[1]; b0, b1 = L(4)
    gy = 1170; x = 540; s = 1.0
    tt = cap_start(4, 'sahne', b0 + 1.2)
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
                eye(c, tx_ + fc * 16, ty_ - 92, .85, tx_ + fc * 16, ty_ + 40)
    if t > tt:
        p = pop(t, tt, .35)
        with xf(c, 540, 460, lerp(.7, 1, p), 0, seg(t, tt, tt + .15)):
            txt(c, 'SAHNE IŞIĞI', 540, 420, 112, INK)
            txt(c, 'ETKİSİ', 540, 540, 112, CORAL)
        line(c, [(290, 576), (420, 570), (560, 580), (790, 568)], INK, 10, seg(t, tt + .4, tt + .8), curve=True)
        txt(c, 'herkes bana bakıyor sanmak', 540, 634, 38, MUTE, 'med', alpha=seg(t, tt + .7, tt + 1.0))

def scene3(c, t):
    a0, _ = L(5); f0, g0 = L(6)[0], L(8)[0]; b0, b1 = L(9)[0], L(10)[1]; d0, d1 = L(11)
    al = seg(t, a0 - .1, a0 + .3)
    with xf(c, 540, 380, 1, 0, al):
        txt(c, 'Cornell Üniversitesi · 2000', 540, 372, 44, INK, 'bold')
        txt(c, 'Gilovich, Medvec ve Savitsky deneyi', 540, 424, 32, MUTE, 'med')
    gy = 850
    ra = seg(t, f0 - .1, f0 + .3)
    if ra <= 0: return
    wash(c, 60, 480, 1020, gy + 14, WASH_T, ra)
    ground(c, 50, 1030, gy, ra, w=8)
    door(c, 90, gy, w=150, h=318, leaf=False, lw=9, prog=ra)
    tw_ = L(7)[0]
    ty_ = cap_start(10, 'yarısı', b0 + 1.6)
    tq = cap_start(11, 'dörtte', d0 + 1.2)
    # izleyenler (masada)
    OBS = (600, 700, 800, 900)
    for i, ox in enumerate(OBS):
        p = pop(t, f0 + .2 + i * .1, .28)
        if p > 0:
            with xf(c, ox, gy, p): fig(c, ox, gy, .42, 0, None, 'oh' if (i == 1 and t > tq + .2) else 'flat')
    box(c, 535, gy - 86, 965, gy, r=14, w=8, fill=PAPER, alpha=ra)
    # tisortlu ogrenci
    u = smooth(seg(t, g0 + .45, g0 + 1.35))
    if t > tw_ - .05:
        wx = lerp(165, 360, u)
        ex = 'flat' if t < b0 else ('confused' if t < d1 - .5 else 'happy')
        def deco(x, y):
            circ(c, x, y - 4, 15, color=CORAL, w=0, fill=CORAL, n=10, amp=.8)
            burst(c, x, y - 4, 20, 29, 8, CORAL, 4)
        with xf(c, wx, gy, 1, 0, seg(t, tw_ - .05, tw_ + .15)):
            fig_shirt(c, wx, gy + 6 * math.sin(u * math.pi * 4) * (u < 1), .6, None, ex, fill=WASH_Y, deco=deco)
    # goz isaretleri: tahmin (2/4) -> gercek (1/4)
    for i in (1, 3):
        ox = OBS[i]
        p = pop(t, ty_ + (i == 3) * .15, .25)
        fade = 1 - smooth(seg(t, tq, tq + .3)) if i == 3 else 1
        if p > 0 and fade > 0.01:
            col = TEAL if (i == 1 and t > tq + .2) else CORAL
            with xf(c, ox, 616, p, 0, fade): eye(c, ox, 616, .85, 360, 760, color=col)
    # cubuklar
    def bar(y, label, col, frac, tin, tf, note):
        p = pop(t, tin, .3)
        if p <= 0: return
        with xf(c, 540, y, lerp(.85, 1, p), 0, seg(t, tin, tin + .15)):
            txt(c, label, 96, y + 15, 40, INK, align='l')
            box(c, 330, y - 32, 984, y + 32, r=30, w=7, fill=PAPER)
            fu = smooth(seg(t, tf, tf + .6))
            if fu > 0.03: wash(c, 339, y - 23, 339 + 636 * frac * fu, y + 23, col, r=22)
            txt(c, note, 339 + 636 * frac + 22, y + 13, 34, MUTE, 'med', align='l', alpha=seg(t, tf + .5, tf + .8))
    bar(985, 'TAHMİN', CORAL, .5, b0, ty_, 'yaklaşık yarısı')
    bar(1105, 'GERÇEK', TEAL, .25, d0, tq, 'dörtte bir kadarı')
    fn = pop(t, tq + .9, .3)
    if fn > 0:
        with xf(c, 540, 1200, fn, -1.5): txt(c, 'tahminin yarısı kadar!', 540, 1214, 42, CORAL)

def scene4(c, t):
    a0, a1 = L(12); b0, b1 = L(13)[0], L(14)[1]; d0, d1 = L(15)
    gy = 1150
    tm = cap_start(12, 'sahnenin', a0 + 1.8)
    son = smooth(seg(t, a0 + .1, a0 + .45))
    own = smooth(seg(t, d0 + .25, d0 + .75))
    wash(c, 60, 330, 1020, gy + 12, WASH_P)
    spot(c, 540, 372, 540, gy - 40, lerp(185, 125, own), son * (1 - .3 * own))
    lampbox(c, 540, 374)
    SIDE = ((125, 1), (280, 1), (800, -1), (955, -1))
    for i, (sx, fc) in enumerate(SIDE):
        if own > 0.01:
            spot(c, sx, 738, sx, gy, 76, own, hw=16)
            lampbox(c, sx, 740, .5, own)
    ground(c, 50, 1030, gy)
    box(c, 372, gy - 40, 708, gy, r=12, w=9, fill=PAPER)
    ta = smooth(seg(t, tm - .1, tm + .3)) * (1 - smooth(seg(t, b0 - .2, b0 + .2)))
    pose = mix(FRONT, dict(FRONT, aL=112, eL=128, aR=112, eR=128), ta)
    ex = 'happy' if t < b0 else ('confused' if t < d0 + .75 else 'happy')
    info = fig(c, 540, gy - 40, .82, 0, pose, ex)
    hcx, hcy = info['head']
    ga = seg(t, b0 + .35, b0 + .65) * (1 - own)
    for i, (sx, fc) in enumerate(SIDE):
        p = pop(t, b0 + i * .1, .28)
        if p <= 0: continue
        away = own >= .5
        with xf(c, sx, gy, p * (1 - .25 * math.sin(math.pi * own))):
            fi = fig(c, sx, gy, .46, -fc if away else fc, dict(STAND), 'flat', color=INK if away else MUTE)
        fx, fy = fi['head']
        if ga > 0.01:
            for k in range(5):
                v = ((k + (t * 1.6) % 1) / 5)
                px, py = lerp(fx + fc * 34, hcx - fc * 52, v), lerp(fy, hcy, v)
                c.drawCircle(px, py, 6, paint(CORAL, fill=True, alpha=ga * (1 - .5 * v)))
        cp = pop(t, d0 + .75 + i * .08, .28)
        if cp > 0:
            tx_, ty_ = fi['top']
            ccx, ccy = sx, ty_ - 74
            with xf(c, ccx, ccy, cp):
                cloud(c, ccx, ccy, 62, 42, tail=(tx_ - fc * 4, ty_ - 4), w=6)
                if i == 0: stain(c, ccx, ccy - 4, .9)
                else: txt(c, ('?', '...', '!')[i - 1], ccx, ccy + (8 if i == 2 else 20), 56, CORAL)

def scene5(c, t):
    a0, a1 = L(16); b0, b1 = L(17); d0, d1 = L(18)
    wash(c, 60, 400, 1020, GY, WASH_Y)
    ground(c, 50, 1030, GY)
    to = L(19)[0]
    no_t = cap_start(18, 'hayır', d0 + .6)
    think = smooth(seg(t, b0, b0 + .4)) * (1 - smooth(seg(t, to - .3, to)))
    pose = mix(STAND, dict(STAND, aR=40, eR=150, tilt=-4), think)
    ex = 'smile' if t < b0 else ('confused' if t < no_t + .3 else ('flat' if t < to + .5 else 'happy'))
    info = fig(c, 225, GY, .9, 1, pose, ex)
    hx, hy = info['top']
    bl = pop(t, a0 + .35, .3) * (1 - seg(t, b0 - .25, b0 - .05))
    if bl > 0:
        with xf(c, hx + 10, hy - 110, bl): bulb(c, hx + 10, hy - 110, 1.15, t=t)
    c1 = pop(t, b0 + .1, .35) * (1 - smooth(seg(t, to - .3, to - .05)))
    if c1 > .01:
        cx, cy = 690, 660
        with xf(c, cx, cy, c1):
            cloud(c, cx, cy, 280, 195, tail=(hx + 44, hy - 6))
            txt(c, 'DÜN', cx, cy - 104, 46, MUTE)
            shirt(c, cx, cy - 70, 1.25, WASH_T)
            qmark(c, cx, cy + 82, 110, t, CORAL)
            ck = seg(t, no_t, no_t + .35)
            if ck > 0: cross(c, cx + 178, cy + 30, 1.25, ck)
    f2 = pop(t, to - .05, .3)
    if f2 > 0:
        with xf(c, 850, GY, f2):
            fi = fig(c, 850, GY, .8, -1, dict(STAND), 'confused')
        tx_, ty_ = fi['top']
        c2 = pop(t, to + .2, .3)
        if c2 > 0:
            cx, cy = 720, 560
            with xf(c, cx, cy, c2):
                cloud(c, cx, cy, 215, 135, tail=(tx_ - 30, ty_ - 6))
                shirt(c, cx - 70, cy - 78, .95, WASH_P)
                qmark(c, cx - 70, cy + 38, 84, t, CORAL)
                cross(c, cx + 96, cy, 1.1, seg(t, to + .7, to + 1.0))
    rl = seg(t, to + .9, to + 1.2)
    if rl > 0:
        for i, (dx, dy) in enumerate(((-120, 0), (120, -30), (-70, -100), (60, -120))):
            r = (14 + 5 * math.sin(t * 6 + i)) * rl
            line(c, [(hx + dx - r, hy + dy), (hx + dx + r, hy + dy)], TEAL if i % 2 else CORAL, 7, amp=.6)
            line(c, [(hx + dx, hy + dy - r), (hx + dx, hy + dy + r)], TEAL if i % 2 else CORAL, 7, amp=.6)

def scene6(c, t):
    a0, a1 = L(20)[0], L(22)[1]; b0, b1 = L(23); d0, d1 = L(24)
    wash(c, 60, 540, 1020, GY, WASH_T)
    te = L(21)[0]
    so = smooth(seg(t, te - .1, te + .25)) * (1 - smooth(seg(t, b0 + .3, b0 + 1.6)))
    spot(c, 540, 596, 540, GY, 235, so)
    lampbox(c, 540, 598, 1.0, so)
    ground(c, 50, 1030, GY)
    shr = smooth(seg(t, te, te + .4)) * (1 - smooth(seg(t, a1 - .3, a1 + .1)))
    wv = smooth(seg(t, d0 - .1, d0 + .3))
    pose = mix(FRONT, dict(FRONT, aL=38, eL=118, aR=38, eR=118, tilt=6), shr)
    pose = mix(pose, dict(FRONT, aR=148, eR=160 + 26 * math.sin(t * 9), aL=12, eL=8), wv)
    ex = 'smile' if t < te else ('confused' if t < b0 + .8 else 'happy')
    info = fig(c, 540, GY, .92, 0, pose, ex)
    gone = 1 - smooth(seg(t, d0 - .3, d0))
    EY = ((150, 680), (285, 860), (160, 1010), (930, 680), (800, 860), (925, 1010))
    for i, (ex_, ey_) in enumerate(EY):
        p = pop(t, te + i * .08, .25)
        if p <= 0 or gone <= 0.01: continue
        order = (0, 3, 1, 2, 4, 5).index(i)                       # kapanma sirasi; 5 numara acik kalir
        cl = seg(t, b0 + .15 + order * .28, b0 + .35 + order * .28) if i != 5 else 0
        with xf(c, ex_, ey_, p, 0, gone * (1 - .6 * cl)):
            eye(c, ex_, ey_, 1.15, 540, 820, op=1 - cl, color=MUTE if cl >= 1 else INK)
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
