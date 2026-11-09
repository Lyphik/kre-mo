#!/usr/bin/env bash
# BAD LIFE V4 — comparatif 4 vues (1080p, H.264) : SOURCE | A | B | C, synchronises, audio source.
# Usage : compare4.sh SOURCE DEBUT_S DUREE_S A.mp4 B.mp4 C.mp4 SORTIE.mp4
set -euo pipefail
SRC="$1"; SS="$2"; DUR="$3"; A="$4"; B="$5"; C="$6"; OUT="$7"
L="fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=6:x=12:y=12"
ffmpeg -hide_banner -loglevel error -y -ss "$SS" -i "$SRC" -i "$A" -i "$B" -i "$C" -t "$DUR" -filter_complex \
 "[0:v]scale=960:540:flags=lanczos,drawtext=text='SOURCE':$L[s];\
  [1:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='A - etalonnage v4':$L[a];\
  [2:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='B - + atmosphere':$L[b];\
  [3:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='C - + lumiere':$L[c];\
  [s][a]hstack[t];[b][c]hstack[u];[t][u]vstack[v]" \
 -map "[v]" -map 0:a:0 -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
