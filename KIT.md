# Niş video üretim kiti ("Demek O Yüzden" kanalı)

Günlük 1 dakikalık videoları üretmek için araçlar. Kit bu deponun kökünde durur; videolar `videos/`, yapılanlar `log.json`.
Seriler üstteki etiketle ayrılır ("1 DAKİKADA PSİKOLOJİ", "1 DAKİKADA BİLİM"). Başka seri yok.

## Kararlar (Cem)
- GÜNDE 3 VİDEO (Cem, 2026-11-13). Günlük görev tek çalışmada üç video üretir: "Sırada" listesinin ilk üç konusu, listedeki sırayla.
  Birinci video 12:00'de, ikinci 15:00'te, üçüncü 19:00'da (Europe/Istanbul) üç platforma planlanır. Bu kural görev talimatındaki
  "bugünün videosu", "19:00" ve "aynı gün ikinci kez planlama" maddelerinin yerine geçer:
  - Önce Buffer'da bugünün gönderilerine bak. Bir saat dilimi (12:00, 15:00 ya da 19:00) üç kanalda da doluysa o dilime ekleme; yalnızca boş dilimleri doldur.
  - Planlanacak saate 30 dakikadan az kaldıysa ya da saat geçtiyse o video için şimdi + 30 dk kullan.
  - Akışın tamamı (senaryo, ses, hizalama, sahneler, kare kontrolü, build, push, Buffer) her video için baştan uygulanır. Bir videoyu bitirip planlamadan sonrakine başlama.
    `script.py` ve `render.py` depoda son üretilen videonun halini taşır; her video ayrı commit olur.
  - Bir video başarısız olursa diğerleri yine yayınlanır; hangisinin neden olmadığını Cem'e bildir. İş yarıda kalmasın.
  - Buffer ücretsiz planda en fazla 10 planlı gönderi tutar (3 video x 3 kanal = 9). Sınır hatası gelirse planlanamayan gönderiyi Cem'e bildir.
  - Rapor tek mesajdır: üç konu, üç YouTube başlığı, üç saat, üç yatay video bağlantısı. Altı dosya ve üç yatay kapak karesi Cem'e gönderilir.
- Gemini ücretsiz kotada (Cem ücretli plana geçmek istemiyor): ses modeli günde 10 istek, `gemini-3-flash-preview` günde 20 istek.
  `sync.py` kota dolarsa (429) kendiliğinden `gemini-3.1-flash-lite` ile devam eder (günde 500); bir şey yapman gerekmez. Gereksiz `list`/`check` tekrarından kaçın.
  Ses kotası dolarsa o gün kalan videolar üretilemez; Cem'e bildir.
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
- İLK 2 SANİYE KANCASI (Cem, 2026-11-19; istisnasız her video: dikey, yatay, uzun video ve "That's Why" İngilizce sürümleri).
  İlk 2 saniye izleyiciyi ekrana kilitler. Logo, kanal adı, jenerik, selamlama ("Merhaba", "Bugün size ... anlatacağım"),
  boş, siyah ya da hareketsiz kareyle açılmaz.
  - 0:00 kapak karesi (`COVER`) doludur; ses en geç 0,5. saniyede başlar.
  - `script.py`'nin ilk satırı kanca cümlesidir: en fazla 8 kelime, 2. saniye dolmadan biter. Konunun en şaşırtıcı ya da
    izleyicinin kendini tanıdığı yanını cevabı vermeden ortaya koyar (beklenmedik iddia, "neden" sorusu, yarıda kesilen an).
    Cevap videonun ilerisinde gelir; kancanın verdiği söz mutlaka karşılanır. Yanıltıcı tıklama tuzağı ve uydurma bilgi yok.
  - İlk karede en fazla 5 kelimelik dev kanca yazısı ve sahne 1'in en çarpıcı anı; ilk 2 saniyede belirgin hareket
    (hızlı yakınlaşma, giriş animasyonu ya da ani kesme). Kanca yazısı altyazıyla üst üste binmez.
  - Bu kural bu dosyadaki ve `uzun/README.md`'deki diğer açılış kurallarından önce gelir; çelişirse buna uy.
- Ses: Gemini TTS, ses = Achird. Model: gemini-3.1-flash-tts-preview.
  gemini-3.8-flash-tts KULLANMA: stil talimatını da sesli okuyor.
- Cem'e yazılan her şey Türkçe, kısa, sade. Em dash yok.

