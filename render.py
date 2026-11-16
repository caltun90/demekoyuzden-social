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

TITLE = 'Kulak Kurdu'   # yatay formatta etiketin altinda gorunur
HOOK = 'Şarkı neden dile dolanır?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['ŞARKI', 'NEDEN DİLE', 'DOLANIR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 4.8                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['şarkı'], 1: ['hâlâ'], 2: ['kulak', 'kurdu.'], 3: ['binden'], 4: ['onda', 'dokuzu'], 5: ['takılıyor?'], 6: ["2017'de"],
      7: ['üç', 'bin'], 8: ['hızlı', 'basit.'], 9: ['beklenmedik', 'sıçrama'], 10: ['kısa', 'parçası.'], 11: ['iç', 'sesiyle'],
      12: ['sakız', 'üçte', 'bir'], 13: ['meşgul'], 14: ['bütün', 'gün'], 15: ['demek', 'o', 'yüzden!']}


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

def lerpc(a, b, u):
    u = clamp(u); out = 0
    for sh in (24, 16, 8, 0):
        out |= int(lerp((a >> sh) & 255, (b >> sh) & 255, u)) << sh
    return out

def note(c, x, y, s=1.0, col=INK, alpha=1.0, rot=0.0):
    if alpha <= 0.01: return
    with xf(c, x, y, s, rot, alpha):
        c.save(); c.translate(x, y); c.rotate(-20)
        c.drawOval(skia.Rect.MakeLTRB(-17, -12, 17, 12), paint(col, fill=True)); c.restore()
        line(c, [(x + 14, y - 2), (x + 14, y - 58)], col, 7, amp=.4)
        line(c, [(x + 14, y - 58), (x + 30, y - 46), (x + 36, y - 30)], col, 7, curve=True, amp=.4)

def radio(c, x, y, s=1.0, t=0.0, on=1.0):
    line(c, [(x + 50 * s, y - 70 * s), (x + 110 * s, y - 160 * s)], INK, 7 * s, amp=.5)
    box(c, x - 120 * s, y - 72 * s, x + 120 * s, y + 72 * s, r=22 * s, w=8 * s, fill=CORAL)
    pulse = 1 + .06 * math.sin(t * 16) * on
    circ(c, x - 50 * s, y, 44 * s * pulse, color=INK, w=6 * s, fill=PAPER, n=12, amp=.6)
    c.drawCircle(x - 50 * s, y, 16 * s * pulse, paint(INK, fill=True))
    for k in range(3): line(c, [(x + 30 * s, y - 30 * s + k * 26 * s), (x + 92 * s, y - 30 * s + k * 26 * s)], INK, 6 * s, amp=.4)

def pawn(c, x, y, col=PAPER, s=1.0):
    """kucuk insan simgesi (ayak tabani y)"""
    line(c, [(x - 34 * s, y), (x - 30 * s, y - 50 * s), (x - 16 * s, y - 66 * s), (x + 16 * s, y - 66 * s), (x + 30 * s, y - 50 * s), (x + 34 * s, y)],
         INK, 6 * s, closed=True, fill=col, curve=True, amp=.6)
    circ(c, x, y - 96 * s, 25 * s, color=INK, w=6 * s, fill=col, n=10, amp=.6)

def worm(c, x, y, s=1.0, t=0.0, n=6):
    pts = [(x + k * 30 * s, y - k * 14 * s + 10 * s * math.sin(t * 6 - k * .9)) for k in range(n)]
    for k, (px, py) in enumerate(pts):
        circ(c, px, py, (24 - k * .6) * s, color=INK, w=5 * s, fill=CORAL if k % 2 == 0 else 0xFFF39A80, n=10, amp=.4)
    hx, hy = pts[-1]
    circ(c, hx + 20 * s, hy - 10 * s, 32 * s, color=INK, w=6 * s, fill=CORAL, n=12, amp=.5)
    c.drawCircle(hx + 14 * s, hy - 18 * s, 5 * s, paint(INK, fill=True)); c.drawCircle(hx + 32 * s, hy - 18 * s, 5 * s, paint(INK, fill=True))
    line(c, [(hx + 10 * s, hy - 2 * s), (hx + 23 * s, hy + 6 * s), (hx + 36 * s, hy - 2 * s)], INK, 4 * s, curve=True, amp=.3)
    return hx + 20 * s, hy - 10 * s

