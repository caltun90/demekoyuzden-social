"""Demek O Yuzden uzun video #1: Bir gunde beyninin sana oynadigi 6 oyun. Yatay 1920x1080, tam genislik.

  python3 uzun.py still <klasor> 5 30 ...      -> kare kontrolu
  python3 uzun.py part <bas_sn> <bit_sn> <ad>  -> parca video (sessiz)
  python3 uzun.py join <cikti.mp4> parca1 ...  -> birlestir + ses (voice/mix.wav)
"""
import os, sys, math, json, subprocess
os.environ['FMT'] = 'h'
import numpy as np, skia
import render as R
from render import (line, circ, box, wash, txt, tw, font, xf, pop, seg, smooth, lerp, back, fig, paint, clamp,
                    INK, CORAL, TEAL, YEL, MUTE, PAPER, BG, WASH_Y, WASH_T, WASH_P)
from senaryo import LINES as SL

W, H, FPS = 1920, 1080, 30
D = json.load(open('voice/final.json'))
TOTAL = D['total']; LN = D['lines']; BT = {k: tuple(v) for k, v in D['beats'].items()}
SCN = {int(k): v for k, v in D['scenes'].items()}
LID = {l['id']: l for l in LN}
GY = 820
SKY = 0xFFE9F1F6

def S(i): return LID[i]['start']
def E(i): return LID[i]['end']
def B(n): return BT[n]
def at(i, f): return S(i) + (E(i) - S(i)) * f
def span(k):
    ks = sorted(SCN); n = ks.index(k)
    return SCN[k], (SCN[ks[n + 1]] if n + 1 < len(ks) else TOTAL)

CH = {1: ('07:30', 'Kapı Eşiği Etkisi', 'SABAH'), 2: ('09:30', 'Sahne Işığı Etkisi', 'İŞ YERİ'), 3: ('11:00', 'Dilimin Ucunda Hissi', 'TOPLANTI'),
      4: ('14:00', 'Bulaşıcı Esneme', 'ÖĞLEDEN SONRA'), 5: ('16:00', 'Anlamsal Doygunluk', 'SUNUM'), 6: ('23:00', 'Yarım Kalan İşler', 'GECE')}
NAMED = {1: 'k3', 2: 's3', 3: 'd3', 4: 'e3', 5: 'a3', 6: 'z3'}


# ---------- kucuk yardimcilar ----------
def pill(c, s, cx, cy, size=30, col=INK, fg=BG, alpha=1.0, align='c'):
    w = tw(s, size); h = size * 1.75
    x0 = cx - w / 2 - size * .8 if align == 'c' else cx
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, cy - h / 2, x0 + w + size * 1.6, cy + h / 2), h / 2, h / 2), paint(col, fill=True, alpha=alpha))
    txt(c, s, x0 + w / 2 + size * .8, cy + size * .36, size, fg, alpha=alpha)
    return x0 + w + size * 1.6

def hl_text(c, s, x, y, size, color=INK, hl=(), align='c', alpha=1.0):
    """kelime kelime yazar, hl'deki kelimelerin arkasina sari vurgu"""
    f = font(size); sp = f.measureText(' ') * 1.05; ws = s.split(); wd = [f.measureText(w) for w in ws]
    tot = sum(wd) + sp * (len(ws) - 1); x = x - tot / 2 if align == 'c' else x
    for w_, ww in zip(ws, wd):
        if w_ in hl:
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 10, y - size * .84, x + ww + 10, y + size * .26), 12, 12), paint(YEL, fill=True, alpha=alpha))
        c.drawString(w_, x, y, f, paint(color, fill=True, alpha=alpha)); x += ww + sp

def bars(c, x0, y0, items, t, t0, w=520, h=56, gap=44):
    """items: [(etiket, oran 0..1, renk, deger yazisi)]"""
    for n, (lab, v, col, vt) in enumerate(items):
        y = y0 + n * (h + gap + 40)
        txt(c, lab, x0, y, 34, INK, 'med', align='l')
        u = back(seg(t, t0 + .2 + n * .5, t0 + .9 + n * .5))
        box(c, x0, y + 16, x0 + w, y + 16 + h, r=14, w=6, fill=PAPER, color=MUTE)
        if u > 0:
            ww = max(28, w * v * clamp(u, 0, 1.08))
            box(c, x0, y + 16, x0 + ww, y + 16 + h, r=14, w=6, fill=col, color=INK)
            txt(c, vt, x0 + w + 24, y + 16 + h * .72, 40, col, align='l', alpha=seg(t, t0 + .6 + n * .5, t0 + .9 + n * .5))

def stamp(c, s, x, y, t, t0, col=CORAL, rot=-8, size=56):
    p = pop(t, t0, .3)
    if p <= 0: return
    with xf(c, x, y, lerp(1.6, 1, p), rot, seg(t, t0, t0 + .12)):
        w = tw(s, size)
        box(c, x - w / 2 - 28, y - size * .95, x + w / 2 + 28, y + size * .45, r=14, w=8, color=col)
        txt(c, s, x, y, size, col)

def countdown(c, x, y, t, t0, n=3):
    u = t - t0
    if u < 0 or u > n: return
    k = n - int(u); fr = u - int(u)
    circ(c, x, y, 70, color=MUTE, w=8, amp=1)
    pth = skia.Path(); pth.addArc(skia.Rect.MakeLTRB(x - 70, y - 70, x + 70, y + 70), -90, 360 * (1 - fr))
    c.drawPath(pth, paint(CORAL, 12))
    txt(c, str(k), x, y + 30, 86, INK)

def clockface(c, x, y, r, hours, alpha=1.0, fill=PAPER):
    circ(c, x, y, r, color=INK, w=10, fill=fill, alpha=alpha, amp=1.5, n=18)
    for k in range(12):
        a = k * math.pi / 6; rr = r * .8
        c.drawCircle(x + math.sin(a) * rr, y - math.cos(a) * rr, 6 if k % 3 else 10, paint(INK, fill=True, alpha=alpha))
    am = (hours % 1) * 2 * math.pi; ah = (hours % 12) / 12 * 2 * math.pi
    line(c, [(x, y), (x + math.sin(ah) * r * .5, y - math.cos(ah) * r * .5)], INK, 14, alpha=alpha, amp=.6)
    line(c, [(x, y), (x + math.sin(am) * r * .74, y - math.cos(am) * r * .74)], CORAL, 9, alpha=alpha, amp=.6)
    c.drawCircle(x, y, 12, paint(INK, fill=True, alpha=alpha))

def sun(c, x, y, r, t, col=YEL):
    circ(c, x, y, r, color=INK, w=7, fill=col, amp=1)
    for k in range(8):
        a = k * math.pi / 4 + t * .4
        line(c, [(x + math.cos(a) * (r + 16), y + math.sin(a) * (r + 16)), (x + math.cos(a) * (r + 40), y + math.sin(a) * (r + 40))], INK, 6, amp=.6)

def moon(c, x, y, r):
    p = skia.Path(); p.addCircle(x, y, r); q = skia.Path(); q.addCircle(x + r * .45, y - r * .25, r * .9)
    m = skia.Op(p, q, skia.PathOp.kDifference_PathOp)
    c.drawPath(m, paint(YEL, fill=True)); c.drawPath(m, paint(INK, 7))

def envelope(c, x, y, s=1.0, alpha=1.0):
    box(c, x - 70 * s, y - 46 * s, x + 70 * s, y + 46 * s, r=8, w=7, fill=PAPER, alpha=alpha)
    line(c, [(x - 70 * s, y - 44 * s), (x, y + 6 * s), (x + 70 * s, y - 44 * s)], INK, 7, alpha=alpha, amp=1)

def cone(c, x, top, gy, w0=40, w1=230, alpha=0.4):
    p = skia.Path(); p.moveTo(x - w0, top); p.lineTo(x + w0, top); p.lineTo(x + w1, gy); p.lineTo(x - w1, gy); p.close()
    c.drawPath(p, paint(YEL, fill=True, alpha=alpha))

def yawn_mouth(c, head, hr, open_=1.0, face=0):
    x, y = head[0] + (17 * hr / 48 * face if face else 0), head[1] + hr * .42
    c.drawOval(skia.Rect.MakeLTRB(x - hr * .2, y - hr * .18 * open_, x + hr * .2, y + hr * .36 * open_), paint(INK, fill=True))

