#!/usr/bin/env python3
"""make_film_notebook — owner ke liye ek-tap notebook (Colab + Kaggle, dono par chalti hai).

Notebook generated artifact hai: source yahi script hai. Isay badlo, phir
`python3 tools/make_film_notebook.py` chala kar notebooks/Monarch_Film_OneTap.ipynb dobara banao.
CI (`film-selftest` workflow) check karta hai ke notebook aur script drift na karein.

Owner ka flow: link kholo -> Run all. Bas.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "Monarch_Film_OneTap.ipynb"
BRANCH = "arena/3d8cfad7-monarch-studio"
REPO = "https://github.com/adil-chandio/Monarch-Studio"


def md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(True)}


def code(src: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": src.splitlines(True)}


def build() -> dict:
    cells = [
        md(f"""# Monarch · "Powerful Personality" — stickman film (36 s, 9:16)

**Sirf ek tap: `Runtime → Run all`** (Colab par pehle `Runtime → Change runtime type → T4 GPU`).
Kaggle par: `Settings → Accelerator → GPU T4`, `Internet → On`.

Yeh notebook kya karta hai:
1. is repo (`{BRANCH}`) ko clone karta hai,
2. `tools/kaggle_stick_film.py` chalata hai — 12 locked stickman keyframes se **asli video model**
   (Wan 2.2 image-to-video; T4 par na chale to LTX-Video 2B) se clips banata hai,
3. un clips par **captions + voice + sound** laga kar 1080×1920 master jodta hai,
4. video yahin notebook me dikhata hai — `monarch_stick_36s.mp4`.

Session toot jaye to dobara `Run all`: jo scene ban chuki hai, woh skip ho jayegi.
"""),
        md("### 1 · Setup (repo clone)"),
        code(f'''#@title 1 · Repo clone / update
import pathlib, subprocess

BRANCH = "{BRANCH}"
REPO = "{REPO}"
base = pathlib.Path("/kaggle/working") if pathlib.Path("/kaggle/working").is_dir() else pathlib.Path("/content")
repo = base / "repo"

if (repo / "tools/kaggle_stick_film.py").exists():
    subprocess.run(["git", "-C", str(repo), "fetch", "--depth", "1", "origin", BRANCH], check=False)
    subprocess.run(["git", "-C", str(repo), "reset", "--hard", f"origin/{{BRANCH}}"], check=False)
else:
    subprocess.run(["git", "clone", "--depth", "1", "-b", BRANCH, REPO, str(repo)], check=True)

head = subprocess.run(["git", "-C", str(repo), "log", "--oneline", "-1"],
                      capture_output=True, text=True).stdout.strip()
print("repo:", repo)
print("commit:", head)
'''),
        md("""### 2 · GPU check (yeh pass hona chahiye)"""),
        code("""#@title 2 · GPU check
import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE")
if not torch.cuda.is_available():
    raise SystemExit("GPU on karo, phir Run all: Colab Runtime > Change runtime type > T4 GPU "
                     "| Kaggle Settings > Accelerator > GPU T4")
p = torch.cuda.get_device_properties(0)
print("VRAM:", round(p.total_memory / 1e9, 1), "GB | bf16:", torch.cuda.is_bf16_supported())
"""),
        md("""### 3 · Film banao (12 scenes — sabse lamba step)

Pehla run me models download honge (Wan ~10 GB) — 6–10 min lag sakte hain. Uske baad har scene
ka apna time. Total 2–4 ghante (GPU par depend). Beech me session toot jaye to cell dobara chala do.
"""),
        code("""#@title 3 · Render 12 scenes + master
import subprocess, sys

out = base / "stick"
cmd = [sys.executable, str(repo / "tools/kaggle_stick_film.py"),
       "--out", str(out), "--final", str(base)]
print(" ".join(cmd), flush=True)
proc = subprocess.run(cmd)
print("exit code:", proc.returncode)
"""),
        md("""### 3b · (optional) Sirf ek scene ka test — pehle yeh chala kar tasalli

Pehli dafa poora run karne se pehle ek scene dekh lo (~10–15 min). Theek lage to **cell 3** chala do.
"""),
        code("""#@title 3b · Sirf ek scene (optional)
import subprocess, sys

scene = "k01"          # k01..k12
cmd = [sys.executable, str(repo / "tools/kaggle_stick_film.py"),
       "--out", str(base / "stick"), "--final", str(base / "test"), "--only", scene]
print(" ".join(cmd), flush=True)
subprocess.run(cmd)
"""),
        md("### 4 · Video dekho"),
        code("""#@title 4 · Master dikhao
import pathlib
from IPython.display import Video, display

master = pathlib.Path(base) / "monarch_stick_36s.mp4"
if master.exists():
    print(master, round(master.stat().st_size / 1e6, 1), "MB")
    display(Video(str(master), embed=False, width=420))
else:
    single = sorted(pathlib.Path(base / "test").glob("*.mp4")) if (pathlib.Path(base) / "test").exists() else []
    print("poora master nahi bana. Jo clips bani hain:", single or "abhi koi nahi")
"""),
        md("### 5 · (Colab) Drive me save"),
        code("""#@title 5 · Drive me copy (Colab)
import pathlib, shutil

master = pathlib.Path(base) / "monarch_stick_36s.mp4"
if not master.exists():
    print("master nahi bana — pehle cell 3 chalao")
else:
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        dst = pathlib.Path('/content/drive/MyDrive/Monarch-T2V'); dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(master, dst / master.name)
        receipts = pathlib.Path(base) / "stick" / "receipts.json"
        if receipts.exists():
            shutil.copy2(receipts, dst / "stick_receipts.json")
        print("Drive me:", dst / master.name)
    except Exception as exc:
        print("Drive copy skip:", type(exc).__name__, exc)
"""),
    ]
    return {"cells": cells, "metadata": {
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU"}, "nbformat": 4, "nbformat_minor": 5}


def main() -> int:
    nb = build()
    text = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if not OUT.exists():
            print(f"MISSING: {OUT.relative_to(ROOT)} — `python3 tools/make_film_notebook.py` chalao")
            return 1
        if json.loads(OUT.read_text()) != nb:
            print(f"DRIFT: {OUT.relative_to(ROOT)} purana hai — "
                  f"`python3 tools/make_film_notebook.py` chalao")
            return 1
        print("notebook up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"likha: {OUT.relative_to(ROOT)} ({len(nb['cells'])} cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
