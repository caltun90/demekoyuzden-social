# Niş video üretim kiti ("Demek O Yüzden" kanalı)

Günlük 1 dakikalık videoları üretmek için araçlar. Kit bu deponun kökünde durur; videolar `videos/`, yapılanlar `log.json`.
Seriler üstteki etiketle ayrılır ("1 DAKİKADA PSİKOLOJİ", "1 DAKİKADA BİLİM"). Başka seri yok.

## Kararlar (Cem)
- HER video iki formatta: yatay 1920x1080 ve dikey 1080x1920. 30 fps, 45-62 sn.
  `./build.sh <ad>` ikisini üretir: `<ad>-yatay.mp4`, `<ad>-dikey.mp4`.
- Yatay düzen: dikey sahne çizimi solda (dikey koordinatlarda y 280-1260), sağda etiket + `TITLE` + büyük altyazı.
  Sahne çizimleri y 280-1260 dışına taşmamalı.
- Dil Türkçe. Kanal yalnızca psikoloji ve gündelik bilim; tarih, dil gibi başka tür video yok (Cem, 2026-11-13).
  Konular "Esnemek neden bulaşıcı?" gibi herkesin kendi yaşadığı, akılda kalan sorular olsun.
  Her video tek bir niş soru ve izleyene "demek o yüzden!" dedirtmeli.
- Görsel: krem zemin, el çizimi çizgi adam, mercan/turkuaz/sarı vurgu, büyük altyazı, üstte seri etiketi.
- Seri etiketi büyük (dikey 46 punto, yatay 40). Telefonda küçük kalmasın; küçültme.
- KAPAK: videonun ilk karesi kapaktır. İlk 0,45 sn (ses başlamadan) sahne 1'in en çarpıcı anı + dev kanca sorusu görünür
  (`COVER`, `COVER_AT`). Kanca kısa, merak uyandıran bir soru olmalı; görünce tıklatmalı.
- Dikeyde etiketin altında kanca sorusu (`HOOK`) video boyunca durur. YouTube Short kapağını kendi seçtiği kareden
  aldığı için her karede konu anlaşılmalı. Sahne çizimleri dikeyde y 315'in üstüne çıkmamalı (kanca satırıyla çakışır).
- Ses: Gemini TTS, ses = Achird. Model: gemini-3.1-flash-tts-preview.
  gemini-3.8-flash-tts KULLANMA: stil talimatını da sesli okuyor.
- Cem'e yazılan her şey Türkçe, kısa, sade. Em dash yok.

## Dosyalar
- `script.py`: senaryo satırları (sahne no, altyazı metni, gerekirse TTS için ayrı yazım).
- `voice_google.py`: Gemini TTS. Tüm senaryoyu tek istekte okutur, `voice/raw_google.wav` yazar, satırlara böler.
- `sync.py`: parça dökümü (`list`), satır eşleme ve duraklama kısaltma (`build`), altyazı kontrolü (`check`).
- `render.py`: çizim motoru + 6 sahne. `FMT=v` (dikey) veya `FMT=h` (yatay). Yeni videoda `scene1..6`, `HL`, `TITLE`, `HOOK`, `COVER`, `COVER_AT`,
  gerekirse `tag()` içindeki seri etiketi yeniden yazılır. Yardımcı fonksiyonlara dokunma.
- `build.sh`: iki formatı üretir, birleştirir, sesi ekler. Bir sahne render edilemezse durur, video üretmez.
- `setup.sh`: bulut ortamı kurulumu (libEGL, Python paketleri, Poppins fontları). Tekrar çalıştırmak güvenli.

## Yeni video için akış
1. Konu seç (aşağıdaki havuz + log.json), en az iki güvenilir kaynaktan doğrula.
2. `script.py`: 14-16 satır, 110-120 kelime: kanca, "bunun adı var", deney/kanıt, neden olur, ipucu, kapanış.
   KAPANIŞ KURALI: "yarın" deme. Son satır "Bir sonraki videoda görüşmek üzere!"; sahne 6'daki büyük yazı "Bir sonraki videoda / görüşürüz!".
   - Rakamla yazılan yıl gibi ifadeler (ör. "1927'de") altyazıda kendi satırı olsun, TTS metni yazıyla ("Bin dokuz yüz yirmi yedide").
     Aksi halde altyazı sesin önüne geçer. Böyle bölünen satır sayıya dahil değil.
   - Yabancı adlar için TTS metnini okunuşla yaz (Zeigarnik -> Zaygarnik).
3. Kurulum (her yeni bulut oturumunda bir kez): `./setup.sh`. Betiğin yaptıkları:
   ```
   apt-get update && apt-get install -y libegl1                                  # skia libEGL.so.1 ister
   python3 -m pip install --break-system-packages skia-python soundfile numpy    # düz "pip" KULLANMA
   # Poppins-Regular/Medium/Bold.ttf -> /usr/share/fonts/truetype/google-fonts/
   ```
   - `pip` ile `python3` farklı Python sürümlerine bağlı olabilir. Paket hep `python3 -m pip` ile kurulur.
   - Poppins fontları bulut ortamında hazır gelmez. `https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700`
     adresi tarayıcı olmayan istemciye (curl) ttf bağlantılarını verir; betik bunları indirir.
   Ses ve hizalama (ÖNEMLİ, her seferinde):
   ```
   python3 voice_google.py Achird gemini-3.1-flash-tts-preview    # hizalamasi guvenilir degil, sadece ham kayit icin
   python3 sync.py list                                           # parcalar + yazi dokumu
   python3 sync.py build "0-1,2-3,4,..."                          # her satira dusen parca araligi (satir sayisi kadar)
   ```
   `list` çıktısını senaryo ile karşılaştır: eksik ya da yanlış okunan cümle varsa sesi yeniden üret.
   `build` satır içi duraklamaları 0,22 sn'ye indirir; ham kayıt 65 sn üstü çıksa bile toplam 62 sn altına iner.
   Toplam süre 62 sn'yi geçerse senaryoyu kısalt ya da `GAP_AFTER` değerlerini azalt.
