#!/usr/bin/env bash
# BAD LIFE — etape 1 : analyse de la source (decoupage en plans + statistiques signal par image).
# Usage : analyze.sh SOURCE DOSSIER_SORTIE
# Produit : cuts.txt, scenes.txt, stats.txt, shots.json (puis tools/build_shotlist.py -> data/shots.csv)
set -euo pipefail
SRC="$1"; OUT="$2"; mkdir -p "$OUT"
# Detection de coupe (score de scene > 0.25), sur une version reduite pour la vitesse
ffmpeg -hide_banner -nostats -i "$SRC" -an -vf "scale=480:-2,select='gt(scene,0.25)',metadata=print:file=$OUT/scenes.txt" -f null - 2>/dev/null
grep -oE "pts_time:[0-9.]+" "$OUT/scenes.txt" | cut -d: -f2 > "$OUT/cuts.txt"
# Statistiques signalstats (luma YMIN/YLOW/YAVG/YHIGH/YMAX, saturation, teinte) par image
ffmpeg -hide_banner -nostats -i "$SRC" -an -vf "scale=480:-2,signalstats,metadata=print:file=$OUT/stats.txt" -f null - 2>/dev/null
python3 -I "$(dirname "$0")/shots.py" "$OUT"
