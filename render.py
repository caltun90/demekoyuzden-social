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

TITLE = 'Soğuk içecek neden baş ağrıtır?'   # yatay formatta etiketin altinda gorunur
HOOK = 'Soğuk neden baş ağrıtır?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['BEYNİN', 'DONUYOR MU?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 1.3                          # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['donuyor'], 1: ['hızlıca'], 2: ['ağrı'], 3: ['dondurmada', 'buzlu'], 4: ['donmuyor.'], 5: ['damağında'], 6: ['büzüyor.'], 7: ['genişliyor.'], 8: ['ağrı'], 9: ['sinirle'], 10: ['karıştırıyor.'], 11: ['alnında'], 12: ['üç', 'kişiden', 'biri'], 13: ['zararsız,'], 14: ['yavaş'], 15: ['başın', 'ağrır'], 16: ['demek', 'o', 'yüzden!']}


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
WASH_C = 0xFFDDEFF7
ICE = 0xFFBFE3F2

def ybox(c, s, cx, cy, size=50, maxw=800, fill=YEL, fg=INK):
    """yaziya gore boyutlanan vurgu kutusu"""
    while tw(s, size) > maxw: size -= 2
    w = tw(s, size); h = size * 1.9
    box(c, cx - w / 2 - 34, cy - h / 2, cx + w / 2 + 34, cy + h / 2, r=28, w=8, fill=fill)
    txt(c, s, cx, cy + size * .36, size, fg)

def snow(c, x, y, r, t, col=TEAL, w=6, alpha=1.0):
    for i in range(3):
        a = i * math.pi / 3 + t * .8
        line(c, [(x - r * math.cos(a), y - r * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))], col, w, alpha=alpha, amp=.4)

def zig(c, x, y, s=1.0, col=CORAL, alpha=1.0):
    """agri simsegi"""
    pts = [(x - 14 * s, y - 50 * s), (x + 18 * s, y - 50 * s), (x + 4 * s, y - 8 * s), (x + 26 * s, y - 8 * s), (x - 16 * s, y + 54 * s), (x - 4 * s, y + 8 * s), (x - 26 * s, y + 8 * s)]
    line(c, pts, INK, max(4, 6 * s), closed=True, fill=col, alpha=alpha, amp=.5)

def glass(c, x, y, s=1.0, straw=True):
    """buzlu bardak; (x, y) tabanin ortasi"""
    w0, w1, h = 62 * s, 82 * s, 210 * s
    line(c, [(x - w1, y - h), (x + w1, y - h), (x + w0, y), (x - w0, y)], INK, max(5, 8 * s), closed=True, fill=ICE, amp=1)
    for dx, dy, rot in ((-26, -150, 12), (22, -106, -15), (-12, -56, 8)):
        with xf(c, x + dx * s, y + dy * s, 1, rot):
            box(c, x + dx * s - 24 * s, y + dy * s - 24 * s, x + dx * s + 24 * s, y + dy * s + 24 * s, r=7 * s, w=max(3.5, 5 * s), fill=PAPER, amp=.6)
    if straw: line(c, [(x + 20 * s, y - 30 * s), (x + 60 * s, y - h - 70 * s)], CORAL, max(6, 10 * s), amp=.5)

def cone(c, x, y, s=1.0):
    """kulahta dondurma; (x, y) topun ortasi"""
    line(c, [(x - 56 * s, y + 30 * s), (x + 56 * s, y + 30 * s), (x, y + 190 * s)], INK, max(5, 7 * s), closed=True, fill=YEL, amp=.8)
    circ(c, x, y, 66 * s, color=INK, w=max(5, 7 * s), fill=WASH_P, amp=1)

def brain(c, x, y, rx, ry, fill=WASH_P):
    cloud(c, x, y, rx, ry, fill=fill, w=8)
    line(c, [(x + 6, y - ry * .86), (x - rx * .12, y - ry * .3), (x + rx * .1, y + ry * .15), (x - rx * .04, y + ry * .82)], INK, 6, curve=True, amp=1)
    for sd in (-1, 1):
        line(c, [(x + sd * rx * .76, y - ry * .18), (x + sd * rx * .46, y - ry * .38), (x + sd * rx * .34, y + ry * .02)], MUTE, 6, curve=True, amp=.8)
        line(c, [(x + sd * rx * .72, y + ry * .36), (x + sd * rx * .46, y + ry * .5), (x + sd * rx * .3, y + ry * .4)], MUTE, 6, curve=True, amp=.8)

