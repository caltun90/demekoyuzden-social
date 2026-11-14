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

TITLE = 'Kan Tutması'   # yatay formatta etiketin altinda gorunur
HOOK = 'Kan neden tutar?'                # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['KAN', 'NEDEN', 'TUTAR?']       # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 8.05                          # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['damla', 'kan'], 1: ['dönüyor,', 'kararıyor.'], 2: ['kan', 'tutması'], 3: ['yalnız', 'değilsin.'], 4: ['vazovagal', 'tepki.'],
      5: ['önce', 'yükseliyor,'], 6: ['birden', 'düşüyor.'], 7: ['azalıyor,'], 8: ['şaşırtıcı'], 9: ['sadece', 'yükselir.'], 10: ['tek', 'korku'],
      11: ['ailede'], 12: ['neden?'], 13: ['kesin', 'bilinmiyor.'], 15: ['eski', 'refleks.'], 16: ['korkak', 'değilsin,'], 17: ['tuhaf'],
      18: ['demek', 'o', 'yüzden!']}

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

def spiral(c, x, y, r, t, color=CORAL, w=6, alpha=1.0):
    """bas donmesi isareti"""
    pts = [(x + r * (i / 22) * math.cos(i * .62 + t * 4), y + r * (i / 22) * math.sin(i * .62 + t * 4)) for i in range(23)]
    line(c, pts, color, w, alpha=alpha, amp=.5, curve=True)

def drop(c, x, y, s=1.0, alpha=1.0):
    """tek kucuk mercan damla"""
    pts = [(x, y - 64 * s), (x + 30 * s, y - 14 * s), (x + 40 * s, y + 22 * s), (x + 24 * s, y + 50 * s), (x, y + 58 * s),
           (x - 24 * s, y + 50 * s), (x - 40 * s, y + 22 * s), (x - 30 * s, y - 14 * s)]
    line(c, pts, INK, max(4, 7 * s), alpha=alpha, closed=True, fill=CORAL, curve=True, amp=.6 * s)
    line(c, [(x - 18 * s, y + 8 * s), (x - 14 * s, y + 28 * s)], PAPER, max(3, 6 * s), alpha=alpha, amp=.3)

def heart(c, x, y, s=1.0):
    pts = [(x, y + 54 * s), (x - 44 * s, y + 14 * s), (x - 58 * s, y - 22 * s), (x - 34 * s, y - 52 * s), (x, y - 26 * s),
           (x + 34 * s, y - 52 * s), (x + 58 * s, y - 22 * s), (x + 44 * s, y + 14 * s)]
    line(c, pts, INK, 7 * s, closed=True, fill=CORAL, curve=True, amp=.6)

def brain(c, x, y, s=1.0):
    cloud(c, x, y, 178 * s, 102 * s, fill=WASH_P, w=max(5, 8 * s))
    line(c, [(x - 96 * s, y - 22 * s), (x - 44 * s, y - 50 * s), (x, y - 18 * s), (x + 46 * s, y - 50 * s), (x + 98 * s, y - 22 * s)], MUTE, max(4, 6 * s), curve=True, amp=1)
    txt(c, 'BEYİN', x, y + 46 * s, 44 * s, INK)

