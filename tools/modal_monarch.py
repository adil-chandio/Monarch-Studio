#!/usr/bin/env python3
"""modal_monarch — Monarch video renders Modal ke free GPU (L4/A10G) par.

Kyun Modal: Lightning PK me band hai, Colab ka free T4 purana (SM75) hai jahan naye models
nahi chalte. Modal ka starter free hai ($30/month credits, **card nahi**), aur L4/A10G
(24 GB, Ada/Ampere) milta hai — wohi hardware jo FreeVideo/H3 aur Wan 2.2 720p chahte hain.

Do tareeqe se chalta hai:
  1. **Modal Notebook** (browser): `notebooks/modal_cell_smoke.py` ka cell paste karo — bas.
  2. **CLI** (jis ke paas terminal ho):
        modal run tools/modal_monarch.py::smoke
        modal run tools/modal_monarch.py::film --job stick-h3

Smoke pehle chalao: ek scene (Wan 2.2 TI2V-5B I2V, 480x832) — poora raasta verify hota hai
(model download, render, file serve). Uske baad `film` poore 12 scenes karta hai.
"""

from __future__ import annotations

import json
import pathlib
import urllib.request

import modal

APP_NAME = "monarch-video"
BRANCH = "arena/3d8cfad7-monarch-studio"
RAW = f"https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/{BRANCH}"

CACHE = modal.Volume.from_name("monarch-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git", "fonts-dejavu-core")
    .pip_install(
        "torch==2.6.0", "diffusers>=0.32", "transformers>=4.49", "accelerate",
        "safetensors", "sentencepiece", "protobuf", "ftfy", "imageio-ffmpeg",
        "huggingface_hub", "pillow", "numpy",
    )
    .env({"HF_HOME": "/cache/hf", "HF_HUB_DISABLE_XET": "1", "TOKENIZERS_PARALLELISM": "false"})
)

app = modal.App(APP_NAME, image=image)


def fetch(url: str, dest: pathlib.Path) -> pathlib.Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return dest


def load_job(name: str) -> dict:
    with urllib.request.urlopen(f"{RAW}/cloud/t2v_jobs/{name}.json") as rsp:
        return json.loads(rsp.read().decode())


@app.function(gpu="L4", timeout=60 * 45, volumes={"/cache": CACHE})
def render_scene(job_name: str = "stick-i2v", scene_id: str = "k01",
                 steps: int = 24, frames: int = 49, width: int = 480, height: int = 832) -> dict:
    """Ek scene: keyframe ko image-conditioning bana kar asli video banao."""
    import hashlib

    import torch
    from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
    from diffusers.utils import export_to_video, load_image

    job = load_job(job_name)
    scene = next(s for s in job["scenes"] if s["id"] == scene_id)
    work = pathlib.Path("/cache/work") / f"{job_name}_{scene_id}"
    work.mkdir(parents=True, exist_ok=True)

    keyframe = fetch(f"{RAW}/{scene['image']}", work / f"{scene_id}.png")
    model = job.get("model") or "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
    if (frames - 1) % 4:
        frames = ((frames - 1) // 4) * 4 + 1

    vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()

    img = load_image(str(keyframe)).resize((width, height))
    out = work / f"{scene_id}.mp4"
    with torch.no_grad():
        result = pipe(
            image=img,
            prompt=f"{scene['prompt']} {job.get('style', '')}".strip(),
            negative_prompt=job.get("negative", "blurry, low quality, text, watermark"),
            height=height, width=width, num_frames=frames,
            num_inference_steps=steps, guidance_scale=float(job.get("guidance", 5.0)),
            generator=torch.Generator("cpu").manual_seed(int(scene["seed"])),
        ).frames[0]
    export_to_video(result, str(out), fps=int(job.get("fps", 24)))
    CACHE.commit()
    return {"scene": scene_id, "file": str(out), "bytes": out.stat().st_size,
            "md5": hashlib.md5(out.read_bytes()).hexdigest(), "frames": len(result),
            "gpu": torch.cuda.get_device_name(0)}


@app.function(timeout=60 * 10, volumes={"/cache": CACHE}, scaledown_window=120)
@modal.concurrent(max_inputs=4)
@modal.asgi_app()
def files():
    """Public link se clip download karo: /k01.mp4 waghera."""
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse

    api = FastAPI()

    @api.get("/")
    def index() -> dict:
        rows = []
        for path in sorted(pathlib.Path("/cache/work").rglob("*.mp4")):
            rows.append({"name": path.name, "stamp": path.parent.name,
                         "bytes": path.stat().st_size, "url": f"/f/{path.parent.name}/{path.name}"})
        return {"clips": rows}

    @api.get("/f/{stamp}/{name}")
    def get(stamp: str, name: str):
        path = pathlib.Path("/cache/work") / stamp / name
        if not path.exists():
            raise HTTPException(404, "not found")
        return FileResponse(path, media_type="video/mp4", filename=name)

    return api


@app.local_entrypoint()
def smoke() -> None:
    """Sab se chhota test: ek scene, kam steps — poora raasta chalta hai ya nahi."""
    info = render_scene.remote("stick-i2v", "k01", 12, 25, 384, 672)
    print(json.dumps(info, indent=2))
    print("ab dekhne ke liye: modal serve / deploy karke `files` endpoint kholo")


@app.local_entrypoint()
def film(job_name: str = "stick-i2v") -> None:
    job = load_job(job_name)
    results = []
    for scene in job["scenes"]:
        try:
            results.append(render_scene.remote(job_name, scene["id"]))
        except Exception as exc:                    # noqa: BLE001
            results.append({"scene": scene["id"], "error": f"{type(exc).__name__}: {exc}"})
        print(json.dumps(results[-1], indent=2))
    print(json.dumps({"job": job_name, "ok": sum(1 for r in results if "file" in r)}, indent=2))
