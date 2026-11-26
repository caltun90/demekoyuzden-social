#!/usr/bin/env python3
"""İçi Nasıl? Short'u birleştirir: anatomy-reveal filmi + kanca yazısı + kelime kelime altyazı + ses miksi.

  python3 anatomi/birlestir.py <hikaye_klasoru> <film.mp4> "<KANCA YAZISI>" [--cikti videos/<ad>-dikey.mp4]

Hikâye klasörü yumurta hikâyesiyle aynı düzendedir (yumurta/stories/<YYYY-MM-DD>-ic-<slug>/): voice/words.json
(WhisperX ile ölçülmüş), audio/mix.wav (mix.py). Altyazı yumurta videolarıyla aynı biçimde (tek kelime ya da kısa
çift, beyaz, koyu kontur) ama nesneyi kapatmasın diye yüksekliğin %80'inde; kanca yazısı sarı, %20'de, 0-2,0 sn,
2,4 sn'de söner. Çıktı 1080x1920, 30 fps, x264 crf 22, AAC 192k, -14 LUFS (mix.wav zaten öyle).
"""
import json, os, re, subprocess, sys

def arg(n, d=None):
    a = sys.argv
    return a[a.index(n) + 1] if n in a else d

def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def groups(words):                                   # captions.js groupWords ile aynı
    out, i = [], 0
    while i < len(words):
        w = words[i]; n = words[i + 1] if i + 1 < len(words) else None
        bare = re.sub(r'[^\w]', '', w['word'])
        if n and len(bare) <= 3 and not re.search(r'[.,:;!?"]$', w['word']) and len(w['word'] + ' ' + n['word']) <= 14:
            out.append({'text': w['word'] + ' ' + n['word'], 'start': w['start'], 'end': n['end']}); i += 2
        else:
            out.append({'text': w['word'], 'start': w['start'], 'end': w['end']}); i += 1
    for k, c in enumerate(out):
        c['until'] = out[k + 1]['start'] if k + 1 < len(out) else c['end'] + .4
    return out

def ass(words, kanca):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Alt,Poppins,90,&H00FFFFFF,&H00FFFFFF,&H001C0C14,&H8C140A06,-1,0,0,0,100,100,0,0,1,9,3,5,60,60,0,1
Style: Kanca,Poppins,112,&H005AE1FF,&H005AE1FF,&H001C0C14,&H8C140A06,-1,0,0,0,100,100,0,0,1,12,4,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    w = kanca.strip().split()
    if len(w) <= 1 or len(' '.join(w)) <= 14:
        lines = [' '.join(w)]
    else:                                             # iki satır: en uzun satırı en kısa yapan bölme
        k = min(range(1, len(w)), key=lambda k: max(len(' '.join(w[:k])), len(' '.join(w[k:]))))
        lines = [' '.join(w[:k]), ' '.join(w[k:])]
    fs = int(min(112, 940 / (max(len(l) for l in lines) * .46)))   # 940 px'e sığsın (Poppins Bold büyük harf ~0,42 em)
    for i, ln in enumerate(lines):
        y = int(1920 * .20 + i * fs * 1.12)
        ev.append(f'Dialogue: 1,{ts(0)},{ts(2.4)},Kanca,,0,0,0,,{{\\pos(540,{y})\\fs{fs}\\fad(0,400)\\t(0,120,\\fscx100\\fscy100)\\fscx108\\fscy108}}{ln}')
    for c in groups(words):
        if c['until'] <= 2.4 and c['start'] < 2.0:
            continue                                  # kanca cümlesi: dev yazı zaten ekranda
        txt = c['text'].replace('"', '').replace('“', '').replace('”', '')
        ev.append(f'Dialogue: 0,{ts(max(c["start"] - .02, 2.4 if c["start"] < 2.4 else 0))},{ts(c["until"])},Alt,,0,0,0,,'
                  f'{{\\pos(540,{int(1920 * .80)})\\fscx106\\fscy106\\t(0,70,\\fscx100\\fscy100)}}{txt}')
    return head + '\n'.join(ev) + '\n'

def main():
    D, film, kanca = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3]
    out = arg('--cikti') or os.path.join('videos', os.path.basename(D) + '-dikey.mp4')
    words = json.load(open(os.path.join(D, 'voice', 'words.json'), encoding='utf-8'))['words']
    sub = os.path.join(D, 'audio', 'altyazi.ass'); open(sub, 'w', encoding='utf-8').write(ass(words, kanca))
    mix = os.path.join(D, 'audio', 'mix.wav')
    fonts = '/usr/share/fonts/truetype/google-fonts'
    vf = f"scale=1080:1920,fps=30,subtitles={sub}:fontsdir={fonts}"
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', film, '-i', mix, '-map', '0:v:0', '-map', '1:a:0', '-vf', vf,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', out], check=True)
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip()
    print('->', out, d, 'sn')

if __name__ == '__main__':
    main()
