#!/usr/bin/env bash
# Assemble le prototype : images Cycles + mixage audio -> MP4 (16:9 + vertical sous-titré)
set -euo pipefail
FRAMES_H="$1"; FRAMES_V="$2"; OUT="$3"
D="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
ffmpeg -y -loglevel error -framerate 25 -i "$FRAMES_H/f%04d.png" -i "$D/proto_mix.wav" \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -x264-params aq-mode=3 -c:a aac -b:a 192k -shortest \
  -movflags +faststart "$OUT/973culture_proto10s_3d_16x9_720p.mp4"
ffmpeg -y -loglevel error -framerate 25 -i "$FRAMES_V/f%04d.png" -i "$D/proto_mix.wav" \
  -vf "ass=$D/proto10s_vertical.ass" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -x264-params aq-mode=3 \
  -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/973culture_proto10s_3d_vertical_720x1280.mp4"
cp "$D/proto10s_fr.srt" "$OUT/973culture_proto10s_3d_16x9_720p.srt"
echo "OK $OUT"