def arrow(c, p0, p1, color=INK, w=9, prog=1.0):
    line(c, [p0, p1], color, w, prog, amp=1)
    if prog >= 1:
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for d in (2.5, -2.5): line(c, [p1, (p1[0] + 28 * math.cos(a + d), p1[1] + 28 * math.sin(a + d))], color, w, amp=.5)
    else: St.n += 2

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1); d0, d1 = L(2)
    gy = 1104
    wash(c, 60, 350, 1020, gy + 34, WASH_P)
    td = cap_start(0, 'damla', a0 + 1.3)
    tz = cap_start(1, 'başın', b0 + .5); tg = cap_start(1, 'gözün', b1 - 1.0)
    dz = smooth(seg(t, tz - .1, tz + .5)); dark = smooth(seg(t, tg, tg + .5))
    if dark > 0: c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(60, 350, 1020, gy + 34), 30, 30), paint(INK, fill=True, alpha=dark * (.2 + .06 * math.sin(t * 5))))
    c.drawOval(skia.Rect.MakeLTRB(190, gy - 14, 510, gy + 20), paint(0xFFE9D3C8, fill=True))
    up = smooth(seg(t, a0, a0 + .35))
    pose = mix(FRONT, dict(FRONT, aR=62, eR=148, tilt=-4), up)
    pose = mix(pose, dict(FRONT, aR=40, eR=120, aL=30, eL=20, tilt=9 * math.sin(t * 3.2), lean=7 * math.sin(t * 2.6)), dz)
    me = fig(c, 350, gy, 1.0, 0, pose, 'smile' if t < td else ('oh' if dz < .5 else 'confused'))
    zp = pop(t, td, .35)
    if zp > 0:                                                 # buyutec: parmakta tek damla
        hx, hy = me['handR']
        line(c, [(hx + 16, hy - 10), (640, 640)], MUTE, 6, seg(t, td, td + .3), amp=1)
        with xf(c, 770, 600, zp):
            c.drawCircle(770, 600, 168, paint(PAPER, fill=True))
            c.save(); cp_ = skia.Path(); cp_.addCircle(770, 600, 166); c.clipPath(cp_, doAntiAlias=True)
            box(c, 700, 560, 840, 900, r=64, w=9, fill=0xFFF6E3DA, amp=1)   # parmak ucu
            line(c, [(742, 640), (800, 628)], INK, 6, amp=.8)                # kucuk kesik
            c.restore()
            circ(c, 770, 600, 168, color=INK, w=10, n=18, amp=1.2)
            drop(c, 772, 586 + 4 * math.sin(t * 3), .78)
    if dz > 0.02:
        hx, hy = me['top']
        for k, (dx, dy, r) in enumerate(((-70, -52, 38), (30, -86, 46), (112, -40, 30))):
            spiral(c, hx + dx, hy + dy, r * dz, t + k, CORAL, 7, dz)
    kp = pop(t, cap_start(2, 'kan', d0 + 1.0), .3)
    if kp > 0:
        with xf(c, 740, 1010, kp, -2):
            box(c, 510, 962, 970, 1062, r=22, w=8, fill=YEL)
            txt(c, 'KAN TUTMASI', 740, 1032, 56, INK)

def scene2(c, t):
    a0, a1 = L(3); b0, b1 = L(4)
    gy = 1170; x = 540
    tt = cap_start(4, 'vazovagal', b0 + 1.4)
    c.drawOval(skia.Rect.MakeLTRB(x - 170, gy - 16, x + 170, gy + 22), paint(0xFFEDE3D0, fill=True))
    shr = smooth(seg(t, a0, a0 + .35)) * (1 - smooth(seg(t, a1 - .2, a1 + .2)))
    pt = smooth(seg(t, tt - .1, tt + .3))
    pose = mix(FRONT, dict(FRONT, aL=38, eL=118, aR=38, eR=118, tilt=5), shr)
    pose = mix(pose, dict(FRONT, aR=152, eR=168 + 4 * math.sin(t * 6), aL=14, eL=8, tilt=-3), pt)
    fig(c, x, gy, 1.0, 0, pose, 'happy' if (t < a1 + .3 or t > tt) else 'smile')
    fr = pop(t, a0 + .4, .3) * (1 - smooth(seg(t, tt - .5, tt - .15)))
    if fr > 0.01:                                              # yalniz degilsin
        for k, (fx, fc) in enumerate(((205, 1), (875, -1))):
            with xf(c, fx, gy, fr):
                o = fig(c, fx, gy - 8, .62, fc, dict(STAND, aR=40, eR=120, aL=30, eL=110, tilt=6, lean=5 * math.sin(t * 3 + k)), 'confused')
            sp = fr * pop(t, a0 + .7 + k * .35, .3)
            if sp > 0.01: spiral(c, o['top'][0], o['top'][1] - 50, 34 * sp, t + k, CORAL, 6)
    if t > tt:
        p = pop(t, tt, .35)
        with xf(c, 540, 460, lerp(.7, 1, p), 0, seg(t, tt, tt + .15)):
            txt(c, 'VAZOVAGAL', 540, 424, 108, INK)
            txt(c, 'TEPKİ', 540, 540, 108, CORAL)
        line(c, [(270, 576), (400, 570), (580, 580), (810, 568)], INK, 10, seg(t, tt + .4, tt + .8), curve=True)
        txt(c, 'nabız ve tansiyon birden düşer', 540, 636, 36, MUTE, 'med', alpha=seg(t, tt + .7, tt + 1.0))

