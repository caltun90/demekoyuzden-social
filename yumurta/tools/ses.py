"""Yumurta stili seslendirme: her cümle ayrı seslendirilir (TTS doğaçlama yapamaz, hizalama kaymaz), birleştirilir,
kelime saatleri (words.json), dudak zarfı (env.json) çıkarılır. Repodaki Whisper aracı bulutta çalışmadığı için onun yerine.

  python3 tools/ses.py tts   <story_dir> <ses> [--model M] [--stil "..."]    satırları üretir (voice/lines/NN.wav, önbellek)
  python3 tools/ses.py build <story_dir> [--tempo 1.25] [--kanca 1.1]        birleştirir: voice.wav, words.json, env.json
  python3 tools/ses.py check <story_dir>                                      her satırı yazıya döker, senaryoyla karşılaştırır

Senaryo: <story_dir>/voice/script.txt, her satır bir cümle (ilk satır kanca). Rakam yerine okunuşu yaz ya da
voice/say.txt dosyasına aynı sırada okunacak hâli koy (altyazı script.txt'den gelir).
Ortam: GEMINI_API_KEY. Gemini 3.1 TTS stil talimatını okumaz; 3.8 TTS stil talimatını SESLİ okur, ona stil verme.
Kokoro (İngilizce, Survivometer): --model kokoro, ses adı "am_puck:0.3,am_fenrir:0.7" biçiminde; KOKORO_DIR model klasörü.
"""
import sys, os, re, io, json, time, base64, subprocess, urllib.request, urllib.error
import numpy as np, soundfile as sf

def arg(name, default=None):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default

def synth_gemini(text, voice, model, style):
    body = {"contents": [{"parts": [{"text": (style + "\n\n" if style else "") + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    for k in range(9):
        req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=180)); break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:600]
            if e.code == 429 and 'PerDay' not in msg and k < 8: print('429 (dakika sınırı), bekleniyor', flush=True); time.sleep(25); continue
            if e.code in (500, 503) and k < 8: time.sleep(10); continue
            raise SystemExit(f"TTS hatası {e.code}: {msg}")
    part = r["candidates"][0]["content"]["parts"][0]["inlineData"]
    m = re.search(r"rate=(\d+)", part.get("mimeType", "")); sr = int(m.group(1)) if m else 24000
    return np.frombuffer(base64.b64decode(part["data"]), dtype="<i2").astype(np.float32) / 32768.0, sr

def synth_kokoro(text, voice):
    from kokoro_onnx import Kokoro
    d = os.environ.get('KOKORO_DIR', 'kokoro')
    k = Kokoro(os.path.join(d, 'kokoro-v1.0.onnx'), os.path.join(d, 'voices-v1.0.bin'))
    mix = None
    for part in voice.split(','):
        name, w = (part.split(':') + ['1'])[:2]; st = k.get_voice_style(name) * float(w)
        mix = st if mix is None else mix + st
    x, sr = k.create(text, voice=mix, speed=1.0, lang='en-us')
    return x.astype(np.float32), sr

def silences(x, sr, min_dur=.06):
    hop = int(sr * .01); n = len(x) // hop
    rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    quiet = rms < max(.012, .04 * np.percentile(rms, 95)); gaps, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            if (j - i) * .01 >= min_dur: gaps.append((i * .01, j * .01))
            i = j
        else: i += 1
    return gaps

def trim(x, sr, thr=.012):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(0, idx[0] - int(.02 * sr)): idx[-1] + int(.05 * sr)] if len(idx) else x

def lines_of(D):
    L = [l.strip() for l in open(os.path.join(D, 'voice', 'script.txt'), encoding='utf-8') if l.strip()]
    sp = os.path.join(D, 'voice', 'say.txt')
    S = [l.strip() for l in open(sp, encoding='utf-8') if l.strip()] if os.path.exists(sp) else L
    assert len(S) == len(L), 'say.txt ile script.txt aynı sayıda satır olmalı'
    return L, S

def cmd_tts(D, voice):
    model = arg('--model', 'gemini-3.1-flash-tts-preview')
    style = arg('--stil', '' if '3.8' in model else 'Merak uyandıran, samimi ve akıcı bir anlatıcı gibi, metni aynen oku:')
    C = os.path.join(D, 'voice', 'lines'); os.makedirs(C, exist_ok=True)
    L, Sy = lines_of(D)
    for i, say in enumerate(Sy):
        f = os.path.join(C, f'{i:02d}.wav')
        if os.path.exists(f): continue
        x, sr = synth_kokoro(say, voice) if model == 'kokoro' else synth_gemini(say, voice, model, style)
        sf.write(f, x, sr); print('satır', i, round(len(x) / sr, 2), 'sn', flush=True)

def cmd_build(D):
    tempo = float(arg('--tempo', '1.25')); hook = arg('--kanca')
    lang_en = os.path.exists(os.path.join(D, 'voice', 'EN'))
    vow = r'[aeiouy]+' if lang_en else r'[aeıioöuüâîû]'
    syl = lambda w: max(1, len(re.findall(vow, w.lower())))
    L, _ = lines_of(D); C = os.path.join(D, 'voice', 'lines')
    W, out, T, sr0 = [], [], .05, None
    for i, line in enumerate(L):
        x, sr = sf.read(os.path.join(C, f'{i:02d}.wav'), dtype='float32')
        if x.ndim > 1: x = x.mean(1)
        sr0 = sr0 or sr
        if sr != sr0: raise SystemExit('satırların örnekleme hızı farklı')
        x = trim(x, sr)
        if i == 0 and hook:                       # the hook line alone a little faster: it must end before 2 s
            sf.write('/tmp/_h.wav', x, sr); subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/_h.wav', '-filter:a', f'atempo={hook}', '/tmp/_h2.wav'], check=True)
            x, _ = sf.read('/tmp/_h2.wav', dtype='float32')
        words = line.split(); nb = len(re.findall(r'[,;:](?=\s)', line))
        gaps = [g for g in silences(x, sr) if g[0] > .05 and g[1] < len(x) / sr - .05]
        gaps = sorted(sorted(gaps, key=lambda g: g[0] - g[1])[:nb])
        groups, cur = [], []
        for w in words:
            cur.append(w)
            if re.search(r'[,;:]["”]?$', w) and len(groups) < len(gaps): groups.append(cur); cur = []
        groups.append(cur); a = 0.0
        for k, gp in enumerate(groups):
            b = gaps[k][0] if k < len(gaps) else len(x) / sr
            wt = np.array([syl(w) + .4 for w in gp]); cs = np.concatenate([[0], np.cumsum(wt)]) / wt.sum()
            for j, w in enumerate(gp): W.append({'word': w, 'start': T + a + cs[j] * (b - a), 'end': T + a + cs[j + 1] * (b - a)})
            a = gaps[k][1] if k < len(gaps) else a
        if not out: out.append(np.zeros(int(.05 * sr), np.float32))
        out.append(x); T += len(x) / sr
        gap = .26 if re.search(r'[.?!]["”]?$', line) else .16
        out.append(np.zeros(int(gap * sr), np.float32)); T += gap
    y = np.concatenate(out); sf.write('/tmp/_y.wav', y, sr0)
    V = os.path.join(D, 'voice')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/_y.wav', '-filter:a', f'atempo={tempo}', '-ar', '48000', os.path.join(V, 'voice.wav')], check=True)
    for w in W: w['start'] = round(w['start'] / tempo, 3); w['end'] = round(w['end'] / tempo, 3)
    dur = round(len(y) / sr0 / tempo, 3)
    json.dump({'words': W, 'duration': dur}, open(os.path.join(V, 'words.json'), 'w'), ensure_ascii=False, indent=0)
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, 'zarf.py'), os.path.join(V, 'voice.wav'), os.path.join(V, 'env.json')], check=True)
    n0 = len(L[0].split()); nw = len(W)
    print(f'kelime {nw} | süre {dur} sn | hız {round(nw / (W[-1]["end"] - W[0]["start"]), 2)} kelime/sn | kanca biter {W[n0 - 1]["end"]} sn')

