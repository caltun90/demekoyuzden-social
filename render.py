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

TITLE = 'Barnum Etkisi'   # yatay formatta etiketin altinda gorunur
HOOK = 'Burcun neden hep tutuyor?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['BURÇ YORUMU', 'NEDEN HEP', 'TUTUYOR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 4.2                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['şaşırdın.'], 1: ['beni'], 2: ['herkese'], 3: ['barnum', 'etkisi.'], 4: ["1949'da"], 5: ['kişilik', 'testi'], 6: ['kişiye', 'özel'],
      7: ['isabetli'], 8: ['dördün'], 9: ['aynı', 'metni'], 10: ['burç', 'kitabından'], 11: ['geneldir.'], 12: ['sosyalsin,', 'yalnız'],
      13: ['kendinden'], 14: ['olumluysa', 'özel'], 15: ['seni'], 16: ['demek', 'o', 'yüzden!']}


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

def star(c, x, y, r, fill=YEL, color=INK, w=6, alpha=1.0):
    """bes koseli yildiz (burc simgesi / puan)"""
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36); rr = r if i % 2 == 0 else r * .45
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    line(c, pts, color, w, alpha=alpha, amp=.6, closed=True, fill=fill)

def sheet(c, x, y, w=200, h=250, n=5, hl=0, alpha=1.0):
    """kagit: ustte yildizli baslik, altinda yazi satirlari; hl = ustten kac satir sari vurgulu"""
    x0, y0 = x - w / 2, y - h / 2
    box(c, x0, y0, x0 + w, y0 + h, r=14, w=7, fill=PAPER, alpha=alpha, amp=1)
    star(c, x0 + 38, y0 + 40, 20, w=4, alpha=alpha)
    line(c, [(x0 + 72, y0 + 40), (x0 + w - 26, y0 + 40)], INK, 7, alpha=alpha, amp=.6)
    for k in range(n):
        yy = y0 + 88 + k * 34
        if k < hl: c.drawRect(skia.Rect.MakeLTRB(x0 + 16, yy - 14, x0 + w - 16, yy + 14), paint(YEL, fill=True, alpha=alpha))
        line(c, [(x0 + 24, yy), (x0 + w - 24 - (34 if k % 2 else 0), yy)], MUTE, 6, alpha=alpha, amp=.6)

def phone(c, x, y, s=1.0):
    box(c, x - 50 * s, y - 90 * s, x + 50 * s, y + 90 * s, r=14 * s, w=max(5, 7 * s), fill=PAPER, amp=.8)
    c.drawCircle(x, y + 66 * s, 8 * s, paint(INK, fill=True))
    star(c, x, y - 16 * s, 28 * s, w=max(3, 4 * s))

def emark(c, x, y, size, t, color=CORAL, sc=1.0):
    with xf(c, x, y - size * .35, sc, 8 * math.sin(t * 5)):
        txt(c, '!', x, y, size, color)

def book(c, x, y, s=1.0):
    """burc kitabi"""
    box(c, x - 120 * s, y - 150 * s, x + 120 * s, y + 150 * s, r=14 * s, w=8, fill=CORAL, amp=1)
    line(c, [(x - 88 * s, y - 146 * s), (x - 88 * s, y + 146 * s)], INK, 6, amp=.8)
    star(c, x + 16 * s, y - 40 * s, 52 * s, w=6)
    txt(c, 'BURÇLAR', x + 16 * s, y + 96 * s, 36 * s, PAPER)

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1)
    gy = 1150
    wash(c, 60, 340, 1020, gy + 20, WASH_Y)
    ground(c, 60, 1020, gy)
    ts = cap_start(0, 'şaşırdın', a1 - .8)
    sur = smooth(seg(t, ts - .05, ts + .2))
    pose = mix(dict(STAND, aR=60, eR=122), dict(STAND, aR=64, eR=126, lean=-5, tilt=-6, aL=-30, eL=40), sur)
    hp = {}
    def hold(p): hp['p'] = p; phone(c, p[0] + 14, p[1] - 34, .66)
    me = fig(c, 340, gy, 1.05, 1, pose, 'smile' if sur < .5 else 'oh', hold=hold)
    px, py = hp['p'][0] + 14, hp['p'][1] - 34
    if t > a0 + .2:
        p = pop(t, a0 + .2, .3)
        with xf(c, 790, 650, p):
            speech(c, 580, 550, 1010, 770, (px + 60, py - 20))
            star(c, 632, 600, 24, w=4)
            txt(c, 'burç yorumun', 826, 614, 38, CORAL)
            for k, wd in enumerate((350, 300, 330)):
                line(c, [(616, 666 + k * 36), (616 + wd, 666 + k * 36)], MUTE, 7, seg(t, a0 + .5 + k * .2, a0 + .8 + k * .2), amp=.6)
    if sur > .05:
        hx, hy = me['head']
        for k, (dx, dy) in enumerate(((-70, -64), (-88, -30))):
            line(c, [(hx + dx, hy + dy), (hx + dx - 30, hy + dy - 16 + 8 * k)], INK, 6, alpha=sur, amp=.5)
    if t > b0 - .1:
        p = pop(t, b0 - .1, .35)
        with xf(c, 290, 470, p):
            cloud(c, 290, 462, 215, 90, tail=(330, 655))
            txt(c, 'Bu resmen ben!', 290, 478, 46, INK)
        tm = cap_start(1, 'beni', b0 + .5)
        if t > tm: emark(c, 660, 505, 170, t, CORAL, pop(t, tm, .3))

