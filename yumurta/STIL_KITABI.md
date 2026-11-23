# Yumurta Kafa stili: ölçülmüş stil kitabı

Kaynak: beyaz yumurta / fasulye kafalı karakterlerin 3B bir dünyada oynadığı bu tarzda, en çok izlenen 10 Short (9,8 – 35 milyon izlenme).
Orijinal İngilizce ses iziyle incelendi. Toplam 593 sn, 17.734 kare. Videolar yalnızca stil çalışması için kullanıldı; repoda yok,
raporlarda `r01` – `r10` olarak geçiyorlar. Ölçüm işlenmiş birkaç örnek kare [`referans/`](referans/) klasöründe.

| # | İzlenme | Süre |
|---|---|---|
| r01 | 35M | 64,9 sn |
| r02 | 29M | 65,2 sn |
| r03 | 18M | 60,5 sn |
| r04 | 16M | 64,6 sn |
| r05 | 16M | 39,1 sn |
| r06 | 15M | 45,1 sn |
| r07 | 13M | 59,5 sn |
| r08 | 11M | 63,2 sn |
| r09 | 10M | 65,3 sn |
| r10 | 9,8M | 63,5 sn |

Konu konu ayrıntılı raporlar [`analiz/`](analiz/) klasöründe, ham sayılar [`analiz/veri/`](analiz/veri/) içinde; bu dosya onların özeti.
Kamera ölçümünde her kare 180 × 320'ye küçültülüyor. Kesmeler, yerel medyana göre kare farkıyla bulunuyor ve gözle doğrulanıyor.
Kamera hareketi 10 kare arayla, 41 yakınlaşma adımında faz korelasyonuyla ölçülüyor; ince sonuç parabolik iyileştirmeyle bulunuyor.

## 1. Metin (ses) kalıbı

