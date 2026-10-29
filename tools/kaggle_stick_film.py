#!/usr/bin/env python3
"""kaggle_stick_film — poora 36s stickman film ek hi run me (Kaggle free GPU).

Owner ke liye sirf 1 cell:
    !git clone --depth 1 -b arena/3d8cfad7-monarch-studio https://github.com/adil-chandio/Monarch-Studio /kaggle/working/repo
    !python /kaggle/working/repo/tools/kaggle_stick_film.py

Kya karta hai:
  1. 12 locked BUDDY keyframes (repo me) ko image-conditioning bana kar animate — asli video model se
     (Wan 2.2 TI2V-5B, aur T4 par na chale to LTX-Video 2B).
  2. Clips ko captions + voice + sound ke sath 1080x1920 master me jodta hai (tools/clip_film.py).
  3. `/kaggle/working/monarch_stick_36s.mp4` + receipts chhodta hai aur notebook me video dikhata hai.

Resume-safe: jo scene ban chuki hai skip hoti hai (session toot jaye to dobara chalao).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOB = ROOT / "cloud/t2v_jobs/stick-i2v.json"
SPEC = ROOT / "studio/films/stick-i2v/film/film_clips.json"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sh(cmd, check=True):
    proc = subprocess.run(cmd if isinstance(cmd, list) else ["bash", "-lc", cmd],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"cmd fail: {cmd}\n{proc.stderr[-800:]}")
    return proc


def ensure_deps() -> None:
    import importlib

    missing = []
    for mod, pkg in (("diffusers", "diffusers>=0.32"), ("transformers", "transformers>=4.49"),
                     ("accelerate", "accelerate"), ("imageio_ffmpeg", "imageio-ffmpeg")):
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            missing.append(pkg)
    if missing:
        log(f"pip install: {' '.join(missing)}")
        sh([sys.executable, "-m", "pip", "install", "-q", *missing])
    if not shutil_which("ffmpeg"):
        log("ffmpeg apt se")
        sh("apt-get -qq update && apt-get -qq install -y ffmpeg", check=False)


def shutil_which(name: str) -> str | None:
    import shutil

    return shutil.which(name)


# --------------------------------------------------------------------------- #
# model + render
# --------------------------------------------------------------------------- #

class Renderer:
    """Wan 2.2 (T2V/I2V) pehle, phir LTX-Video. Dono diffusers par, T4-friendly fp16."""

    def __init__(self, job: dict):
        import torch

        self.torch = torch
        self.job = job
        self.dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        self.pipe = None
        self.kind = None
        self.width = int(job.get("width", 480))
        self.height = int(job.get("height", 832))
        self.frames = int(job.get("frames", 49))
        self.steps = int(job.get("steps", 16))
        log(f"GPU: {torch.cuda.get_device_name(0)} | dtype {self.dtype}")

    def load(self) -> None:
        if self.pipe is not None:
            return
        torch = self.torch
        try:
            from diffusers import AutoencoderKLWan, WanImageToVideoPipeline

            model = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
            log(f"loading {model} (pehli baar ~10 GB download)")
            vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
            pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, torch_dtype=self.dtype)
            pipe.enable_model_cpu_offload()
            pipe.set_progress_bar_config(disable=True)
            self.pipe, self.kind = pipe, "wan22_i2v"
        except Exception as exc:                       # noqa: BLE001
            log(f"Wan 2.2 fail ({type(exc).__name__}: {str(exc)[:160]}) -> LTX-Video")
            from diffusers import LTXImageToVideoPipeline

            pipe = LTXImageToVideoPipeline.from_pretrained(
                "Lightricks/LTX-Video", torch_dtype=self.dtype)
            pipe.enable_model_cpu_offload()
            pipe.set_progress_bar_config(disable=True)
            self.pipe, self.kind = pipe, "ltx_i2v"
        log(f"backend: {self.kind}")

    def render(self, scene: dict, keyframe: pathlib.Path, seconds: float):
        from diffusers.utils import load_image

        torch = self.torch
        self.load()
        img = load_image(str(keyframe)).resize((self.width, self.height))
        gen = torch.Generator("cpu").manual_seed(int(scene.get("seed", 7)))
        prompt = f"{scene['prompt']} {self.job.get('style', '')}".strip()
        neg = self.job.get("negative", "blurry, low quality, text, watermark")
        with torch.no_grad():
            if self.kind == "wan22_i2v":
                out = self.pipe(image=img, prompt=prompt, negative_prompt=neg,
                                height=self.height, width=self.width, num_frames=self.frames,
                                num_inference_steps=self.steps, guidance_scale=5.0,
                                generator=gen).frames[0]
            else:
                out = self.pipe(image=img, prompt=prompt, negative_prompt=neg,
                                height=self.height, width=self.width, num_frames=self.frames,
                                num_inference_steps=24, guidance_scale=3.0,
                                decode_timestep=0.03, decode_noise_scale=0.025,
                                generator=gen).frames[0]
        return out

    def downshift(self) -> bool:
        """VRAM kam pare to chhota canvas."""
        if self.width <= 384:
            return False
        self.width, self.height = 384, 672
        log(f"canvas chhota kar diya: {self.width}x{self.height}")
        return True


def render_all(runner: Renderer, scenes: list[dict], out: pathlib.Path) -> dict:
    from diffusers.utils import export_to_video

    receipts, done = [], 0
    for n, scene in enumerate(scenes, 1):
        clip = out / f"{scene['id']}.mp4"
        if clip.exists() and clip.stat().st_size > 20000:
            log(f"[{n}/{len(scenes)}] {scene['id']}: pehle se bani, skip")
            continue
        kf = ROOT / scene["image"]
        started = time.time()
        log(f"[{n}/{len(scenes)}] {scene['id']}: render ({runner.kind or 'load'})")
        for attempt in (1, 2):
            try:
                frames = runner.render(scene, kf, scene.get("seconds", 3.0))
                tmp = out / f"{scene['id']}_raw.mp4"
                export_to_video(frames, str(tmp), fps=16)
                tmp.replace(clip)
                dt = time.time() - started
                log(f"{scene['id']}: OK {len(frames)}f in {dt / 60:.1f} min")
                receipts.append({"scene": scene["id"], "state": "ok",
                                 "backend": runner.kind, "seconds": round(dt)})
                done += 1
                if done == 1:
                    eta = dt * (len(scenes) - n) / 60
                    log(f"ETA baqi scenes ke liye: ~{eta:.0f} min")
                break
            except Exception as exc:                   # noqa: BLE001
                msg = f"{type(exc).__name__}: {str(exc)[:200]}"
                log(f"{scene['id']}: try {attempt} FAIL {msg}")
                if "out of memory" in msg.lower() and runner.downshift():
                    continue
                if attempt == 2:
                    receipts.append({"scene": scene["id"], "state": "fail", "error": msg})
        (out / "receipts.json").write_text(json.dumps(receipts, indent=2))
    return {"receipts": receipts, "ok": sum(1 for r in receipts if r["state"] == "ok")}


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #

def assemble(clips_dir: pathlib.Path, work: pathlib.Path) -> pathlib.Path | None:
    sys.path.insert(0, str(ROOT / "tools"))
    spec = json.loads(SPEC.read_text())
    spec["clips"] = str(clips_dir)
    spec["voice_dir"] = str(ROOT / "studio/films/personality-t2v/voice")
    available = {p.stem for p in clips_dir.glob("k*.mp4")}
    spec["scenes"] = [s for s in spec["scenes"] if s["id"] in available]
    if not spec["scenes"]:
        log("koi clip nahi — assembly skip")
        return None
    work.mkdir(parents=True, exist_ok=True)
    spec_path = work / "film_clips.json"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    master = work / "monarch_stick_36s.mp4"
    import clip_film

    log(f"assembly: {len(spec['scenes'])} clips + captions + voice + sound")
    info = clip_film.render(spec_path, master)
    log(f"MASTER: {master} ({master.stat().st_size / 1e6:.1f} MB, "
        f"{info.get('info', {}).get('duration', '?')}s, scenes {info.get('scenes')})")
    return master


def show(master: pathlib.Path) -> None:
    try:
        from IPython.display import Video, display

        display(Video(str(master), embed=False, width=420))
    except Exception:                                  # noqa: BLE001
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kaggle_stick_film")
    ap.add_argument("--out", default="/kaggle/working/stick")
    ap.add_argument("--only", default="")
    ap.add_argument("--no-assemble", action="store_true")
    args = ap.parse_args(argv)

    ensure_deps()
    job = json.loads(JOB.read_text())
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    scenes = [s for s in job["scenes"] if not args.only or s["id"] in args.only.split(",")]

    runner = Renderer(job)
    result = render_all(runner, scenes, out)
    log(f"clips: {result['ok']}/{len(scenes)}")

    master = None
    if not args.no_assemble:
        master = assemble(out, pathlib.Path("/kaggle/working"))
    final = pathlib.Path("/kaggle/working")
    if master and master.exists():
        target = final / master.name
        if target != master:
            target.write_bytes(master.read_bytes())
        log(f"FINAL: {target}")
        show(target)
    print(json.dumps({"clips": result["ok"], "master": str(master) if master else None,
                      "receipts": str(out / 'receipts.json')}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