UPC = [(170, 800), (260, 786), (350, 720), (440, 640), (530, 600)]            # once yukselir
DNC = [(530, 600), (590, 640), (650, 800), (720, 930), (810, 962), (910, 968)]  # sonra birden duser

def scene3(c, t):
    a0, a1 = L(5); b0, b1 = L(6); d0, d1 = L(7)
    ty = cap_start(5, 'önce', a1 - 1.3); tdn = cap_start(6, 'birden', b0 + .5)
    tn = cap_start(5, 'nabız', a0 + 1.8)
    up = seg(t, ty, ty + 1.0); dn = seg(t, tdn, tdn + .7)
    rate = 5 + 9 * up - 11 * dn                               # kalp: once hizlanir, sonra yavaslar
    hp = pop(t, a0, .3)
    if hp > 0:
        with xf(c, 190, 440, hp * (1 + .1 * max(0, math.sin(t * rate)))): heart(c, 190, 440, 1.0)
        txt(c, 'nabız ve tansiyon', 280, 458, 52, INK, align='l', alpha=seg(t, tn - .1, tn + .2))
    gp = seg(t, a0 + .2, a0 + .6)
    if gp > 0:                                                 # grafik
        line(c, [(140, 540), (140, 1000), (960, 1000)], INK, 9, gp, amp=1.2)
        for k in range(9): line(c, [(170 + k * 88, 800), (214 + k * 88, 800)], MUTE, 6, alpha=gp, amp=.5)
        txt(c, 'normal', 952, 786, 30, MUTE, 'med', align='r', alpha=gp)
    if up > 0:
        line(c, UPC, CORAL, 15, up, amp=1, curve=True)
        txt(c, '1. önce yükselir', 336, 566, 44, CORAL, alpha=seg(t, ty + .3, ty + .6))
    else: St.n += 1
    if dn > 0:
        line(c, DNC, TEAL, 15, dn, amp=1, curve=True)
        txt(c, '2. birden düşer', 808, 700, 44, TEAL, alpha=seg(t, tdn + .3, tdn + .6))
    else: St.n += 1
    if t > d0 - .1:                                            # beyne giden kan azalir
        bp = pop(t, d0, .3)
        if bp > 0:
            with xf(c, 250, 1140, bp): brain(c, 250, 1140, .62)
        tb = cap_start(7, 'baş', d1 - .9)
        for k in range(3):
            al = seg(t, d0 + .2 + k * .12, d0 + .4 + k * .12) * (1 - (0, .55, .9)[k] * smooth(seg(t, d0 + .8, d0 + 1.5)))
            if al > 0: drop(c, 450 + k * 78, 1136, .5, al)
        txt(c, 'daha az kan', 790, 1124, 44, CORAL, alpha=seg(t, d0 + .5, d0 + .8))
        sp = pop(t, tb, .3)
        if sp > 0:
            txt(c, 'baş döner', 800, 1196, 44, INK, alpha=clamp(sp))
            spiral(c, 650, 1180, 30 * sp, t, CORAL, 6)

def spider(c, x, y, s=1.0):
    for sd in (-1, 1):
        for k in range(4):
            a = math.radians(-50 + k * 34)
            kx, ky = x + sd * 62 * s * math.cos(a), y + 62 * s * math.sin(a) - 16 * s
            line(c, [(x + sd * 20 * s, y), (kx, ky), (kx + sd * 26 * s, ky + 44 * s)], INK, 6 * s, amp=.6)
    circ(c, x, y, 36 * s, 32 * s, color=INK, w=6 * s, fill=INK, n=12, amp=.8)
    for sd in (-1, 1): c.drawCircle(x + sd * 12 * s, y - 6 * s, 6 * s, paint(PAPER, fill=True))

