#!/usr/bin/env python3
"""Export constant-fps MP4, decode all frames, inspect streams and extract PNGs."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import shutil
import subprocess
import sys


def run(args):
    p=subprocess.run(args,capture_output=True,text=True,encoding="utf-8",errors="replace")
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or f"Command failed: {args[0]}")
    return p


def export_verify(source,output,fps=30,keep_audio=False,sample_times=None,overwrite=False):
    source,output=Path(source).resolve(),Path(output).resolve()
    if not source.is_file():
        raise ValueError(f"Input does not exist: {source}")
    if source==output or output.suffix.lower()!=".mp4":
        raise ValueError("Use a different output file with the .mp4 extension.")
    if fps<=0 or fps>240:
        raise ValueError("FPS must be in (0, 240].")
    if output.exists() and not overwrite:
        raise ValueError("Output exists. Choose a new version or use --overwrite.")
    for exe in ("ffmpeg","ffprobe"):
        if not shutil.which(exe):
            raise RuntimeError(f"{exe} is missing from PATH.")
    before=json.loads(run(["ffprobe","-v","error","-show_format","-of","json",str(source)]).stdout)
    duration=float(before["format"]["duration"])
    times=list(sample_times) if sample_times is not None else [duration*.1,duration*.5,duration*.9]
    if any(t<0 or t>=duration for t in times):
        raise ValueError(f"Sample times must lie in [0, {duration:.3f}).")
    output.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-v","error","-y" if overwrite else "-n","-i",str(source),"-map","0:v:0",
         "-vf",f"fps={fps}","-fps_mode","cfr","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p"]
    cmd+=(["-map","0:a?","-c:a","aac","-b:a","160k"] if keep_audio else ["-an"])
    run(cmd+["-movflags","+faststart",str(output)])
    probe=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(output)]).stdout)
    video=next(s for s in probe["streams"] if s["codec_type"]=="video")
    audio=any(s["codec_type"]=="audio" for s in probe["streams"])
    if not keep_audio and audio:
        raise RuntimeError("Silent export contains an audio stream.")
    if abs(float(Fraction(video["avg_frame_rate"]))-fps)>.001:
        raise RuntimeError("Exported FPS differs from the request.")
    decoded=run(["ffmpeg","-v","error","-i",str(output),"-f","null","-"])
    if decoded.stderr.strip():
        raise RuntimeError(f"Full-file decoding reported errors: {decoded.stderr.strip()}")
    qa=output.parent/(output.stem+"_qa")
    qa.mkdir(exist_ok=True)
    frames=[]
    for i,t in enumerate(times,1):
        frame=qa/f"frame_{i:02d}_{t:.3f}s.png"
        run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",str(output),"-frames:v","1",str(frame)])
        frames.append(dict(time=t,path=str(frame)))
    report=dict(output=str(output),duration=float(probe["format"]["duration"]),width=video["width"],
                height=video["height"],fps=fps,audio=audio,codec=video["codec_name"],
                full_decode="passed",frames=frames,probe=probe)
    output.with_suffix(".qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return {k:v for k,v in report.items() if k!="probe"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--fps",type=float,default=30)
    p.add_argument("--keep-audio",action="store_true")
    p.add_argument("--sample-times",nargs="+",type=float)
    p.add_argument("--overwrite",action="store_true")
    a=p.parse_args()
    try:
        result=export_verify(a.input,a.output,a.fps,a.keep_audio,a.sample_times,a.overwrite)
    except (RuntimeError,ValueError,OSError,KeyError,StopIteration) as e:
        print(f"Export verification failed: {e}",file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
