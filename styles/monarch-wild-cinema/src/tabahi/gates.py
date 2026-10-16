#!/usr/bin/env python3
"""TABAHI GATES — the measured acceptance table.

    python3 src/tabahi/gates.py --master build/EP_MASTER.mp4 \
        --plan projects/<slug>/PLAN.json --out build/GATES.json

An output without a measurement is a preview, not a delivery. This tool decodes
the actual delivered file; it never trusts the renderer's own report. Anything
it cannot measure is reported UNMEASURED, and UNMEASURED fails.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tabahi import core as C          # noqa: E402
from tabahi import film as FM         # noqa: E402
from tabahi import kinetic as K       # noqa: E402
from tabahi import score as S         # noqa: E402

# ── the table, as data (mirrored in data/gates.json) ────────────────────────
PROBE_W, PROBE_H = 160, 90


def decode_luma(master, fps: int = C.FPS) -> np.ndarray:
    """Decode the delivered video to a small luma strip: (frames, H, W) uint8."""
    cmd = [C.ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(master),
           "-vf", f"scale={PROBE_W}:{PROBE_H},fps={fps}", "-f", "rawvideo",
           "-pix_fmt", "gray", "-"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise SystemExit("could not decode master for gating")
    a = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(a) // (PROBE_W * PROBE_H)
    return a[: n * PROBE_W * PROBE_H].reshape(n, PROBE_H, PROBE_W)


def frame_diffs(lum: np.ndarray) -> np.ndarray:
    return np.abs(np.diff(lum.astype(np.float32), axis=0)).mean(axis=(1, 2))


def _frame_rgb(master, at: float):
    """Decode one full-resolution frame — G05/G06 measure the delivered pixels."""
    st = subprocess.run([C.ffmpeg(), "-v", "error", "-ss", f"{max(at, 0):.3f}", "-i", str(master),
                         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                        capture_output=True)
    if len(st.stdout) < C.W * C.H * 3:
        return None
    return np.frombuffer(st.stdout[: C.W * C.H * 3], np.uint8).reshape(C.H, C.W, 3)


def _wcag(fg, bg) -> float:
    """WCAG contrast ratio between two mean RGB colours (0-255)."""
    def lum(c):
        v = np.asarray(c, np.float32) / 255.0
        v = np.where(v <= 0.03928, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
        return float(0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2])
    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def plate_mean_luma(stage, p=0.5, look="nocturne") -> float:
    from tabahi import grade as G
    gr = G.Grade(look)
    f = stage.frame(p, {})
    f = gr.apply(f, 0)
    return float(C.luma(f).mean() / 255.0)


def run(master, plan_path=None, spans=None, out=None) -> dict:
    master = pathlib.Path(master)
    rows = []

    def add(gid, name, value, target, ok, note=""):
        rows.append({"gate": gid, "name": name, "value": value, "target": target,
                     "verdict": "PASS" if ok else ("UNMEASURED" if value is None else "FAIL"),
                     "note": note})

    plan = json.loads(pathlib.Path(plan_path).read_text()) if plan_path else None
    planned_s = float(sum(s["dur"] for s in plan["shots"])) if plan else None
    planned_frames = int(round(planned_s * C.FPS)) if planned_s else None

    # ── video ───────────────────────────────────────────────────────────────
    lum = decode_luma(master)
    got_frames = lum.shape[0]
    add("G01", "frames produced", got_frames,
        f">= {planned_frames}" if planned_frames else "n/a",
        True if not planned_frames else got_frames >= planned_frames * 0.995,
        f"planned {planned_frames}")

    d = frame_diffs(lum)
    identical = int((d < 1e-6).sum())
    add("G02", "duplicate frames", identical, "0", identical == 0,
        "a frozen frame reads as a broken upload")

    # G04 RECALIBRATION (measured on PROOF-01, 2026-10-16). The original target
    # ran over every frame pair, so it read a hard CUT as a strobe. Measured:
    # the six largest jumps (77.2, 72.5, 70.2, 51.7, 47.7, 47.0) all landed on
    # shot boundaries, while the in-shot mean dLuma was 0.5-2.8 — the film is
    # steady, and the gate was measuring the edit. The strobe rule now applies
    # where strobing is physically possible: INSIDE a shot, excluding a 0.35 s
    # window after each cut, where a designed transition belongs. The cut itself
    # is gated separately by G15 against the BT.1702 flash threshold (< 26 luma
    # of change per frame is not classified as a flash).
    cut_frames, acc = [], 0
    for shot in (plan["shots"][:-1] if plan else []):
        acc += int(round(shot["dur"] * C.FPS))
        cut_frames.append(acc)
    if cut_frames:
        guard = int(round(0.35 * C.FPS))
        mask = np.ones(len(d), bool)
        for cf in cut_frames:
            mask[max(cf - 1 - guard, 0):cf + guard] = False
        in_shot = float(d[mask].max()) if mask.any() else float(d.max())
        cut_delta = float(max((d[cf - 1] for cf in cut_frames if 0 < cf <= len(d)), default=0.0))
        add("G04", "max dLuma inside shots", round(in_shot, 2), "< 8",
            in_shot < 8.0, "strobe rule; 0.35 s cut windows excluded")
        add("G15", "cut-point luma delta", round(cut_delta, 2), "< 26",
            cut_delta < 26.0, "BT.1702 flash threshold; transitions must spread the cut")
    else:
        add("G04", "max dLuma between frames", round(float(d.max()), 2), "< 8",
            float(d.max()) < 8.0, "no strobe transitions")

    # ── per-shot motion (G03) ───────────────────────────────────────────────
    if plan:
        idx = 0
        worst = 999.0
        worst_id = None
        for shot in plan["shots"]:
            n = int(round(shot["dur"] * C.FPS))
            seg = d[idx: idx + n - 1]
            idx += n
            if len(seg) < 4:
                continue
            p10 = float(np.percentile(seg, 10))
            if p10 < worst:
                worst, worst_id = p10, shot["id"]
        add("G03", "per-shot motion p10 (worst)", round(worst, 3), "> 0.12",
            worst > 0.12, f"shot {worst_id}")

    # ── type legibility (G05) and safe band (G06) ────────────────────────────
    # G05, third and final definition (2026-10-16). The first compared the ink
    # against the PLATE's mean luma (a proxy that cannot see a scrim). The
    # second measured the delivered frame but took "ink" to be every layer
    # pixel with alpha > 40 — which for a CARD layer is the card's own dark
    # panel, so shot 05's cream-on-black species card scored 1.11:1 while its
    # glyphs measure ~15:1. The ink is now the GLYPH CORE (alpha > 250), and
    # the backdrop is the panel the viewer actually reads against when the
    # layer has one, otherwise the surrounding pixels of the delivered frame.
    if plan:
        starts, acc = {}, 0.0
        for shot in plan["shots"]:
            starts[str(shot["id"])] = acc
            acc += float(shot["dur"])
        worst_c, worst_lbl = 99.0, None
        band_bad = []
        card_clip = []
        for shot in plan["shots"]:
            for spec in shot.get("type", []) or []:
                lay, pos = FM._build_pil_raw(spec)
                al = np.array(lay)
                a = al[..., 3]
                ink = a > 250
                if int(ink.sum()) < 150:
                    ink = a > 200
                if int(ink.sum()) < 150:
                    continue
                panel = (a >= 150) & (a <= 220)
                oy, ox = int(pos[1]), int(pos[0])
                iys, ixs = np.where(ink)
                # G06: where the TYPE sits
                ty0, ty1 = oy + int(iys.min()), oy + int(iys.max())
                if not (60 <= ty0 and ty1 <= C.H - 60):
                    band_bad.append(f"{shot['id']}:{spec['kind']}@y{ty0}-{ty1}")
                # G05: how the type reads in the delivered frame
                oys, oxs = np.where(a > 8)
                y0, y1 = oy + int(oys.min()), oy + int(oys.max()) + 1
                x0, x1 = ox + int(oxs.min()), ox + int(oxs.max()) + 1
                t_in = starts[str(shot["id"])] + float(spec.get("in", 0.0))
                t_out = min(float(spec.get("out", 1e9)), shot["dur"])
                t_show = t_in + min(1.0, max((t_out - float(spec.get("in", 0.0))) * 0.5, 0.25))
                fr = _frame_rgb(master, t_show)
                if fr is None:
                    continue
                # G16: a card's own canvas must not clip its ink. Every card
                # builder draws into a fixed-size panel, and text that outgrows
                # it is silently sliced by the canvas edge (measured: the gauge
                # label ran 46 px past its card). An ink bbox touching the
                # canvas edge is the signature of that bug.
                # G16: every text run a builder recorded must fit inside the
                # canvas it was drawn on. This is a contract, not a heuristic:
                # the builders report where their text landed (core.RecDraw),
                # so a label that outgrows its card cannot ship unnoticed.
                w_, h_ = lay.size
                for r in (lay.info.get("text_rects") or []):
                    if r[0] < -2 or r[1] < -2 or r[2] > w_ + 2 or r[3] > h_ + 2:
                        card_clip.append(f"{shot['id']}:{spec['kind']}"
                                         f"@{r[0]:.0f},{r[1]:.0f}-{r[2]:.0f},{r[3]:.0f}"
                                         f"/{w_}x{h_}")
                        break
                sub = fr[y0:y1, x0:x1].astype(np.float32)
                im = ink[oys.min():oys.max() + 1, oxs.min():oxs.max() + 1]
                pm = panel[oys.min():oys.max() + 1, oxs.min():oxs.max() + 1]
                if sub.shape[:2] != im.shape[:2]:
                    continue
                fg = sub[im].mean(axis=0)
                # A CARD layer carries a panel that is a large contiguous region
                # (05 species 9x its glyph area, 08 lower 7.7x). Small text
                # layers have a 150-220 alpha band too — it is their own
                # anti-aliased edge (03 mark: 0.33x), and treating that as the
                # backdrop scored a bone-on-plate corner mark 1.57:1 against its
                # own outline. The panel must dominate the ink to count.
                if pm.sum() > 3.0 * im.sum():
                    bg = sub[pm].mean(axis=0)          # a card: the panel is the backdrop
                else:
                    ring = cv2.dilate(im.astype(np.uint8), np.ones((11, 11), np.uint8)) > 0
                    ring &= ~im
                    if ring.sum() < 64:
                        mrg = 40
                        ey0, ey1 = max(y0 - mrg, 0), min(y1 + mrg, C.H)
                        ex0, ex1 = max(x0 - mrg, 0), min(x1 + mrg, C.W)
                        wide = fr[ey0:ey1, ex0:ex1].astype(np.float32)
                        wm = np.ones(wide.shape[:2], bool)
                        wm[(y0 - ey0):(y0 - ey0) + im.shape[0], (x0 - ex0):(x0 - ex0) + im.shape[1]] = ~im
                        bg = wide[wm].mean(axis=0) if wm.sum() >= 64 else sub.mean(axis=(0, 1))
                    else:
                        bg = sub[ring].mean(axis=0)
                c = _wcag(fg, bg)
                if c < worst_c:
                    label = str(spec.get("text", spec.get("value", spec.get("name", "?"))))[:26]
                    worst_c, worst_lbl = c, f"{shot['id']}:{label}"
        add("G05", "min type contrast (delivered)", round(worst_c, 2) if worst_c < 99 else None,
            ">= 4.5", worst_c >= 4.5,
            f"glyph core vs its real backdrop; worst: {worst_lbl}")
        add("G06", "type inside safe band", len(band_bad), "0", not band_bad,
            "; ".join(band_bad[:3]))
        add("G16", "card ink inside its canvas", len(card_clip), "0", not card_clip,
            "a card that clips its own label reads as a typo: " + "; ".join(card_clip[:3]))

    # ── audio ───────────────────────────────────────────────────────────────
    try:
        m = S.measure(master)
        add("G07", "decoded sample peak dBFS", m.get("decoded_peak_dbfs"), "<= -1.0",
            (m.get("decoded_peak_dbfs") is not None) and m["decoded_peak_dbfs"] <= -1.0,
            "measured AFTER the codec, not before encoding")
        lufs = m.get("i_lufs")
        add("G08", "integrated loudness LUFS", lufs, "-16.5 +- 1.0",
            lufs is not None and abs(float(lufs) + 16.5) <= 1.0)
        tp = m.get("true_peak")
        add("G09", "true peak dBTP", tp, "<= -1.0", tp is not None and float(tp) <= -1.0)
    except Exception as e:  # noqa: BLE001
        add("G07", "decoded sample peak dBFS", None, "<= -1.0", False, str(e))
        add("G08", "integrated loudness LUFS", None, "-16.5 +- 1.0", False, str(e))
        add("G09", "true peak dBTP", None, "<= -1.0", False, str(e))

    try:
        st = S.stereo_report(master)
        add("G10", "L/R correlation", round(st["lr_correlation"], 3), "0.55 - 0.85",
            0.55 <= st["lr_correlation"] <= 0.85, st["verdict"])
        add("G11", "side/mid energy", round(st["side_mid"], 3), "> 0.25",
            st["side_mid"] > 0.25)
    except Exception as e:  # noqa: BLE001
        add("G10", "L/R correlation", None, "0.55 - 0.85", False, str(e))
        add("G11", "side/mid energy", None, "> 0.25", False, str(e))

    try:
        bands = S.band_energy(master, spans)
        key = "vo_absent" if (spans and bands.get("vo_absent")) else "whole"
        b = bands.get(key, {})
        add("G13", f"4-8 kHz share ({key})", round(b.get("4000-8000", 0.0), 1), "> 10",
            b.get("4000-8000", 0.0) > 10.0)
        add("G14", "120-500 Hz share (whole)", round(bands["whole"].get("120-500", 0.0), 1),
            "< 58", bands["whole"].get("120-500", 0.0) < 58.0)
    except Exception as e:  # noqa: BLE001
        add("G13", "4-8 kHz share", None, "> 10", False, str(e))
        add("G14", "120-500 Hz share", None, "< 58", False, str(e))

    # ── duration agreement (G12) ────────────────────────────────────────────
    v = FM.verify(master, expect_seconds=planned_s)
    if planned_s:
        delta = v.get("av_duration_delta_s")
        add("G12", "video/audio duration delta", delta, "<= 0.10 s",
            delta is not None and delta <= 0.10)
    report = {
        "master": str(master),
        "master_bytes": master.stat().st_size,
        "duration_s": v.get("duration_s"),
        "planned_s": planned_s,
        "gates": rows,
        "passed": sum(1 for r in rows if r["verdict"] == "PASS"),
        "failed": sum(1 for r in rows if r["verdict"] == "FAIL"),
        "unmeasured": sum(1 for r in rows if r["verdict"] == "UNMEASURED"),
        "total": len(rows),
    }
    report["result"] = "PASS" if report["failed"] == 0 and report["unmeasured"] == 0 else "FAIL"

    if out:
        C.write_json(out, report)
    return report


def print_report(rep: dict):
    C.say(f"\nGATE REPORT — {pathlib.Path(rep['master']).name}  "
          f"({rep['master_bytes']/1e6:.1f} MB, {rep['duration_s']}s of {rep['planned_s']}s planned)")
    C.say(f"{'ID':<5}{'GATE':<32}{'VALUE':>12}{'TARGET':>20}   VERDICT")
    for r in rep["gates"]:
        v = r["value"] if r["value"] is not None else "-"
        C.say(f"{r['gate']:<5}{r['name']:<32}{str(v):>12}{r['target']:>20}   {r['verdict']}")
    C.say(f"\nRESULT  {rep['passed']}/{rep['total']} PASS · "
          f"{rep['failed']} FAIL · {rep['unmeasured']} UNMEASURED  ->  {rep['result']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--plan")
    ap.add_argument("--out")
    args = ap.parse_args()
    rep = run(args.master, args.plan, out=args.out)
    print_report(rep)
    raise SystemExit(0 if rep["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