def scene4(c, t):
    a0, a1 = L(8); b0, b1 = L(9); d0, d1 = L(10); e0, e1 = L(11)
    hp = pop(t, a0, .35)
    if hp > 0:
        with xf(c, 540, 400, lerp(.7, 1, hp), 0, seg(t, a0, a0 + .15)): txt(c, 'Şaşırtıcı olan şu:', 540, 424, 68, INK)
    c1 = pop(t, b0, .3); ts = cap_start(9, 'sadece', b1 - 1.2)
    if c1 > 0:                                                 # baska korkular: nabiz sadece yukselir
        with xf(c, 290, 700, c1):
            box(c, 90, 490, 490, 910, r=30, w=8, fill=PAPER)
            spider(c, 290, 590, .9)
            txt(c, 'örümcek, yükseklik', 290, 700, 34, INK)
        u = seg(t, ts, ts + .6)
        if u > 0: line(c, [(150, 860), (230, 846), (320, 800), (430, 740)], CORAL, 13, u, amp=1, curve=True)
        else: St.n += 1
        txt(c, 'sadece yükselir', 290, 968, 40, CORAL, alpha=seg(t, ts + .3, ts + .55))
    c2 = pop(t, d0, .3); tt = cap_start(10, 'tek', d1 - .9)
    if c2 > 0:                                                 # kan: yukselir, sonra duser
        with xf(c, 790, 700, c2):
            box(c, 590, 490, 990, 910, r=30, w=8, fill=PAPER)
            drop(c, 790, 590, .9)
            txt(c, 'kan', 790, 700, 34, INK)
        u = seg(t, d0 + .3, d0 + 1.0)
        if u > 0: line(c, [(650, 820), (720, 800), (780, 746), (820, 760), (860, 850), (930, 872)], TEAL, 13, u, amp=1, curve=True)
        else: St.n += 1
        zp = pop(t, tt, .3)
        if zp > 0:
            with xf(c, 790, 982, zp, -3):
                box(c, 600, 940, 980, 1024, r=18, w=7, fill=YEL)
                txt(c, 'bayıltabilir', 790, 998, 42, INK)
    fp = pop(t, e0, .3)
    if fp > 0:                                                 # ailede sik gorulur
        gy = 1250
        for k, (fx, sc) in enumerate(((230, .46), (330, .46), (420, .3))):
            with xf(c, fx, gy, pop(t, e0 + k * .12, .3)): fig(c, fx, gy, sc, 0, None, 'smile')
        txt(c, 'ailede sık görülür', 740, 1180, 46, TEAL, alpha=seg(t, e0 + .3, e0 + .55))

def gauge(c, x, y, r, v):
    """tansiyon gostergesi: v 1 (yuksek) -> 0 (dusuk)"""
    pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(180, 361, 15)]
    line(c, pts, INK, 10, curve=True, amp=.8)
    line(c, [(x - r, y), (x + r, y)], INK, 8, amp=.8)
    a = math.radians(lerp(205, 335, v))
    line(c, [(x, y), (x + r * .78 * math.cos(a), y + r * .78 * math.sin(a))], CORAL, 11, amp=.5)
    c.drawCircle(x, y, 13, paint(INK, fill=True))

