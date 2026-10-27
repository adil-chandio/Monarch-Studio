"""Resumable frame renderer.

    blender -b build/chaos04.blend --python chaos04/render.py -- \
        --out render/frames --start 1 --end 120 --samples 20 --device GPU

Skips frames that already exist, logs per-frame seconds to render/progress.jsonl
so the box can be restarted at any time without losing work.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import bpy


def enable_gpu(scene, prefer="CUDA"):
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in (prefer, "OPTIX", "CUDA", "HIP", "METAL"):
        try:
            prefs.compute_device_type = backend
        except Exception:
            continue
        try:
            prefs.get_devices()
        except Exception:
            continue
        gpus = [d for d in prefs.devices if d.type != "CPU"]
        if gpus:
            for d in prefs.devices:
                d.use = d.type != "CPU"
            scene.cycles.device = "GPU"
            return backend, [d.name for d in gpus]
    scene.cycles.device = "CPU"
    return "CPU", []


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="render/frames")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=1332)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--samples", type=int, default=0)
    ap.add_argument("--device", default="AUTO", choices=["AUTO", "CPU", "GPU"])
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--height", type=int, default=0)
    ap.add_argument("--skip-existing", type=int, default=1)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--only", default="", help="comma separated frame numbers to render")
    ap.add_argument("--blend", default="", help="scene to open (required for the bpy wheel)")
    args = ap.parse_args(argv)

    # With a blender binary you pass the .blend on the command line; with the bpy
    # wheel we start from the factory startup scene, so open it here.
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
        print("OPENED", args.blend, flush=True)

    scene = bpy.context.scene
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if args.samples:
        scene.cycles.samples = args.samples
    if args.width and args.height:
        scene.render.resolution_x = args.width
        scene.render.resolution_y = args.height

    backend, names = ("CPU", [])
    if args.device in {"AUTO", "GPU"}:
        backend, names = enable_gpu(scene)
    print(json.dumps({"device": backend, "gpus": names,
                      "samples": scene.cycles.samples,
                      "res": [scene.render.resolution_x, scene.render.resolution_y]}),
          flush=True)

    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.compression = 30

    if args.only:
        frames = [int(x) for x in args.only.split(",") if x.strip()]
    else:
        frames = list(range(args.start, min(args.end, scene.frame_end) + 1,
                            max(1, args.step)))
    log_path = out.parent / "progress.jsonl"
    done = 0
    t_all = time.time()
    for i, f in enumerate(frames):
        path = out / (f"{args.prefix}{f:04d}.png")
        if args.skip_existing and path.exists() and path.stat().st_size > 20000:
            continue
        t0 = time.time()
        scene.frame_set(f)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        done += 1
        remain = len(frames) - i - 1
        line = dict(frame=f, seconds=round(dt, 2), eta_min=round(remain * dt / 60, 1),
                    bytes=path.stat().st_size if path.exists() else 0)
        with log_path.open("a") as fh:
            fh.write(json.dumps(line) + "\n")
        print("FRAME", json.dumps(line), flush=True)
    total = time.time() - t_all
    print(json.dumps({"rendered": done, "seconds": round(total, 1),
                      "per_frame": round(total / done, 2) if done else 0}), flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
