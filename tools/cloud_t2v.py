#!/usr/bin/env python3
"""cloud_t2v — ek scene ka asli AI video (text-to-video) cloud CPU par.

Slideshow nahi: AnimateDiff (SD1.5 motion adapter) har frame generate karta hai, phir
clip ko 1080x1920 tak upscale + 24 fps interpolate karke deliver karta hai.

Kaam:  python3 tools/cloud_t2v.py <job.json> --scene s01 --out <dir>
Job me global settings aur scenes[] hote hain (cloud/t2v_jobs/<id>.json).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

BASE_MODEL = "Lykon/dreamshaper-8"
MOTION_ADAPTER = "guoyww/animatediff-motion-adapter-v1-5-2"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def generate(scene: dict, job: dict, work: pathlib.Path) -> pathlib.Path:
    import torch
    from diffusers import AnimateDiffPipeline, EulerDiscreteScheduler, MotionAdapter
    from diffusers.utils import export_to_video

    threads = int(job.get("threads", 4))
    torch.set_num_threads(threads)
    frames = int(scene.get("frames", job.get("frames", 24)))
    width = int(scene.get("width", job.get("width", 432)))
    height = int(scene.get("height", job.get("height", 768)))
    steps = int(scene.get("steps", job.get("steps", 12)))

    log(f"{scene['id']}: {width}x{height} {frames}f {steps} steps on {threads} threads")
    adapter = MotionAdapter.from_pretrained(MOTION_ADAPTER, torch_dtype=torch.float32)
    pipe = AnimateDiffPipeline.from_pretrained(BASE_MODEL, motion_adapter=adapter,
                                               torch_dtype=torch.float32)
    pipe.scheduler = EulerDiscreteScheduler.from_config(
        pipe.scheduler.config, beta_schedule="linear", timestep_spacing="trailing")
    pipe.set_progress_bar_config(disable=True)

    started = time.time()
    result = pipe(
        prompt=f"{scene['prompt']}, {job.get('style', '')}".strip(", "),
        negative_prompt=job.get("negative", "blurry, low quality, watermark, text, static"),
        num_frames=frames, guidance_scale=float(job.get("guidance", 7.5)),
        num_inference_steps=steps, width=width, height=height,
        generator=torch.Generator("cpu").manual_seed(int(scene.get("seed", 7))),
    ).frames[0]
    log(f"{scene['id']}: {len(result)} frames in {time.time() - started:.0f}s")

    raw = work / "raw.mp4"
    export_to_video(result, str(raw), fps=int(job.get("raw_fps", 8)))
    return raw


def finish(raw: pathlib.Path, scene: dict, job: dict, out: pathlib.Path, ffmpeg: str) -> pathlib.Path:
    """Clip ko delivery look: 1080x1920, film grade, grain, 24 fps interpolation."""
    fps = int(job.get("fps", 24))
    seconds = float(scene.get("seconds", 3.0))
    graph = (
        # 24 fps ke liye motion interpolation (judder na ho)
        f"[0:v]minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,"
        f"scale=1080:-2:flags=lanczos,"
        f"eq=contrast=1.06:gamma=0.99:saturation=1.04,"
        f"colorbalance=rs=-0.012:bs=0.01:rh=0.022:bh=-0.016,"
        f"noise=alls=6:allf=t+u,vignette=PI/5.6,"
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"trim=duration={seconds},setpts=PTS-STARTPTS,"
        f"fade=t=in:st=0:d=0.25,format=yuv420p[v]"
    )
    cmd = [ffmpeg, "-y", "-i", str(raw), "-filter_complex", graph, "-map", "[v]",
           "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-tune", "film",
           "-pix_fmt", "yuv420p", "-r", str(fps), str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("finish fail: " + " | ".join(proc.stderr.strip().splitlines()[-3:]))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cloud_t2v")
    parser.add_argument("job")
    parser.add_argument("--scene", help="sirf ek scene (matrix job)")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    job = json.loads(pathlib.Path(args.job).read_text())
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = os.environ.get("FFMPEG", "ffmpeg")

    scenes = [s for s in job["scenes"] if args.scene in (None, s["id"])]
    if not scenes:
        print("scene nahi mila:", args.scene)
        return 1

    for scene in scenes:
        work = out_dir / f"work_{scene['id']}"
        work.mkdir(exist_ok=True)
        clip = out_dir / f"{scene['id']}.mp4"
        if clip.exists() and clip.stat().st_size > 50000:
            log(f"{scene['id']}: already present, skip")
            continue
        raw = generate(scene, job, work)
        finish(raw, scene, job, clip, ffmpeg)
        log(f"{scene['id']}: {clip.name} {clip.stat().st_size / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
