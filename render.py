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

TITLE = 'Pestisit ve Yıkama'   # yatay formatta etiketin altinda gorunur
HOOK = 'Yıkamak pestisiti alır mı?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['YIKAMAK', 'PESTİSİTİ', 'ALIR MI?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 5.1                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['çalkaladın.'], 1: ['tertemiz'], 2: ['pestisit'], 3: ['böceklere,', 'mantarlara', 'otlara'], 4: ['zarar'], 5: ["2017'de"],
      6: ['deney'], 7: ['ilaç'], 8: ['farklı'], 9: ['bir', 'kısmını'], 10: ['çok', 'daha', 'fazlasını'], 11: ['hiçbir'],
      12: ['kabuğun', 'içine'], 13: ['yüzeydekini', 'içeri'], 14: ['akan', 'sabunsuz,', 'ovarak'], 15: ['"bir', 'daha', 'yıka"'], 16: ['demek', 'o', 'yüzden!']}


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

def _dot_pos(seed, n=18):
    r = random.Random(seed); out = []
    while len(out) < n:
        u, v = r.uniform(-1, 1), r.uniform(-1, 1)
        if u * u + v * v > 1: continue
        if all((u - a) ** 2 + (v - b) ** 2 > .09 for a, b in out): out.append((u, v))
        elif r.random() < .02: out.append((u, v))
    return out
DOTS = {s: _dot_pos(s) for s in (3, 5, 7, 11)}

def apple(c, x, y, r, n=0, fade=None, seed=3, two=True):
    """elma; n tane ilac kalintisi noktasi (sari = mantar ilaci, turkuaz = bocek ilaci). Nokta konumlarini dondurur."""
    circ(c, x, y + r * .04, r, r * .94, color=INK, w=max(5, r * .07), fill=CORAL, amp=1.2, n=14)
    c.drawOval(skia.Rect.MakeLTRB(x - r * .62, y - r * .58, x - r * .3, y - r * .12), paint(PAPER, fill=True, alpha=.45))
    line(c, [(x, y - r * .84), (x + r * .07, y - r * 1.2)], INK, max(4, r * .07), amp=.6)
    line(c, [(x + r * .08, y - r * 1.06), (x + r * .32, y - r * 1.27), (x + r * .55, y - r * 1.14), (x + r * .3, y - r * .99)],
         INK, max(3, r * .05), closed=True, fill=TEAL, curve=True, amp=.6)
    pos = []
    for i, (u, v) in enumerate(DOTS[seed][:n]):
        px, py, rr = x + u * r * .7, y + v * r * .66, max(5, r * .085)
        pos.append((px, py, rr))
        a = 1.0 if fade is None else clamp(fade(i))
        if a <= 0.01: continue
        c.drawCircle(px, py, rr, paint(TEAL if (two and i % 2) else YEL, fill=True, alpha=a))
        c.drawCircle(px, py, rr, paint(INK, max(2, r * .022), alpha=a))
    return pos

def faucet(c, bx, by, nx, ny):
    pts = [(bx, by), (bx, ny - 55), (bx - 34, ny - 95), (nx + 40, ny - 95), (nx, ny - 55), (nx, ny)]
    line(c, pts, INK, 28, curve=True, amp=.4); line(c, pts, MUTE, 12, curve=True, amp=.4)
    line(c, [(bx, by - 150), (bx + 62, by - 176)], INK, 16, amp=.5)

def stream(c, x, y0, y1, t, alpha=1.0, w=44):
    if alpha <= 0.01: return
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - w / 2, y0, x + w / 2, y1), w / 2, w / 2), paint(0xFFBFE3DC, fill=True, alpha=alpha))
    for k in (-1, 0, 1):
        pts = [(x + k * 11 + 4 * math.sin(yy * .05 + t * 20 + k * 2), yy) for yy in range(int(y0) + 10, int(y1) - 10, 36)]
        if len(pts) > 2: line(c, pts, TEAL, 5, alpha=alpha, curve=True, amp=.4)

