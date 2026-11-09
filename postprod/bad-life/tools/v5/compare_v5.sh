#!/usr/bin/env bash
# BAD LIFE V5 — comparatif 4 vues (1080p H.264) par extrait + compilation des extraits.
#   haut : SOURCE | V5 ETALONNAGE SEUL     bas : V5 COMPLET | ZONE PROTEGEE (artistes = source)
# Usage : compare_v5.sh SOURCE EXTRAITS.json RENDU_DIR SORTIE_DIR
set -euo pipefail
SRC="$1"; EXT="$2"; RD="$3"; OUT="$4"; mkdir -p "$OUT"
L="fontsize=24:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=6:x=12:y=12"
LIST="$OUT/liste.txt"; : > "$LIST"
python3 -c "import json,sys; [print(e['id'], e['debut_s'], e['fin_s']) for e in json.load(open(sys.argv[1]))['extraits']]" "$EXT" |
while read -r id a b; do
  d=$(python3 -c "print(round($b-$a,3))")
  titre=$(echo "$id" | sed 's/_/ /g')
  ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$a" -i "$SRC" -i "$RD/$id/${id}_V5_ETALONNAGE_SEUL.mp4" -i "$RD/$id/${id}_V5_COMPLET.mp4" -i "$RD/$id/${id}_MASQUE.mp4" -t "$d" -filter_complex \
   "[0:v]scale=960:540:flags=lanczos,drawtext=text='SOURCE  -  $titre':$L[s];\
    [1:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='V5 ETALONNAGE SEUL':$L[e];\
    [2:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='V5 COMPLET':$L[c];\
    [3:v]scale=960:540:flags=lanczos,format=yuv420p,drawtext=text='ZONE PROTEGEE (vert) = pixels source':$L[m];\
    [s][e]hstack[t];[c][m]hstack[u];[t][u]vstack,format=yuv420p[v]" \
   -map "[v]" -map 0:a:0 -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT/BADLIFE_V5_COMPARATIF_${id}.mp4"
  echo "file 'BADLIFE_V5_COMPARATIF_${id}.mp4'" >> "$LIST"
done
ffmpeg -nostdin -hide_banner -loglevel error -y -f concat -safe 0 -i "$LIST" -c copy -movflags +faststart "$OUT/BADLIFE_V5_COMPARATIF_5_EXTRAITS.mp4"
echo "comparatifs ecrits dans $OUT"