def melody(c, x0, y0, steps, dx=70, col=INK, prog=1.0, hi=None):
    """basit ezgi: nota basliklari ve onlari baglayan cizgi; hi = vurgulanan adim (sicrama)"""
    pts = [(x0 + i * dx, y0 - v) for i, v in enumerate(steps)]
    k = max(1, int(len(pts) * prog + .999))
    if k > 1: line(c, pts[:k], MUTE, 5, amp=.3)
    for i, (px, py) in enumerate(pts[:k]):
        cl = CORAL if hi is not None and i in hi else col
        c.drawCircle(px, py, 15, paint(cl, fill=True))
    return pts

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1)
    gy = 1200
    eve = smooth(seg(t, b0 - .1, b0 + .7))
    wash(c, 60, 340, 1020, gy + 30, lerpc(WASH_Y, 0xFFDCE0EC, eve))
    sky = lerpc(0xFFBFE6F0, 0xFF34405E, eve)                                           # pencere
    box(c, 620, 380, 960, 640, r=16, w=9, fill=sky)
    c.save(); c.clipRect(skia.Rect.MakeLTRB(626, 386, 954, 634))
    c.drawCircle(780, lerp(480, 700, eve), 46, paint(YEL, fill=True))
    c.drawCircle(860, lerp(720, 470, eve), 36, paint(0xFFF4EBD0, fill=True)); c.drawCircle(878, lerp(708, 458, eve), 32, paint(sky, fill=True))
    for k in range(4): c.drawCircle(680 + k * 70, 420 + (k % 2) * 40, 4, paint(PAPER, fill=True, alpha=eve))
    c.restore()
    line(c, [(790, 380), (790, 640)], INK, 7, amp=.5); line(c, [(620, 510), (960, 510)], INK, 7, amp=.5)
    box(c, 90, 960, 470, 990, r=8, w=8, fill=PAPER)                                        # masa
    line(c, [(130, 990), (130, gy)], INK, 9); line(c, [(430, 990), (430, gy)], INK, 9)
    ground(c, 60, 1020, gy)
    on = 1 - smooth(seg(t, b0 - .2, b0 + .2))
    radio(c, 280, 884, .9, t, on)
    me = fig(c, 720, gy, 1.0, -1, dict(STAND, tilt=lerp(0, -6, eve)), 'smile' if eve < .5 else 'flat')
    hx, hy = me['head']
    if on > 0.01:                                                                         # radyodan gelen notalar
        for k in range(4):
            ph = (t * .6 + k / 4) % 1
            note(c, lerp(330, hx - 30, ph), lerp(780, hy - 40, ph) - 60 * math.sin(ph * math.pi), .8, CORAL if k % 2 else INK, on * min(1, 4 * ph) * min(1, 4 * (1 - ph)))
    if t > b0 - .2:                                                                       # kafanin icinde donuyor
        a = seg(t, b0, b0 + .4)
        for k in range(3):
            ang = t * 2.2 + k * 2 * math.pi / 3
            note(c, hx + 120 * math.cos(ang), hy - 30 + 50 * math.sin(ang), .75, CORAL if k == 0 else INK, a)
        line(c, [(hx + 120 * math.cos(t * 2.2 + i * .2), hy - 30 + 50 * math.sin(t * 2.2 + i * .2)) for i in range(-14, -2)], MUTE, 5, alpha=a * .7, curve=True, amp=.3)