def phead(c, cx, cy, r, bfill=WASH_P, wob=0.0):
    """yandan bas kesiti (saga bakar): beyin, agiz boslugu, damak"""
    line(c, [(cx - r * .32, cy + r * .9), (cx - r * .36, cy + r * 1.4)], INK, 9, amp=1)
    line(c, [(cx + r * .22, cy + r * .95), (cx + r * .26, cy + r * 1.4)], INK, 9, amp=1)
    circ(c, cx, cy, r, color=INK, w=10, fill=PAPER, amp=1.4, n=18)
    line(c, [(cx + r * .985, cy - r * .08), (cx + r * 1.15, cy + r * .1), (cx + r * .97, cy + r * .17)], INK, 10, fill=PAPER, amp=.6)
    c.drawCircle(cx + r * .62, cy - r * .2, r * .045, paint(INK, fill=True))
    x0, x1, y0, y1 = cx + r * .1, cx + r * .84, cy + r * .34, cy + r * .56
    wash(c, x0, y0, x1, y1, WASH_Y, 1, 14)
    line(c, [(x0, y1), (x1, y1)], INK, 7, amp=.8)
    line(c, [(x0, y1), (x0 - 5, (y0 + y1) / 2), (x0, y0)], INK, 7, curve=True, amp=.5)
    line(c, [(x0, y0), ((x0 + x1) / 2, y0 - r * .05), (x1, y0)], CORAL, 15, curve=True, amp=.6)
    bx, by = cx - r * .14, cy - r * .36
    with xf(c, bx, by, 1 + wob): brain(c, bx, by, r * .56, r * .4, bfill)
    a = math.radians(36)
    return dict(pal=((x0 + x1) / 2 + r * .08, y0), brain=(bx, by), fore=(cx + r * math.cos(a), cy - r * math.sin(a)), mouth=(x1, (y0 + y1) / 2))

