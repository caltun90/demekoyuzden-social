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

TITLE = 'Araç Tutması'   # yatay formatta etiketin altinda gorunur
HOOK = 'Arabada mide neden bulanır?'     # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['ARABADA', 'MİDE NEDEN', 'BULANIR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 7.4                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['telefona'], 1: ['miden', 'bulanıyor.'], 2: ['şoföre'], 3: ['yaygın.'], 4: ['duyusal', 'çatışma.'], 5: ['hareketi'],
      6: ['dönüyoruz,', 'sallanıyoruz.'], 7: ['sabit', 'duruyoruz'], 8: ['karışıyor.'], 9: ['şoförü'], 10: ['önceden'], 11: ["1991'de"],
      12: ['aynı'], 13: ['daha', 'az'], 14: ['mide?'], 16: ['zehirlenme'], 17: ['uzağa'], 18: ['fenalaşırsın'], 19: ['demek', 'o', 'yüzden!']}

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
SICK = 0xFFCFE2A6   # mide bulantisi: yuz yesile calar

def pill(c, s, cx, cy, size=34, col=INK, fg=BG):
    w = tw(s, size); h = size * 1.7
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 26, cy - h / 2, cx + w / 2 + 26, cy + h / 2), h / 2, h / 2), paint(col, fill=True))
    txt(c, s, cx, cy + size * .36, size, fg)

def spiral(c, x, y, r, t, color=CORAL, w=6, alpha=1.0):
    """bas donmesi / bulanti isareti"""
    pts = [(x + r * (i / 22) * math.cos(i * .62 + t * 4), y + r * (i / 22) * math.sin(i * .62 + t * 4)) for i in range(23)]
    line(c, pts, color, w, alpha=alpha, amp=.5, curve=True)

def head(c, x, y, r, mood='ok', fc=1, tint=0.0):
    """govdesiz bas (arabadaki yolcu, deney katilimcisi). mood: ok / happy / sick"""
    s = r / 48
    c.drawCircle(x, y, r, paint(PAPER, fill=True))
    if tint > 0: c.drawCircle(x, y, r, paint(SICK, fill=True, alpha=tint))
    circ(c, x, y, r, color=INK, w=9 * s, amp=1.2 * s)
    for dx in (fc * 5 * s, fc * 29 * s):
        px, py = x + dx, y - 6 * s
        if mood == 'sick':
            c.drawCircle(px, py, 9 * s, paint(INK, 3.5 * s)); c.drawCircle(px, py + 2 * s, 4 * s, paint(INK, fill=True))
        elif mood == 'happy':
            line(c, [(px - 8 * s, py + 3 * s), (px, py - 6 * s), (px + 8 * s, py + 3 * s)], INK, 5 * s, amp=.5, curve=True)
        else: c.drawCircle(px, py, 5.5 * s, paint(INK, fill=True))
    mx, my = x + fc * 17 * s, y + 21 * s
    if mood == 'sick':
        line(c, [(mx - 15 * s, my + 2 * s), (mx - 5 * s, my - 5 * s), (mx + 5 * s, my + 5 * s), (mx + 15 * s, my - 2 * s)], INK, 5 * s, amp=.4, curve=True)
    else:
        line(c, [(mx - 13 * s, my - 3 * s), (mx, my + 7 * s), (mx + 13 * s, my - 3 * s)], INK, 5 * s, amp=.5, curve=True)

def phone(c, x, y, s=1.0, rot=0):
    with xf(c, x, y, 1, rot):
        box(c, x - 26 * s, y - 46 * s, x + 26 * s, y + 46 * s, r=9 * s, w=max(4, 6 * s), fill=INK, amp=.6)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 18 * s, y - 35 * s, x + 18 * s, y + 33 * s), 4 * s, 4 * s), paint(TEAL, fill=True))

