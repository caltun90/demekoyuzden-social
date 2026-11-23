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

TITLE = 'Karnın neden guruldar?'   # yatay formatta etiketin altinda gorunur
HOOK = 'Karnın neden guruldar?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['KARNIN NEDEN', 'GURULDAR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 9.0                          # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['susmuyor.'], 1: ['sessiz,'], 2: ['gurulduyor.'], 3: ['bakıyor.'], 4: ['açlık', 'değil.'], 5: ['adı'], 7: ['kaslardan', 'boru.'], 8: ['kasılıp', 'itiyor.'], 9: ['gaz', 'sıvı'], 10: ['ince', 'bağırsaktan'], 11: ['hep', 'var.'], 12: ['bastırıyor.'], 13: ['çınlıyor.'], 14: ['kasılma', 'dalgası'], 15: ['süpürmek.'], 16: ['tekrarlıyor.'], 17: ['guruldar'], 18: ['demek', 'o', 'yüzden!'], 6: ['borborigmi.']}


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
MUS = 0xFFF3B9A6
GREY = 0xFFEDE6D8
BROWN = 0xFFC99A6B

def ybox(c, s, cx, cy, size=50, maxw=800, fill=YEL, fg=INK):
    """yaziya gore boyutlanan vurgu kutusu"""
    while tw(s, size) > maxw: size -= 2
    w = tw(s, size); h = size * 1.9
    box(c, cx - w / 2 - 34, cy - h / 2, cx + w / 2 + 34, cy + h / 2, r=28, w=8, fill=fill)
    txt(c, s, cx, cy + size * .36, size, fg)

def smoothpts(pts, n=10):
    """Catmull-Rom: az noktadan yumusak egri noktalar"""
    P = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            u = j / n; u2, u3 = u * u, u * u * u
            out.append(tuple(.5 * (2 * p1[k] + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3) for k in (0, 1)))
    out.append(pts[-1])
    return out

def along(pts, u):
    d = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    v = clamp(u) * sum(d)
    for i, di in enumerate(d):
        if v <= di: return (lerp(pts[i][0], pts[i + 1][0], v / di), lerp(pts[i][1], pts[i + 1][1], v / di))
        v -= di
    return pts[-1]

def dot(c, q, r=12, fill=YEL):
    c.drawCircle(q[0], q[1], r, paint(fill, fill=True)); c.drawCircle(q[0], q[1], r, paint(INK, 4))

def seg_line(c, p0, p1, color, w, alpha=1.0):
    c.drawLine(p0[0], p0[1], p1[0], p1[1], paint(color, w, alpha=alpha))