def lens(c, x, y, r):
    """buyutec: elma kabugu yakindan, ustunde ilac noktalari"""
    c.save(); p = skia.Path(); p.addCircle(x, y, r); c.clipPath(p, doAntiAlias=True)
    c.drawCircle(x, y, r, paint(CORAL, fill=True))
    for k, (u, v) in enumerate(((-.5, -.35), (.15, -.55), (.55, -.05), (-.2, .2), (.3, .5), (-.6, .45), (.0, -.05))):
        rr = r * .14
        c.drawCircle(x + u * r, y + v * r, rr, paint(TEAL if k % 2 else YEL, fill=True))
        c.drawCircle(x + u * r, y + v * r, rr, paint(INK, 4))
    c.restore()
    circ(c, x, y, r, color=INK, w=12, amp=1, n=16)
    line(c, [(x + r * .72, y + r * .72), (x + r * 1.28, y + r * 1.28)], INK, 22, amp=.6)

def bug(c, x, y, s=1.0, t=0.0):
    for sd in (-1, 1):
        for k in range(3):
            yy = y - 14 * s + k * 22 * s; wg = 5 * math.sin(t * 14 + k + sd)
            line(c, [(x + sd * 30 * s, yy), (x + sd * 62 * s, yy - 10 * s + wg), (x + sd * 72 * s, yy + 14 * s + wg)], INK, 6 * s, amp=.5)
    line(c, [(x - 8 * s, y - 52 * s), (x - 26 * s, y - 80 * s)], INK, 5 * s, amp=.4)
    line(c, [(x + 8 * s, y - 52 * s), (x + 26 * s, y - 80 * s)], INK, 5 * s, amp=.4)
    c.drawCircle(x, y - 42 * s, 19 * s, paint(INK, fill=True))
    c.drawOval(skia.Rect.MakeLTRB(x - 38 * s, y - 30 * s, x + 38 * s, y + 46 * s), paint(INK, fill=True))
    line(c, [(x, y - 26 * s), (x, y + 42 * s)], MUTE, 4 * s, amp=.3)

def mushroom(c, x, y, s=1.0, t=0.0):
    box(c, x - 24 * s, y - 4 * s, x + 24 * s, y + 62 * s, r=12 * s, w=7 * s, fill=PAPER, amp=.8)
    pts = [(x + 74 * s * math.cos(math.pi + math.pi * i / 10), y - 2 * s + 70 * s * math.sin(math.pi + math.pi * i / 10)) for i in range(11)]
    line(c, pts, INK, 7 * s, closed=True, fill=CORAL, curve=False, amp=.8)
    for u, v in ((-36, -24), (6, -48), (36, -18)): c.drawCircle(x + u * s, y + v * s, 9 * s, paint(PAPER, fill=True))

def weed(c, x, y, s=1.0, t=0.0):
    sw = 4 * math.sin(t * 3)
    for ex, ey in ((-56, -44), (-12, -74), (40, -60), (64, -14)):
        line(c, [(x, y + 60 * s), (x + ex * .45 * s, y + (ey * .3 + 20) * s), (x + (ex + sw) * s, y + ey * s)], TEAL, 11 * s, curve=True, amp=.6)
    line(c, [(x - 70 * s, y + 62 * s), (x + 70 * s, y + 62 * s)], INK, 7 * s, amp=.8)

def bowl(c, x, y, w=300, h=120, t=0.0):
    line(c, [(x - w / 2, y), (x - w / 2 + 34, y + h), (x + w / 2 - 34, y + h), (x + w / 2, y)], INK, 8, closed=True, fill=0xFFBFE3DC, amp=1)
    line(c, [(x - w / 2 + 18, y + 22 + 4 * math.sin(t * 4)), (x - w / 4, y + 16), (x, y + 24 - 4 * math.sin(t * 4)), (x + w / 4, y + 16), (x + w / 2 - 18, y + 22)], TEAL, 6, curve=True, amp=.6)