def car(c, x, gy, s=1.0, t=0.0, back='ok', front='ok', sick=0.0, road=True):
    """yandan araba, saga gider. x: orta, gy: yer. Arkada telefonlu yolcu, onde sofor. sick 0-1: yolcunun bulantisi"""
    with xf(c, x, gy, s):
        if road:
            for k in range(5):
                dx = ((k * 270 - t * 560) % 1350) - 675
                line(c, [(x + dx, gy + 44), (x + dx + 100, gy + 44)], MUTE, 8, amp=.8)
        y = gy + 4 * math.sin(t * 7)
        cab = [(x - 285, y - 236), (x - 220, y - 398), (x - 172, y - 426), (x + 150, y - 426), (x + 200, y - 398), (x + 300, y - 236)]
        line(c, cab, INK, 10, closed=True, fill=PAPER, amp=1.4)
        head(c, x - 120, y - 300, 52, 'sick' if sick > .5 else back, 1, sick)
        head(c, x + 105, y - 300, 52, front, 1)
        line(c, [(x - 8, y - 426), (x - 8, y - 236)], INK, 10, amp=1)                # orta direk
        line(c, [(x + 196, y - 244), (x + 222, y - 300)], INK, 9, amp=.6)            # direksiyon
        line(c, [(x + 206, y - 322), (x + 240, y - 286)], INK, 11, amp=.6)
        phone(c, x - 40, y - 272, .6, -16)
        box(c, x - 400, y - 240, x + 400, y - 78, r=58, w=10, fill=CORAL)
        circ(c, x + 372, y - 178, 13, 22, color=INK, w=6, fill=YEL, n=10, amp=.8)   # far
        for dx in (-150, 70): line(c, [(x + dx, y - 168), (x + dx + 52, y - 168)], INK, 7, amp=.6)   # kapi kollari
        line(c, [(x - 8, y - 236), (x - 8, y - 84)], INK, 6, alpha=.55, amp=.8)
        for dx in (-245, 245):
            wx, wy = x + dx, gy - 62
            circ(c, wx, wy, 62, color=INK, w=10, fill=INK, n=14, amp=1)
            c.drawCircle(wx, wy, 26, paint(PAPER, fill=True))
            a = t * 9
            line(c, [(wx - 22 * math.cos(a), wy - 22 * math.sin(a)), (wx + 22 * math.cos(a), wy + 22 * math.sin(a))], INK, 6, amp=.3)

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1); d0, d1 = L(2)
    gy = 1066; x = 540
    wash(c, 60, 340, 1020, gy + 76, WASH_T)
    tp = cap_start(0, 'telefona', a0 + .9)
    tm = cap_start(1, 'miden', b0 + 1.3)
    ts = cap_start(2, 'hiçbir', d0 + .8)
    sick = smooth(seg(t, tm - .1, tm + .6))
    ok = pop(t, ts, .3)
    for k in range(3):                                         # hiz cizgileri
        yy = gy - 330 + k * 90; u = (t * 1.6 + k * .37) % 1
        line(c, [(118 - 50 * u, yy), (60 - 50 * u, yy)], MUTE, 7, alpha=1 - u, amp=.6)
    car(c, x, gy, 1.0, t, 'ok', 'happy' if ok > 0 else 'ok', sick)
    pp = pop(t, tp, .3)
    if pp > 0:
        with xf(c, 300, 420, pp): pill(c, 'telefona bakıyor', 300, 420, 36, INK, PAPER)
    if sick > 0.02:                                            # bulanti
        for k, (dx, dy, r) in enumerate(((-150, -520, 46), (-60, -556, 34), (-232, -536, 28))):
            spiral(c, x + dx, gy + dy + 5 * math.sin(t * 3 + k), r * sick, t + k, CORAL, 7, sick)
    if ok > 0:
        with xf(c, 800, 420, ok): pill(c, 'şoför', 760, 420, 36, TEAL, PAPER)
        check(c, 892, 420, .8, seg(t, ts + .2, ts + .5))
        txt(c, 'sorun yok', 800, 510, 38, TEAL, alpha=seg(t, ts + .3, ts + .55))

