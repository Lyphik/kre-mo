#!/usr/bin/env bash
# BAD LIFE — rendu etalonne + upscale 4K.
# Usage :
#   render.sh SOURCE SORTIE [DEBUT_S FIN_S]
# Variables : LUT (defaut luts/badlife_look_v3.cube), CRF (16), PRESET (medium),
#             VIGNETTE (angle rad, 0.40 ; 0 = desactive), BW_RANGES ("a-b,c-d" plans N&B a garder N&B)
# Sans DEBUT/FIN : clip complet, audio original copie bit a bit (-c:a copy), duree inchangee.
# Avec DEBUT/FIN : extrait de test, audio reencode (AAC 320k) car un extrait ne peut pas etre
#                  coupe a l'echantillon pres en copie de flux.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$1"; OUT="$2"; SS="${3:-}"; TO="${4:-}"
LUT="${LUT:-$HERE/luts/badlife_look_v3.cube}"
CRF="${CRF:-16}"; PRESET="${PRESET:-medium}"; VIGNETTE="${VIGNETTE:-0.40}"; BW_RANGES="${BW_RANGES:-}"

# 1) RGB 16 bits (conversion explicite BT.709 plage TV -> RGB plein)
VF="scale=in_color_matrix=bt709:in_range=tv,format=gbrp16le"
# 2) look (LUT 3D, interpolation tetraedrique)
VF="$VF,lut3d=file='$LUT':interp=tetrahedral"
# 3) plans N&B d'origine : on conserve le N&B (suppression de toute chroma introduite par la LUT)
if [[ -n "$BW_RANGES" ]]; then
  EXPR=""; IFS=',' read -ra R <<< "$BW_RANGES"
  for r in "${R[@]}"; do a="${r%-*}"; b="${r#*-}"; EXPR="${EXPR:+$EXPR+}between(t,$a,$b)"; done
  VF="$VF,hue=s=0:enable='$EXPR'"
fi
# 4) vignettage tres leger (optionnel)
if [[ "$VIGNETTE" != "0" ]]; then VF="$VF,vignette=angle=$VIGNETTE:mode=forward"; fi
# 5) upscale 4K Lanczos (interpolation : aucun detail invente), puis YUV 4:2:0 10 bits plage TV
VF="$VF,scale=3840:2160:flags=lanczos+accurate_rnd+full_chroma_int,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le"
VF="$VF,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"

X265="colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited:vbv-maxrate=80000:vbv-bufsize=160000:aq-mode=3"
if [[ -n "$SS" ]]; then
  # recherche cote entree : precise a l'image en transcodage, et la chaine de filtres ne traite
  # que l'extrait (les temps de BW_RANGES sont alors relatifs au debut de l'extrait)
  DUR=$(python3 -c "print(round($TO-$SS,3))")
  ffmpeg -hide_banner -y -ss "$SS" -i "$SRC" -t "$DUR" -map 0:v:0 -map 0:a:0 \
    -vf "$VF" -c:v libx265 -preset "$PRESET" -crf "$CRF" -profile:v main10 -tag:v hvc1 -x265-params "$X265" \
    -c:a aac -b:a 320k -movflags +faststart "$OUT"
else
  ffmpeg -hide_banner -y -i "$SRC" -map 0:v:0 -map 0:a:0 \
    -vf "$VF" -c:v libx265 -preset "$PRESET" -crf "$CRF" -profile:v main10 -tag:v hvc1 -x265-params "$X265" \
    -c:a copy -movflags +faststart "$OUT"
fi