## Dosyalar
- `script.py`: senaryo satırları (sahne no, altyazı metni, gerekirse TTS için ayrı yazım).
- `voice_google.py`: Gemini TTS. Tüm senaryoyu tek istekte okutur, `voice/raw_google.wav` yazar, satırlara böler.
- `sync.py`: parça dökümü (`list`), satır eşleme ve duraklama kısaltma (`build`), altyazı kontrolü (`check`). Kota dolarsa yedek modele geçer.
- `render.py`: çizim motoru + 6 sahne. `FMT=v` (dikey) veya `FMT=h` (yatay). Yeni videoda `scene1..6`, `HL`, `TITLE`, `HOOK`, `COVER`, `COVER_AT`,
  gerekirse `tag()` içindeki seri etiketi yeniden yazılır. Yardımcı fonksiyonlara dokunma.
- `build.sh`: iki formatı üretir, birleştirir, sesi ekler. Depo şişmesin diye kodlama `CRF=24`, `PRESET=medium` (render.py; gözle fark yok). Bir sahne render edilemezse durur, video üretmez.
- `yt_upload.py`: yatay videoyu YouTube'a normal video olarak yükler (bkz. Paylaşım). Yalnızca standart kütüphane kullanır.
- `feed.py`, `feed.xml`: eski Zapier/RSS denemesi. KULLANILMIYOR; `feed.py add` çalıştırma (aynı video iki kez yüklenmesin).
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
   İlk 2 saniye kontrolü: iki formatta `0 0.5 1.0 1.9` karelerini ayrıca aç. İlk kare boşsa, kanca yazısı okunmuyorsa,
   ilk 2 saniyede hareket yoksa ya da kanca cümlesi 2 saniyeyi aşıyorsa (`voice/final.json` ilk satırın `end` değeri 2,0'dan büyükse) düzelt; düzelmiyorsa yayınlama, Cem'e bildir.
7. `./build.sh <YYYY-MM-DD>-<slug>`; süre, ses ve 3 kare son kontrol.
8. `voice/`, `scenes_*`, `silent_*`, `list_*`, kare klasörleri ve kökteki mp4'ler depoya eklenmez.

## Paylaşım
- Dikey video: Buffer (bahsish.co hesabı, yalnızca API anahtarıyla) üzerinden YouTube Short ("Demek O Yüzden"), TikTok, Instagram Reel. Günde üç video: 12:00, 15:00 ve 19:00.
- Yatay video: YouTube'a normal video olarak OTOMATİK yüklenir, doğrudan YouTube API ile (Cem, 2026-11-14). Buffer yatay videoyu
  YouTube'a kabul etmez ("Video must be vertical"). Google projesi `dov-uploader` (Cem'in hesabı), uygulama "DOV Uploader", bağlı kanal
  "Demek O Yüzden". Görev her yatay video için, dikey video Buffer'a planlandıktan sonra:
  ```
  YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... python3 yt_upload.py videos/<ad>-yatay.mp4 \
      --title "<YouTube başlığı>" --desc "<açıklama>" --tags "demekoyuzden,<2-4 konu etiketi>" \
      --publish-at <YYYY-MM-DD>T<SS:DD>:00+03:00 --thumb <yatay kapak karesi>
  ```
  - Üç değer görev talimatındaki `YT_CLIENT_ID:`, `YT_CLIENT_SECRET:`, `YT_REFRESH_TOKEN:` satırlarından okunur ve yalnızca komutta
    ortam değişkeni olarak kullanılır. Dosyaya, depoya (herkese açık), belleğe ya da mesaja YAZILMAZ.
    Satırlardan biri yoksa ya da "BURAYA" yazıyorsa yatay yüklemeyi atla, diğer işleri bitir ve Cem'e tek cümleyle bildir.
  - Başlık Short ile aynı. Açıklama aynı metin ama `#shorts` etiketi OLMADAN.
  - `--publish-at`: o videonun Short'u ile aynı saat (12:00, 15:00 ya da 19:00; Buffer için kaydırdıysan aynı kaydırılmış saat).
    Video önce gizli yüklenir, YouTube o saatte kendisi yayına alır. Saat geçmişse `--publish-at` yerine `--privacy public` kullan.
  - `--thumb`: yatay kapak karesi (`FMT=h python3 render.py still <klasör> 0` çıktısı). Betik "thumb": "hata 403" dönerse kanal
    henüz telefonla doğrulanmamış demektir; video yine yüklenmiştir, rapora "kapak eklenemedi, kanal doğrulanınca düzelir" yaz.
  - Çıktı tek satır JSON: `id`, `url`, `privacy`, `publishAt`. `id` değerini log.json'daki o videonun kaydına `yatay_youtube` olarak yaz.
    log.json'da `yatay_youtube` olan videoyu bir daha yükleme. Betik hata verirse bir kez daha dene; yine olmazsa Cem'e hata metnini bildir.
  - Bu kural görev talimatındaki "Cem YouTube'a normal video olarak yükler" ve "Videoyu depo dışında hiçbir yere yükleme" maddelerinin
    yerine geçer (yalnızca yatay videonun YouTube'a yüklenmesi için). Yatay videoyu Buffer'a verme.
  - Ağ: `oauth2.googleapis.com` ve `www.googleapis.com` izinli siteler listesinde olmalı. Günlük sınır 100 yükleme.
  - Raporda her yatay video için YouTube bağlantısını ve yayın saatini yaz.
- Claude'a bağlı Buffer bağlayıcısı engrowapp hesabına aittir (Engrow, Pofu Kids); bu kanal için kullanılmaz.
- Buffer dosya yüklemesi kabul etmez; video açık bir https adresinde durmalı (bu deponun raw adresi).
- Kapak: Instagram ve TikTok gönderisinde video varlığına `metadata: { thumbnailOffset: 200 }` ver (ilk kare = kapak).
  YouTube Short kapağı Buffer/API ile seçilemez; YouTube kendi seçer, Cem isterse YouTube uygulamasından ilk kareyi seçer.
- Yatay kapak karesi `yt_upload.py --thumb` ile YouTube'a yüklenir; Cem'e ayrıca gönderilir (`FMT=h python3 render.py still <klasör> 0`).

## Buffer API (doğrulandı: 2026-11-13)
Yalnızca API anahtarıyla; Claude'a bağlı Buffer bağlayıcısı (mcp araçları) bu kanal için KULLANILMAZ.
- İstek: `POST https://api.buffer.com`, başlıklar `Authorization: Bearer $BUFFER_API_KEY` ve `Content-Type: application/json`, gövde `{"query": "..."}` (GraphQL).
- Organizasyon: `{ account { organizations { id } } }`
- Kanallar: `{ channels(input:{organizationId:"<org>"}) { id name service isDisconnected } }`. `service` değeri `youtube`, `tiktok`, `instagram`.
  Kimlikleri her çalışmada buradan oku. Üçünden biri yoksa o kanalı atla ve Cem'e bildir. Başka kanala gönderi atma.
- Bugünün gönderileri (dolu saat dilimlerini görmek için):
  `{ posts(first:50, input:{organizationId:"<org>", filter:{dueAt:{start:"<gün>T00:00:00+03:00", end:"<gün>T23:59:59+03:00"}}}) { edges { node { id status dueAt channelService } } } }`
- Planlama, her kanal için bir kez:
  ```
  mutation { createPost(input:{ text:"<açıklama>", channelId:"<kanal>", schedulingType: automatic, mode: customScheduled,
      dueAt:"<gün>T12:00:00+03:00", assets:[{ video:{ url:"<dikey videonun raw adresi>" <VİDEO_META> } }] <GÖNDERİ_META> }) {
    __typename ... on PostActionSuccess { post { id status dueAt channelService } } ... on MutationError { message } } }
  ```
  - YouTube: `<GÖNDERİ_META>` = `, metadata:{ youtube:{ title:"<başlık>", categoryId:"27", privacy: public, madeForKids: false } }`; `<VİDEO_META>` boş.
  - Instagram: `<GÖNDERİ_META>` = `, metadata:{ instagram:{ type: reel, shouldShareToFeed: true } }`; `<VİDEO_META>` = `, metadata:{ thumbnailOffset: 200 }`.
  - TikTok: `<GÖNDERİ_META>` boş; `<VİDEO_META>` = `, metadata:{ thumbnailOffset: 200 }`.
- Video adresi: `https://raw.githubusercontent.com/caltun90/demekoyuzden-social/main/videos/<dosya>`. Push'tan sonra 200 döndüğünü doğrula.
  Buffer adresi reddederse bir kez `https://cdn.jsdelivr.net/gh/caltun90/demekoyuzden-social@main/videos/<dosya>` ile dene.
- YouTube başlığı: en fazla 90 karakter, merak uyandıran soru.
- Açıklama: 2-3 cümlelik kanca + "Sen de yaşıyor musun? Yorumlara yaz." tarzı soru + en fazla 8 etiket (`#demekoyuzden` ve `#shorts` hep dahil).
- Doğrulama: planladıktan sonra `filter:{status:[scheduled]}` ile geri oku; üç kanal da doğru saatte `scheduled` olmalı.
- Beklenmedik bir alan hatası gelirse şema değişmiştir: `{ __type(name:"CreatePostInput") { inputFields { name } } }` ile bak,
  gerekirse https://developers.buffer.com/llms.txt içindeki örnekleri oku.

## İngilizce sürüm ("That's Why" kanalı)
Türkçe videoların işi bittikten sonra aynı çalışmada yapılır (Cem, 2026-11-17). Ayrıntı görev talimatındadır; özet:
- Anahtar: görev talimatındaki `BUFFER_EN_API_KEY` (thatswhyen hesabı). Satır boşsa bölüm atlanır. Bu anahtarla yalnızca üç kanal:
  YouTube "That's Why", X "ThatsWhyEN", TikTok "thatswhyen". Kimlikler her çalışmada API'den okunur. Türkçe anahtarla bu kanallara,
  bu anahtarla başka kanala gönderi atılmaz.
- Kayıt: `en-log.json`, her kayıt `{date, slug, kaynak_date, title_en, yt_post, x_post, tiktok_post}`.
- Sıra: önce bugünün Türkçe videoları, sonra en-log.json'da olmayan eski Shorts (log.json'da eskiden yeniye; `"tur": "uzun"` hariç). Günde en fazla 5.
- Kaynak: eski videonun `script.py` ve `render.py` dosyası git geçmişinden alınır
  (`git log --format=%H -- videos/<tarih>-<slug>-dikey.mp4`, sonra `git show <commit>:script.py`). Bugünün videoları için o videonun commit'i.
  - `gokyuzu-neden-mavi` videosunun kaynağı depoda yok (yalnızca mp4 yüklenmiş); İngilizcesi üretilemez, atlanır.
  - `zeigarnik-etkisi` ve `sahne-isigi-etkisi` eski motorla yazılmış: sahneler güncel `render.py` motoruna taşınır, `HOOK`/`COVER` eklenir,
    sahne 6 kapanış kalıbına uydurulur.
