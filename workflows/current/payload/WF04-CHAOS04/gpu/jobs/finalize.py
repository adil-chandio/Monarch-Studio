"""Final assembly: concat rendered chunks → grade + strobes + our score → verify.

    python gpu/jobs/finalize.py --chunks render/chunks --out build/CHAOS04_MASTER_1080x1920.mp4

The chunks are lossless-ish intermediates (crf 12) written by the production
matrix; this pass is the only grade the film gets, so it stays gentle.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from chaos04.encode import (build_flash_overlay, measure_loudness, run,  # noqa: E402
                            TARGET_LUFS, TARGET_LRA, TARGET_TP, verify, ffmpeg_exe)
from chaos04.timeline import TOTAL_FRAMES  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default="render/chunks")
    ap.add_argument("--audio", default="build/score_48k.wav")
    ap.add_argument("--out", default="build/CHAOS04_MASTER_1080x1920.mp4")
    ap.add_argument("--preview", default="build/CHAOS04_PREVIEW_540x960.mp4")
    ap.add_argument("--crf", type=float, default=18.5)
    args = ap.parse_args(argv)

    ff = ffmpeg_exe()
    chunks = sorted(Path(args.chunks).glob("chunk_*.mp4"))
    if not chunks:
        raise SystemExit("no chunks found")
    print("chunks", [c.name for c in chunks], flush=True)

    listing = Path(args.chunks) / "concat.txt"
    listing.write_text("\n".join(f"file '{c.resolve()}'" for c in chunks))
    joined = Path(args.chunks) / "joined.mp4"
    run([ff, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
         "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)])
    print("joined", joined.stat().st_size, flush=True)

    flash = build_flash_overlay(ROOT / "build/flash_overlay.mkv")
    audio = Path(args.audio)
    meas = measure_loudness(audio)
    loud = (f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"
            f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
            f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
            f":offset={meas['target_offset']}:linear=true")

    def encode(out, width, height, crf, preset):
        fc = (
            f"[1:v]scale={width}:{height}:flags=bicubic,gblur=sigma=26,format=gbrp[fl];"
            f"[0:v]format=gbrp[base];"
            f"[base][fl]blend=all_mode=screen:all_opacity=1.0[lit];"
            f"[lit]rgbashift=rh=2:bh=-2,eq=contrast=1.055:saturation=1.06:gamma=0.985,"
            f"vignette=angle=PI/4.3:mode=forward,noise=alls=8:allf=t+u,"
            f"scale={width}:{height}:flags=lanczos,format=yuv420p[v];"
            f"[2:a]{loud}[a]"
        )
        run([ff, "-y", "-hide_banner", "-loglevel", "warning",
             "-i", str(joined), "-i", str(flash), "-i", str(audio),
             "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
             "-frames:v", str(TOTAL_FRAMES),
             "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
             "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
             "-x264-params", "keyint=60:min-keyint=15:scenecut=0",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", "-shortest", str(out)])
        return verify(out)

    master = encode(args.out, 1080, 1920, args.crf, "slow")
    print("MASTER " + json.dumps(master), flush=True)
    Path(args.out).with_suffix(".report.json").write_text(json.dumps(master, indent=1))

    prev = encode(args.preview, 540, 960, 23, "veryfast")
    print("PREVIEW " + json.dumps(prev), flush=True)
    Path(args.preview).with_suffix(".report.json").write_text(json.dumps(prev, indent=1))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
