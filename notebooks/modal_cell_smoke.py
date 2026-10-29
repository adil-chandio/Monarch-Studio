# Modal Notebook me yeh POORA cell paste karo aur Run dabao.
# (modal.com/notebooks -> New notebook)
#
# Kya hota hai: Modal ke free L4 GPU par ek scene render hoti hai (Wan 2.2 TI2V-5B, image se video).
# Pehli baar model download hoga (~10 GB, 5-8 min), phir render ~3-5 min.
# Aakhir me ek link aata hai jahan se clip khul jati hai.

import modal

APP = "monarch-video"
BRANCH = "arena/3d8cfad7-monarch-studio"
RAW = f"https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/{BRANCH}"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git")
    .pip_install(
        "torch==2.6.0", "diffusers>=0.32", "transformers>=4.49", "accelerate",
        "safetensors", "sentencepiece", "protobuf", "ftfy", "imageio-ffmpeg",
        "huggingface_hub", "pillow", "numpy", "fastapi",
    )
    .env({"HF_HOME": "/cache/hf", "HF_HUB_DISABLE_XET": "1"})
)

cache = modal.Volume.from_name("monarch-cache", create_if_missing=True)
app = modal.App(APP, image=image)


@app.function(gpu="L4", timeout=2700, volumes={"/cache": cache})
def render(scene_id="k01", steps=12, frames=25, width=384, height=672):
    import hashlib, json, pathlib, urllib.request
    import torch
    from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
    from diffusers.utils import export_to_video, load_image

    job = json.loads(urllib.request.urlopen(f"{RAW}/cloud/t2v_jobs/stick-i2v.json").read())
    scene = next(s for s in job["scenes"] if s["id"] == scene_id)
    work = pathlib.Path("/cache/work") / f"stick-i2v_{scene_id}"
    work.mkdir(parents=True, exist_ok=True)
    kf = work / f"{scene_id}.png"
    if not kf.exists():
        urllib.request.urlretrieve(f"{RAW}/{scene['image']}", kf)

    model = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
    vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()

    out = work / f"{scene_id}.mp4"
    with torch.no_grad():
        frames_out = pipe(
            image=load_image(str(kf)).resize((width, height)),
            prompt=f"{scene['prompt']} {job.get('style', '')}".strip(),
            negative_prompt=job.get("negative", "blurry, low quality, text, watermark"),
            height=height, width=width, num_frames=frames,
            num_inference_steps=steps, guidance_scale=5.0,
            generator=torch.Generator("cpu").manual_seed(int(scene["seed"])),
        ).frames[0]
    export_to_video(frames_out, str(out), fps=24)
    cache.commit()
    return {"scene": scene_id, "file": str(out), "bytes": out.stat().st_size,
            "md5": hashlib.md5(out.read_bytes()).hexdigest(), "gpu": torch.cuda.get_device_name(0)}


print(render.remote("k01"))
print("\n✅ Clip /cache/work/stick-i2v_k01/k01.mp4 par hai — bolo 'smoke ok' taake poore 12 chalein.")
