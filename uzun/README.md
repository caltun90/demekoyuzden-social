# Uzun video kiti (Demek O Yüzden, 7-10 dk yatay)

Depoda `uzun/` klasöründe durur. İlk video: "Beyninin Sana Oynadığı 6 Oyun" (7:11, Kasım 2026).

## Yayın takvimi
- Pazartesi, Perşembe, Cumartesi 16:00 (Europe/Istanbul), YouTube'a yatay normal video.
- Yükleme deponun kökündeki `yt_upload.py` ile YouTube Data API üzerinden yapılır (KIT.md "Paylaşım"). Buffer uzun video yüklemez, bu işte Buffer kullanılmaz.
- Metinde "haftaya", "her hafta", "yarın" geçmez. Kapanış hep "Bir sonraki videoda görüşmek üzere!".
- Mini test / soru bölümü YOK (Cem: gereksiz).

## Konu seçimi (Cem, 14 Kasım 2026)
Uzun videolar sırayla iki türden olur (log.json'daki son "tur": "uzun" kaydının "kaynak_tur" alanına bak, öbürünü seç):
- "derinlik": Son uzun videodan bu yana yayınlanmış Shorts konularından (log.json, bugünden önceki tarihler; bugünün 19:00 Short'unu verme) ortak bir temaya oturan 5-6 tanesi. Short'un metni ya da görüntüsü kullanılmaz: her konu yeni örnek, yeni deney, yeni "neden" ile daha derin anlatılır. Açıklamada "Kısa hallerini Shorts'ta izleyebilirsin" denir.
- "yeni": Psikoloji ya da günlük bilim üzerine, log.json'da hiç geçmeyen bir tema ve 5-6 alt konu.
Kayda "kaynak_tur": "derinlik" ya da "yeni" yazılır. İlk video ("6 oyun", 14 Kasım) "derinlik" sayılır.

## İçerik formatı
- 7-10 dk. Bir tema altında 5-6 kısa bölüm (ör. "bir günde beynin oynadığı 6 oyun", "mutfaktaki 5 bilim sırrı", "dilimizdeki 6 kelimenin hikâyesi").
- Format dönüşümlü olsun: "bir günün hikâyesi", "efsane mi gerçek mi", "karşılaştırma", "tarihte tek bir gün", "sayılarla".
- Her bölümde: kısa sahne/hikâye, adı (isim kartı), deney/kanıt ve kaynak ekranda (yazar, yıl, kurum), neden olur, "BU NEDEN ÖNEMLİ?" kartı.
- Bilgiler en az iki güvenilir kaynaktan doğrulanır. Tıbbi tavsiye yok. Gerçek kişi ve telifli karakter çizilmez.
- Günlük Shorts konularını kelimesi kelimesine tekrar etme; uzun video daha derin ve yeni bilgiler içersin.

## Dosyalar
- `senaryo.py`: TITLE, SEQ (('scene', n), ('line', id, metin, vurgu), ('beat', ad, sn)), PRON (yabancı isimlerin TTS yazımı), GROUPS (TTS istekleri, grup başına ~15-22 satır), mix_plan (efekt/fon), FIX (TTS'siz ses düzeltmeleri). Örnek olarak ilk videonunki duruyor; yeni videoda baştan yazılır.
- `ses.py`: `tts g1 g2 ...` ham ses, `build` -> voice/voice.wav, mix.wav, final.json.
- `realign.py`: ham sesi sessizliklerde keser, parçaları yazıya döker, satırlara eşler -> voice/cuts.json. Deponun kökündeki `sync.py`yi kullanır.
- `uzun.py`: 1920x1080 çizim. Hazır paneller: `p_clock` (saat/bölüm açılışı), `p_name` (isim kartı), `p_study` (kaynak kartı + sağda çizim), `p_matter` (BU NEDEN ÖNEMLİ?), `p_card` (büyük başlık), `bars` (oran çubukları), `stamp`, `icon_row`. Yeni videoda CH, NAMED, ICON/icon(), sahne çizim fonksiyonları ve PLAN yeniden yazılır.
- `kapak.py`: 1280x720 kapak.
- `fix.py`: sesli harf uzatma (TD-PSOLA). Okunuş hatasında önce PRON ile yeniden seslendirmeyi dene.
- `render.py`: çizim yardımcıları (deponun kökündekinin kopyası, voice/final.json'u kendi klasöründen okur).

## Akış (her uzun video)
1. log.json'da bugünün tarihli `"tur": "uzun"` kaydı varsa dur (aynı gün ikinci uzun video yok).
2. Tema ve 5-6 alt konu seç, kaynakları doğrula, `senaryo.py` yaz (1050-1350 kelime, 7-10 dk).
3. `GEMINI_API_KEY=... python3 ses.py tts g1 g2 g3 g4` (model: gemini-3.1-flash-tts-preview; kota bitti ise `TTS_MODEL=gemini-3.8-flash-tts`, bu model stil talimatını okuduğu için ses.py ona sadece düz metin gönderir).
4. `GEMINI_API_KEY=... python3 realign.py`, sonra `python3 ses.py build`. final.json satırlarına 'i' ve 'scene' ekle, `cp voice/voice.wav voice/final.wav`.
5. Kesim kontrolü: hiçbir satırın başında önceki satırın son hecesi kalmasın (gerekirse cuts.json'da sınırı sessizliğe kaydır).
6. `uzun.py` sahnelerini yaz. `python3 uzun.py still chk <sn> ...` ile her bölümden en kalabalık kareleri aç ve bak: taşma, üst üste binme, altyazı.
7. `python3 uzun.py part 0 <orta> p1 & python3 uzun.py part <orta> 9999 p2`, sonra `python3 uzun.py join cikti.mp4 p1 p2`.
8. `python3 kapak.py` (başlık ve simgeleri konuya göre değiştir).
9. Video ve kapağı depoya koy: `videos/<tarih>-uzun-<slug>.mp4`, `-kapak.jpg`. log.json'a {date, slug, tur: "uzun", baslik, kaynaklar} ekle.
10. Deponun kökünden yükle (başlık en fazla 90 karakter, açıklamada bölüm dakikaları ve kaynaklar, `#shorts` YOK):
    `YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... python3 yt_upload.py videos/<ad>.mp4 --title "..." --desc "..." --tags "demekoyuzden,..." --publish-at <bugün>T16:00:00+03:00 --thumb videos/<ad>-kapak.jpg`
    Saat 15:50'yi geçtiyse `--publish-at` yerine `--privacy public`. Çıktıdaki `id`yi log.json kaydına `yatay_youtube` olarak yaz.
    Özel kapak 403 verirse kanal henüz telefonla doğrulanmamıştır; video yine yüklenmiştir.

## TTS kotası
gemini-3.1-flash-tts-preview günde 10 istek, ~11:00 İstanbul'da sıfırlanır. Günlük Short + uzun video aynı gün aynı kotayı kullanır; uzun video için gruplar 4-5 isteği geçmesin.
