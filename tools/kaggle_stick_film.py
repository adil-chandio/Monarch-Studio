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


def hud(done: int, total: int, eta_min: float = -1) -> None:
    """Film-set progress: ek nazar me kitna bacha hai."""
    filled = round(12 * done / max(total, 1))
    bar = "▓" * filled + "░" * (12 - filled)
    tail = f" · ETA ~{eta_min:.0f} min" if eta_min >= 0 else ""
    print(f"\n  🎬 SCENE {done}/{total}  {bar}  {round(100 * done / max(total, 1))}%{tail}\n",
          flush=True)


def sh(cmd, check=True):
    proc = subprocess.run(cmd if isinstance(cmd, list) else ["bash", "-lc", cmd],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"cmd fail: {cmd}\n{proc.stderr[-800:]}")
    return proc


def ensure_deps(quant: str = "") -> None:
    import importlib

    missing = []
    for mod, pkg in (("diffusers", "diffusers>=0.32"), ("transformers", "transformers>=4.49"),
                     ("bitsandbytes", "bitsandbytes"),
                     ("accelerate", "accelerate"), ("imageio_ffmpeg", "imageio-ffmpeg"),
                     ("ftfy", "ftfy"), ("sentencepiece", "sentencepiece"),
                     ("safetensors", "safetensors"), ("regex", "regex")):
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            missing.append(pkg)
    if missing:
        log(f"pip install: {' '.join(missing)}")
        sh([sys.executable, "-m", "pip", "install", "-q", *missing])
    if str(quant).lower() == "int8":
        # Kaggle par purana bnb hota hai — int8 quantization ke liye taza chahiye
        log("int8: bitsandbytes + accelerate upgrade")
        sh([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes", "accelerate"],
           check=False)
        try:
            import bitsandbytes as _bnb

            log(f"bitsandbytes {_bnb.__version__}")
        except Exception as exc:                       # noqa: BLE001
            log(f"bitsandbytes import FAIL: {type(exc).__name__}: {str(exc)[:200]}")
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
        # resolution ladder: OOM par neeche, quality bar 720p par shuru
        ladder = job.get("ladder") or [[720, 1280], [576, 1024], [480, 832]]
        self.ladder = [(int(w), int(h)) for w, h in ladder]
        self.frames = int(job.get("frames", 49))
        self.steps = int(job.get("steps", 16))
        # offload: "sequential" (safe, dheema, har layer) | "model" (module-wise, ~2x tez)
        #          | "none" (sab GPU par — sirf bare GPU par). Bench se decide hota hai.
        self.offload = str(job.get("offload") or "sequential").lower()
        # quant: "" (bf16) | "int8" (bitsandbytes — T4 par 720p fit karane ke liye)
        self.quant = str(job.get("quant") or "").lower()
        # attn: "slice" => attention slicing (720p par activation memory ~30% kam, thoda dheema)
        self.attn = str(job.get("attn") or "").lower()
        self.transformer = None
        log(f"GPU: {torch.cuda.get_device_name(0)} | dtype {self.dtype}")

    def load(self) -> None:
        if self.pipe is not None:
            return
        torch = self.torch
        # T4 (16 GB) par Wan 2.2 5B (bf16 ~10 GB) + umt5 encoder ek sath nahi aate.
        # "sequential": har layer alag GPU jati hai — chalta hai magar ~2x dheema.
        # "model": poora module ek dafa GPU (encoder -> transformer -> vae) — tez.
        def _wan():
            from diffusers import AutoencoderKLWan, WanImageToVideoPipeline

            model = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
            log(f"loading {model} (~10 GB download, T4 par pehli baar 5-8 min)")
            vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=self.dtype)
            if self.quant == "int8":
                # 720p par attention 16 GB se zyada maangta hai — weights int8 (aadhe) karo.
                # Transformer + text encoder dono int8 => dono GPU par aa jate hain (offload ki zarurat nahi).
                from diffusers import WanTransformer3DModel
                from transformers import BitsAndBytesConfig, UMT5EncoderModel

                qcfg = BitsAndBytesConfig(load_in_8bit=True)
                tf = WanTransformer3DModel.from_pretrained(
                    model, subfolder="transformer", quantization_config=qcfg,
                    torch_dtype=self.dtype, device_map={"": 0})
                te = UMT5EncoderModel.from_pretrained(
                    model, subfolder="text_encoder", quantization_config=qcfg,
                    torch_dtype=self.dtype, device_map={"": 0})
                log("int8 (bitsandbytes): transformer + text encoder — 720p ke liye")
                pipe = WanImageToVideoPipeline.from_pretrained(
                    model, vae=vae, transformer=tf, text_encoder=te, torch_dtype=self.dtype)
                self.offload = "none"
            else:
                pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, torch_dtype=self.dtype)
            self._apply_offload(pipe)
            if self.attn == "slice":
                try:
                    pipe.enable_attention_slicing("max")
                    log("attention slicing: max")
                except Exception as exc:               # noqa: BLE001
                    log(f"attention slicing fail: {type(exc).__name__}")
            pipe.set_progress_bar_config(disable=True)
            log(f"offload: {self.offload} | quant: {self.quant or 'bf16'}")
            return pipe

        def _ltx():
            from diffusers import LTXImageToVideoPipeline

            log("loading LTX-Video 2B (halka, T4 par aaram se)")
            pipe = LTXImageToVideoPipeline.from_pretrained(
                "Lightricks/LTX-Video", torch_dtype=self.dtype)
            pipe.enable_sequential_cpu_offload()
            pipe.set_progress_bar_config(disable=True)
            return pipe

        engine = str(self.job.get("engine") or "auto").lower()
        if engine == "ltx":
            self.pipe, self.kind = _ltx(), "ltx_i2v"
        else:
            try:
                self.pipe, self.kind = _wan(), "wan22_i2v"
            except Exception as exc:                   # noqa: BLE001
                msg = f"{type(exc).__name__}: {str(exc)[:600]}"
                if self.quant == "int8":
                    log(f"int8 load fail ({msg}) -> bf16 + sequential")
                    self.quant, self.offload = "", "sequential"
                    try:
                        self.pipe, self.kind = _wan(), "wan22_i2v"
                        log(f"backend: {self.kind} (bf16 fallback)")
                        return
                    except Exception as exc2:          # noqa: BLE001
                        log(f"bf16 bhi fail ({type(exc2).__name__}) -> LTX-Video")
                else:
                    log(f"Wan 2.2 load fail ({msg}) -> LTX-Video")
                self.pipe, self.kind = _ltx(), "ltx_i2v"
        log(f"backend: {self.kind}")

    def _apply_offload(self, pipe) -> None:
        """offload mode lagao (pipeline hooks pehle hata kar)."""
        try:
            if hasattr(pipe, "remove_all_hooks"):
                pipe.remove_all_hooks()
        except Exception:                              # noqa: BLE001
            pass
        if self.offload == "none":
            try:
                pipe.to("cuda")
            except Exception as exc:                   # noqa: BLE001
                log(f"pipe.to(cuda) fail ({type(exc).__name__}: {str(exc)[:120]}) — device_map par bharosa")
        elif self.offload == "model":
            pipe.enable_model_cpu_offload()
        else:
            self.offload = "sequential"
            pipe.enable_sequential_cpu_offload()
        try:
            pipe.vae.enable_tiling()
            pipe.vae.enable_slicing()
        except Exception:                              # noqa: BLE001
            pass

    def set_offload(self, mode: str) -> bool:
        """OOM par: quality girane se pehle sasta offload try karo (resolution wohi)."""
        mode = str(mode).lower()
        if self.pipe is None or mode == self.offload:
            return False
        log(f"offload {self.offload} -> {mode} (resolution barqarar)")
        self.offload = mode
        try:
            self.pipe.to("cpu")
        except Exception:                              # noqa: BLE001
            pass
        self.torch.cuda.empty_cache()
        self._apply_offload(self.pipe)
        return True

    def retune(self, quant: str | None = None, offload: str | None = None) -> bool:
        """Quant/offload badalne ke liye pipeline dobara load karo. Fail ho to False."""
        if quant is not None:
            self.quant = quant
        if offload is not None:
            self.offload = offload
        log(f"retune -> quant={self.quant or 'bf16'} offload={self.offload}")
        self.pipe = None
        self.kind = None
        import gc

        gc.collect()
        try:
            self.torch.cuda.empty_cache()
        except Exception:                              # noqa: BLE001
            pass
        try:
            self.load()
            return True
        except Exception as exc:                       # noqa: BLE001
            log(f"retune fail: {type(exc).__name__}: {str(exc)[:160]}")
            return False

    def next_fallback(self) -> str:
        """OOM par tarteeb: sasta offload -> int8 -> chhota canvas -> LTX. Quality pehle."""
        if self.kind == "wan22_i2v":
            if self.offload in ("model", "none"):
                if self.set_offload("sequential"):
                    return "offload:sequential"
                return ""
            if self.quant != "int8":
                if self.retune(quant="int8", offload="none"):
                    return "quant:int8"
                if self.retune(quant="", offload="sequential"):
                    return "offload:sequential"
                return ""
            if self.downshift():
                return "downshift"
        if self.switch_to_ltx():
            return "ltx"
        return ""

    def switch_to_ltx(self) -> bool:
        """Wan 2.2 T4 par OOM hi deta rahe to LTX-Video par (asli video, halka model)."""
        if self.kind == "ltx_i2v":
            return False
        log("Wan 2.2 OOM -> LTX-Video 2B par switch")
        self.pipe = None
        import gc

        gc.collect()
        self.torch.cuda.empty_cache()
        from diffusers import LTXImageToVideoPipeline

        self.pipe = LTXImageToVideoPipeline.from_pretrained(
            "Lightricks/LTX-Video", torch_dtype=self.dtype)
        self.pipe.enable_sequential_cpu_offload()
        self.pipe.set_progress_bar_config(disable=True)
        self.kind = "ltx_i2v"
        self.width, self.height = 480, 832
        return True

    def prepare(self, scene: dict) -> None:
        """Scene ke apne overrides lagao (ek hi run me 720p vs 576p test ho sake)."""
        want_w = int(scene.get("width", self.width))
        want_h = int(scene.get("height", self.height))
        if not hasattr(self, "ceiling"):               # OOM ke baad upar wapas na jao
            self.ceiling = (int(self.job.get("width", want_w)), int(self.job.get("height", want_h)))
        cw, ch = self.ceiling
        if want_w * want_h > cw * ch:
            want_w, want_h = cw, ch
        self.width, self.height = want_w, want_h
        self.frames = int(scene.get("frames", self.job.get("frames", self.frames)))
        self.attn = str(scene.get("attn", self.job.get("attn") or "")).lower()
        want_q = str(scene.get("quant", self.job.get("quant") or "")).lower()
        want_o = str(scene.get("offload", self.job.get("offload") or "sequential")).lower()
        if self.pipe is not None and (want_q != self.quant or want_o != self.offload):
            self.retune(quant=want_q, offload=want_o)
        else:
            self.quant, self.offload = want_q, want_o

    def render(self, scene: dict, keyframe: pathlib.Path, seconds: float):
        from diffusers.utils import load_image

        torch = self.torch
        self.load()
        img = load_image(str(keyframe)).resize((self.width, self.height))
        gen = torch.Generator("cpu").manual_seed(int(scene.get("seed", 7)))
        prompt = f"{scene['prompt']} {self.job.get('style', '')}".strip()
        neg = self.job.get("negative", "blurry, low quality, text, watermark")
        steps = int(scene.get("steps", self.steps))
        self.frames = int(scene.get("frames", self.frames))
        self.last_steps = steps
        with torch.no_grad():
            if self.kind == "wan22_i2v":
                out = self.pipe(image=img, prompt=prompt, negative_prompt=neg,
                                height=self.height, width=self.width, num_frames=self.frames,
                                num_inference_steps=steps, guidance_scale=5.0,
                                generator=gen).frames[0]
            else:
                out = self.pipe(image=img, prompt=prompt, negative_prompt=neg,
                                height=self.height, width=self.width, num_frames=self.frames,
                                num_inference_steps=steps,
                                guidance_scale=float(self.job.get("guidance", 3.0)),
                                decode_timestep=0.03, decode_noise_scale=0.025,
                                generator=gen).frames[0]
        return out

    def downshift(self) -> bool:
        """OOM par ladder me agla (chhota) canvas. Sabse chhota bhi fail ho to LTX."""
        current = (self.width, self.height)
        smaller = [(w, h) for w, h in self.ladder if w * h < current[0] * current[1]]
        if not smaller:
            return False
        self.width, self.height = max(smaller, key=lambda s: s[0] * s[1])
        self.ceiling = (self.width, self.height)
        log(f"canvas chhota: {self.width}x{self.height}")
        return True