- Çeviri: doğal İngilizce, 45-62 sn. Ekrandaki bütün yazılar çevrilir (`TITLE`, `HOOK`, `COVER`, `HL`, sahne içi yazılar, `cap_start` kelimeleri,
  seri etiketi "PSYCHOLOGY IN 1 MINUTE" / "SCIENCE IN 1 MINUTE"). Kapanış "So that's why!" ve "See you in the next video!";
  sahne 6'daki büyük yazı "See you in the / next video!". Ekranda hiç Türkçe kalmamalı; kare kontrolünde buna bak.
- Ses: Achird, İngilizce stil talimatıyla (`voice_google.synth(..., style=...)`). Model önce `gemini-2.5-flash-preview-tts`;
  429 verirse `gemini-3.1-flash-tts-preview`; ikisi de doluysa kalan videolar ertesi güne kalır.
  `sync.py` dökümü Türkçe sorar; İngilizce ses için istemdeki "Turkce" kelimesi "Ingilizce" yapılarak çalıştırılır.
- Akışın 3-7. adımları aynen uygulanır. Üretim depo dışında ayrı bir çalışma klasöründe yapılır; kökteki `script.py` ve `render.py`
  son Türkçe videonun hali olarak kalır. Ad `<bugün>-<slug>-en`; dosyalar `videos/en/` altına (`-dikey.mp4`, `-yatay.mp4`).