def scene2(c, t):
    a0, a1 = L(2); n0, n1 = L(3)
    gy = 1090
    ty = cap_start(2, 'aynı', a0 + .4); th = cap_start(2, 'herkese', a1 - 1.3); tb = cap_start(3, 'Barnum', n1 - 1.0)
    with xf(c, 540, 455, pop(t, a0 - .1, .35)): sheet(c, 540, 455, 230, 220, n=4)
    if t > ty:
        with xf(c, 540, 618, pop(t, ty, .3)): pill(c, 'aynı yorum', 540, 618, 40, CORAL, PAPER)
    ground(c, 50, 1030, gy, seg(t, a0, a0 + .4))
    for k, x in enumerate((165, 415, 665, 915)):
        p = pop(t, a0 + .3 + k * .12, .3)
        if p <= 0: continue
        tk = th + k * .16
        ok = t > tk
        with xf(c, x, gy, p):
            fig(c, x, gy, .6, 0, dict(FRONT, aL=150, eL=165, aR=150, eR=165) if ok else None, 'happy' if ok else 'smile')
        dashes(c, (540 + (x - 540) * .3, 665), (x, 730 if ok else 790), 3, MUTE, 6, seg(t, th - .3, th))
        if ok: check(c, x, 772, .95, seg(t, tk, tk + .3))
    if t > tb:
        with xf(c, 540, 1195, pop(t, tb, .35), -2):
            box(c, 240, 1140, 840, 1250, r=26, w=8, fill=YEL)
            txt(c, 'Barnum etkisi', 540, 1216, 64, INK)