def along(pts, u):
    d = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    v = clamp(u) * sum(d)
    for i, di in enumerate(d):
        if v <= di: return (lerp(pts[i][0], pts[i + 1][0], v / di), lerp(pts[i][1], pts[i + 1][1], v / di))
        v -= di
    return pts[-1]

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1); d0, d1 = L(2); e0, e1 = L(3)
    thz = cap_start(1, 'hızlıca', b0 + 1.0); tbi = cap_start(2, 'bıçak', d0 + .8); tag_ = cap_start(2, 'ağrı', d0 + 1.5)
    tbu = cap_start(3, 'buzlu', e0 + 1.1)
    gy = 1130
    wash(c, 60, 340, 1020, gy, WASH_Y)
    ground(c, 60, 1020, gy)
    x = 330
    if t < b0 - .1:
        me = fig(c, x, gy, 1.0, 0, dict(FRONT, aR=40, eR=150, aL=40, eL=150), 'oh')
        hx, hy = me['head']
        with xf(c, hx, hy, pop(t, a0 + .05, .25), -6 + 2 * math.sin(t * 7)):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(hx - 92, hy - 92, hx + 92, hy + 92), 18, 18), paint(ICE, fill=True, alpha=.72))
            box(c, hx - 92, hy - 92, hx + 92, hy + 92, r=18, w=9, amp=1.2)
            line(c, [(hx - 66, hy - 30), (hx - 30, hy - 68)], PAPER, 9, amp=.5)
            line(c, [(hx - 62, hy + 6), (hx - 6, hy - 60)], PAPER, 7, amp=.5)
        for k, (sx, sy, sr) in enumerate(((150, 520, 34), (520, 470, 28), (180, 880, 26), (560, 620, 22))):
            if t > a0 + .1 + .08 * k:
                with xf(c, sx, sy, pop(t, a0 + .1 + .08 * k, .25)): snow(c, sx, sy + 14 * math.sin(t * 3 + k), sr, t + k)
        if t > a0 + .3: qmark(c, 780, 900, 340, t, CORAL, 1.0, pop(t, a0 + .3, .3))
    elif t < d0:
        sip = .5 + .5 * math.sin((t - b0) * 9)
        me = fig(c, x, gy, 1.0, 0, dict(FRONT, aR=30, eR=140 + 8 * sip, aL=10, eL=6), 'smile', hold=lambda p: glass(c, p[0] + 10, p[1] + 46, .42))
        with xf(c, 730, 560, pop(t, b0 - .05, .3), -2): pill(c, 'buz gibi', 730, 560, 54, TEAL, PAPER)
        for k, (sx, sy, sr) in enumerate(((560, 520, 22), (910, 510, 26), (880, 640, 20))):
            snow(c, sx, sy + 10 * math.sin(t * 3 + k), sr, t + k)
        if t > thz:
            with xf(c, 730, 800, pop(t, thz, .3), 2): ybox(c, 'hızlıca', 730, 800, 70)
            for j in range(3): line(c, [(560 + 12 * j, 760 + 40 * j), (510 + 12 * j - 14 * ((j + int(t * 9)) % 2), 760 + 40 * j)], CORAL, 8, amp=.4)
    else:
        calm = t > e0 - .1
        hurt = t > tbi - .1 and not calm
        pose = dict(FRONT, aR=40, eR=150, aL=40, eL=150) if hurt else None
        me = fig(c, x, gy - (8 * abs(math.sin(t * 14)) if hurt and t < tbi + .8 else 0), 1.0, 0, pose, 'oh' if hurt else ('sad' if calm else 'confused'))
        hx, hy = me['head']
        if hurt:
            with xf(c, hx + 4, hy - 126, pop(t, tbi - .1, .22), 8 * math.sin(t * 10)): zig(c, hx + 4, hy - 126, 1.35)
            burst(c, hx, hy, 76, 104, 9, CORAL, 7, alpha=.5 + .5 * abs(math.sin(t * 8)))
        if tag_ < t < e0 - .1:
            with xf(c, 740, 720, pop(t, tag_, .25), -6 + 3 * math.sin(t * 9)): txt(c, 'AH!', 740, 790, 200, CORAL)
        if calm:
            for k, (cx_, tt, lab) in enumerate(((640, e0 - .05, 'dondurma'), (890, tbu, 'buzlu su'))):
                if t <= tt: continue
                with xf(c, cx_, 640, pop(t, tt, .35), (-3, 3)[k]):
                    box(c, cx_ - 105, 500, cx_ + 105, 780, r=30, w=8, fill=PAPER)
                    if k == 0: cone(c, cx_, 590, .7)
                    else: glass(c, cx_, 752, .78)
                with xf(c, cx_, 836, pop(t, tt + .1, .3)): pill(c, lab, cx_, 836, 36, INK)

def scene2(c, t):
    a0, a1 = L(4); p0, p1 = L(5)
    tbd = cap_start(4, 'beyin', a0 + .4); tam = cap_start(4, 'ama', a0 + 1.9); tdm = cap_start(5, 'damağında', p0 + .7)
    wash(c, 60, 340, 1020, 1120, WASH_T)
    cx, cy, r = 500, 790, 220
    thaw = smooth(seg(t, tam, tam + .3))
    with xf(c, cx, cy, pop(t, a0 - .2, .3)):
        H = phead(c, cx, cy, r, ICE if thaw < .5 else WASH_P)
    bx, by = H['brain']
    if t > a0 and thaw < 1: snow(c, bx, by, 46, t, TEAL, 8, 1 - thaw)
    if t > tbd:
        with xf(c, 540, 410, pop(t, tbd, .3), -2): ybox(c, 'beyin donması', 540, 410, 58)
    if t > tam:
        with xf(c, 540, 505, pop(t, tam + .15, .3), 1.5): pill(c, 'ama beyin donmuyor', 540, 505, 40, TEAL, PAPER)
    if t > tdm:
        px, py = H['pal']
        pu = 1 + .12 * math.sin(t * 9)
        with xf(c, px, py, pu * pop(t, tdm, .25)): circ(c, px, py, 96, 54, color=CORAL, w=9, amp=1.2)
        with xf(c, 890, 866, pop(t, tdm + .1, .3)): pill(c, 'damak', 890, 866, 48, CORAL, PAPER)
        arrow(c, (790, 866), (716, 866), CORAL, 8, seg(t, tdm + .2, tdm + .45))
        with xf(c, 540, 1192, pop(t, tdm + .3, .35), -1.5): ybox(c, 'her şey damakta başlıyor', 540, 1192, 50, 780)

