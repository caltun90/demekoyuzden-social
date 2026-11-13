"""Demek O Yuzden, haftalik uzun video #1: Bir gunde beyninin sana oynadigi 6 oyun.
Yatay 1920x1080, ~9 dk. Bir gunun hikayesi: her bolum bir saat dilimi, bir etki.

SEQ: ('scene', no) | ('beat', ad, sn) | ('line', id, 'N', altyazi, vurgu, sonraki_bosluk)
"""
import re
TITLE = 'Beyninin Sana Oynadığı 6 Oyun'

SEQ = [
    ('scene', 0),
    ('beat', 'alarm', 2.2),
    ('line', 'i1', 'N', 'Sabah yedi. Alarm çalıyor ve sen daha gözünü açmadan, beynin bugün sana en az altı kez oyun oynamaya hazırlanıyor.', ['altı', 'kez', 'oyun'], 0.5),
    ('line', 'i2', 'N', 'Bunlar arıza değil. Her birinin bir adı var ve her biri bilim insanlarının deneylerle yakaladığı bir şey.', ['adı', 'var'], 0.5),
    ('line', 'i2b', 'N', 'Bu videoda altı bölüm var. Her bölüm, günün bir saati.', ['altı', 'bölüm'], 0.5),
    ('line', 'i3', 'N', 'Hadi bir günü birlikte yaşayalım. Her oyunda dur, adını öğren ve kendine şunu söyle: demek o yüzden!', ['demek', 'o', 'yüzden!'], 0.4),
    ('beat', 'title', 3.6),

    ('scene', 1),
    ('beat', 'clock1', 2.6),
    ('line', 'k1', 'N', 'Saat yedi buçuk. Kahvaltı hazırlarken telefonunun şarj aletini almak için yatak odasına gidiyorsun.', [], 0.3),
    ('line', 'k2', 'N', 'Kapıdan geçiyorsun, odanın ortasında duruyorsun ve... ne almaya gelmiştin?', ['ne', 'almaya'], 0.8),
    ('line', 'k3', 'N', 'Bunun adı kapı eşiği etkisi.', ['kapı', 'eşiği', 'etkisi.'], 0.5),
    ('line', 'k4', 'N', "Notre Dame Üniversitesi'nden Radvansky ve ekibi, 2011'de bunu ölçtü. Önce bir bilgisayar oyununda: insanlar sanal odalarda dolaşıp bir masadan nesne alıyor, başka bir masaya bırakıyordu.", ['Radvansky'], 0.3),
    ('line', 'k5', 'N', 'Kapıdan geçip başka odaya gidenler, aynı mesafeyi aynı odada yürüyenlere göre taşıdıkları şeyi daha çok unuttu.', ['kapıdan', 'geçip', 'daha', 'çok'], 0.4),
    ('line', 'k5b', 'N', 'Sonra deneyi gerçek odalarda, gerçek masalar ve kutularla tekrarladılar. Sonuç aynıydı.', ['Sonuç', 'aynıydı.'], 0.4),
    ('line', 'k6', 'N', 'Neden mi? Beynin hayatı bölüm bölüm kaydediyor. Kapı, yeni bir bölümün başladığını söylüyor ve eski bölüm rafa kalkıyor.', ['bölüm', 'rafa', 'kalkıyor.'], 0.4),
    ('line', 'k7', 'N', 'İşin ilginci, ilk odaya geri dönmek de hafızayı geri getirmedi. Önemli olan, kaç kapıdan geçtiğin.', ['geri', 'getirmedi.'], 0.4),
    ('line', 'k8', 'N', 'Bu neden önemli? Unuttuğunda kendine kızma. Bu dikkatsizlik değil, beyninin düzen tutma şekli.', ['düzen', 'tutma'], 0.9),

    ('scene', 2),
    ('beat', 'clock2', 2.6),
    ('line', 's1', 'N', 'Dokuz buçuk. İşe vardın ve ilk yudumda kahveyi gömleğine döktün.', ['kahveyi'], 0.3),
    ('line', 's2', 'N', 'Bütün gün herkesin o lekeye baktığından eminsin. Asansörde, toplantıda, koridorda.', ['herkesin'], 0.6),
    ('line', 's3', 'N', 'Bunun adı sahne ışığı etkisi. Sanki bir projektör hep senin üstünde.', ['sahne', 'ışığı', 'etkisi.'], 0.4),
    ('line', 's4', 'N', "Cornell Üniversitesi'nde Gilovich ve ekibi, 2000 yılında öğrencilere utanç verici bir tişört giydirip onları kalabalık bir odaya soktu.", ['utanç', 'verici'], 0.3),
    ('line', 's5', 'N', 'Tişörtü giyenler, odadakilerin yaklaşık yarısının fark ettiğini sandı. Gerçekte fark edenler dörtte birden azdı.', ['yarısının', 'dörtte', 'birden', 'azdı.'], 0.4),
    ('line', 's5b', 'N', 'Bir başka deneyde öğrenciler hiç de utanç verici olmayan bir tişörtü kendileri seçti. Yine yarısının fark edeceğini sandılar. Fark edenler yüzde onu bile bulmadı.', ['yüzde', 'onu'], 0.4),
    ('line', 's6', 'N', 'Neden? Kendi lekeni çok net görüyorsun ve herkesin de aynı netlikte gördüğünü varsayıyorsun. Oysa herkes kendi projektörünün altında.', ['kendi', 'projektörünün'], 0.4),
    ('line', 's6b', 'N', 'Bir de şu çıktı: tişörtü giydikten sonra on beş dakika bekleyenlerin tahmini düştü. Yani o his, zamanla sönüyor.', ['zamanla', 'sönüyor.'], 0.4),
    ('line', 's7', 'N', 'Bu neden önemli? Herkes sana bakıyor gibi geldiğinde hatırla: çoğu kişi o an kendi lekesini düşünüyor.', ['kendi', 'lekesini'], 0.9),

    ('scene', 3),
    ('beat', 'clock3', 2.6),
    ('line', 'd1', 'N', 'Saat on bir. Toplantıdasın ve geçen ay tanıştığın müşteri içeri giriyor. Adı... adı neydi?', ['adı', 'neydi?'], 0.6),
    ('line', 'd2', 'N', 'İlk harfini biliyorsun. Kaç heceli olduğunu bile biliyorsun. Ama ismin kendisi bir türlü gelmiyor.', ['İlk', 'harfini'], 0.5),
    ('line', 'd3', 'N', 'Bunun adı dilimin ucunda hissi. Pek çok dilde bu duygu için aynı benzetme kullanılıyor: dilin ucu.', ['dilimin', 'ucunda'], 0.4),
    ('line', 'd4', 'N', "Harvard'da Brown ve McNeill, 1966'da öğrencilere az bilinen kelimelerin tanımlarını okudu. Kelimeyi bulamayanlar bile çoğu zaman ilk harfi ve hece sayısını doğru tahmin etti.", ['ilk', 'harfi', 'hece', 'sayısını'], 0.4),
    ('line', 'd5', 'N', 'Araştırmalara göre çoğumuz bunu haftada yaklaşık bir kez yaşıyoruz. Yaşla birlikte biraz artıyor ve en çok özel isimlerde oluyor.', ['haftada', 'özel', 'isimlerde'], 0.4),
    ('line', 'd6', 'N', 'Neden? Kelimenin anlamı hazır, ama anlamı sese bağlayan köprü o an zayıf. Özellikle uzun süredir kullanmadığın kelimelerde.', ['köprü'], 0.4),
    ('line', 'd6b', 'N', 'Bu yüzden biri ismin ilk hecesini söylediğinde, isim çoğu zaman hemen geliyor. Köprünün eksik parçası ses tarafında.', ['ilk', 'hecesini'], 0.4),
    ('line', 'd7', 'N', 'Bu neden önemli? Zorlamayı bırakabilirsin. Bu anların yaklaşık yarısı kısa süre içinde kendiliğinden çözülüyor.', ['kendiliğinden', 'çözülüyor.'], 0.9),

    ('scene', 4),
    ('beat', 'clock4', 2.6),
    ('line', 'e1', 'N', 'Öğleden sonra iki. Yemekten yeni döndün ve karşındaki arkadaşın esniyor. Birkaç saniye sonra sen de esniyorsun.', ['sen', 'de'], 0.5),
    ('line', 'e2', 'N', 'Belki şu an, bunu dinlerken sen de esnemek üzeresin.', ['şu', 'an,'], 1.0),
    ('line', 'e3', 'N', "Esnemek bulaşıcı. Psikolog Provine, 1986'da insanlara beş dakika boyunca esneyen yüzler izletti. İzleyenlerin yarısından fazlası esnedi.", ['yarısından', 'fazlası'], 0.4),
    ('line', 'e3b', 'N', 'Hatta esnemeyi okumak ya da düşünmek bile bazı insanları esnetmeye yetiyor. Şempanzelerde de bulaşıcı esneme görülmüş.', ['okumak', 'düşünmek'], 0.4),
    ('line', 'e4', 'N', 'Tanıdık birinin esnemesi daha kolay bulaşabiliyor. Küçük çocuklarda ise bu bulaşma dört beş yaşından önce pek görülmüyor.', ['Tanıdık'], 0.4),
    ('line', 'e5', 'N', 'Neden? İşte burada bilim hâlâ tam emin değil. Bir açıklama empatiyle ilgili, ama bu bağlantı tartışmalı.', ['emin', 'değil.'], 0.4),
    ('line', 'e6', 'N', 'Bu neden önemli? Bir toplantıda esnemen sıkıldığın anlamına gelmeyebilir. Belki sadece birini fark ettin.', ['fark', 'ettin.'], 0.9),

    ('scene', 5),
    ('beat', 'clock5', 2.6),
    ('line', 'a1', 'N', 'Saat dört. Bir sunum hazırlıyorsun ve slayta aynı kelimeyi tekrar tekrar yazıyorsun: rapor, rapor, rapor.', ['rapor,'], 0.5),
    ('line', 'a2', 'N', 'Bir süre sonra kelime tuhaflaşıyor. Sanki hiç var olmamış, uydurma bir sesmiş gibi.', ['tuhaflaşıyor.'], 0.5),
    ('line', 'a2b', 'N', 'İstersen şimdi dene: kaşık kelimesini yirmi kez hızlı hızlı söyle. Sonuna doğru tuhaf gelecek.', ['kaşık'], 1.2),
    ('line', 'a3', 'N', "Bunun adı anlamsal doygunluk. Daha 1907'de araştırmacılar, uzun süre bakılan bir kelimenin yabancı görünmeye başladığını yazmıştı.", ['anlamsal', 'doygunluk.'], 0.4),
    ('line', 'a4', 'N', "Terim 1960'larda McGill Üniversitesi'nde ortaya çıktı. Deneylerde bir kelimeyi hızlı hızlı tekrarlayan kişiler, anlamını daha zayıf hissetti.", ['daha', 'zayıf'], 0.4),
    ('line', 'a5', 'N', 'Neden? Kelimenin biçimi ile anlamı arasındaki bağ, art arda kullanılınca kısa süreliğine yoruluyor.', ['bağ,', 'yoruluyor.'], 0.4),
    ('line', 'a6', 'N', 'Bu neden önemli? Endişelenme, kalıcı değil. Birkaç saniye başka bir şeye geç, anlam geri gelir.', ['kalıcı', 'değil.'], 0.9),

    ('scene', 6),
    ('beat', 'clock6', 2.6),
    ('line', 'z1', 'N', 'Gece on bir. Yataktasın, ama aklın hâlâ yarım bıraktığın o e-postada.', ['yarım'], 0.4),
    ('line', 'z2', 'N', 'Bitirdiğin işler gün boyunca hiç aklına gelmedi. Peki yarım kalanlar neden peşini bırakmıyor?', ['peşini'], 0.6),
    ('line', 'z3', 'N', "1927'de Berlin'de Bluma Zeigarnik, yarıda kesilen işlerin bitirilenlerden daha iyi hatırlandığını öne sürdü. Buna Zeigarnik etkisi dendi.", ['Zeigarnik', 'etkisi'], 0.4),
    ('line', 'z3b', 'N', 'Anlatılan hikayeye göre fikir, siparişleri yazmadan hatırlayan ama hesap ödenince hepsini unutan bir garsondan çıktı.', ['garsondan'], 0.4),
    ('line', 'z4', 'N', "Ama 2025'te Bern Üniversitesi'nden iki araştırmacı, yaklaşık yüz yıllık deneyleri bir araya getirdi. Bu hafıza avantajı tekrar bulunamadı.", ['tekrar', 'bulunamadı.'], 0.4),
    ('line', 'z5', 'N', "Sağlam çıkan başka bir şeydi: Zeigarnik'in meslektaşı Maria Ovsiankina'nın gösterdiği gibi, insanlar yarıda kalan işe geri dönme isteği duyuyor.", ['geri', 'dönme', 'isteği'], 0.4),
    ('line', 'z6', 'N', 'Yani yarım işi daha iyi hatırlamıyorsun. Ama zihnin, onu kapatman için seni dürtüyor.', ['dürtüyor.'], 0.4),
    ('line', 'z7', 'N', 'Bu neden önemli? Başka bir çalışmada, yarım kalan iş için ne zaman ve nasıl devam edeceğini yazmak, o işin zihni meşgul etmesini azalttı.', ['yazmak,'], 0.9),

    ('scene', 8),
    ('beat', 'night', 1.2),
    ('line', 'o1', 'N', 'Ve gün bitti. Bugün beynin sana altı kez oyun oynadı: kapıda unuttun, lekeyi büyüttün, ismi bulamadın, esnedin, bir kelimeyi yabancılaştırdın ve yarım işi yatağa taşıdın.', ['altı', 'kez'], 0.6),
    ('line', 'o2', 'N', 'Hiçbiri arıza değil. Hepsi, beyninin sıradan ve çoğu zaman işe yarayan çalışma şeklinin yan etkileri.', ['arıza', 'değil.'], 0.5),
    ('line', 'o2b', 'N', 'Onları tanımak işe yarıyor. Bir dahaki sefere kapıda durduğunda, kendine kızmak yerine gülümseyebilirsin.', ['gülümseyebilirsin.'], 0.5),
    ('line', 'o3', 'N', 'Senin başına en çok hangisi geliyor? Yorumlara yaz.', ['Yorumlara', 'yaz.'], 0.4),
    ('line', 'o4', 'N', 'Bir sonraki videoda görüşmek üzere!', ['görüşmek', 'üzere!'], 0.3),
    ('beat', 'end', 5.0),
]

