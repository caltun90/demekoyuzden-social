"""Yatay videolarin YouTube'a otomatik yuklenmesi icin RSS akisi (feed.xml).

Zapier (Cem'in hesabi) bu akisi izler; yeni oge gorunce videoyu YouTube'a normal video olarak yukler.
Buffer yatay videoyu YouTube'a kabul etmez ("Video must be vertical"), o yuzden bu yol kullanilir.

  python3 feed.py add videos/<ad>-yatay.mp4 "YouTube basligi" "Aciklama metni"     -> ogeyi feed.xml'in basina ekler
  python3 feed.py add videos/<ad>-yatay.mp4 "YouTube basligi" @aciklama.txt        -> aciklamayi dosyadan okur
  python3 feed.py list                                                             -> akistaki ogeler

Oge, video dosyasiyla AYNI commit'te ya da ondan sonra push edilmeli (Zapier videoyu raw adresinden indirir).
Ayni video ikinci kez eklenmez. Anahtar gerekmez.
"""
import sys, os, re, email.utils
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FEED = os.path.join(HERE, 'feed.xml')
RAW = 'https://raw.githubusercontent.com/caltun90/demekoyuzden-social/main/'
KEEP = 30   # akista tutulan en yeni oge sayisi


def load():
    if not os.path.exists(FEED): return []
    return [dict(guid=i.findtext('guid'), title=i.findtext('title'), desc=i.findtext('description') or '',
                 url=i.findtext('link'), size=i.find('enclosure').get('length'), date=i.findtext('pubDate'))
            for i in ET.parse(FEED).getroot().iter('item')]


def save(items):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0">', '<channel>',
           '<title>Demek O Yüzden: yatay videolar</title>',
           '<link>https://github.com/caltun90/demekoyuzden-social</link>',
           '<description>YouTube\'a normal video olarak yüklenecek yatay videolar</description>']
    for it in items[:KEEP]:
        out += ['<item>', f'<title>{escape(it["title"])}</title>', f'<link>{escape(it["url"])}</link>',
                f'<guid isPermaLink="false">{escape(it["guid"])}</guid>', f'<pubDate>{it["date"]}</pubDate>',
                f'<description>{escape(it["desc"])}</description>',
                f'<enclosure url="{escape(it["url"])}" length="{it["size"]}" type="video/mp4"/>', '</item>']
    out += ['</channel>', '</rss>', '']
    open(FEED, 'w', encoding='utf-8').write('\n'.join(out))
    ET.parse(FEED)   # bozuk XML yazildiysa burada hata verir


def clean(s):   # YouTube baslik ve aciklamada < > kabul etmez
    return re.sub(r'[<>]', '', s).strip()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'list':
        for it in load(): print(it['date'], '|', it['guid'], '|', it['title'])
    elif cmd == 'add' and len(sys.argv) == 5:
        path, title, desc = sys.argv[2], clean(sys.argv[3]), sys.argv[4]
        desc = clean(open(desc[1:], encoding='utf-8').read() if desc.startswith('@') else desc)
        rel = os.path.relpath(os.path.abspath(path), HERE).replace(os.sep, '/')
        if not (rel.startswith('videos/') and rel.endswith('-yatay.mp4') and os.path.isfile(os.path.join(HERE, rel))):
            sys.exit(f'HATA: {rel} bulunamadi ya da videos/<ad>-yatay.mp4 biciminde degil')
        if not title or len(title) > 100: sys.exit(f'HATA: baslik 1-100 karakter olmali ({len(title)})')
        if not desc or len(desc) > 4500: sys.exit(f'HATA: aciklama 1-4500 karakter olmali ({len(desc)})')
        if '#shorts' in desc.lower(): sys.exit('HATA: yatay video aciklamasinda #shorts olmamali')
        guid = os.path.basename(rel)[:-len('-yatay.mp4')]
        items = load()
        if any(it['guid'] == guid for it in items): print('zaten akista:', guid); sys.exit(0)
        items.insert(0, dict(guid=guid, title=title, desc=desc, url=RAW + rel,
                             size=os.path.getsize(os.path.join(HERE, rel)), date=email.utils.formatdate(usegmt=True)))
        save(items); print('eklendi:', guid, '| akista', min(len(items), KEEP), 'oge')
    else:
        sys.exit(__doc__)