def scene3(c, t):
    a0, a1 = L(6); g0, g1 = L(7); s0, s1 = L(8)
    tso = cap_start(6, 'soğuk', a0 + 1.6); tda = cap_start(6, 'damarları', a0 + 2.6); tbz = cap_start(6, 'büzüyor', a1 - .7)
    tgn = cap_start(7, 'genişliyor', g1 - .9); tsi = cap_start(8, 'sinir', s0 + .5); tag_ = cap_start(8, 'ağrı', s1 - 1.3)
    wash(c, 60, 340, 1020, 1060, WASH_P)
    with xf(c, 540, 405, pop(t, a0, .3)): pill(c, 'damağın içi', 540, 405, 44, INK)
    wv = lerp(46, 16, smooth(seg(t, tbz, tbz + .3)))
    wv = lerp(wv, 88 + 5 * math.sin(t * 9), smooth(seg(t, tgn, tgn + .35)))
    pts = [(40, 592), (300, 578), (540, 602), (780, 582), (1040, 592)]
    c.save(); c.clipRect(skia.Rect.MakeLTRB(60, 340, 1020, 1060))
    line(c, pts, INK, wv + 16, amp=0, curve=True)
    line(c, pts, CORAL, wv, amp=0, curve=True)
    for k in range(5):
        ph = (t * .35 + k / 5) % 1
        c.drawCircle(lerp(60, 1020, ph), 592 + 6 * math.sin(k * 2 + t), max(3, wv * .16), paint(PAPER, fill=True, alpha=.7))
    c.restore()
    if t > tda - .3:
        with xf(c, 180, 492, pop(t, tda - .3, .3), -3): pill(c, 'damar', 180, 492, 42, CORAL, PAPER)
    active = t > tag_
    for k, x in enumerate((300, 540, 780)):
        col = CORAL if active else TEAL
        line(c, [(x, 770), (x, 700)], col, 9, amp=.6)
        line(c, [(x, 700), (x - 24, 664)], col, 9, amp=.6); line(c, [(x, 700), (x + 24, 664)], col, 9, amp=.6)
        if t > tsi: c.drawCircle(x, 700, 13 + 3 * math.sin(t * 10 + k), paint(YEL, fill=True)); c.drawCircle(x, 700, 13, paint(INK, 4))
        if active: burst(c, x, 690, 40, 58 + 6 * math.sin(t * 12 + k), 7, CORAL, 6)
    line(c, [(60, 776), (1020, 776)], INK, 8, amp=1.2)
    cold = smooth(seg(t, tso - .1, tso + .4))
    if cold > 0:
        x0 = lerp(1020, 60, cold)
        c.drawRect(skia.Rect.MakeLTRB(x0, 782, 1020, 960), paint(ICE, fill=True))
        for k in range(5):
            sx = 1020 - ((t * 70 + k * 200) % 960)
            if sx > x0 + 30: snow(c, sx, 830 + 70 * (k % 2), 24, t + k, TEAL, 6)
        if cold > .9: txt(c, 'soğuk içecek', 540, 1020, 44, TEAL)
    if tbz < t < tgn:
        for x in (420, 660):
            arrow(c, (x, 500), (x, 556), TEAL, 8, seg(t, tbz, tbz + .25)); arrow(c, (x, 690), (x, 632), TEAL, 8, seg(t, tbz, tbz + .25))
    lab, tl = None, 0
    if t > tbz: lab, tl = 'damarlar büzülüyor', tbz
    if t > tgn: lab, tl = 'sonra hızla genişliyor', tgn
    if t > tsi: lab, tl = 'sinir uçları uyarılıyor', tsi
    if t > tag_: lab, tl = 'sinir uçları: ağrı!', tag_
    if lab:
        with xf(c, 540, 1165, pop(t, tl, .3), -1.5): ybox(c, lab, 540, 1165, 52, 780)