4. `render.py` sahnelerini yaz. Zamanları `L(i)` (satır başı/sonu) ve `cap_start(satır, 'kelime', varsayılan)` ile sese bağla.
   Her videoda `HOOK` (en fazla ~26 karakter soru), `COVER` (aynı sorunun 2-3 kısa satırı, büyük harf) ve
   `COVER_AT` (sahne 1'in kapakta görünecek anı, sn) değerlerini de yaz.
5. `python3 sync.py check`: her altyazı penceresinde duyulan söz, altyazıyla aynı olmalı. Altyazı sesten ÖNCE gelmemeli.
6. Kare kontrolü: `FMT=v python3 render.py still <klasör> 0 3 17 30 ...` ve `FMT=h` ile en az 6'şar kare; aç ve bak.
   `0` kapak karesidir: yazı taşmıyor mu, çizim çarpıcı mı, tek başına merak uyandırıyor mu?
7. `./build.sh <YYYY-MM-DD>-<slug>`; süre, ses ve 3 kare son kontrol.
8. `voice/`, `scenes_*`, `silent_*`, `list_*`, kare klasörleri ve kökteki mp4'ler depoya eklenmez.

## Paylaşım
- Dikey video: Buffer (bahsish.co hesabı, yalnızca API anahtarıyla) üzerinden YouTube Short ("Demek O Yüzden"), TikTok, Instagram Reel. 19:00.
- Yatay video: YouTube'a normal video. Buffer yalnızca Short gönderdiği için YouTube Studio'dan elle yüklenir.
- Claude'a bağlı Buffer bağlayıcısı engrowapp hesabına aittir (Engrow, Pofu Kids); bu kanal için kullanılmaz.
- Buffer dosya yüklemesi kabul etmez; video açık bir https adresinde durmalı (bu deponun raw adresi).
- Kapak: Instagram ve TikTok gönderisinde video varlığına `metadata: { thumbnailOffset: 200 }` ver (ilk kare = kapak).
  YouTube Short kapağı Buffer/API ile seçilemez; YouTube kendi seçer, Cem isterse YouTube uygulamasından ilk kareyi seçer.
- Yatay videoyla birlikte yatay kapak karesini de Cem'e gönder (`FMT=h python3 render.py still <klasör> 0`); YouTube'da küçük resim olarak yükler.

## Konu havuzu
Yapıldı: Kapı eşiği etkisi (pilot, psikoloji); Zeigarnik etkisi (psikoloji); Gökyüzü neden mavi, gün batımı neden kırmızı? (bilim); Sahne ışığı etkisi (psikoloji); Esnemek neden bulaşıcı? (bilim); Dilimin ucunda hissi (psikoloji); Klavyede harfler neden alfabetik sırada değil? (tarih).
Sırada (bu sırayla, bir psikoloji bir bilim):
1. Bir kelimeyi çok tekrarlayınca neden anlamsızlaşır? (psikoloji)
2. Kendimizi neden gıdıklayamayız? (bilim)
3. Şarkı neden dile dolanır? (psikoloji)
4. Kendi sesimiz kayıtta neden yabancı gelir? (bilim)
5. Yeni öğrendiğin şeyi neden her yerde görmeye başlarsın? (psikoloji)
6. Soğan doğrarken neden ağlarız? (bilim)
7. Burç yorumları neden hep tutar gibi gelir? Barnum etkisi (psikoloji)
8. Parmaklarımız suda neden buruşur? (bilim)
9. Bulutlarda neden yüz görürüz? (psikoloji)
10. Uykuya dalarken neden düşer gibi sıçrarız? (bilim)
11. Kendi yaptığımız şeyi neden daha çok severiz? IKEA etkisi (psikoloji)
12. Nane neden serinletir, acı biber neden yakar? (bilim)
Liste hiç bitmesin: "Sırada" 4 konunun altına inince aynı dengeyle (bir psikoloji, bir bilim) en az 6 yeni konu ekle. Tarih ve dil konusu ekleme.
Konu seçme ölçütü (Cem onayladı, 2026-11-13; kalıcı):
- Herkesin kendi yaşadığı, gündelik bir şey olsun (esnemek, gıdıklanmak, dile dolanan şarkı gibi). Başlık kısa bir "neden" sorusu olsun.
- Cevabı tek cümleyle anlatılabilsin ve izleyene "demek o yüzden!" dedirtsin. Etki adları (Barnum, IKEA) başlıkta değil, cevabın içinde geçsin.
- Sağlam kaynağı olsun; tartışmalı ya da tekrarlanamamış bulgu, tıbbi tavsiye ve "Yapıldı" listesindekilerin benzeri olmasın.
