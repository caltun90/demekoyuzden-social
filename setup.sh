#!/bin/bash
# Bulut ortami kurulumu: skia icin libEGL, Python paketleri, Poppins fontlari.
# Kullanim: ./setup.sh      (tekrar calistirmak guvenli; kurulu olani atlar)
set -euo pipefail
FD=/usr/share/fonts/truetype/google-fonts
SUDO=""; [ "$(id -u)" = 0 ] || SUDO=sudo

# 1) skia-python libEGL.so.1 ister
if ! ldconfig -p | grep -q 'libEGL\.so\.1'; then
  $SUDO apt-get update
  $SUDO apt-get install -y libegl1
fi

# 2) Python paketleri. "pip" baska bir Python surumune bagli olabilir; hep "python3 -m pip" kullan.
python3 -m pip install --break-system-packages skia-python soundfile numpy

# 3) Poppins fontlari (render.py bu klasorden okur). Google Fonts, tarayici olmayan istemciye ttf baglantisi verir.
$SUDO mkdir -p "$FD"
CSS=""
for pair in 400:Regular 500:Medium 700:Bold; do
  wght=${pair%%:*}; out="$FD/Poppins-${pair##*:}.ttf"
  [ -s "$out" ] && continue
  [ -n "$CSS" ] || CSS=$(curl -fsSL --retry 3 -A curl "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700")
  url=$(printf '%s\n' "$CSS" | awk -v w="$wght" '/font-weight:/ { cur = $2 + 0 }
    /src:/ && cur == w { if (match($0, /https:[^)]+\.ttf/)) { print substr($0, RSTART, RLENGTH); exit } }')
  [ -n "$url" ] || { echo "HATA: Poppins $wght icin ttf baglantisi bulunamadi" >&2; exit 1; }
  tmp=$(mktemp)
  curl -fsSL --retry 3 -o "$tmp" "$url"
  $SUDO install -m 644 "$tmp" "$out"; rm -f "$tmp"
done

# 4) Kontrol: skia aciliyor mu, uc font da yukleniyor mu?
python3 - "$FD" <<'EOF'
import sys, skia
for f in ('Poppins-Regular.ttf', 'Poppins-Medium.ttf', 'Poppins-Bold.ttf'):
    assert skia.Typeface.MakeFromFile(f'{sys.argv[1]}/{f}') is not None, f'font yuklenemedi: {f}'
print('kurulum tamam: skia', skia.__version__)
EOF