def soap(c, x, y, s=1.0):
    box(c, x - 56 * s, y - 32 * s, x + 56 * s, y + 32 * s, r=22 * s, w=7 * s, fill=YEL, amp=.8)
    for u, v, rr in ((-30, -48, 14), (2, -62, 10), (30, -46, 12)): circ(c, x + u * s, y + v * s, rr * s, color=INK, w=4 * s, fill=PAPER, amp=.5, n=9)

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1)
    gy = 1200
    wash(c, 60, 340, 1020, gy + 30, WASH_Y)
    c.drawOval(skia.Rect.MakeLTRB(150, gy - 14, 410, gy + 18), paint(0xFFEDE3D0, fill=True))
    line(c, [(390, 1000), (420, 1110), (840, 1110), (870, 1000)], INK, 8, closed=True, fill=PAPER, amp=1)   # lavabo
    box(c, 370, 958, 1010, 1002, r=10, w=8, fill=PAPER)                                                    # tezgah
    faucet(c, 720, 958, 450, 640)
    tq = cap_start(1, 'değil', b0 + .5)
    on = smooth(seg(t, a0 - .2, a0 + .1)) * (1 - smooth(seg(t, b0 - .15, b0 + .1)))
    stream(c, 450, 650, 1100, t, on)
    pose = dict(STAND, aR=95, eR=110 + 10 * math.sin(t * 13) * on, tilt=3)
    me = fig(c, 280, gy, 1.0, 1, pose, 'smile' if t < b0 else ('happy' if t < tq + .2 else 'oh'))
    hx, hy = me['handR']
    ax, ay = hx + 28, hy - 20
    apple(c, ax, ay, 58)
    if on > 0.02:                                                      # su sicramasi
        for k in range(6):
            ph = (t * 2.2 + k / 6) % 1; ang = math.radians(200 + k * 28)
            c.drawCircle(ax + math.cos(ang) * (64 + 50 * ph), ay + 40 + math.sin(ang) * -1 * (20 + 40 * ph) + 60 * ph * ph,
                         7, paint(TEAL, fill=True, alpha=on * (1 - ph)))
    sp = seg(t, b0, b0 + .3) * (1 - seg(t, tq + .2, tq + .5))
    if sp > 0: burst(c, ax, ay, 80, 104, 8, YEL, 8, sp)
    lp = pop(t, tq - .1, .35)
    if lp > 0:                                                         # yakindan bak: kabukta noktalar
        dashes(c, (ax + 40, ay - 42), (744, 518), 6, MUTE, 6, clamp(lp))
        with xf(c, 820, 440, lp): lens(c, 820, 440, 110)
        qmark(c, 640, 470, 130, t, CORAL, sc=clamp(lp))

def scene2(c, t):
    p0, p1 = L(2); d0, d1 = L(3); u0, u1 = L(4)
    tp = cap_start(2, 'pestisit', p0 + .8)
    ap = pop(t, p0 - .15, .35)
    sh = smooth(seg(t, d0 - .2, d0 + .3))
    ay, ar = lerp(730, 650, sh), lerp(170, 120, sh)
    if ap > 0:
        with xf(c, 540, ay, ap):
            apple(c, 540, ay, ar, n=16, fade=lambda i: seg(t, tp + i * .04, tp + .15 + i * .04))
    if t > tp - .05:
        pp = pop(t, tp - .05, .35)
        with xf(c, 540, 420, lerp(.7, 1, pp), 0, seg(t, tp - .05, tp + .1)):
            txt(c, 'PESTİSİT', 540, 452, 104, CORAL)
    for k, (ix, word, lab, fn) in enumerate(((230, 'böceklere', 'böcek', bug), (540, 'mantarlara', 'mantar', mushroom), (850, 'otlara', 'yabani ot', weed))):
        ti = cap_start(3, word, d0 + .5 + k * 1.2)
        ip = pop(t, ti - .1, .3)
        if ip > 0:
            with xf(c, ix, 960, ip): fn(c, ix, 960, 1.0, t)
            txt(c, lab, ix, 1090, 36, MUTE, 'med', alpha=seg(t, ti, ti + .3))
            cross(c, ix + 66, 900, .8, seg(t, ti + .25, ti + .6))
    if t > u0 - .1:
        circ(c, 540, ay, ar + 44, color=TEAL, w=10, prog=seg(t, u0, u0 + .5), n=16)
        with xf(c, 540, 1190, pop(t, u0 + .1, .3)): pill(c, 'ürün korunsun diye', 540, 1190, 38, TEAL, PAPER)