def bed(c, x, gy, w=520):
    box(c, x, gy - 120, x + w, gy - 40, r=18, w=8, fill=PAPER)
    box(c, x - 6, gy - 230, x + 40, gy, r=10, w=8, fill=WASH_P)
    box(c, x + 60, gy - 150, x + 190, gy - 110, r=18, w=6, fill=PAPER)
    line(c, [(x + 20, gy - 40), (x + 20, gy)], INK, 8); line(c, [(x + w - 20, gy - 40), (x + w - 20, gy)], INK, 8)

def table(c, x0, x1, y):
    line(c, [(x0, y), (x1, y)], INK, 10, amp=1.2)
    line(c, [(x0 + 30, y), (x0 + 30, GY)], INK, 8); line(c, [(x1 - 30, y), (x1 - 30, GY)], INK, 8)

def tshirt(c, head, hr, s=1.0, col=CORAL, mark=True):
    x, y = head[0], head[1] + hr + 30 * s
    p = [(x - 60 * s, y), (x - 110 * s, y + 40 * s), (x - 90 * s, y + 80 * s), (x - 56 * s, y + 62 * s), (x - 56 * s, y + 170 * s),
         (x + 56 * s, y + 170 * s), (x + 56 * s, y + 62 * s), (x + 90 * s, y + 80 * s), (x + 110 * s, y + 40 * s), (x + 60 * s, y)]
    line(c, p, INK, 7, closed=True, fill=col, amp=1)
    if mark: circ(c, x, y + 90 * s, 30 * s, color=INK, w=5, fill=YEL, amp=.8)

# ---------- 6 oyunun simgeleri ----------
def icon(c, k, x, y, s=1.0, t=0.0, alpha=1.0, hi=False):
    if hi: c.drawCircle(x, y, 110 * s, paint(YEL, fill=True, alpha=alpha))
    circ(c, x, y, 96 * s, color=INK, w=7, fill=PAPER if not hi else 0xFFFFF4CC, alpha=alpha, amp=1)
    if k == 1:
        line(c, [(x - 34 * s, y + 52 * s), (x - 34 * s, y - 56 * s), (x + 34 * s, y - 56 * s), (x + 34 * s, y + 52 * s)], INK, 8, alpha=alpha, amp=1)
        line(c, [(x + 34 * s, y - 56 * s), (x + 58 * s, y - 44 * s), (x + 58 * s, y + 60 * s), (x + 34 * s, y + 52 * s)], INK, 6, alpha=alpha, amp=1, closed=True, fill=WASH_T)
    elif k == 2:
        p = skia.Path(); p.moveTo(x - 14 * s, y - 70 * s); p.lineTo(x + 14 * s, y - 70 * s); p.lineTo(x + 56 * s, y + 50 * s); p.lineTo(x - 56 * s, y + 50 * s); p.close()
        c.drawPath(p, paint(YEL, fill=True, alpha=alpha)); circ(c, x, y + 12 * s, 22 * s, color=INK, w=6, fill=PAPER, alpha=alpha, amp=.6)
        line(c, [(x, y + 34 * s), (x, y + 60 * s)], INK, 6, alpha=alpha, amp=.5)
    elif k == 3:
        txt(c, 'S _ _', x, y + 26 * s, 50 * s, INK, alpha=alpha)
        txt(c, '?', x + 40 * s, y - 24 * s, 46 * s, CORAL, alpha=alpha)
    elif k == 4:
        circ(c, x, y, 52 * s, color=INK, w=7, fill=PAPER, alpha=alpha, amp=.8)
        line(c, [(x - 30 * s, y - 14 * s), (x - 12 * s, y - 10 * s)], INK, 6, alpha=alpha, amp=.5); line(c, [(x + 12 * s, y - 10 * s), (x + 30 * s, y - 14 * s)], INK, 6, alpha=alpha, amp=.5)
        c.drawOval(skia.Rect.MakeLTRB(x - 14 * s, y + 4 * s, x + 14 * s, y + 38 * s), paint(INK, fill=True, alpha=alpha))
    elif k == 5:
        for n, ch in enumerate('RAPOR'):
            with xf(c, x - 52 * s + n * 26 * s, y + 6 * s, 1, 14 * math.sin(n * 2.1 + t * 3), alpha):
                txt(c, ch, x - 52 * s + n * 26 * s, y + 18 * s, 38 * s, INK)
    elif k == 6:
        envelope(c, x, y - 4 * s, .62 * s, alpha)
        box(c, x - 48 * s, y + 44 * s, x + 48 * s, y + 60 * s, r=6, w=4, fill=PAPER, alpha=alpha)
        box(c, x - 48 * s, y + 44 * s, x, y + 60 * s, r=6, w=4, fill=CORAL, alpha=alpha)

ICON_NAMES = {1: 'Kapı eşiği', 2: 'Sahne ışığı', 3: 'Dilimin ucu', 4: 'Esneme', 5: 'Doygunluk', 6: 'Yarım iş'}

def icon_row(c, t, t0=None, hi=None, y=470, s=0.95, labels=True, only=None, gap=290):
    for k in range(1, 7):
        x = 960 + (k - 3.5) * gap
        a = 1.0 if t0 is None else pop(t, t0 + (k - 1) * .18, .3)
        if only is not None and k > only: continue
        if a <= 0: continue
        with xf(c, x, y, a * (1.12 if hi == k else 1)):
            icon(c, k, x, y, s, t, hi=hi == k)
        if labels: txt(c, ICON_NAMES[k], x, y + 150 * s, 30, INK if hi in (None, k) else MUTE, 'med')


# ---------- panel tipleri ----------
def p_clock(k):
    hh, name, lab = CH[k]; h0 = [7.0, 7.5, 9.5, 11.0, 14.0, 16.0][k - 1]
    hm = int(hh[:2]) + int(hh[3:]) / 60
    def draw(c, t, t0):
        u = smooth(seg(t, t0, t0 + 1.4)); hrs = lerp(h0, hm, u)
        night = k == 6
        if night: c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), paint(0xFF2E3550, fill=True, alpha=.12))
        clockface(c, 700, 470, 230, hrs)
        if night: moon(c, 1460, 250, 70)
        else: sun(c, 1500, 250, 60, t)
        a = seg(t, t0 + .3, t0 + .8)
        txt(c, hh, 1300, 520, 170, INK, alpha=a)
        pill(c, f'{k}. OYUN · {lab}', 1300, 640, 34, CORAL, PAPER, alpha=a)
    return draw

def p_name(k, art=None):
    hh, name, lab = CH[k]
    def draw(c, t, t0):
        p = pop(t, t0 + .1, .35)
        txt(c, 'BUNUN ADI', 960, 290, 44, MUTE, 'med', alpha=seg(t, t0, t0 + .2))
        with xf(c, 960, 430, lerp(.6, 1, p), 0, seg(t, t0 + .1, t0 + .25)):
            w = tw(name, 120)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(960 - w / 2 - 30, 330, 960 + w / 2 + 30, 470), 24, 24), paint(YEL, fill=True))
            txt(c, name, 960, 440, 120, INK)
        with xf(c, 960, 640, pop(t, t0 + .4, .35)):
            icon(c, k, 960, 640, 1.0, t)
        if art: art(c, t, t0)
    return draw

def p_study(src, place, art):
    def draw(c, t, t0):
        a = seg(t, t0, t0 + .25)
        box(c, 110, 190, 760, 760, r=30, w=8, fill=PAPER, alpha=a)
        pill(c, 'KAYNAK', 435, 250, 30, TEAL, PAPER, alpha=a)
        rows = src if isinstance(src, (list, tuple)) else [src]
        y = 360
        for r_ in rows:
            sz = 50
            while tw(r_, sz) > 600: sz -= 2
            txt(c, r_, 435, y, sz, INK, alpha=a); y += sz * 1.3
        txt(c, place, 435, y + 10, 34, MUTE, 'med', alpha=a)
        art(c, t, t0)
    return draw

