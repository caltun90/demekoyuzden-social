#!/bin/bash
# Kullanim: ./build.sh video-adi      (voice/final.wav ve voice/final.json hazir olmali)
# Cikti: video-adi-dikey.mp4 (1080x1920, Instagram/TikTok) ve video-adi-yatay.mp4 (1920x1080, YouTube)
set -e
NAME="${1:-video}"; NAME="${NAME%.mp4}"
for F in v h; do
  [ "$F" = v ] && OUT="$NAME-dikey.mp4" || OUT="$NAME-yatay.mp4"
  PIDS=()
  for k in 1 2 3 4 5 6; do FMT=$F python3 render.py scene $k & PIDS+=($!); done
  FAIL=""
  for i in "${!PIDS[@]}"; do wait "${PIDS[$i]}" || FAIL="$FAIL $((i + 1))"; done
  if [ -n "$FAIL" ]; then echo "HATA: FMT=$F render edilemeyen sahne(ler):$FAIL. Video uretilmedi." >&2; exit 1; fi
  for k in 1 2 3 4 5 6; do echo "file 'scenes_$F/s$k.mp4'"; done > list_$F.txt
  ffmpeg -y -loglevel error -f concat -safe 0 -i list_$F.txt -c copy silent_$F.mp4
  ffmpeg -y -loglevel error -i silent_$F.mp4 -i voice/final.wav -map 0:v -map 1:a -c:v copy \
    -af "aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11" -c:a aac -b:a 160k -movflags +faststart -shortest "$OUT"
  echo "$OUT $(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUT") sn"
done