- Planlama (yukarıdaki "Buffer API" şeması, `BUFFER_EN_API_KEY` ile): saat dilimleri 14:00, 17:00, 20:00, 23:00 ve ertesi gün 02:00
  (Europe/Istanbul). Şimdiden en az 30 dk sonraki ilk boş dilimden sırayla doldur; bütün kanallarda dolu dilimi atla.
  Kanal başına en fazla 10 planlı gönderi; sınıra gelince dur.
  - YouTube Short: başlık İngilizce soru (en fazla 90 karakter), `categoryId:"27"`, `privacy: public`, `madeForKids: false`.
    Açıklama: 2-3 cümlelik kanca + "Does this happen to you too? Tell us in the comments." tarzı soru + en fazla 8 etiket (`#thatswhy`, `#shorts` dahil).
  - X (`service: twitter`): aynı dikey video, metadata yok. Metin: başlık, boş satır, kısa kanca, en fazla 3 etiket (`#thatswhy` dahil); 280 karakteri geçmez, bağlantı yok.
  - TikTok: videoya `metadata:{ thumbnailOffset: 200 }`; açıklama YouTube ile aynı ama `#shorts` olmadan.
  - Planladıktan sonra üç kanalda da `scheduled` olduğunu geri oku, sonra en-log.json'a yaz, commit ve push.
  - en-log.json'da `tiktok_post` alanı olmayan eski kayıtların videosu da boş bir dilime TikTok için planlanır (günlük 5 sınırına sayılmaz).
