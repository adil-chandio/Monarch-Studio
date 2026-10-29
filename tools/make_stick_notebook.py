#!/usr/bin/env python3
"""make_stick_notebook — owner ke liye Colab notebook (image -> video) generate karta hai.

Notebook ko hi source of truth rakho: is script ko badlo, phir notebook dobara banao
(`python3 tools/make_stick_notebook.py`), taake Drive wali copy kabhi drift na kare.

Owner ka flow sirf 2 tap: Runtime > T4 GPU, phir Run all.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOB = ROOT / "cloud" / "t2v_jobs" / "stick-i2v.json"
OUT = ROOT / "notebooks" / "Stick_I2V_Colab.ipynb"
RAW = ("https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/"
       "arena/3d8cfad7-monarch-studio/studio/films/stick-i2v/keyframes")


def build() -> dict:
    job = json.loads(JOB.read_text())
    scenes = [{"id": s["id"], "seed": s["seed"], "prompt": s["prompt"]} for s in job["scenes"]]
    cells: list[dict] = []

    def md(src: str) -> None:
        cells.append({"cell_type": "markdown", "metadata": {}, "source": src.splitlines(True)})

    def code(src: str) -> None:
        cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                      "outputs": [], "source": src.splitlines(True)})

    md("""# Monarch · Stickman film (image → video)

Pehle **12 stickman images**, phir unhi ko **image-to-video model** se animate.

**2 tap:** (1) `Runtime → Change runtime type → T4 GPU` → Save, (2) `Runtime → Run all`.
Clips khud Google Drive me `Monarch-T2V/stick-clips/` me jati hain. Session toot jaye to
dobara Run all — jo clip ban chuki hai woh skip ho jayegi.

