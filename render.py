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

TITLE = 'Bulaşıcı Esneme'   # yatay formatta etiketin altinda gorunur
HOOK = 'Esnemek neden bulaşıcı?'         # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['ESNEMEK NEDEN', 'BULAŞICI?']    # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 4.0                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['esnedi,'], 1: ['sen', 'de', 'esniyorsun.'], 2: ['uykun', 'bile', 'yok.'], 3: ['olmuyor.'], 4: ['bulaşıcı', 'esneme.'],
      6: ['esneme', 'videoları'], 7: ['yaklaşık', 'yarısı'], 10: ['aileden', 'arkadaştan,'], 11: ['yabancıdan'],
      13: ['henüz', 'bilinmiyor.'], 15: ['taklit', 'ediyor.'], 16: ['empatiye'], 18: ['çelişkili.'],
      19: ['küçük', 'çocuklara'], 20: ['dört', 'beş', 'yaşından'], 21: ['azalıyor.'], 23: ['esnediysen'],
      24: ['görmek', 'bile', 'yetiyor.']}

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
GY = 1090
EXPR['yawn'] = ('happy', 'none')      # gozler kapali; agzi yawn_mouth cizer

def yw(t, t0, dur=1.7):
    """esneme egri: acil, bekle, kapan (0..1)"""
    return smooth(seg(t, t0, t0 + .4)) * (1 - smooth(seg(t, t0 + dur - .45, t0 + dur)))

def yawn_mouth(c, hc, s, face, u, color=INK):
    mx = hc[0] + (0 if face == 0 else face * 17 * s); my = hc[1] + 21 * s
    rx, ry = 13 * s * (.55 + .45 * u), 18 * s * u
    c.drawOval(skia.Rect.MakeLTRB(mx - rx, my - ry * .8, mx + rx, my + ry * 1.2), paint(color, fill=True))
    if u > .5: c.drawOval(skia.Rect.MakeLTRB(mx - rx * .55, my + ry * .35, mx + rx * .55, my + ry * 1.05), paint(CORAL, fill=True))

def yfig(c, x, gy, s, face, u, pose=None, expr='smile', color=INK, stretch=True):
    """u>0 iken esneyen cizgi adam (kollar yukari gerinir)"""
    base = dict(FRONT if face == 0 else STAND); base.update(pose or {})
    tgt = dict(base, aL=150, eL=168, aR=142, eR=160, tilt=-6) if stretch else dict(base, tilt=-6)
    info = fig(c, x, gy, s, face, mix(base, tgt, u), 'yawn' if u > .2 else expr, color=color)
    if u > .2: yawn_mouth(c, info['head'], s, face, u, color)
    return info

def yface(c, x, y, r, u=1.0, alpha=1.0, color=INK):
    """yuz ikonu: u>0.2 esniyor, degilse gulumsuyor"""
    s = r / 48
    if alpha <= 0.01: return
    if alpha < 1: c.saveLayerAlpha(None, int(clamp(alpha) * 255))
    circ(c, x, y, r, color=color, w=max(4, 9 * s), fill=PAPER, amp=1.2 * s + .3)
    if u > .2:
        for dx in (-16, 16):
            line(c, [(x + (dx - 8) * s, y - 3 * s), (x + dx * s, y - 12 * s), (x + (dx + 8) * s, y - 3 * s)], color, 5 * s, amp=.5, curve=True)
        yawn_mouth(c, (x, y - 4 * s), s, 0, u, color)
    else:
        for dx in (-16, 16): c.drawCircle(x + dx * s, y - 6 * s, 5.5 * s, paint(color, fill=True))
        line(c, [(x - 13 * s, y + 16 * s), (x, y + 26 * s), (x + 13 * s, y + 16 * s)], color, 5 * s, amp=.5, curve=True)
    if alpha < 1: c.restore()

def dots(c, x0, y0, x1, y1, t, alpha=1.0, n=6, arc=46, color=CORAL):
    """bulasma: bir kafadan digerine akan noktalar"""
    if alpha <= 0.01: return
    for k in range(n):
        v = (k + (t * 1.5) % 1) / n
        c.drawCircle(lerp(x0, x1, v), lerp(y0, y1, v) - arc * math.sin(math.pi * v), 8, paint(color, fill=True, alpha=alpha * (1 - .4 * v)))

