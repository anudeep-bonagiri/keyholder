#!/usr/bin/env bash
# Full demo build: render frames sized to the narration, encode with exact timing,
# lay the voiceover on the beat marks, join the intro clip. Usage:
#   demo/video/build.sh <intro.mp4> <voiceover dir with 01..10.mp3 + narr.json> <work dir> <out.mp4>
set -euo pipefail
INTRO="$1"; VO="$2"; WK="$3"; OUT="$4"; HERE="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$WK/frames" "$WK/clips"; mkdir -p "$WK/frames" "$WK/clips"
NARR="$VO/narr.json" PAD=0.6 python3 "$HERE/render.py" "$WK/frames" "$WK/walk-planned.mp4" >/dev/null
python3 - "$WK" "$VO" <<'PY'
import re, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
WK, VO = sys.argv[1], sys.argv[2]
pairs = re.findall(r"file '([^']+)'\nduration ([0-9.]+)", open(f"{WK}/frames/list.txt").read())
states = [(p, float(d)) for p, d in pairs]; frames = [max(1, round(d * 30)) for _, d in states]
def enc(i):
    out = f"{WK}/clips/c{i:03d}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-framerate","30","-i",states[i][0],"-frames:v",str(frames[i]),
                    "-c:v","libx264","-preset","ultrafast","-tune","stillimage","-crf","18","-pix_fmt","yuv420p","-g","30",out],check=True)
    return out
with ThreadPoolExecutor(8) as ex: outs = list(ex.map(enc, range(len(states))))
open(f"{WK}/clips/list.txt","w").write("".join(f"file '{o}'\n" for o in outs))
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{WK}/clips/list.txt","-c","copy","-movflags","+faststart",f"{WK}/walk-exact.mp4"],check=True)
planned = json.load(open(f"{WK}/frames/marks.json")); cp=[0.0]; ce=[0.0]
for (p,d),n in zip(states,frames): cp.append(cp[-1]+d); ce.append(ce[-1]+n/30)
marks = {name: round(ce[min(range(len(cp)), key=lambda i: abs(cp[i]-t))],3) for name,t in planned}
ins=[]; fl=[]; names=[]
for i in range(1,11):
    n=f"{i:02d}"; ms=int(round(marks[n]*1000)); ins+=["-i",f"{VO}/{n}.mp3"]
    fl.append(f"[{i-1}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[a{i}]"); names.append(f"[a{i}]")
fl.append("".join(names)+f"amix=inputs=10:normalize=0:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad=whole_dur={marks['end']}[out]")
subprocess.run(["ffmpeg","-y","-loglevel","error",*ins,"-filter_complex",";".join(fl),"-map","[out]","-c:a","aac","-b:a","160k",f"{WK}/narr.m4a"],check=True)
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"{WK}/walk-exact.mp4","-i",f"{WK}/narr.m4a","-map","0:v","-map","1:a","-c","copy","-shortest","-movflags","+faststart",f"{WK}/walk-voiced.mp4"],check=True)
print("walkthrough", round(sum(frames)/30,2), "s; marks", marks)
PY
"$HERE/../join.sh" "$INTRO" "$WK/walk-voiced.mp4" "$OUT" | grep -E "duration"