def scene2(c, t):
    a0, a1 = L(2); f0, f1 = L(3); n0, n1 = L(4)
    tk = cap_start(2, 'kulak', a0 + 1.0)
    hd = 1 - smooth(seg(t, f0 - .3, f0 + .1))
    if hd > 0.01:
        with xf(c, 540, 760, 1, 0, hd):
            p = pop(t, a0 - .1, .35)
            with xf(c, 450, 790, p):
                circ(c, 450, 790, 190, color=INK, w=10, fill=PAPER, n=16)
                line(c, [(500, 700), (560, 690), (585, 745), (560, 820), (520, 860)], INK, 9, curve=True, amp=.6)   # kulak
                c.drawCircle(545, 765, 14, paint(INK, fill=True))
                c.drawCircle(370, 760, 8, paint(INK, fill=True))
            wp = pop(t, tk, .4)
            if wp > 0:
                with xf(c, 560, 760, wp):
                    wx, wy = worm(c, 560, 770, 1.0, t)
                    note(c, wx + 70, wy - 70 + 8 * math.sin(t * 5), .9, CORAL)
                    note(c, wx - 40, wy - 110 + 8 * math.sin(t * 5 + 1), .7, INK)
            if t > tk - .05:
                pp = pop(t, tk - .05, .35)
                with xf(c, 540, 420, lerp(.7, 1, pp), 0, seg(t, tk - .05, tk + .1)):
                    txt(c, 'KULAK KURDU', 540, 452, 100, CORAL)
    if t > f0 - .2:
        a = seg(t, f0 - .2, f0 + .2)
        with xf(c, 540, 420, 1, 0, a):
            txt(c, 'Finlandiya · Liikkanen, 2012', 540, 410, 42, INK)
            pill(c, '12.519 kişi', 540, 500, 38, INK, PAPER)
        tn = cap_start(4, 'dokuzu', n0 + .4)
        for k in range(10):
            x, y = 220 + (k % 5) * 160, 760 + (k // 5) * 200
            p = pop(t, f0 + .3 + k * .07, .25)
            if p <= 0: continue
            hit = k != 6 and t > tn + k * .08
            with xf(c, x, y, p): pawn(c, x, y, CORAL if hit else PAPER, 1.0)
            if hit: note(c, x + 26, y - 150 + 6 * math.sin(t * 6 + k), .55, INK, seg(t, tn + k * .08, tn + k * .08 + .2))
        if t > tn + .3:
            with xf(c, 540, 1130, pop(t, tn + .3, .35), -2):
                box(c, 240, 1080, 840, 1186, r=24, w=8, fill=YEL)
                txt(c, '%89 her hafta', 540, 1156, 60, INK)

def scene3(c, t):
    q0, q1 = L(5); y0_, y1_ = L(6); l0, l1 = L(7); h0, h1 = L(8); s0, s1 = L(9)
    cards = 1 - smooth(seg(t, y0_ - .2, y0_ + .1))
    if cards > 0.01:
        for k, x in enumerate((250, 540, 830)):
            p = pop(t, q0 + k * .15, .3) * cards
            if p <= 0.01: continue
            with xf(c, x, 760, p, (k - 1) * 5):
                box(c, x - 110, 640, x + 110, 880, r=20, w=8, fill=PAPER)
                note(c, x - 6, 790, 1.4, CORAL if k == 1 else INK)
        qmark(c, 540, 560, 150, t, CORAL, cards, pop(t, cap_start(5, 'takılıyor', q0 + .8), .3))
    if t > y0_ - .1:
        with xf(c, 540, 400, 1, 0, seg(t, y0_ - .1, y0_ + .3)):
            txt(c, 'Goldsmiths, Londra Üniversitesi · 2017', 540, 396, 40, INK)
            txt(c, 'Jakubowski ve ark.', 540, 442, 30, MUTE, 'med')
        p = pop(t, cap_start(7, 'bin', l0 + .8), .3)
        if p > 0:
            with xf(c, 540, 520, p): pill(c, '3.000 kişi', 540, 520, 38, INK, PAPER)
    th = cap_start(8, 'hızlı', h0 + 1.0); tb = cap_start(8, 'ezgisi', h1 - 1.2)
    p = pop(t, th - .1, .3)
    if p > 0:                                                                   # hizli
        with xf(c, 290, 760, p):
            box(c, 120, 630, 460, 900, r=22, w=8, fill=WASH_T)
            for k in range(3): line(c, [(160, 720 + k * 34), (230 + k * 20, 720 + k * 34)], MUTE, 6, amp=.4)
            note(c, 330 + 10 * math.sin(t * 14), 770, 1.2, INK)
            txt(c, 'hızlı', 290, 870, 42, TEAL)
    p = pop(t, tb - .1, .3)
    if p > 0:                                                                   # basit ezgi
        with xf(c, 790, 760, p):
            box(c, 620, 630, 960, 900, r=22, w=8, fill=WASH_T)
            melody(c, 660, 790, [0, 30, 60, 30, 0], 64, INK, seg(t, tb, tb + .6))
            txt(c, 'basit ezgi', 790, 870, 42, TEAL)
    ts = cap_start(9, 'beklenmedik', s0 + .5)
    p = pop(t, ts - .1, .3)
    if p > 0:                                                                   # surpriz sicrama
        with xf(c, 540, 1090, p):
            box(c, 120, 960, 960, 1220, r=22, w=8, fill=WASH_P)
            pts = melody(c, 190, 1120, [0, 20, 0, 20, 140, 110, 110, 110], 92, INK, seg(t, ts, ts + 1.4), hi={4})
            if t > ts + .9:
                x3, y3 = pts[3]; x4, y4 = pts[4]
                line(c, [(x3 + 10, y3 - 30), (x3 + 30, y4 - 10), (x4 - 22, y4 - 20)], CORAL, 7, seg(t, ts + .9, ts + 1.2), curve=True, amp=.3)
            txt(c, 'sürpriz sıçrama', 330, 1196, 38, CORAL, alpha=seg(t, ts + 1.0, ts + 1.3))
            if t > cap_start(9, 'tekrar', s1 - .8):
                txt(c, 've tekrar', 760, 1196, 38, INK, alpha=seg(t, cap_start(9, 'tekrar', s1 - .8), cap_start(9, 'tekrar', s1 - .8) + .3))

def scene4(c, t):
    k0, k1 = L(10); b0, b1 = L(11)
    tp = cap_start(10, 'kısa', k1 - 1.0)
    p = pop(t, k0 - .1, .3)
    if p > 0:                                                                   # sarkinin tamami
        with xf(c, 540, 520, p):
            box(c, 90, 470, 990, 570, r=50, w=8, fill=PAPER)
            for i in range(17):
                note(c, 130 + i * 50, 545 - 18 * ((i * 7) % 3), .42, MUTE)
        txt(c, 'şarkının tamamı', 540, 630, 38, MUTE, 'med', alpha=seg(t, k0 + .2, k0 + .5))
    hp = smooth(seg(t, tp - .1, tp + .3))
    if hp > 0:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(600, 474, 760, 566), 30, 30), paint(YEL, fill=True, alpha=hp * .85))
        for i in range(3): note(c, 630 + i * 50, 545 - 18 * (((i + 10) * 7) % 3), .42, INK)
        box(c, 600, 474, 760, 566, r=30, w=9, color=CORAL, prog=hp)
        txt(c, 'kısa bir parça', 680, 440, 38, CORAL, alpha=hp)
    if t > b0 - .2:
        a = seg(t, b0 - .2, b0 + .2)
        with xf(c, 540, 960, pop(t, b0 - .2, .35)):
            circ(c, 540, 960, 190, color=INK, w=10, fill=PAPER, n=16)
            c.drawCircle(460, 930, 9, paint(INK, fill=True)); c.drawCircle(620, 930, 9, paint(INK, fill=True))
            line(c, [(500, 1030), (540, 1040), (580, 1030)], INK, 6, curve=True, amp=.3)
        tl = cap_start(11, 'iç', b1 - 2.0)
        lp = seg(t, tl - .2, tl + .2)
        if lp > 0:                                                              # dongu
            ang = t * 3
            for k in range(3):
                a_ = ang + k * 2 * math.pi / 3
                pts = [(540 + 120 * math.cos(a_ + i * .12), 880 + 46 * math.sin(a_ + i * .12)) for i in range(12)]
                line(c, pts, CORAL, 7, alpha=lp, curve=True, amp=.3)
                note(c, 540 + 120 * math.cos(a_ + 1.6), 900 + 46 * math.sin(a_ + 1.6), .6, INK, lp)
            with xf(c, 540, 1210, pop(t, tl, .3)): pill(c, 'iç ses: tekrar, tekrar', 540, 1210, 38, CORAL, PAPER)
        with xf(c, 540, 700, pop(t, b0 - .1, .3)): pill(c, 'BİR AÇIKLAMA', 540, 700, 34, TEAL, PAPER)

