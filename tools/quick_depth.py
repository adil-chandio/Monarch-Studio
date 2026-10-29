#!/usr/bin/env python3
"""quick_depth — bina model, image se subject mask (parallax ke liye).

Asli depth (Depth-Anything) cloud me banti hai; yeh local fallback hai taake film aaj hi ban jaye.
Tareeqa: border ke rang se jitna door, utna "subject"; saath me center-weight. Halka feather.

python3 tools/quick_depth.py studio/films/personality-36/scenes
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter


def subject_mask(image_path: pathlib.Path, out_path: pathlib.Path) -> pathlib.Path:
    image = Image.open(image_path).convert("RGB")
    small = image.resize((96, 168), Image.LANCZOS)
    arr = np.asarray(small, dtype=np.float32) / 255.0
    height, width, _ = arr.shape

    border = np.concatenate([arr[0, :, :], arr[-1, :, :], arr[:, 0, :], arr[:, -1, :]], axis=0)
    background = np.median(border, axis=0)
    distance = np.sqrt(((arr - background) ** 2).sum(axis=2))

    yy, xx = np.mgrid[0:height, 0:width]
    cy, cx = height * 0.46, width * 0.5
    centre = 1.0 - np.sqrt(((xx - cx) / (width * 0.62)) ** 2 + ((yy - cy) / (height * 0.62)) ** 2)
    centre = np.clip(centre, 0, 1)

    score = 0.75 * (distance / (distance.max() + 1e-6)) + 0.25 * centre
    score = (score - score.min()) / (score.max() - score.min() + 1e-6)
    mask = Image.fromarray((score * 255).astype(np.uint8), mode="L")
    mask = mask.resize(image.size, Image.LANCZOS)
    mask = mask.filter(ImageFilter.GaussianBlur(18))
    mask.save(out_path)
    return out_path


def main(argv: list[str] | None = None) -> int:
    folder = pathlib.Path((argv or sys.argv[1:])[0])
    made = 0
    for image in sorted(folder.glob("s*.png")):
        if image.stem.endswith("_depth") or "-" in image.stem:
            continue
        target = image.with_name(f"{image.stem}_depth.png")
        if target.exists():
            continue
        subject_mask(image, target)
        print("depth:", target.name)
        made += 1
    print("made", made)
    return 0


if __name__ == "__main__":
    sys.exit(main())