def scene3(c, t):
    y0_, y1_ = L(5); m0, m1 = L(6); s0, s1 = L(7); w0, w1 = L(8)
    with xf(c, 540, 400, 1, 0, seg(t, y0_ - .1, y0_ + .3)):
        txt(c, 'Massachusetts Üniversitesi · 2017', 540, 396, 42, INK)
        txt(c, 'Journal of Agricultural and Food Chemistry', 540, 444, 28, MUTE, 'med')
    ts = cap_start(7, 'sürüldü', s0 + .9)
    tb = cap_start(7, 'bekletildi', s1 - 1.2)
    dn = smooth(seg(t, w0 + .1, w0 + .7))
    for k, (x, lab, col) in enumerate(((330, 'musluk suyu', TEAL), (750, 'karbonatlı su', INK))):
        ap = pop(t, m0 + .3 + k * .2, .3)
        if ap <= 0: continue
        ay = lerp(660, 920, dn)
        with xf(c, x, ay, ap):
            apple(c, x, ay, 100, n=12, seed=5, fade=lambda i: seg(t, ts + i * .07, ts + .12 + i * .07))
        if t > w0:
            with xf(c, x, 1010, pop(t, w0 + .2 + k * .15, .3)): bowl(c, x, 960, 300, 120, t)
            txt(c, lab, x, 1180, 40, col, alpha=seg(t, w0 + .4 + k * .15, w0 + .7 + k * .15))
    la = seg(t, ts + .5, ts + .8) * (1 - seg(t, w0 - .1, w0 + .2))
    if la > 0:
        for x, col, s in ((210, YEL, 'mantar ilacı'), (600, TEAL, 'böcek ilacı')):
            c.drawCircle(x, 836, 15, paint(col, fill=True, alpha=la)); c.drawCircle(x, 836, 15, paint(INK, 4, alpha=la))
            txt(c, s, x + 30, 848, 36, INK, 'med', 'l', la)
    if t > tb - .1:
        with xf(c, 540, 930, pop(t, tb - .1, .3) * (1 - seg(t, w0 - .1, w0 + .2))): pill(c, '1 gün bekledi', 540, 930, 38, INK, PAPER)

LKEEP = {1, 3, 4, 6, 8, 10, 11, 13, 15}   # musluk suyundan sonra kalan noktalar
RKEEP = {2, 7, 12}                        # karbonatli sudan sonra kalan noktalar

def scene4(c, t):
    r0_, r1_ = L(9); k0, k1 = L(10); h0, h1 = L(11)
    th = cap_start(11, 'hiçbir', h0 + .3)
    rings = []
    for x, name, dur, keep, w0, w1, col, res in ((300, 'musluk suyu', '2 dakika', LKEEP, r0_ + .5, r1_ - .2, TEAL, 'bir kısmı gitti'),
                                                  (780, 'karbonatlı su', '15 dakika', RKEEP, k0 + .4, k1 - .2, INK, 'çoğu gitti')):
        ap = pop(t, w0 - .6, .3)
        if ap <= 0: continue
        with xf(c, x, 500, 1, 0, seg(t, w0 - .6, w0 - .3)):
            txt(c, name, x, 476, 46, col)
            txt(c, dur, x, 526, 36, MUTE, 'med')
        rem = [i for i in range(16) if i not in keep]
        fd = {i: 1 - seg(t, w0 + j * (w1 - w0) / len(rem), w0 + j * (w1 - w0) / len(rem) + .25) for j, i in enumerate(rem)}
        wsh = seg(t, w0 - .2, w0) * (1 - seg(t, w1, w1 + .3))
        with xf(c, x, 740, ap):
            pos = apple(c, x, 740, 135, n=16, seed=7, fade=lambda i: fd.get(i, 1.0))
        if wsh > 0.01:                                                      # yikanirken su dalgalari
            for k in range(3):
                ph = (t * 1.5 + k / 3) % 1
                line(c, [(x - 175, 650 + ph * 200), (x - 200, 700 + ph * 200), (x - 175, 750 + ph * 200)], TEAL, 7, alpha=wsh * (1 - ph), curve=True, amp=.5)
        txt(c, res, x, 960, 36, col, 'med', alpha=seg(t, w1 - .3, w1))
        rings += [pos[i] for i in keep]
    if t > h0:
        for px, py, rr in rings: circ(c, px, py, rr + 13, color=INK, w=5, prog=seg(t, h0 + .1, h0 + .5), n=10, amp=.6)
    sp = pop(t, th, .3)
    if sp > 0:
        with xf(c, 540, 1080, sp, -3):
            box(c, 220, 1028, 860, 1132, r=24, w=8, fill=YEL)
            txt(c, 'hiçbiri hepsini almadı', 540, 1100, 50, INK)

