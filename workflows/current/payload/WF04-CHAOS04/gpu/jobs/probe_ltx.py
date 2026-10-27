import os, time, json, traceback
t_all = time.time()
os.environ.setdefault("HF_HOME", "/content/hf")
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), flush=True)
W = "/content/chaos_work/probe"
os.makedirs(W, exist_ok=True)
rep = {"stages": []}

def mark(k, v=None):
    rep["stages"].append({"t": round(time.time() - t_all, 1), "stage": k, "info": v})
    print("[%7.1fs] %s %s" % (time.time() - t_all, k, "" if v is None else v), flush=True)

H, WD, NF, ST = 512, 896, 97, 30
try:
    t0 = time.time()
    from diffusers import LTXPipeline
    from diffusers.utils import export_to_video
    mark("imports", round(time.time() - t0, 1))

    t0 = time.time()
    pipe = LTXPipeline.from_pretrained("Lightricks/LTX-Video", torch_dtype=torch.bfloat16)
    mark("weights_loaded", round(time.time() - t0, 1))
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    mark("offload_ready")

    prompt = ("vertical cinematic night alley, stylised 3D character in black hooded "
              "coat walking toward camera, neon red rim light, volumetric haze, "
              "handheld camera, film grain, moody thriller look")
    t0 = time.time()
    out = pipe(prompt=prompt, height=H, width=WD, num_frames=NF,
               num_inference_steps=ST, guidance_scale=3.0,
               negative_prompt="blurry, low quality, watermark, text, distorted face").frames[0]
    dur = time.time() - t0
    mark("generate", "%.1fs for %d frames %dx%d @%d steps = %.2f fps"
         % (dur, NF, WD, H, ST, NF / max(dur, 0.001)))

    p = W + "/probe_t4.mp4"
    export_to_video(out, p, fps=24)
    sz = os.path.getsize(p)
    mark("export", "%s %d B" % (p, sz))
    rep.update(ok=True, sec_per_frame=round(dur / NF, 2), file=p, bytes=sz,
               peak_vram_gb=round(torch.cuda.max_memory_allocated() / 1e9, 2),
               width=WD, height=H, frames=NF, steps=ST)
except Exception as e:
    mark("ERROR", "%s: %s" % (type(e).__name__, e))
    traceback.print_exc()
    rep.update(ok=False, error="%s: %s" % (type(e).__name__, e))
json.dump(rep, open(W + "/probe_report.json", "w"), indent=1)
print("DONE " + json.dumps(rep)[:700], flush=True)
