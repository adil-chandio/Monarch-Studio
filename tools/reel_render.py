#!/usr/bin/env python3
"""reel_render — render a vertical reel on CPU, with no GPU, no network, no owner taps.

This is the "agent does it himself" path. It turns existing art plates into a
finished 1080x1920 reel: per-shot camera move (push / pull / pan), film grain,
vignette, graded contrast, kinetic captions, designed sound (drone + rain +
impacts + riser) and a loudnorm master.

Everything is ffmpeg. A 5-shot, 18-second reel renders in well under a minute on
two cores, so it can be produced inside the agent's own sandbox while the owner
is asleep — no Colab, no link, no tap.

Spec (JSON):
{
  "id": "reel-local-01",
  "title": "MONARCH",
  "size": [1080, 1920],
  "fps": 24,
  "plate_height": 608,           # 16:9 band inside the vertical frame
  "shots": [
    {"image": "path.png", "seconds": 3.2, "move": "push",
     "caption": "SHEHAR SO NAHI RAHA"},
    ...
  ],
  "audio": {"drone": 0.5, "rain": 0.5, "impacts": true, "riser": true, "voice": null}
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

VERSION = "reelrender-1.0"
MOVES = ("push", "pull", "pan_left", "pan_right", "still")
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
)


class RenderError(RuntimeError):
    """Anything that makes the reel impossible to deliver."""


# --------------------------------------------------------------------------- helpers
def which(binary: str) -> str | None:
    found = shutil.which(binary)
    return found or None


def md5(path: pathlib.Path) -> str:
    digest = hashlib.md5()
    with pathlib.Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def font_path(preferred: str | None = None) -> str:
    for candidate in ([preferred] if preferred else []) + list(FONT_CANDIDATES):
        if candidate and pathlib.Path(candidate).exists():
            return candidate
    raise RenderError("koi TTF font nahi mila — spec me 'font' de do")


def probe(path: pathlib.Path, ffmpeg: str = "ffmpeg") -> dict:
    text = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)],
                          capture_output=True, text=True).stderr
    import re
    size = re.search(r"[,\s](\d{2,5})x(\d{2,5})(?=[\s,\[])", text)
    dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    return {"name": pathlib.Path(path).name,
            "width": int(size.group(1)) if size else 0,
            "height": int(size.group(2)) if size else 0,
            "duration": round(int(dur.group(1)) * 3600 + int(dur.group(2)) * 60
                              + float(dur.group(3)), 3) if dur else 0.0,
            "bytes": pathlib.Path(path).stat().st_size,
            "md5": md5(path)}


def escape_text(text: str) -> str:
    """drawtext me colon/comma/quote escape karna padta hai."""
    out = str(text)
    for bad, good in (("\\", "\\\\"), (":", "\\:"), ("'", "\u2019"),
                      ("%", "\\%"), (",", "\\,")):
        out = out.replace(bad, good)
    return out.replace("\n", "\\n")


# --------------------------------------------------------------------------- titles
def make_caption_png(text: str, spec: dict, out: pathlib.Path) -> pathlib.Path:
    """Caption ko PIL se PNG banao — har ffmpeg build me drawtext nahi hota."""
    from PIL import Image, ImageDraw, ImageFont
    width, height = spec["size"]
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    size = int(spec.get("caption_size", 54))
    font = ImageFont.truetype(font_path(spec.get("font")), size)
    label = text.upper() if spec.get("uppercase", True) else text
    box = draw.textbbox((0, 0), label, font=font)
    text_w = box[2] - box[0]
    x = (width - text_w) // 2
    y = int(height * float(spec.get("caption_y", 0.79)))
    shadow = (0, 0, 0, 200)
    for dx, dy in ((0, 3), (2, 3), (-2, 3)):
        draw.text((x + dx, y + dy), label, font=font, fill=shadow)
    draw.text((x, y), label, font=font, fill=(255, 255, 255, 245))
    image.save(out)
    return out


# --------------------------------------------------------------------------- video
def _zoom_expr(move: str, frames: int) -> tuple[str, str, str]:
    """zoompan ke z / x / y expressions — inme har shot ka motion banta hai."""
    span = max(frames - 1, 1)
    if move == "push":
        return (f"min(1.0+0.12*on/{span},1.12)",
                "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)")
    if move == "pull":
        return (f"max(1.12-0.12*on/{span},1.0)",
                "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)")
    if move == "pan_left":
        return ("1.10", f"(iw-iw/zoom)*(1-0.35*on/{span})", "ih/2-(ih/zoom/2)")
    if move == "pan_right":
        return ("1.10", f"(iw-iw/zoom)*(0.35*on/{span})", "ih/2-(ih/zoom/2)")
    return ("1.04", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)")


def shot_filter(shot: dict, spec: dict, index: int, caption_png: pathlib.Path | None) -> str:
    """Ek shot ka filtergraph: blurred bed + plate ka camera move + caption overlay."""
    width, height = spec["size"]
    fps = int(spec.get("fps", 24))
    band = int(spec.get("plate_height", 608))
    seconds = float(shot["seconds"])
    frames = max(int(round(seconds * fps)), 2)
    move = shot.get("move", "push")
    if move not in MOVES:
        raise RenderError(f"shot {index}: move '{move}' '{move}' samajh nahi aaya ({', '.join(MOVES)})")
    zoom, xpos, ypos = _zoom_expr(move, frames)
    big_w = int(width * 2.6) // 2 * 2
    big_h = int(band * 2.6) // 2 * 2
    grain = int(spec.get("grain", 9))
    y0 = (height - band) // 2
    fade = float(spec.get("fade", 0.35))

    parts = [
        "[0:v]split=2[bgs][fgs]",
        (f"[bgs]scale={width}:{height}:force_original_aspect_ratio=increase,"
         f"crop={width}:{height},gblur=sigma=45,"
         f"eq=brightness={float(spec.get('bg_brightness', -0.04)):.2f}:saturation=0.7,noise=alls=6:allf=t,fps={fps},setsar=1[bg]"),
        (f"[fgs]scale={big_w}:{big_h}:flags=lanczos,"
         f"zoompan=z='{zoom}':d={frames}:x='{xpos}':y='{ypos}':"
         f"s={width}x{band}:fps={fps},setsar=1,"
         f"noise=alls={grain}:allf=t+u,vignette=PI/5,"
         f"eq=contrast=1.08:saturation=0.82[fg]"),
        f"[bg][fg]overlay=x=0:y={y0}:shortest=1[layered]",
    ]
    tail = "[layered]"
    if caption_png is not None:
        parts.append(f"[1:v]format=rgba,"
                     f"fade=t=in:st=0:d={fade:.2f}:alpha=1,"
                     f"fade=t=out:st={max(seconds - fade, 0):.2f}:d={fade:.2f}:alpha=1[cap]")
        parts.append("[layered][cap]overlay=x=0:y=0:shortest=1[captioned]")
        tail = "[captioned]"
    parts.append(f"{tail}fade=t=in:st=0:d={fade:.2f},"
                 f"fade=t=out:st={max(seconds - fade, 0):.2f}:d={fade:.2f},"
                 f"format=yuv420p[v]")
    return ";".join(parts)


def render_shot(shot: dict, spec: dict, index: int, out: pathlib.Path,
                ffmpeg: str, work: pathlib.Path) -> pathlib.Path:
    fps = int(spec.get("fps", 24))
    seconds = float(shot["seconds"])
    caption = (shot.get("caption") or "").strip()
    caption_png = (make_caption_png(caption, spec, work / f"cap{index:02d}.png")
                   if caption else None)
    graph = shot_filter(shot, spec, index, caption_png)
    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", str(fps),
           "-t", f"{seconds:.3f}", "-i", str(shot["image"])]
    if caption_png is not None:
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{seconds:.3f}",
                "-i", str(caption_png)]
    cmd += ["-filter_complex", graph, "-map", "[v]",
            "-c:v", "libx264", "-crf", str(spec.get("crf", 18)), "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-r", str(fps), str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " | ".join(proc.stderr.strip().splitlines()[-3:])
        raise RenderError(f"shot {index} ({pathlib.Path(shot['image']).name}) render nahi hua: {tail}")
    return out


def concat_shots(parts: list[pathlib.Path], spec: dict, out: pathlib.Path,
                 ffmpeg: str) -> pathlib.Path:
    """Shots ko xfade (dissolve) se jodo — hard cut nahi, film jaisa flow."""
    fade = float(spec.get("xfade", 0.4))
    if len(parts) == 1:
        shutil.copyfile(parts[0], out)
        return out
    lengths = [probe(p, ffmpeg)["duration"] for p in parts]
    cmd = [ffmpeg, "-y"]
    for part in parts:
        cmd += ["-i", str(part)]
    chain, previous, running = [], "[0:v]", lengths[0]
    for index in range(1, len(parts)):
        offset = max(running - fade, 0)
        label = f"vx{index}"
        chain.append(f"{previous}[{index}:v]xfade=transition=fade:"
                     f"duration={fade}:offset={offset:.3f}[{label}]")
        previous = f"[{label}]"
        running = offset + lengths[index]
    cmd += ["-filter_complex", ";".join(chain), "-map", previous,
            "-c:v", "libx264", "-crf", str(spec.get("crf", 18)), "-preset", "veryfast",
            "-pix_fmt", "yuv420p", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " | ".join(proc.stderr.strip().splitlines()[-3:])
        raise RenderError("shots jodne me masla: " + tail)
    return out


# --------------------------------------------------------------------------- audio
def audio_graph(spec: dict, duration: float, cut_times: list[float]) -> str:
    """Designed bed: drone + rain + cut impacts + closing riser. Har layer ffmpeg se."""
    cfg = spec.get("audio") or {}
    fps = int(spec.get("fps", 24))
    rate = 48000
    layers, mixin = [], []
    slot = 0

    if cfg.get("drone", 0.5):
        gain = float(cfg.get("drone", 0.5))
        layers.append(f"sine=frequency=55:duration={duration:.3f}:sample_rate={rate}[d1]")
        layers.append(f"sine=frequency=82.5:duration={duration:.3f}:sample_rate={rate}[d2]")
        layers.append("[d1][d2]amix=inputs=2:normalize=0,tremolo=f=0.16:d=0.35,"
                      f"volume={gain:.2f}[drone]")
        mixin.append("[drone]")
        slot += 1

    if cfg.get("rain", 0.5):
        gain = float(cfg.get("rain", 0.5))
        layers.append(f"anoisesrc=color=pink:duration={duration:.3f}:sample_rate={rate}:"
                      f"amplitude=0.16[rn]")
        layers.append(f"[rn]highpass=f=320,lowpass=f=6200,volume={gain:.2f}[rain]")
        mixin.append("[rain]")
        slot += 1

    if cfg.get("impacts", True) and cut_times:
        for number, at in enumerate(cut_times[:6], 1):
            layers.append(f"sine=frequency=58:duration=0.55:sample_rate={rate}[i{number}]")
            layers.append(f"[i{number}]afade=t=out:st=0.05:d=0.5,volume=0.9,"
                          f"adelay={int(at * 1000)}|{int(at * 1000)}[imp{number}]")
            mixin.append(f"[imp{number}]")

    if cfg.get("pulse", 0.5):
        gain = float(cfg.get("pulse", 0.5))
        layers.append(f"aevalsrc='0.55*sin(2*PI*44*t)*exp(-6*mod(t\,1.2))'"
                      f":s={rate}:d={duration:.3f}[pl]")
        layers.append(f"[pl]volume={gain:.2f}[pulse]")
        mixin.append("[pulse]")

    if cfg.get("riser", True):
        start = max(duration - 2.2, 0.0)
        layers.append(f"anoisesrc=color=white:duration=2.2:sample_rate={rate}:amplitude=0.1[rs]")
        layers.append(f"[rs]highpass=f=600,lowpass=f=5200,"
                      f"afade=t=in:st=0:d=1.9,volume=0.55,adelay={int(start * 1000)}|"
                      f"{int(start * 1000)}[riser]")
        mixin.append("[riser]")

    voice = cfg.get("voice")
    if voice and pathlib.Path(voice).exists():
        layers.append("[0:a]volume=1.0,aresample=48000[vo]")
        mixin.append("[vo]")

    if not mixin:
        layers.append(f"anullsrc=channel_layout=stereo:sample_rate={rate}:duration={duration:.3f}[sil]")
        mixin.append("[sil]")

    layers.append("".join(mixin) + f"amix=inputs={len(mixin)}:normalize=0,"
                                   f"loudnorm=I=-16:TP=-1.5:LRA=11,"
                                   f"atrim=0:{duration:.3f},asetpts=N/SR/TB[aout]")
    return ";".join(layers), fps


def build_audio(spec: dict, duration: float, cut_times: list[float], out: pathlib.Path,
                ffmpeg: str) -> pathlib.Path:
    graph, _ = audio_graph(spec, duration, cut_times)
    voice = (spec.get("audio") or {}).get("voice")
    cmd = [ffmpeg, "-y"]
    if voice and pathlib.Path(voice).exists():
        cmd += ["-i", str(voice)]
    cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000:duration=0.1",
            "-filter_complex", graph, "-map", "[aout]",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " | ".join(proc.stderr.strip().splitlines()[-3:])
        raise RenderError("audio nahi bana: " + tail)
    return out


# --------------------------------------------------------------------------- entry
def load_spec(path: pathlib.Path) -> dict:
    import re
    spec = json.loads(pathlib.Path(path).read_text())
    base = pathlib.Path(path).parent
    shots = spec.get("shots") or []
    if not shots:
        raise RenderError("spec me koi shot nahi hai")
    for index, shot in enumerate(shots, 1):
        if not shot.get("image"):
            raise RenderError(f"shot {index}: 'image' missing")
        raw = pathlib.Path(shot["image"])
        if raw.is_absolute():
            image = raw
        else:
            # pehle spec ke folder se, phir repo root se (paths repo-relative likhna aasan hai)
            here = (base / raw).resolve()
            root = (pathlib.Path(__file__).resolve().parent.parent / raw).resolve()
            image = here if here.exists() else root
        if not image.exists():
            raise RenderError(f"shot {index}: image nahi mila — {image}")
        shot["image"] = str(image)
        shot["seconds"] = float(shot.get("seconds", 3.0))
        if shot["seconds"] <= 0.2:
            raise RenderError(f"shot {index}: seconds bahut kam hai")
    spec["size"] = [int(spec.get("size", [1080, 1920])[0]), int(spec.get("size", [1080, 1920])[1])]
    spec["fps"] = int(spec.get("fps", 24))
    spec["fade"] = float(spec.get("fade", 0.35))
    return spec


def render(spec_path: pathlib.Path, out: pathlib.Path, *, keep: pathlib.Path | None = None,
           ffmpeg: str | None = None) -> dict:
    ffmpeg = ffmpeg or which("ffmpeg")
    if not ffmpeg:
        raise RenderError("ffmpeg nahi mila")
    spec = load_spec(spec_path)
    started = time.time()
    work = pathlib.Path(keep) if keep else pathlib.Path(tempfile.mkdtemp(prefix="reel_"))
    work.mkdir(parents=True, exist_ok=True)
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    parts, log = [], []
    for index, shot in enumerate(spec["shots"], 1):
        part = work / f"shot{index:02d}.mp4"
        render_shot(shot, spec, index, part, ffmpeg, work)
        parts.append(part)
        log.append(f"shot {index}: {pathlib.Path(shot['image']).name} "
                   f"{shot['seconds']:.1f}s {shot.get('move', 'push')}")

    stitched = work / "stitched.mp4"
    concat_shots(parts, spec, stitched, ffmpeg)

    cuts, running = [], 0.0
    fade = float(spec.get("xfade", 0.4))
    for index, shot in enumerate(spec["shots"]):
        running += shot["seconds"] - (fade if index else 0)
        cuts.append(round(running, 3))
    total = round(running, 3)

    voiced = work / "bed.m4a"
    build_audio(spec, total, cuts[:-1], voiced, ffmpeg)

    master = work / "master.mp4"
    proc = subprocess.run([ffmpeg, "-y", "-i", str(stitched), "-i", str(voiced),
                           "-c:v", "copy", "-c:a", "copy", "-shortest",
                           "-movflags", "+faststart", str(master)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " | ".join(proc.stderr.strip().splitlines()[-3:])
        raise RenderError("master mux nahi hua: " + tail)
    shutil.copyfile(master, out)

    info = probe(out, ffmpeg)
    receipt = {
        "tool": VERSION, "reel": spec.get("id", "reel"), "title": spec.get("title"),
        "master": out.name, "info": info, "log": log,
        "seconds_rendered": round(time.time() - started, 1),
        "engine": "ffmpeg-cpu (no GPU, no network)",
        "audio": {"layers": [k for k in ("drone", "rain", "impacts", "riser", "voice")
                             if (spec.get("audio") or {}).get(k)],
                  "loudnorm": "I=-16:TP=-1.5:LRA=11"},
    }
    receipt_path = out.with_name(out.stem + "_receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reel_render", description=__doc__)
    parser.add_argument("spec", help="reel.json")
    parser.add_argument("--out", required=True, help="output master.mp4")
    parser.add_argument("--keep", help="intermediate files yahan rakho (debug)")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)
    try:
        receipt = render(pathlib.Path(args.spec), pathlib.Path(args.out),
                         keep=pathlib.Path(args.keep) if args.keep else None)
    except RenderError as exc:
        print("REEL FAIL:", exc)
        return 1
    info = receipt["info"]
    print(f"REEL OK  {info['name']}  {info['bytes'] / 1e6:.2f} MB  "
          f"{info['width']}x{info['height']}  {info['duration']}s  "
          f"md5={info['md5']}  ({receipt['seconds_rendered']}s render)")
    for line in receipt["log"]:
        print("  ·", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
