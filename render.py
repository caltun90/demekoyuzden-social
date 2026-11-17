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

TITLE = 'Sıklık Yanılsaması'   # yatay formatta etiketin altinda gorunur
HOOK = 'Neden hep karşına çıkıyor?'      # dikeyde etiketin altinda surekli gorunen kanca sorusu (en fazla ~26 karakter)
COVER = ['YENİ ÖĞRENDİĞİN', 'NEDEN HEP', 'KARŞINA ÇIKAR?']   # kapak = ilk kare: dev kanca yazisi, 2-3 kisa satir (son satir sari vurgulu)
COVER_AT = 5.6                           # kapakta sahne 1'in hangi ani cizilsin (sn, en carpici kare)
COVER_T = 0.45                           # kapak suresi: ses baslayana kadar (voice_google.LEAD)
HL = {0: ['kelime'], 1: ['karşına'], 3: ['dolu.'], 4: ['değişmedi.'], 5: ['sıklık', 'yanılsaması.'], 6: ["2005'te"], 7: ['zwicky'], 8: ['iki', 'şey'],
      9: ['seçici', 'dikkat.'], 10: ['eler,', 'yakalar.'], 11: ['üç', 'kişiden', 'biri'], 12: ['doğrulama', 'yanlılığı.'], 13: ['"bak', 'yine"'],
      14: ['hiç'], 15: ['hep', 'oradaydı.'], 16: ['yeni'], 17: ['her', 'yerde'], 18: ['demek', 'o', 'yüzden!']}


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
WORD = 'petrikor'

def pill(c, s, cx, cy, size=34, col=INK, fg=BG):
    w = tw(s, size); h = size * 1.7
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2 - 26, cy - h / 2, cx + w / 2 + 26, cy + h / 2), h / 2, h / 2), paint(col, fill=True))
    txt(c, s, cx, cy + size * .36, size, fg)

def brain(c, x, y, s=1.0, label='BEYİN'):
    cloud(c, x, y, 178 * s, 102 * s, fill=WASH_P, w=max(5, 8 * s))
    line(c, [(x - 96 * s, y - 22 * s), (x - 44 * s, y - 50 * s), (x, y - 18 * s), (x + 46 * s, y - 50 * s), (x + 98 * s, y - 22 * s)], MUTE, max(4, 6 * s), curve=True, amp=1)
    if label: txt(c, label, x, y + 46 * s, 44 * s, INK)

def dashes(c, p0, p1, n=7, color=MUTE, w=6, alpha=1.0):
    for k in range(n):
        u0, u1 = k / n, (k + .55) / n
        line(c, [(lerp(p0[0], p1[0], u0), lerp(p0[1], p1[1], u0)), (lerp(p0[0], p1[0], u1), lerp(p0[1], p1[1], u1))], color, w, alpha=alpha, amp=.5)

def wordtag(c, x, y, size=40, word=None):
    """sari vurgulu kelime"""
    word = word or WORD; w = tw(word, size)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - w / 2 - 12, y - size * .86, x + w / 2 + 12, y + size * .3), 10, 10), paint(YEL, fill=True))
    txt(c, word, x, y, size, INK)

def tv(c, x, y, s=1.0):
    line(c, [(x - 36 * s, y - 85 * s), (x - 70 * s, y - 132 * s)], INK, 6, amp=.5)
    line(c, [(x + 36 * s, y - 85 * s), (x + 70 * s, y - 132 * s)], INK, 6, amp=.5)
    box(c, x - 125 * s, y - 85 * s, x + 125 * s, y + 85 * s, r=20 * s, w=8, fill=PAPER)
    line(c, [(x - 60 * s, y + 104 * s), (x + 60 * s, y + 104 * s)], INK, 8, amp=.5)
    txt(c, 'dizi', x, y - 36 * s, 28 * s, MUTE, 'med')
    wordtag(c, x, y + 30 * s, 40 * s)

def paper(c, x, y, s=1.0):
    box(c, x - 120 * s, y - 100 * s, x + 120 * s, y + 100 * s, r=8 * s, w=8, fill=PAPER)
    txt(c, 'HABER', x, y - 52 * s, 34 * s, INK)
    line(c, [(x - 96 * s, y - 36 * s), (x + 96 * s, y - 36 * s)], INK, 5, amp=.6)
    wordtag(c, x, y + 16 * s, 40 * s)
    for k in range(2): line(c, [(x - 96 * s, y + (50 + k * 24) * s), (x + (96 - k * 50) * s, y + (50 + k * 24) * s)], MUTE, 5, amp=.6)

