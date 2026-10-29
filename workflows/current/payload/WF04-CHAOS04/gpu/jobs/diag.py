"""One frame from the middle of every segment, with a luma report.

Cheap way to prove no shot is black, blown out or empty before a long render.

    python gpu/jobs/diag.py -- <workdir> [--samples 8]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy
import numpy as np

from chaos04 import build, direct  # noqa: E402


def main(argv):
    work = Path(argv[0]) if argv else Path(".")
    samples = 8
    if "--samples" in argv:
        samples = int(argv[argv.index("--samples") + 1])
    out = work / "render/diag"
    out.mkdir(parents=True, exist_ok=True)

    build.main(["--out", str(work / "build/diag.blend"), "--width", "360",
                "--height", "640", "--samples", str(samples)])
    scene = bpy.context.scene
    scene.cycles.samples = samples

    rows = []
    for seg in direct.SEGMENTS:
        f = (seg["start"] + seg["end"]) // 2
        scene.frame_set(f)
        path = out / f"{seg['id']}_{f:04d}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(str(path))
        px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
        luma = float(px.mean()) * 255.0
        peak = float(px.max()) * 255.0
        rows.append(dict(id=seg["id"], name=seg["name"], frame=f,
                         luma=round(luma, 1), peak=round(peak, 1),
                         black=luma < 3.0, blown=luma > 235.0))
        print("DIAG", json.dumps(rows[-1]), flush=True)

    (out / "report.json").write_text(json.dumps(rows, indent=1))
    bad = [r for r in rows if r["black"] or r["blown"]]
    print("DIAG BAD " + json.dumps(bad), flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
