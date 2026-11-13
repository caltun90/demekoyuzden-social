"""Ses hizalama ve altyazi senkron araci (Gemini ile yaziya dokme).

  GEMINI_API_KEY=... python3 sync.py list            -> ham kaydi duraklamalardan parcalara boler, her parcayi yaziya doker
  python3 sync.py build "0-1,2-3,4,5-7,..."          -> her satir icin parca araligi; ic duraklamalari kisaltip voice/final.* uretir
  GEMINI_API_KEY=... python3 sync.py check           -> her altyazi penceresinin sesini yaziya doker, altyazi metniyle yan yana basar
"""
import sys, os, io, json, base64, urllib.request, urllib.error
import numpy as np, soundfile as sf
CAP = 0.22   # satir ici en uzun duraklama (sn)

# Yaziya dokme modelleri, sirayla. Ilki gunluk kotaya takilirsa (429) ya da yogunsa (503) siradaki denenir; is yarida kalmaz.
# Ucretsiz kotada gemini-3-flash-preview gunde 20, gemini-3.1-flash-lite gunde 500 istek (dakikada 15). SYNC_MODEL=... ile tek model zorlanir.
# Lite parcalari birlestirmeye yatkin; bu yuzden ona kucuk gruplar (BATCH) ve "tam N ogeli JSON" semasi verilir.
MODELS = ["gemini-3-flash-preview", "gemini-3.1-flash-lite"]
BATCH = 12

def _wav(c, sr):
    b = io.BytesIO(); sf.write(b, c, sr, format='WAV', subtype='PCM_16')
    return {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(b.getvalue()).decode()}}

def _call(model, body):
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    return json.load(urllib.request.urlopen(req, timeout=180))["candidates"][0]["content"]["parts"][0]["text"]

def _plain(model, clips, sr):
    parts = [{"text": "Asagida numarali Turkce ses parcalari var. Her biri icin duydugunu aynen yaz. Bicim: 'Parca N: metin'. Baska hicbir sey yazma."}]
    for i, c in enumerate(clips): parts += [{"text": f"Parca {i}:"}, _wav(c, sr)]
    return _call(model, {"contents": [{"parts": parts}]})

def _grouped(model, clips, sr):
    out = []
    for g in range(0, len(clips), BATCH):
        grp = clips[g:g + BATCH]; n = len(grp)
        parts = [{"text": f"Asagida 0'dan {n - 1}'e numarali {n} ayri Turkce ses parcasi var. Her parcayi TEK BASINA dinle ve yalnizca o parcada duydugunu yaz. "
                          "Parcalari birlestirme, komsu parcanin sozunu ekleme. Parca bir kelimenin ortasinda kesilmis olabilir; duydugun kadarini yaz. "
                          f"Sessiz ya da anlasilmaz parca icin bos metin yaz. Tam {n} ogeli bir JSON dizisi dondur; i. oge i. parcanin metni."}]
        for i, c in enumerate(grp): parts += [{"text": f"Parca {i}:"}, _wav(c, sr)]
        schema = {"type": "ARRAY", "minItems": n, "maxItems": n, "items": {"type": "OBJECT", "properties": {"i": {"type": "INTEGER"}, "metin": {"type": "STRING"}}, "required": ["i", "metin"]}}
        res = json.loads(_call(model, {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": schema}}))
        out += [str(res[i].get("metin", "")) if i < len(res) else "" for i in range(n)]
    return "\n".join(f"Parca {i}: {t}" for i, t in enumerate(out))

def transcribe(clips, sr):
    models = [os.environ["SYNC_MODEL"]] if os.environ.get("SYNC_MODEL") else MODELS
    for k, m in enumerate(models):
        try:
            return (_grouped if "lite" in m else _plain)(m, clips, sr)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code in (429, 503) and k + 1 < len(models):
                print(f"[{m}: {e.code}, {models[k + 1]} ile deneniyor]", file=sys.stderr); continue
            raise SystemExit(f"STT hatasi {e.code} ({m}): {msg}")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "list":
        from voice_google import silences
        x, sr = sf.read('voice/raw_google.wav', dtype='float32')
        g = silences(x, sr, 0.12)
        b = [(g[i][1], g[i + 1][0]) for i in range(len(g) - 1)]
        json.dump(b, open('voice/pieces.json', 'w'))
        print(transcribe([x[int(max(0, a - .03) * sr):int((e + .05) * sr)] for a, e in b], sr))
        print("parca sayisi:", len(b), "| ham sure:", round(len(x) / sr, 1), "sn")
    elif cmd == "build":
        from voice_google import assemble
        from script import LINES
        x, sr = sf.read('voice/raw_google.wav', dtype='float32'); b = json.load(open('voice/pieces.json'))
        rng = [tuple(int(v) for v in (p.split('-') if '-' in p else (p, p))) for p in sys.argv[2].split(',')]
        assert len(rng) == len(LINES), f"{len(rng)} aralik var, {len(LINES)} satir bekleniyor"
        assert [k for a, e in rng for k in range(a, e + 1)] == list(range(len(b))), "araliklar tum parcalari sirayla kapsamali"
        segs = []
        for a, e in rng:
            out = []
            for k in range(a, e + 1):
                s0, s1 = b[k]; out.append(x[int(max(0, s0 - .03) * sr):int((s1 + .05) * sr)])
                if k < e: out.append(np.zeros(int(max(0.06, min(CAP, b[k + 1][0] - s1 - .08)) * sr), dtype=np.float32))
            segs.append(np.concatenate(out))
        for l in assemble(segs, sr): print(l['i'], l['scene'], l['start'], l['end'], l['text'][:50])
    elif cmd == "check":
        import render as R
        out = transcribe([R._AU[int(max(0, cp['a'] - .02) * R._SR):int(cp['b'] * R._SR)] for cp in R.CAPS], R._SR).strip().split('\n')
        for i, cp in enumerate(R.CAPS):
            print(cp['line'], round(cp['a'], 2), round(cp['b'], 2), '|', ' '.join(cp['words']), '||', out[i] if i < len(out) else '')