def scene4(c, t):
    a0, a1 = L(9); k0, k1 = L(10); h0, h1 = L(11)
    tyu = cap_start(9, 'yüzünün', a0 + 1.2); tsn = cap_start(9, 'sinirle', a1 - 1.0)
    tka = cap_start(10, 'karıştırıyor', k1 - .9); tal = cap_start(11, 'alnında', h1 - 1.3)
    wash(c, 60, 340, 1020, 1120, WASH_T)
    cx, cy, r = 500, 790, 220
    wob = .05 * math.sin(t * 22) * (1 - seg(t, tka, tka + .8)) if t > tka else 0.0
    with xf(c, cx, cy, pop(t, a0 - .2, .3)): H = phead(c, cx, cy, r, WASH_P, wob)
    P = H['pal']; F = H['fore']; B = (H['brain'][0] + 30, H['brain'][1] + 40); J = (cx + r * .3, cy + r * .02)
    F2 = (F[0] - 16, F[1] + 12)
    line(c, [P, J, B], TEAL, 11, seg(t, a0, a0 + .5), amp=.6)
    line(c, [F2, J], TEAL, 11, seg(t, tyu, tyu + .35), amp=.6)
    if t > a0 + .3:
        for k in range(3):
            ph = ((t - a0) * .9 + k / 3) % 1
            q = along([P, J, B], ph)
            c.drawCircle(q[0], q[1], 12, paint(YEL, fill=True)); c.drawCircle(q[0], q[1], 12, paint(INK, 4))
    with xf(c, 890, 866, pop(t, a0, .3)): pill(c, 'damak', 890, 866, 44, CORAL, PAPER)
    if t > tyu:
        with xf(c, 880, 640, pop(t, tyu, .3)): pill(c, 'alın', 880, 640, 44, INK)
        dashes(c, (818, 646), (F[0] + 16, F[1] + 4), 4, MUTE, 6, seg(t, tyu, tyu + .2))
    if k0 < t:
        bx, by = H['brain']
        if t > tka: qmark(c, bx, by - 130, 130, t, CORAL, 1.0, pop(t, tka, .3))
    if t > h0:
        cross(c, 890, 866, 1.5, seg(t, h0 + .2, h0 + .5))
    if t > tal:
        burst(c, F[0], F[1], 30, 60 + 8 * math.sin(t * 11), 9, CORAL, 7)
        with xf(c, F[0] + 60, F[1] - 96, pop(t, tal, .22), 8 * math.sin(t * 10)): zig(c, F[0] + 60, F[1] - 96, 1.2)
    lab, tl = None, 0
    if t > tsn: lab, tl = 'aynı sinir: damak ve yüz', tsn
    if t > tka: lab, tl = 'beyin yeri karıştırıyor', tka
    if t > tal: lab, tl = 'ağrı alında hissediliyor', tal
    if lab:
        with xf(c, 540, 1192, pop(t, tl, .3), -1.5): ybox(c, lab, 540, 1192, 50, 780)

