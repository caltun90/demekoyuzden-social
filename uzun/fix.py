"""Ses duzeltmeleri (TTS kotasi olmadan): sesli harf uzatma (TD-PSOLA) ve satir sonu kesme."""
import numpy as np

def period(x, sr, lo=70, hi=320):
    x = x - x.mean(); r = np.correlate(x, x, 'full')[len(x) - 1:]
    a, b = int(sr / hi), int(sr / lo)
    return a + int(np.argmax(r[a:b]))

def marks(x, sr, a, b, T):
    """a..b arasinda (ornek) periyot araliklarinda tepe noktalari"""
    m = []; p = a + int(np.argmax(np.abs(x[a:a + T])))
    while p < b:
        m.append(p); q = p + T
        w = x[max(0, q - T // 4): q + T // 4]
        p = max(0, q - T // 4) + int(np.argmax(np.abs(w))) if len(w) else q
    return np.array(m)

def stretch_vowel(x, sr, t0, t1, factor, pad=0.04):
    """x[t0:t1] (saniye) bolgesini factor kat uzatir; disi aynen kalir."""
    a, b = int(t0 * sr), int(t1 * sr); A, B = int((t0 - pad) * sr), int((t1 + pad) * sr)
    T = period(x[a:b], sr)
    M = marks(x, sr, A, B, T)
    extra = int((b - a) * (factor - 1))
    L = (B - A) + extra
    out = np.zeros(L + 4 * T, dtype=np.float32)
    def src(o):   # cikis zamani (ornek, A'ya gore) -> giris zamani
        if o < a - A: return o
        if o < a - A + (b - a) * factor: return (a - A) + (o - (a - A)) / factor
        return o - extra
    o = M[0] - A
    win = np.hanning(2 * T + 1).astype(np.float32)
    while o < L:
        s = src(o) + A; k = M[int(np.argmin(np.abs(M - s)))]
        g = x[k - T: k + T + 1] * win
        if o - T >= 0: out[o - T: o + T + 1] += g
        o += T
    seg = out[M[0] - A: L - (B - M[-1])]
    head, tail = x[:M[0]], x[M[-1]:]
    n = int(0.004 * sr); f = np.linspace(0, 1, n, dtype=np.float32)
    seg[:n] = seg[:n] * f + x[M[0]:M[0] + n] * (1 - f)
    seg[-n:] = seg[-n:] * (1 - f) + x[M[-1] - n:M[-1]] * f
    return np.concatenate([head, seg, tail]).astype(np.float32), extra / sr
