#!/usr/bin/env python3
"""cloud_scene_pack — cloud par poora scene pack banao: AI images + depth maps + voice.

Runner ke paas internet hai, is liye model wahin download hote hain. Output `cloud-scenes`
branch par jaata hai, phir agent git se wapas laata hai.

Input (cloud/scene_jobs/<id>.json):
{
  "id": "personality-36",
  "size": [768, 1344],
  "model": "stabilityai/sdxl-turbo",
  "steps": 2,
  "scenes": [{"id": "s01", "prompt": "...", "voice": "..."}]
}

Output:  <out>/s01.png ... (images), s01_depth.png (depth), s01.wav (voice), receipt.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def make_images(job: dict, out: pathlib.Path) -> list[dict]:
    import torch
    from diffusers import AutoPipelineForText2Image

    model = job.get("model", "stabilityai/sdxl-turbo")
    steps = int(job.get("steps", 2))
    width, height = (int(v) for v in job.get("size", [768, 1344]))
    torch.set_num_threads(int(job.get("threads", 4)))
    log(f"loading {model} (cpu, {steps} steps, {width}x{height})")
    pipe = AutoPipelineForText2Image.from_pretrained(model, torch_dtype=torch.float32,
                                                     variant=None, use_safetensors=True)
    pipe.set_progress_bar_config(disable=True)

    made = []
    for index, scene in enumerate(job["scenes"], 1):
        target = out / f"{scene['id']}.png"
        if target.exists():
            made.append({"id": scene["id"], "file": target.name, "skipped": True})
            continue
        started = time.time()
        image = pipe(prompt=scene["prompt"], num_inference_steps=steps, guidance_scale=0.0,
                     width=width, height=height,
                     generator=torch.Generator("cpu").manual_seed(int(scene.get("seed", 100 + index)))
                     ).images[0]
        image.save(target)
        log(f"scene {index}/{len(job['scenes'])} {scene['id']} in {time.time() - started:.0f}s")
        made.append({"id": scene["id"], "file": target.name,
                     "seconds": round(time.time() - started, 1)})
    return made


def make_depth(job: dict, out: pathlib.Path) -> int:
    """Depth map — parallax camera move ke liye (2.5D), slide nahi."""
    import torch
    from PIL import Image
    from transformers import pipeline

    torch.set_num_threads(4)
    log("loading depth model")
    estimator = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf",
                         device=-1)
    count = 0
    for scene in job["scenes"]:
        source = out / f"{scene['id']}.png"
        target = out / f"{scene['id']}_depth.png"
        if not source.exists() or target.exists():
            continue
        depth = estimator(Image.open(source))["depth"]
        depth.save(target)
        count += 1
    log(f"depth maps: {count}")
    return count


def make_voice(job: dict, out: pathlib.Path) -> int:
    """Kokoro-82M CPU par — har scene ki narrator line."""
    lines = [s for s in job["scenes"] if (s.get("voice") or "").strip()]
    if not lines:
        return 0
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="a")
    voice = job.get("voice_id", "am_michael")
    made = 0
    for scene in lines:
        target = out / f"{scene['id']}.wav"
        if target.exists():
            continue
        chunks = [audio for _, _, audio in pipeline(scene["voice"], voice=voice, speed=1.0)]
        audio = np.concatenate([c if isinstance(c, np.ndarray) else c.numpy() for c in chunks])
        sf.write(target, audio, 24000)
        log(f"voice {scene['id']} {len(audio) / 24000:.2f}s")
        made += 1
    return made


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cloud_scene_pack")
    parser.add_argument("job")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    job = json.loads(pathlib.Path(args.job).read_text())
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    images = make_images(job, out)
    depths = make_depth(job, out)
    voices = make_voice(job, out)

    receipt = {"job": job["id"], "engine": "sdxl-turbo + depth-anything-v2 + kokoro",
               "scenes": images, "depth_maps": depths, "voice_lines": voices,
               "seconds": round(time.time() - started, 1)}
    (out / "scene_receipt.json").write_text(json.dumps(receipt, indent=2))
    log(json.dumps(receipt, indent=2)[:800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