def eye(c, x, y, s=1.0, tx=None, ty=None, alpha=1.0, color=INK):
    if alpha <= 0.01: return
    circ(c, x, y, 34 * s, 21 * s, color=color, w=6 * s, fill=PAPER, alpha=alpha, amp=.8, n=12)
    dx = dy = 0
    if tx is not None:
        d = math.hypot(tx - x, ty - y) or 1; dx, dy = (tx - x) / d * 12 * s, (ty - y) / d * 6 * s
    c.drawCircle(x + dx, y + dy, 10 * s, paint(color, fill=True, alpha=alpha))

def heart(c, x, y, s=1.0, color=CORAL, alpha=1.0):
    p = skia.Path(); p.moveTo(x, y + 26 * s)
    p.cubicTo(x - 46 * s, y - 6 * s, x - 22 * s, y - 40 * s, x, y - 14 * s)
    p.cubicTo(x + 22 * s, y - 40 * s, x + 46 * s, y - 6 * s, x, y + 26 * s); p.close()
    c.drawPath(p, paint(color, fill=True, alpha=alpha))

def pill(c, s, cx, cy, size=34, col=INK, fg=BG):
    w = tw(s, size); h = size * 1.7
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 26, cy - h / 2, cx + w / 2 + 26, cy + h / 2), h / 2, h / 2), paint(col, fill=True))
    txt(c, s, cx, cy + size * .36, size, fg)

def card(c, cx, cy, w, h, title, col, content, sc=1.0, alpha=1.0, rot=0.0):
    with xf(c, cx, cy, sc, rot, alpha):
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        box(c, x0, y0, x1, y1, r=26, w=8, fill=PAPER)
        wl = tw(title, 32)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - wl / 2 - 24, y0 - 28, cx + wl / 2 + 24, y0 + 28), 28, 28), paint(col, fill=True))
        txt(c, title, cx, y0 + 12, 32, PAPER)
        content(cx, cy)

def scene1(c, t):
    a0, a1 = L(0); b0, b1 = L(1); d0, d1 = L(2)
    ts = cap_start(1, 'sen', b0 + 1.2)
    wash(c, 60, 330, 1020, 1100, WASH_Y)
    ground(c, 50, 1030, GY)
    u1 = max(yw(t, a0 + .1, 1.9), yw(t, ts + .3, 2.8))     # yanindaki: once o esner, sonra zincir surer
    u2 = yw(t, ts, 3.2)
    o = yfig(c, 310, GY, 1.15, 0, u1)
    ex = 'smile' if t < a0 + .7 else ('confused' if t < ts else 'smile')
    me = yfig(c, 770, GY, 1.15, 0, u2, expr=ex)
    da = seg(t, a0 + .7, a0 + 1.0) * (1 - smooth(seg(t, ts + .9, ts + 1.3)))
    dots(c, o['head'][0] + 74, o['head'][1] + 14, me['head'][0] - 74, me['head'][1] + 14, t, da, n=7, arc=56)
    hx, hy = me['top']
    sl = pop(t, a0 + .1, .3) * (1 - smooth(seg(t, d0 - .3, d0 - .1)))
    if sl > 0.01:
        with xf(c, 770, 470, sl):
            pill(c, 'SEN', 770, 440, 44, CORAL, PAPER)
            line(c, [(770, 486), (770, 528)], CORAL, 9, amp=.8)
            line(c, [(752, 510), (770, 532), (788, 510)], CORAL, 9, amp=.8)
    zp = pop(t, d0, .3)
    if zp > 0:
        cx, cy = 770, 440
        with xf(c, cx, cy, zp):
            cloud(c, cx, cy, 170, 96, tail=(hx + 4, hy - 46))
            txt(c, 'Zzz', cx - 4, cy + 26, 84, MUTE)
            cross(c, cx, cy, 1.9, seg(t, d0 + .35, d0 + .7))

