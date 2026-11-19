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

TITLE = 'Buruşan parmaklar'   # yatay formatta etiketin altinda gorunur
HOOK = 'Parmak suda neden buruşur?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['PARMAK', 'SUDA NEDEN', 'BURUŞUR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 2.2                          # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['buruşur?'], 1: ['hayır.'], 2: ['sinir', 'sistemin'], 3: ['yüz', 'yıl'], 4: ['buruşmuyor.'], 5: ['damarları', 'daraltıyor.'], 6: ['küçülüyor,', 'kıvrılıyor.'], 7: ['lastiğinin', 'dişleri'], 8: ['tutuşu'], 9: ["2013'te"], 10: ['daha', 'hızlı'], 11: ['fark', 'yoktu.'], 12: ['bulamadı.'], 13: ['hâlâ', 'tartışılıyor.'], 14: ['buruş'], 15: ['demek', 'o', 'yüzden!']}


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
SKIN = 0xFFF8D8C2
PULP = 0xFFF6B7A3
WATER = 0xFFBDE5DF
TIRE = 0xFF3A3936

def brain(c, x, y, s=1.0):
    cloud(c, x, y, 330 * s, 215 * s, fill=WASH_P, w=10)
    for k, (dx, dy) in enumerate(((-170, -70), (10, -110), (170, -40), (-80, 50))):
        line(c, [(x + (dx - 70) * s, y + dy * s), (x + (dx - 25) * s, y + (dy - 34) * s), (x + (dx + 20) * s, y + (dy + 6) * s), (x + (dx + 70) * s, y + (dy - 26) * s)], CORAL, 8, amp=.8, curve=True)

def finger(c, x, y, s=1.0, wr=0.0, alpha=1.0):
    """parmak ucu (ic yuz), yukari bakar; wr 0-1: burusukluk"""
    hw = 90 * s
    pts = [(x - hw, y + 260 * s), (x - hw, y - 110 * s)]
    for i in range(1, 8):
        a = math.pi - math.pi * i / 8
        pts.append((x + hw * math.cos(a), y - 110 * s - hw * math.sin(a)))
    pts += [(x + hw, y - 110 * s), (x + hw, y + 260 * s)]
    line(c, pts, INK, max(5, 9 * s), alpha=alpha, amp=1.2, fill=SKIN)
    if wr > 0:
        for k in (-2, -1, 0, 1, 2):
            ox = k * 31 * s; top = y - (150 - abs(k) * 30) * s; bot = y + 170 * s
            w_ = [(x + ox + 9 * s * math.sin(j * 1.9 + k * 1.3), lerp(top, bot, j / 7)) for j in range(8)]
            line(c, w_, INK, max(3.5, 5.5 * s), wr, .8 * alpha, amp=.6, curve=True)
    else: St.n += 5

def water(c, x0, y0, x1, y1, t, alpha=.82):
    wash(c, x0, y0, x1, y1, WATER, alpha)
    line(c, [(x, y0 + 7 * math.sin(x * .021 + t * 3)) for x in range(int(x0) + 10, int(x1) - 9, 40)], TEAL, 8, amp=.5, curve=True)

def drop(c, x, y, s=1.0, alpha=1.0, col=TEAL):
    p = skia.Path(); p.moveTo(x, y - 24 * s); p.quadTo(x + 17 * s, y + 2 * s, x, y + 14 * s); p.quadTo(x - 17 * s, y + 2 * s, x, y - 24 * s); p.close()
    c.drawPath(p, paint(col, fill=True, alpha=alpha))

def tire(c, x, y, s=1.0):
    """lastik onden: disler"""
    box(c, x - 110 * s, y - 200 * s, x + 110 * s, y + 200 * s, r=56 * s, w=9 * s, fill=TIRE, amp=1)
    for k in range(-3, 4):
        yy = y + k * 52 * s
        line(c, [(x - 76 * s, yy - 16 * s), (x, yy + 18 * s), (x + 76 * s, yy - 16 * s)], BG, 11 * s, amp=.6)

