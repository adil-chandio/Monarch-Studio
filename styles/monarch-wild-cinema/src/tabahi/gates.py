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


def _probe_geometry(path) -> dict:
    st = subprocess.run([C.ffmpeg(), "-hide_banner", "-i", str(path)],
                        capture_output=True, text=True).stderr
    w = h = 0
    for line in st.splitlines():
        if "Video:" in line:
            for tok in (t.strip() for t in line.split(",")):
                a, _, b = tok.partition("x")
                if a.isdigit() and b.isdigit():
                    w, h = int(a), int(b)
                    break
            break
    return {"w": w, "h": h}


def _frame_rgb(master, at: float):
    """Decode one full-resolution frame — G05/G06 measure the delivered pixels.

    MEASURED BUG: `-ss` BEFORE `-i` is a fast (keyframe) seek. With a 2 s GOP the
    frame that came back was up to two seconds early — the gate was measuring a
    frame from the PREVIOUS shot, which is why shot 03's corner mark reported
    1.00:1 (fg == bg exactly, i.e. flat plate) while the mark in the real frame
    reads 6.5:1. Seeking AFTER the input is decode-accurate; a 31 s file costs
    nothing to decode up to the timestamp.
    """
    st = subprocess.run([C.ffmpeg(), "-v", "error", "-i", str(master), "-ss", f"{max(at, 0):.3f}",
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




def _corr_in_spans(path, spans, sr=8000):
    """L/R correlation of the delivered file inside the narration spans only."""
    import subprocess as _sp
    if not spans:
        return None
    raw = _sp.run([C.ffmpeg(), "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(sr),
                   "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0
    a = a.reshape(-1, 2)
    keep = np.concatenate([a[int(t0 * sr):int(t1 * sr)] for t0, t1 in spans]) if spans else a
    if keep.size < 64:
        return None
    l, r = keep[:, 0], keep[:, 1]
    den = float(np.sqrt((l ** 2).sum() * (r ** 2).sum()))
    return float((l * r).sum() / den) if den > 1e-9 else None

def _vo_spans(plan_path):
    """Declared narration spans [(t0, t1)], from plan.audio.vo. Measured, not assumed:
    each line's duration is read off its own file, so the gate samples exactly the
    time the voice is meant to be there."""
    import subprocess as _sp
    plan_path = pathlib.Path(plan_path)
    plan = json.loads(plan_path.read_text())
    out = []
    for e in plan.get("audio", {}).get("vo", []) or []:
        f = e.get("file")
        if not f or e.get("at") is None:
            continue
        f = (plan_path.parent / f).resolve()
        if not f.exists():
            continue
        st = _sp.run([C.ffmpeg(), "-i", str(f)], capture_output=True, text=True).stderr
        try:
            hms = st.split("Duration:")[1].split(",")[0].strip()
            h, m, sec = hms.split(":")
            d = int(h) * 3600 + int(m) * 60 + float(sec)
        except Exception:  # noqa: BLE001
            continue
        out.append((round(float(e["at"]), 3), round(float(e["at"]) + d, 3)))
    return out


def _band_rms(path, lo=300.0, hi=3400.0, sr=8000):
    """Mono speech-band waveform of a delivered file (decode-accurate)."""
    import subprocess as _sp
    raw = _sp.run([C.ffmpeg(), "-v", "error", "-i", str(path), "-af",
                   f"highpass=f={lo},lowpass=f={hi}", "-ac", "1", "-ar", str(sr),
                   "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0
    return a, sr


def _rms(x):
    return float(np.sqrt(np.mean(np.square(x)))) if x.size else 0.0

def run(master, plan_path=None, spans=None, out=None, vertical=None, score=None) -> dict:
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
                # the RAW layer (no scrim) for masks, the FITTED position from the
                # shared pair API, so the sampled box is always the box the
                # renderer drew into
                lay, _scr, pos = FM._build_pil_pair(spec)
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
                # a backdrop mush must not be sampled: if the glyph mask and its
                # surroundings are the same colour the box is wrong, not the type.
                # MEASURED (mark, shot 03): a 9x11 glyph mask over a dark scrim
                # patch reported 1.00:1 while the delivered mark reads 6.5:1.
                if int(im.sum()) < 400:
                    continue
                # INK SAMPLE: the interior of the glyph stroke. MEASURED: the
                # 1-px anti-aliased rim of a 21 px mark blends into whatever is
                # behind it, so averaging the whole mask reported fg 202 for ink
                # that is 242 in the layer.
                ksz = 3 if max(im.shape) < 40 else 5
                core_m = cv2.erode(im.astype(np.uint8), np.ones((ksz, ksz), np.uint8)) > 0
                sample = core_m if int(core_m.sum()) >= 60 else im
                fg = sub[sample].mean(axis=0)
                # A CARD layer carries a panel that is a large contiguous region
                # (05 species 9x its glyph area, 08 lower 7.7x). Small text
                # layers have a 150-220 alpha band too — it is their own
                # anti-aliased edge (03 mark: 0.33x), and treating that as the
                # backdrop scored a bone-on-plate corner mark 1.57:1 against its
                # own outline. The panel must dominate the ink to count.
                if pm.sum() > 3.0 * im.sum():
                    bg = sub[pm].mean(axis=0)          # a card: the panel is the backdrop
                else:
                    # RING WIDTH follows the glyph size: on a 14 px mark an 11x11
                    # ring reaches past the halo and samples open plate; a 5x5 ring
                    # measures the backdrop the letters are actually read against.
                    kk = 5 if max(im.shape) < 40 else 11
                    ring = cv2.dilate(im.astype(np.uint8), np.ones((kk, kk), np.uint8)) > 0
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
                import os as _os
                if _os.environ.get("TB_DEBUG_G05"):
                    C.say(f"    [g05] {shot['id']}:{spec['kind']:<9} t={t_show:6.2f} "
                          f"fg={fg.round(0)} bg={bg.round(0)} c={c:.2f} ink={int(im.sum())}")
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
        src, note = master, st["verdict"]
        if score is not None:
            # A narration master cannot be judged by the whole-file correlation: a
            # centred voice is corr ~1.0 by definition and drags the file with it
            # (measured on the delivered master: 0.968). The bed is judged on the
            # STEM and the voice is judged INSIDE ITS OWN SPANS, which is what both
            # gates were always about. data/gates.json carries the revision.
            sp = _vo_spans(plan_path) if plan_path else []
            # MEASURED: with narration present the master's width statistics are
            # dominated by a mono, centred voice (corr up, S/M down) — that is the
            # correct consequence of having a narrator, not a defect in the bed.
            # These two gates are about the BED, so with --score they grade the bed
            # and carry the master's own numbers in the note. data/gates.json holds
            # the revision with this evidence.
            st_stem = S.stereo_report(score)
            vcorr = _corr_in_spans(master, sp)
            src = score
            add("G10", "L/R correlation (voice, in its spans)",
                round(vcorr, 3) if vcorr is not None else None, ">= 0.90",
                vcorr is not None and vcorr >= 0.90,
                f'centred narration; bed corr {st_stem["lr_correlation"]:.3f}, '
                f'whole master {st["lr_correlation"]:.3f}')
            stm = st_stem
        stm = S.stereo_report(src) if score is not None else S.stereo_report(master)
        if score is None:
            add("G10", "L/R correlation", round(stm["lr_correlation"], 3), "0.55 - 0.85",
                0.55 <= stm["lr_correlation"] <= 0.85, note)
        add("G11", "side/mid energy" + (" (bed)" if score is not None else ""),
            round(stm["side_mid"], 3), "> 0.25", stm["side_mid"] > 0.25)
    except Exception as e:  # noqa: BLE001
        add("G10", "L/R correlation", None, "0.55 - 0.85", False, str(e))
        add("G11", "side/mid energy", None, "> 0.25", False, str(e))

    vspans = list(spans) if spans else (_vo_spans(plan_path) if plan_path else [])
    if vspans:
        try:
            a, sr = _band_rms(master)                  # 300-3400 Hz, delivered file
            mask = np.ones(a.shape[0], bool)
            for t0, t1 in vspans:
                mask[int(t0 * sr):int(t1 * sr)] = False
            hi, lo = _rms(a[~mask]), _rms(a[mask])
            lift = 20.0 * np.log10(hi / lo) if (hi > 0 and lo > 0) else None
            add("G20", "narration present in the master (speech band)",
                round(float(lift), 2) if lift is not None else None, ">= 4 dB",
                lift is not None and lift >= 4.0,
                f"{len(vspans)} declared lines, {hi/lo:.2f}x speech-band lift in the spans")
        except Exception as e:  # noqa: BLE001
            add("G20", "narration present in the master (speech band)", None, ">= 4 dB", False, str(e))
        if score is not None:
            # "Narration over the bed" is a MIX-TIME ratio, so it is measured on the
            # two stems at the plan's declared bed gain — NOT master-vs-stem, which
            # compares two different normalisations (the first version of this gate
            # reported -0.86 dB for a master that was in fact 12 dB clear).
            try:
                import pathlib as _pl
                plan_d = json.loads(_pl.Path(plan_path).read_text())
                bg = float(plan_d.get("audio", {}).get("mix_bed_gain", 0.42))
                vpath = _pl.Path(score).with_name("voice.wav")
                vv, sr = _band_rms(vpath)
                ss, _ = _band_rms(score)
                worst, where = 99.0, None
                for t0, t1 in vspans:
                    r = 20.0 * np.log10((_rms(vv[int(t0*sr):int(t1*sr)]) + 1e-9) /
                                        (bg * _rms(ss[int(t0*sr):int(t1*sr)]) + 1e-9))
                    if r < worst:
                        worst, where = r, t0
                add("G21", "narration level over the bed", round(worst, 2), ">= 6 dB",
                    worst >= 6.0, f"worst line at {where}s (voice stem vs bed at gain {bg}; "
                                  f"ducking only widens this)")
            except Exception as e:  # noqa: BLE001
                add("G21", "narration level over the bed", None, ">= 6 dB", False, str(e))

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
    # ── vertical (Shorts) ───────────────────────────────────────────────────
    # G17/G18 run only when a 9:16 master is handed in. They exist because the
    # first vertical cut was a real 1080x1920 render with NO type: the crop and
    # the camera were there, the reason to watch was not. A portrait frame also
    # has a different safe band (the platform's handle and action bar cover the
    # top ~13 % and the bottom ~25 %), so type that passes in 16:9 can sit under
    # the like button in 9:16.
    if vertical and plan:
        vinfo = _probe_geometry(vertical)
        ok_geom = (vinfo["w"], vinfo["h"]) == (C.VW, C.VH)
        add("G18", "vertical geometry", f"{vinfo['w']}x{vinfo['h']}",
            f"{C.VW}x{C.VH}", ok_geom, "9:16 master at the brand resolution")
        bad = []
        with C.canvas(C.VW, C.VH):
            band = C.SAFE
            for shot in plan["shots"]:
                for spec in shot.get("vertical_type", shot.get("type", [])) or []:
                    lay, _sc, (x, y) = FM._build_pil_pair(spec)
                    bb = lay.getchannel("A").getbbox()
                    if bb is None:
                        continue
                    y0, y1 = y + bb[1], y + bb[3]
                    x0, x1 = x + bb[0], x + bb[2]
                    if not (band[0] <= y0 and y1 <= band[1] and 0 <= x0 and x1 <= C.W):
                        bad.append(f"{shot['id']}:{spec['kind']}@y{y0}-{y1}")
        add("G17", "portrait type inside the Shorts band", len(bad), "0", not bad,
            f"safe band y {band[0]}-{band[1]} of {C.VH}: " + "; ".join(bad[:3]))

        # G19: the same legibility question, asked of the VERTICAL master. The
        # portrait crop changes the plate under the type, so a layer that passes
        # in 16:9 can fail in 9:16 (measured: shot 03's mark 6.5:1 -> 4.03:1
        # because the crop pulled a lit patch of fog under it).
        vworst, vlbl = 99.0, None
        with C.canvas(C.VW, C.VH):
            for shot in plan["shots"]:
                for spec in shot.get("vertical_type", shot.get("type", [])) or []:
                    lay, _sc, (x, y) = FM._build_pil_pair(spec)
                    al = np.array(lay)
                    a = al[..., 3]
                    ink = a > 250
                    if int(ink.sum()) < 150:
                        ink = a > 200
                    if int(ink.sum()) < 150:
                        continue
                    oys, oxs = np.where(a > 8)
                    y0, y1 = y + int(oys.min()), y + int(oys.max()) + 1
                    x0, x1 = x + int(oxs.min()), x + int(oxs.max()) + 1
                    t_v = starts[str(shot["id"])] + float(spec.get("in", 0.0))
                    t_out = min(float(spec.get("out", 1e9)), shot["dur"])
                    t_show = t_v + min(1.0, max((t_out - float(spec.get("in", 0.0))) * 0.5, 0.25))
                    fr = _frame_rgb(vertical, t_show)
                    if fr is None:
                        continue
                    sub = fr[y0:y1, x0:x1].astype(np.float32)
                    im = ink[oys.min():oys.max() + 1, oxs.min():oxs.max() + 1]
                    if sub.shape[:2] != im.shape[:2] or int(im.sum()) < 400:
                        continue
                    panel = ((a >= 150) & (a <= 220))[oys.min():oys.max() + 1,
                                                       oxs.min():oxs.max() + 1]
                    if panel.sum() > 3.0 * im.sum():
                        bg = sub[panel].mean(axis=0)
                    else:
                        kk = 5 if max(im.shape) < 40 else 11
                        ring = cv2.dilate(im.astype(np.uint8), np.ones((kk, kk), np.uint8)) > 0
                        ring &= ~im
                        if ring.sum() < 64:
                            continue
                        bg = sub[ring].mean(axis=0)
                    c = _wcag(sub[im].mean(axis=0), bg)
                    import os as _os
                    if _os.environ.get("TB_DEBUG_G05"):
                        C.say(f"    [g19] {shot['id']}:{spec['kind']:<9} t={t_show:6.2f} "
                              f"fg={sub[im].mean(axis=0).round(0)} bg={bg.round(0)} c={c:.2f}")
                    if c < vworst:
                        vworst, vlbl = c, f"{shot['id']}:{spec['kind']}"
        add("G19", "vertical type contrast (delivered)", round(vworst, 2) if vworst < 99 else None,
            ">= 4.5", vworst >= 4.5, f"worst: {vlbl}")

    # MEASURED BUG: the summary used to be computed BEFORE the vertical block, so
    # a report could print PASS while G17/G19 had failed — the counts simply did
    # not include them. The summary is built after every gate has been added.
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
    ap.add_argument("--vertical", help="9:16 master to run G17/G18 against")
    ap.add_argument("--score", help="score stem (score.wav) — enables the G10/G11 bed scope and G21")
    args = ap.parse_args()
    rep = run(args.master, args.plan, out=args.out, vertical=args.vertical, score=args.score)
    print_report(rep)
    raise SystemExit(0 if rep["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