def scene5(c, t):
    a0, a1 = L(12); k0, k1 = L(13); b0, b1 = L(14); d0, d1 = L(15); q0, q1 = L(16)
    hp = pop(t, a0, .35)
    if hp > 0:
        with xf(c, 540, 400, lerp(.7, 1, hp), 0, seg(t, a0, a0 + .15)): txt(c, 'Neden?', 540, 430, 88, INK)
    kp = pop(t, k0, .3)
    if kp > 0:
        with xf(c, 320, 540, kp): pill(c, 'KESİN BİLİNMİYOR', 320, 540, 32, MUTE, PAPER)
    bp = pop(t, b0, .3)
    if bp > 0:
        with xf(c, 770, 540, bp): pill(c, 'BİR AÇIKLAMA', 770, 540, 32, TEAL, PAPER)
    tt = cap_start(15, 'tansiyonu', d0 + .9); tk = cap_start(15, 'kan', d0 + 2.0); tr = cap_start(15, 'eski', d1 - 1.0)
    gp = pop(t, tt - .1, .3)
    if gp > 0:                                                 # tansiyon duser
        with xf(c, 280, 800, gp):
            gauge(c, 280, 830, 130, 1 - smooth(seg(t, tt + .2, tt + 1.0)))
        txt(c, 'tansiyon düşer', 280, 920, 40, INK, alpha=seg(t, tt + .2, tt + .45))
    arrow(c, (470, 790), (590, 790), INK, 9, seg(t, tk - .2, tk + .1))
    dp = pop(t, tk, .3)
    if t > tk:                                                 # kan kaybi azalir
        less = smooth(seg(t, tk + .3, tk + 1.0))
        for k in range(3):
            drop(c, 700 + k * 90, 780, .62, 1 - (0, .6, .9)[k] * less)
        txt(c, 'kan kaybı azalır', 790, 920, 40, CORAL, alpha=seg(t, tk + .2, tk + .45))
    rp = pop(t, tr, .3)
    if rp > 0:
        with xf(c, 540, 1010, rp): pill(c, 'eski bir refleks', 540, 1010, 38, INK, PAPER)
    yp = pop(t, cap_start(16, 'vücudun', q0 + 1.3), .32)
    if yp > 0:                                                 # vucudun seni korumaya calisiyor
        with xf(c, 540, 1150, yp, -1.5):
            box(c, 110, 1090, 970, 1210, r=26, w=8, fill=YEL)
            txt(c, 'vücudun seni korumaya çalışıyor', 540, 1166, 46, INK)

def scene6(c, t):
    a0, a1 = L(17); d0, d1 = L(18); e0, e1 = L(19)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_P)
    ground(c, 50, 1030, gy)
    tf = cap_start(17, 'tuhaf', a1 - 1.1)
    done = smooth(seg(t, d0 - .2, d0 + .05))
    dz = smooth(seg(t, tf - .2, tf + .4)) * (1 - done)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    ah = clamp(pop(t, d0 - .05, .3)) * (1 - wv)
    pose = mix(FRONT, dict(FRONT, aR=58, eR=96, tilt=-4), smooth(seg(t, a0, a0 + .3)) * (1 - done))     # kolunu uzatmis
    pose = mix(pose, dict(FRONT, aR=58, eR=96, aL=30, eL=20, tilt=9 * math.sin(t * 3.2), lean=6 * math.sin(t * 2.6)), dz)
    pose = mix(pose, dict(FRONT, aL=150, eL=166, aR=150, eR=166), ah)
    pose = mix(pose, dict(FRONT, aR=148, eR=160 + 26 * math.sin(t * 9), aL=12, eL=8), wv)
    me = fig(c, 300, gy, .85, 0, pose, ('smile' if dz < .5 else 'confused') if t < d0 - .1 else 'happy')
    cp = pop(t, a0 + .3, .3) * (1 - done)
    if cp > 0.01:                                              # aklindaki tek damla
        hx, hy = me['top']
        with xf(c, 720, 800, cp):
            cloud(c, 720, 800, 190, 120, tail=(hx + 70, hy + 30))
            drop(c, 720, 800, .9)
    if dz > 0.02:
        hx, hy = me['top']
        for k, (dx, dy, r) in enumerate(((-64, -46, 32), (26, -74, 40), (100, -34, 26))):
            spiral(c, hx + dx, hy + dy, r * dz, t + k, CORAL, 6, dz)
    if d0 - .05 < t < e0 - .05:
        p = pop(t, d0 - .05, .35)
        with xf(c, 540, 430, lerp(.7, 1, p), 0, seg(t, d0 - .05, d0 + .1) * (1 - seg(t, e0 - .3, e0 - .08))):
            txt(c, 'Demek o yüzden!', 540, 452, 88, CORAL)
    if t > d0 - .05:
        bp = pop(t, d0 - .05, .3)
        with xf(c, 720, 800, bp): bulb(c, 720, 790, 1.1, t=t)
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