def arcs(c, x, y, r0, n=3, t=0, col=CORAL, w=7, side=(1, -1), gap=26):
    """ses dalgasi: iki yana yay cizgileri"""
    for sd in side:
        for k in range(n):
            r = r0 + gap * k + 5 * math.sin(t * 14 + k)
            line(c, [(x + sd * r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in (-38, -19, 0, 19, 38)], col, w, amp=.8, curve=True)

def gurr(c, s, x, y, size, t, col=CORAL, sc=1.0):
    with xf(c, x, y - size * .35, sc * (1 + .05 * math.sin(t * 13)), 5 * math.sin(t * 9)): txt(c, s, x, y, size, col)

def tube(c, P, w=64, fill=MUS):
    p = skia.Path(); p.moveTo(*P[0])
    for q in P[1:]: p.lineTo(*q)
    c.drawPath(p, paint(INK, w + 16)); c.drawPath(p, paint(fill, w))

GUT = smoothpts([(470, 640), (640, 602), (800, 640), (862, 722), (790, 800), (540, 800), (290, 800), (216, 875), (290, 950), (540, 950), (790, 950), (862, 1025), (790, 1100), (600, 1100), (440, 1100)], 10)

def gut(c, prog=1.0):
    """yemek borusu + mide + kivrimli bagirsak"""
    seg_line(c, (330, 372), (330, 470), INK, 60)
    n = max(2, int(len(GUT) * clamp(prog)))
    tube(c, GUT[:n])
    circ(c, 340, 560, 152, 116, color=INK, w=9, fill=MUS, amp=1.5)
    seg_line(c, (330, 380), (330, 470), MUS, 44)
    if n > 8: seg_line(c, (455, 632), (500, 632), MUS, 62)

def flow(c, t, t0, n=7, sp=.085):
    """boruda ilerleyen gaz kabarciklari (beyaz) ve sivi damlalari (turkuaz)"""
    for k in range(n):
        q = along(GUT, ((t - t0) * sp + k / n) % 1)
        if k % 2: dot(c, q, 11, TEAL)
        else: dot(c, q, 14, PAPER)

def stomach(c, cx, cy, s=1.0):
    seg_line(c, (cx - 95 * s, cy - 250 * s), (cx - 95 * s, cy - 100 * s), INK, 58 * s)
    seg_line(c, (cx + 120 * s, cy + 70 * s), (cx + 215 * s, cy + 130 * s), INK, 58 * s)
    circ(c, cx, cy, 175 * s, 140 * s, color=INK, w=9, fill=MUS, amp=1.5)
    seg_line(c, (cx - 95 * s, cy - 244 * s), (cx - 95 * s, cy - 100 * s), MUS, 42 * s)
    seg_line(c, (cx + 120 * s, cy + 70 * s), (cx + 209 * s, cy + 126 * s), MUS, 42 * s)

def scene1(c, t):
    h0, h1 = L(0); o0, o1 = L(1); g0, g1 = L(2); b0, b1 = L(3)
    tgu = cap_start(2, 'gurulduyor', g1 - 1.0); the = cap_start(1, 'herkes', o0 + 1.2)
    gy = 1130
    wash(c, 60, 340, 1020, gy, WASH_Y)
    ground(c, 60, 1020, gy)
    intro = t < o0 - .1
    loud = intro or t > tgu
    stare = t > b0 - .1
    if not intro:
        for k, (x, f) in enumerate(((180, 1), (900, -1))):
            a = seg(t, the + .15 * k, the + .3 + .15 * k)
            if a > 0: fig(c, x, gy, .78, f, None, 'oh' if t > tgu + .2 else 'smile', alpha=a)
    shake = loud and (intro or t < tgu + .9)
    P = dict(FRONT, lean=2.5 * math.sin(t * 26)) if shake else FRONT
    expr = 'oh' if intro else ('sad' if stare else ('oh' if t > tgu else 'smile'))
    me = fig(c, 540, gy, 1.0, 0, P, expr)
    bx, by = me['hip'][0], me['hip'][1] - 75
    if loud:
        arcs(c, bx, by, 62, 3, t)
        gurr(c, 'GURRR!', 540, 600, 130, t, CORAL, pop(t, h0 - .25 if intro else tgu, .3))
    elif t > o0:
        with xf(c, 540, 560, pop(t, o0, .3), -2): pill(c, 'şşşt... sessizlik', 540, 560, 46, INK)
    if stare:
        hx, hy = me['head']
        for x in (180, 900):
            sd = 1 if x < 540 else -1
            dashes(c, (x + sd * 75, gy - 300), (hx - sd * 75, hy + 5), 5, CORAL, 6, seg(t, b0 - .1, b0 + .2))

def scene2(c, t):
    a0, a1 = L(4); s0, s1 = L(5)
    tac = cap_start(4, 'açlık', a0 + 1.2); tbo = L(6)[0]
    gy = 1040
    wash(c, 60, 340, 1020, gy, WASH_T)
    ground(c, 60, 1020, gy)
    me = fig(c, 300, gy, 1.05, 0, FRONT, 'happy' if t > tac + .4 else 'smile')
    arcs(c, me['hip'][0], me['hip'][1] - 78, 60, 2, t, CORAL, 6)
    if t > tac - .5:
        with xf(c, 300, 470, pop(t, tac - .5, .3), -3): pill(c, 'sadece açlık', 300, 470, 46, INK)
        if t > tac + .25: cross(c, 300, 470, 2.2, seg(t, tac + .25, tac + .55))
    gurr(c, 'GURRR', 730, 640, 110, t, CORAL, pop(t, a0 - .1, .3))
    if t > s0:
        with xf(c, 730, 790, pop(t, s0, .3), 2):
            if t < tbo: pill(c, 'adı ne?', 730, 790, 46, INK)
            else: pill(c, 'adı var!', 730, 790, 46, TEAL, PAPER)
    if t > tbo:
        with xf(c, 540, 1160, pop(t, tbo, .35), -1.5): ybox(c, 'borborigmi', 540, 1160, 66, 760)

def scene3(c, t):
    m0, m1 = L(7); k0, k1 = L(8); g0, g1 = L(9); s0, s1 = L(10)
    tbg = cap_start(7, 'bağırsakların', m0 + .5); tka = cap_start(8, 'kasılıp', k0 + 1.2)
    tgz = cap_start(9, 'gaz', g0 + .6); tse = cap_start(9, 'ses', g1 - .8)
    tmi = cap_start(10, 'mideden', s0 + .4); tin = cap_start(10, 'ince', s1 - 1.6)
    wash(c, 60, 340, 1020, 1150, WASH_P)
    gut(c, seg(t, tbg - .2, tbg + 1.5))
    txt(c, 'mide', 340, 578, 50, INK, alpha=seg(t, m0, m0 + .2))
    if tbg + 1.0 < t < tin:
        with xf(c, 560, 875, pop(t, tbg + 1.0, .3)): pill(c, 'bağırsak', 560, 875, 34, INK)
    if t > tka - .2: flow(c, t, tka - .2)
    if tka - .2 < t < tse:
        with xf(c, 720, 470, pop(t, tka - .2, .3), -2): pill(c, 'kaslar itiyor', 720, 470, 40, TEAL, PAPER)
        arrow(c, (600, 540), (790, 560), TEAL, 8, seg(t, tka, tka + .3))
    if t > tgz:
        with xf(c, 110, 1035, pop(t, tgz, .3)): dot(c, (110, 1035), 16, PAPER)
        txt(c, 'gaz', 140, 1050, 42, INK, align='l', alpha=seg(t, tgz, tgz + .15))
        tsv = tgz + .45
        if t > tsv:
            with xf(c, 110, 1100, pop(t, tsv, .3)): dot(c, (110, 1100), 13, TEAL)
            txt(c, 'sıvı', 140, 1115, 42, INK, align='l', alpha=seg(t, tsv, tsv + .15))
    if t > tse:
        gurr(c, 'GURRR', 740, 500, 96, t, CORAL, pop(t, tse, .3))
        arcs(c, 150, 875, 26, 2, t, side=(-1,))
        arcs(c, 925, 722, 20, 2, t, side=(1,))
    if t > tmi: arcs(c, 172, 560, 20, 3, t, side=(-1,))
    if t > tin:
        with xf(c, 560, 875, pop(t, tin, .3)): pill(c, 'ince bağırsak', 560, 875, 34, CORAL, PAPER)
        arcs(c, 925, 1025, 20, 2, t, side=(1,))
    if t > tin + .5:
        with xf(c, 540, 1200, pop(t, tin + .5, .35), -1.5): ybox(c, 'ses bağırsaktan da geliyor', 540, 1200, 46, 820)

FOOD = ((-75, 25, 36, YEL), (5, 55, 42, CORAL), (70, -15, 32, TEAL), (-20, -45, 34, BROWN), (95, 50, 26, YEL), (-110, -25, 24, TEAL), (35, -80, 22, CORAL), (-60, 80, 24, BROWN))

def scene4(c, t):
    h0, h1 = L(11); k0, k1 = L(12); b0, b1 = L(13)
    tye = cap_start(12, 'yemek', k0 + .5); tba = cap_start(12, 'bastırıyor', k1 - .8); tci = cap_start(13, 'çınlıyor', b1 - .9)
    wash(c, 60, 340, 1020, 1110, WASH_T)
    quiet = t > tba; loud = t > b0 + .2
    for cx, kind in ((290, 'tok'), (790, 'boş')):
        emp = kind == 'boş'
        with xf(c, cx, 740, lerp(.85, 1, pop(t, h0 - .2 + (.15 if emp else 0), .35)) * (1 + (.02 * math.sin(t * 24) if emp and loud else 0))):
            stomach(c, cx, 740, .9)
            if emp:
                for i, (dx, dy, r) in enumerate(((-60, 30, 16), (40, -30, 12), (70, 50, 10))):
                    circ(c, cx + dx, 740 + dy + 6 * math.sin(t * 5 + i), r, w=4, fill=PAPER, amp=.8, n=9)
            else:
                for i, (dx, dy, r, col) in enumerate(FOOD):
                    tf = tye + .07 * i
                    if t > tf:
                        with xf(c, cx + dx, 740 + dy, pop(t, tf, .2)): circ(c, cx + dx, 740 + dy, r, w=5, fill=col, amp=1, n=10)
    if t > h0 + .2:
        if quiet: arcs(c, 290, 740, 185, 1, t, MUTE, 6)
        else: arcs(c, 290, 740, 185, 2, t, CORAL, 6)
        arcs(c, 790, 740, 185, 3 if loud else 2, t, CORAL, 8 if loud else 6)
    if t > k0:
        with xf(c, 290, 420, pop(t, k0, .3), -2): pill(c, 'tok', 290, 420, 50, TEAL, PAPER)
    if t > b0:
        with xf(c, 790, 420, pop(t, b0, .3), 2): pill(c, 'boş', 790, 420, 50, CORAL, PAPER)
    if quiet:
        txt(c, 'gur', 290, 965, 44, MUTE, alpha=seg(t, tba, tba + .2))
        with xf(c, 290, 1045, pop(t, tba + .2, .3), -2): pill(c, 'yemek sesi bastırıyor', 290, 1045, 30, TEAL, PAPER)
    if loud: gurr(c, 'GURRR!', 790, 1045, 84, t, CORAL, pop(t, b0 + .2, .3))
    if h0 + .4 < t < b0:
        with xf(c, 540, 1190, pop(t, h0 + .4, .35), -1.5): ybox(c, 'bu ses hep var', 540, 1190, 50, 800)
    if t > tci:
        with xf(c, 540, 1190, pop(t, tci, .35), -1.5): ybox(c, 'boşken sesi bastıran yok', 540, 1190, 46, 820)

CRUMB = (.13, .27, .41, .56, .7, .85)

def scene5(c, t):
    m0, m1 = L(14); g0, g1 = L(15); y0, y1 = L(16)
    tda = cap_start(14, 'kasılma', m1 - 1.6); tar = cap_start(15, 'artıkları', g0 + 1.2); tsa = cap_start(16, 'saatte', y0 + 1.2)
    wash(c, 60, 340, 1020, 1150, WASH_Y)
    gut(c, 1.0)
    txt(c, 'boş', 340, 578, 50, MUTE)
    second = t > y0 + .3
    w1 = seg(t, tda, tda + 3.6); uw = seg(t, y0 + .3, y0 + 2.9) if second else w1
    if 0 < uw < 1:
        N = len(GUT); i1 = max(2, int(uw * N)); i0 = max(0, i1 - int(.085 * N))
        p = skia.Path(); p.moveTo(*GUT[i0])
        for q in GUT[i0 + 1:i1]: p.lineTo(*q)
        c.drawPath(p, paint(YEL, 50))
        q = along(GUT, uw); c.drawCircle(q[0], q[1], 30, paint(INK, fill=True)); c.drawCircle(q[0], q[1], 22, paint(CORAL, fill=True))
    if not second:
        for k, u in enumerate(CRUMB):
            v = u if w1 < u - .02 else w1 + .025 + .012 * (len(CRUMB) - k)
            if v < 1:
                q = along(GUT, v); c.drawCircle(q[0], q[1] + (5 if k % 2 else -5), 9, paint(INK, fill=True)); c.drawCircle(q[0], q[1] + (5 if k % 2 else -5), 6, paint(BROWN, fill=True))
    if m0 + .3 < t < g1:
        with xf(c, 215, 1060, pop(t, m0 + .3, .3), -2): pill(c, 'yemek artıkları', 215, 1060, 32, INK)
    if tda < t < y0:
        with xf(c, 720, 470, pop(t, tda, .3), -2): pill(c, 'temizlik dalgası', 720, 470, 40, TEAL, PAPER)
    if tar < t < y0:
        with xf(c, 540, 1200, pop(t, tar, .35), -1.5): ybox(c, 'kalan artıkları süpürüyor', 540, 1200, 46, 820)
    if t > tsa:
        with xf(c, 720, 470, pop(t, tsa, .3), -2):
            circ(c, 560, 470, 40, w=7, fill=PAPER, amp=1, n=12)
            line(c, [(560, 470), (560, 444)], INK, 6, amp=.4); line(c, [(560, 470), (580, 480)], INK, 6, amp=.4)
            pill(c, '1-2 saatte bir', 770, 470, 40, CORAL, PAPER)
        with xf(c, 540, 1200, pop(t, tsa + .3, .35), -1.5): ybox(c, 'yiyene kadar tekrar ediyor', 540, 1200, 46, 820)

def scene6(c, t):
    a0, a1 = L(17); d0, d1 = L(18); e0, e1 = L(19)
    tgu = cap_start(17, 'guruldar', a1 - .9)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_T)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    aha = t > d0 - .1
    x = 580
    if not aha:
        rum = t > tgu
        me = fig(c, x, gy, .95, 0, dict(FRONT, lean=2.5 * math.sin(t * 26)) if rum else FRONT, 'oh' if rum else 'confused')
        if rum:
            arcs(c, me['hip'][0], me['hip'][1] - 72, 58, 3, t)
            gurr(c, 'GURRR!', 850, 900, 80, t, CORAL, pop(t, tgu, .3))
    else:
        pose = mix(dict(FRONT, aR=20, eR=150, aL=10, eL=6), dict(FRONT, aR=10, eR=6, aL=148, eL=160 + 26 * math.sin(t * 9)), wv)
        me = fig(c, x, gy, .95, 0, pose, 'happy')
    hx, hy = me['top']
    if not aha: qmark(c, hx - 150, hy + 40, 150, t, CORAL, 1.0, pop(t, a0 + .3, .3))
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