def p_matter(head, hl, mood='happy', art=None):
    def draw(c, t, t0):
        a = seg(t, t0, t0 + .25)
        pill(c, 'BU NEDEN ÖNEMLİ?', 960, 240, 46, CORAL, PAPER, alpha=a)
        sz = 64
        while tw(head, sz) > 1500: sz -= 2
        hl_text(c, head, 960, 370, sz, INK, hl, alpha=seg(t, t0 + .3, t0 + .6))
        f = fig(c, 960, GY, .78, 0, dict(R.FRONT, aR=150, eR=170), mood)
        R.check(c, 1180, 560, 1.6, seg(t, t0 + .5, t0 + .9))
        if art: art(c, t, t0)
    return draw

def p_card(title, sub=None, col=INK):
    def draw(c, t, t0):
        p = pop(t, t0 + .05, .4)
        with xf(c, 960, 470, lerp(.7, 1, p), 0, seg(t, t0, t0 + .2)):
            sz = 104
            while tw(title, sz) > 1640: sz -= 4
            txt(c, title, 960, 470, sz, col)
            line(c, [(560, 520), (760, 512), (1160, 524), (1360, 512)], CORAL, 10, seg(t, t0 + .4, t0 + .9), curve=True)
            if sub: txt(c, sub, 960, 610, 48, MUTE, 'med', alpha=seg(t, t0 + .5, t0 + .8))
    return draw


# ============ BOLUM 0: giris ============
def i_alarm(c, t, t0):
    ring = t < S('i1') + 1.2
    jx = (4 if (int(t * 24) % 2) else -4) if ring else 0
    bed(c, 220, GY)
    with xf(c, 1480 + jx, 560, 1, 8 * jx / 4):
        circ(c, 1480, 560, 90, color=INK, w=9, fill=PAPER, amp=1)
        clockface(c, 1480, 560, 70, 7.0)
        for sd in (-1, 1): circ(c, 1480 + sd * 70, 470, 30, color=INK, w=7, fill=CORAL, amp=.8)
        line(c, [(1430, 650), (1410, 680)], INK, 8); line(c, [(1530, 650), (1550, 680)], INK, 8)
    if ring: R.burst(c, 1480, 560, 120, 160, 10, CORAL, 7)
    up = smooth(seg(t, S('i1') + .4, S('i1') + 1.4))
    pose = R.mix(dict(R.FRONT, aL=40, eL=60, aR=40, eR=60), dict(R.FRONT, aL=165, eL=175, aR=165, eR=175), up)
    f = fig(c, 960, GY, 1.05, 0, pose, 'oh' if t < S('i1') + 1 else 'confused')
    if t > at('i1', .55):
        for n in range(6):
            a = pop(t, at('i1', .6) + n * .15, .3)
            if a > 0:
                x = 960 + (n - 2.5) * 130
                with xf(c, x, 200, a): R.qmark(c, x, 240, 90, t + n, CORAL if n % 2 else TEAL)

def i_grid(c, t, t0):
    txt(c, 'HER BİRİNİN BİR ADI VAR', 960, 250, 56, INK, alpha=seg(t, t0, t0 + .3))
    reveal = t >= S('i2b')
    for k in range(1, 7):
        x = 960 + (k - 3.5) * 290; y = 520
        a = pop(t, t0 + .3 + (k - 1) * .2, .3)
        if a <= 0: continue
        with xf(c, x, y, a):
            if reveal: icon(c, k, x, y, .95, t)
            else:
                circ(c, x, y, 92, color=INK, w=7, fill=PAPER, amp=1); txt(c, '?', x, y + 34, 100, MUTE)
        if reveal: txt(c, ['07:30', '09:30', '11:00', '14:00', '16:00', '23:00'][k - 1], x, y + 160, 36, CORAL, alpha=seg(t, S('i2b') + k * .12, S('i2b') + k * .12 + .3))

def i_day(c, t, t0):
    u = smooth(seg(t, t0, E('i3')))
    p = skia.Path(); p.addArc(skia.Rect.MakeLTRB(260, 260, 1660, 1160), 180, 180)
    pa = paint(MUTE, 6); pa.setPathEffect(skia.DashPathEffect.Make([18, 14], 0)); c.drawPath(p, pa)
    for k in range(6):
        a = math.pi + (k + .5) / 6 * math.pi
        x, y = 960 + math.cos(a) * 700, 710 + math.sin(a) * 450
        icon(c, k + 1, x, y, .55, t, alpha=1.0 if u * 6 >= k else .35)
    a = math.pi + u * math.pi
    x, y = 960 + math.cos(a) * 700, 710 + math.sin(a) * 450
    if u < .82: sun(c, x, y - 70, 34, t)
    else: moon(c, x, y - 70, 36)
    fig(c, 960, GY, .85, 0, dict(R.FRONT, aR=150, eR=160), 'happy')

def i_title(c, t, t0):
    p = pop(t, t0 + .05, .45)
    with xf(c, 960, 430, lerp(.6, 1, p), 0, seg(t, t0, t0 + .2)):
        txt(c, 'BEYNİNİN SANA', 960, 380, 110, INK)
        w = tw('OYNADIĞI 6 OYUN', 130)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(960 - w / 2 - 30, 420, 960 + w / 2 + 30, 560), 24, 24), paint(YEL, fill=True))
        txt(c, 'OYNADIĞI 6 OYUN', 960, 530, 130, INK)
    txt(c, 'bir günün hikâyesi', 960, 660, 48, MUTE, 'med', alpha=seg(t, t0 + .6, t0 + 1.0))
    icon_row(c, t, t0 + .8, y=820, s=.5, labels=False, gap=160)


# ============ BOLUM 1: kapi esigi ============
def k_walk(c, t, t0):
    wash(c, 90, 180, 760, GY, WASH_Y); wash(c, 760, 180, 1830, GY, WASH_T)
    R.ground(c, 80, 1840, GY)
    R.door(c, 660, GY, 200, 470, wall_top=180)
    R.fridge(c, 140, GY, 170, 400)
    box(c, 360, GY - 150, 600, GY, r=10, w=8, fill=PAPER); box(c, 400, GY - 190, 470, GY - 150, r=8, w=6, fill=CORAL)
    bed(c, 1300, GY, 480)
    w0, w1 = at('k1', .5), at('k2', .45)
    u = smooth(seg(t, w0, w1)); x = lerp(500, 1180, u)
    if 0 < u < 1: pose = R.walk_pose((x - 500) / 160 * math.pi, 26); ex = 'smile'
    elif u >= 1: pose = dict(R.STAND, aR=118, eR=202, tilt=-8); ex = 'confused'
    else: pose = R.STAND; ex = 'smile'
    f = fig(c, x, GY, 1.0, 1, pose, ex)
    hx, hy = f['top']
    cross_t = w0 + (w1 - w0) * .37
    if t < cross_t + .2 and t > w0 - .6:
        pu = seg(t, cross_t, cross_t + .2)
        with xf(c, hx - 40, hy - 130, lerp(1, 1.3, pu) * pop(t, w0 - .6), 0, 1 - pu):
            R.cloud(c, hx - 40, hy - 130, 100, 70, tail=(hx - 6, hy - 6))
            line(c, [(hx - 80, hy - 120), (hx - 40, hy - 150), (hx, hy - 120)], INK, 7)   # sarj kablosu
            box(c, hx - 100, hy - 140, hx - 72, hy - 108, r=6, w=5, fill=TEAL)
    if cross_t < t < cross_t + .6:
        v = seg(t, cross_t, cross_t + .6); R.burst(c, hx - 40, hy - 130, 60 + 70 * v, 95 + 90 * v, 9, CORAL, 7, 1 - v)
    if t > at('k2', .5): R.qmark(c, hx + 40, hy - 40, 200, t, sc=pop(t, at('k2', .5), .35))

def k_virtual(c, t, t0):
    box(c, 860, 230, 1800, 760, r=24, w=9, fill=0xFF2E3550)
    for n, (x0, x1) in enumerate(((900, 1320), (1340, 1760))):
        wash(c, x0, 280, x1, 700, WASH_T if n else WASH_Y, r=16)
        line(c, [(x0 + 120, 560), (x0 + 300, 560)], INK, 8); box(c, x0 + 180, 500, x0 + 240, 560, r=6, w=5, fill=CORAL)
    line(c, [(1330, 280), (1330, 440)], INK, 8)
    u = (t - t0) % 3 / 3; x = lerp(1000, 1640, smooth(u))
    fig(c, x, 690, .5, 1, R.walk_pose(x / 70, 26), 'smile', hold=lambda h: R.parcel(c, h[0] + 6, h[1] - 4, .55))
    txt(c, 'Sanal odalar', 1330, 820, 40, MUTE, 'med')