def sign(c, x, y, gy, s=1.0):
    line(c, [(x, gy), (x, y + 44 * s)], INK, 9, amp=.6)
    box(c, x - 125 * s, y - 46 * s, x + 125 * s, y + 46 * s, r=14 * s, w=8, fill=WASH_T)
    wordtag(c, x, y + 14 * s, 40 * s)

def car(c, x, gy, s=1.0, fill=CORAL, alpha=1.0):
    with xf(c, x, gy, 1, 0, alpha):
        line(c, [(x - 64 * s, gy - 54 * s), (x - 40 * s, gy - 98 * s), (x + 34 * s, gy - 98 * s), (x + 64 * s, gy - 54 * s)], INK, max(4, 7 * s), closed=True, fill=PAPER, amp=.8)
        box(c, x - 110 * s, gy - 58 * s, x + 110 * s, gy - 14 * s, r=16 * s, w=max(4, 7 * s), fill=fill, amp=.8)
        for sd in (-1, 1): circ(c, x + sd * 62 * s, gy - 14 * s, 20 * s, color=INK, w=max(4, 6 * s), fill=PAPER, n=10, amp=.5)

def scene1(c, t):
    a0 = L(0)[0]; a1 = L(1)[1]; b0 = L(2)[0]; b1 = L(3)[1]
    gy = 1200
    wash(c, 60, 340, 1020, gy + 30, WASH_Y)
    ground(c, 60, 1020, gy)
    sw = smooth(seg(t, b0 - .3, b0 + .05))          # kelime -> araba
    te = L(1)[0]; th = cap_start(1, 'haberde', a0 + 3.4); ts = cap_start(1, 'sokakta', a0 + 4.2)
    td = lerp(te, th, .45)
    tsi = L(3)[0]
    # yollar ve arabalar (ikinci cumle)
    if sw > 0.01:
        cp = seg(t, tsi - .1, tsi + .2)
        for ry in (540, 720):
            line(c, [(70, ry), (1010, ry)], MUTE, 6, alpha=sw * cp, amp=1.2)
        for k, (cx, ry, d) in enumerate(((190, 540, 0), (520, 540, .12), (850, 540, .24), (300, 720, .18), (790, 720, .3))):
            p = pop(t, tsi + d, .3)
            if p > 0:
                dx = 26 * (t - tsi) * (1 if ry == 540 else -1)
                with xf(c, cx + dx, ry, p): car(c, cx + dx, ry, .72)
        # dusunce balonu: goz koydugu araba
        ca = sw * (1 - seg(t, tsi - .25, tsi))
        if ca > 0.01:
            with xf(c, 540, 600, pop(t, b0 - .1, .3), 0, ca):
                cloud(c, 540, 580, 210, 120, tail=(560, 770))
                car(c, 540, 640, .85)
    expr = 'smile' if t < td else ('oh' if t < b0 - .2 else ('happy' if t < tsi else 'oh'))
    pose = mix(dict(FRONT, aR=30, eR=120, aL=30, eL=120), dict(FRONT, aR=110, eR=150, aL=110, eL=150), smooth(seg(t, td - .1, td + .3)) * (1 - sw))
    pose = mix(pose, dict(FRONT, aR=62, eR=20, aL=62, eL=20), smooth(seg(t, tsi, tsi + .3)))
    me = fig(c, 540, gy, .95, 0, pose, expr)
    hx, hy = me['top']
    if sw < .99:
        wa = 1 - sw
        # yeni ogrenilen kelime: basin ustunde kart
        with xf(c, 540, 650, pop(t, a0 + .5, .3), 0, wa):
            box(c, 380, 590, 700, 706, r=20, w=8, fill=PAPER)
            wordtag(c, 540, 664, 54)
            txt(c, 'yeni kelime', 540, 562, 32, MUTE, 'med')
        if t > td:
            with xf(c, 215, 520, pop(t, td, .3), -4, wa): tv(c, 215, 520)
        if t > th:
            with xf(c, 865, 500, pop(t, th, .3), 5, wa): paper(c, 865, 500)
        if t > ts:
            with xf(c, 870, 900, pop(t, ts, .3), 0, wa): sign(c, 870, 900, gy)
            with xf(c, 215, 930, pop(t, ts + .25, .3), 0, wa):
                speech(c, 80, 870, 350, 980, (330, 1030))
                wordtag(c, 215, 942, 40)
            burst(c, me['head'][0], me['head'][1], 70, 100, 8, CORAL, 7, wa * (1 - seg(t, ts + .7, ts + 1.3)))