def bowl(c, x, y, wet=False):
    pts = [(x + 135 * math.cos(math.pi * i / 10), y + 95 * math.sin(math.pi * i / 10)) for i in range(11)]
    line(c, pts, INK, 8, amp=1, closed=True, fill=WATER if wet else PAPER, curve=False)
    for dx, dy, col in ((-58, 34, CORAL), (0, 50, YEL), (58, 34, TEAL)):
        circ(c, x + dx, y + dy, 24, color=INK, w=5, fill=col, amp=.6, n=10)

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1)
    tb = cap_start(0, 'buruşur', a0 + .9); th = b1 - .5
    wy = 960
    rise = back(seg(t, .45, .95))
    fx, fy = 540, 800 + 420 * (1 - rise)
    wr = seg(t, .9, max(tb + .3, 1.5))
    c.save(); c.clipRect(skia.Rect.MakeLTRB(0, 0, 1080, 1140))
    for k in range(3):
        ph = (t * 1.1 + k / 3) % 1
        drop(c, fx + (k - 1) * 150 + 20, fy - 60 + ph * 260, 1.3, (1 - ph) * rise)
    with xf(c, fx, fy + 300, 1, 2.5 * math.sin(t * 1.6)): finger(c, fx, fy, 1.3, wr)
    c.restore()
    water(c, 60, wy, 1020, 1150, t)
    if t > tb: qmark(c, 860, 720, 240, t, CORAL, 1.0, pop(t, tb, .3))
    if t > b0 - .05:
        shake = 5 * math.sin(t * 45) if th < t < th + .3 else 0
        with xf(c, 540, 410, pop(t, b0 - .05, .3), -2 + shake): pill(c, 'su çekip şişti?', 540, 410, 56, INK)
        if t > th: cross(c, 540, 410, 2.3, seg(t, th, th + .25))

def scene2(c, t):
    a0, a1 = L(2); d0, d1 = L(3); h0, h1 = L(4)
    ts = cap_start(2, 'sinir', a0 + 1.1); tyz = cap_start(3, 'yüz', d0 + 1.2)
    th = cap_start(4, 'hasarlıysa', h0 + .8); tbm = cap_start(4, 'buruşmuyor', h1 - .9)
    wy = 1045
    nl = [(540, 640), (290, 700), (290, 762)]; nr = [(540, 640), (790, 700), (790, 762)]
    if t > ts:
        pr = seg(t, ts, ts + .5)
        for pts in (nl, nr):
            line(c, pts, INK, 17, pr, amp=.8); St.n -= 1; line(c, pts, YEL, 9, pr, amp=.8)
        for k in range(2):
            ph = (t * .9 + k * .5) % 1
            for pts, ok in ((nl, True), (nr, t < th)):
                if not ok or pr < 1: continue
                u = ph * 2; i = min(1, int(u)); u -= i
                c.drawCircle(lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u), 11, paint(CORAL, fill=True))
    with xf(c, 540, 520, pop(t, a0 - .1, .35)): brain(c, 540, 520, .5)
    if t > ts:
        with xf(c, 540, 372, pop(t, ts, .3)): pill(c, 'sinir sistemi', 540, 372, 44, TEAL, PAPER)
    if t > tyz:
        with xf(c, 850, 452, pop(t, tyz, .3), 5): pill(c, '~100 yıl önce', 850, 452, 38, INK)
    if t > d0 - .1:
        p = pop(t, d0 - .1, .35)
        with xf(c, 290, 1000, p): finger(c, 290, 930, .8, seg(t, h0, h0 + .9))
        with xf(c, 790, 1000, pop(t, d0 + .05, .35)): finger(c, 790, 930, .8, 0)
        water(c, 60, wy, 1020, 1250, t)
    if t > h0:
        with xf(c, 290, 1140, pop(t, h0, .3)): pill(c, 'sinir sağlam', 290, 1140, 40, TEAL, PAPER)
    if t > th:
        cross(c, 665, 670, 1.3, seg(t, th, th + .25))
        with xf(c, 790, 1140, pop(t, th, .3)): pill(c, 'sinir hasarlı', 790, 1140, 40, CORAL, PAPER)
    if t > tbm:
        with xf(c, 540, 1215, pop(t, tbm, .3)):
            txt(c, 'buruşuyor', 290, 1228, 46, TEAL); txt(c, 'buruşmuyor', 790, 1228, 46, CORAL)