def render_all(runner: Renderer, scenes: list[dict], out: pathlib.Path) -> dict:
    from diffusers.utils import export_to_video

    receipts, done, avg = [], 0, 0.0
    for n, scene in enumerate(scenes, 1):
        clip = out / f"{scene['id']}.mp4"
        if clip.exists() and clip.stat().st_size > 20000:
            log(f"[{n}/{len(scenes)}] {scene['id']}: pehle se bani, skip")
            continue
        kf = ROOT / scene["image"]
        started = time.time()
        hud(n - 1, len(scenes), (avg * (len(scenes) - n + 1) / 60) if avg else -1)
        log(f"[{n}/{len(scenes)}] {scene['id']} · {scene.get('caption', '')} · "
            f"{scene.get('seconds', 3.0)}s · backend {runner.kind or 'load'}")
        for attempt in range(1, 5):
            try:
                runner.prepare(scene)
                frames = runner.render(scene, kf, scene.get("seconds", 3.0))
                tmp = out / f"{scene['id']}_raw.mp4"
                export_to_video(frames, str(tmp), fps=16)
                # interp: kam frames (720p par 25 hi fit hote hain) ko doubla karo taake
                # scene ki asli cadence (3s) bani rahe. ffmpeg CPU par, GPU quota free.
                interp = int(runner.job.get("interp") or 0)
                if interp and len(frames) < interp and shutil_which("ffmpeg"):
                    doubled = out / f"{scene['id']}_interp.mp4"
                    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(tmp),
                           "-vf", f"minterpolate=fps={interp}:mi_mode=mci",
                           "-r", str(int(runner.job.get("fps", 16))),
                           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(doubled)]
                    try:
                        sh(cmd)
                        if doubled.exists() and doubled.stat().st_size > 20000:
                            doubled.replace(clip)
                            tmp.unlink(missing_ok=True)
                            log(f"{scene['id']}: interp {len(frames)}f -> fps {interp} "
                                f"(scene {int(runner.job.get('fps', 16))}fps cadence)")
                        else:
                            tmp.replace(clip)
                    except Exception as exc:               # noqa: BLE001
                        log(f"{scene['id']}: interp fail ({type(exc).__name__}) — asli clip")
                        tmp.replace(clip)
                else:
                    tmp.replace(clip)
                dt = time.time() - started
                log(f"{scene['id']}: OK {len(frames)}f in {dt / 60:.1f} min")
                receipts.append({"scene": scene["id"], "state": "ok",
                                 "backend": runner.kind, "seconds": round(dt),
                                 "size": f"{runner.width}x{runner.height}",
                                 "steps": getattr(runner, "last_steps", runner.steps),
                                 "offload": runner.offload,
                                 "quant": runner.quant or "bf16",
                                 "frames": runner.frames})
                done += 1
                avg = dt if not avg else (avg + dt) / 2
                hud(n, len(scenes))
                if dt > 60:
                    log(f"{scene['id']}: {dt / 60:.1f} min · baqi ~"
                        f"{avg * (len(scenes) - n) / 60:.0f} min")
                break
            except Exception as exc:                   # noqa: BLE001
                import traceback

                msg = f"{type(exc).__name__}: {str(exc)[:300]}"
                tb = traceback.format_exc()[-900:]
                log(f"{scene['id']}: try {attempt} FAIL {msg}")
                if "out of memory" in msg.lower():
                    step = runner.next_fallback()
                    log(f"{scene['id']}: OOM -> {step or 'koi fallback nahi'}")
                    if step:
                        continue
                if attempt == 2:
                    receipts.append({"scene": scene["id"], "state": "fail", "error": msg,
                                     "trace": tb})
        (out / "receipts.json").write_text(json.dumps(receipts, indent=2))
    return {"receipts": receipts, "ok": sum(1 for r in receipts if r["state"] == "ok")}


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #

def assemble(clips_dir: pathlib.Path, work: pathlib.Path) -> pathlib.Path | None:
    sys.path.insert(0, str(ROOT / "tools"))
    spec = json.loads(SPEC.read_text())
    clips_dir = pathlib.Path(clips_dir).resolve()      # relative path kabhi na phanse
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


def show_kit(kit_dir: pathlib.Path) -> None:
    try:
        from IPython.display import Image, Video, display

        teaser = kit_dir / "teaser_11s.mp4"
        if teaser.exists():
            log(f"TEASER: {teaser} ({teaser.stat().st_size / 1e6:.1f} MB)")
            display(Video(str(teaser), embed=False, width=320))
        cover = kit_dir / "cover.jpg"
        if cover.exists():
            display(Image(filename=str(cover), width=320))
    except Exception:                                  # noqa: BLE001
        pass


def work_root(out: pathlib.Path) -> pathlib.Path:
    """Kaggle -> /kaggle/working, Colab -> /content, warna out ke sath."""
    for candidate in ("/kaggle/working", "/content"):
        if pathlib.Path(candidate).is_dir():
            return pathlib.Path(candidate)
    return out.parent


# --------------------------------------------------------------------------- #
# selftest — GPU ke bagair poora pipeline (clips -> captions -> voice -> master)
# --------------------------------------------------------------------------- #