def k_bars(c, t, t0):
    txt(c, 'Taşıdığını unutma', 1290, 300, 48, INK)
    bars(c, 900, 400, [('Kapıdan geçince', .78, CORAL, 'daha çok'), ('Aynı odada', .4, TEAL, 'daha az')], t, t0, w=640)

def k_real(c, t, t0):
    for n, x in enumerate((1000, 1420)):
        box(c, x - 170, 300, x + 170, 640, r=16, w=8, fill=WASH_T if n else WASH_Y)
        line(c, [(x - 90, 560), (x + 90, 560)], INK, 8)
        for j in range(3): R.parcel(c, x - 50 + j * 50, 520, .6, fill=[CORAL, TEAL, YEL][j])
    txt(c, 'Gerçek odalar', 1210, 720, 44, INK, 'med')
    stamp(c, 'SONUÇ AYNI', 1210, 260, t, at('k5b', .75), TEAL)

def k_why(c, t, t0):
    arch = smooth(seg(t, at('k6', .55), at('k6', .9)))
    for n, (lab, col) in enumerate((('BÖLÜM: MUTFAK', WASH_Y), ('BÖLÜM: YATAK ODASI', WASH_T))):
        if n == 1 and t < at('k6', .45): continue
        x = 560 if n == 0 else 1360; y = 460
        if n == 0: x, y = lerp(560, 420, arch), lerp(460, 700, arch)
        sc = lerp(1, .55, arch) if n == 0 else pop(t, at('k6', .45), .35)
        with xf(c, x, y, sc, -6 * arch if n == 0 else 0):
            box(c, x - 260, y - 160, x + 260, y + 160, r=24, w=8, fill=col)
            txt(c, lab, x, y + 14, 42, INK)
    if arch > 0:
        line(c, [(120, 880), (720, 880)], INK, 10, arch); txt(c, 'RAF', 420, 940, 34, MUTE, alpha=arch)
    R.door(c, 900, 700, 120, 330, leaf=False, color=CORAL, lw=11)
    if t >= S('k7'):
        line(c, [(1360, 660), (1200, 860), (700, 860)], INK, 8, seg(t, S('k7'), S('k7') + .8), curve=True)
        R.cross(c, 980, 860, 1.4, seg(t, at('k7', .45), at('k7', .6)))
        txt(c, 'Geri dönmek kurtarmadı', 1400, 860, 40, CORAL, alpha=seg(t, at('k7', .45), at('k7', .6)))


# ============ BOLUM 2: sahne isigi ============
def s_spill(c, t, t0):
    wash(c, 90, 180, 1830, GY, 0xFFF1ECE2)
    R.ground(c, 80, 1840, GY)
    for x in (260, 1660):
        box(c, x - 120, 300, x + 120, 520, r=10, w=7, fill=WASH_T)
    spill = t >= at('s1', .62)
    f = fig(c, 960, GY, 1.1, 0, dict(R.FRONT, aR=60, eR=150) if not spill else dict(R.FRONT, aR=50, eR=110, aL=40, eL=80),
            'smile' if not spill else 'oh')
    hx, hy = f['head']
    tshirt(c, (hx, hy), f['hr'], 1.05, PAPER, mark=False)
    hr_ = f['handR']
    with xf(c, hr_[0] + 10, hr_[1] - 20, 1, 0 if not spill else 70 * smooth(seg(t, at('s1', .6), at('s1', .75)))):
        box(c, hr_[0] - 22, hr_[1] - 60, hr_[0] + 30, hr_[1] + 10, r=8, w=6, fill=PAPER)
    if spill:
        st = pop(t, at('s1', .7), .3)
        circ(c, hx + 10, hy + 160, 40 * st, ry=50 * st, color=0xFF7A4E2D, w=0, fill=0xFF8A5A33, amp=2)
    if t >= S('s2'):
        cone(c, 960, 120, GY, 60, 300, .35 * seg(t, S('s2'), S('s2') + .4))
        for n, x in enumerate((420, 600, 1320, 1500)):
            fig(c, x, GY, .62, -1 if x > 960 else 1, R.STAND, 'oh' if t < at('s2', .5) else 'flat')
            if t < at('s2', .5):
                with xf(c, x, 360, pop(t, S('s2') + n * .12, .3)): txt(c, '!', x + (40 if x < 960 else -40), 380, 70, CORAL)

def s_room(c, t, t0):
    R.ground(c, 860, 1820, 760, w=7)
    for j in range(6):
        x = 940 + j * 140
        fig(c, x, 760, .45, 0, R.mix(R.FRONT, dict(R.FRONT, aL=40, eL=90, aR=40, eR=90), 1), 'flat')
        box(c, x - 40, 640, x + 40, 690, r=6, w=5, fill=PAPER)
    u = smooth(seg(t, at('s4', .45), at('s4', .85))); x = lerp(1900, 1320, u)
    f = fig(c, x, 760, .62, -1, R.walk_pose(x / 50, 22) if 0 < u < 1 else R.STAND, 'confused')
    tshirt(c, f['head'], f['hr'], .6, CORAL)

def s_bars1(c, t, t0):
    txt(c, 'Kaç kişi fark etti?', 1290, 290, 48, INK)
    bars(c, 900, 390, [('Giyenin tahmini', .5, CORAL, '~%50'), ('Gerçekte', .23, TEAL, '%23')], t, t0, w=700)

def s_bars2(c, t, t0):
    txt(c, 'Utanç verici olmayan tişört', 1290, 290, 48, INK)
    bars(c, 900, 390, [('Giyenin tahmini', .5, CORAL, '~%50'), ('Gerçekte', .09, TEAL, '<%10')], t, t0, w=700)

def s_why(c, t, t0):
    R.ground(c, 160, 1760, GY)
    if t < S('s6b'):
        for n, x in enumerate((420, 780, 1140, 1500)):
            cone(c, x, 150, GY, 30, 170, .32 * pop(t, t0 + .3 + n * .25, .3))
            fig(c, x, GY, .72, 0, R.FRONT, 'confused' if n == 1 else 'flat')
        txt(c, 'Herkes kendi ışığının altında', 960, 160, 52, INK, alpha=seg(t, at('s6', .6), at('s6', .75)))
    else:
        fig(c, 600, GY, 1.0, 0, R.FRONT, 'smile')
        tshirt(c, (600, GY - 430), 48, 1.0, CORAL)
        clockface(c, 1200, 420, 150, 9.5 + .25 * smooth(seg(t, t0, at('s6b', .6))))
        txt(c, '15 dakika sonra', 1200, 650, 44, INK)
        bars(c, 1000, 720, [('Tahmin', lerp(.5, .3, smooth(seg(t, at('s6b', .4), at('s6b', .8)))), CORAL, 'düşüyor')], t, t0, w=420, h=40)


# ============ BOLUM 3: dilimin ucunda ============
def d_meet(c, t, t0):
    wash(c, 90, 180, 1830, GY, WASH_P); R.ground(c, 80, 1840, GY)
    table(c, 560, 1360, 620)
    u = smooth(seg(t, at('d1', .3), at('d1', .62))); cx = lerp(1900, 1300, u)
    fig(c, cx, GY, 1.0, -1, R.walk_pose(cx / 70, 24) if 0 < u < 1 else dict(R.STAND, aR=60, eR=60), 'smile')
    f = fig(c, 620, GY, 1.0, 1, dict(R.STAND, aR=60, eR=50) if t < at('d1', .7) else dict(R.STAND, aR=118, eR=202, tilt=-6),
            'smile' if t < at('d1', .7) else 'confused')
    hx, hy = f['top']
    if at('d1', .55) < t < S('d2'):
        with xf(c, hx + 160, hy - 120, pop(t, at('d1', .55))):
            R.speech(c, hx + 10, hy - 200, hx + 380, hy - 70, (hx + 40, hy - 20))
            txt(c, 'Merhaba...', hx + 195, hy - 118, 50, INK)
    if t >= S('d2'):
        letters = ['S', '_', '_', '_', '_']
        for n, ch in enumerate(letters):
            a = pop(t, S('d2') + n * .1, .3)
            with xf(c, 820 + n * 90, 290, a): txt(c, ch, 820 + n * 90, 320, 96, CORAL if n == 0 else MUTE)
        if t > at('d2', .2):
            txt(c, 'ilk harf', 1260, 300, 42, TEAL, align='l', alpha=seg(t, at('d2', .2), at('d2', .3))); R.check(c, 1480, 284, .8, seg(t, at('d2', .25), at('d2', .4)))
        if t > at('d2', .5):
            txt(c, 'hece sayısı', 1260, 370, 42, TEAL, align='l', alpha=seg(t, at('d2', .5), at('d2', .6))); R.check(c, 1530, 354, .8, seg(t, at('d2', .55), at('d2', .7)))