def scene3(c, t):
    a0, a1 = L(5); b0, b1 = L(6)
    tsn = cap_start(5, 'sinirlerin', a0 + 1.0); tdm = cap_start(5, 'damarları', a1 - 1.6); tdr = cap_start(5, 'daraltıyor', a1 - .9)
    tk = cap_start(6, 'küçülüyor', b0 + .9); tdd = cap_start(6, 'deri', b0 + 2.0); tkv = cap_start(6, 'kıvrılıyor', b1 - .9)
    cx_, cy_ = 540, 800
    u1 = smooth(seg(t, tdr, tdr + .7)); u2 = smooth(seg(t, tk, tk + .8)); u3 = smooth(seg(t, tkv - .2, tkv + .6))
    rp = lerp(236, 182, u2)
    Rm = lerp(lerp(266, 262, u2), 222, u3); A = 27 * u3
    with xf(c, cx_, cy_, pop(t, a0 - .1, .35)):
        p = skia.Path(); n = 112
        for i in range(n + 1):
            th_ = 2 * math.pi * i / n; r = Rm + A * math.sin(14 * th_)
            q = (cx_ + r * math.cos(th_), cy_ + r * math.sin(th_))
            p.moveTo(*q) if i == 0 else p.lineTo(*q)
        p.close()
        c.drawPath(p, paint(SKIN, fill=True)); c.drawPath(p, paint(INK, 10))
        circ(c, cx_, cy_, rp, color=INK, w=6, fill=PULP, amp=1, n=16)
        rv = lerp(54, 22, u1)
        for k, ang in enumerate((-90, 30, 150)):
            vx, vy = cx_ + rp * .46 * math.cos(math.radians(ang)), cy_ + rp * .46 * math.sin(math.radians(ang))
            circ(c, vx, vy, rv, color=INK, w=6, fill=CORAL, amp=.6, n=10)
            c.drawCircle(vx, vy, rv * .45, paint(0xFFB8402A, fill=True))
    if t > a0 + .3:
        with xf(c, 170, 520, pop(t, a0 + .3, .3), -4): pill(c, 'deri', 170, 520, 42, INK)
        dashes(c, (215, 560), (340, 640), 4, INK, 6, seg(t, a0 + .3, a0 + .5))
    if t > tdm:
        with xf(c, 900, 520, pop(t, tdm, .3), 4): pill(c, 'damar', 900, 520, 42, CORAL, PAPER)
        dashes(c, (850, 560), (600, cy_ - rp * .46 - 30), 5, CORAL, 6, seg(t, tdm, tdm + .2))
    if t > tsn:
        with xf(c, 540, 385, pop(t, tsn, .3)): pill(c, 'sinir: “daral!”', 540, 385, 46, TEAL, PAPER)
        fl = .6 + .4 * math.sin(t * 14)
        z = [(540, 430), (518, 462), (560, 480), (540, 524)]
        line(c, z, INK, 15, seg(t, tsn + .1, tsn + .4), amp=.5); St.n -= 1; line(c, z, YEL, 8, seg(t, tsn + .1, tsn + .4), fl, amp=.5)
    if tk < t <= tdd:
        with xf(c, 540, 1165, pop(t, tk, .3)): pill(c, 'içten küçülüyor', 540, 1165, 48, CORAL, PAPER)
    if t > tdd:
        with xf(c, 540, 1180, pop(t, tdd, .3)):
            box(c, 140, 1128, 940, 1232, r=26, w=8, fill=YEL)
            txt(c, 'deri bol gelip kıvrılıyor', 540, 1198, 52, INK)