def scene5(c, t):
    g0, g1 = L(12); m0, m1 = L(13)
    with xf(c, 540, 400, 1, 0, seg(t, g0 - .1, g0 + .3)):
        txt(c, 'Reading Üniversitesi · 2015', 540, 396, 42, INK)
        txt(c, 'Beaman, Powell ve Rapley', 540, 442, 30, MUTE, 'med')
    gy = 1230
    tg = cap_start(12, 'sakız', g0 + .8)
    chew = t > tg
    c.drawOval(skia.Rect.MakeLTRB(170, gy - 14, 430, gy + 18), paint(0xFFEDE3D0, fill=True))
    expr = ('talk' if math.sin(t * 9) > 0 else 'flat') if chew else 'confused'
    me = fig(c, 300, gy, .85, 0, None, expr)
    hx, hy = me['top']
    p = pop(t, g0 + .2, .35)
    if p > 0:                                                                   # akildaki sarki
        with xf(c, 300, 650, p):
            cloud(c, 300, 650, 170, 96, tail=(hx + 20, hy - 10))
            dim = seg(t, cap_start(12, 'üçte', g1 - 1.5), cap_start(12, 'üçte', g1 - 1.5) + .6)
            for k in range(3): note(c, 230 + k * 70, 690 - 20 * (k % 2), .8, INK, 1 - .55 * dim * (k != 1))
    if chew:
        with xf(c, hx + 90, hy + 90, pop(t, tg, .3)): pill(c, 'sakız', hx + 90, hy + 90, 30, CORAL, PAPER)
    tb = cap_start(12, 'üçte', g1 - 1.5)
    bp = seg(t, tb - .3, tb + .4)
    if bp > 0:                                                                  # cubuklar
        for x, hgt, col, lab in ((640, 360, MUTE, 'sakızsız'), (860, 240, TEAL, 'sakızla')):
            hh = hgt * smooth(bp)
            box(c, x - 70, 1110 - hh, x + 70, 1110, r=12, w=7, fill=col)
            txt(c, lab, x, 1160, 36, INK, 'med')
        ground(c, 540, 980, 1110, w=7)
        txt(c, "3'te 1 daha az", 860, 840, 42, TEAL, alpha=seg(t, tb + .3, tb + .6))
    tm = cap_start(13, 'meşgul', m1 - 1.3)
    if t > tm - .1:
        with xf(c, 300, 650, pop(t, tm - .1, .35), -8):
            box(c, 105, 600, 495, 700, r=16, w=8, fill=YEL)
            txt(c, 'İÇ SES MEŞGUL', 300, 668, 40, INK)

