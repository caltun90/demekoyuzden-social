"""WhisperX ile kelime hizalama: words.json'daki tahmini kelime saatlerini gerçek sesten ölçülen saatlerle değiştirir.

Bulut oturumunda HuggingFace kapalı olduğu için bu betik GitHub Actions'ta (`.github/workflows/hizala.yml`) çalışır.
Metin zaten bilindiği için Whisper ile yazıya dökme YAPILMAZ: her satır, ses.py'nin bildiği satır aralığı içinde
wav2vec2 (WhisperX align) ile kelime kelime sese oturtulur. Türkçe model: mpoyraz/wav2vec2-xls-r-300m-cv7-turkish.

  python3 tools/hizala.py <story_dir> [--dil tr|en] [--ses <dosya>]

Girdi : <story>/voice/words.json (ses.py build ya da dizivanastudio kopru.py: words + lines), voice/script.txt (+ say.txt;
        yoksa satır metinleri words.json'daki lines'tan), ses:
        voice/voice.ogg > voice/voice.wav > audio/mix.wav (ilk bulunan)
Çıktı : voice/words.json (ölçülen saatler; "hizalama" alanı), voice/words_tahmin.json (eski tahmin),
        voice/hizalama.txt (satır satır fark raporu)
Bir satır güvenle hizalanamazsa o satırın tahmini saatleri korunur ve raporda yazılır; betik videoyu asla bozmaz.
"""
import sys, os, re, json, difflib
import numpy as np

def arg(name, default=None):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default

def norm(w):
    w = w.replace('I', 'ı').replace('İ', 'i').lower()
    return re.sub(r"[^0-9a-zçğıöşüâîûéèäëï]", '', w)

def read_lines(p):
    return [l.strip() for l in open(p, encoding='utf-8') if l.strip()] if os.path.exists(p) else None

def fill_missing(ws, a, b):
    """ws: [{'start','end'} or None]; eksikleri komşulardan doğrusal doldurur (satır aralığı a-b içinde)."""
    n = len(ws); out = [dict(w) if w else None for w in ws]
    i = 0
    while i < n:
        if out[i] is not None: i += 1; continue
        j = i
        while j < n and out[j] is None: j += 1
        lo = out[i - 1]['end'] if i > 0 else a
        hi = out[j]['start'] if j < n else b
        hi = max(hi, lo + .05 * (j - i)); step = (hi - lo) / (j - i)
        for k in range(i, j): out[k] = {'start': lo + step * (k - i), 'end': lo + step * (k - i + 1)}
        i = j
    for k in range(n):                                   # sıra ve en kısa süre güvencesi
        if k and out[k]['start'] < out[k - 1]['start']: out[k]['start'] = out[k - 1]['start']
        out[k]['end'] = max(out[k]['end'], out[k]['start'] + .04)
    return out

def map_to_script(spoken, times, script):
    """Okunan kelimelerin (say.txt) saatlerini altyazı kelimelerine (script.txt) taşır."""
    if len(spoken) == len(script): return list(times)
    sm = difflib.SequenceMatcher(None, [norm(w) for w in spoken], [norm(w) for w in script], autojunk=False)
    out = [None] * len(script)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1): out[j1 + k] = times[i1 + k]
        elif j2 > j1:
            blk = [t for t in times[i1:i2] if t]
            if not blk: continue                          # kaynakta karşılığı yok: fill_missing doldurur
            a, b = blk[0]['start'], blk[-1]['end']
            wt = np.array([max(1, len(norm(w))) for w in script[j1:j2]], float); cs = np.concatenate([[0], np.cumsum(wt)]) / wt.sum()
            for k in range(j2 - j1): out[j1 + k] = {'start': a + cs[k] * (b - a), 'end': a + cs[k + 1] * (b - a)}
    return out

