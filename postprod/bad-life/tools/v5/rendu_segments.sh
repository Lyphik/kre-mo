#!/usr/bin/env bash
# BAD LIFE V5.1 — rendu du master par segments, reprenable apres interruption du conteneur.
#   - chaque segment SEGn (tools/v5/master_segments.json) est rendu par composite_v5.py ; au-dela du
#     premier, PREROLL=1 rejoue l'etat inter-plans du rendu monolithique (equivalence verifiee, doc 11 §11.4) ;
#   - un segment termine (fichier OK) n'est pas refait ;
#   - assemblage : concatenation des flux video SANS reencodage + flux audio ORIGINAL de la source copie
#     tel quel (aucun reencodage audio).
# Usage : rendu_segments.sh SOURCE PROJET SCRATCH_MASTER PYTHON
set -euo pipefail
SRC=$1; P=$2; M=$3; PY=$4
SEGS="SEG1 SEG2 SEG3 SEG4"
for s in $SEGS; do
  out=$M/seg/$s
  if [ -f "$out/OK" ]; then echo "$s deja rendu"; continue; fi
  rm -rf "$out"; mkdir -p "$out"
  pre=1; [ "$s" = SEG1 ] && pre=0
  echo "$s debut $(date -u +%H:%M:%S)"
  PREROLL=$pre STILL_EVERY=500 "$PY" "$P/tools/v5/composite_v5.py" "$SRC" "$P/data/v5/plans.csv" "$P/tools/v5/v5_1_final_config.json" \
      "$P/data/v5/musique.json" "$M/../v5/matte" "$M/depth" "$P/luts" "$P/tools/v5/master_segments.json" "$s" "$out" < /dev/null
  touch "$out/OK"; echo "$s fin $(date -u +%H:%M:%S)"
done
F=$M/final; mkdir -p "$F"
# Les segments contiennent une piste AAC reencodee (avec delai d'amorcage de -21 ms) : si on les concatene
# tels quels, le demultiplexeur concat cale le depart sur cet audio et DECALE la video de +21 ms (1 image).
# On extrait donc d'abord la seule piste video de chaque segment (copie sans reencodage).
for v in COMPLET ETALONNAGE_SEUL; do
  : > "$F/liste_$v.txt"
  for s in $SEGS; do
    ffmpeg -nostdin -v error -y -i "$M/seg/$s/${s}_V5_1_$v.mp4" -map 0:v:0 -c copy "$M/seg/$s/${s}_V5_1_${v}_video.mp4"
    echo "file '$M/seg/$s/${s}_V5_1_${v}_video.mp4'" >> "$F/liste_$v.txt"
  done
  ffmpeg -nostdin -v error -y -f concat -safe 0 -i "$F/liste_$v.txt" -i "$SRC" -map 0:v:0 -map 1:a:0 -c copy \
         -tag:v hvc1 -movflags +faststart "$F/BADLIFE_V5_1_MASTER_4K_$v.mp4"
done
# QC : tables par image recollees
head -1 "$M/seg/SEG1/qc_effets.csv" > "$F/qc_effets.csv"; head -1 "$M/seg/SEG1/qc_artistes.csv" > "$F/qc_artistes.csv"
for s in $SEGS; do tail -n +2 "$M/seg/$s/qc_effets.csv" >> "$F/qc_effets.csv"; tail -n +2 "$M/seg/$s/qc_artistes.csv" >> "$F/qc_artistes.csv"; done
echo ASSEMBLAGE_OK
