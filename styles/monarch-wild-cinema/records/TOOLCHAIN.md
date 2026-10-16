# WF-07 · toolchain and exact commands

## Environment

| | |
|---|---|
| Python | 3.11 (`/home/user/.venv`) — the system interpreter is PEP 668-restricted, always use the venv |
| pillow | 12.3.0 |
| numpy | 2.4.6 |
| opencv-python-headless | 5.0.0 |
| imageio | 2.38.1 |
| imageio-ffmpeg | bundled **ffmpeg 7.0.2** binary (`imageio_ffmpeg.get_ffmpeg_exe()`); there is **no system ffmpeg**, so all calls go through `tabahi.core.ffmpeg()` |
| Fonts | `assets/fonts/`: Anton-Regular, BarlowCondensed-Medium(Italic), Montserrat-VF, PermanentMarker (+ OFL texts) |
| Hardware measured on | 2 vCPU, no GPU |

## Commands

```bash
# full build (picture + score + mix + master + measurement)
/home/user/.venv/bin/python src/run_film.py \
    --plan projects/proof-01-trailer/PLAN.json \
    --out-dir projects/proof-01-trailer/build \
    --crf 19 --preset medium

# audio-only rebuild (~85 s) reusing an existing picture
/home/user/.venv/bin/python src/run_film.py --plan … --out-dir … --skip-picture

# gates (16, measured on the delivered master)
/home/user/.venv/bin/python src/tabahi/gates.py \
    --master projects/proof-01-trailer/delivery/PROOF-01-TRAILER_MASTER.mp4 \
    --plan projects/proof-01-trailer/PLAN.json \
    --out projects/proof-01-trailer/reports/GATES.json

# thumbnails (5 concepts + 213×120 feed tests + contact sheet)
/home/user/.venv/bin/python src/tabahi/thumbs.py --plates assets/plates \
    --out-dir projects/proof-01-trailer/build/thumbs

# vertical 9:16 cut (camera + grade, subject-tracked crop), then mux the same mix
python - <<'PY'
import sys, json, pathlib; sys.path.insert(0, "src")
from tabahi import film as FM
plan = json.loads(pathlib.Path("projects/proof-01-trailer/PLAN.json").read_text())
FM.vertical_path(plan, "projects/proof-01-trailer/delivery/PROOF-01-TRAILER_VERTICAL.mp4",
                 plate_dir="assets/plates")
PY
```

## Measured cost

| Step | Value |
|---|---|
| Depth per unique plate | ≈ 2.5 s |
| Picture (930 frames, 1920×1080) | **535 s** including score, mix, mux and measurement → **0.58 s/frame** |
| Vertical (930 frames, 1080×1920) | 302 s silent + 115 s mux |
| Thumbnails | ≈ 17 s |
| Audio-only rebuild | ≈ 85 s |

## Known hard constraints

- `plan["plates"]` is resolved **relative to the plan file's directory**, not the process CWD.
  Never pass a CWD-relative plate path (`film.vertical_path(…, plate_dir=…)` exists for this).
- `-ar 48000` on every audio encode (MF-01 once shipped 96 kHz by accident).
- The picture intermediate is deliberately `crf 12 / ultrafast`: a `medium` intermediate steals a
  core from the renderer on this 2-core box and roughly halves the render rate.