def main():
    D = sys.argv[1].rstrip('/'); V = os.path.join(D, 'voice')
    dil = arg('--dil') or ('en' if os.path.exists(os.path.join(V, 'EN')) else 'tr')
    ses = arg('--ses') or next((p for p in (os.path.join(V, 'voice.ogg'), os.path.join(V, 'voice.wav'), os.path.join(D, 'audio', 'mix.wav')) if os.path.exists(p)), None)
    if not ses: raise SystemExit('ses dosyası yok (voice/voice.ogg, voice/voice.wav ya da audio/mix.wav)')
    J = json.load(open(os.path.join(V, 'words.json'), encoding='utf-8')); W = J['words']
    if J.get('hizalama', '').startswith('whisperx') and os.path.exists(os.path.join(V, 'words_tahmin.json')):
        J = json.load(open(os.path.join(V, 'words_tahmin.json'), encoding='utf-8')); W = J['words']   # yeniden çalıştırma: tahminden başla
    L = read_lines(os.path.join(V, 'script.txt'))
    if L is None and J.get('lines') and 'text' in J['lines'][0]:          # dizivanastudio: satırlar kopru.py'den
        L = [l['text'] for l in J['lines']]
    S = read_lines(os.path.join(V, 'say.txt')) or L
    if 'lines' in J: spans = [(l['start'], l['end']) for l in J['lines']]
    else:                                                 # eski words.json: satır aralıkları kelimelerden çıkarılır
        cnt = [len(l.split()) for l in L]
        if sum(cnt) != len(W): raise SystemExit(f'words.json ({len(W)} kelime) script.txt ile uyuşmuyor ({sum(cnt)})')
        spans, k = [], 0
        for c in cnt: spans.append((W[k]['start'], W[k + c - 1]['end'])); k += c

    import whisperx, torch
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    audio = whisperx.load_audio(ses); dur = len(audio) / 16000
    model, meta = whisperx.load_align_model(language_code=dil, device='cpu')
    new, rep, k0, kept = [], [], 0, 0
    for i, (line, say) in enumerate(zip(L, S)):
        sw, lw = say.split(), line.split(); a, b = spans[i]
        old = W[k0:k0 + len(lw)]; k0 += len(lw)
        pad_a = max(0, a - .08); pad_b = min(dur, b + .08)
        try:
            r = whisperx.align([{'text': say, 'start': pad_a, 'end': pad_b}], model, meta, audio, 'cpu', return_char_alignments=False)
            ws = r.get('word_segments') or [w for s in r['segments'] for w in s.get('words', [])]
        except Exception as e:
            ws = []; print(f'satır {i}: hizalama hatası {str(e)[:80]}')
        if len(ws) != len(sw):                            # sayı tutmazsa kelime metnine göre eşle
            sm = difflib.SequenceMatcher(None, [norm(w) for w in sw], [norm(w.get('word', '')) for w in ws], autojunk=False)
            got = [None] * len(sw)
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op == 'equal':
                    for q in range(i2 - i1): got[i1 + q] = ws[j1 + q]
            ws = got
        timed = [({'start': float(w['start']), 'end': float(w['end'])} if w and w.get('start') is not None and w.get('end') is not None else None) for w in ws]
        score = np.mean([w.get('score', 0) for w in ws if w and w.get('score') is not None] or [0])
        ok = sum(t is not None for t in timed) >= max(1, .6 * len(sw)) and score >= .2
        if ok:
            st = fill_missing(map_to_script(sw, timed, lw), a, b)
            st = [{'start': min(max(t['start'], pad_a), pad_b), 'end': min(max(t['end'], pad_a), pad_b)} for t in st]
            for o, t in zip(old, st):                 # kelimenin diğer alanları (konuşmacı, vurgu...) korunur
                nw = dict(o); nw['start'] = round(t['start'], 3); nw['end'] = round(t['end'], 3); new.append(nw)
            d = [abs(t['start'] - o['start']) for t, o in zip(st, old)]
            rep.append(f'{i:02d} tamam  skor {score:.2f}  ort. fark {np.mean(d):.2f} sn  en büyük {max(d):.2f} sn | {line}')
        else:
            new.extend(old); kept += 1
            rep.append(f'{i:02d} TAHMİN KALDI (skor {score:.2f}, ölçülen {sum(t is not None for t in timed)}/{len(sw)}) | {line}')
    if not os.path.exists(os.path.join(V, 'words_tahmin.json')):
        json.dump({k: v for k, v in J.items()}, open(os.path.join(V, 'words_tahmin.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    out = dict(J); out['words'] = new; out['hizalama'] = f'whisperx-{dil}'
    json.dump(out, open(os.path.join(V, 'words.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    alld = [abs(n['start'] - o['start']) for n, o in zip(new, W)]
    head = (f'WhisperX hizalama ({dil}, ses: {os.path.basename(ses)}): {len(new)} kelime, {len(L) - kept}/{len(L)} satır ölçüldü, '
            f'tahminle ortalama fark {np.mean(alld):.2f} sn, en büyük {max(alld):.2f} sn')
    open(os.path.join(V, 'hizalama.txt'), 'w', encoding='utf-8').write(head + '\n' + '\n'.join(rep) + '\n')
    print(head); print('\n'.join(rep))

if __name__ == '__main__':
    main()