def d_tongue(c, t, t0):
    for n, (lang, word) in enumerate((('Türkçe', 'dilimin ucunda'), ('İngilizce', 'tip of the tongue'), ('Fransızca', 'sur le bout de la langue'))):
        a = seg(t, at('d3', .5) + n * .3, at('d3', .5) + n * .3 + .3)
        txt(c, lang, 640, 760 + 0 * n, 0, INK, alpha=0)
        txt(c, f'{lang}: {word}', 960, 820 - (2 - n) * 0 + n * 0, 1, INK, alpha=0)
    # isim kartinin altindaki dil listesi
    for n, (lang, word) in enumerate((('Türkçe', 'dilimin ucunda'), ('İngilizce', 'tip of the tongue'), ('Fransızca', 'sur le bout de la langue'))):
        a = seg(t, at('d3', .45) + n * .25, at('d3', .45) + n * .25 + .3)
        if a > 0: pill(c, f'{lang}: {word}', 960 + (n - 1) * 560, 820, 28, PAPER, INK, alpha=a)

def d_quiz(c, t, t0):
    box(c, 860, 250, 1800, 470, r=24, w=8, fill=PAPER)
    txt(c, '"Denizcilerin yıldızlarla', 1330, 340, 46, INK, 'med')
    txt(c, 'yön bulduğu alet?"', 1330, 410, 46, INK, 'med')
    for n, ch in enumerate('S_______'):
        x = 1000 + n * 76
        txt(c, ch if n == 0 else '_', x, 600, 80, CORAL if n == 0 else MUTE, alpha=pop(t, at('d4', .5) + n * .06, .2))
    a_ = seg(t, at('d4', .75), at('d4', .85))
    txt(c, 'ilk harf', 1120, 720, 44, TEAL, alpha=a_); R.check(c, 1240, 704, .8, a_)
    txt(c, 'hece sayısı', 1450, 720, 44, TEAL, alpha=a_); R.check(c, 1600, 704, .8, a_)

def d_stats(c, t, t0):
    items = [('HAFTADA', '~1 kez', 1050), ('YAŞLA', 'artıyor', 1330), ('EN ÇOK', 'özel isimler', 1610)]
    for n, (a_, b_, x) in enumerate(items):
        p = pop(t, at('d5', .1 + n * .3), .3)
        if p <= 0: continue
        with xf(c, x, 480, p):
            circ(c, x, 480, 125, color=INK, w=8, fill=[WASH_Y, WASH_T, WASH_P][n], amp=1)
            txt(c, a_, x, 455, 30, MUTE, 'med'); txt(c, b_, x, 515, 40 if n < 2 else 32, INK)

def d_bridge(c, t, t0):
    circ(c, 520, 470, 170, color=INK, w=9, fill=WASH_T, amp=1.2); txt(c, 'ANLAM', 520, 488, 60, INK)
    circ(c, 1400, 470, 170, color=INK, w=9, fill=WASH_Y, amp=1.2, alpha=1.0); txt(c, 'SES', 1400, 488, 60, INK)
    fixed = t >= at('d6b', .45)
    pa = paint(INK if fixed else MUTE, 14 if fixed else 9)
    if not fixed: pa.setPathEffect(skia.DashPathEffect.Make([30, 26], (t * 40) % 56))
    p = skia.Path(); p.moveTo(690, 470); p.quadTo(960, 380 + (0 if fixed else 12 * math.sin(t * 9)), 1230, 470); c.drawPath(p, pa)
    if not fixed and t < S('d6b'): R.cross(c, 960, 420, 1.0, seg(t, at('d6', .4), at('d6', .55)))
    if t >= S('d6b'):
        u = smooth(seg(t, at('d6b', .1), at('d6b', .45)))
        with xf(c, lerp(960, 960, u), lerp(760, 420, u), 1):
            pill(c, 'S-', 960, lerp(760, 420, u), 44, CORAL, PAPER)
        if fixed: R.check(c, 960, 260, 1.4, seg(t, at('d6b', .5), at('d6b', .7)))


# ============ BOLUM 4: esneme ============
def e_table(c, t, t0):
    wash(c, 90, 180, 1830, GY, WASH_Y); R.ground(c, 80, 1840, GY)
    table(c, 700, 1220, 640)
    y1 = at('e1', .35); y2 = at('e1', .78)
    def yawning(t1): return seg(t, t1, t1 + .3) * (1 - seg(t, t1 + 1.6, t1 + 1.9))
    a1, a2 = yawning(y1), yawning(y2)
    f1 = fig(c, 560, GY, 1.0, 1, dict(R.STAND, aL=150, eL=170, aR=150, eR=170, tilt=-10) if a1 > .2 else R.STAND, 'flat' if a1 > .2 else 'smile')
    if a1 > .2: yawn_mouth(c, f1['head'], f1['hr'], a1, 1)
    f2 = fig(c, 1360, GY, 1.0, -1, dict(R.STAND, aL=150, eL=170, aR=150, eR=170, tilt=-10) if a2 > .2 else R.STAND, 'flat' if a2 > .2 else 'oh' if t > y1 + .3 else 'smile')
    if a2 > .2: yawn_mouth(c, f2['head'], f2['hr'], a2, -1)
    if t >= S('e2'):
        dim = seg(t, S('e2'), S('e2') + .3)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 900), paint(BG, fill=True, alpha=.82 * dim))
        f = fig(c, 960, GY, 1.15, 0, dict(R.FRONT, aR=100, eR=100), 'oh')
        with xf(c, 960, 300, pop(t, S('e2') + .3, .35)): hl_text(c, 'SEN DE Mİ?', 960, 300, 110, CORAL)