def scene2(c, t):
    a0, a1 = L(3); b0, b1 = L(4)
    gy = 1170; x = 540; s = 1.0
    tt = cap_start(4, 'bulaşıcı', b0 + 1.2)
    c.drawOval(skia.Rect.MakeLTRB(x - 170, gy - 16, x + 170, gy + 22), paint(0xFFEDE3D0, fill=True))
    shr = smooth(seg(t, a0, a0 + .35)) * (1 - smooth(seg(t, a1 - .2, a1 + .2)))
    pt = smooth(seg(t, tt - .1, tt + .3))
    pose = mix(FRONT, dict(FRONT, aL=38, eL=118, aR=38, eR=118, tilt=5), shr)
    pose = mix(pose, dict(FRONT, aR=152, eR=168 + 4 * math.sin(t * 6), aL=14, eL=8, tilt=-3), pt)
    ex = 'happy' if (t < a1 + .3 or t > tt) else 'smile'
    info = fig(c, x, gy, s, 0, pose, ex)
    fr = pop(t, a0 + .4, .3) * (1 - smooth(seg(t, tt - .5, tt - .15)))
    if fr > 0.01:
        for k, (fx, fc) in enumerate(((205, 1), (875, -1))):
            with xf(c, fx, gy, fr):
                yfig(c, fx, gy - 8, .62, fc, yw(t, a0 + .7 + k * .5, 1.9))
    if t > tt:
        p = pop(t, tt, .35)
        with xf(c, 540, 460, lerp(.7, 1, p), 0, seg(t, tt, tt + .15)):
            txt(c, 'BULAŞICI', 540, 424, 112, INK)
            txt(c, 'ESNEME', 540, 544, 112, CORAL)
        line(c, [(290, 580), (420, 574), (560, 584), (790, 572)], INK, 10, seg(t, tt + .4, tt + .8), curve=True)
        txt(c, 'gören de esniyor', 540, 638, 38, MUTE, 'med', alpha=seg(t, tt + .7, tt + 1.0))

def scene3(c, t):
    a0, a1 = L(5); b0, b1 = L(6); d0, d1 = L(7); e0 = L(8)[0]; f0 = L(9)[0]; g0 = L(10)[0]; h0, h1 = L(11)
    pa = 1 - smooth(seg(t, e0 - .3, e0 - .05))        # bolum A: Provine deneyi
    pb = smooth(seg(t, e0 - .05, e0 + .25))           # bolum B: yakinlik
    al = seg(t, a0 - .1, a0 + .3)
    if pa > .01:
        with xf(c, 540, 380, 1, 0, al * pa):
            txt(c, 'Robert Provine · 1986', 540, 372, 44, INK, 'bold')
            txt(c, 'Maryland Üniversitesi (UMBC) deneyi', 540, 424, 32, MUTE, 'med')
        with xf(c, 540, 760, 1, 0, pa):
            tv = cap_start(6, 'esneme', b0 + 1.6)
            sp = pop(t, b0, .3)
            if sp > 0:
                with xf(c, 540, 590, sp):
                    line(c, [(540, 700), (540, 742)], INK, 9, amp=1); line(c, [(470, 744), (610, 744)], INK, 9, amp=1)
                    box(c, 385, 478, 695, 702, r=22, w=10, fill=WASH_T)
                    us = 0 if t < tv - .3 else .5 + .5 * math.sin((t - tv) * 3.2 - 1.2)
                    yface(c, 540, 590, 70, max(us, 0))
                    tri = [(404, 500), (404, 528), (428, 514)]
                    line(c, tri, CORAL, 5, closed=True, fill=CORAL, amp=.5)
            tm = cap_start(6, 'dakika', b0 + .9) - .3
            mp = pop(t, tm, .3)
            if mp > 0:
                with xf(c, 800, 520, mp, 8):
                    circ(c, 800, 520, 62, color=INK, w=8, fill=YEL, n=14)
                    txt(c, '5 dk', 800, 536, 40, INK)
            ty_ = cap_start(7, 'yaklaşık', d0 + .9)
            gy = 1060
            for i in range(6):
                vx = 165 + i * 150
                vp = pop(t, b0 + .25 + i * .07, .28)
                if vp <= 0: continue
                yy = i in (0, 2, 5)
                u = yw(t, ty_ + (0, 0, .2, 0, 0, .4)[i], 9) if yy else 0
                with xf(c, vx, gy, vp):
                    yfig(c, vx, gy, .5, 0, u, expr='flat', color=INK)
                if yy and u > .5: line(c, [(vx - 46, gy + 26), (vx + 46, gy + 26)], CORAL, 10, amp=1)
            rp = pop(t, ty_ + .5, .3)
            if rp > 0:
                with xf(c, 540, 1180, rp, -1.5): txt(c, 'yaklaşık yarısı esnedi (%55)', 540, 1194, 44, CORAL)
    if pb > .01:
        with xf(c, 540, 380, 1, 0, pb):
            txt(c, 'Norscia ve Palagi · 2011', 540, 372, 44, INK, 'bold')
            txt(c, 'Pisa Üniversitesi gözlemi', 540, 424, 32, MUTE, 'med')
        txt(c, 'esneme kimden daha çok bulaşıyor?', 540, 520, 36, MUTE, 'med', alpha=pb * seg(t, f0, f0 + .3))
        rows = (('AİLE', .92, CORAL, g0, 3), ('ARKADAŞ', .66, CORAL, cap_start(10, 'arkadaştan', g0 + 1.0), 2),
                ('YABANCI', .2, MUTE, cap_start(11, 'yabancıdan', h0 + .5) - .2, 0))
        for k, (lab, frac, col, tin, nf) in enumerate(rows):
            y = 640 + k * 180
            p = pop(t, tin, .3)
            if p <= 0: continue
            with xf(c, 540, y, lerp(.85, 1, p), 0, seg(t, tin, tin + .15)):
                txt(c, lab, 80, y + 17, 46, INK, align='l')
                box(c, 370, y - 40, 1000, y + 40, r=38, w=8, fill=PAPER)
                fu = smooth(seg(t, tin + .1, tin + .7))
                x1 = 381 + 608 * frac * fu
                if fu > .05: wash(c, 381, y - 29, max(x1, 381 + 58), y + 29, col, r=28)
                for j in range(nf):
                    fx = 381 + 608 * frac - 52 - j * 92
                    yface(c, fx, y, 36, 1.0, alpha=seg(t, tin + .5 + j * .1, tin + .7 + j * .1))
        ep = pop(t, h1 - .5, .3)
        if ep > 0:
            with xf(c, 540, 1180, ep, -1.5): txt(c, 'yakınlık arttıkça daha çok', 540, 1194, 44, CORAL)

