# Niş video üretim kiti ("Demek O Yüzden" kanalı)

Günlük 1 dakikalık videoları üretmek için araçlar. Kit bu deponun kökünde durur; videolar `videos/`, yapılanlar `log.json`.
Seriler üstteki etiketle ayrılır ("1 DAKİKADA PSİKOLOJİ", "1 DAKİKADA BİLİM", "1 DAKİKADA DİL", "1 DAKİKADA TARİH").

## Kararlar (Cem)
- HER video iki formatta: yatay 1920x1080 ve dikey 1080x1920. 30 fps, 45-62 sn.
  `./build.sh <ad>` ikisini üretir: `<ad>-yatay.mp4`, `<ad>-dikey.mp4`.
- Yatay düzen: dikey sahne çizimi solda (dikey koordinatlarda y 280-1260), sağda etiket + `TITLE` + büyük altyazı.
  Sahne çizimleri y 280-1260 dışına taşmamalı.
- Dil Türkçe. Psikoloji ağırlıklı; arada gündelik bilim, dil, tarih. Her video tek bir niş soru ve izleyene "demek o yüzden!" dedirtmeli.
- Görsel: krem zemin, el çizimi çizgi adam, mercan/turkuaz/sarı vurgu, büyük altyazı, üstte seri etiketi.
- Ses: Gemini TTS, ses = Achird. Model: gemini-3.1-flash-tts-preview.
  gemini-3.8-flash-tts KULLANMA: stil talimatını da sesli okuyor.
- Cem'e yazılan her şey Türkçe, kısa, sade. Em dash yok.

## Dosyalar
- `script.py`: senaryo satırları (sahne no, altyazı metni, gerekirse TTS için ayrı yazım).
- `voice_google.py`: Gemini TTS. Tüm senaryoyu tek istekte okutur, `voice/raw_google.wav` yazar, satırlara böler.
- `sync.py`: parça dökümü (`list`), satır eşleme ve duraklama kısaltma (`build`), altyazı kontrolü (`check`).
- `render.py`: çizim motoru + 6 sahne. `FMT=v` (dikey) veya `FMT=h` (yatay). Yeni videoda `scene1..6`, `HL`, `TITLE`,
  gerekirse `tag()` içindeki seri etiketi yeniden yazılır. Yardımcı fonksiyonlara dokunma.
- `build.sh`: iki formatı üretir, birleştirir, sesi ekler.

## Yeni video için akış
1. Konu seç (aşağıdaki havuz + log.json), en az iki güvenilir kaynaktan doğrula.
2. `script.py`: 14-16 satır, 110-120 kelime: kanca, "bunun adı var", deney/kanıt, neden olur, ipucu, kapanış.
   KAPANIŞ KURALI: "yarın" deme. Son satır "Bir sonraki videoda görüşmek üzere!"; sahne 6'daki büyük yazı "Bir sonraki videoda / görüşürüz!".
   - Rakamla yazılan yıl gibi ifadeler (ör. "1927'de") altyazıda kendi satırı olsun, TTS metni yazıyla ("Bin dokuz yüz yirmi yedide").
     Aksi halde altyazı sesin önüne geçer. Böyle bölünen satır sayıya dahil değil.
   - Yabancı adlar için TTS metnini okunuşla yaz (Zeigarnik -> Zaygarnik).
3. Ses ve hizalama (ÖNEMLİ, her seferinde):
   ```
   pip install --break-system-packages skia-python soundfile numpy
   python3 voice_google.py Achird gemini-3.1-flash-tts-preview    # hizalamasi guvenilir degil, sadece ham kayit icin
   python3 sync.py list                                           # parcalar + yazi dokumu
   python3 sync.py build "0-1,2-3,4,..."                          # her satira dusen parca araligi (satir sayisi kadar)
   ```
   `list` çıktısını senaryo ile karşılaştır: eksik ya da yanlış okunan cümle varsa sesi yeniden üret.
   `build` satır içi duraklamaları 0,22 sn'ye indirir; ham kayıt 65 sn üstü çıksa bile toplam 62 sn altına iner.
   Toplam süre 62 sn'yi geçerse senaryoyu kısalt ya da `GAP_AFTER` değerlerini azalt.
4. `render.py` sahnelerini yaz. Zamanları `L(i)` (satır başı/sonu) ve `cap_start(satır, 'kelime', varsayılan)` ile sese bağla.
5. `python3 sync.py check`: her altyazı penceresinde duyulan söz, altyazıyla aynı olmalı. Altyazı sesten ÖNCE gelmemeli.
6. Kare kontrolü: `FMT=v python3 render.py still <klasör> 3 17 30 ...` ve `FMT=h` ile en az 6'şar kare; aç ve bak.
7. `./build.sh <YYYY-MM-DD>-<slug>`; süre, ses ve 3 kare son kontrol.
8. `voice/`, `scenes_*`, `silent_*`, `list_*`, kare klasörleri ve kökteki mp4'ler depoya eklenmez.

## Paylaşım
- Dikey video: Buffer (bahsish.co hesabı, yalnızca API anahtarıyla) üzerinden YouTube Short ("Demek O Yüzden"), TikTok, Instagram Reel. 19:00.
- Yatay video: YouTube'a normal video. Buffer yalnızca Short gönderdiği için YouTube Studio'dan elle yüklenir.
- Claude'a bağlı Buffer bağlayıcısı engrowapp hesabına aittir (Engrow, Pofu Kids); bu kanal için kullanılmaz.
- Buffer dosya yüklemesi kabul etmez; video açık bir https adresinde durmalı (bu deponun raw adresi).

## Konu havuzu
Yapıldı: Kapı eşiği etkisi (pilot, psikoloji).
Sırada (bu sırayla, bir psikoloji bir başka alan):
1. Zeigarnik etkisi: yarım kalan iş neden akıldan çıkmaz? (psikoloji) Not: render.py şu an bu konunun sahnelerini içeriyor;
   2025 meta-analizi (Ghibellini ve Meier) hafıza farkını doğrulamadı, "geri dönme isteği" ise güçlü. Kesinmiş gibi anlatma.
2. Gökyüzü neden mavi, gün batımı neden kırmızı? (bilim)
3. Sahne ışığı etkisi (psikoloji)
4. Esnemek neden bulaşıcı? (bilim)
5. Dilimin ucunda hissi (psikoloji)
6. Klavyede harfler neden alfabetik sırada değil? (tarih)
7. IKEA etkisi (psikoloji)
8. Soğan doğrarken neden ağlarız? (bilim)
9. Barnum etkisi (psikoloji)
10. "Tamam" kelimesi nereden geliyor? (dil)
Liste bitince aynı dengeyle (bir psikoloji, bir başka alan) yeni konular bul.
