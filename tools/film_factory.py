#!/usr/bin/env python3
"""film_factory — ek master se poori "launch kit": teaser, cover, subtitles, sheet, packaging.

Owner ko ek run me sirf film nahi milti — upload ke liye taiyar cheezein milti hain:

  teaser_11s.mp4   9:16 hook cut (Reels/Shorts/TikTok ke liye) — asli clips se, slideshow nahi
  cover.jpg        1080x1920 thumbnail, chalk+gold type (styles/ authority se)
  subtitles.srt    scene captions, waqt ke sath (koi manual typing nahi)
  contact.png      12 scenes ka sheet — ek nazar me poori film
  kit.md           title, hook, hashtags, beat sheet — copy-paste caption
  premiere.json    kya bana, kitna bada, kitne scene (receipt)

Kaam:
  python3 tools/film_factory.py --master master.mp4 --clips clips/ --out kit/
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

SPEC = ROOT / "studio/films/stick-i2v/film/film_clips.json"
VOICE = ROOT / "studio/films/personality-t2v/voice"
FONTS = ROOT / "styles/monarch-stickman-animation/fonts"

TEASER_PICKS = ("k01", "k03", "k07", "k12")
TEASER_SECONDS = {"k01": 2.2}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise SystemExit("ffmpeg nahi mila")
    return found


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("cmd fail: " + " ".join(cmd[:4]) + "\n" + proc.stderr[-600:])
    return proc


# --------------------------------------------------------------------------- #
# spec helpers
# --------------------------------------------------------------------------- #

def base_spec(clips_dir: pathlib.Path) -> dict:
    spec = json.loads(SPEC.read_text())
    spec["clips"] = str(clips_dir)
    spec["voice_dir"] = str(VOICE)
    have = {p.stem for p in clips_dir.glob("*.mp4")}
    spec["scenes"] = [s for s in spec["scenes"] if s["id"] in have]
    return spec


def srt_time(t: float) -> str:
    h, rem = divmod(max(t, 0.0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


# --------------------------------------------------------------------------- #
# 1 · teaser
# --------------------------------------------------------------------------- #

def teaser(spec: dict, out: pathlib.Path, picks: tuple[str, ...] = TEASER_PICKS) -> pathlib.Path | None:
    """Hook cut: pehla scene + 3 sabse strong beats, bade captions, tez fade."""
    import clip_film

    order = [s for p in picks for s in spec["scenes"] if s["id"] == p]
    if len(order) < 2:
        order = spec["scenes"][:4]
    if len(order) < 2:
        log("teaser skip — 2 se kam clips")
        return None

    spec = json.loads(json.dumps(spec))                      # deep copy
    keep = {s["id"] for s in order}
    spec["scenes"] = [dict(s, seconds=TEASER_SECONDS.get(s["id"], 3.0)) for s in order if s["id"] in keep]
    spec.update({"fade": 0.14, "caption_size": 64, "caption_y": 0.64, "grade": "none",
                 "crf": 22, "grain": 4})
    spec["audio"] = {"drone": 0.30, "pad": 0.20, "pulse": 0.30, "riser": True, "hiss": 0.05}

    out.parent.mkdir(parents=True, exist_ok=True)
    spec_path = out.parent / "spec_teaser.json"
    spec_path.write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    log(f"teaser: {len(spec['scenes'])} beats ({', '.join(s['id'] for s in spec['scenes'])})")
    clip_film.render(spec_path, out)
    spec_path.unlink(missing_ok=True)
    return out


# --------------------------------------------------------------------------- #
# 2 · cover
# --------------------------------------------------------------------------- #

def _font(name: str, size: int):
    from PIL import ImageFont

    path = FONTS / name
    if not path.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size)


def _wrap(draw, text: str, font, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        probe = (line + " " + word).strip()
        if draw.textlength(probe, font=font) <= width or not line:
            line = probe
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def cover(master: pathlib.Path, out: pathlib.Path, title: str, sub: str = "36s · 9:16 · AI film") -> pathlib.Path:
    """Master ke ek asli frame par chalk+gold type — thumbnail jo feed me rukta hai."""
    from PIL import Image, ImageDraw, ImageFilter

    ff = ffmpeg_bin()
    frame = out.parent / "_cover_frame.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    run([ff, "-y", "-ss", "1.2", "-i", str(master), "-frames:v", "1", str(frame)])

    img = Image.open(frame).convert("RGB")
    w, h = img.size

    # neeche ka gradient — text padhne ke liye (silhouette ko chhoota nahi)
    shade = Image.new("L", (1, h))
    for y in range(h):
        t = max(0.0, (y / h - 0.42) / 0.58)
        shade.putpixel((0, y), int(232 * (t ** 1.35)))
    grad = shade.resize((w, h))
    img = Image.composite(Image.new("RGB", (w, h), (6, 6, 8)), img, grad)

    draw = ImageDraw.Draw(img)
    gold = (240, 190, 92)
    chalk = (238, 236, 230)

    # upar: studio stamp
    stamp = _font("Montserrat-VF.ttf", 26)
    draw.text((56, 64), "M O N A R C H   S T U D I O", font=stamp, fill=(*gold, 220))

    # title — hand type, 2-3 lines, gold underline
    size = 118
    font = _font("PermanentMarker.ttf", size)
    lines = _wrap(draw, title.upper(), font, w - 200)
    while len(lines) > 3 and size > 64:
        size -= 12
        font = _font("PermanentMarker.ttf", size)
        lines = _wrap(draw, title.upper(), font, w - 200)

    line_h = int(size * 1.12)
    y = h - 400 - (len(lines) - 1) * line_h

    # art ke andar bhi apna text hota hai — is liye title ke peeche halka plate,
    # taake do text ek doosre par na chadhein (feed me saaf padhe).
    # neeche ka art halka blur — uske andar jo text chapa hai woh title se nahi takraye
    blur_top = max(0, y - 120)
    band = img.crop((0, blur_top, w, h)).filter(ImageFilter.GaussianBlur(26))
    ramp = Image.new("L", (w, h - blur_top), 255)
    rd = ImageDraw.Draw(ramp)
    for i in range(110):                                  # dheemi shuruaat, koi seam nahi
        rd.line([(0, i), (w, i)], fill=int(255 * i / 110))
    img.paste(band, (0, blur_top), ramp)

    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle([40, y - 46, w - 40, y + line_h * len(lines) + 118],
                         radius=28, fill=(6, 6, 9, 148))
    img = Image.alpha_composite(img.convert("RGBA"), plate).convert("RGB")
    draw = ImageDraw.Draw(img)

    for line in lines:
        draw.text((70, y), line, font=font, fill=chalk)
        y += line_h

    draw.rectangle([70, y + 8, 70 + 150, y + 18], fill=gold)
    meta = _font("Montserrat-VF.ttf", 30)
    draw.text((70, y + 40), sub, font=meta, fill=(212, 208, 198))

    # halka vignette + grain, taake feed me flat na lage
    vig = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-w * 0.35, -h * 0.18, w * 1.35, h * 1.18], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    img = Image.composite(img, Image.new("RGB", (w, h), (0, 0, 0)), vig)

    img.save(out, quality=92, optimize=True)
    frame.unlink(missing_ok=True)
    return out


# --------------------------------------------------------------------------- #
# 3 · subtitles + sheet + kit
# --------------------------------------------------------------------------- #

def subtitles(spec: dict, out: pathlib.Path) -> pathlib.Path:
    lines, t = [], 0.0
    for i, scene in enumerate(spec["scenes"], 1):
        dur = float(scene.get("seconds") or 3.0)
        text = (scene.get("caption") or scene.get("kicker") or scene["id"]).strip()
        lines += [str(i), f"{srt_time(t)} --> {srt_time(t + dur - 0.05)}", text, ""]
        t += dur
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def contact(spec: dict, out: pathlib.Path, cols: int = 4) -> pathlib.Path | None:
    """Har scene ka asli pehla frame — poori film ek image me."""
    from PIL import Image, ImageDraw

    ff = ffmpeg_bin()
    scenes = spec["scenes"]
    if not scenes:
        return None
    tw, th = 270, 480
    rows = (len(scenes) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (8, 8, 10))
    label = _font("Montserrat-VF.ttf", 22)
    for i, scene in enumerate(scenes):
        clip = pathlib.Path(spec["clips"]) / (scene.get("clip") or f"{scene['id']}.mp4")
        if not clip.exists():
            continue
        shot = out.parent / f"_{scene['id']}.png"
        run([ff, "-y", "-ss", "0.4", "-i", str(clip), "-frames:v", "1",
             "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}",
             str(shot)], check=False)
        if not shot.exists():
            continue
        tile = Image.open(shot).convert("RGB")
        tile = tile.resize((tw, th))
        d = ImageDraw.Draw(tile)
        d.rectangle([0, 0, tw, 30], fill=(0, 0, 0))
        d.text((8, 4), scene["id"], font=label, fill=(240, 190, 92))
        sheet.paste(tile, ((i % cols) * tw, (i // cols) * th))
        shot.unlink(missing_ok=True)
    sheet.save(out, quality=90, optimize=True)
    return out


def kit(out: pathlib.Path, title: str, spec: dict, files: dict) -> pathlib.Path:
    beats = "\n".join(f"{i}. **{s.get('kicker', '')}** — {s.get('caption', '')}  ·  {s.get('seconds', 3.0)}s"
                      for i, s in enumerate(spec["scenes"], 1))
    total = sum(float(s.get("seconds") or 3.0) for s in spec["scenes"])
    lines = "\n".join(f"- `{k}` — {v}" for k, v in files.items() if v)
    text = f"""# {title}

