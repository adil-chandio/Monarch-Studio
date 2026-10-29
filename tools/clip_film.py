#!/usr/bin/env python3
"""clip_film — AI clips (video) se poori film: captions, voice, sound design, master.

Input clips asli generated frames hote hain (cloud T2V), is liye yahan koi camera-move
trick nahi: clip jaisi hai waisi chalti hai, bas grade/haptics/captions us par late hain.

Spec (JSON) — studio/films/<project>/film_clips.json:
{
  "id": "personality-t2v", "title": "...", "size": [1080, 1920], "fps": 24,
  "clips": "clips", "voice_dir": "voice",
  "scenes": [{"id": "s01", "clip": "s01.mp4", "seconds": 3.0,
              "caption": "...", "kicker": "...", "voice": "v01.wav"}],
  "audio": {...}
}
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import reel_render as base            # noqa: E402
import scene_film as film             # noqa: E402  (sound_bed reuse)

RenderError = base.RenderError


def clip_graph(scene: dict, spec: dict, seconds: float | None) -> str:
    """Clip ko delivery frame + grade par le aao (koi zoom trick nahi — frames asli hain)."""
    width, height = spec["size"]
    fps = int(spec.get("fps", 24))
    grain = int(spec.get("grain", 6))
    trim = f"trim=duration={seconds:.3f},setpts=PTS-STARTPTS," if seconds else ""
    # Wan ke clips bahut dark aate hain. Blunt brightness se blacks grey ho jate hain,
    # is liye shadow lift + gamma (0.4/0.46 curve) use karte hain: detail khulti hai,
    # black black rehta hai. Grain halka, vignette bhi halka.
    return (
        f"[0:v]{trim}"
        f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={width}:{height},setsar=1,fps={fps},"
        f"eq=contrast=1.04:gamma=1.10:brightness=0.04:saturation=1.05,"
        f"curves=all='0/0.0 0.35/0.42 0.7/0.76 1/1',"
        f"colorbalance=rs=-0.008:bs=0.01:rh=0.02:bh=-0.014,"
        f"noise=alls={grain}:allf=t,vignette=PI/8.0,"
        f"format=yuv420p[v]"
    )


def render_scene(scene: dict, spec: dict, index: int, clip: pathlib.Path,
                 work: pathlib.Path, ffmpeg: str) -> pathlib.Path:
    fps = int(spec.get("fps", 24))
    caption = (scene.get("caption") or "").strip()
    cap_png = base.make_caption_png(caption, spec, work / f"cap{index:02d}.png") if caption else None
    seconds = scene.get("seconds")
    graph = clip_graph(scene, spec, seconds)
    cmd = [ffmpeg, "-y", "-i", str(clip)]
    if cap_png is not None:
        total = float(seconds or 3.0)
        fade = float(spec.get("fade", 0.3))
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{total:.3f}", "-i", str(cap_png)]
        graph = (clip_graph(scene, spec, seconds).replace("format=yuv420p[v]", "setsar=1[graded]")
                 + f";[1:v]format=rgba,fade=t=in:st=0:d={fade:.2f}:alpha=1,"
                   f"fade=t=out:st={max(total - fade, 0):.2f}:d={fade:.2f}:alpha=1[cap]"
                   f";[graded][cap]overlay=x=0:y='-3*t':shortest=1,format=yuv420p[v]")
    out = work / f"scene{index:02d}.mp4"
    cmd += ["-filter_complex", graph, "-map", "[v]",
            "-c:v", "libx264", "-crf", str(spec.get("crf", 19)),
            "-preset", str(spec.get("preset", "medium")), "-tune", "film",
            "-pix_fmt", "yuv420p", "-r", str(fps), str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError(f"scene {index} render nahi hua: "
                          + " | ".join(proc.stderr.strip().splitlines()[-3:]))
    return out


def render(spec_path: pathlib.Path, out: pathlib.Path, *, keep: pathlib.Path | None = None,
           ffmpeg: str | None = None) -> dict:
    ffmpeg = ffmpeg or base.which("ffmpeg")
    if not ffmpeg:
        raise RenderError("ffmpeg nahi mila")
    spec = json.loads(pathlib.Path(spec_path).read_text())
    base_dir = pathlib.Path(spec_path).parent
    clips_dir = base_dir / spec.get("clips", "clips")
    voice_dir = base_dir / spec.get("voice_dir", "voice")
    spec.setdefault("size", [1080, 1920])
    spec.setdefault("fps", 24)
    started = time.time()
    work = pathlib.Path(keep) if keep else pathlib.Path(tempfile.mkdtemp(prefix="clipfilm_"))
    work.mkdir(parents=True, exist_ok=True)
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    parts, voice_files, log = [], {}, []
    missing = []
    for index, scene in enumerate(spec["scenes"], 1):
        clip = clips_dir / (scene.get("clip") or f"{scene['id']}.mp4")
        if not clip.exists():
            missing.append(scene["id"])
            continue
        parts.append(render_scene(scene, spec, index, clip, work, ffmpeg))
        wav_name = scene.get("voice")
        if wav_name:
            wav = voice_dir / wav_name
            if wav.exists():
                voice_files[scene["id"]] = wav
        log.append(f"scene {index}: {scene['id']} {scene.get('seconds')}s"
                   + (" +voice" if scene["id"] in voice_files else ""))
    if not parts:
        raise RenderError("koi clip nahi mila" + (f" ({', '.join(missing)})" if missing else ""))

    joined = film.join_scenes(parts, work / "joined.mp4", ffmpeg)
    duration = round(sum(float(s.get("seconds") or 3.0) for s in spec["scenes"]
                         if s["id"] not in missing), 3)
    bed = film.sound_bed(spec, [s for s in spec["scenes"] if s["id"] not in missing],
                         voice_files, duration, work / "bed.m4a", ffmpeg)

    master = work / "master.mp4"
    proc = subprocess.run([ffmpeg, "-y", "-i", str(joined), "-i", str(bed),
                           "-c:v", "copy", "-c:a", "copy", "-shortest",
                           "-movflags", "+faststart", str(master)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError("master mux nahi hua: "
                          + " | ".join(proc.stderr.strip().splitlines()[-2:]))
    shutil.copyfile(master, out)
    info = base.probe(out, ffmpeg)
    receipt = {"tool": "clipfilm-1.0", "film": spec.get("id"), "title": spec.get("title"),
               "master": out.name, "info": info, "log": log,
               "scenes": len(parts), "missing": missing, "with_voice": len(voice_files),
               "seconds_rendered": round(time.time() - started, 1),
               "engine": "cloud AnimateDiff clips + ffmpeg finish"}
    out.with_name(out.stem + "_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="clip_film")
    parser.add_argument("spec")
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep")
    args = parser.parse_args(argv)
    try:
        receipt = render(pathlib.Path(args.spec), pathlib.Path(args.out),
                         keep=pathlib.Path(args.keep) if args.keep else None)
    except RenderError as exc:
        print("FILM FAIL:", exc)
        return 1
    info = receipt["info"]
    print(f"FILM OK  {info['name']}  {info['bytes'] / 1e6:.2f} MB  {info['width']}x{info['height']}  "
          f"{info['duration']}s  scenes={receipt['scenes']} voice={receipt['with_voice']}  "
          f"md5={info['md5']}  ({receipt['seconds_rendered']}s)")
    for line in receipt["log"]:
        print("  ·", line)
    if receipt["missing"]:
        print("  missing clips:", ", ".join(receipt["missing"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