Model: **Wan 2.2 TI2V-5B** (image → video). Agar woh T4 par na chale to notebook khud
**LTX-Video 2B** par switch kar ke wahi scene bana deta hai — aap ko kuch nahi karna.
""")

    md("""### 1 · GPU check""")
    code("""import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE")
assert torch.cuda.is_available(), "Runtime > Change runtime type > T4 GPU chuno, phir Run all"
p = torch.cuda.get_device_properties(0)
print("VRAM:", round(p.total_memory / 1e9, 1), "GB | bf16:", torch.cuda.is_bf16_supported())
DTYPE = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
""")

    md("""### 2 · Libraries""")
    code("""%pip -q install "git+https://github.com/huggingface/diffusers" "transformers>=4.49" accelerate safetensors sentencepiece protobuf ftfy imageio imageio-ffmpeg
import diffusers, transformers
print("diffusers", diffusers.__version__, "| transformers", transformers.__version__)
""")

    md("""### 3 · Drive folder + keyframes""")
    code("""import pathlib
OUT = None
try:
    from google.colab import drive
    drive.mount('/content/drive', force_remount=False)
    OUT = pathlib.Path('/content/drive/MyDrive/Monarch-T2V/stick-clips')
    OUT.mkdir(parents=True, exist_ok=True)
    print("Drive folder ready:", OUT)
except Exception as exc:
    print("Drive mount nahi hua:", type(exc).__name__, exc, "— approve karke cell dobara chala dein")
""")

    code(f'''import json, urllib.request

KF = pathlib.Path('/content/keyframes'); KF.mkdir(exist_ok=True)
RAW = "{RAW}"
for i in range(1, 13):
    sid = f"k{{i:02d}}"
    f = KF / f"{{sid}}.png"
    if not f.exists() or f.stat().st_size < 10000:
        urllib.request.urlretrieve(f"{{RAW}}/{{sid}}.png", f)
print(len(list(KF.glob('*.png'))), "keyframes ready")

if OUT is None:
    OUT = pathlib.Path('/content/stick-clips'); OUT.mkdir(exist_ok=True)
print("clips jayengi:", OUT)

SCENES = {json.dumps(scenes, indent=1, ensure_ascii=False)}
NEG = {json.dumps(job["negative"], ensure_ascii=False)}
FRAMES, STEPS, H, W = 73, 22, 832, 480     # 73 = 4k+1 = 8k+1 -> ~3.0s @24fps
print(len(SCENES), "scenes |", W, "x", H, "|", FRAMES, "frames")
''')

    md("""### 4 · Models (Wan 2.2 I2V, fallback LTX-Video)""")
    code("""import gc, torch
from diffusers.utils import load_image, export_to_video

WAN_ID = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
LTX_ID = "Lightricks/LTX-Video"
PIPES = {}

def wan():
    # Wan 2.2 TI2V-5B image-to-video pipeline (WanPipeline image= nahi leta)
    if "wan" not in PIPES:
        from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
        vae = AutoencoderKLWan.from_pretrained(WAN_ID, subfolder="vae", torch_dtype=torch.float32)
        pipe = WanImageToVideoPipeline.from_pretrained(WAN_ID, vae=vae, torch_dtype=DTYPE)
        pipe.enable_model_cpu_offload()
        pipe.vae.enable_slicing()
        pipe.set_progress_bar_config(disable=True)
        PIPES["wan"] = pipe
    return PIPES["wan"]

def ltx():
    if "ltx" not in PIPES:
        from diffusers import LTXImageToVideoPipeline
        pipe = LTXImageToVideoPipeline.from_pretrained(LTX_ID, torch_dtype=DTYPE)
        pipe.to("cuda")
        pipe.enable_attention_slicing()
        pipe.set_progress_bar_config(disable=True)
        PIPES["ltx"] = pipe
    return PIPES["ltx"]

def drop(kind):
    PIPES.pop(kind, None)
    gc.collect(); torch.cuda.empty_cache()

print("model loaders ready")
""")

    md("""### 5 · Render (resume-safe)""")
    code("""import time

def render(kind, scene, steps=STEPS, frames=FRAMES):
    img = load_image(str(KF / f'{scene["id"]}.png')).resize((W, H))
    gen = torch.Generator("cpu").manual_seed(int(scene["seed"]))
    with torch.no_grad():
        if kind == "wan":
            return wan()(image=img, prompt=scene["prompt"], negative_prompt=NEG,
                         height=H, width=W, num_frames=frames,
                         num_inference_steps=steps, guidance_scale=5.0,
                         generator=gen).frames[0]
        return ltx()(image=img, prompt=scene["prompt"], negative_prompt=NEG,
                     height=H, width=W, num_frames=frames,
                     num_inference_steps=24, guidance_scale=3.0,
                     decode_timestep=0.03, decode_noise_scale=0.025,
                     generator=gen).frames[0]

state = {"kind": "wan"}
results = []
todo = [s for s in SCENES
        if not ((OUT / f'{s["id"]}.mp4').exists() and (OUT / f'{s["id"]}.mp4').stat().st_size > 20000)]
print(f"{len(todo)} scenes baqi")

for n, scene in enumerate(todo, 1):
    t0 = time.time()
    print(f'[{n}/{len(todo)}] {scene["id"]} — {state["kind"]} se animate ho rahi hai...', flush=True)
    try:
        try:
            frames = render(state["kind"], scene)
        except Exception as exc:
            print(f'  {state["kind"]} fail ({type(exc).__name__}: {str(exc)[:160]})', flush=True)
            if state["kind"] == "wan":
                print("  → LTX-Video (2B) par switch kar rahe hain", flush=True)
                drop("wan"); state["kind"] = "ltx"
                frames = render("ltx", scene)
            else:
                raise
        tmp = pathlib.Path('/content') / f'{scene["id"]}.mp4'
        export_to_video(frames, str(tmp), fps=24)
        clip = OUT / f'{scene["id"]}.mp4'
        clip.write_bytes(tmp.read_bytes())
        dt = round(time.time() - t0)
        print(f'{scene["id"]} OK in {dt//60}m {dt%60}s ({clip.stat().st_size/1e6:.1f} MB)', flush=True)
        results.append({"scene": scene["id"], "state": "ok", "backend": state["kind"], "seconds": dt})
    except Exception as exc:
        print(f'{scene["id"]} FAIL {type(exc).__name__}: {str(exc)[:220]}', flush=True)
        results.append({"scene": scene["id"], "state": "fail", "backend": state["kind"],
                        "error": f"{type(exc).__name__}: {str(exc)[:220]}"})
    (OUT / "receipt.json").write_text(json.dumps(results, indent=2))
print("batch done")
""")

    md("""### 6 · Status""")
    code("""done = sorted(p.stem for p in OUT.glob('k*.mp4'))
print(f"{len(done)} / {len(SCENES)} clips ready:", ", ".join(done))
missing = [s["id"] for s in SCENES if s["id"] not in done]
print("baqi:", missing if missing else "kuch nahi")
if missing:
    print("\\nRun all dobara dabayein — bani hui clips skip ho jayengi, baqi naye backend par banengi.")
else:
    print("\\nAgent ko bolen: 'stick clips ready' — final 36s film main bana dunga.")
""")

    return {"cells": cells,
            "metadata": {"accelerator": "GPU",
                         "colab": {"provenance": [], "gpuType": "T4",
                                   "name": "Monarch_Stick_I2V_36s.ipynb"},
                         "kernelspec": {"display_name": "Python 3", "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 0}


def main() -> int:
    nb = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    print(f"{OUT.relative_to(ROOT)} — {len(nb['cells'])} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