def e_faces(c, t, t0):
    box(c, 880, 220, 1260, 470, r=18, w=8, fill=0xFF2E3550)
    fh = (1070, 345); circ(c, fh[0], fh[1], 80, color=INK, w=7, fill=PAPER, amp=1)
    c.drawOval(skia.Rect.MakeLTRB(1050, 345, 1090, 345 + 50 * (.5 + .5 * math.sin(t * 2.4))), paint(INK, fill=True))
    for n in range(10):
        x = 940 + (n % 5) * 200; y = 600 + (n // 5) * 160
        yn = n in (0, 2, 3, 5, 7, 8) and t > at('e3', .55) + n * .08
        circ(c, x, y, 52, color=INK, w=6, fill=WASH_Y if yn else PAPER, amp=.8)
        if yn: c.drawOval(skia.Rect.MakeLTRB(x - 12, y + 4, x + 12, y + 34), paint(INK, fill=True))
        else: line(c, [(x - 12, y + 18), (x + 12, y + 18)], INK, 5, amp=.4)
    if t > at('e3', .8): stamp(c, '%55', 1720, 340, t, at('e3', .8), CORAL, size=80)
    if t >= S('e3b'):
        c.drawRect(skia.Rect.MakeLTRB(860, 180, 1840, 900), paint(BG, fill=True, alpha=.92 * seg(t, S('e3b'), S('e3b') + .3)))
        box(c, 960, 300, 1300, 620, r=14, w=8, fill=PAPER)
        for j in range(5): line(c, [(1000, 360 + j * 50), (1260 - (j % 2) * 60, 360 + j * 50)], MUTE, 6)
        txt(c, 'esneme...', 1130, 345, 40, CORAL)
        fig(c, 1560, 780, .8, -1, R.STAND, 'flat'); yawn_mouth(c, (1560 - 6, 780 - 8 - 430 * .8 + 30), 48 * .8, .9, -1)
        pill(c, 'Şempanzelerde de görülmüş', 1350, 820, 32, TEAL, PAPER, alpha=seg(t, at('e3b', .6), at('e3b', .7)))

def e_kin(c, t, t0):
    R.ground(c, 880, 1820, GY)
    fig(c, 1000, GY, .8, 1, R.STAND, 'flat'); fig(c, 1180, GY, .8, -1, R.STAND, 'flat')
    if t > t0 + .3:
        p = pop(t, t0 + .3)
        with xf(c, 1090, 330, p):
            for sd in (-1, 1): c.drawCircle(1090 + sd * 16, 322, 20, paint(CORAL, fill=True))
            pth = skia.Path(); pth.moveTo(1054, 330); pth.lineTo(1090, 372); pth.lineTo(1126, 330); pth.close(); c.drawPath(pth, paint(CORAL, fill=True))
    txt(c, 'tanıdık: daha kolay', 1090, 260, 40, INK, alpha=seg(t, t0 + .3, t0 + .6))
    fig(c, 1600, GY, .5, 0, R.FRONT, 'smile')
    pill(c, '4-5 yaşından önce nadir', 1600, 430, 28, PAPER, INK, alpha=seg(t, at('e4', .55), at('e4', .65)))

def e_why(c, t, t0):
    R.qmark(c, 960, 520, 340, t, CORAL)
    if t > at('e5', .55):
        pill(c, 'empati?', 560, 420, 44, PAPER, INK)
        stamp(c, 'TARTIŞMALI', 1380, 460, t, at('e5', .75), CORAL)


# ============ BOLUM 5: anlamsal doygunluk ============
def a_board(c, t, t0):
    box(c, 520, 200, 1640, 720, r=20, w=10, fill=PAPER)
    weird = seg(t, S('a2'), S('a2') + 1.2)
    n_words = min(9, int(seg(t, at('a1', .6), at('a1', 1.0)) * 9) + (1 if t > at('a1', .6) else 0))
    for n in range(n_words):
        x = 760 + (n % 3) * 320; y = 340 + (n // 3) * 130
        for j, ch in enumerate('RAPOR'):
            rot = weird * 26 * math.sin(n * 3.1 + j * 1.7 + t * 2); dy = weird * 12 * math.sin(j + n + t * 3)
            with xf(c, x - 80 + j * 40, y - 20 + dy, 1, rot):
                txt(c, ch, x - 80 + j * 40, y + dy, 58, INK if weird < .5 else CORAL)
    f = fig(c, 380, GY, 1.0, 1, dict(R.STAND, aR=120, eR=120) if weird < .5 else dict(R.STAND, aR=118, eR=202, tilt=-8), 'smile' if weird < .5 else 'confused')
    if weird > .5: R.qmark(c, 460, 220, 140, t)

def a_spoon(c, t, t0):
    t1 = S('a2b'); cnt = int(clamp((t - at('a2b', .5)) / (E('a2b') + 1.4 - at('a2b', .5))) * 20)
    hl_text(c, 'KAŞIK', 960, 470, 220, INK if cnt < 14 else CORAL, ['KAŞIK'] if cnt >= 14 else [])
    if t > at('a2b', .5): txt(c, f'{max(1, cnt)} / 20', 960, 640, 70, MUTE)

def a_meter(c, t, t0):
    hl_text(c, 'RAPOR', 1300, 420, 120, INK)
    u = smooth(seg(t, at('a4', .5), E('a4')))
    txt(c, 'anlam gücü', 1300, 560, 40, MUTE, 'med')
    box(c, 1000, 600, 1600, 660, r=16, w=7, fill=PAPER)
    box(c, 1000, 600, 1000 + 600 * lerp(.92, .35, u), 660, r=16, w=7, fill=TEAL)
    txt(c, f'tekrar: {int(lerp(1, 30, u))}', 1300, 740, 40, INK, alpha=seg(t, at('a4', .5), at('a4', .6)))

def a_rope(c, t, t0):
    hl_text(c, 'KAŞIK', 1080, 500, 96, INK)
    c.drawOval(skia.Rect.MakeLTRB(1600, 400, 1720, 510), paint(PAPER, fill=True)); c.drawOval(skia.Rect.MakeLTRB(1600, 400, 1720, 510), paint(INK, 9))
    line(c, [(1660, 510), (1660, 690)], INK, 14, amp=.6)
    tired = seg(t, at('a5', .4), at('a5', .8))
    pa = paint(MUTE if tired > .5 else INK, lerp(12, 3, tired))
    if tired > .3: pa.setPathEffect(skia.DashPathEffect.Make([lerp(40, 10, tired), lerp(0.1, 24, tired)], 0))
    p = skia.Path(); p.moveTo(1240, 470); p.quadTo(1420, 470 + 140 * tired, 1590, 460); c.drawPath(p, pa)
    if tired > .6: txt(c, 'yoruldu', 1420, 660, 44, CORAL, alpha=seg(t, at('a5', .7), at('a5', .8)))


# ============ BOLUM 6: yarim isler ============
def z_bed(c, t, t0):
    c.drawRect(skia.Rect.MakeLTRB(80, 170, 1840, 900), paint(0xFF2E3550, fill=True, alpha=.10))
    R.ground(c, 80, 1840, GY)
    bed(c, 620, GY, 640)
    with xf(c, 800, GY - 170, 1, -90):
        fig(c, 800, GY - 170 + 230, .62, 0, R.FRONT, 'flat')
    moon(c, 1650, 260, 60)
    if t < S('z2'):
        with xf(c, 1180, 340, pop(t, at('z1', .5))):
            R.cloud(c, 1180, 340, 210, 130, tail=(860, 560))
            envelope(c, 1110, 330, .8)
            box(c, 1190, 360, 1340, 384, r=8, w=5, fill=PAPER); box(c, 1190, 360, 1265, 384, r=8, w=5, fill=CORAL)
    else:
        box(c, 1060, 190, 1640, 620, r=20, w=8, fill=PAPER)
        rows = [('Fatura ödendi', True), ('Market', True), ('E-posta', False), ('Spor', True)]
        for n, (lab, done) in enumerate(rows):
            y = 290 + n * 90; a = seg(t, S('z2') + n * .2, S('z2') + n * .2 + .3)
            if done: R.check(c, 1120, y - 12, .7, a, MUTE); txt(c, lab, 1180, y, 46, MUTE, 'med', align='l', alpha=a)
            else:
                with xf(c, 1300, y - 14, 1, 3 * math.sin(t * 8)):
                    box(c, 1100, y - 40, 1140, y, r=6, w=6, color=CORAL, alpha=a); txt(c, lab, 1180, y, 52, CORAL, align='l', alpha=a)

def z_waiter(c, t, t0):
    R.ground(c, 860, 1820, GY)
    f = fig(c, 1150, GY, .95, 1, dict(R.STAND, aR=100, eR=30), 'smile')
    box(c, f['handR'][0] - 10, f['handR'][1] - 30, f['handR'][0] + 150, f['handR'][1] - 18, r=6, w=6, fill=PAPER)
    paid = t >= at('z3b', .7)
    with xf(c, 1450, 360, 1):
        R.cloud(c, 1450, 360, 200, 120, tail=(f['top'][0] + 30, f['top'][1] - 10))
        if not paid:
            for j in range(3): pill(c, ['çay', 'tost', 'su'][j], 1370 + j * 85, 360, 26, WASH_Y, INK)
        else: txt(c, '?', 1450, 400, 110, MUTE)

def z_meta(c, t, t0):
    txt(c, 'Yarım iş mi daha iyi hatırlanıyor?', 1300, 300, 46, INK)
    bars(c, 950, 400, [('Yarım kalan', .5, CORAL, ''), ('Biten', .5, TEAL, '')], t, t0, w=640)
    stamp(c, 'FARK YOK', 1300, 800, t, at('z4', .7), CORAL)

def z_resume(c, t, t0):
    box(c, 960, 260, 1680, 520, r=20, w=8, fill=PAPER)
    txt(c, 'E-posta taslağı', 1320, 340, 44, INK)
    box(c, 1040, 420, 1600, 452, r=10, w=6, fill=PAPER); box(c, 1040, 420, 1320, 452, r=10, w=6, fill=CORAL)
    u = smooth(seg(t, at('z5', .55), at('z5', .95)))
    f = fig(c, lerp(1900, 1240, u) if u < 1 else 1240, GY, .8, -1, R.walk_pose(t * 6, 24) if 0 < u < 1 else dict(R.STAND, aR=150, eR=150), 'smile')
    if u >= 1: R.check(c, 1700, 300, 1.4, seg(t, at('z5', .95), E('z5') + .3))

def z_poke(c, t, t0):
    f = fig(c, 760, GY, 1.0, 1, R.STAND, 'confused')
    hx, hy = f['head']
    R.cloud(c, 1200, 340, 190, 120, tail=(hx + 50, hy - 30)); envelope(c, 1200, 340, .9)
    k = int(t * 6) % 2
    line(c, [(1060, 420 + k * 10), (hx + 60 + k * 8, hy - 10)], CORAL, 10)
    R.burst(c, hx + 50, hy - 20, 40, 70, 6, CORAL, 6, .8 if k else .3)


# ============ BOLUM 7: test ============
QA = {1: 'q1', 2: 'q2', 3: 'q3', 4: 'q4', 5: 'q5', 6: 'q6'}
ANS = {'q1': 1, 'q2': 2, 'q3': 3, 'q4': 4, 'q5': 5, 'q6': 6}
def quiz(c, t, t0):
    cur = None
    for n in range(1, 7):
        if t >= S(QA[n]) - .3: cur = n
    if t < S('q1') - .3:
        p = pop(t, t0, .4)
        with xf(c, 960, 380, lerp(.6, 1, p)): hl_text(c, 'MİNİ TEST', 960, 400, 150, INK, ['TEST'])
        icon_row(c, t, t0 + .6, y=640, s=.8, gap=270)
        return
    if t >= S('q7'):
        hl_text(c, 'Kaç tanesini bildin?', 960, 400, 100, INK, ['bildin?'])
        txt(c, '_ / 6', 960, 600, 140, CORAL)
        txt(c, 'Puanını yorumlara yaz', 960, 760, 52, MUTE, 'med')
        return
    q = QA[cur]; a = q + 'a'
    pill(c, f'SORU {cur} / 6', 960, 200, 36, INK, BG)
    f = font(46); sp = f.measureText(' '); rows, row = [], []
    for w_ in LID[q]['text'].split():
        if row and f.measureText(' '.join(row + [w_])) > 1500: rows.append(row); row = []
        row.append(w_)
    rows.append(row)
    for n, r_ in enumerate(rows): txt(c, ' '.join(r_), 960, 290 + n * 62, 46, INK, 'med', alpha=seg(t, S(q) - .3, S(q)))
    shown = t >= S(a) - .05
    icon_row(c, t, None, hi=ANS[q] if shown else None, y=560 if len(rows) < 2 else 590, s=.85, gap=275)
    if not shown: countdown(c, 960, 800, t, E(q) + .1, 3)
    else: hl_text(c, CH[ANS[q]][1] if cur != 6 else 'Yarım iş: dönme isteği', 960, 830, 62, INK, [])


# ============ BOLUM 8: kapanis ============
def o_recap(c, t, t0):
    if t < S('o2'):
        txt(c, 'BUGÜNÜN 6 OYUNU', 960, 250, 60, INK)
        for k in range(1, 7):
            tk = at('o1', .26 + (k - 1) * .12)
            if t < tk: continue
            x = 960 + (k - 3.5) * 290
            with xf(c, x, 520, pop(t, tk, .3)): icon(c, k, x, 520, .95, t)
            txt(c, ICON_NAMES[k], x, 670, 30, INK, 'med')
    elif t < S('o2b'):
        icon_row(c, t, None, y=420, s=.7, labels=False, gap=230)
        stamp(c, 'ARIZA DEĞİL', 960, 720, t, at('o2', .15), TEAL, rot=-4, size=90)
    elif t < S('o3'):
        R.ground(c, 160, 1760, GY); R.door(c, 640, GY, 200, 470, wall_top=180)
        fig(c, 1060, GY, 1.0, -1, dict(R.STAND, aR=150, eR=170), 'happy')
        R.qmark(c, 1150, 300, 120, t, MUTE)
    else:
        box(c, 560, 250, 1360, 520, r=30, w=8, fill=PAPER)
        txt(c, 'Senin başına en çok', 960, 360, 56, INK); txt(c, 'hangisi geliyor?', 960, 440, 56, CORAL)
        p = pop(t, at('o3', .5), .35)
        with xf(c, 960, 680, p):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(760, 630, 1160, 730), 50, 50), paint(CORAL, fill=True))
            txt(c, 'ABONE OL', 960, 700, 50, PAPER)