def scene4(c, t):
    a0, a1 = L(7); b0, b1 = L(8)
    tac = cap_start(7, 'açıklamaya', a0 + 1.0); tkv = cap_start(7, 'kıvrımlar', a0 + 2.2); tl = cap_start(7, 'lastiğinin', a1 - 1.6)
    tka = cap_start(8, 'kanallardan', b0 + .4); ttu = cap_start(8, 'tutuşu', b1 - 1.1)
    if t < tac + .15: qmark(c, 540, 930, 430, t, CORAL, 1 - seg(t, tac - .1, tac + .15), pop(t, a0 - .1, .3))
    if t > tac:
        with xf(c, 540, 395, pop(t, tac, .3)): pill(c, 'bir açıklamaya göre', 540, 395, 46, INK)
    if t > tkv - .1:
        with xf(c, 300, 800, pop(t, tkv - .1, .35)): finger(c, 300, 790, .95, 1)
        with xf(c, 300, 1095, pop(t, tkv, .3)): pill(c, 'kıvrım', 300, 1095, 40, CORAL, PAPER)
    if t > tl:
        with xf(c, 540, 790, pop(t, tl, .3)): txt(c, '=', 540, 830, 130, INK)
        with xf(c, 780, 790, pop(t, tl + .08, .35)): tire(c, 780, 790, .95)
        with xf(c, 780, 1095, pop(t, tl + .1, .3)): pill(c, 'lastik dişi', 780, 1095, 40, INK)
    if t > tka:
        a = seg(t, tka, tka + .2)
        for k in range(4):
            ph = (t * .8 + k * .27) % 1
            drop(c, 300 + (k - 1.5) * 29.5, 650 + ph * 420, .85, a * (1 - ph ** 3))
            drop(c, 780 + (-1) ** k * (60 + 70 * ph), 640 + ph * 420, .85, a * (1 - ph ** 3))
    if t > ttu:
        with xf(c, 540, 1195, pop(t, ttu, .35), -1.5):
            box(c, 280, 1146, 800, 1246, r=26, w=8, fill=YEL)
            txt(c, 'daha iyi tutuş', 540, 1215, 56, INK)

