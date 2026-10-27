"""Contact sheet + a 2 s clip out of whatever the look test rendered."""
import pathlib
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
LOOK = ROOT / "render/look"
BUILD = ROOT / "build"
BUILD.mkdir(parents=True, exist_ok=True)
ff = imageio_ffmpeg.get_ffmpeg_exe()

frames = sorted(LOOK.glob("*.png"))
print("frames", len(frames), flush=True)
if not frames:
    sys.exit("no frames rendered")

thumbs = [Image.open(f).convert("RGB") for f in frames]
tw, th = thumbs[0].size
cols = 4
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
for i, im in enumerate(thumbs):
    sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
sheet.save(BUILD / "looktest_sheet.jpg", quality=92)
print("sheet", sheet.size, flush=True)

run = [f for f in frames if 223 <= int(f.stem) <= 279]
if run:
    first = int(run[0].stem)
    span = (int(run[-1].stem) - first + 1) / 30.0
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error",
                    "-framerate", "30", "-start_number", str(first),
                    "-i", str(LOOK / "%04d.png"),
                    "-ss", "7.40", "-t", f"{span:.3f}", "-i", str(BUILD / "score_48k.wav"),
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-shortest",
                    str(BUILD / "looktest_clip.mp4")], check=True)
    print("clip", span, flush=True)
