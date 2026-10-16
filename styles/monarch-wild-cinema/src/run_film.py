#!/usr/bin/env python3
"""run_film.py — build a Monarch Wild Cinema episode from a declarative plan.

    python3 src/run_film.py --plan projects/<slug>/PLAN.json \
                            --out-dir projects/<slug>/build \
                            [--vertical] [--crf 19] [--fast]

The plan is DATA. A03 (Architect) writes it, A05 (Craftsman) runs it, A07
(Warden) gates the output. No step requires editing this file.

Plan schema (all keys optional except `shots`):

{
  "episode": "MF-01",
  "look": "nocturne",                       # nocturne | first_light | archive | alarm
  "plates": "assets/plates",
  "audio": {
      "bed": {"drone": 0.20, "air": 0.05, "tension": 0.06},
      "cues": [{"at": 0.0, "cue": "impact", "gain": 1.0}],
      "auto_cues_from_transitions": true,
      "vo": ["../../04_VOICE/vo_01.mp3"],   # optional; omitted = music-led
      "target_i": -16.0
  },
  "shots": [
    {"id":"01","plate":"01_hook_charge.jpg","dur":4.0,"look":"nocturne",
     "depth":{"mode":"hybrid","rect":[0.18,0.16,0.86,0.98]},
     "cam":{"zoom":[0.03,0.085],"orbit":30,"roll":0.45,"ramp":"linear"},
     "fx":{"rays":0.22,"motes":80,"impact":[0.0],"shake":9,"flash":[0.0]},
     "transition_in":"hard",
     "type":[{"kind":"headline","text":"40 METRES.","accent_word":"40",
              "in":0.15,"out":3.4,"anim":"extrude_tilt"}]}
  ]
}
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from tabahi import core as C          # noqa: E402
from tabahi import film as FM         # noqa: E402
from tabahi import score as S         # noqa: E402
from tabahi import transitions as T   # noqa: E402


def auto_cues(shots: list[dict]) -> list[dict]:
    """One matched cue per transition kind, read from the same table the
    picture uses — so a cue can never drift away from its cut."""
    cues = []
    t = 0.0
    for i, s in enumerate(shots):
        kind = s.get("transition_in", "hard")
        cue = T.KINDS.get(kind, {}).get("cue")
        if cue and kind != "hard":
            cues.append({"at": round(t, 3), "cue": cue, "gain": 0.9})
        for at in (s.get("fx", {}) or {}).get("impact", []) or []:
            cues.append({"at": round(t + at, 3), "cue": "impact", "gain": 1.0})
        t += s["dur"]
    return cues


def build_score(plan: dict, total: float, out_dir: pathlib.Path) -> pathlib.Path:
    """Assemble the procedural score: beds + cues, true stereo at the source."""
    import numpy as np
    a = plan.get("audio", {}) or {}
    n = int((total + 2.0) * C.SR)
    bed = a.get("bed", {"drone": 0.20, "air": 0.05})
    buf = np.zeros((n, 2), np.float32)
    buf += S.bed_drone(n, level=float(bed.get("drone", 0.20)), width=float(bed.get("width", 1.0)))
    buf += S.bed_air(n, level=float(bed.get("air", 0.05)))
    buf += S.bed_shimmer(n, level=float(bed.get("shimmer", 0.05)),
                         per_second=float(bed.get("shimmer_per_second", 1.6)))
    buf += S.bed_pad(n, level=float(bed.get("pad", 0.05)),
                     root=float(bed.get("pad_root", 440.0)))
    if bed.get("tension"):
        buf += S.bed_tension(n, level=float(bed["tension"]))

    # spectral shaping: bass-heavy beds are the default failure of a synthesised
    # score, so the tilt is applied deterministically rather than dialled by ear
    buf = S.shape_spectrum(buf,
                           high_shelf_db=float(a.get("high_shelf_db", 7.0)),
                           shelf_hz=float(a.get("shelf_hz", 1600.0)),
                           low_cut_hz=float(a.get("low_cut_hz", 34.0)))

    cues = list(a.get("cues", []))
    if a.get("auto_cues_from_transitions", True):
        have = {round(c["at"], 2) for c in cues}
        cues += [c for c in auto_cues(plan["shots"]) if round(c["at"], 2) not in have]
    for c in cues:
        fn = S.CUES.get(c["cue"])
        if fn is None:
            continue
        S.add(buf, fn(), float(c.get("at", 0.0)),
              float(c.get("gain", 1.0)) * float(a.get("cue_scale", 1.0)))

    # gain structure: cue balance first, then saturation, then a strict
    # pre-master peak. A score whose crest is wider than the loudness target
    # allows cannot be fixed downstream (measured: 24.5 dB crest produced a
    # clipped 16-bit master that only looked like a successful loudness match).
    buf *= float(a.get("bed_drive", 1.0))
    buf = S.soft_clip(buf, drive=float(a.get("soft_clip", 1.0)))
    pre = float(a.get("pre_peak", 0.90))
    pk0 = float(np.abs(buf).max())
    if pk0 > 0:
        buf = buf * (pre / pk0)
    rms0 = float(np.sqrt((buf ** 2).mean()))
    C.say(f"  score crest: peak {pre:.2f} rms {rms0:.4f} "
          f"-> {20*np.log10(max(pre,1e-9)/max(rms0,1e-9)):.1f} dB "
          f"(needs <= {(20*np.log10(float(a.get('peak_guard',0.68))/0.133)):.1f} dB for -16 LUFS)")
    # The correlation target is NOT set here any more. MEASURED: the loudness
    # stage re-weights the correlation sum, so a score balanced here arrived at
    # the master 0.21 off target. balance is now the last step inside
    # score.solve_mix(), where it is applied after the gain and the limiter.
    peak = float(np.abs(buf).max())
    if peak > 0.92:
        buf *= 0.92 / peak
    path = out_dir / "score.wav"
    C.wav_write(path, buf)
    C.say(f"  score: {n/C.SR:.1f}s · {len(cues)} cues · {peak:.2f} pre-trim peak")
    return path


def _pickup(f, plan, out_dir, picture, args, plate_dir):
    """Score + mix + master + optional vertical, given an existing picture."""
    C.say("[2/4] score")
    score_path = build_score(plan, sum(s["dur"] for s in plan["shots"]), out_dir)
    C.say("[3/4] mix")
    voice_files = plan.get("audio", {}).get("vo", [])
    spans = None
    if voice_files:
        voice, spans = S.build_voice_track([pathlib.Path(v) for v in voice_files], out_dir)
    else:
        voice = score_path
    report = S.mix(voice, score_path, out_dir / "master.wav",
                   bed_gain=float(plan.get("audio", {}).get("mix_bed_gain", 0.42)),
                   target_i=float(plan.get("audio", {}).get("target_i", -16.0)),
                   target_corr=float(plan.get("audio", {}).get("target_corr", 0.575)),
                   peak_guard=float(plan.get("audio", {}).get("peak_guard", 0.68)),
                   has_voice=bool(voice_files))
    C.say("[4/4] master")
    master = FM.mux(picture, out_dir / "master.wav",
                    out_dir / f"{plan.get('episode','episode')}_MASTER.mp4", crf=args.crf,
                    preset=args.preset)
    st = S.stereo_report(master)
    bands = S.band_energy(master, spans)
    C.say(f"\n  master  {master}")
    C.say(f"  {master.stat().st_size/1e6:.2f} MB · {report.get('i_lufs')} LUFS "
          f"· LRA {report.get('lra')} · TP {report.get('true_peak')} dBTP "
          f"· decoded peak {report.get('decoded_peak_dbfs')} dBFS")
    C.say(f"  stereo  corr={st['lr_correlation']:.3f} side/mid={st['side_mid']:.3f} ({st['verdict']})")
    C.say("  bands   " + "  ".join(f"{k}:{v:.1f}%" for k, v in bands["whole"].items()))
    if args.vertical:
        # MEASURED: this call used to emit a SILENT 1080x1920 file - render_vertical
        # writes the picture-only pass, and nothing muxed master.wav into it. The
        # delivered vertical is the same film as the master, so it carries the same
        # mix (one master.wav, two containers). The silent file is removed.
        C.say("\n[+] vertical 9:16 cut (type re-laid out for the portrait frame)")
        sil = out_dir / f"{plan.get('episode','episode')}_VERTICAL_silent.mp4"
        vpath = out_dir / f"{plan.get('episode','episode')}_VERTICAL.mp4"
        FM.render_vertical(plan, sil, plate_dir=plate_dir)
        FM.mux(sil, out_dir / "master.wav", vpath, crf=args.crf, preset="medium")
        sil.unlink()
        C.say(f"  {vpath} ({vpath.stat().st_size/1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--vertical", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--limit-shots", type=int, default=0)
    ap.add_argument("--skip-picture", action="store_true",
                    help="reuse an existing picture.mp4 and rebuild score/mix/master only")
    args = ap.parse_args()

    t0 = time.time()
    plan_path = pathlib.Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text())
    out_dir = pathlib.Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    plate_dir = plan.get("plates")
    if plate_dir and not pathlib.Path(plate_dir).is_absolute():
        plate_dir = (plan_path.parent / plate_dir).resolve()
    else:
        plate_dir = C.PLATES

    shots = plan["shots"][: args.limit_shots] if args.limit_shots else plan["shots"]
    plan = {**plan, "shots": shots}
    total = float(sum(s["dur"] for s in shots))

    C.say(f"MONARCH WILD CINEMA — {plan.get('episode','episode')}")
    C.say(f"  {len(shots)} shots · {total:.1f}s · look={plan.get('look','nocturne')} "
          f"· {plan.get('size',[C.W,C.H])[0]}x{plan.get('size',[C.W,C.H])[1]}")

    # 1 · PICTURE
    f = FM.Film(plan, out_dir, plate_dir=plate_dir, size=tuple(plan.get("size", [C.W, C.H])))
    if args.skip_picture and (out_dir / "picture.mp4").exists():
        C.say("[1/4] picture — REUSED build/picture.mp4 (--skip-picture)")
        f.timeline = [{"id": s["id"], "dur": s["dur"]} for s in shots]
        picture = out_dir / "picture.mp4"
        C.say(f"  picture: {picture} ({picture.stat().st_size/1e6:.1f} MB)")
        C.say(f"[1/4] picture done")
        _pickup(f, plan, out_dir, picture, args, plate_dir)
        return
    C.say("[1/4] picture")
    # The picture master is an INTERMEDIATE: encoded near-lossless and cheap
    # (ultrafast) so the x264 worker never starves the renderer on this 2-core
    # box, then encoded for real exactly once at mux time. Measured: a medium
    # intermediate stole ~1.3 cores and halved the render rate.
    picture = f.render(out_dir / "picture.mp4", crf=12, preset="ultrafast")
    C.say(f"  picture: {picture} ({picture.stat().st_size/1e6:.1f} MB, {f.total_duration():.1f}s planned)")

    if args.no_audio:
        C.say(f"DONE (no audio) in {time.time()-t0:.0f}s")
        return

    # 2 · SCORE
    C.say("[2/4] score")
    score_path = build_score(plan, f.total_duration(), out_dir)

    # 3 · MIX
    C.say("[3/4] mix")
    voice_files = plan.get("audio", {}).get("vo", [])
    spans = None
    if voice_files:
        voice, spans = S.build_voice_track([pathlib.Path(v) for v in voice_files], out_dir)
    else:
        # music-led: the score becomes the "voice" input to the 2-pass chain so
        # the delivery loudness is still normalised to the same target
        voice = score_path
    report = S.mix(voice, score_path, out_dir / "master.wav",
                   bed_gain=float(plan.get("audio", {}).get("mix_bed_gain", 0.42)),
                   target_i=float(plan.get("audio", {}).get("target_i", -16.0)),
                   target_corr=float(plan.get("audio", {}).get("target_corr", 0.575)),
                   peak_guard=float(plan.get("audio", {}).get("peak_guard", 0.68)),
                   has_voice=bool(voice_files))

    # 4 · MUX + MEASURE
    C.say("[4/4] master")
    master = FM.mux(picture, out_dir / "master.wav", out_dir / f"{plan.get('episode','episode')}_MASTER.mp4",
                    crf=args.crf, preset=args.preset)
    v = FM.verify(master, expect_seconds=f.total_duration())
    st = S.stereo_report(master)
    bands = S.band_energy(master, spans)

    build = {"episode": plan.get("episode"), "shots": len(shots),
             "total_s": round(f.total_duration(), 3), "master": str(master),
             "master_mb": round(master.stat().st_size / 1e6, 2), "video": v,
             "loudness": report, "stereo": st, "bands": bands,
             "render_seconds": round(time.time() - t0, 1),
             "engine": "monarch-wild-cinema/tabahi"}
    C.write_json(out_dir / "BUILD.json", build)

    C.say(f"\n  master  {master}")
    C.say(f"  {build['master_mb']} MB · {v.get('duration_s')}s · {report.get('i_lufs')} LUFS "
          f"· LRA {report.get('lra')} · TP {report.get('true_peak')} dBTP "
          f"· decoded peak {report.get('decoded_peak_dbfs')} dBFS")
    C.say(f"  stereo  corr={st['lr_correlation']:.3f} side/mid={st['side_mid']:.3f} ({st['verdict']})")
    if bands.get("whole"):
        C.say("  bands   " + "  ".join(f"{k}:{v:.1f}%" for k, v in bands["whole"].items()))

    if args.vertical:
        # MEASURED: this call used to emit a SILENT 1080x1920 file - render_vertical
        # writes the picture-only pass, and nothing muxed master.wav into it. The
        # delivered vertical is the same film as the master, so it carries the same
        # mix (one master.wav, two containers). The silent file is removed.
        C.say("\n[+] vertical 9:16 cut (type re-laid out for the portrait frame)")
        sil = out_dir / f"{plan.get('episode','episode')}_VERTICAL_silent.mp4"
        vpath = out_dir / f"{plan.get('episode','episode')}_VERTICAL.mp4"
        FM.render_vertical(plan, sil, plate_dir=plate_dir)
        FM.mux(sil, out_dir / "master.wav", vpath, crf=args.crf, preset="medium")
        sil.unlink()
        C.say(f"  {vpath} ({vpath.stat().st_size/1e6:.1f} MB)")

    C.say(f"\nDONE in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
