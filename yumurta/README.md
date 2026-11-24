# Yumurta stili video kiti

3B bir dünyada 2B yumurta kafalı, komik karakterlerle dikey Short ya da yatay uzun video. Motor
[kodlaciz/yumurta-stili](https://github.com/kodlaciz/yumurta-stili) (MIT, `LICENSE`); bulutta çalışan ses aracı,
16:9 desteği ve GitHub Actions'ta paralel render bize ait. Kanala özel kurallar (konu, kanca, kaynak, paylaşım) kanalın
kendi `KIT.md` dosyasındadır; bu dosya yalnızca nasıl ÜRETİLECEĞİNİ anlatır. Cem'e yazılan her şey Türkçe, kısa ve
sade; uzun tire (em dash) asla kullanılmaz.

Örnek hikâyeler (her biri çalışan, kontrol edilmiş bir `story.js`; yeni hikâyede set ve karakter kodunu buradan kopyala):

| Klasör | Ne | Setler (kopyalanabilir `build...` fonksiyonları) |
|---|---|---|
| `stories/dus-fikri` | Demek O Yüzden, 27 sn | gece ofisi (masa, lamba, duvar saati, kapıda patron, yan masa), duş/banyo (çini, perde, su, buhar, fikir ampulü) |
| `stories/dilsizler` | Lala Anlatıyor, 29 sn | saray taht odası (çini, kafesli pencereden güneş, kandiller), mutfak + yer sofrası |
| `stories/ayna` | dizivanastudio, 36 sn | apartman lobisi (asansör, kat göstergesi, ayna), gün batımı sokağı (evler, ağaçlar, lambalar) |

Motorun orijinal örneği ve ayrıntılı stil kuralları: `SKILL_KAYNAK.md` (İngilizce, tamamını oku) ve `STIL_KITABI.md`.

## 1. Akış (bir video)

1. **Konu ve bilgi:** kanalın `KIT.md` kurallarına göre. Bilgiler iki kaynakla doğrulanır; `stories/<ad>/SCRIPT.md` dosyasına iddia/kaynak tablosu yazılır.
2. **Senaryo:** `stories/<ad>/voice/script.txt`, her satır tek cümle. Yapı: paradoks kanca (en fazla 8 kelime, 2 sn dolmadan biter) → "Bakın," dönüşü + kurulum → gülen ya da itiraz eden biri (tırnak içinde tek replik) → 2-3 adımda tırmanma → gündelik benzetmeyle mekanizma ("Tıpkı ...") → tek satırlık son vuruş. Türkçe hız hedefi 2,4-2,9 kelime/sn. Rakamları okunuşuyla `voice/say.txt` dosyasına yaz (aynı satır sayısı) ya da metinde yazıyla yaz.
3. **Ses** (`GEMINI_API_KEY` ortam değişkeni):
   ```bash
   python3 tools/ses.py tts   stories/<ad> <ses_adı>          # satırları üretir; 429 dakika sınırında kendisi bekler
   python3 tools/ses.py check stories/<ad>                    # her satırı yazıya döker; SORUNLU satırın wav'ını sil, tts'i tekrarla
   python3 tools/ses.py build stories/<ad> --tempo 1.25 --kanca 1.1   # voice.wav, words.json, env.json
   ```
   `build` çıktısında hız 2,4-2,9 ve "kanca biter" 2,0 sn'nin altında olmalı; değilse `--tempo` ve `--kanca` ile ayarla.
   Model: `gemini-3.1-flash-tts-preview` (varsayılan, stil talimatını okumaz). `gemini-3.8-flash-tts` stil talimatını SESLİ okur; onunla `--stil ""` ver.
   TTS bazen kelime tekrar eder ya da ekler: `check` bunun için var, atlamadan çalıştır.
4. **Sahneler:** `stories/<ad>/story.js`. Bir örnek hikâyeyi kopyalayıp sahneleri bu hikâyeye göre yeniden kur. Her görsel olay bir kelimeye bağlıdır (`W('kelime', n)`), saniye elle yazılmaz. Aynı kelime birden çok geçiyorsa `n` ver (`W('padişah', 2)`); `W()` noktalama ve büyük harfi yok sayar.
   - Yatay uzun video: `export const ASPECT = '16:9';` (1920x1080). Dikey varsayılan.
5. **Kare kontrolü** (yarım çözünürlük, hızlı):
   ```bash
   cd engine && npm ci --ignore-scripts && node render.mjs <ad> --stills=0,0.5,1,1.9,<her plandan bir saniye> --scale=0.5
   ```
   `stories/<ad>/out/stills.jpg` dosyasını Read ile aç ve 2. bölümdeki listeyle kontrol et. Düzelt, tekrar bak.
6. **Ses miksi:** `cd engine && node render.mjs <ad> --cues && python3 audio/mix.py ../stories/<ad>` → `audio/mix.wav`.
7. **Render (GitHub Actions, paralel):** hikâye klasörünü commit edip main'e push et (`out/` ve `voice/lines/` git'e girmez), sonra:
   ```bash
   gh api -X POST repos/<owner>/<repo>/actions/workflows/yumurta-render.yml/dispatches -f ref=main -f 'inputs[story]=<ad>' -f 'inputs[parts]=<N>'
   gh api "repos/<owner>/<repo>/actions/runs?per_page=5" --jq '.workflow_runs[] | [.id,.status,.conclusion,.display_title] | @tsv'
   # bittiğinde video "dal" girdisindeki dalda durur (varsayılan render/short; uzun video için -f 'inputs[dal]=render/uzun').
   # Artifact indirme bulut oturumunda engelli, videoyu git ile al:
   git fetch -q --depth 1 origin render/short && git show FETCH_HEAD:<ad>.mp4 > /tmp/<ad>.mp4
   # 100 MB üstü video parça parça gelir: git ls-tree --name-only FETCH_HEAD ; her <ad>.mp4.partNN dosyasını sırayla git show ile al, cat ile birleştir.
   # Dal her render'da üzerine yazılır: aynı dalı kullanan iki render'ı aynı anda başlatma; aldığın dosyanın adının hikâyenin adı olduğunu kontrol et.
   ```
   (`gh workflow run` çalışmaz, GraphQL kapalı; yukarıdaki REST çağrılarını kullan.) Parça sayısı: Short 8, 3-5 dk video 16, 7-10 dk video 20. Parçalar render maliyetine göre eşit bölünür; ölçülen süre: 27-36 sn'lik Short 6-8 dakikada biter. 1-2 dakikada bir durumu kontrol et. Bir parça başarısız olursa (çoğunlukla Chrome geç açılır) önce yalnızca başarısızları yeniden çalıştır: `gh api -X POST repos/<owner>/<repo>/actions/runs/<run_id>/rerun-failed-jobs`. Yine olmazsa `gh api repos/<owner>/<repo>/actions/jobs/<job_id>/logs` ile hatayı oku, düzelt, yeniden tetikle.