def scene5(c, t):
    a0, a1 = L(12); z0, z1 = L(13); y0, y1 = L(14)
    tuc = cap_start(12, 'üç', a0 + .5); tbi = cap_start(12, 'biri', a0 + 1.2)
    tco = cap_start(13, 'çoğu', z0 + .8)
    gy = 800
    wash(c, 60, 340, 1020, gy, WASH_Y)
    ground(c, 60, 1020, gy)
    for k, x in enumerate((190, 390, 590)):
        tk = tuc - .2 + .12 * k
        if t <= tk: continue
        hit = k == 2 and t > tbi
        if hit: wash(c, x - 92, gy - 300, x + 92, gy - 6, YEL, seg(t, tbi, tbi + .15), 36)
        with xf(c, x, gy, pop(t, tk, .3)):
            me = fig(c, x, gy, .62, 0, dict(FRONT, aR=40, eR=150, aL=40, eL=150) if hit else None, 'oh' if hit else 'smile', color=INK if (k == 2 or t < tbi) else MUTE)
        if hit:
            with xf(c, x, gy - 372, pop(t, tbi, .22), 8 * math.sin(t * 10)): zig(c, x, gy - 372, .8)
    if t > tbi:
        with xf(c, 850, 640, pop(t, tbi, .3), -3): txt(c, "3'te 1", 850, 650, 100, CORAL)
        with xf(c, 850, 724, pop(t, tbi + .12, .3)): pill(c, 'bunu yaşıyor', 850, 724, 34, INK)
    if t > z0 - .05:
        with xf(c, 290, 950, pop(t, z0 - .05, .35), -2): ybox(c, 'zararsız', 290, 950, 60, 400, WASH_T)
        check(c, 290, 1060, 1.3, seg(t, z0 + .2, z0 + .5))
    if t > tco:
        with xf(c, 740, 950, pop(t, tco, .3)):
            circ(c, 740, 950, 84, color=INK, w=9, fill=PAPER, amp=1)
            line(c, [(740, 866), (740, 846)], INK, 9, amp=.4); line(c, [(722, 842), (758, 842)], INK, 9, amp=.4)
            a = -math.pi / 2 + 2 * math.pi * .8 * smooth(seg(t, tco, z1))
            p = skia.Path(); p.moveTo(740, 950); p.arcTo(skia.Rect.MakeLTRB(740 - 70, 950 - 70, 740 + 70, 950 + 70), -90, math.degrees(a + math.pi / 2), False); p.close()
            c.drawPath(p, paint(TEAL, fill=True, alpha=.45))
            line(c, [(740, 950), (740 + 62 * math.cos(a), 950 + 62 * math.sin(a))], CORAL, 9, amp=.4)
        with xf(c, 740, 1080, pop(t, tco + .15, .3)): pill(c, '1 dakikadan kısa', 740, 1080, 34, INK)
    if t > y0:
        with xf(c, 540, 1196, pop(t, y0, .35), -1.2): ybox(c, 'yavaş içince pek olmuyor', 540, 1196, 48, 780)

def scene6(c, t):
    a0, a1 = L(15); d0, d1 = L(16); e0, e1 = L(17)
    tba = cap_start(15, 'başın', a0 + 1.4)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_T)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    aha = t > d0 - .1
    hurt = t > tba and not aha
    if not aha and not hurt:
        me = fig(c, 540, gy, .95, 0, dict(FRONT, aR=30, eR=144 + 6 * math.sin(t * 9), aL=10, eL=6), 'smile', hold=lambda p: glass(c, p[0] + 10, p[1] + 44, .4))
    else:
        pose = dict(FRONT, aR=40, eR=150, aL=40, eL=150) if hurt else dict(FRONT, aR=20, eR=150, aL=10, eL=6)
        pose = mix(pose, dict(FRONT, aR=10, eR=6, aL=148, eL=160 + 26 * math.sin(t * 9)), wv)
        me = fig(c, 540, gy, .95, 0, pose, 'oh' if hurt else 'happy')
        glass(c, 800, gy - 6, .62)
    hx, hy = me['top']
    if not aha:
        for k, (sx, sy) in enumerate(((190, 700), (880, 680), (220, 980))):
            snow(c, sx, sy + 12 * math.sin(t * 3 + k), 28, t + k)
    if hurt:
        with xf(c, hx + 150, hy - 20, pop(t, tba, .22), 8 * math.sin(t * 10)): zig(c, hx + 150, hy - 20, 1.2)
        burst(c, me['head'][0], me['head'][1], 72, 98, 9, CORAL, 7, alpha=.5 + .5 * abs(math.sin(t * 8)))
        qmark(c, hx - 150, hy + 30, 150, t, CORAL, 1.0, pop(t, tba + .1, .3))
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