SURF = [(190, 0), (330, 1), (470, 0), (630, 1), (770, 0), (900, 1)]     # yuzeydeki noktalar (x, renk)
INNER = [(350, 664, 1), (600, 676, 0), (840, 660, 1)]                   # kabuga isleyen noktalar

def scene5(c, t):
    c0, c1 = L(12); s0, s1 = L(13); u0, u1 = L(14)
    sec = 1 - smooth(seg(t, u0 - .25, u0 + .1))
    ti = cap_start(12, 'kabuğun', c1 - 1.2)
    ty = cap_start(13, 'yüzeydekini', s0)
    tin = cap_start(13, 'içeri', s1 - 1.0)
    if sec > 0.01:
        with xf(c, 540, 760, 1, 0, sec):
            txt(c, 'elma kabuğu, yakından kesit', 540, 410, 40, MUTE, 'med', alpha=seg(t, c0 - .2, c0 + .1))
            box(c, 110, 690, 970, 1010, r=22, w=8, fill=0xFFFFF0CF)
            box(c, 110, 620, 970, 720, r=16, w=8, fill=CORAL)
            txt(c, 'kabuk', 140, 684, 40, PAPER, 'bold', 'l')
            txt(c, 'meyve', 540, 940, 44, MUTE, 'med')
            go = smooth(seg(t, ty + .1, ty + 1.1))
            for k, (x, cl) in enumerate(SURF):
                a = 1 - seg(t, ty + .3 + k * .08, ty + 1.0 + k * .08)
                if a <= 0.01: continue
                dx = 260 * smooth(seg(t, ty + .1 + k * .08, ty + 1.1 + k * .08))
                c.drawCircle(x + dx, 600, 20, paint(TEAL if cl else YEL, fill=True, alpha=a)); c.drawCircle(x + dx, 600, 20, paint(INK, 5, alpha=a))
            sink = smooth(seg(t, ti, ti + .9))
            for x, yy, cl in INNER:
                y = lerp(600, yy, sink)
                c.drawCircle(x, y, 20, paint(TEAL if cl else YEL, fill=True)); c.drawCircle(x, y, 20, paint(INK, 5))
            wa = seg(t, ty - .1, ty + .2) * (1 - seg(t, ty + 1.3, ty + 1.7))
            if wa > 0:                                                  # su yuzeyden akiyor
                for k in range(3):
                    yy = 520 + k * 22
                    pts = [(xx, yy + 6 * math.sin(xx * .03 - t * 12 + k)) for xx in range(120, 980, 40)]
                    line(c, pts, TEAL, 6, alpha=wa, curve=True, amp=.4)
            if t > ty + .2: txt(c, 'yüzeydeki gider', 540, 486, 48, TEAL, alpha=seg(t, ty + .2, ty + .5))
            if t > tin:
                for x, yy, cl in INNER: circ(c, x, yy, 36, color=INK, w=6, prog=seg(t, tin, tin + .4), n=12, amp=.6)
                txt(c, 'içeri geçen kalır', 540, 820, 48, CORAL, alpha=seg(t, tin + .1, tin + .4))
    if t > u0 - .25:
        a = seg(t, u0 - .2, u0 + .15)
        with xf(c, 540, 700, 1, 0, a):
            ground(c, 260, 900, 900)
            faucet(c, 780, 900, 540, 470)
            stream(c, 540, 480, 895, t)
            apple(c, 540, 700, 105)
            rot = t * 2.4
            for k in range(2):                                          # ovma oklari
                a0_ = rot + k * math.pi
                pts = [(540 + 160 * math.cos(a0_ + i * .14), 700 + 150 * math.sin(a0_ + i * .14)) for i in range(9)]
                line(c, pts, INK, 9, curve=True, amp=.4)
                ex, ey = pts[-1]; dxa, dya = -math.sin(a0_ + 1.12), math.cos(a0_ + 1.12)
                line(c, [(ex - 22 * dxa + 16 * dya, ey - 22 * dya - 16 * dxa), (ex, ey), (ex - 22 * dxa - 16 * dya, ey - 22 * dya + 16 * dxa)], INK, 9, amp=.3)
        for x, word, lab, col in ((250, 'akan', 'akan su', TEAL), (540, 'ovarak', 'ovarak', INK)):
            p = pop(t, cap_start(14, word, u0 + 1), .3)
            if p > 0:
                with xf(c, x, 1060, p): pill(c, lab, x, 1060, 40, col, PAPER)
        p = pop(t, cap_start(14, 'sabunsuz', u0 + 2), .3)
        if p > 0:
            with xf(c, 830, 1050, p):
                soap(c, 830, 1050, 1.0)
                cross(c, 830, 1040, 1.4, seg(t, cap_start(14, 'sabunsuz', u0 + 2) + .2, cap_start(14, 'sabunsuz', u0 + 2) + .6))
            txt(c, 'sabun yok', 830, 1160, 36, CORAL, alpha=seg(t, cap_start(14, 'sabunsuz', u0 + 2) + .3, cap_start(14, 'sabunsuz', u0 + 2) + .6))

