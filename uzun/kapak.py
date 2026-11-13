import os; os.environ['FMT'] = 'h'
import skia, math
import render as R
from uzun import icon, fig, txt, tw, paint, INK, CORAL, YEL, BG, PAPER
W, H = 1920, 1080
s = skia.Surface(W, H); c = s.getCanvas(); c.clear(BG); R.St.boil = 0
txt(c, 'BEYNİNİN SANA', 640, 250, 120, INK)
w = tw('OYNADIĞI 6 OYUN', 132)
c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(640 - w/2 - 30, 300, 640 + w/2 + 30, 450), 26, 26), paint(YEL, fill=True))
txt(c, 'OYNADIĞI 6 OYUN', 640, 418, 132, INK)
txt(c, 'Hepsi bilimsel. Kaçını yaşadın?', 640, 560, 56, CORAL)
for n in range(6):
    x = 200 + (n % 3) * 220 + 0; y = 720 + (n // 3) * 200
    icon(c, n + 1, x + 110, y, .85, 0)
f = fig(c, 1500, 980, 1.45, 0, dict(R.STAND, aR=118, eR=202, tilt=-8), 'confused')
R.qmark(c, 1660, 260, 230, 0)
s.makeImageSnapshot().save('kapak_full.png', skia.kPNG)