def scene3(c, t):
    y0_, y1_ = L(4); f0, f1 = L(5); s0, s1 = L(6); i0, i1 = L(7); o0, o1 = L(8)
    gy = 1225
    fa = 1 - smooth(seg(t, s0 - .3, s0 - .05))
    if fa > .01:
        with xf(c, 540, 800, 1, 0, fa):
            with xf(c, 540, 440, pop(t, y0_ - .1, .35)): txt(c, '1949', 540, 490, 150, CORAL)
            if t > f0 - .1:
                with xf(c, 540, 650, pop(t, f0 - .1, .35)):
                    box(c, 200, 565, 880, 735, r=30, w=8, fill=PAPER)
                    txt(c, 'Bertram Forer', 540, 648, 60, INK)
                    txt(c, 'psikolog · ABD', 540, 702, 32, MUTE, 'med')
            tt = cap_start(5, 'kişilik', f1 - 1.3)
            if t > tt:
                with xf(c, 540, 1010, pop(t, tt, .35), -2):
                    box(c, 320, 810, 760, 1230, r=22, w=8, fill=PAPER)
                    txt(c, 'KİŞİLİK TESTİ', 540, 880, 44, INK)
                    line(c, [(360, 906), (720, 906)], INK, 6, amp=.8)
                    for k in range(4):
                        yy = 968 + k * 62
                        box(c, 364, yy - 20, 404, yy + 20, r=6, w=5, amp=.6)
                        line(c, [(432, yy), (706 - (40 if k % 2 else 0), yy)], MUTE, 7, amp=.6)
                        check(c, 384, yy - 2, .5, seg(t, tt + .35 + k * .22, tt + .55 + k * .22))
    if t > s0 - .3:
        a = seg(t, s0 - .2, s0 + .1)
        tk = cap_start(6, 'kişiye', s0 + 1.0); ti = cap_start(7, 'isabetli', i0 + 1.0); td = cap_start(8, 'beş', o0 + 1.0)
        so = smooth(seg(t, o0 - .25, o0))
        xs = (200, 540, 880)
        with xf(c, 540, 800, 1, 0, a):
            ground(c, 50, 1030, gy)
            for k, x in enumerate(xs):
                hap = t > ti + k * .12
                fig(c, x, gy, .62, 0, dict(FRONT, aL=150, eL=165, aR=150, eR=165) if hap else None, 'happy' if hap else 'smile')
                if hap:
                    with xf(c, x, 895, pop(t, ti + k * .12, .3)): txt(c, 'Tam ben!', x, 908, 40, TEAL)
            if so < 1:
                with xf(c, 540, 600, 1, 0, 1 - so):
                    for k, x in enumerate(xs):
                        u = smooth(seg(t, s0 + k * .15, s0 + .5 + k * .15))
                        sheet(c, x, lerp(430, 560, u), 210, 250, alpha=u)
                        if t > tk + k * .12:
                            with xf(c, x, 742, pop(t, tk + k * .12, .3)): pill(c, 'sana özel', x, 742, 34, CORAL, PAPER)
            if so > 0:
                with xf(c, 540, 600, 1, 0, so):
                    txt(c, 'ortalama puan', 540, 420, 44, MUTE, 'med')
                    for k in range(5):
                        x = 240 + k * 150
                        on = seg(t, td + k * .13, td + k * .13 + .12)
                        n0 = St.n
                        if k < 4: star(c, x, 550, 66 * lerp(.8, 1, back(on)), fill=YEL if on > 0 else PAPER, w=7)
                        else:
                            star(c, x, 550, 66, fill=PAPER, w=7)
                            if on > 0:
                                St.n = n0
                                c.save(); c.clipRect(skia.Rect.MakeLTRB(x - 70, 470, x - 70 + 140 * .36, 630))
                                star(c, x, 550, 66, fill=YEL, w=7); c.restore()
                    tdd = cap_start(8, 'dördün', td + .8)
                    if t > tdd:
                        with xf(c, 540, 730, pop(t, tdd, .3)): txt(c, '5 üzerinden 4+', 540, 756, 84, INK)

def scene4(c, t):
    o0, o1 = L(9); u0, u1 = L(10)
    gy = 1235
    tk = cap_start(9, 'kelimesi', o0 + .9); ta = cap_start(9, 'aynı', o1 - 1.2); tb = cap_start(10, 'burç', u0 + 1.2)
    xs = (200, 540, 880)
    nh = int(5 * seg(t, tk, ta) + .001)
    for k, x in enumerate(xs):
        with xf(c, x, 520, pop(t, o0 - .1 + k * .1, .35)): sheet(c, x, 520, 220, 260, hl=nh)
    if t > ta:
        p = pop(t, ta, .3)
        for x in (370, 710):
            with xf(c, x, 520, p): txt(c, '=', x, 548, 90, CORAL)
        with xf(c, 540, 770, pop(t, ta + .1, .35), -2):
            box(c, 300, 712, 780, 828, r=26, w=8, fill=YEL)
            txt(c, 'AYNI METİN', 540, 794, 66, INK)
    ground(c, 50, 1030, gy, seg(t, o0, o0 + .4))
    fig(c, 250, gy, .74, 1, dict(STAND, aR=70, eR=130) if t > ta else None, 'oh' if t > ta else 'flat')
    if t > u0 - .1:
        with xf(c, 740, 1060, pop(t, u0 - .1, .35), 4): book(c, 740, 1060, .98)
        if t > tb:
            a = seg(t, tb, tb + .3)
            line(c, [(700, 900), (660, 868), (640, 838)], INK, 7, a, curve=True, amp=.6)
            line(c, [(618, 868), (638, 836), (672, 846)], INK, 7, seg(t, tb + .25, tb + .4), amp=.5)

