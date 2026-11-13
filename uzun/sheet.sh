#!/bin/bash
# sheet.sh <out.png> <tile_w> files...
out=$1; tw=$2; shift 2; n=$#
inputs=""; for f in "$@"; do inputs="$inputs -i $f"; done
filt=""; for i in $(seq 0 $((n-1))); do filt="$filt[$i]scale=$tw:-1[s$i];"; done
for i in $(seq 0 $((n-1))); do filt="$filt[s$i]"; done
ffmpeg -y -loglevel error $inputs -filter_complex "${filt}hstack=inputs=$n" $out