# TTS okunuslari (altyazi ozgun yazimi gosterir)
PRON = {"Notre Dame": "Notır Deym", "Radvansky": "Radvanski", "Cornell": "Kornel", "Gilovich": "Gilloviç", "McNeill": "Mekneyl",
        "Harvard'da": "Harvırd'da", "Provine": "Provayn", "McGill": "Mekgil", "Zeigarnik": "Zaygarnik", "Ovsiankina": "Ovsiyankina", "Bluma": "Bluma",
        "e-postada": "e-postada"}
def say(t):
    for a, b in PRON.items(): t = t.replace(a, b)
    return t

VOICES = {'N': 'Achird'}
NAMES = {}
STYLE = ('Sıcak, samimi ve rahat bir tonla, yakın bir arkadaşına anlatır gibi, merak uyandırarak ve akıcı bir Türkçe ile oku. '
         'Çok yavaşlama, ama acele de etme. Her paragraftan sonra belirgin biçimde, yaklaşık bir saniye dur:')
_ids = [it[1] for it in SEQ if it[0] == 'line']
_sc = {}
cur = 0
for it in SEQ:
    if it[0] == 'scene': cur = it[1]
    elif it[0] == 'line': _sc[it[1]] = cur
GROUPS = {
    'g1': dict(ids=[i for i in _ids if _sc[i] in (0, 1, 2)], style=STYLE),
    'g2': dict(ids=[i for i in _ids if _sc[i] in (3, 4)], style=STYLE),
    'g3': dict(ids=[i for i in _ids if _sc[i] in (5, 6, 8)], style=STYLE),
}
LINES = {it[1]: dict(id=it[1], spk=it[2], text=it[3], say=say(it[3]), hl=it[4], gap=it[5] + (0.25 if it[5] < 2 else 0), scene=_sc[it[1]]) for it in SEQ if it[0] == 'line'}
SEG_ALIAS = {}
# TTS'siz ses duzeltmeleri (ham ses saniyesi): 'aletini'deki a uzatildi; o3 'Her hafta...' cumlesinden once kesildi
FIX = dict(stretch={'g1': [(24.105, 24.185, 2.3)]}, clip={'o3': 137.46})

