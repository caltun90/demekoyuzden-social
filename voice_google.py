"""Google (Gemini TTS) seslendirme: tum senaryoyu TEK istekte okutur, sonra cumlelere boler.

Kullanim:
  GEMINI_API_KEY=... python3 voice_google.py <voice> [model]        -> voice/final.wav + voice/final.json
  python3 voice_google.py --from-wav in.wav                         -> ayni hizalama, hazir bir kayittan (test icin)
  GEMINI_API_KEY=... python3 voice_google.py --sample Achird Enceladus Algieba   -> samples/<voice>.wav

Tek istek kullanmanin nedeni: ucretsiz kotada gunluk istek sayisi dusuk olabilir ve ton cumleler arasinda tutarli kalir.
render.py yalnizca voice/final.json icindeki satir zamanlarini okur.
"""
import sys, os, json, base64, re, urllib.request, urllib.error
import numpy as np, soundfile as sf
from script import LINES

STYLE = ("Sıcak, samimi ve rahat bir tonla, yakın bir arkadaşına anlatır gibi, acele etmeden, "
         "hafif gülümseyerek Türkçe oku. Cümleler arasında kısa bir nefes payı bırak:")
SAMPLE = "Mutfağa girdin ve durdun. Ben buraya ne için gelmiştim? Merak etme, unutkan değilsin. Bunun bir adı bile var: kapı eşiği etkisi."
DEFAULT_MODEL = "gemini-3.8-flash-tts"   # olmazsa: gemini-3.1-flash-tts-preview, gemini-2.5-flash-preview-tts
GAP_LINE, GAP_SCENE, LEAD, TAIL = 0.3, 0.55, 0.45, 1.0
GAP_AFTER = {3: 0.7}   # satir indeksine gore ozel bosluk (animasyon icin sure); her senaryoda yeniden ayarla


def synth(text, voice, model=DEFAULT_MODEL, style=STYLE):
    key = os.environ["GEMINI_API_KEY"]
    body = {"contents": [{"parts": [{"text": style + "\n\n" + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"TTS hatasi {e.code}: {e.read().decode()[:400]}")
    part = r["candidates"][0]["content"]["parts"][0]["inlineData"]
    m = re.search(r"rate=(\d+)", part.get("mimeType", ""))
    sr = int(m.group(1)) if m else 24000
    x = np.frombuffer(base64.b64decode(part["data"]), dtype="<i2").astype(np.float32) / 32768.0
    return x, sr


def silences(x, sr, min_dur=0.12):
    hop = int(sr * 0.01)
    n = len(x) // hop
    rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    quiet = rms < max(0.012, 0.04 * np.percentile(rms, 95))
    gaps, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            if (j - i) * 0.01 >= min_dur: gaps.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return gaps


def align(x, sr, texts):
    """Kaydi len(texts) parcaya boler. Beklenen sinir = karakter oranina gore; en yakin sessizlige oturtulur (DP)."""
    total = len(x) / sr
    gaps = silences(x, sr)
    lead = gaps[0][1] if gaps and gaps[0][0] < 0.05 else 0.0
    trail = gaps[-1][0] if gaps and gaps[-1][1] > total - 0.05 else total
    inner = [g for g in gaps if g[0] > lead + 0.05 and g[1] < trail - 0.05]
    mids = np.array([(a + b) / 2 for a, b in inner]); durs = np.array([b - a for a, b in inner])
    # sessizlikler cikarilmis "konusma zamani" uzerinden hizala: uzun duraklamalar orani bozmasin
    voiced_before = np.array([(g[0] - lead) - sum(d for (a2, b2), d in zip(inner, durs) if b2 <= g[0]) for g in inner])
    voiced_total = (trail - lead) - durs.sum()
    w = np.array([len(t) for t in texts], dtype=float)
    exp = voiced_total * np.cumsum(w)[:-1] / w.sum()
    nb, ng = len(exp), len(inner)
    if ng < nb: raise SystemExit(f"Yeterli duraklama bulunamadi ({ng} < {nb}); satirlari ayri ayri okutmak gerekir.")
    cost = np.abs(voiced_before[None, :] - exp[:, None]) - 1.5 * np.minimum(durs, 0.6)[None, :]
    INF = 1e9
    dp = np.full((nb, ng), INF); arg = np.zeros((nb, ng), dtype=int)
    dp[0] = cost[0]
    for i in range(1, nb):
        best, bj = INF, -1
        for j in range(ng):
            if j >= 1 and dp[i - 1, j - 1] < best: best, bj = dp[i - 1, j - 1], j - 1
            if bj >= 0: dp[i, j] = best + cost[i, j]; arg[i, j] = bj
    j = int(np.argmin(dp[-1])); pick = [j]
    for i in range(nb - 1, 0, -1):
        j = arg[i, j]; pick.append(j)
    pick = pick[::-1]
    cuts = [lead] + [mids[j] for j in pick] + [trail]
    segs = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        s = x[int(a * sr):int(b * sr)]
        idx = np.where(np.abs(s) > 0.012)[0]
        segs.append(s[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.06 * sr)] if len(idx) else s)
    return segs, cuts


def assemble(segs, sr, out="voice/final"):
    t = LEAD; timing = []; place = []
    for i, ((sc, cap, _), s) in enumerate(zip(LINES, segs)):
        d = len(s) / sr
        timing.append(dict(i=i, scene=sc, text=cap, start=round(t, 3), end=round(t + d, 3)))
        place.append((t, s)); t += d
        nxt = LINES[i + 1][0] if i + 1 < len(LINES) else None
        t += GAP_AFTER.get(i, GAP_SCENE if nxt != sc else GAP_LINE)
    total = t - GAP_LINE + TAIL
    buf = np.zeros(int(total * sr) + 1, dtype=np.float32)
    for st, s in place:
        k = int(st * sr); f = int(0.01 * sr); s = s.copy()
        s[:f] *= np.linspace(0, 1, f); s[-f:] *= np.linspace(1, 0, f)
        buf[k:k + len(s)] += s
    buf = buf / max(1e-6, np.abs(buf).max()) * 0.89
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sf.write(out + ".wav", buf, sr)
    json.dump(dict(total=round(total, 3), lines=timing), open(out + ".json", "w"), ensure_ascii=False, indent=1)
    print("toplam sure", round(total, 2), "sn")
    return timing


if __name__ == "__main__":
    texts = [(say or cap) for _, cap, say in LINES]
    if sys.argv[1] == "--sample":
        os.makedirs("samples", exist_ok=True)
        for v in sys.argv[2:]:
            x, sr = synth(SAMPLE, v); sf.write(f"samples/{v}.wav", x, sr); print("ornek:", v, round(len(x) / sr, 1), "sn")
    elif sys.argv[1] == "--from-wav":
        x, sr = sf.read(sys.argv[2], dtype="float32")
        segs, cuts = align(x, sr, texts); print("kesimler:", [round(float(c), 2) for c in cuts])
        assemble(segs, sr, out=sys.argv[3] if len(sys.argv) > 3 else "voice/final")
    else:
        voice = sys.argv[1]; model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL
        x, sr = synth("\n".join(texts), voice, model)
        os.makedirs("voice", exist_ok=True); sf.write("voice/raw_google.wav", x, sr)
        segs, cuts = align(x, sr, texts); print("kesimler:", [round(float(c), 2) for c in cuts])
        assemble(segs, sr)
