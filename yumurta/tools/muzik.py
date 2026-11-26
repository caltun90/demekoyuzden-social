"""Openverse'ten telifsiz müzik bulur, librosa ile vuruşlarını çıkarır ve parçayı sahne geçişleri vuruşa denk gelecek
yerden keser. Bulut oturumunda Openverse kapalı olduğu için GitHub Actions'ta (`.github/workflows/muzik.yml`) çalışır.

  python3 tools/muzik.py <story_dir> [--sorgu "playful curious"] [--lisans cc0|cc0,by] [--kullanilan <json>]

Girdi : <story>/audio/cues.json (render.mjs --cues: DUR ve whoosh/cut geçiş saatleri)
Çıktı : <story>/audio/muzik.ogg (video boyu, giriş/çıkış yumuşatmalı), <story>/audio/muzik.json (kaynak, lisans, atıf,
        tempo, kesim noktası, kaç geçişin vuruşa oturduğu). mix.py muzik.ogg varsa kendi bestesi yerine onu kullanır.
Kurallar: yalnızca ticari kullanıma açık lisans (varsayılan CC0; "by" verilirse CC BY de olur, o zaman açıklamaya
muzik.json'daki "atif" satırı yazılır). NC ve ND lisanslar hiçbir zaman alınmaz. Aynı parça iki kez kullanılmaz
(--kullanilan listesi). Uygun parça yoksa hiçbir şey yazmaz, çıkış kodu 2: mix.py kendi bestesiyle devam eder.
"""
import sys, os, json, random, subprocess, urllib.request, urllib.parse
import numpy as np

UA = {'User-Agent': 'demekoyuzden-muzik/1.0 (github.com/caltun90)'}

def arg(name, default=None):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default

def get_json(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))

def ara(sorgu, lisans, page=1):
    q = urllib.parse.urlencode({'q': sorgu, 'license': lisans, 'category': 'music', 'page_size': 50, 'page': page, 'mature': 'false'})
    return get_json('https://api.openverse.org/v1/audio/?' + q).get('results', [])

def main():
    D = sys.argv[1].rstrip('/'); A = os.path.join(D, 'audio')
    sorgu = arg('--sorgu', 'upbeat playful'); lisans = arg('--lisans', 'cc0')
    kul_p = arg('--kullanilan'); kul = set(json.load(open(kul_p))) if kul_p and os.path.exists(kul_p) else set()
    cues = json.load(open(os.path.join(A, 'cues.json'), encoding='utf-8')); DUR = float(cues['DUR'])
    cuts = sorted(c['t'] for c in cues['cues'] if c['type'] in ('whoosh', 'cut'))
    bad = ('-nc', 'nc-', 'nd')
    adaylar = []
    for s in [sorgu] + ([w for w in sorgu.split()] if len(sorgu.split()) > 1 else []) + ['instrumental']:
        for r in ara(s, lisans):
            lic = (r.get('license') or '').lower()
            if any(b in lic for b in bad) or r['id'] in kul or not r.get('url'): continue
            d = (r.get('duration') or 0) / 1000
            if d < DUR + 3 or d > 900: continue
            if r['id'] not in [x['id'] for x in adaylar]: adaylar.append(r)
        if len(adaylar) >= 12: break
    if not adaylar: print('uygun müzik bulunamadı (sorgu/lisans):', sorgu, lisans); sys.exit(2)
    random.seed(os.path.basename(D)); random.shuffle(adaylar)       # her videoda farklı parça, aynı hikâyede aynı seçim
    import librosa
    for r in adaylar[:6]:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(r['url'], headers=UA), timeout=120).read()
            open('/tmp/_m.bin', 'wb').write(raw)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', '/tmp/_m.bin', '-ac', '1', '-ar', '22050', '/tmp/_m.wav'], check=True)
            y, sr = librosa.load('/tmp/_m.wav', sr=22050, mono=True)
        except Exception as e:
            print('indirilemedi:', r.get('title'), str(e)[:80]); continue
        L = len(y) / sr
        if L < DUR + 2: continue
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
        tempo = float(np.atleast_1d(tempo)[0])
        if len(beats) < 8 or not 60 <= tempo <= 180: print('vuruşu belirsiz:', r.get('title'), tempo); continue
        rms = librosa.feature.rms(y=y, hop_length=512)[0]; rt = np.arange(len(rms)) * 512 / sr
        loud = np.percentile(rms, 70)
        best = None
        for o in np.arange(0, L - DUR - 1, .05):
            seg = rms[(rt >= o) & (rt < o + DUR)]
            if len(seg) == 0 or np.mean(seg) < .45 * loud: continue          # sessiz giriş ya da kapanış bölgesi olmasın
            hits = sum(np.exp(-(np.min(np.abs(beats - (c + o))) / .06) ** 2) for c in cuts)
            start_on_beat = np.exp(-(np.min(np.abs(beats - o)) / .05) ** 2)
            sc = hits + .5 * start_on_beat + .3 * np.mean(seg) / loud
            if best is None or sc > best[0]: best = (sc, o)
        if best is None: print('uygun bölüm yok:', r.get('title')); continue
        o = float(best[1])
        oturan = sum(1 for c in cuts if np.min(np.abs(beats - (c + o))) < .08)
        out_ogg = os.path.join(A, 'muzik.ogg')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{o:.3f}', '-t', f'{DUR + .3:.3f}', '-i', '/tmp/_m.bin',
                        '-af', f'afade=t=in:d=0.12,afade=t=out:st={max(0, DUR - 1.2):.3f}:d=1.2', '-ac', '2', '-ar', '48000',
                        '-c:a', 'libvorbis', '-q:a', '6', out_ogg], check=True)
        lic = (r.get('license') or '').upper(); ver = r.get('license_version') or ''
        bilgi = {'id': r['id'], 'baslik': r.get('title'), 'sanatci': r.get('creator'), 'lisans': f'CC {lic} {ver}'.strip(),
                 'lisans_url': r.get('license_url'), 'kaynak': r.get('foreign_landing_url'), 'saglayici': r.get('source'),
                 'atif': r.get('attribution') or f"{r.get('title')} - {r.get('creator')} ({lic} {ver})",
                 'atif_gerekli': lic != 'CC0', 'tempo': round(tempo, 1), 'kesim_sn': round(o, 2),
                 'gecis': len(cuts), 'vurusa_oturan_gecis': oturan, 'sorgu': sorgu}
        json.dump(bilgi, open(os.path.join(A, 'muzik.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if kul_p:
            kul.add(r['id']); json.dump(sorted(kul), open(kul_p, 'w'), indent=0)
        print(f"seçildi: {bilgi['baslik']} | {bilgi['sanatci']} | {bilgi['lisans']} | {tempo:.0f} bpm | kesim {o:.2f} sn | "
              f"{oturan}/{len(cuts)} geçiş vuruşta | {bilgi['kaynak']}")
        return
    print('adayların hiçbiri uymadı'); sys.exit(2)

if __name__ == '__main__':
    main()