**Duration:** {total:.1f}s · **Format:** 1080x1920 (9:16) · **Scenes:** {len(spec['scenes'])}

## Hook (pehli line)
> {spec['scenes'][0].get('caption', title) if spec['scenes'] else title}

## Caption (copy-paste)
{title.lower()} — {spec['scenes'][1].get('caption', '') if len(spec['scenes']) > 1 else ''}
5 aadatein, 36 second. Save kar lo.

#personality #confidence #growth #discipline #monarch #aifilm #shorts

## Beat sheet
{beats}

## Files
{lines}
"""
    out.write_text(text, encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def build(master: pathlib.Path, clips: pathlib.Path, out: pathlib.Path,
          title: str, picks: tuple[str, ...] = TEASER_PICKS) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    spec = base_spec(clips)
    if not spec["scenes"]:
        raise SystemExit(f"koi clip nahi mila: {clips}")

    got: dict[str, str] = {}
    try:
        t = teaser(spec, out / "teaser_11s.mp4", picks)
        got["teaser_11s.mp4"] = f"{t.stat().st_size / 1e6:.1f} MB" if t else ""
    except Exception as exc:                                   # noqa: BLE001
        log(f"teaser FAIL: {type(exc).__name__}: {str(exc)[:160]}")
    for name, fn in (("cover.jpg", lambda: cover(master, out / "cover.jpg", title)),
                     ("subtitles.srt", lambda: subtitles(spec, out / "subtitles.srt")),
                     ("contact.png", lambda: contact(spec, out / "contact.png"))):
        try:
            got[name] = str(fn())
        except Exception as exc:                               # noqa: BLE001
            log(f"{name} FAIL: {type(exc).__name__}: {str(exc)[:160]}")
    try:
        kit(out / "kit.md", title, spec, got)
        got["kit.md"] = str(out / "kit.md")
    except Exception as exc:                                   # noqa: BLE001
        log(f"kit FAIL: {type(exc).__name__}: {str(exc)[:160]}")

    receipt = {"title": title, "master": str(master), "scenes": len(spec["scenes"]),
               "kit": {k: v for k, v in got.items()}, "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    (out / "premiere.json").write_text(json.dumps(receipt, indent=1, ensure_ascii=False))
    return receipt


def card(receipt: dict) -> None:
    try:
        title = receipt["title"][:34]
        lines = ["", "  🎬  PREMIERE — " + title,
                 f"  {receipt['scenes']} scenes · launch kit ready", "  " + "─" * 44]
        for name, val in receipt["kit"].items():
            if val:
                size = val if not val.startswith("/") else ""
                lines.append(f"  ✓  {name}" + (f"  ·  {size}" if size else ""))
        lines.append("  " + "─" * 44)
        print("\n".join(lines), flush=True)
    except Exception:                                          # noqa: BLE001
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="film_factory")
    ap.add_argument("--master", required=True)
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Powerful Personality")
    ap.add_argument("--picks", default=",".join(TEASER_PICKS))
    args = ap.parse_args(argv)

    receipt = build(pathlib.Path(args.master), pathlib.Path(args.clips), pathlib.Path(args.out),
                    args.title, tuple(p.strip() for p in args.picks.split(",") if p.strip()))
    card(receipt)
    print(json.dumps(receipt["kit"], indent=1, ensure_ascii=False))
    return 0 if receipt["kit"].get("subtitles.srt") else 1


if __name__ == "__main__":
    sys.exit(main())