def scene2(c, t):
    a0, a1 = L(3); b0, b1 = L(4)
    gy = 1170; x = 540
    tt = cap_start(4, 'duyusal', b0 + 1.4)
    c.drawOval(skia.Rect.MakeLTRB(x - 170, gy - 16, x + 170, gy + 22), paint(0xFFEDE3D0, fill=True))
    shr = smooth(seg(t, a0, a0 + .35)) * (1 - smooth(seg(t, a1 - .2, a1 + .2)))
    pt = smooth(seg(t, tt - .1, tt + .3))
    pose = mix(FRONT, dict(FRONT, aL=38, eL=118, aR=38, eR=118, tilt=5), shr)
    pose = mix(pose, dict(FRONT, aR=152, eR=168 + 4 * math.sin(t * 6), aL=14, eL=8, tilt=-3), pt)
    fig(c, x, gy, 1.0, 0, pose, 'happy' if (t < a1 + .3 or t > tt) else 'smile')
    fr = pop(t, a0 + .4, .3) * (1 - smooth(seg(t, tt - .5, tt - .15)))
    if fr > 0.01:                                              # cok yaygin: baskalarina da oluyor
        for k, (fx, fc) in enumerate(((205, 1), (875, -1))):
            with xf(c, fx, gy, fr):
                o = fig(c, fx, gy - 8, .62, fc, dict(STAND, aR=40, eR=120, aL=30, eL=110, tilt=6), 'sad')
            sp = fr * pop(t, a0 + .7 + k * .35, .3)
            if sp > 0.01: spiral(c, o['top'][0], o['top'][1] - 50, 34 * sp, t + k, CORAL, 6)
    if t > tt:
        p = pop(t, tt, .35)
        with xf(c, 540, 460, lerp(.7, 1, p), 0, seg(t, tt, tt + .15)):
            txt(c, 'DUYUSAL', 540, 424, 108, INK)
            txt(c, 'ÇATIŞMA', 540, 540, 108, CORAL)
        line(c, [(270, 576), (400, 570), (580, 580), (810, 568)], INK, 10, seg(t, tt + .4, tt + .8), curve=True)
        txt(c, 'göz ile iç kulak aynı şeyi söylemiyor', 540, 636, 36, MUTE, 'med', alpha=seg(t, tt + .7, tt + 1.0))

def snail(c, x, y, s=1.0, color=INK):
    """ic kulak (salyangoz)"""
    pts = [(x + s * (6 + 3.2 * i) * math.cos(i * .5), y + s * (6 + 3.2 * i) * math.sin(i * .5)) for i in range(26)]
    line(c, pts, color, 9 * s, amp=.5, curve=True)

def eye(c, x, y, s=1.0):
    line(c, [(x - 72 * s, y), (x - 36 * s, y - 34 * s), (x, y - 46 * s), (x + 36 * s, y - 34 * s), (x + 72 * s, y), (x + 36 * s, y + 34 * s), (x, y + 46 * s), (x - 36 * s, y + 34 * s)],
         INK, 8 * s, closed=True, fill=PAPER, curve=True, amp=1)
    c.drawCircle(x + 8 * s, y, 25 * s, paint(TEAL, fill=True)); c.drawCircle(x + 12 * s, y, 11 * s, paint(INK, fill=True))

