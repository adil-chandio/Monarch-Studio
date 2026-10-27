"""Finish and deliver: strobe overlay, grade, grain, loudness conform, verification.

    python3 chaos04/encode.py --frames render/frames --audio build/score_48k.wav \
        --out build/CHAOS04_MONARCH_1080x1920.mp4

Everything timed here comes from the measured reference grid (120 BPM half-beats):
the strobes are generated per frame, so they cannot drift.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chaos04.timeline import CUT_TIMES, FLASH_TIMES, FPS, TOTAL_FRAMES  # noqa: E402

TARGET_LUFS = -13.9
TARGET_TP = -0.3
TARGET_LRA = 9.0


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def ffprobe_exe() -> str:
    ff = ffmpeg_exe()
    cand = Path(ff).with_name("ffprobe")
    if cand.exists():
        return str(cand)
    return "ffprobe"


def run(cmd, **kw):
    proc = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if proc.returncode != 0:
        print(proc.stdout[-4000:])
        print(proc.stderr[-4000:], file=sys.stderr)
        raise SystemExit(f"command failed ({proc.returncode}): {' '.join(map(str, cmd[:6]))} …")
    return proc


def flash_envelope(frames=TOTAL_FRAMES):
    """0..1 per frame: a strobe hit on every measured 120 BPM half-beat."""
    env = np.zeros(frames, dtype=np.float32)
    for t in FLASH_TIMES:
        n = int(round(t * FPS))
        for k, v in ((0, 0.92), (1, 0.34), (2, 0.09)):
            if 0 <= n + k < frames:
                env[n + k] = max(env[n + k], v)
    # the cut grid gets a smaller kick, so cuts read as hits not just jumps
    for t in CUT_TIMES:
        n = int(round(t * FPS))
        if 0 <= n < frames:
            env[n] = max(env[n], 0.22)
    return env


def build_flash_overlay(path: Path, frames=TOTAL_FRAMES, w=180, h=320):
    """Stream a streamable overlay: soft radial bloom + fine noise, screen-blended later."""
    ff = ffmpeg_exe()
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ff, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "8",
           "-pix_fmt", "yuv444p", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - w / 2) / (w / 2)
    ny = (yy - h / 2) / (h / 2)
    r = np.sqrt(nx ** 2 * 0.55 + ny ** 2 * 0.45)
    env = flash_envelope(frames)
    rng = np.random.default_rng(7)
    for i in range(frames):
        a = float(env[i])
        if a <= 0.001:
            proc.stdin.write(np.zeros((h, w, 3), np.uint8).tobytes())
            continue
        cx, cy = rng.normal(0, 0.06, 2)
        rr = np.sqrt((nx - cx) ** 2 * 0.55 + (ny - cy) ** 2 * 0.45)
        core = np.clip(1.0 - np.clip(rr / 1.25, 0, 1), 0, 1) ** 1.7
        ring = np.exp(-((rr - 0.55) ** 2) / 0.035) * 0.35
        grain = rng.normal(0, 0.06, (h, w)).astype(np.float32)
        field = np.clip((core + ring) * a + grain * a, 0, 1)
        tint = np.array([1.0, 0.97, 0.93], np.float32)   # warm white, not pure #fff
        img = (field[..., None] * tint * 255.0).astype(np.uint8)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode(errors="replace")
    if proc.wait() != 0:
        raise SystemExit("flash overlay encode failed: " + err[-2000:])
    return path


def measure_loudness(audio: Path) -> dict:
    ff = ffmpeg_exe()
    cmd = [ff, "-hide_banner", "-nostats", "-i", str(audio),
           "-af", f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
           "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    text = out.stderr
    blob = text[text.rfind("{"):text.rfind("}") + 1]
    try:
        return json.loads(blob)
    except Exception:
        raise SystemExit("could not read loudnorm measurement:\n" + text[-1500:])


def encode(frames_dir: Path, audio: Path | None, out: Path, start_frame=1,
           count=None, width=1080, height=1920, crf=18.5, preset="slow",
           vignette=True, grain=9, ca=2, overlay=True, flash_path=None,
           loudness=True, preview=False, fps=FPS, extra_fade=None):
    ff = ffmpeg_exe()
    frames_dir = Path(frames_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    count = count or TOTAL_FRAMES

    inputs = ["-framerate", str(fps), "-start_number", str(start_frame),
              "-i", str(frames_dir / "%04d.png")]
    fc = []
    chain = []
    if overlay and flash_path:
        if start_frame > 1:      # keep the strobe grid locked to the picture
            inputs += ["-ss", f"{(start_frame - 1) / fps:.4f}"]
        inputs += ["-i", str(flash_path)]
        fc.append(f"[1:v]scale={width}:{height}:flags=bicubic,gblur=sigma=26,"
                  f"format=gbrp[fl]")
        fc.append("[0:v]format=gbrp[base]")
        fc.append("[base][fl]blend=all_mode=screen:all_opacity=1.0[lit]")
        last = "[lit]"
    else:
        fc.append("[0:v]format=gbrp[base]")
        last = "[base]"

    grade = []
    if ca:
        grade.append(f"rgbashift=rh={ca}:bh=-{ca}:gv=0:bv=0")
    grade.append("eq=contrast=1.055:saturation=1.06:gamma=0.985")
    if vignette:
        grade.append("vignette=angle=PI/4.3:mode=forward")
    if grain:
        grade.append(f"noise=alls={grain}:allf=t+u")
    grade.append("scale=%d:%d:flags=lanczos" % (width, height))
    grade.append("format=yuv420p")
    fc.append(last + ",".join(grade) + "[v]")

    audio_idx = 2 if (overlay and flash_path) else 1
    afilter = None
    if audio:
        inputs += ["-i", str(audio)]
        if loudness:
            meas = measure_loudness(audio)
            afilter = (f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"
                       f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
                       f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
                       f":offset={meas['target_offset']}:linear=true")
        else:
            afilter = "anull"
        fc.append(f"[{audio_idx}:a]{afilter}[a]")

    cmd = [ff, "-y", "-hide_banner", "-loglevel", "warning", *inputs,
           "-filter_complex", ";".join(fc), "-map", "[v]"]
    if audio:
        cmd += ["-map", "[a]"]
    cmd += ["-frames:v", str(count),
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
            "-x264-params", "keyint=60:min-keyint=15:scenecut=0",
            "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    cmd += ["-movflags", "+faststart", "-shortest", str(out)]
    run(cmd)
    return out


def verify(video: Path) -> dict:
    """ffprobe when it exists, otherwise read the same facts out of ffmpeg."""
    ff = ffmpeg_exe()
    fp = ffprobe_exe()
    info = {}
    if Path(fp).exists() and fp != "ffprobe":
        try:
            probe = run([fp, "-v", "error", "-count_frames", "-select_streams", "v:0",
                         "-show_entries", "stream=codec_name,width,height,nb_read_frames,"
                         "avg_frame_rate,pix_fmt,duration", "-of", "json", str(video)])
            st = json.loads(probe.stdout)["streams"][0]
            info = dict(codec=st["codec_name"], width=int(st["width"]),
                        height=int(st["height"]), frames=int(st["nb_read_frames"]),
                        fps=st["avg_frame_rate"], pix_fmt=st["pix_fmt"])
            fmt = json.loads(run([fp, "-v", "error", "-show_entries",
                                  "format=duration,size,bit_rate", "-of", "json",
                                  str(video)]).stdout)["format"]
            info.update(bytes=int(fmt["size"]), seconds=float(fmt["duration"]),
                        bitrate=int(fmt["bit_rate"]))
        except Exception:
            info = {}

    if not info:
        meta = subprocess.run([ff, "-hide_banner", "-i", str(video)], capture_output=True,
                              text=True).stderr
        dur = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", meta)
        seconds = (int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
                   if dur else 0.0)
        vid = re.search(r"Video: (\w+).*?(\d{2,5})x(\d{2,5}).*?([\d.]+) fps", meta)
        size = re.search(r"bitrate: (\d+) kb/s", meta)
        count = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(video),
                                "-map", "0:v:0", "-f", "null", "-"],
                               capture_output=True, text=True).stderr
        frames = re.findall(r"frame=\s*(\d+)", count)
        info = dict(codec=vid.group(1) if vid else None,
                    width=int(vid.group(2)) if vid else 0,
                    height=int(vid.group(3)) if vid else 0,
                    fps=(vid.group(4) + "/1") if vid else None,
                    frames=int(frames[-1]) if frames else 0,
                    pix_fmt="yuv420p", seconds=seconds,
                    bytes=Path(video).stat().st_size,
                    bitrate=int(size.group(1)) * 1000 if size else 0)

    loud = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(video), "-vn",
                           "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    integrated = re.findall(r"I:\s+(-?\d+\.\d+) LUFS", loud)
    peaks = re.findall(r"Peak:\s+(-?\d+\.\d+) dBFS", loud)
    info.update(
        file=str(video),
        integrated_lufs=float(integrated[-1]) if integrated else None,
        true_peak_dbfs=float(peaks[-1]) if peaks else None,
        has_audio="Audio:" in loud,
    )
    return info


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default="render/frames")
    ap.add_argument("--audio", default="build/score_48k.wav")
    ap.add_argument("--out", default="build/CHAOS04_MONARCH_1080x1920.mp4")
    ap.add_argument("--start-frame", type=int, default=1)
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--crf", type=float, default=18.5)
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--no-overlay", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--flash-cache", default="build/flash_overlay.mkv")
    args = ap.parse_args(argv)

    count = args.count or TOTAL_FRAMES
    if args.preview:
        args.width, args.height, args.crf, args.preset = 540, 960, 22, "veryfast"

    flash = None
    if not args.no_overlay:
        flash = build_flash_overlay(Path(args.flash_cache), frames=TOTAL_FRAMES)
    audio = None if args.no_audio else Path(args.audio)
    if audio and not audio.exists():
        raise SystemExit(f"audio missing: {audio} (run chaos04/score.py first)")
    out = encode(Path(args.frames), audio, Path(args.out), start_frame=args.start_frame,
                 count=count, width=args.width, height=args.height, crf=args.crf,
                 preset=args.preset, overlay=not args.no_overlay, flash_path=flash,
                 preview=args.preview)
    report = verify(out)
    report["flash_frames"] = len(np.nonzero(flash_envelope(TOTAL_FRAMES))[0])
    report["overlay"] = bool(flash)
    print(json.dumps(report, indent=1))
    Path(out).with_suffix(".report.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    argv = sys.argv[1:]
    main(argv)