def selftest(scenes: list[dict], out: pathlib.Path, ffmpeg: str) -> dict:
    """Har scene ki jagah keyframe se ek dummy clip banata hai, phir asli assembly.

    Maqsad sirf yeh prove karna hai ke GPU wala run jo code chalayega woh yahan bhi chalta hai
    (spec, captions, voice, sound bed, master export). Output ko film ki tarah deliver na karo.
    """
    clips = out / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    for scene in scenes:
        kf = ROOT / scene["image"]
        clip = clips / f"{scene['id']}.mp4"
        if clip.exists() and clip.stat().st_size > 20000:
            continue
        if not kf.exists():
            raise SystemExit(f"keyframe nahi mila: {kf}")
        sh([ffmpeg, "-y", "-loop", "1", "-i", str(kf), "-t", f"{float(scene.get('seconds', 3.0)):.3f}",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-r", "24", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast",
            str(clip)])
    master = assemble(clips, out)
    expected = round(sum(float(s.get("seconds") or 3.0) for s in scenes), 2)
    have = round(master.stat().st_size / 1e6, 2) if master and master.exists() else 0.0
    return {"master": str(master) if master else None,
            "duration": expected, "mb": have, "scenes": len(scenes)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kaggle_stick_film")
    ap.add_argument("--out", default="", help="clips kahan (default: <work>/stick)")
    ap.add_argument("--final", default="", help="master kahan (default: /kaggle/working ya /content)")
    ap.add_argument("--only", default="", help="sirf yeh scenes, e.g. k01,k02")
    ap.add_argument("--job", default="", help="alternate job json (prompts/size override)")
    ap.add_argument("--no-assemble", action="store_true")
    ap.add_argument("--title", default="Powerful Personality", help="cover/kit ka title")
    ap.add_argument("--no-kit", action="store_true", help="sirf film, launch kit nahi")
    ap.add_argument("--assemble-only", action="store_true",
                    help="render skip — pehle se maujood clips se master + kit banao (CPU)")
    ap.add_argument("--selftest", action="store_true",
                    help="GPU ke bagair pipeline check (dummy clips, asli assembly)")
    args = ap.parse_args(argv)

    job_path = pathlib.Path(args.job) if args.job else JOB
    if not job_path.is_absolute():
        job_path = ROOT / job_path
    job = json.loads(job_path.read_text())
    scenes = [s for s in job["scenes"] if not args.only or s["id"] in args.only.split(",")]

    out = pathlib.Path(args.out) if args.out else work_root(pathlib.Path(".")) / "stick"
    final = pathlib.Path(args.final) if args.final else work_root(out)
    out.mkdir(parents=True, exist_ok=True)

    if args.selftest:
        import shutil as _sh

        ffmpeg = _sh.which("ffmpeg")
        if not ffmpeg:
            raise SystemExit("ffmpeg chahiye selftest ke liye")
        res = selftest(scenes, out, ffmpeg)
        kit_ok = False
        try:
            import film_factory

            receipt = film_factory.build(pathlib.Path(res["master"]), out / "clips",
                                         out / "kit", args.title)
            film_factory.card(receipt)
            kit_ok = bool(receipt["kit"].get("cover.jpg") and receipt["kit"].get("subtitles.srt"))
        except Exception as exc:                       # noqa: BLE001
            log(f"selftest kit FAIL: {type(exc).__name__}: {str(exc)[:200]}")
        res["kit"] = kit_ok
        log(f"SELFTEST: {res}")
        print(json.dumps(res, indent=2))
        return 0 if res["master"] and res["duration"] > 0 and kit_ok else 1

    if args.assemble_only:
        have = sorted(p.stem for p in out.glob("*.mp4") if p.stat().st_size > 20000)
        log(f"assemble-only: {len(have)} clips mile ({', '.join(have) or 'none'})")
        if not have:
            raise SystemExit(f"koi clip nahi mila: {out}")
        result = {"ok": len(have)}
    else:
        # quant scene-level bhi ho sakta hai — kisi bhi scene ko int8 chahiye to bnb upgrade karo
        wants_int8 = any(str(s.get("quant", "")).lower() == "int8" for s in scenes)
        ensure_deps("int8" if wants_int8 or str(job.get("quant", "")).lower() == "int8" else "")
        runner = Renderer(job)
        result = render_all(runner, scenes, out)
        log(f"clips: {result['ok']}/{len(scenes)}")

    master = None
    if not args.no_assemble:
        master = assemble(out, final)
    final.mkdir(parents=True, exist_ok=True)
    if master and master.exists():
        target = final / master.name
        if target != master:
            target.write_bytes(master.read_bytes())
        log(f"FINAL: {target}")
        if not args.no_kit:
            try:
                import film_factory

                receipt = film_factory.build(target, out, final / "kit", args.title)
                film_factory.card(receipt)
                show_kit(final / "kit")
            except Exception as exc:                   # noqa: BLE001
                log(f"launch kit fail (film theek hai): {type(exc).__name__}: {str(exc)[:160]}")
        show(target)
    print(json.dumps({"clips": result["ok"], "master": str(master) if master else None,
                      "receipts": str(out / 'receipts.json')}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