def scene3(c, t):
    a0, a1 = L(5); b0, b1 = L(6); d0, d1 = L(7); e0, e1 = L(8)
    bx, by, ny = 540, 480, 890
    th = cap_start(5, 'hareketi', a0 + .9); td = cap_start(7, 'duruyoruz', d1 - 1.2)
    tk = cap_start(8, 'karışıyor', e1 - .8)
    mx = smooth(seg(t, tk - .1, tk + .3))
    line(c, [(322, 792), (452, 578)], CORAL, 9, seg(t, th, th + .4), amp=1.2)
    line(c, [(758, 792), (628, 578)], TEAL, 9, seg(t, td, td + .4), amp=1.2)
    for x0, y0, x1, y1, col, ts in ((322, 792, 452, 578, CORAL, th + .4), (758, 792, 628, 578, TEAL, td + .4)):
        if t > ts:                                             # beyne giden haber
            u = ((t - ts) / .7) % 1
            c.drawCircle(lerp(x0, x1, u), lerp(y0, y1, u), 16, paint(col, fill=True, alpha=min(1, 4 * (1 - u))))
    bp = pop(t, a0 - .15, .3)
    if bp > 0:
        jx = 8 * math.sin(t * 31) * mx
        with xf(c, bx + jx, by, bp, 3 * math.sin(t * 23) * mx):
            cloud(c, bx + jx, by, 178, 102, fill=WASH_P)
            line(c, [(bx + jx - 96, by - 22), (bx + jx - 44, by - 50), (bx + jx, by - 18), (bx + jx + 46, by - 50), (bx + jx + 98, by - 22)], MUTE, 6, curve=True, amp=1)
            txt(c, 'BEYİN', bx + jx, by + 46, 44, INK)
    n1 = pop(t, a0, .3)
    if n1 > 0:                                                 # ic kulak: hareket var
        amp = 12 * smooth(seg(t, b0 - .1, b0 + .2)) * (1 - .6 * smooth(seg(t, b1, b1 + .4)))
        with xf(c, 250, ny, n1, amp * math.sin(t * 7)):
            circ(c, 250, ny, 125, color=CORAL, w=10, fill=WASH_P, n=16)
            snail(c, 250, ny - 22, .66)
            txt(c, 'İÇ KULAK', 250, ny + 92, 30, CORAL)
        if b0 - .05 < t:
            for k, sd in enumerate((-1, 1)):                   # sallanti cizgileri
                xx = 250 + sd * 150
                line(c, [(xx, ny - 60), (xx + sd * 16, ny), (xx, ny + 60)], CORAL, 7, alpha=.35 + .65 * abs(math.sin(t * 7 + k)), amp=.8, curve=True)
        hp = pop(t, th, .3)
        if hp > 0:
            with xf(c, 250, 1090, hp): txt(c, 'hareket var!', 250, 1106, 50, CORAL)
    n2 = pop(t, d0, .3)
    if n2 > 0:                                                 # goz: sabit ekran
        with xf(c, 830, ny, n2):
            circ(c, 830, ny, 125, color=TEAL, w=10, fill=WASH_T, n=16)
            eye(c, 796, ny - 22, .62); phone(c, 884, ny - 22, .66, 8)
            txt(c, 'GÖZ', 830, ny + 92, 30, TEAL)
        dp = pop(t, td, .3)
        if dp > 0:
            with xf(c, 830, 1090, dp): txt(c, 'duruyoruz!', 830, 1106, 50, TEAL)
    if mx > 0:
        qp = pop(t, tk, .3)
        qmark(c, 300, 500, 110, t, CORAL, sc=qp); qmark(c, 780, 500, 110, t + 1, CORAL, sc=qp)
        zp = pop(t, tk + .25, .3)
        if zp > 0:
            with xf(c, 540, 700, zp, -3):
                box(c, 400, 656, 680, 744, r=18, w=7, fill=YEL)
                txt(c, 'ÇATIŞMA', 540, 718, 46, INK)

def swheel(c, x, y, r, rot=0.0):
    """direksiyon"""
    with xf(c, x, y, 1, rot):
        circ(c, x, y, r, color=INK, w=18, n=16, amp=1)
        for a in (90, 200, 340):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            line(c, [(x + r * .2 * ca, y + r * .2 * sa), (x + r * .93 * ca, y + r * .93 * sa)], INK, 13, amp=.5)
        c.drawCircle(x, y, r * .24, paint(INK, fill=True))

def arc_arrow(c, x, y, r, a0, a1, color=MUTE, w=8):
    pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(a0, a1 + 1, 12)]
    line(c, pts, color, w, curve=True, amp=.6)
    ex, ey = pts[-1]; ta = math.radians(a1 + 90)
    for d in (2.5, -2.5):
        line(c, [(ex, ey), (ex + 30 * math.cos(ta + d), ey + 30 * math.sin(ta + d))], color, w, amp=.4)