- Yatay İngilizce video şimdilik hiçbir yere yüklenmez; yalnızca depoda durur.
- Rapor: Türkçe raporun sonuna tek satır: kaç İngilizce video hangi saatlere planlandı, kaç eski video çevrilmeyi bekliyor.

## Konu havuzu
Yapıldı: Kapı eşiği etkisi (pilot, psikoloji); Zeigarnik etkisi (psikoloji); Gökyüzü neden mavi, gün batımı neden kırmızı? (bilim); Sahne ışığı etkisi (psikoloji); Esnemek neden bulaşıcı? (bilim); Dilimin ucunda hissi (psikoloji); Klavyede harfler neden alfabetik sırada değil? (tarih); Bir kelimeyi çok tekrarlayınca neden anlamsızlaşır? (psikoloji); Arabada telefona bakınca neden midemiz bulanır? (bilim); Söyleyeceğin şey araya başka konu girince neden aklından uçar? (psikoloji); Kan neden tutar? Kan görünce neden başımız döner? (bilim); Gözümüz neden dalar? (psikoloji); Meyveyi yıkayınca pestisit gider mi? (bilim, Cem istedi); Şarkı neden dile dolanır? (psikoloji); Kendimizi neden gıdıklayamayız? (bilim); Yeni öğrendiğin şeyi neden her yerde görmeye başlarsın? (psikoloji); Kendi sesimiz kayıtta neden yabancı gelir? (bilim); Burç yorumları neden hep tutar gibi gelir? Barnum etkisi (psikoloji); Bir canlı ölünce hücreleri de hemen ölür mü? Ksenobotlar ve antrobotlar (bilim, Cem istedi); Soğan doğrarken neden ağlarız? (bilim); Bulutlarda neden yüz görürüz? Pareidolia (psikoloji); Parmaklarımız suda neden buruşur? (bilim); Kendi yaptığımız şeyi neden daha çok severiz? IKEA etkisi (psikoloji); Uykuya dalarken neden düşer gibi sıçrarız? Hipnik sıçrama (bilim).
Sırada (bu sırayla, bir psikoloji bir bilim):
1. Nane neden serinletir, acı biber neden yakar? (bilim)
2. Dönüş yolu neden gidişten kısa gelir? Dönüş yolu etkisi (psikoloji)
3. Hıçkırık neden tutar? (bilim)
4. Kalabalıkta adını duyunca neden hemen dönersin? Kokteyl partisi etkisi (psikoloji)
5. Soğuk içecek neden başımızı ağrıtır? Beyin donması (bilim)
6. Aynı şarkıyı dinledikçe neden daha çok severiz? Salt maruz kalma etkisi (psikoloji)
7. Güneşe bakınca neden hapşırırız? (bilim)
Liste hiç bitmesin: "Sırada" 4 konunun altına inince aynı dengeyle (bir psikoloji, bir bilim) en az 6 yeni konu ekle. Tarih ve dil konusu ekleme.
Konu seçme ölçütü (Cem onayladı, 2026-11-13; kalıcı):
- Herkesin kendi yaşadığı, gündelik bir şey olsun (esnemek, gıdıklanmak, dile dolanan şarkı gibi). Başlık kısa bir "neden" sorusu olsun.
- Cevabı tek cümleyle anlatılabilsin ve izleyene "demek o yüzden!" dedirtsin. Etki adları (Barnum, IKEA) başlıkta değil, cevabın içinde geçsin.
- Sağlam kaynağı olsun; tartışmalı ya da tekrarlanamamış bulgu, tıbbi tavsiye ve "Yapıldı" listesindekilerin benzeri olmasın.