def scene2(c, t):
    q0, q1 = L(4); p0, p1 = L(5)
    tn = cap_start(5, 'sıklık', p0 + 1.2)
    ga = 1 - smooth(seg(t, tn - .3, tn))
    gs = lerp(.55, 1, ga)
    gx, gyy = 540, lerp(470, 720, ga)
    with xf(c, gx, gyy, pop(t, q0 - .1, .35) * gs):
        circ(c, gx, gyy, 210, color=INK, w=9, fill=WASH_T, n=18)
        line(c, [(gx - 205, gyy), (gx + 205, gyy)], INK, 6, amp=1)
        for sd in (-1, 1):
            line(c, [(gx + sd * 95 * math.cos(math.radians(a)), gyy + 205 * math.sin(math.radians(a))) for a in range(-90, 91, 20)], INK, 6, curve=True, amp=.6)
            line(c, [(gx - 178, gyy + sd * 104), (gx - 80, gyy + sd * 92), (gx + 80, gyy + sd * 92), (gx + 178, gyy + sd * 104)], INK, 6, curve=True, amp=.6)
    td = cap_start(4, 'değişmedi', q0 + .9)
    if t > td and ga > .01:
        with xf(c, 540, 1040, pop(t, td, .3), 0, ga):
            pill(c, 'dünya aynı', 540, 1040, 46, TEAL, PAPER)
        check(c, 790, 600, 1.6, seg(t, td + .1, td + .45) * float(ga > .5))
    if t > p0 - .1:
        txt(c, 'bunun bir adı var:', 540, 700, 44, MUTE, 'med', alpha=seg(t, p0, p0 + .25))
    if t > tn:
        p = pop(t, tn, .35)
        with xf(c, 540, 900, p):
            box(c, 130, 760, 950, 1050, r=40, w=9, fill=YEL)
            txt(c, 'SIKLIK', 540, 878, 92, INK)
            txt(c, 'YANILSAMASI', 540, 990, 92, INK)
        txt(c, 'diğer adı: Baader-Meinhof olgusu', 540, 1150, 36, MUTE, 'med', alpha=seg(t, tn + .5, tn + .9))

def scene3(c, t):
    y0_, y1_ = L(6); z0, z1 = L(7); i0, i1 = L(8)
    with xf(c, 540, 440, pop(t, y0_ - .1, .35)):
        txt(c, '2005', 540, 490, 150, CORAL)
    if t > z0 - .1:
        with xf(c, 540, 660, pop(t, z0 - .1, .35)):
            box(c, 190, 580, 890, 760, r=30, w=8, fill=PAPER)
            txt(c, 'Arnold Zwicky', 540, 664, 64, INK)
            txt(c, 'dilbilimci · Stanford Üniversitesi', 540, 722, 32, MUTE, 'med')
    ta = cap_start(7, 'adı', z1 - 1.0)
    if t > ta:
        with xf(c, 540, 860, pop(t, ta, .3), -2):
            box(c, 250, 810, 830, 910, r=22, w=8, fill=YEL)
            txt(c, 'sıklık yanılsaması', 540, 876, 50, INK)
    tk = cap_start(8, 'iki', i0 + 1.0)
    if t > tk:
        for k, (x, col, lab) in enumerate(((360, TEAL, '1'), (720, CORAL, '2'))):
            p = pop(t, tk + k * .22, .3)
            if p <= 0: continue
            with xf(c, x, 1090, p):
                circ(c, x, 1090, 96, color=INK, w=9, fill=col, n=14)
                txt(c, lab, x, 1128, 108, PAPER)
        txt(c, '+', 540, 1124, 100, INK, alpha=seg(t, tk + .3, tk + .5))