def scene4(c, t):
    a0, a1 = L(12); b0, b1 = L(13); d0 = L(14)[0]; e0, e1 = L(15); f0, f1 = L(16); g0 = L(17)[0]; h0, h1 = L(18)
    qp = pop(t, a0, .35)
    if qp > 0:
        with xf(c, 540, 420, lerp(.7, 1, qp), 0, seg(t, a0, a0 + .15)):
            txt(c, 'NEDEN', 480, 462, 124, INK)
        qmark(c, 800, 462, 150, t, CORAL, sc=qp)
    bn = pop(t, cap_start(13, 'henüz', b0 + .7), .3)
    if bn > 0:
        with xf(c, 540, 562, bn, -1.5):
            box(c, 210, 522, 870, 604, r=30, w=7, fill=PAPER, color=MUTE)
            txt(c, 'kesin cevap: henüz yok', 540, 577, 40, INK, 'med')
    te = cap_start(15, 'taklit', e0 + 1.6)
    def c1(cx, cy):
        yface(c, cx - 100, cy - 30, 58, smooth(seg(t, d0 + .4, d0 + .8)))
        yface(c, cx + 100, cy - 30, 58, smooth(seg(t, te - .1, te + .3)))
        ar = seg(t, e0, e0 + .4)
        line(c, [(cx - 30, cy - 30), (cx + 30, cy - 30)], TEAL, 8, ar, amp=.8)
        if ar >= 1: line(c, [(cx + 14, cy - 46), (cx + 32, cy - 30), (cx + 14, cy - 14)], TEAL, 8, amp=.8)
        txt(c, 'gördüğünü taklit', cx, cy + 112, 36, TEAL, alpha=seg(t, te, te + .3))
    dim = 1 - .45 * smooth(seg(t, g0, g0 + .3))
    def c2(cx, cy):
        yface(c, cx - 104, cy - 30, 58, 0)
        yface(c, cx + 104, cy - 30, 58, 0)
        hp = pop(t, cap_start(16, 'empatiye', f0 + 1.0), .3)
        if hp > 0:
            with xf(c, cx, cy - 30, hp * (1 + .08 * math.sin(t * 7))): heart(c, cx, cy - 28, .95)
        txt(c, 'empati', cx, cy + 112, 36, CORAL, alpha=seg(t, f0 + 1.0, f0 + 1.3))
    p1 = pop(t, d0, .3); p2 = pop(t, f0, .3)
    if p1 > 0: card(c, 285, 890, 420, 360, 'FİKİR 1', TEAL, c1, sc=p1)
    if p2 > 0: card(c, 795, 890, 420, 360, 'FİKİR 2', CORAL, c2, sc=p2, alpha=dim)
    st = pop(t, h0 - .05, .3)
    if st > 0:
        with xf(c, 795, 880, st, -9):
            box(c, 640, 836, 950, 924, r=18, w=8, fill=YEL)
            txt(c, 'çelişkili', 795, 897, 50, INK)
    qa = pop(t, g0, .3)
    if qa > 0: qmark(c, 965, 700, 96, t, INK, sc=qa)

