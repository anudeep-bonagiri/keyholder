#!/usr/bin/env bash
# Joins an intro clip in front of the walkthrough render. Both are normalised to
# 1920x1080, 30 fps, yuv420p, H.264 + AAC 48 kHz stereo so the concat is seamless.
# Usage: demo/join.sh "<intro.mp4>" "<walkthrough.mp4>" "<out.mp4>"
set -euo pipefail
INTRO="$1"; WALK="$2"; OUT="$3"
T=$(mktemp -d)
norm() {  # $1 in, $2 out ; adds a silent track when the input has no audio
  if ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$1" | grep -q audio; then
    ffmpeg -v error -y -i "$1" -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p" \
      -c:v libx264 -preset veryfast -crf 18 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -ar 48000 -ac 2 -b:a 160k -movflags +faststart "$2"
  else
    ffmpeg -v error -y -i "$1" -f lavfi -i anullsrc=r=48000:cl=stereo -shortest \
      -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p" \
      -c:v libx264 -preset veryfast -crf 18 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -ar 48000 -ac 2 -b:a 160k -movflags +faststart "$2"
  fi
}
norm "$INTRO" "$T/a.mp4"; norm "$WALK" "$T/b.mp4"
printf "file '%s'\nfile '%s'\n" "$T/a.mp4" "$T/b.mp4" > "$T/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$T/list.txt" -c copy -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,width,height,r_frame_rate -of default=nw=1 "$OUT"
rm -rf "$T"