def o_end(c, t, t0):
    p = pop(t, t0, .4)
    with xf(c, 960, 340, lerp(.7, 1, p)):
        txt(c, 'Bir sonraki videoda', 960, 310, 100, INK)
        w = tw('görüşürüz!', 120)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(960 - w / 2 - 26, 340, 960 + w / 2 + 26, 470), 22, 22), paint(YEL, fill=True))
        txt(c, 'görüşürüz!', 960, 440, 120, INK)
    fig(c, 960, GY + 40, .55, 0, dict(R.FRONT, aR=150, eR=160 + 25 * math.sin(t * 8)), 'happy')
    pill(c, 'ABONE OL', 960, 880, 40, CORAL, PAPER, alpha=seg(t, t0 + .8, t0 + 1.2))


# ---------- program ----------
PLAN = {
    0: [(0, i_alarm), ('i2', i_grid), ('i3', i_day), (('title', 0), i_title)],
    1: [(('clock1', 0), p_clock(1)), ('k1', k_walk), ('k3', p_name(1)),
        ('k4', p_study(['Radvansky, Krawietz', 've Tamplin, 2011'], 'Notre Dame Üniversitesi', k_virtual)),
        ('k5', p_study(['Radvansky, Krawietz', 've Tamplin, 2011'], 'Notre Dame Üniversitesi', k_bars)),
        ('k5b', p_study(['Radvansky, Krawietz', 've Tamplin, 2011'], 'Gerçek odalarla deney', k_real)),
        ('k6', k_why), ('k8', p_matter('Kızma: bu, beyninin düzen tutma şekli.', ['düzen', 'tutma']))],
    2: [(('clock2', 0), p_clock(2)), ('s1', s_spill), ('s3', p_name(2)),
        ('s4', p_study(['Gilovich, Medvec', 've Savitsky, 2000'], 'Cornell Üniversitesi', s_room)),
        ('s5', p_study(['Gilovich, Medvec', 've Savitsky, 2000'], 'Cornell Üniversitesi', s_bars1)),
        ('s5b', p_study(['Gilovich, Medvec', 've Savitsky, 2000'], 'İkinci deney', s_bars2)),
        ('s6', s_why), ('s7', p_matter('Çoğu kişi o an kendi lekesini düşünüyor.', ['kendi', 'lekesini']))],
    3: [(('clock3', 0), p_clock(3)), ('d1', d_meet), ('d3', p_name(3, d_tongue)),
        ('d4', p_study(['Brown ve McNeill, 1966'], 'Harvard Üniversitesi', d_quiz)),
        ('d5', p_study(['A. S. Brown, 1991'], 'Psychological Bulletin', d_stats)),
        ('d6', d_bridge), ('d7', p_matter('Zorlamayı bırak: çoğu kendiliğinden gelir.', ['kendiliğinden']))],
    4: [(('clock4', 0), p_clock(4)), ('e1', e_table), ('e3', p_study(['Provine, 1986'], 'Ethology dergisi', e_faces)),
        ('e4', p_study(['Norscia ve Palagi, 2011'], 'PLoS ONE', e_kin)),
        ('e5', p_study(['Massen ve Gallup, 2017'], 'Neurosci. Biobehav. Rev.', e_why)),
        ('e6', p_matter('Esnemek sıkıldığın anlamına gelmeyebilir.', ['gelmeyebilir.']))],
    5: [(('clock5', 0), p_clock(5)), ('a1', a_board), ('a2b', a_spoon), ('a3', p_name(5)),
        ('a4', p_study(['Severance ve Washburn, 1907', 'Lambert ve Jakobovits, 1960'], 'McGill Üniversitesi', a_meter)),
        ('a5', p_study(['Tian ve Huber, 2010'], 'Cognitive Psychology', a_rope)),
        ('a6', p_matter('Kalıcı değil: birkaç saniyede geçer.', ['Kalıcı', 'değil:']))],
    6: [(('clock6', 0), p_clock(6)), ('z1', z_bed), ('z3', p_study(['Zeigarnik, 1927'], 'Berlin', lambda c, t, t0: p_name(6)(c, t, t0) if False else z_waiter(c, t, t0) if t >= S('z3b') else None)),
        ('z4', p_study(['Ghibellini ve Meier, 2025'], 'Bern Üniversitesi · 37 çalışma', z_meta)),
        ('z5', p_study(['Ovsiankina, 1928'], 'Berlin', z_resume)), ('z6', z_poke),
        ('z7', p_study(['Masicampo ve', 'Baumeister, 2011'], 'Plan yazmak zihni rahatlattı',
                       lambda c, t, t0: (pill(c, 'BU NEDEN ÖNEMLİ?', 1290, 260, 40, CORAL, PAPER), box(c, 1000, 330, 1580, 640, r=16, w=8, fill=WASH_Y),
                                         txt(c, 'Yarın 10:00', 1290, 430, 54, INK), txt(c, 'e-postayı bitir', 1290, 510, 46, INK, 'med'),
                                         R.check(c, 1290, 720, 1.5, seg(t, at('z7', .6), at('z7', .8))))))],
    8: [(('night', 0), o_recap), (('end', 0), o_end)],
}

