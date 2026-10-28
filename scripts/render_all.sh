#!/usr/bin/env bash
# Render every scene and concatenate them into out/opc_mask_cd_oscillation.mp4.
#   scripts/render_all.sh            # final: 1920x1080 @ 30 fps
#   QUALITY=preview scripts/render_all.sh   # 854x480 @ 15 fps
# Requires data/ produced by scripts/generate_data.py (scenes verify array digests on load).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_BIN="${ENV_BIN:-/home/kyp/miniconda/envs/mano/bin}"
export PATH="$ENV_BIN:$PATH"
QUALITY="${QUALITY:-final}"
SCENES=(
  s1_measured:S1Measured
  s2_coupling:S2Coupling
  s3_iterations:S3Iterations
  s4_two_decays:S4TwoDecays
  s5_contrast:S5Contrast
  s6_held_fixed:S6HeldFixed
  s7_observations:S7Observations
  s8_action:S8Action
)
if [[ "$QUALITY" == final ]]; then
  ARGS=(-r 1920,1080 --frame_rate 30); SUB=1080p30; OUT="$ROOT/out/opc_mask_cd_oscillation.mp4"
else
  ARGS=(-ql); SUB=480p15; OUT="$ROOT/out/opc_mask_cd_oscillation_preview.mp4"
fi
cd "$ROOT/scenes"
LIST="$ROOT/out/concat_${SUB}.txt"
: > "$LIST"
for item in "${SCENES[@]}"; do
  file="${item%%:*}"; scene="${item##*:}"
  manim render "${ARGS[@]}" "$file.py" "$scene"
  clip="$ROOT/out/media/videos/$file/$SUB/$scene.mp4"
  [[ -s "$clip" ]] || { echo "missing clip $clip" >&2; exit 1; }
  echo "file '$clip'" >> "$LIST"
done
ffmpeg -v error -y -f concat -safe 0 -i "$LIST" -c copy "$OUT"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$OUT"
echo "wrote $OUT"
