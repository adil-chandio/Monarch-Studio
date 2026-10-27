"""Gate 1: build the scene small, render a spread of frames, report timings.

    source gpu/jobs/env.sh && ensure_blender && fetch_repo
    $BL "$WF/gpu/jobs/selftest.py" -- --work "$WF"
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy

from chaos04 import build, camera, character, direct, world  # noqa: E402

FRAMES = [1, 60, 250, 420, 500, 620, 750, 900, 1100, 1200, 1240, 1300]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=".")
    ap.add_argument("--frames", default=",".join(map(str, FRAMES)))
    ap.add_argument("--width", type=int, default=360)
    ap.add_argument("--height", type=int, default=640)
    ap.add_argument("--samples", type=int, default=8)
    args = ap.parse_args(argv)

    work = Path(args.work)
    out = work / "build/selftest"
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    build.main(["--out", str(work / "build/selftest.blend"), "--width", str(args.width),
                "--height", str(args.height), "--samples", str(args.samples)])
    build_s = time.time() - t0

    scene = bpy.context.scene
    scene.cycles.samples = args.samples
    timings = []
    for f in [int(x) for x in args.frames.split(",")]:
        t = time.time()
        scene.frame_set(f)
        scene.render.filepath = str(out / f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        timings.append(dict(frame=f, seconds=round(time.time() - t, 2),
                            bytes=(out / f"{f:04d}.png").stat().st_size))
    per = sum(t["seconds"] for t in timings) / len(timings)
    report = dict(build_seconds=round(build_s, 1), resolution=[args.width, args.height],
                  samples=args.samples, frames=timings, mean_seconds=round(per, 2),
                  # at 1080x1920 the cost is ~9x the pixels of 360x640
                  eta_1080_min=round(per * 9 * 1332 / 60, 1),
                  objects=len(bpy.data.objects), materials=len(bpy.data.materials))
    (work / "build/selftest.json").write_text(json.dumps(report, indent=1))
    print("SELFTEST " + json.dumps(report))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