# ---- fon ve efektler ----
AM = [110.0, 164.81, 220.0, 261.63]
CM = [130.81, 196.0, 261.63, 329.63]
FM = [87.31, 130.81, 174.61, 220.0]
GM = [98.0, 146.83, 196.0, 246.94]

def mix_plan(T):
    B, S, tot = T['beats'], T['scenes'], T['total']
    keys = sorted(S, key=lambda k: S[k])
    chords = [CM, FM, GM, AM, CM, FM, GM, AM, CM]
    pads = []
    for n, k in enumerate(keys):
        a = S[k]; b = S[keys[n + 1]] if n + 1 < len(keys) else tot
        pads.append((a, b, chords[n % len(chords)], 0.9))
    fx = [('ring', B['alarm'][0] + 0.15, 0.32, dict(d=1.5)), ('chime', B['title'][0] + 0.1, 0.6, dict(freqs=[523.25, 659.3, 783.99]))]
    for k in range(1, 7):
        c0 = B[f'clock{k}'][0]
        for j in range(3): fx.append(('tick', c0 + 0.15 + j * 0.32, 0.45, {}))
        fx.append(('ding', c0 + 1.1, 0.35, {}))
    fx.append(('chime', B['end'][0] + 0.2, 0.55, dict(freqs=[523.25, 783.99], d=2.6)))
    return dict(pads=pads, fx=fx)