def spinner(c, x, y, t, mood, tint=0.0, spin=1.0):
    """doner koltuktaki katilimci"""
    with xf(c, x, y, 1, t * 150 * spin):
        arc_arrow(c, x, y, 138, 10, 142); arc_arrow(c, x, y, 138, 190, 322)
    head(c, x, y, 80, mood, 1, tint)

def scene4(c, t):
    a0, a1 = L(9); b0, b1 = L(10); f0, f1 = L(11); d0, d1 = L(12); e0, e1 = L(13)
    A = 1 - seg(t, f0 - .3, f0 - .08)
    if A > 0:                                                  # sofor onceden biliyor
        with xf(c, 540, 700, 1, 0, A):
            hp = pop(t, a0, .35)
            if hp > 0:
                with xf(c, 540, 400, lerp(.7, 1, hp), 0, seg(t, a0, a0 + .15)): txt(c, 'Şoförü neden tutmuyor?', 540, 424, 68, INK)
            wp = pop(t, a0 + .3, .3)
            if wp > 0:
                with xf(c, 270, 740, wp): swheel(c, 270, 740, 150, 34 * math.sin(t * 2.4))
            t1 = cap_start(10, 'dönüşü', b0 + .5); t2 = cap_start(10, 'freni', b0 + 1.3); t3 = cap_start(10, 'önceden', b1 - 1.0)
            c1 = pop(t, t1, .3)
            if c1 > 0:
                with xf(c, 630, 690, c1):
                    box(c, 530, 580, 730, 800, r=24, w=8, fill=PAPER)
                    line(c, [(590, 730), (590, 668), (612, 640), (668, 640)], TEAL, 14, curve=True, amp=.8)
                    line(c, [(650, 618), (676, 640), (650, 662)], TEAL, 14, amp=.6)
                    txt(c, 'dönüş', 630, 782, 34, INK)
            c2 = pop(t, t2, .3)
            if c2 > 0:
                with xf(c, 870, 690, c2):
                    box(c, 770, 580, 970, 800, r=24, w=8, fill=PAPER)
                    oc = [(870 + 62 * math.cos(math.radians(22.5 + 45 * k)), 664 + 62 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
                    line(c, oc, INK, 7, closed=True, fill=CORAL, amp=.8)
                    txt(c, 'DUR', 870, 678, 38, PAPER)
                    txt(c, 'fren', 870, 782, 34, INK)
            c3 = pop(t, t3, .3)
            if c3 > 0:
                with xf(c, 540, 1010, c3, -2):
                    box(c, 250, 950, 830, 1070, r=26, w=8, fill=YEL)
                    txt(c, 'ÖNCEDEN BİLİYOR', 500, 1030, 52, INK)
                check(c, 772, 1010, .8, seg(t, t3 + .25, t3 + .5))
    if t > f0 - .1:                                            # deney
        al = seg(t, f0 - .05, f0 + .3)
        with xf(c, 540, 380, 1, 0, al):
            txt(c, 'Rolnick ve Lubow · 1991', 540, 376, 44, INK)
            txt(c, 'Ergonomics dergisi', 540, 426, 32, MUTE, 'med')
        res = smooth(seg(t, e0 + .2, e0 + .9))
        tz = cap_start(13, 'daha', e1 - 1.2)
        sp = pop(t, f0 + .3, .3)
        if sp > 0:
            spin = smooth(seg(t, d0 - .2, d0 + .4))
            with xf(c, 290, 760, sp): spinner(c, 290, 760, t, 'happy' if t > tz else 'ok', 0, spin)
            with xf(c, 790, 760, sp): spinner(c, 790, 760, t, 'sick' if res > .5 else 'ok', res, spin)
            if res > .05:
                spiral(c, 905, 630, 34 * res, t, CORAL, 6, res); spiral(c, 690, 640, 26 * res, t + 2, CORAL, 6, res)
        pp = pop(t, d0, .3)
        if pp > 0:
            with xf(c, 540, 520, pp): pill(c, '22 çift, aynı dönüş', 540, 520, 34, INK, PAPER)
            txt(c, 'dönüşü yöneten', 290, 970, 38, TEAL, alpha=seg(t, d0 + .2, d0 + .45))
            txt(c, 'sadece oturan', 790, 970, 38, MUTE, alpha=seg(t, d0 + .4, d0 + .65))
        if t > e0:                                             # bulanti: az / cok
            b1p = seg(t, tz, tz + .4); b2p = seg(t, e0 + .3, e0 + .9)
            line(c, [(170, 1060), (170 + 240, 1060)], 0xFFE4DAC6, 30, amp=.5); line(c, [(670, 1060), (670 + 240, 1060)], 0xFFE4DAC6, 30, amp=.5)
            if b1p > 0: line(c, [(170, 1060), (170 + 72 * b1p, 1060)], TEAL, 30, amp=.5)
            if b2p > 0: line(c, [(670, 1060), (670 + 216 * b2p, 1060)], CORAL, 30, amp=.5)
            txt(c, 'az bulantı', 290, 1146, 40, TEAL, alpha=seg(t, tz + .1, tz + .35))
            txt(c, 'çok bulantı', 790, 1146, 40, CORAL, alpha=seg(t, e0 + .5, e0 + .75))

def bottle(c, x, y, s=1.0):
    pts = [(x - 20 * s, y - 88 * s), (x - 20 * s, y - 50 * s), (x - 62 * s, y - 12 * s), (x - 62 * s, y + 88 * s), (x + 62 * s, y + 88 * s), (x + 62 * s, y - 12 * s), (x + 20 * s, y - 50 * s), (x + 20 * s, y - 88 * s)]
    line(c, pts, INK, 8 * s, closed=True, fill=PAPER, amp=1)
    line(c, [(x - 26 * s, y - 98 * s), (x + 26 * s, y - 98 * s)], INK, 18 * s, amp=.4)
    box(c, x - 44 * s, y + 2 * s, x + 44 * s, y + 68 * s, r=8 * s, w=5 * s, fill=YEL, amp=.8)
    cross(c, x, y + 35 * s, .5 * s, 1.0)

def scene5(c, t):
    a0, a1 = L(14); b0, b1 = L(15); d0, d1 = L(16); q0, q1 = L(17)
    A = 1 - seg(t, q0 - .3, q0 - .08)
    if A > 0:                                                  # bir aciklama: beyin zehirlenme saniyor
        with xf(c, 540, 700, 1, 0, A):
            hp = pop(t, a0, .35)
            if hp > 0:
                with xf(c, 540, 400, lerp(.7, 1, hp), 0, seg(t, a0, a0 + .15)): txt(c, 'Neden mide?', 540, 426, 80, INK)
            bp = pop(t, b0, .3)
            if bp > 0:
                with xf(c, 540, 536, bp): pill(c, 'BİR AÇIKLAMA', 540, 536, 36, TEAL, PAPER)
            np_ = pop(t, d0, .3)
            if np_ > 0:
                with xf(c, 290, 800, np_):
                    cloud(c, 290, 800, 172, 100, fill=WASH_P)
                    line(c, [(196, 778), (246, 750), (290, 782), (336, 750), (386, 778)], MUTE, 6, curve=True, amp=1)
                    txt(c, 'BEYİN', 290, 846, 44, INK)
                txt(c, 'çelişki var', 290, 976, 40, MUTE, alpha=seg(t, d0 + .2, d0 + .45))
            tz = cap_start(16, 'zehirlenme', d1 - 1.2)
            line(c, [(490, 800), (640, 800)], INK, 9, seg(t, tz - .15, tz + .15), amp=1.2)
            if t > tz + .15: line(c, [(612, 776), (642, 800), (612, 824)], INK, 9, amp=.6)
            else: St.n += 1
            zp = pop(t, tz, .3)
            if zp > 0:
                with xf(c, 800, 800, zp, 4 * math.sin(t * 5)): bottle(c, 800, 790, 1.05)
                txt(c, 'zehir mi?', 800, 976, 46, CORAL, alpha=seg(t, tz + .2, tz + .45))
    if t > q0 - .1:                                            # camdan uzaga bak
        pp = pop(t, q0, .3)
        if pp > 0:
            with xf(c, 540, 404, pp): pill(c, 'CAMDAN UZAĞA BAK', 540, 404, 40, TEAL, PAPER)
        wp = pop(t, q0 - .05, .35)
        if wp > 0:
            with xf(c, 540, 700, wp):
                rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(200, 490, 880, 920), 60, 60)
                c.save(); c.clipRRect(rr, True)
                c.drawRect(skia.Rect.MakeLTRB(200, 490, 880, 770), paint(WASH_T, fill=True))
                c.drawRect(skia.Rect.MakeLTRB(200, 770, 880, 920), paint(WASH_Y, fill=True))
                c.drawCircle(720, 610, 46, paint(YEL, fill=True))
                line(c, [(200, 770), (330, 720), (450, 762), (590, 700), (720, 758), (880, 730)], TEAL, 8, curve=True, amp=1)   # uzak tepeler (ufuk)
                line(c, [(200, 772), (880, 772)], INK, 6, amp=1)
                for k in range(4):                             # yakindaki direkler hizla geciyor
                    px = 880 - ((t * 620 + k * 215) % 860)
                    line(c, [(px, 640), (px, 920)], MUTE, 16, alpha=.55, amp=.5)
                c.restore()
                c.drawRRect(rr, paint(INK, 12))
        tg = cap_start(17, 'göz', q0 + 1.6); ty = cap_start(17, 'yeniden', q1 - 1.0)
        ep = pop(t, tg, .3)
        if ep > 0:
            with xf(c, 330, 1080, ep): eye(c, 330, 1070, .8)
            txt(c, 'göz', 330, 1176, 34, TEAL, alpha=seg(t, tg + .1, tg + .3))
            with xf(c, 650, 1080, pop(t, tg + .35, .3)): snail(c, 650, 1070, .62)
            txt(c, 'iç kulak', 650, 1176, 34, CORAL, alpha=seg(t, tg + .45, tg + .65))
        yp = pop(t, ty, .3)
        if yp > 0:
            with xf(c, 490, 1080, yp): txt(c, '=', 490, 1098, 90, INK)
            check(c, 850, 1075, 1.1, seg(t, ty + .2, ty + .5))

def scene6(c, t):
    a0, a1 = L(18); d0, d1 = L(19); e0, e1 = L(20)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_Y)
    ground(c, 50, 1030, gy)
    tf = cap_start(18, 'fenalaşırsın', a1 - 1.1)
    done = smooth(seg(t, d0 - .2, d0 + .05))
    sick = smooth(seg(t, tf - .1, tf + .5)) * (1 - done)
    car(c, 590, gy - 4, .76, t, 'happy' if done > .5 else 'ok', 'ok', sick, road=False)
    mp = pop(t, a0 + .5, .3) * (1 - smooth(seg(t, tf - .1, tf + .2)))
    if mp > 0.01:                                              # mesaj yaziyor
        with xf(c, 250, 700, mp):
            speech(c, 100, 640, 400, 760, (478, 902))
            for k in range(3): c.drawCircle(200 + k * 50, 700, 13, paint(MUTE if int(t * 5) % 3 != k else INK, fill=True))
    if sick > 0.02:
        for k, (dx, dy, r) in enumerate(((-128, -404, 40), (-52, -440, 30), (-196, -450, 26))):
            spiral(c, 590 + dx, gy + dy, r * sick, t + k, CORAL, 6, sick)
    bp = pop(t, d0 - .05, .3)
    if bp > 0 and t < e0 + 5:
        with xf(c, 500, 730, bp): bulb(c, 500, 730, .95, t=t)
    if d0 - .05 < t < e0 - .05:
        p = pop(t, d0 - .05, .35)
        with xf(c, 540, 430, lerp(.7, 1, p), 0, seg(t, d0 - .05, d0 + .1) * (1 - seg(t, e0 - .3, e0 - .08))):
            txt(c, 'Demek o yüzden!', 540, 452, 88, CORAL)
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
