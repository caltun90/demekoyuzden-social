"""Ses hizalama ve altyazi senkron araci (Gemini ile yaziya dokme).

  GEMINI_API_KEY=... python3 sync.py list            -> ham kaydi duraklamalardan parcalara boler, her parcayi yaziya doker
  python3 sync.py build "0-1,2-3,4,5-7,..."          -> her satir icin parca araligi; ic duraklamalari kisaltip voice/final.* uretir
  GEMINI_API_KEY=... python3 sync.py check           -> her altyazi penceresinin sesini yaziya doker, altyazi metniyle yan yana basar
"""
import sys, os, io, json, base64, urllib.request, urllib.error
import numpy as np, soundfile as sf
CAP = 0.22   # satir ici en uzun duraklama (sn)

def transcribe(clips, sr):
    parts = [{"text": "Asagida numarali Turkce ses parcalari var. Her biri icin duydugunu aynen yaz. Bicim: 'Parca N: metin'. Baska hicbir sey yazma."}]
    for i, c in enumerate(clips):
        b = io.BytesIO(); sf.write(b, c, sr, format='WAV', subtype='PCM_16')
        parts.append({"text": f"Parca {i}:"})
        parts.append({"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(b.getvalue()).decode()}})
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
                                 data=json.dumps({"contents": [{"parts": parts}]}).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    try: r = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e: raise SystemExit(f"STT hatasi {e.code}: {e.read().decode()[:400]}")
    return r["candidates"][0]["content"]["parts"][0]["text"]

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