- **Hız:** 3,30–3,88 kelime/sn (medyan 3,73). İlk kelime 0,0 sn'de. Hiçbir videoda 0,9 sn'den uzun boşluk yok (10 videodan 9'u).
- **Süre:** 8 video 59–65 sn, 2 video 39–45 sn.
- **Kanca:** İlk cümle bir paradoks. Giriş ya da selam yok.
  - "He put a bronze ball in a dragon's mouth and told the emperor if this ever falls out, run."
  - "They buried a man alive with a bell tied to his finger."
- **Açılışta görüntü:** Her videonun ilk 4,4 saniyesinden 0,8 sn arayla 6 kareye bakıldı.
  - 10 videonun 9'unda bu sürede en az 3 farklı görüntü var; çoğunda 4–5.
  - Görüntüler ilk cümlenin parçalarını izliyor. Sık görülen sıra: karakter → nesnenin yakın planı → geniş plan → sonuç.
  - İlk karede karakter, hikâyenin ana nesnesiyle bir şey yapıyor: ejderhanın ağzına top koyuyor, rayı kesiyor, tencereyi denize boşaltıyor.
  - Tek istisna r05: aynı karakter, aynı kadraj, yalnızca yavaş itme.
- **"You see," dönüşü:**
  - 10 videonun 9'unda var.
  - 5'inde hemen ikinci cümlenin başında, kurulumu açmak için kullanılıyor.
  - 3'ünde ikinci kez, açıklamaya geçerken geliyor.
  - Türkçe karşılığı olarak **"Bakın,"** kullanılacak.
- **Kurgu:**
  1. Kanca
  2. "You see" + kurulum
  3. Biri ona güler veya karşı çıkar (diyalog, tırnak içinde)
  4. 3–4 basamakta tırmanış
  5. Karanlık an
  6. "You see" + gerçek mekanizma, gündelik bir benzetmeyle (çorbaya üflemek, virajı hızlı almak)
  7. Son vuruş
- **Döngü:** 10 videonun 3'ünde son cümle yarıda kesiliyor ve videonun başına bağlanıyor ("...drops straight onto the pirates'" → baş).
- **Diyalog:** Tek anlatıcı sesi. Karakter repliklerini aynı ses okuyor, araya tırnak koyarak. Ayrı oyuncu yok.

## 2. Kamera ve kurgu

| Ölçüm | Değer (10 video) |
|---|---|
| Gerçek kesme | Video başına 0–2 (medyan 1). 4 videoda hiç kesme yok |
| Sabit kare oranı | %1–7 (kamera neredeyse hiç durmuyor) |
| İçeri itme (zoom-in) olan kareler | %45–76 |
| Dışarı çekme | %23–49 (çoğu, kameranın geri kayarak sahne açması) |
| İtme hızı (medyan) | Kare başına %0,25–0,37 |
| Kaydırma, %90'lık dilim | 6–17 px/kare (1080 genişlikte) |

- "Kesme gibi görünen" anlar (r01: 23–27. kareler, r09: 1390–1398) aslında **5–9 karelik hızlı zoom ya da süzülme**. Bu anlarda yoğun hareket bulanıklığı var: kamera bir sonraki sahneye uçuyor.
- Sahneler tek bir dünyada akıyor. Kamera bir sonraki ana fiziksel olarak gidiyor.
- Kamera karaktere çok yakın, alçak açıdan ve geniş lensle bakıyor. Ön plandaki karakter kadrajın 1/3–2/3'ünü dolduruyor.

## 3. Işık ve renk

| Ölçüm | Değer |
|---|---|
| Medyan parlaklık | 0,32–0,57. Gece ağırlıklı iki video (r05, r06): 0,16–0,21 |
| Karanlık uç (p5) | 0,07–0,21. Saf siyah yok, en koyu yer bile lacivert/mor |
| Doygunluk (Lab C*, %90'lık dilim) | 38–77 (medyan 49) |
| Karanlık piksel (<%8) | Genelde %1'in altında |

- Gündüz sahnelerinde yüksek doygunluk var: turuncu kaya, mavi gök.
- Gece sahneleri lacivert-mor tonda, sıcak lamba sarısı ile kontrast kuruyor.
- Gün ↔ gece geçişi hikâyeye bağlı.
  - r07: gece başlıyor, gündüze dönüyor, alacakaranlıkta bitiyor.
  - r02: gündüz başlıyor, gün batımında bitiyor.
  - "Açıklamaya geçerken sahne gece mavisine döner" gibi bir kural bu 10 videoda yok: ışık, hikâyedeki zamana uyuyor.
- Arka plan bulanık (alan derinliği), göz öndeki karaktere gidiyor.

### Işığın ölçümü

Saniyede 2 kare alınıyor. Altyazı bandı (yüksekliğin %62–78'i) sayılmıyor; yoksa beyaz yazı "ışık" diye sayılır.

| Ölçüm | Ne demek | 10 referans (ortanca) |
|---|---|---|
| Kontrast | Karedeki aydınlık uç ile karanlık uç arasındaki fark (parlaklığın %95'lik ve %5'lik dilimi) | 0,57–0,81 (0,62) |
| Parlak piksel | Parlaklığı 0,92'nin üstündeki piksel oranı: görünen ışık kaynakları ve patlayan yüzeyler | %0,1–5,2 (1,2) |
| Işık kaynağı olan kareler | İçinde en az %0,15'lik parlak bir leke bulunan karelerin oranı | %32–88 (75) |
| Sıcak ve soğuk birlikte | Hem turuncu-sarı hem mavi-mor tonların karenin en az %8'ini kapladığı karelerin oranı | %1,5–57 (25) |
| Sıcak piksel (turuncu-sarı) | Doygun piksellerde | %0,4–36 (16) |
| Soğuk piksel (mavi-mor) | Doygun piksellerde | %5–45 (23) |

Kareleri tek tek inceleyince görülen kurallar:

- **Işığın kaynağı görüntüde.** Tavan lambası, ay, fener, meşale, pencere. Karelerin dörtte üçünde ekranda parlayan bir kaynak var.
- **Kaynağın çevresinde hale var.** Alev ve lamba, beyazdan daha parlakmış gibi çevresine taşıyor.
- **Sıcak ışık soğuk gölgeye karşı.** Gece sahnesinde lacivert-mor ortam, sarı-turuncu lamba. Gölgeler gri değil renkli.
- **Gölgeler gerçek.** Karakterin ve nesnelerin gölgesi yere ve duvara düşüyor (r04 güverte, r09 duvardaki kronometre, r10 kumsal).
- **Işık huzmesi görünüyor.** Tavan lambasından koni (r05), duvarda sarı bant (r03), pencereden giren demet.
- **Işık düz değil.** En düz referansta bile kontrast 0,57.

### Renk aileleri, gölge ve hale (ayrıntı: `analiz/renk.md`, `analiz/isik.md`)

| Ölçüm | 10 referans (ortanca) |
|---|---|
| Sıcak renklerin payı (kırmızı + sarı-turuncu) | %49 (%18 – %74) |
| Soğuk renklerin payı (camgöbeği + mavi) | %46 (%26 – %68) |
| En koyu yüzeyler (çizgiler sayılmadan, parlaklığın %5'lik dilimi) | 0,15 (0,04 – 0,23) |
| Aydınlık yüzeylerin renk yoğunluğu (Lab C*) | 32 (18 – 60) |
| Gölgelerin rengi (Lab b*; eksi = maviye) | −9 (−27 – +5) |
| Gölge / aydınlık, aynı yüzeyde | yaklaşık 0,5 |
| Lambanın halesi | geniş ve düz: 20 px ötede parlaklığın 0,45'i, 40 px ötede 0,37'si duruyor |
| Kafanın parlaklığı (HSV V) ve tonu (S) | V 0,98 (0,89 – 1,00), S 0,09 (0,00 – 0,24) |

- **Tek renge boyanmış kare yok.** Sıcak ve soğuk kareyi paylaşıyor; turuncu ışık turuncu duvara vurmuyor.
- **Gölge kahverengi değil.** Aynı yüzeyin aydınlığının yarısı kadar parlak ve ortamın rengine (çoğu zaman maviye) kaymış.
- **İç mekânda ışık lekesi bir renk değişimi:** soğuk renkli duvarda sıcak leke.

## 4. Dünya

- Gerçek 3B geometri: kanyon, gemi güvertesi, kasaba, oda. Dokular boyanmış gibi; tahta derzleri ve taşlar elle çizilmiş gibi.
- Siyaha yakın mürekkep çizgileri var, ama yalnızca silüetlerde ve kenarlarda.
- Kesit görünümleri (mezar toprağının altı) ve iç mekân / dış mekân geçişleri kullanılıyor.
- Yazılı sahne nesneleri sık: gazete, ölüm belgesi, takvim, tabela. Bunlar hikâyeyi anlatıyor, okunacak kadar büyük gösteriliyor.

## 5. Karakterler (30 fps kare kare inceleme)

- **Kafa:** Bembeyaz; genişliği yüksekliğinden biraz fazla (yaklaşık 1,07 kat). Tam bir elips değil: tepesi hafif sivri, çenesi dolgun, yüzün döndüğü yanda biraz şişkin. Dış çizgi koyu mürdüm; ortalama kalınlığı kafa genişliğinin yaklaşık %5'i, ama altta ve ışığın gelmediği yanda üstteki kalınlığın yaklaşık 3 katı.
- **Kafanın gölgesi:** Kafa düz beyaz; yalnızca ışığın gelmediği kenarda ve altta yumuşak, çok açık (yaklaşık 0,89 kat), lavanta bir gölge var. Gölgenin rengi sahneye göre değişiyor: gece gri-mavi, lamba ışığında sıcak krem. Lambaya yakın duran kafanın o tarafında hafif sıcak bir ton oluyor.
- **Gövde:** Kafadan dar (kafa genişliğinin %60–70'i), yuvarlak köşeli bir torba. Kıyafet ayrıntılı: çizgi, düğme, yaka, cep, kuşak.
- **Uzuvlar:** Kollar ve bacaklar dış çizgi kalınlığında koyu çizgiler. Eller başparmağı belli olan küçük yuvarlak eldivenler. Ayaklar küçük oval. Toplam boy yaklaşık 3,5 kafa.
- **Gözler (8 yakın plan kareden ölçüldü):** Nokta değil, oval de değil.
  - Göz, düz bir **göz kapağı çizgisinden** sarkan koyu bir yarım daire: genişliği kafa genişliğinin yaklaşık %13'ü, yüksekliği %9 – 10'u. Kapak çizgisi yarım daireden biraz geniş (%17).
  - İki gözün arası (merkezden merkeze) kafa genişliğinin %26 – 30'u. Gözler birbirine yakın.
  - Kapak çizgisinin eğimi duyguyu değiştiriyor: iç ucu aşağıdaysa kızgın, düzse umursamaz, daha aşağı inmişse kendinden emin.
  - Şaşkınlıkta gözler bambaşka: birbirine değen iki beyaz daire (çap %22), ortalarında küçük birer nokta. Gülerken gözler ters yay (∩ ∩).
- **Kaşlar:** Gözün epey üstünde duran, ortası kalın, uçları incelen kısa fırça darbeleri. Şapkanın kenarına kadar çıkabiliyor.
- **Yüzün yeri:** Gözler kafa yüksekliğinin üstten %34–48'inde, ağız %60–68'inde. Karakter nereye bakıyorsa **bütün yüz o tarafa kayıyor** (3/4 dönüş) ve o taraftaki göz daralıyor.
- **Ağız:** Küçük ve kalın çizgili. Düz hâli hafif kırık bir çizgi. Sırıtışta ağzın bir ucu yukarı kıvrılıyor. Kahkahada dişler görünüyor: üstte beyaz bir sıra, aralarında dikey çizgiler.
- **Bıyık, sakal, gözlük ve şapka** kişiliği veriyor.
- **Ağız senkronu:** Konuşan karakterin ağzı 2–3 karede bir açılıp kapanıyor. Konuşmayan karakterin ağzı kapalı.
- **Mikro hareketler:** Kafa sallama, konuşurken öne eğilme, omuz kaldırma, ter damlası, öfke dumanı. Göz kırpma 1 – 2 sn'de bir, dört kare sürüyor (yarım, kapalı, kapalı, yarım); ifade değişimleri bir göz kırpmanın içinde oluyor. Oynamayan karakter hiç kıpırdamıyor: nefes ya da sallanma döngüsü yok.
- **Mimik sıklığı:** Yüz ifadesi sahne boyunca aynı kalmıyor; her önemli kelimede değişiyor (şaşkınlık → kızgınlık → sırıtış).
- **Duygu anları:** Yüz renk değiştiriyor (öfkede mor) ve buhar bulutu çıkıyor.

## 6. Altyazı

- Her seferinde 1–2 kelime, konuşmayla aynı anda.
- Beyaz, kalın, yuvarlak hatlı sans-serif yazı; kalın koyu kontur ve yumuşak gölge.
- Yatayda ortada, dikeyde ekranın yaklaşık %70'inde. Yükseklik yaklaşık 64 px (1080 genişlikte).

## 7. Ses

- Anlatıcı sesi baskın, konuşma kesintisiz.
- Altında hafif bir müzik yatağı var (otomatik altyazıda "[music]" etiketi).
- Olay sesleri: çan, metal tıngırtısı, patlama.

## Bizim kurallarımız (stilden çıkardıklarımız)

1. Remotion ve Blender yok. Dünya three.js ile tarayıcıda çiziliyor, karakterler Canvas 2D ile. Kareler tek tek yakalanıyor, ffmpeg birleştiriyor.
2. Hikâye, karakterler ve ses tamamen bizim. Referanstan yalnızca ölçülen sayılar alınıyor.
3. Kamera hiçbir zaman sabit durmuyor: her an kare başına %0,2–0,35 itme. Sahne geçişleri ya 18–40 karelik süzülme ya da 5–8 karelik hızlı zoom (hareket bulanıklığıyla). En fazla 1 sert kesme.
4. Konuşan karakterin ağzı sesin genliğine göre açılıp kapanıyor. Her karakter 0,9 – 2,4 sn'de bir ve her ifade değişiminde göz kırpıyor. Oynamayan karakter sabit duruyor; tepkiler kelimeden iki kare önce geliyor.
5. Altyazı tek tek kelime, ekranın %70 yüksekliğinde.
6. Saf siyah yok: en koyu ton lacivert/mor. Mürekkep çizgileri `#0b0a0c`, karakter çizgisi mürdüm `#2a1a2c`. Dünya çizgisi ince: 1080 genişlikte yakında 3,4 px, uzakta 2,2 px. Dokuya boyanan çizgiler bundan da ince ve açık.
7. Açılış, ilk 5 saniyede 3–4 ayrı görüntüden oluşuyor ve her görüntü ilk cümlenin bir parçasını gösteriyor. İlk karede karakter ana nesneyle bir şey yapıyor.
8. Kafalar her sahnede beyaz. Kart rengi, renk düzeltmesinin tonunu geri alacak şekilde ayarlanıyor.
9. Bir el bir şeye dokunuyorsa gerçekten dokunuyor. Nesne 3B ise kol da 3B çiziliyor (`Arm3D`).
10. Ölçüm tuttuktan sonra video baştan sona izleniyor. Kesik şapka, boşta duran el ve düz renkli pencere ölçümde görünmüyor.
11. Her sahnede görünen tek bir ana ışık var (kandil, pencere, ay). Sıcak ışık soğuk gölgeye karşı duruyor ve gerçek gölge düşürüyor; karakterlerin gölgesi de buna dahil.
12. Işık veren her şeyin rengi beyazdan parlak veriliyor; yalnızca bunlar hale yapıyor. Beyaz kafalar hale yapmıyor.
13. Gözler kapak çizgisinden sarkan yarım daire, birbirine yakın; kaşlar gözün üstünde ayrı. Yüz, bakış yönüne kayıyor. İfade her vuruşta değişiyor. Kafa simetrik bir elips değil, dış çizgisi altta kalın.
14. Hiçbir iki yüzey aynı düzlemde durmuyor (titreme yapar). Bir nesnenin yeri her karede hesaplanıyor, önbellekten alınmıyor.
15. Sıcak ve soğuk kareyi paylaşıyor: bir sahnede sıcak renklerin payı %75'i geçmiyor. Sıcak ışık soğuk renkli yüzeye vuruyor.
16. Gölge, aynı yüzeyin aydınlığının 0,3 – 0,5 katı ve ortamın renginde; kahverengi gölge yok.
17. Lambanın halesi geniş ve düz; yalnızca ışık veren şeyler hale yapıyor. Kameranın yaklaştığı lambada ayrıca zayıf, geniş bir ışık halkası var; kareyi doldurduğu planda kısılıyor, yoksa soğuk renkli odayı turuncuya boyuyor.
18. Arka plan bulanıklığı her planda değil: yakın planda, ayrıntı planında ve ön planında nesne olan planda.

## Örnek videonun ölçümü (İs Odası, aynı yöntemle)

| Ölçüm | Referans aralığı (ortanca) | İs Odası |
|---|---|---|
| Sabit kamera | %1–7 (3) | %1,8 |
| Kaydırma olan kareler | %77–94 (86) | %85 |
| İtme hızı | %0,25–0,37/kare (0,28) | 0,28 |
| Karanlık piksel (<%8) | %0,2–15 (0,6) | %0,4 |
| Karanlık uç (p5) | 0,04–0,21 (0,13) | 0,11 |
| Doygunluk C* p90 | 30–77 (49) | 47 |
| Sert kesme | 0–2 | 1 |
| Kontrast | 0,57–0,81 (0,62) | 0,72 |
| Parlak piksel | %0,1–5,2 (1,2) | %3,4 |
| Işık kaynağı olan kareler | %32–88 (75) | %77 |
| Sıcak ve soğuk birlikte | %1,5–57 (25) | %19 |
| Sıcak renklerin payı (kırmızı dahil) | %18–74 (49) | %41 |
| Soğuk renklerin payı | %26–68 (46) | %41 |
| Lambanın halesi, 20 / 40 px ötede | 0,45 / 0,37 | 0,50 / 0,36 |
| İnce ayrıntı | 0,042–0,081 (0,062) | 0,059 |
| İnce çizgilerin payı | %60–82 (72) | %67 |
| Görüntünün dönmesi (10 sn'de) | 0,0–1,9 (0,6) | 1,8 (kamera yatmadan) |
| Titreyen piksel | %1,58–4,57 (2,53) | %1,23 |

- Hikâyenin büyük kısmı gece geçtiği için orta parlaklık (0,29) gece referansları (r05: 0,16, r06: 0,21) ile gündüz referansları (0,32–0,57) arasında.
- "Sıcak ve soğuk birlikte" ölçüsü sıcak olarak yalnızca turuncu-sarıyı sayıyor; salonda sıcak taraf kırmızı halı ve alevler. Kırmızıyı da sayan renk aileleri ölçümünde sıcak ve soğuk eşit (%41 / %41).
- Görüntü, kamera hiç yatmadığı hâlde kubbeye dik bakan iki planda dönüyor; bu yüzden kameraya yatış eklenmedi.

### Ölçümün tek başına göremediği kusurlar

Sayılar tuttuktan sonra video izlenince bulunanlar. Bir şey "göze yanlış geliyorsa" önce onu gösterecek bir sayı arayın; düz ışık ve tek renk sahne sonradan ölçülebilir çıktı.

| Kusur | Sebep | Çözüm |
|---|---|---|
| Kafalar krem rengi | Kart rengi sahne ışığıyla çarpılıyor, renk düzeltmesi de üstüne biniyor | Kafa `#ffffff`; kart rengi = istenen ton / düzeltmenin tonu |
| Sarığın tepesi ve eldeki tomar düz bir çizgiyle kesik | Karakter tuvali dar | Tuval 768 × 1184; figür aynı boyda, çevresinde pay var |
| El bir yerde, kalem başka yerde | Karakter 2B kart, kalem 3B nesne | Kol 3B (`Arm3D`), el kalemi tutuyor. Karıştırma çubuğunda ve kandilde de aynısı |
| Pencerenin dışı düz renk | Arkada tek renkli düzlem | Bakış yönüne göre örneklenen boyalı panorama (`vistaMat`) |
| Pencerenin altında ve üstünde taşlar küçük | Duvar parçalıydı, her parça dokuyu baştan sarıyordu | Tek parça delikli duvar (`holedWall`), doku metre cinsinden |
| Açılışta 5 saniye duran karakter | Tek plan | 4 görüntü: kandil → kubbe → dumanla uçuş → kilitlenen oda |
| Kâğıt turuncu | Sıcak ışık altında aydınlanan malzeme | Işıktan etkilenmeyen krem malzeme |
| Pencere kasası titriyor | Kasanın bir yüzü duvarla aynı düzlemde; ekran kartı her karede ikisinden birini seçiyor | Kasa duvardan 6 cm önde. Hiçbir iki yüzey aynı düzlemde durmuyor |
| Kalem bazı karelerde çizginin sonuna zıplıyor | Kalem yerini, yalnızca çizgi uzayınca çalışan çizim fonksiyonundan alıyordu | Kalemin yeri her karede hesaplanıyor; yalnızca çizim önbellekte |
| Işık düz, sahneler "boyanmış karton" gibi | Güçlü ortam ışığı her yeri eşit aydınlatıyor; gölge yok, kaynaklar parlamıyor | Sahne başına tek ana ışık, gerçek gölgeler, beyazdan parlak alevler ve hale, ışık huzmeleri. Kontrast 0,72 (en düz referans 0,57) |
| Bir sahne tek renk turuncu | Krem duvara turuncu ışık | Soğuk renkli duvar ve halı; güneş duvarda sıcak bir leke yapıyor |
| Gölgeler kahverengi | Ortam ışığının alttan yansıması sıcak | Dolgu ışığı mavi, yansıma mor; tavan ahşabı mürdüm |
| Kaşlar görünmüyor | Şapka kaşların üstüne çiziliyor | Yüz şapkadan sonra çiziliyor; şapkalar biraz yukarıda |
| Duvarlar boş | Düz duvar; derz ne kadar ince olsa da ayrıntı ölçüsü oynamıyor | Desen: çini kuşağı, boyalı kuşak, pencere çevresinde pano; halıya motif |
| Kubbe bulanık | Önceki planın odak ayarı kubbe planlarına taşınmış | Bulanıklık, kamera bir sonraki plana dönerken kapanıyor |
| Bir odada zemin yok, yer lacivert | Zemini sahneye ekleyen kod, aynı satırdaki bir açıklamanın içinde kalmış | Satır bölündü. Uzun tek satırlık kodu değiştirdikten sonra resme bakın |
| Yakın planda kandilin halkası mavi odayı turuncuya boyuyor | Halka dünyada sabit boyda; yakında kareyi dolduruyor | O sahnede halka kısık (`haloK`) |