def scene5(c, t):
    y0_, y1_ = L(9); a0, a1 = L(10); k0, k1 = L(11); s0, s1 = L(12); h0, h1 = L(13)
    st1 = 1 - smooth(seg(t, s0 - .3, s0 - .05))
    if st1 > .01:
        ti = cap_start(10, 'ıslak', a0 + 1.2); thz = cap_start(10, 'hızlı', a1 - 1.0); tf = cap_start(11, 'fark', k1 - .8)
        with xf(c, 540, 800, 1, 0, st1):
            with xf(c, 540, 430, pop(t, y0_ - .1, .35)): txt(c, '2013', 600, 480, 150, CORAL)
            if t > a0 - .1:
                with xf(c, 250, 740, pop(t, a0 - .1, .3)):
                    dip = 26 * math.sin(t * 5)
                    finger(c, 250, 600 + dip, .42, 1)
                    bowl(c, 250, 740, True)
            if t > ti:
                with xf(c, 250, 888, pop(t, ti, .3)): pill(c, 'ıslak bilye', 250, 888, 40, TEAL, PAPER)
            if t > thz:
                arrow(c, (425, 770), (545, 770), INK, 8, seg(t, thz, thz + .2))
                with xf(c, 780, 770, pop(t, thz + .1, .35), -2):
                    box(c, 590, 708, 970, 832, r=28, w=8, fill=YEL)
                    txt(c, 'daha hızlı', 780, 790, 60, INK)
                check(c, 930, 690, 1.3, seg(t, thz + .3, thz + .55))
            if t > k0 - .1:
                with xf(c, 250, 1010, pop(t, k0 - .1, .3)): bowl(c, 250, 1010, False)
                with xf(c, 250, 1160, pop(t, k0, .3)): pill(c, 'kuru bilye', 250, 1160, 40, INK)
            if t > tf:
                arrow(c, (425, 1040), (545, 1040), INK, 8, seg(t, tf, tf + .2))
                with xf(c, 780, 1040, pop(t, tf + .1, .35), 2):
                    box(c, 590, 978, 970, 1102, r=28, w=8, fill=PAPER)
                    txt(c, 'fark yok', 780, 1060, 60, MUTE)
    if t > s0 - .3:
        a = seg(t, s0 - .2, s0 + .1)
        tsn = cap_start(12, 'aynı', s0 + 1.0); thl = cap_start(13, 'hâlâ', h1 - 1.3)
        with xf(c, 540, 800, 1, 0, a):
            with xf(c, 290, 610, pop(t, s0 - .2, .35), -2):
                box(c, 100, 400, 480, 820, r=30, w=9, fill=PAPER)
                txt(c, '2013', 290, 510, 92, INK); check(c, 290, 640, 2.0); txt(c, 'daha hızlı', 290, 770, 46, TEAL)
            if t > s0 + .1:
                with xf(c, 790, 610, pop(t, s0 + .1, .35), 2):
                    box(c, 600, 400, 980, 820, r=30, w=9, fill=PAPER)
                    txt(c, '2014', 790, 510, 92, INK)
                    cross(c, 790, 640, 1.9, seg(t, tsn, tsn + .3))
                    if t > tsn: txt(c, 'aynı sonuç yok', 790, 770, 44, CORAL, alpha=seg(t, tsn, tsn + .2))
            if t > h0 - .1:
                with xf(c, 540, 1120, pop(t, h0 - .1, .3)):
                    me = fig(c, 540, 1120, .6, 0, dict(FRONT, aL=62, eL=150, aR=62, eR=150), 'confused')
                qmark(c, me['top'][0] + 90, me['top'][1] + 80, 100, t, CORAL, 1.0, pop(t, h0 + .1, .3))
            if t > thl:
                with xf(c, 540, 1200, pop(t, thl, .35)):
                    box(c, 190, 1150, 890, 1250, r=26, w=8, fill=YEL)
                    txt(c, 'hâlâ tartışılıyor', 540, 1218, 56, INK)

def scene6(c, t):
    a0, a1 = L(14); d0, d1 = L(15); e0, e1 = L(16)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_T)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    aha = t > d0 - .1
    tp = cap_start(14, 'buruş', a0 + 1.2)
    pose = dict(FRONT, aR=20, eR=150, aL=10, eL=6, tilt=-6 if not aha else 0)
    pose = mix(pose, dict(FRONT, aR=10, eR=6, aL=148, eL=160 + 26 * math.sin(t * 9)), wv)
    me = fig(c, 540, gy, .95, 0, pose, 'confused' if not aha else 'happy')
    hx, hy = me['top']
    if not aha:
        with xf(c, 230, 760, pop(t, a0, .3)):
            box(c, 100, 720, 360, 850, r=44, w=8, fill=PAPER)
            wash(c, 116, 742, 344, 800, WATER, 1, r=16)
            for k, (dx, r_) in enumerate(((-70, 20), (-20, 28), (40, 22), (84, 16))):
                circ(c, 230 + dx, 728 - r_ * .4 + 4 * math.sin(t * 3 + k), r_, color=INK, w=5, fill=PAPER, amp=.6, n=9)
            for sd in (-1, 1): line(c, [(230 + sd * 90, 850), (230 + sd * 100, 880)], INK, 8, amp=.6)
        if t > tp:
            with xf(c, 820, 760, pop(t, tp, .3), 5): finger(c, 820, 740, .6, 1)
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
