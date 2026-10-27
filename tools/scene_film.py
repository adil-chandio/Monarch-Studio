#!/usr/bin/env python3
"""scene_film — AI scenes se poori film: 2.5D parallax, captions, voice, sound design.

Slideshow nahi: har scene ke depth map se subject aur background alag ho kar **mukhtalif
speed** par chalte hain (parallax), upar se camera push/pan, film grade, grain, handheld
shake. Voice lines scene ke start par baithti hain, neeche cinematic bed + loudnorm.

Spec (JSON):
{
  "id": "personality-36", "title": "Powerful Personality",
  "size": [1080, 1920], "fps": 24,
  "dir": "scenes/",            # images s01.png, depth s01_depth.png, voice s01.wav
  "scenes": [{"id": "s01", "seconds": 3.0, "move": "push",
              "caption": "...", "kicker": "01 · SUNNA"}],
  "audio": {"drone": 0.5, "pad": 0.35, "pulse": 0.3, "riser": true}
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import reel_render as base  # noqa: E402  (caption typography + probe + md5)

RenderError = base.RenderError
MOVES = base.MOVES


def make_mask(depth_path: pathlib.Path, out: pathlib.Path, spec: dict) -> pathlib.Path:
    """Depth map se subject ka feathered alpha mask banao (parallax ke liye)."""
    import numpy as np
    from PIL import Image, ImageFilter

    depth = Image.open(depth_path).convert("L")
    width, height = spec["size"]
    depth = depth.resize((width, height), Image.LANCZOS)
    arr = np.asarray(depth, dtype=np.float32) / 255.0
    # closer = brighter in Depth-Anything v2; subject = top quantile
    cut = float(spec.get("subject_quantile", 0.55))
    threshold = float(np.quantile(arr, cut))
    mask = (arr >= threshold).astype(np.float32)
    # edges ko feather karo warna cut-out jaisa lage
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(int(spec.get("mask_feather", 14))))
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(8))
    mask_img.save(out)
    return out


def scene_graph(scene: dict, spec: dict, index: int, caption_png: pathlib.Path | None,
                mask_png: pathlib.Path | None) -> str:
    width, height = spec["size"]
    fps = int(spec.get("fps", 24))
    seconds = float(scene["seconds"])
    frames = max(int(round(seconds * fps)), 2)
    move = scene.get("move", "push")
    if move not in MOVES:
        raise RenderError(f"scene {index}: move '{move}' samajh nahi aaya")
    zoom, xpos, ypos = base._zoom_expr(move, frames)
    grain = int(spec.get("grain", 8))
    fade = float(spec.get("fade", 0.3))
    far_zoom = float(spec.get("parallax_far", 1.16))
    near_zoom = float(spec.get("parallax_near", 1.28))

    parts = [
        "[0:v]split=2[fars][nears]",
        # background: dheema, thoda blur + dark (depth ka ehsaas)
        (f"[fars]scale=iw*{far_zoom}:ih*{far_zoom}:flags=lanczos,"
         f"zoompan=z='1.02+0.04*on/{frames}':d={frames}:"
         f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps},"
         f"gblur=sigma={int(spec.get('far_blur', 2))},"
         f"eq=brightness=-0.015:saturation=0.9,setsar=1[far]"),
    ]
    if mask_png is not None:
        # foreground subject: tez camera move, mask se alag
        parts += [
            (f"[nears]scale=iw*{near_zoom}:ih*{near_zoom}:flags=lanczos,"
             f"zoompan=z='{zoom}':d={frames}:x='{xpos}':y='{ypos}':"
             f"s={width}x{height}:fps={fps},setsar=1[near]"),
            f"[1:v]scale={width}:{height},format=gray,"
            f"loop=loop={frames - 1}:size=1:start=0,fps={fps}[alpha]",
            "[near][alpha]alphamerge[near_a]",
            "[far][near_a]overlay=x=0:y=0:shortest=1[layered]",
        ]
        cap_index = 2
    else:
        parts.append(f"[nears]scale=iw*{near_zoom}:ih*{near_zoom}:flags=lanczos,"
                     f"zoompan=z='{zoom}':d={frames}:x='{xpos}':y='{ypos}':"
                     f"s={width}x{height}:fps={fps},setsar=1[full]")
        parts.append("[full]null[layered]")
        cap_index = 1

    # film grade + halation-lite + grain + vignette + handheld shake
    parts += [
        "[layered]eq=contrast=1.06:gamma=0.99:saturation=1.03,"
        "colorbalance=rs=-0.012:bs=0.01:rh=0.025:bh=-0.018[graded]",
        f"[graded]noise=alls={grain}:allf=t+u,vignette=PI/5.6[filmic]",
    ]
    tail = "[filmic]"
    if caption_png is not None:
        parts += [
            f"[{cap_index}:v]format=rgba,"
            f"fade=t=in:st=0:d={fade:.2f}:alpha=1,"
            f"fade=t=out:st={max(seconds - fade, 0):.2f}:d={fade:.2f}:alpha=1[cap]",
            f"{tail}[cap]overlay=x=0:y='-{int(spec.get('caption_drift', 4))}*t':shortest=1[capd]",
        ]
        tail = "[capd]"
    if spec.get("shake", True):
        parts.append(f"{tail}crop=w=iw-6:h=ih-6:x='3+2*sin(t*7.3)':y='3+2*cos(t*5.7)',"
                     f"scale={width}:{height}:flags=lanczos,setsar=1[shaken]")
        tail = "[shaken]"
    parts.append(f"{tail}fade=t=in:st=0:d={min(fade, 0.25):.2f},"
                 f"scale={width}:{height}:flags=lanczos,setsar=1,format=yuv420p[v]")
    return ";".join(parts)


def render_scene(scene: dict, spec: dict, index: int, image: pathlib.Path,
                 depth: pathlib.Path | None, work: pathlib.Path, ffmpeg: str) -> pathlib.Path:
    fps = int(spec.get("fps", 24))
    seconds = float(scene["seconds"])
    cap = (scene.get("caption") or "").strip()
    cap_png = base.make_caption_png(cap, spec, work / f"cap{index:02d}.png") if cap else None
    mask = make_mask(depth, work / f"mask{index:02d}.png", spec) if depth and depth.exists() else None
    graph = scene_graph(scene, spec, index, cap_png, mask)

    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", str(fps), "-t", f"{seconds:.3f}",
           "-i", str(image)]
    if mask is not None:
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{seconds:.3f}", "-i", str(mask)]
    if cap_png is not None:
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{seconds:.3f}", "-i", str(cap_png)]
    out = work / f"scene{index:02d}.mp4"
    cmd += ["-filter_complex", graph, "-map", "[v]",
            "-c:v", "libx264", "-crf", str(spec.get("crf", 19)),
            "-preset", str(spec.get("preset", "veryfast")), "-tune", "film",
            "-pix_fmt", "yuv420p", "-r", str(fps), str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " | ".join(proc.stderr.strip().splitlines()[-3:])
        raise RenderError(f"scene {index} render nahi hua: {tail}")
    return out


def join_scenes(parts: list[pathlib.Path], out: pathlib.Path, ffmpeg: str) -> pathlib.Path:
    listing = out.parent / "scenes.txt"
    listing.write_text("".join(f"file {p.name}\n" for p in parts))
    proc = subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", listing.name,
                           "-c", "copy", out.name],
                          capture_output=True, text=True, cwd=str(out.parent))
    if proc.returncode != 0:
        raise RenderError("scenes jodne me masla: "
                          + " | ".join(proc.stderr.strip().splitlines()[-2:]))
    return out


def sound_bed(spec: dict, scenes: list[dict], voice_files: dict, duration: float,
              out: pathlib.Path, ffmpeg: str) -> pathlib.Path:
    """Cinematic bed + scene-wise voice, phir loudnorm."""
    cfg = spec.get("audio") or {}
    rate = 48000
    layers, mixin = [], []

    if cfg.get("drone", 0.5):
        gain = float(cfg.get("drone", 0.5))
        layers.append(f"sine=frequency=55:duration={duration:.3f}:sample_rate={rate}[d1]")
        layers.append(f"sine=frequency=110:duration={duration:.3f}:sample_rate={rate}[d2]")
        layers.append(f"[d1][d2]amix=inputs=2:normalize=0,tremolo=f=0.12:d=0.3,"
                      f"pan=stereo|c0=c0|c1=c0,volume={gain:.3f}[drone]")
        mixin.append("[drone]")

    if cfg.get("pad", 0.35):
        gain = float(cfg.get("pad", 0.35))
        # A minor pad: 220, 261.6, 329.6 — halka, voice ke neeche
        layers.append(f"sine=frequency=220:duration={duration:.3f}:sample_rate={rate}[p1]")
        layers.append(f"sine=frequency=261.63:duration={duration:.3f}:sample_rate={rate}[p2]")
        layers.append(f"sine=frequency=329.63:duration={duration:.3f}:sample_rate={rate}[p3]")
        layers.append("[p1][p2][p3]amix=inputs=3:normalize=0,"
                      "tremolo=f=0.18:d=0.5,lowpass=f=1800,"
                      f"pan=stereo|c0=c0|c1=c0,volume={gain:.3f}[pad]")
        mixin.append("[pad]")

    if cfg.get("hiss", 0.08):
        gain = float(cfg.get("hiss", 0.08))
        layers.append(f"anoisesrc=color=white:duration={duration:.3f}:sample_rate={rate}:"
                      f"amplitude=0.05,highpass=f=7000,pan=stereo|c0=c0|c1=c0,"
                      f"volume={gain:.3f}[hiss]")
        mixin.append("[hiss]")

    if cfg.get("pulse", 0.3):
        gain = float(cfg.get("pulse", 0.3))
        layers.append(f"aevalsrc='0.5*sin(2*PI*44*t)*exp(-7*mod(t\\,1.5))':s={rate}:"
                      f"d={duration:.3f},pan=stereo|c0=c0|c1=c0,volume={gain:.3f}[pulse]")
        mixin.append("[pulse]")

    if cfg.get("riser", True):
        start = max(duration - 2.4, 0)
        layers.append(f"anoisesrc=color=white:duration=2.4:sample_rate={rate}:amplitude=0.1,"
                      f"highpass=f=600,lowpass=f=5200,afade=t=in:st=0:d=2.0,"
                      f"pan=stereo|c0=c0|c1=c0,volume=0.5,"
                      f"adelay={int(start * 1000)}|{int(start * 1000)}[riser]")
        mixin.append("[riser]")

    voice_index = {}
    for order, scene in enumerate(scenes):
        wav = voice_files.get(scene["id"])
        if not wav or not pathlib.Path(wav).exists():
            continue
        voice_index[len(voice_index)] = pathlib.Path(wav)
        at = int(round(sum(float(s["seconds"]) for s in scenes[:order]) * 1000))
        label = f"vo{order}"
        layers.append(f"[{len(voice_index) - 1}:a]aresample={rate},"
                      f"pan=stereo|c0=c0|c1=c0,volume=1.15,"
                      f"adelay={at}|{at}[{label}]")
        mixin.append(f"[{label}]")

    if not mixin:
        layers.append(f"anullsrc=channel_layout=stereo:sample_rate={rate}:"
                      f"duration={duration:.3f}[sil]")
        mixin.append("[sil]")
    layers.append("".join(mixin) + f"amix=inputs={len(mixin)}:normalize=0,"
                                   f"loudnorm=I=-16:TP=-1.5:LRA=11,"
                                   f"atrim=0:{duration:.3f},asetpts=N/SR/TB[aout]")

    cmd = [ffmpeg, "-y"]
    for wav in voice_index.values():
        cmd += ["-i", str(wav)]
    cmd += ["-f", "lavfi", "-i",
            f"anullsrc=channel_layout=stereo:sample_rate={rate}:duration=0.1",
            "-filter_complex", ";".join(layers), "-map", "[aout]",
            "-c:a", "aac", "-b:a", "192k", "-ar", str(rate), "-ac", "2", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError("sound bed nahi bana: "
                          + " | ".join(proc.stderr.strip().splitlines()[-3:]))
    return out


def render(spec_path: pathlib.Path, out: pathlib.Path, *, keep: pathlib.Path | None = None,
           ffmpeg: str | None = None) -> dict:
    ffmpeg = ffmpeg or base.which("ffmpeg")
    if not ffmpeg:
        raise RenderError("ffmpeg nahi mila")
    spec = json.loads(pathlib.Path(spec_path).read_text())
    spec_dir = pathlib.Path(spec_path).parent
    directory = pathlib.Path(spec.get("dir", "."))
    if not directory.is_absolute():
        directory = (spec_dir / directory).resolve()
    spec.setdefault("size", [1080, 1920])
    spec.setdefault("fps", 24)
    started = time.time()
    work = pathlib.Path(keep) if keep else pathlib.Path(tempfile.mkdtemp(prefix="film_"))
    work.mkdir(parents=True, exist_ok=True)
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    scenes, voice_files, log = spec["scenes"], {}, []
    parts = []
    for index, scene in enumerate(scenes, 1):
        image = directory / f"{scene['id']}.png"
        depth = directory / f"{scene['id']}_depth.png"
        if not image.exists():
            raise RenderError(f"scene {index}: image nahi mila ({image})")
        wav = directory / f"{scene['id']}.wav"
        if wav.exists():
            voice_files[scene["id"]] = wav
        parts.append(render_scene(scene, spec, index, image, depth, work, ffmpeg))
        log.append(f"scene {index}: {scene['id']} {scene['seconds']}s {scene.get('move', 'push')}"
                   + (" +depth" if depth.exists() else "") + (" +voice" if wav.exists() else ""))

    joined = join_scenes(parts, work / "joined.mp4", ffmpeg)
    duration = round(sum(float(s["seconds"]) for s in scenes), 3)
    bed = sound_bed(spec, scenes, voice_files, duration, work / "bed.m4a", ffmpeg)

    master = work / "master.mp4"
    proc = subprocess.run([ffmpeg, "-y", "-i", str(joined), "-i", str(bed),
                           "-c:v", "copy", "-c:a", "copy", "-shortest",
                           "-movflags", "+faststart", str(master)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError("master mux nahi hua: "
                          + " | ".join(proc.stderr.strip().splitlines()[-2:]))
    import shutil
    shutil.copyfile(master, out)

    info = base.probe(out, ffmpeg)
    receipt = {"tool": "scenefilm-1.0", "film": spec.get("id"), "title": spec.get("title"),
               "master": out.name, "info": info, "log": log,
               "scenes": len(scenes), "with_depth": sum(1 for s in scenes
                                                       if (directory / f"{s['id']}_depth.png").exists()),
               "with_voice": len(voice_files),
               "seconds_rendered": round(time.time() - started, 1),
               "engine": spec.get("engine", "ffmpeg-cpu + AI scenes")}
    out.with_name(out.stem + "_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scene_film", description=__doc__)
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
    print(f"FILM OK  {info['name']}  {info['bytes'] / 1e6:.2f} MB  "
          f"{info['width']}x{info['height']}  {info['duration']}s  "
          f"depth={receipt['with_depth']}/{receipt['scenes']} voice={receipt['with_voice']}  "
          f"md5={info['md5']}  ({receipt['seconds_rendered']}s)")
    for line in receipt["log"]:
        print("  ·", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
