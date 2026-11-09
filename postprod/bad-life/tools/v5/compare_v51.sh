#!/usr/bin/env bash
# BAD LIFE V5.1 — comparatif 4 vues (1080p H.264) : 1 SOURCE | 2 ETALONNAGE SEUL | 3 V5 PRECEDENTE | 4 V5.1 ALLEGEE
# + compilation des 5 extraits. Les extraits V5.1 « seuls » (sans grille) sont les fichiers 4K du rendu.
# Usage : compare_v51.sh SOURCE EXTRAITS.json RENDU_V5_DIR RENDU_V51_DIR SORTIE_DIR
set -euo pipefail
SRC="$1"; EXT="$2"; R5="$3"; R51="$4"; OUT="$5"; mkdir -p "$OUT"
L="fontsize=24:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=6:x=12:y=12"
LIST="$OUT/liste.txt"; : > "$LIST"
python3 -c "import json,sys; [print(e['id'], e['debut_s'], e['fin_s']) for e in json.load(open(sys.argv[1]))['extraits']]" "$EXT" |
while read -r id a b; do
  d=$(python3 -c "print(round($b-$a,3))"); titre=$(echo "$id" | sed 's/_/ /g')
  ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$a" -i "$SRC" -i "$R51/$id/${id}_V5_1_ETALONNAGE_SEUL.mp4" -i "$R5/$id/${id}_V5_COMPLET.mp4" -i "$R51/$id/${id}_V5_1_COMPLET.mp4" -t "$d" -filter_complex \
   "[0:v]scale=960:540:flags=lanczos,drawtext=text='1 SOURCE  -  $titre':$L[s];\
    [1:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='2 ETALONNAGE SEUL':$L[e];\
    [2:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='3 V5 PRECEDENTE':$L[c];\
    [3:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='4 V5.1 ALLEGEE':$L[m];\
    [s][e]hstack[t];[c][m]hstack[u];[t][u]vstack,format=yuv420p[v]" \
   -map "[v]" -map 0:a:0 -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT/BADLIFE_V5_1_COMPARATIF_${id}.mp4"
  echo "file 'BADLIFE_V5_1_COMPARATIF_${id}.mp4'" >> "$LIST"
done
ffmpeg -nostdin -hide_banner -loglevel error -y -f concat -safe 0 -i "$LIST" -c copy -movflags +faststart "$OUT/BADLIFE_V5_1_COMPARATIF_5_EXTRAITS.mp4"
echo "comparatifs ecrits dans $OUT"