def scene4(c, t):
    s0, s1 = L(9); f0, f1 = L(10); d0, d1 = L(11)
    with xf(c, 540, 400, pop(t, s0 - .1, .35)): pill(c, '1 · SEÇİCİ DİKKAT', 540, 400, 46, TEAL, PAPER)
    fa = 1 - smooth(seg(t, d0 - .3, d0))
    tc = cap_start(10, 'çoğunu', f0 + 1.2); tk = cap_start(10, 'önemli', f0 + 2.4)
    if fa > 0.01 and t > s0 + .4:
        with xf(c, 540, 800, 1, 0, fa * seg(t, s0 + .4, s0 + .8)):
            brain(c, 540, 1090, .85)
            # huni (elek)
            line(c, [(150, 640), (460, 880), (460, 950)], INK, 10, amp=1.4)
            line(c, [(930, 640), (620, 880), (620, 950)], INK, 10, amp=1.4)
            for k in range(14):
                ph = (t * .45 + k * .137) % 1.0
                x0 = 190 + (k * 211) % 700
                x = lerp(x0, lerp(x0, 540, .55), ph); y = lerp(490, 800, ph)
                c.drawCircle(x, y, 17, paint(MUTE, fill=True, alpha=(1 - seg(ph, .7, 1)) * seg(ph, 0, .12) * seg(t, f0 - .1, f0 + .2)))
            if t > tk - .2:
                u = smooth(seg(t, tk - .2, tk + .9))
                yy = lerp(480, 1010, u)
                circ(c, 540, yy, 30, color=INK, w=7, fill=CORAL, n=10, amp=.6)
                if u >= 1: burst(c, 540, 1010, 44, 74, 8, CORAL, 7, 1 - seg(t, tk + .9, tk + 1.6))
            txt(c, 'çoğu elenir', 215, 900, 38, MUTE, 'med', alpha=seg(t, tc, tc + .3))
            txt(c, 'önemli olan', 860, 900, 38, CORAL, alpha=seg(t, tk, tk + .3))
            txt(c, 'geçer', 860, 950, 38, CORAL, alpha=seg(t, tk, tk + .3))
    if t > d0 - .3:
        a = seg(t, d0 - .2, d0 + .15)
        tu = cap_start(11, 'üç', d1 - 2.0); ty = cap_start(11, 'yakalıyor', d1 - .9)
        tad = cap_start(11, 'adı', d0 + 2.2)
        with xf(c, 540, 800, 1, 0, a):
            txt(c, 'dinlemediği konuşma', 540, 520, 36, MUTE, 'med')
            speech(c, 210, 550, 870, 680, (540, 740))
            f = font(50); parts = [('bla bla ', MUTE), ('ADIN', CORAL if t > tad else MUTE), (' bla bla', MUTE)]
            x = 540 - sum(f.measureText(s) for s, _ in parts) / 2
            for s_, col in parts:
                if s_ == 'ADIN' and t > tad:
                    w_ = f.measureText(s_)
                    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 8, 588, x + w_ + 8, 650), 10, 10), paint(YEL, fill=True))
                c.drawString(s_, x, 634, f, paint(col, fill=True)); x += f.measureText(s_)
            gy = 1230
            for k, x in enumerate((250, 540, 830)):
                hit = k == 1 and t > ty
                p = pop(t, tu + k * .12, .3) if t > tu else 0
                if p <= 0: continue
                with xf(c, x, gy, p):
                    me = fig(c, x, gy, .66, 0, dict(FRONT, aR=120, eR=165, aL=120, eL=165) if hit else None, 'oh' if hit else 'flat', color=CORAL if hit else INK)
                if hit:
                    burst(c, me['head'][0], me['head'][1], 50, 76, 8, CORAL, 6, 1 - seg(t, ty + .7, ty + 1.3))
            if t > tu:
                with xf(c, 540, 830, pop(t, tu, .3)): pill(c, '3 kişiden 1’i', 540, 830, 44, CORAL, PAPER)

