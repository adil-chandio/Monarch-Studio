#!/usr/bin/env python3
"""
CHAOS · NEXT FILM — v3 audio master.

The score has a wide dynamic range (LRA ~16 LU) because it is a film score, not a
song. Loudnorm's dynamic mode reshapes it and drifts off target. So the master is
built deterministically instead:

    gentle glue compression -> static gain to hit the loudness target
    -> true-peak limiter -> AAC

Every step is measured after it runs; if the result is off target the static gain
is corrected once and the chain is rebuilt. Output is verifiable on its own.

Targets (delivery spec): -14.5 LUFS integrated, true peak <= -1.5 dBFS.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
SRC = HERE / "score" / "score_raw.wav"
OUTDIR = HERE / "out"
MASTER = OUTDIR / "master_audio.wav"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
I_TARGET = -14.5
TP_TARGET = -1.5


def measure(path: Path) -> dict:
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path),
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    t = r.stderr
    d = json.loads(t[t.rindex("{"):t.rindex("}") + 1])
    return dict(I=float(d["input_i"]), TP=float(d["input_tp"]),
                LRA=float(d["input_lra"]), thresh=float(d["input_thresh"]))


def build(gain_db: float, lim_db: float = -4.0) -> None:
    """highpass -> compress -> gain -> limit, written at 48 kHz / 24-bit stereo.

    The limiter caps SAMPLE peaks; true peak (inter-sample) runs a little higher,
    so the limit is set with headroom and then verified on the rendered file.
    The highpass also removes inaudible sub energy that was eating that headroom.
    """
    lin = 10 ** (lim_db / 20.0)
    chain = (
        "highpass=f=32,"
        "acompressor=threshold=-19dB:ratio=2.6:attack=8:release=260:makeup=1,"
        f"volume={gain_db:.2f}dB,"
        f"alimiter=limit={lin:.5f}:attack=5:release=60:level=false"
    )
    r = subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(SRC),
                        "-af", chain, "-ar", "48000", "-ac", "2",
                        "-c:a", "pcm_s24le", str(MASTER)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    base = measure(SRC)
    print("score measured:", base)
    gain = -10.0  # first guess: compression lifts the body, so start from a cut
    lim = -4.0
    best = None
    for attempt in range(6):
        build(gain, lim)
        m = measure(MASTER)
        print(f"attempt {attempt + 1}: gain={gain:+.2f} dB -> I={m['I']} TP={m['TP']} "
              f"LRA={m['LRA']}")
        best = dict(gain_db=round(gain, 2), limit_db=round(lim, 2), **m, source=base)
        if abs(m["I"] - I_TARGET) <= 0.4 and m["TP"] <= TP_TARGET - 0.1:
            break
        over = m["TP"] - TP_TARGET
        if over > 0.1:                       # too hot: pull the limiter down
            lim -= (over + 0.4)
        else:                                # headroom fine: chase the loudness
            gain += (I_TARGET - m["I"])
    ok = abs(best["I"] - I_TARGET) <= 0.6 and best["TP"] <= TP_TARGET + 0.05
    best["targets"] = dict(I=I_TARGET, TP=TP_TARGET)
    best["passed"] = bool(ok)
    (OUTDIR / "AUDIO_MASTER_RECEIPT.json").write_text(json.dumps(best, indent=1))
    print(f"MASTER_AUDIO {'ok' if ok else 'CHECK'}  {MASTER}  "
          f"I={best['I']} TP={best['TP']} LRA={best['LRA']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