def starts(k):
    out = []
    for key, fn in PLAN[k]:
        if key == 0: s0 = span(k)[0]
        elif isinstance(key, tuple): s0 = B(key[0])[key[1]]
        else: s0 = S(key) - .15
        out.append((s0, fn))
    return out
STARTS = {k: starts(k) for k in PLAN}

def zeig_card(c, t, t0):
    """z3: Zeigarnik karti (sag): yarim isler daha mi iyi hatirlaniyor?"""
    if t >= S('z3b'): return
    box(c, 960, 260, 1680, 640, r=20, w=8, fill=PAPER)
    txt(c, 'İddia (1927):', 1320, 340, 40, MUTE, 'med')
    txt(c, 'Yarım kalan iş', 1320, 430, 56, CORAL); txt(c, 'daha iyi hatırlanır', 1320, 500, 48, INK)
    R.qmark(c, 1600, 600, 90, t, MUTE)


# ---------- ust bant, altyazi ----------
def chrome(c, t, k):
    pill(c, 'DEMEK O YÜZDEN', 60, 64, 26, INK, BG, align='l')
    if 1 <= k <= 6:
        hh, name, lab = CH[k]
        for n in range(6):
            x = 760 + n * 80; on = n + 1 <= k
            c.drawCircle(x, 64, 14 if n + 1 == k else 10, paint(CORAL if n + 1 == k else (INK if on else MUTE), fill=True))
            if n < 5: line(c, [(x + 16, 64), (x + 64, 64)], MUTE, 4, amp=.4)
        s_ = f'{hh} · {name}' if t >= S(NAMED[k]) - .1 else hh
        w = tw(s_, 30); pill(c, s_, 1860 - w - 48, 64, 30, PAPER, INK, align='l')

VOW = set('aeıioöuüâîûAEIİOÖUÜÂÎÛ')
def syl(ws): return max(1, sum(ch in VOW for ch in ''.join(ws)) + sum(ch.isdigit() for ch in ''.join(ws)) * 1.2)
def chunks(text, maxc=34):
    out, cur = [], []
    for wd in text.split():
        if cur and len(' '.join(cur + [wd])) > maxc: out.append(cur); cur = []
        cur.append(wd)
        if wd[-1] in '.!?' and len(' '.join(cur)) > 8: out.append(cur); cur = []
        elif wd[-1] in ',:' and len(' '.join(cur)) > 16: out.append(cur); cur = []
    if cur: out.append(cur)
    if len(out) > 1 and len(' '.join(out[-1])) < 6:
        last = out.pop(); out[-1] = out[-1] + last
    return out
CAPS = []
for n_, l in enumerate(LN):
    ch = chunks(l['text']); st = R.chunk_times(l['start'], l['end'], ch) if len(ch) > 1 else [l['start']]
    nxt = LN[n_ + 1]['start'] if n_ + 1 < len(LN) else TOTAL
    for j, x in enumerate(ch):
        b = st[j + 1] if j + 1 < len(ch) else min(l['end'] + .3, nxt - .02)
        CAPS.append(dict(a=st[j], b=b, words=x, hl=SL[l['id']]['hl']))
# R.chunk_times hece agirligini kendi syl'iyle hesaplar; rakamlari da sayalim
R.syl = syl

def captions(c, t):
    for cp in CAPS:
        if cp['a'] <= t < cp['b']:
            size = 60; f = font(size); sp = f.measureText(' ') * 1.05
            ws = cp['words']; wd = [f.measureText(w) for w in ws]; tot = sum(wd) + sp * (len(ws) - 1)
            a = seg(t, cp['a'], cp['a'] + .08)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(960 - tot / 2 - 40, 940, 960 + tot / 2 + 40, 1040), 26, 26), paint(PAPER, fill=True, alpha=.92 * a))
            x = 960 - tot / 2; y = 1011
            for w_, ww in zip(ws, wd):
                if w_ in cp['hl']:
                    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 8, y - 52, x + ww + 8, y + 16), 12, 12), paint(YEL, fill=True, alpha=a))
                c.drawString(w_, x, y, f, paint(INK, fill=True, alpha=a)); x += ww + sp
            return

def scene_of(t):
    k = 0
    for s_ in sorted(SCN):
        if t >= SCN[s_] - 1e-6: k = s_
    return k

def frame(cv, t, fi):
    R.St.boil = fi // 5; R.St.n = 0
    cv.clear(BG)
    k = scene_of(t)
    act = None
    for s0, fn in STARTS[k]:
        if t >= s0 - 1e-6: act = (s0, fn)
    if act is None: act = STARTS[k][0]
    s0, fn = act
    fn(cv, t, s0)
    if k == 6 and S('z3') - .15 <= t < S('z4') - .15: zeig_card(cv, t, S('z3'))
    fa = seg(t, s0, s0 + .22)
    if fa < 1: cv.drawRect(skia.Rect.MakeWH(W, H), paint(BG, fill=True, alpha=1 - fa))
    chrome(cv, t, k)
    captions(cv, t)
    a, b = span(k)
    f = min(seg(t, a, a + .3), 1 - seg(t, b - .3, b)) if k != 8 else min(seg(t, a, a + .3), 1 - seg(t, TOTAL - .7, TOTAL - .05))
    if k == 0: f = min(seg(t, 0, .35), 1 - seg(t, b - .3, b))
    if f < 1: cv.drawRect(skia.Rect.MakeWH(W, H), paint(BG, fill=True, alpha=1 - f))


if __name__ == '__main__':
    cmd = sys.argv[1]
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    if cmd == 'still':
        os.makedirs(sys.argv[2], exist_ok=True)
        for ts in sys.argv[3:]:
            t = float(ts); frame(cv, t, int(t * FPS)); surf.makeImageSnapshot().save(f'{sys.argv[2]}/u_{t:06.2f}.png', skia.kPNG)
    elif cmd == 'part':
        a, b, name = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        f0, f1 = round(a * FPS), round(min(b, TOTAL) * FPS)
        os.makedirs('parts', exist_ok=True); tmp, out = f'parts/tmp_{name}.mp4', f'parts/{name}.mp4'
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-crf', '21', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            frame(cv, fi / FPS, fi); p.stdin.write(surf.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.replace(tmp, out); print('parca', name, f1 - f0, 'kare')
        else: sys.exit(1)
    elif cmd == 'join':
        out = sys.argv[2]; names = sys.argv[3:]
        open('parts/list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in names))
        tmp = out.replace('.mp4', '.tmp.mp4')
        r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'parts/list.txt', '-i', 'voice/mix.wav',
                            '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp])
        if r.returncode != 0: sys.exit(1)
        os.replace(tmp, out); print('ok', out)