def scene5(c, t):
    s0, s1 = L(12); b0, b1 = L(13); g0, g1 = L(14); y0_ = L(15)[0]; y1_ = L(16)[1]
    with xf(c, 540, 400, pop(t, s0 - .1, .35)): pill(c, '2 · DOĞRULAMA YANLILIĞI', 540, 400, 42, CORAL, PAPER)
    fa = 1 - smooth(seg(t, y0_ - .3, y0_))
    if fa > 0.01:
        with xf(c, 540, 800, 1, 0, fa):
            line(c, [(540, 500), (540, 1200)], MUTE, 5, seg(t, s0 + .5, s0 + 1.0), amp=1.5)
            # sol: gordugun anlar sayilir
            txt(c, 'gördüğün', 280, 540, 44, TEAL, alpha=seg(t, s0 + .7, s0 + 1.0))
            txt(c, 'görmediğin', 800, 540, 44, MUTE, alpha=seg(t, s0 + 1.0, s0 + 1.3))
            if t > b0 - .1:
                tb = cap_start(13, 'bak', b0 + 1.0)
                n = 0
                for k in range(6):
                    at = b0 + .2 + k * .32
                    if t > at:
                        check(c, 130 + (k % 3) * 150, 660 + (k // 3) * 130, 1.25, seg(t, at, at + .25)); n += 1
                if t > tb:
                    with xf(c, 280, 1000, pop(t, tb, .3), -3):
                        speech(c, 110, 930, 450, 1050, (300, 1110))
                        txt(c, 'bak yine!', 280, 1008, 52, INK)
                txt(c, 'sayılır', 280, 1190, 40, TEAL, alpha=seg(t, tb + .3, tb + .6))
            # sag: gormedigin anlar sayilmaz
            if t > g0 - .1:
                for k in range(42):
                    at = g0 + .2 + k * .03
                    if t > at:
                        c.drawCircle(625 + (k % 7) * 58, 630 + (k // 7) * 68, 15, paint(MUTE, fill=True, alpha=.55 * seg(t, at, at + .15)))
                tz = cap_start(14, 'hiç', g1 - 1.0)
                if t > tz:
                    with xf(c, 800, 1130, pop(t, tz, .3)): pill(c, 'sayılmaz', 800, 1130, 44, INK, BG)
                    cross(c, 980, 1070, .9, seg(t, tz + .15, tz + .5))
    if t > y0_ - .3:
        a = seg(t, y0_ - .2, y0_ + .15)
        th = cap_start(15, 'hep', y0_ + .9); tsd = L(16)[0]
        with xf(c, 540, 800, 1, 0, a):
            with xf(c, 540, 700, pop(t, y0_ - .1, .35)):
                box(c, 250, 600, 830, 790, r=30, w=9, fill=PAPER)
                wordtag(c, 540, 726, 96)
            if t > th:
                with xf(c, 540, 900, pop(t, th, .3)): pill(c, 'hep oradaydı', 540, 900, 50, TEAL, PAPER)
            if t > tsd:
                with xf(c, 540, 510, pop(t, tsd, .3)): bulb(c, 540, 500, 1.0, t=t)
                txt(c, 'sen yeni fark ettin', 540, 1080, 60, CORAL, alpha=seg(t, tsd, tsd + .3))

def scene6(c, t):
    a0, a1 = L(17); d0, d1 = L(18); e0, e1 = L(19)
    gy = 1200
    wash(c, 60, 560, 1020, gy, WASH_Y)
    ground(c, 50, 1030, gy)
    wv = smooth(seg(t, e0 - .1, e0 + .3))
    pose = dict(FRONT, aR=110, eR=150, aL=110, eL=150)
    pose = mix(pose, dict(FRONT, aR=148, eR=160 + 26 * math.sin(t * 9)), wv)
    me = fig(c, 540, gy, .95, 0, pose, 'oh' if t < d0 - .1 else 'happy')
    hx, hy = me['top']
    wa = 1 - seg(t, d0 - .3, d0 - .1)
    if wa > 0:
        for k, (x, y, r) in enumerate(((210, 760, -6), (870, 740, 6), (540, 450, 0), (230, 1010, 4), (860, 1000, -4))):
            p = pop(t, a0 + .2 + k * .35, .3)
            if p <= 0: continue
            with xf(c, x, y, p, r, wa):
                box(c, x - 130, y - 50, x + 130, y + 50, r=18, w=7, fill=PAPER)
                wordtag(c, x, y + 14, 42)
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