def scene5(c, t):
    g0, g1 = L(11); m0, m1 = L(12); h0, h1 = L(13); e0, e1 = L(14)
    gy = 1225
    xs = (200, 540, 880)
    fa = 1 - smooth(seg(t, e0 - .3, e0 - .05))
    if fa > .01:
        tg = cap_start(11, 'herkese', g0 + 1.0); tb1 = cap_start(12, 'sosyalsin', m0 + .5); tb2 = cap_start(12, 'yalnız', m0 + 1.8)
        tp = cap_start(13, 'kendinden', h0 + .9)
        with xf(c, 540, 800, 1, 0, fa):
            with xf(c, 540, 395, pop(t, g0 - .1, .35)): pill(c, 'genel cümleler', 540, 395, 46, TEAL, PAPER)
            with xf(c, 540, 600, pop(t, g0 + .1, .35)):
                box(c, 100, 480, 980, 720, r=30, w=8, fill=PAPER)
                if t < tb1:
                    for k, wd in enumerate((700, 620, 660)): line(c, [(170, 545 + k * 55), (170 + wd, 545 + k * 55)], MUTE, 8, amp=.8)
                else:
                    s1_, s2_ = '“Bazen sosyalsin,', 'bazen yalnız kalmak istersin.”'
                    sz = 58
                    while tw(s2_, sz) > 800: sz -= 2
                    txt(c, s1_, 540, 582, sz, INK, alpha=seg(t, tb1, tb1 + .2))
                    txt(c, s2_, 540, 662, sz, INK, alpha=seg(t, tb2, tb2 + .2))
            ground(c, 50, 1030, gy, seg(t, tg - .2, tg + .2))
            for k, x in enumerate(xs):
                p = pop(t, tg + k * .12, .3)
                if p <= 0: continue
                me_ = t > tp + k * .15
                with xf(c, x, gy, p): fig(c, x, gy, .62, 0, dict(FRONT, aR=40, eR=150) if me_ else None, 'happy' if me_ else 'smile')
                if me_:
                    dashes(c, (540 + (x - 540) * .6, 735), (x, 820), 3, MUTE, 6, seg(t, tp + k * .15, tp + k * .15 + .2))
                    with xf(c, x, 880, pop(t, tp + k * .15, .3)): pill(c, 'bu ben!', x, 880, 38, CORAL, PAPER)
    if t > e0 - .3:
        a = seg(t, e0 - .2, e0 + .1)
        to_ = cap_start(14, 'olumluysa', e0 + .6); tz = cap_start(14, 'özel', e0 + 1.8); ti = cap_start(14, 'inanırız', e1 - 1.0)
        lvl = lerp(lerp(.28, .62, smooth(seg(t, to_, to_ + .4))), 1.0, smooth(seg(t, tz, tz + .5)))
        with xf(c, 540, 800, 1, 0, a):
            ground(c, 50, 1030, gy)
            txt(c, 'ne kadar inanırız?', 540, 400, 46, INK)
            wash(c, 170, 440, 170 + 740 * lvl, 520, YEL, r=24)
            box(c, 170, 440, 910, 520, r=24, w=8)
            if t > to_:
                with xf(c, 280, 650, pop(t, to_, .3), -3): pill(c, '+ olumlu', 280, 650, 50, TEAL, PAPER)
            if t > tz:
                with xf(c, 790, 650, pop(t, tz, .3), 3): pill(c, '+ bana özel', 790, 650, 50, CORAL, PAPER)
            up = smooth(seg(t, ti, ti + .25))
            pose = mix(dict(FRONT), dict(FRONT, aL=150, eL=165, aR=150, eR=165), up)
            fig(c, 540, gy, .95, 0, pose, 'happy' if t > to_ else 'smile')
            if t > ti: burst(c, 910, 480, 60, 60 + 34 * pop(t, ti, .3), 8, CORAL, 7)

def scene6(c, t):
    a0, a1 = L(15); d0, d1 = L(16); e0, e1 = L(17)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_Y)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    aha = t > d0 - .1
    pose = dict(FRONT, aR=30, eR=150, aL=10, eL=6, tilt=-6 if not aha else 0)
    pose = mix(pose, dict(FRONT, aR=30, eR=150, aL=148, eL=160 + 26 * math.sin(t * 9)), wv)
    def hold(p): phone(c, p[0] + 4, p[1] - 40, .6)
    me = fig(c, 540, gy, .95, 0, pose, 'confused' if not aha else 'happy', hold=hold)
    hx, hy = me['top']
    if not aha:
        bx, by = me['handR'][0] + 150, me['handR'][1] - 150
        with xf(c, bx, by, pop(t, a0, .3)):
            speech(c, bx - 130, by - 62, bx + 130, by + 62, (me['handR'][0] + 46, me['handR'][1] - 70))
            txt(c, 'tam sen!', bx, by + 16, 44, CORAL)
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