def scene6(c, t):
    a0, a1 = L(14); d0, d1 = L(15); e0, e1 = L(16)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_Y)
    ground(c, 50, 1030, gy)
    done = smooth(seg(t, d0 - .2, d0 + .05))
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    u = seg(t, a0 - .2, a1 + .2)                                              # gunes gun boyu yay cizer
    if t < d0:
        ang = math.pi * (1 - u)
        c.drawCircle(540 + 380 * math.cos(ang), 1000 - 380 * math.sin(ang), 40, paint(YEL, fill=True, alpha=1 - done))
    bob = 6 * math.sin(t * 8)
    pose = dict(STAND, tilt=4 * math.sin(t * 4), aR=20 + 10 * math.sin(t * 8), aL=20 - 10 * math.sin(t * 8))
    pose = mix(pose, dict(STAND, aR=148, eR=160 + 26 * math.sin(t * 9)), wv)
    me = fig(c, 540, gy, .9, 0, pose, 'happy' if t > d0 - .1 else 'talk' if math.sin(t * 8) > 0 else 'smile')
    hx, hy = me['top']
    if t < e0:
        for k in range(4):
            ph = (t * .7 + k / 4) % 1
            note(c, hx + (k - 1.5) * 50 + 30 * math.sin(ph * 6 + k), hy - 20 - ph * 260, .7, CORAL if k % 2 else INK, min(1, 4 * ph) * (1 - ph))
    if d0 - .05 < t < e0 - .05:
        p = pop(t, d0 - .05, .35)
        with xf(c, 540, 430, lerp(.7, 1, p), 0, seg(t, d0 - .05, d0 + .1) * (1 - seg(t, e0 - .3, e0 - .08))):
            txt(c, 'Demek o yüzden!', 540, 452, 88, CORAL)
    if t > d0 - .05:
        with xf(c, hx + 160, hy - 40, pop(t, d0 - .05, .3)): bulb(c, hx + 160, hy - 40, .9, t=t)
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