def scene5(c, t):
    a0, a1 = L(19); b0, b1 = L(20); d0, d1 = L(21)
    wash(c, 60, 400, 1020, GY, WASH_T)
    ground(c, 50, 1030, GY)
    tk = cap_start(19, 'küçük', a0 + 1.2)
    tb = cap_start(19, 'bulaşmıyor', a1 - .5)
    ua = yw(t, tk - .7, 2.6)
    ad = yfig(c, 190, GY, .9, 1, ua)
    kp = pop(t, tk - .15, .3)
    if kp > 0:
        with xf(c, 440, GY, kp):
            kid = fig(c, 440, GY, .5, -1, dict(STAND), 'happy')
        da = seg(t, tk, tk + .3) * (1 - smooth(seg(t, tb + .5, tb + .9)))
        dots(c, ad['head'][0] + 56, ad['head'][1] + 16, kid['head'][0] - 60, kid['head'][1] - 26, t, da, n=5, arc=30)
        kx, ky = kid['top']
        cross(c, kx - 6, ky - 66, 1.0, seg(t, tb, tb + .3))
    bl = pop(t, a0 + .25, .3) * (1 - seg(t, tk - .5, tk - .3))
    if bl > 0:
        with xf(c, 330, 560, bl): bulb(c, 330, 560, 1.15, t=t)
    # yas grafigi
    ga = seg(t, b0 - .1, b0 + .2)
    if ga > 0:
        line(c, [(610, 560), (610, 990), (1005, 990)], INK, 8, ga, amp=1)
        txt(c, 'bulaşma', 628, 548, 32, MUTE, 'med', align='l', alpha=ga)
        txt(c, 'yaş', 1004, 1046, 34, MUTE, 'med', align='r', alpha=ga)
        pr = .6 * smooth(seg(t, b0 + .2, b0 + 1.3)) + .4 * smooth(seg(t, d0 + .1, d0 + 1.1))
        pts = [(612, 972), (670, 970), (708, 950), (742, 820), (782, 690), (836, 664), (900, 716), (1000, 806)]
        line(c, pts, CORAL, 12, pr, amp=1, curve=True)
        tp = pop(t, cap_start(20, 'yaşından', b0 + .5) - .2, .3)
        if tp > 0:
            line(c, [(736, 978), (736, 1004)], INK, 7, amp=.6)
            with xf(c, 736, 1040, tp): txt(c, '4-5', 736, 1050, 40, INK)
        dp = pop(t, d0 + .9, .3)
        if dp > 0:
            with xf(c, 930, 640, dp):
                line(c, [(900, 610), (960, 668)], MUTE, 8, amp=.8)
                line(c, [(960, 636), (960, 668), (928, 668)], MUTE, 8, amp=.8)

def scene6(c, t):
    a0 = L(22)[0]; b0, b1 = L(23); d0, d1 = L(24); e0, e1 = L(25)
    wash(c, 60, 540, 1020, GY, WASH_Y)
    ground(c, 50, 1030, GY)
    te = cap_start(23, 'esnediysen', b0 + 1.4)
    pt = smooth(seg(t, a0, a0 + .3)) * (1 - smooth(seg(t, te - .25, te)))
    um = yw(t, te, 2.2)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    pose = mix(FRONT, dict(FRONT, aR=118, eR=172, tilt=4), pt)
    pose = mix(pose, dict(FRONT, aR=148, eR=160 + 26 * math.sin(t * 9), aL=12, eL=8), wv)
    info = yfig(c, 540, GY, .92, 0, um, pose=pose, expr='happy')
    gone = 1 - smooth(seg(t, e0 - .3, e0 - .05))
    sp = pop(t, d0, .3)
    if sp > 0 and gone > 0.01:
        for k, (fx, fc) in enumerate(((190, 1), (890, -1))):
            with xf(c, fx, GY, sp, 0, gone):
                yfig(c, fx, GY, .6, fc, yw(t, d0 + .5 + k * .3, 3))
            with xf(c, fx, 730, sp, 0, gone): eye(c, fx, 730, 1.0, 540, 760)
        dots(c, 470, 700, 250, 800, t, gone * seg(t, d0 + .2, d0 + .5), n=4, arc=24)
        dots(c, 610, 700, 830, 800, t, gone * seg(t, d0 + .2, d0 + .5), n=4, arc=24)
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
                              '-c:v', 'libx264', '-crf', '17', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            frame(surface, fi / FPS, k)
            p.stdin.write(surface.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.replace(tmp, out); print('scene', k, f1 - f0, 'frames')
        else: sys.exit(1)