def scene6(c, t):
    a0, a1 = L(15); d0, d1 = L(16); e0, e1 = L(17)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_Y)
    ground(c, 50, 1030, gy)
    done = smooth(seg(t, d0 - .2, d0 + .05))
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    talk = float(a0 - .1 < t < d0 - .2)
    mp = mix(STAND, dict(STAND, aR=100, eR=96 + 18 * math.sin(t * 11), tilt=-3), talk)
    mom = fig(c, 770, gy, 1.0, -1, mp, ('talk' if int(t * 7) % 2 == 0 else 'flat') if talk else 'smile')
    mx, my = mom['top']
    c.drawCircle(mx + 20, my + 4, 26, paint(INK, fill=True))                      # topuz
    kp = mix(STAND, dict(STAND, aR=70, eR=96), 1)
    kp = mix(kp, dict(STAND, aR=150, eR=162 + 24 * math.sin(t * 9)), wv)
    kid = fig(c, 290, gy, .8, 1, kp, 'confused' if t < d0 - .1 else 'happy')
    if wv < .5:
        hx, hy = kid['handR']
        apple(c, hx + 24, hy - 16, 44)
        if t > d0 - .1: burst(c, hx + 24, hy - 16, 60, 80, 8, YEL, 6, 1 - seg(t, d0 + .6, d0 + 1.0))
    if t < d0 - .1:
        sp = pop(t, a0, .3)
        if sp > 0:
            with xf(c, 720, 600, sp):
                speech(c, 470, 520, 980, 660, (mx - 30, my - 10))
                txt(c, 'Bir daha yıka!', 725, 610, 56, CORAL)
    kx, ky = kid['top']
    if d0 - .05 < t < e0 - .05:
        p = pop(t, d0 - .05, .35)
        with xf(c, 540, 430, lerp(.7, 1, p), 0, seg(t, d0 - .05, d0 + .1) * (1 - seg(t, e0 - .3, e0 - .08))):
            txt(c, 'Demek o yüzden!', 540, 452, 88, CORAL)
    if t > d0 - .05:
        with xf(c, kx, ky - 110, pop(t, d0 - .05, .3)): bulb(c, kx, ky - 110, .9, t=t)
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