8. **Son kontrol:** bitmiş dosyadan 0,0 / 0,5 / 1,0 / 1,9 sn ve her plandan bir kare (ffmpeg ile) çıkar, Read ile aç; süre ve ses (`ebur128`, yaklaşık -14 LUFS) kontrol et. Sonra kanalın `KIT.md` paylaşım adımları.

## 2. Görünüm kuralları (kontrol listesi)

- **Karakterler komik ve abartılı** (Cem'in beğendiği örnek: `dus-fikri` içindeki patron). Büyük kafa (`headW` 260-280), bıyık/sakal, düğmeli ceket, sarık/külah/şapka gibi ayırt edici bir şey. İfadeler sözle birlikte değişir: kahkaha (`laugh` + `laughMarks` + `bob`), sinsi yarı kapalı göz (`smug` + `lid`), ter damlası (`sweat`), şaşkın (`surprised`), kızgın kaş (`angry`, `brow: -.5`). Bir sahne boyunca tek ifadede kalma. Hareket etmeyen karakter kıpırdamaz ama göz kırpar (`blinkAt`), konuşan karakterin ağzı `flap(env, t)` ile oynar.
- **Kanca yazısı:** kanalın kuralı istiyorsa ilk 2 sn dev yazı `lib/kanca.js` ile: `import { kancaYazisi } from '/lib/kanca.js'; export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'EN FAZLA BEŞ KELİME?'); }`
- **Kanca:** 0:00'daki ilk kare dolu, karakter hikâyenin ana nesnesiyle bir şey yapıyor; ilk 2 sn'de belirgin hareket (hızlı geçiş ya da itme); ilk cümle 2-3 farklı görüntüye bölünür.
- **Kadraj:** yüzler ekran yüksekliğinin %35-60'ında, altyazı %70'te (yatayda %86); altyazı yüzün üstüne binmez. Karakter ve şapka kadraj kenarında kesilmez. Kart önce ölçülür: kafanın üstündeki ampul, düşünce balonu gibi kartlar kafa MERKEZİNE göre yerleştirilir (kafa üstü yaklaşık boy - 0,45 m), kamera yönüne göre sağ/sol (bkz. `dus-fikri` içindeki `at2`).
- **Işık:** her sette görünen bir ışık kaynağı (lamba, pencere, güneş); sıcak anahtar ışık + soğuk dolgu; gölgeler mavimsi/mor, kahverengi değil. Duvarlar soğuk renk (açık mavi-gri taş), sıcak ışık havuz yapar; her şey sarı-turuncu olursa duvar rengini soğut ve lamba gücünü düşür.
- **Büyük duvarda desen:** çini kuşak, boyalı bant, ahşap lambri; duvarın 5 cm önünde, aynı düzlemde değil (titreme yapar).
- **Kamera hiç durmaz:** her plan yavaş iter (`creep`) ve yana kayar (`drift`); setler arası `whip`; en fazla 1-2 sert kesme (`cut`). Bulanıklık: `look.blur = cp.moving > .15 ? 12 : 0` (bir yürüme/takip planında kapat).
- **Hikâyeye hizmet etmeyen yazı yok;** ekranda yazı gerekiyorsa (kaynak, sayı) kısa ve okunaklı.
- Telifli karakter, gerçek kişi karikatürü, marka logosu yok. Şiddet, kan yok.

## 3. Bilinen tuzaklar

- `POS` tablosunda olmayan bir karakter adıyla `place()` çağrısı sahneyi çökertir ("undefined is not iterable").
- `kandil()` ve sahne ışıkları çok güçlü olursa her şey sarıya boğulur; tavan düz açık renkse lamba tavanda parlak leke yapar.
- `drawCaption` Segoe/Arial Black ister, yoksa sistemin kalın yazısına düşer; sorun değil.
- Lokal render arka planda bırakılırsa oturum biterken kesilebilir; tam render her zaman Actions'ta yapılır, lokalde yalnızca `--stills`.
- Kokoro (İngilizce) ile: `voice/EN` adında boş bir dosya koy (hece sayımı İngilizceye göre yapılır).