def cmd_check(D):
    L, _ = lines_of(D); C = os.path.join(D, 'voice', 'lines'); clips = []
    for i in range(len(L)):
        x, sr = sf.read(os.path.join(C, f'{i:02d}.wav'), dtype='float32'); b = io.BytesIO(); sf.write(b, x, sr, format='WAV', subtype='PCM_16')
        clips.append({"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(b.getvalue()).decode()}})
    n = len(clips)
    parts = [{"text": f"Aşağıda 0'dan {n - 1}'e numaralı {n} ayrı ses parçası var. Her parçayı TEK BAŞINA dinle, yalnızca o parçada duyduğunu aynen yaz. Tam {n} öğeli JSON dizisi döndür."}]
    for i, c in enumerate(clips): parts += [{"text": f"Parça {i}:"}, c]
    schema = {"type": "ARRAY", "minItems": n, "maxItems": n, "items": {"type": "OBJECT", "properties": {"i": {"type": "INTEGER"}, "metin": {"type": "STRING"}}, "required": ["i", "metin"]}}
    for model in ('gemini-3-flash-preview', 'gemini-3.1-flash-lite', 'gemini-3.1-flash-lite'):
        try:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                data=json.dumps({"contents": [{"parts": parts}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": schema}}).encode(),
                headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
            res = json.loads(json.load(urllib.request.urlopen(req, timeout=180))["candidates"][0]["content"]["parts"][0]["text"]); break
        except Exception as e: print('[stt]', model, str(e)[:90]); time.sleep(10)
    else: raise SystemExit('yazıya dökme yapılamadı')
    from difflib import SequenceMatcher
    norm = lambda s: re.sub(r'[^0-9a-zçğıöşüâîû ]', '', s.replace('I', 'ı').replace('İ', 'i').lower()).split()
    bad = 0
    for i, line in enumerate(L):
        got = res[i].get('metin', '') if i < len(res) else ''
        r = SequenceMatcher(None, norm(line), norm(got)).ratio()
        flag = 'TAMAM' if r >= .85 else 'SORUNLU'; bad += r < .85
        print(f'{i:02d} {flag} {r:.2f} | {got}')
    print('sorunlu satır:', bad, '(sorunlu satırın lines/NN.wav dosyasını silip tts ile yeniden üret)')

if __name__ == '__main__':
    c, D = sys.argv[1], sys.argv[2]
    {'tts': lambda: cmd_tts(D, sys.argv[3]), 'build': lambda: cmd_build(D), 'check': lambda: cmd_check(D)}[c]()
