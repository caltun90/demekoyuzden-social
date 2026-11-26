# İçi Nasıl? (haftalık anatomy Short, Cem 27 Kasım 2026)

Demek O Yüzden için haftada bir dikey Short: gündelik bir eşya kâğıt üzerinde mürekkep çizimi gibi döner, ayrıntılara
yakınlaşır, bir özelliği çalışır, parçalarına ayrılır ve yeniden birleşir; seslendirme eşyanın "neden/nasıl" sorusunu
o parçalar üzerinden cevaplar. Film `skill/` (anatomy-reveal, MIT, Ann Nguyen) ile kodla çizilir; ses, altyazı ve
müzik yumurta araçlarıyla aynıdır. Kanalın bütün kuralları (`../KIT.md`: güvenlik, kaynak, yapay zeka etiketi, ilk 2
saniye kancası) burada da geçerlidir. Cem'e yazılan her şey Türkçe, kısa ve sade; uzun tire (em dash) yok.

## 1. Konu
- İçindeki parçalarla açıklanabilen gündelik bir eşya ve onun merak edilen sorusu: termos sıcağı nasıl tutar, düdüklü
  tencere neden daha hızlı pişirir, buzdolabı içini nasıl soğutur, kalem pil nasıl elektrik verir, çakmak nasıl yanar,
  mikrodalga yemeği nasıl ısıtır, kulaklık sesi nasıl çıkarır, ütü, tost makinesi, kapı kilidi, su ısıtıcısı, mekanik saat...
- `log.json`'daki `"tur": "ic-nasil"` kayıtlarına bak, aynı eşyayı tekrar etme. Marka ve logo çizme (nötr eşya).
- Gerçek ölçüleri ve iç yapıyı araştır (söküm yazıları, üretici şemaları); seslendirmedeki her bilgi iki kaynakla doğrulanır.

## 2. Senaryo ve ses (yumurta düzeni)
- Klasör: `yumurta/stories/<YYYY-MM-DD>-ic-<slug>/`. `voice/script.txt`: 7-11 satır, her satır tek cümle, toplam 30-45 sn.
- Yapı filmin vuruşlarıyla aynı sırada: kanca (en fazla 8 kelime, 2 sn dolmadan biter, ör. "Termos sıcağı nasıl tutar?")
  → eşya döner, "Bakın," ile kurulum → 1-2 ayrıntıya yakınlaşma (her biri bir cümle) → özellik çalışır → parçalarına
  ayrılır ve asıl sırrı veren iç parça anlatılır → yeniden birleşir, tek cümlelik son vuruş.
- Ses: `python3 yumurta/tools/ses.py tts|check|build` (Achird, `yumurta/README.md` adım 3), sonra WhisperX
  (`yumurta/README.md` adım 3b). Film süresi = `words.json` süresi + 0,8 sn.

## 3. Film (anatomy-reveal)
```bash
export CHROME_PATH=/usr/bin/google-chrome MAGICK=convert      # ImageMagick 7 yok; convert aynı işi görür
node anatomi/skill/scripts/new-project.mjs /tmp/ic-<slug>      # şablonu kopyalar, kurar, örneği çizer
```
- `anatomi/skill/SKILL.md` ve `references/` (object, objects, shots, look) okunur ve uygulanır. Zaman için nesne
  40-90 parça olsun (beceri 100-150 önerir); dış kabuk, 1-2 ayrıntı ve sırrı veren iç parçalar yeter.
- Ekrandaki bütün yazılar Türkçe: `object/film.mjs` başlık, açıklama ve etiketler, `motion/timeline.mjs` etiketleri
  (ör. "VAKUM KATMANI · ısı geçemez"). "Fig 1" ve "ANATOMY" üst yazıları "Şekil 1" ve "İÇİ NASIL?" olur.
- `node motion/build.mjs --duration <sn> --ratio 9:16`, sonra `motion/timeline.mjs` vuruşlarını seslendirmeye oturt:
  her ayrıntı çekimi onu söyleyen kelimenin saatinde başlar (`voice/words.json`). `node motion/render.mjs stills ...`
  ile kareleri Read ile aç, `node motion/scan.mjs` temiz olmalı.
- Render: `node motion/render.mjs blur out/blur --step 4 --most 10` ARKA PLANDA (iki çekirdekte film saniyesi başına
  yaklaşık 2 dk; 40 sn ≈ 70-80 dk), birkaç dakikada bir ilerlemeye bak; bitince `node motion/encode.mjs out/blur out/film.mp4`.
- Nesnenin kaynak dosyalarını (`object/geometry.mjs`, `object/film.mjs`, `motion/timeline.mjs`) hikâye klasöründe
  `anatomi/` altına kopyala ve commit et (sonraki eşyalarda örnek olur).

## 4. Müzik, miks, birleştirme
- `audio/cues.json`: `{"DUR": <film süresi>, "cues": [{"t": <her vuruşun başı>, "type": "whoosh"}, ...]}` yaz, push et,
  `muzik.yml` ile müzik al (`yumurta/README.md` adım 6), sonra `python3 yumurta/engine/audio/mix.py yumurta/stories/<ad>`.
- `python3 anatomi/birlestir.py yumurta/stories/<ad> /tmp/ic-<slug>/out/film.mp4 "<EN FAZLA 5 KELİMELİK KANCA>"`
  → `videos/<ad>-dikey.mp4` (kanca yazısı 0-2 sn, kelime kelime altyazı, -14 LUFS).
- Kontrol: 0,0 / 0,5 / 1,0 / 1,9 sn ve her vuruştan bir kare (Read ile aç), ilk kareyi 3:4 kırpıp kapak güvenli alanına
  bak (`crop=iw:iw*4/3`), süre 30-50 sn, ses var. Yazı nesneyi ya da altyazıyı kapatıyorsa düzelt.

## 5. Kayıt ve yayın (Cem 27 Kasım 2026: "Otomatik yayınlansın, bana sormasın")
- Kalite kontrolünden (bölüm 4) geçmeyen video yayınlanmaz; düzeltilemezse Cem'e bildirilir.
- Commit: hikâye klasörü (voice/script.txt, words.json, voice.ogg, audio/cues.json, muzik.*, altyazi.ass, anatomi/) ve
  video (`videos/<ad>-dikey.mp4`).
- Buffer API ile YouTube Short, TikTok ve Instagram Reel olarak 16:00'ya planlanır (günlük Short'ların 12:00 ve 19:00
  dilimleri dışında; 16:00'ya 30 dakikadan az kaldıysa ya da geçtiyse ertesi gün 16:00). Planlananlar API'den geri okunur.
- Planlamadan SONRA kayıt `log.json`'a `{date, slug, konu, baslik, kaynaklar, "tur": "ic-nasil"}` olarak eklenir; X'e
  günlük X görevi log.json'dan kendisi atar. Video bilgi için Cem'e gönderilir; beğenmezse Buffer'dan silebilir.
- `anatomi/bekleyen.json`: yarım kalan (render ya da kota yüzünden bitmeyen) iş `{date, slug, durum, not}` olarak
  buraya yazılır; sonraki çalışma önce onu tamamlar.
