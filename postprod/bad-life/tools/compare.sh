#!/usr/bin/env bash
# BAD LIFE — video de comparaison AVANT / APRES (1080p, H.264) pour validation sur telephone ou ordinateur.
# Usage : compare.sh SOURCE RENDU_ETALONNE DEBUT_S FIN_S SORTIE.mp4
# Gauche : source ; droite : rendu etalonne (reduit). Audio : celui de la source.
set -euo pipefail
SRC="$1"; GRADED="$2"; SS="$3"; TO="$4"; OUT="$5"
DUR=$(python3 -c "print(round($TO-$SS,3))")
LBL="fontsize=30:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8:x=16:y=16"
ffmpeg -hide_banner -loglevel error -y -ss "$SS" -i "$SRC" -i "$GRADED" -t "$DUR" -filter_complex \
  "[0:v]scale=960:540:flags=lanczos,drawtext=text='AVANT (source)':$LBL[a];\
   [1:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='APRES (look v3, 4K reduit)':$LBL[b];\
   [a][b]hstack,pad=1920:1080:0:270:black[v]" \
  -map "[v]" -map 0:a:0 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k \
  -movflags +faststart "$OUT"
