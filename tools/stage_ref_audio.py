#!/usr/bin/env python3
"""Prepare the WF-04 render inputs that are materialized from Drive.

The reference video itself must never live in the workspace: it is 26 MB of the
~128 MB snapshot budget. This tool derives the small render inputs from a staged
copy under /tmp and records the Drive provenance of the source video.

Usage:
    python3 tools/stage_ref_audio.py /tmp/monarch-stage/ref.mp4
    python3 tools/stage_ref_audio.py /tmp/monarch-stage/ref.mp4 --drive-id <id> --md5 <md5>

Output (default): $MONARCH_STAGE_DIR/ref_video/ref_audio.wav
    with MONARCH_STAGE_DIR defaulting to /tmp/monarch-stage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(os.environ.get("MONARCH_STAGE_DIR", "/tmp/monarch-stage"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("video", type=Path, help="staged reference video (outside the workspace)")
    parser.add_argument("--drive-id", default="", help="Drive file id of the reference video")
    parser.add_argument("--md5", dest="md5", default="", help="MD5 of the reference video (from Drive metadata)")
    parser.add_argument("--out-dir", type=Path, default=STAGE / "ref_video")
    parser.add_argument("--record", type=Path, default=ROOT / "workflows/current/payload/records/REFERENCE_SOURCE.json")
    args = parser.parse_args()

    if not args.video.exists():
        print(f"reference video not found: {args.video}", file=sys.stderr)
        return 2

    try:
        import imageio_ffmpeg
    except ImportError:
        print("imageio_ffmpeg missing — run: bash tools/bootstrap_env.sh", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    wav = args.out_dir / "ref_audio.wav"
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [exe, "-y", "-hide_banner", "-loglevel", "error", "-i", str(args.video),
         "-vn", "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", str(wav)],
        check=True,
    )
    size = args.video.stat().st_size
    local_md5 = args.md5 or hashlib.md5(args.video.read_bytes()).hexdigest()
    if args.record:
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps({
            "schema_version": 1,
            "note": "Reference video for WF-04 renders. The video itself is staged under /tmp (outside the workspace snapshot).",
            "reference_video": {
                "name": args.video.name,
                "drive_id": args.drive_id,
                "md5": local_md5,
                "size_bytes": size,
            },
            "derived": {
                "ref_audio_wav": str(wav),
                "ref_audio_bytes": wav.stat().st_size,
                "ffmpeg": exe,
            },
        }, indent=1) + "\n")
        print(f"recorded source provenance: {args.record.relative_to(ROOT)}")
    print(f"staged audio: {wav} ({wav.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
