#!/usr/bin/env python3
"""cloud_ai_clip — cloud (GitHub runner, CPU) par chhota AI video clip banao.

Sandbox se HuggingFace/Colab band hai; GitHub runner ke paas poora internet hai, is liye
model wahin download hota hai aur clip `cloud-ai-artifacts` branch se wapas aata hai.

Model: Stable Diffusion 1.5 + AnimateDiff (motion adapter) — CPU par chalta hai, koi GPU
account nahi, koi Colab tap nahi. 14 frames @ 384x640, 12 steps.

Usage: python3 tools/cloud_ai_clip.py cloud/ai_jobs/ai-clip-01.json --out cloud_out/ai-clip-01
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cloud_ai_clip")
    parser.add_argument("job", help="cloud/ai_jobs/<id>.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    job = json.loads(pathlib.Path(args.job).read_text())
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    import torch
    from diffusers import AnimateDiffPipeline, EulerDiscreteScheduler, MotionAdapter
    from diffusers.utils import export_to_video

    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "4")))
    print("torch", torch.__version__, "threads", torch.get_num_threads())

    adapter = MotionAdapter.from_pretrained(MOTION_ADAPTER, torch_dtype=torch.float32)
    pipe = AnimateDiffPipeline.from_pretrained(BASE_MODEL, motion_adapter=adapter,
                                               torch_dtype=torch.float32)
    pipe.scheduler = EulerDiscreteScheduler.from_config(
        pipe.scheduler.config, beta_schedule="linear", timestep_spacing="trailing")
    pipe.set_progress_bar_config(disable=False)
    print("pipe ready in", round(time.time() - started, 1), "s")

    frames = int(job.get("frames", 14))
    width = int(job.get("width", 384))
    height = int(job.get("height", 640))
    steps = int(job.get("steps", 12))
    t0 = time.time()
    produced = pipe(
        prompt=job["prompt"],
        negative_prompt=job.get("negative", "blurry, low quality, watermark, text"),
        num_frames=frames,
        guidance_scale=float(job.get("guidance", 7.5)),
        num_inference_steps=steps,
        width=width,
        height=height,
        generator=torch.Generator("cpu").manual_seed(int(job.get("seed", 7))),
    ).frames[0]
    print(f"generated {len(produced)} frames in {time.time() - t0:.0f}s")

    raw = out / "raw.mp4"
    export_to_video(produced, str(raw), fps=int(job.get("fps", 8)))

    clip = out / (job.get("id", "ai-clip") + ".mp4")
    # vertical delivery: 1080x1920, blurred bed par clip, thoda grade + grain
    graph = (
        f"[0:v]split=2[b][f];"
        f"[b]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=40,eq=brightness=-0.06:saturation=0.7[bg];"
        f"[f]scale=1080:-2:flags=lanczos,eq=contrast=1.06:saturation=0.9,"
        f"noise=alls=6:allf=t[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    proc = subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-filter_complex", graph,
                           "-map", "[v]", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                           "-pix_fmt", "yuv420p", str(clip)], capture_output=True, text=True)
    if proc.returncode != 0:
        print("ffmpeg fail:", " | ".join(proc.stderr.strip().splitlines()[-3:]))
        return 1

    meta = {"job": job.get("id"), "model": f"{BASE_MODEL} + {MOTION_ADAPTER}",
            "frames": frames, "steps": steps, "size": [width, height],
            "prompt": job["prompt"], "seed": job.get("seed", 7),
            "clip": clip.name, "bytes": clip.stat().st_size,
            "seconds": round(time.time() - started, 1), "device": "cpu"}
    (out / "ai_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
