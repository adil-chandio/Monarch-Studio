#!/usr/bin/env python3
"""cloud_t2v — ek scene ka asli AI video (text-to-video), cloud CPU par.

Slideshow nahi: har frame video model generate karta hai.

Backends:
  animatediff  SD1.5 + AnimateDiff motion adapter  (2023, sasta, fantasy look)
  wan          Wan 2.1 T2V-1.3B                     (2025, asli realism ke qareeb)
  ltx          LTX-Video 2B                        (2024/25, 24 fps native motion)

Kaam:  python3 tools/cloud_t2v.py <job.json> --scene s01 --out <dir>
Backend scene-level ""backend"" se aata hai, warna job-level, warna animatediff.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

DEFAULTS = {
    "animatediff": {
        "model": "Lykon/dreamshaper-8",
        "adapter": "guoyww/animatediff-motion-adapter-v1-5-2",
        "raw_fps": 8,
        "steps": 14,
        "guidance": 7.5,
    },
    "wan": {
        "model": "Wan-AI/Wan2.1-T2V-1.3B-Diffusers",
        "raw_fps": 16,
        "steps": 15,
        "guidance": 5.0,
    },
    "ltx": {
        "model": "Lightricks/LTX-Video",
        "raw_fps": 24,
        "steps": 20,
        "guidance": 3.0,
    },
    "wan22_i2v": {
        "model": "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
        "raw_fps": 24,
        "steps": 24,
        "guidance": 5.0,
    },
    "ltx_i2v": {
        "model": "Lightricks/LTX-Video",
        "raw_fps": 24,
        "steps": 24,
        "guidance": 3.0,
    },
}

NEGATIVE = {
    "animatediff": "blurry, low quality, watermark, text, static image, deformed face, extra limbs, cartoon, anime",
    "wan": "blurry, low quality, watermark, text, static, overexposed, cartoon, anime, deformed face, extra limbs",
    "ltx": "worst quality, inconsistent motion, blurry, jittery, distorted, watermark, text, cartoon",
    "wan22_i2v": "blurry, low quality, watermark, text, static, overexposed, deformed, extra limbs, "
                 "wobbly lines, melting, morphing",
    "ltx_i2v": "worst quality, inconsistent motion, blurry, jittery, distorted, watermark, text, "
               "melting, morphing",
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def pick(scene: dict, job: dict, key: str, default=None):
    if key in scene:
        return scene[key]
    if key in job:
        return job[key]
    return default


def export(frames, path: pathlib.Path, fps: int) -> pathlib.Path:
    from diffusers.utils import export_to_video

    export_to_video(frames, str(path), fps=fps)
    return path


# --------------------------------------------------------------------------- #
# backends
# --------------------------------------------------------------------------- #

def generate_animatediff(scene: dict, job: dict, work: pathlib.Path) -> pathlib.Path:
    import torch
    from diffusers import AnimateDiffPipeline, EulerDiscreteScheduler, MotionAdapter

    cfg = DEFAULTS["animatediff"]
    model = pick(scene, job, "model", cfg["model"])
    adapter_id = pick(scene, job, "adapter", cfg["adapter"])
    width = int(pick(scene, job, "width", 432))
    height = int(pick(scene, job, "height", 768))
    frames = int(pick(scene, job, "frames", 16))
    steps = int(pick(scene, job, "steps", cfg["steps"]))
    log(f"animatediff {model} + {adapter_id}: {width}x{height} {frames}f {steps} steps")

    adapter = MotionAdapter.from_pretrained(adapter_id, torch_dtype=torch.float32)
    pipe = AnimateDiffPipeline.from_pretrained(model, motion_adapter=adapter,
                                              torch_dtype=torch.float32)
    pipe.scheduler = EulerDiscreteScheduler.from_config(
        pipe.scheduler.config, beta_schedule="linear", timestep_spacing="trailing")
    pipe.set_progress_bar_config(disable=True)

    prompt = ", ".join(x for x in (scene["prompt"], job.get("style", "")) if x)
    t0 = time.time()
    result = pipe(
        prompt=prompt,
        negative_prompt=pick(scene, job, "negative", NEGATIVE["animatediff"]),
        num_frames=frames,
        guidance_scale=float(pick(scene, job, "guidance", cfg["guidance"])),
        num_inference_steps=steps,
        width=width,
        height=height,
        generator=torch.Generator("cpu").manual_seed(int(scene.get("seed", 7))),
    ).frames[0]
    log(f"{scene['id']}: {len(result)} frames in {time.time() - t0:.0f}s")
    return export(result, work / "raw.mp4", int(pick(scene, job, "raw_fps", cfg["raw_fps"])))


def _free_text_encoder(pipe) -> None:
    import gc
    import torch

    for attr in ("text_encoder", "text_encoder_2"):
        if getattr(pipe, attr, None) is not None:
            setattr(pipe, attr, None)
    gc.collect()
    try:
        torch.cuda.empty_cache()
    except Exception:
        pass


def generate_wan(scene: dict, job: dict, work: pathlib.Path) -> pathlib.Path:
    """Wan 2.1 T2V-1.3B — CPU par: encoder bf16 me chalao, phir free karke fp32 denoise."""
    import gc

    import torch
    from diffusers import WanPipeline

    cfg = DEFAULTS["wan"]
    model = pick(scene, job, "model", cfg["model"])
    width = int(pick(scene, job, "width", 480))
    height = int(pick(scene, job, "height", 832))
    frames = int(pick(scene, job, "frames", 33))
    steps = int(pick(scene, job, "steps", cfg["steps"]))
    if (frames - 1) % 4:
        frames = ((frames - 1) // 4) * 4 + 1
    width -= width % 16
    height -= height % 16
    log(f"wan {model}: {width}x{height} {frames}f {steps} steps")

    pipe = WanPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
    pipe.set_progress_bar_config(disable=True)
    pipe.vae.enable_slicing()

    prompt = ", ".join(x for x in (scene["prompt"], job.get("style", "")) if x)
    negative = pick(scene, job, "negative", NEGATIVE["wan"])
    t0 = time.time()
    with torch.no_grad():
        pos, neg = pipe.encode_prompt(prompt=prompt, negative_prompt=negative,
                                      do_classifier_free_guidance=True,
                                      max_sequence_length=226, device="cpu")
    log(f"{scene['id']}: prompt encoded in {time.time() - t0:.0f}s")
    _free_text_encoder(pipe)
    pipe.transformer.to(torch.float32)
    pipe.vae.to(torch.float32)
    gc.collect()

    t1 = time.time()
    with torch.no_grad():
        result = pipe(
            prompt_embeds=pos.to(torch.float32),
            negative_prompt_embeds=neg.to(torch.float32),
            height=height,
            width=width,
            num_frames=frames,
            num_inference_steps=steps,
            guidance_scale=float(pick(scene, job, "guidance", cfg["guidance"])),
            generator=torch.Generator("cpu").manual_seed(int(scene.get("seed", 7))),
        ).frames[0]
    log(f"{scene['id']}: {len(result)} frames in {time.time() - t1:.0f}s")
    return export(result, work / "raw.mp4", int(pick(scene, job, "raw_fps", cfg["raw_fps"])))


def generate_ltx(scene: dict, job: dict, work: pathlib.Path) -> pathlib.Path:
    import torch
    from diffusers import LTXPipeline

    cfg = DEFAULTS["ltx"]
    model = pick(scene, job, "model", cfg["model"])
    width = int(pick(scene, job, "width", 480))
    height = int(pick(scene, job, "height", 832))
    frames = int(pick(scene, job, "frames", 97))
    steps = int(pick(scene, job, "steps", cfg["steps"]))
    if (frames - 1) % 8:
        frames = ((frames - 1) // 8) * 8 + 1
    width -= width % 32
    height -= height % 32
    log(f"ltx {model}: {width}x{height} {frames}f {steps} steps")

    pipe = LTXPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
    pipe.set_progress_bar_config(disable=True)

    prompt = ", ".join(x for x in (scene["prompt"], job.get("style", "")) if x)
    t0 = time.time()
    with torch.no_grad():
        result = pipe(
            prompt=prompt,
            negative_prompt=pick(scene, job, "negative", NEGATIVE["ltx"]),
            width=width,
            height=height,
            num_frames=frames,
            num_inference_steps=steps,
            guidance_scale=float(pick(scene, job, "guidance", cfg["guidance"])),
            decode_timestep=0.03,
            decode_noise_scale=0.025,
            generator=torch.Generator("cpu").manual_seed(int(scene.get("seed", 7))),
        ).frames[0]
    log(f"{scene['id']}: {len(result)} frames in {time.time() - t0:.0f}s")
    return export(result, work / "raw.mp4", int(pick(scene, job, "raw_fps", cfg["raw_fps"])))


def _load_image(scene: dict) -> "object":
    """Keyframe image (stickman PNG) — I2V ka pehla frame."""
    from diffusers.utils import load_image

    path = scene.get("image")
    if not path:
        raise ValueError(f"{scene['id']}: 'image' chahiye I2V ke liye")
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = pathlib.Path(__file__).resolve().parent.parent / p
    if not p.exists():
        raise FileNotFoundError(f"keyframe nahi mila: {p}")
    return load_image(str(p))


def generate_wan22_i2v(scene: dict, job: dict, work: pathlib.Path) -> pathlib.Path:
    """Wan 2.2 TI2V-5B — image-to-video (stickman keyframe se asli motion)."""
    import torch
    from diffusers import AutoencoderKLWan

    cfg = DEFAULTS["wan22_i2v"]
    model = pick(scene, job, "model", cfg["model"])
    image = _load_image(scene)
    width = int(pick(scene, job, "width", 480))
    height = int(pick(scene, job, "height", 832))
    frames = int(pick(scene, job, "frames", 49))
    steps = int(pick(scene, job, "steps", cfg["steps"]))
    if (frames - 1) % 4:
        frames = ((frames - 1) // 4) * 4 + 1
    width -= width % 32
    height -= height % 32
    log(f"wan22_i2v {model}: {width}x{height} {frames}f {steps} steps (image conditioning)")

    # NOTE: WanPipeline (T2V) `image=` nahi leta — I2V ke liye WanImageToVideoPipeline lazmi hai.
    from diffusers import WanImageToVideoPipeline

    vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, torch_dtype=torch.bfloat16)
    pipe.set_progress_bar_config(disable=True)
    pipe.vae.enable_slicing()

    prompt = ", ".join(x for x in (scene["prompt"], job.get("style", "")) if x)
    t0 = time.time()
    with torch.no_grad():
        result = pipe(
            prompt=prompt,
            negative_prompt=pick(scene, job, "negative", NEGATIVE["wan22_i2v"]),
            image=image.resize((width, height)),
            height=height,
            width=width,
            num_frames=frames,
            num_inference_steps=steps,
            guidance_scale=float(pick(scene, job, "guidance", cfg["guidance"])),
            generator=torch.Generator("cpu").manual_seed(int(scene.get("seed", 7))),
        ).frames[0]
    log(f"{scene['id']}: {len(result)} frames in {time.time() - t0:.0f}s")
    return export(result, work / "raw.mp4", int(pick(scene, job, "raw_fps", cfg["raw_fps"])))


def generate_ltx_i2v(scene: dict, job: dict, work: pathlib.Path) -> pathlib.Path:
    """LTX-Video image-to-video — halka (2B), T4 par tez."""
    import torch
    from diffusers import LTXImageToVideoPipeline

    cfg = DEFAULTS["ltx_i2v"]
    model = pick(scene, job, "model", cfg["model"])
    image = _load_image(scene)
    width = int(pick(scene, job, "width", 480))
    height = int(pick(scene, job, "height", 832))
    frames = int(pick(scene, job, "frames", 73))
    steps = int(pick(scene, job, "steps", cfg["steps"]))
    if (frames - 1) % 8:
        frames = ((frames - 1) // 8) * 8 + 1
    width -= width % 32
    height -= height % 32
    log(f"ltx_i2v {model}: {width}x{height} {frames}f {steps} steps")

    pipe = LTXImageToVideoPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
    pipe.set_progress_bar_config(disable=True)

    prompt = ", ".join(x for x in (scene["prompt"], job.get("style", "")) if x)
    t0 = time.time()
    with torch.no_grad():
        result = pipe(
            image=image.resize((width, height)),
            prompt=prompt,
            negative_prompt=pick(scene, job, "negative", NEGATIVE["ltx_i2v"]),
            height=height,
            width=width,
            num_frames=frames,
            num_inference_steps=steps,
            guidance_scale=float(pick(scene, job, "guidance", cfg["guidance"])),
            decode_timestep=0.03,
            decode_noise_scale=0.025,
            generator=torch.Generator("cpu").manual_seed(int(scene.get("seed", 7))),
        ).frames[0]
    log(f"{scene['id']}: {len(result)} frames in {time.time() - t0:.0f}s")
    return export(result, work / "raw.mp4", int(pick(scene, job, "raw_fps", cfg["raw_fps"])))


BACKENDS = {
    "wan22_i2v": generate_wan22_i2v,
    "ltx_i2v": generate_ltx_i2v,
    "animatediff": generate_animatediff,
    "wan": generate_wan,
    "ltx": generate_ltx,
}


# --------------------------------------------------------------------------- #
# delivery finish
# --------------------------------------------------------------------------- #

def finish(raw: pathlib.Path, scene: dict, job: dict, out: pathlib.Path, ffmpeg: str) -> pathlib.Path:
    """1080x1920 delivery. Koi fake smoothness nahi: minterpolate nahi, halka grade."""
    fps = int(pick(scene, job, "fps", 24))
    seconds = float(scene.get("seconds", 3.0))
    sharpen = float(pick(scene, job, "sharpen", 0.6))
    grain = int(pick(scene, job, "grain", 3))
    graph = (
        f"scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop=1080:1920,"
        f"unsharp=5:5:{sharpen}:5:5:0.0,"
        f"eq=contrast=1.03:saturation=1.02:gamma=1.0,"
        f"noise=alls={grain}:allf=t,"
        f"fps={fps},"
        f"trim=duration={seconds},setpts=PTS-STARTPTS,"
        f"fade=t=in:st=0:d=0.2,format=yuv420p[v]"
    )
    cmd = [ffmpeg, "-y", "-i", str(raw), "-filter_complex", graph, "-map", "[v]",
           "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-tune", "film",
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
    parser.add_argument("--backend", help="animatediff | wan | ltx (job JSON ko override)")
    args = parser.parse_args(argv)

    job = json.loads(pathlib.Path(args.job).read_text())
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = os.environ.get("FFMPEG", "ffmpeg")

    import torch
    torch.set_num_threads(int(job.get("threads", 4)))

    scenes = [s for s in job["scenes"] if args.scene in (None, s["id"])]
    if not scenes:
        print("scene nahi mila:", args.scene)
        return 1

    backend = args.backend or job.get("backend", "animatediff")
    for scene in scenes:
        name = scene.get("backend", backend)
        if name not in BACKENDS:
            print(f"unknown backend: {name}")
            return 2
        work = out_dir / f"work_{scene['id']}"
        work.mkdir(exist_ok=True)
        clip = out_dir / f"{scene['id']}.mp4"
        if clip.exists() and clip.stat().st_size > 50000:
            log(f"{scene['id']}: already present, skip")
            continue
        log(f"{scene['id']}: backend={name}")
        raw = BACKENDS[name](scene, job, work)
        finish(raw, scene, job, clip, ffmpeg)
        log(f"{scene['id']}: {clip.name} {clip.stat().st_size / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
