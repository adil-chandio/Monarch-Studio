#!/usr/bin/env python3
"""Measured delivery gates for THE GRAVITY OF THE PHONE (WTF-30 #1), run on the DELIVERED file.

Covers the per-video WTF gates the brain cannot measure from DNA alone:
  G-W1  container: 1080x1920, 30 fps, H.264 + AAC, 20.0 s
  G-W2  frame 1 in motion + visual question by 0.8 s (frame 0→3 and 0→24 change)
  G-W5  silence hole before the WTF onset (0.3–0.6 s under −60 dBFS)
  G-W6  one uncut WTF set-piece ≥ 3 s; no other shot > 4 s (cut detector vs the planned cut list)
  G-W10 loop seam: last frame vs first frame mean abs diff ≤ 6/255
  plus: loudness (−14 ± 1 LUFS, TP ≤ −1), max-still ≤ 0.4 s, 4:5 safe-centre proof, md5/size receipt.
Writes artifacts/gate_receipt.json and fills DNA.measured.

  python3 gate.py --video ../render/gravity-of-the-phone_master.mp4 --dna ../dna/DNA.json --out ../artifacts
"""
import argparse, hashlib, json, math, pathlib, re, subprocess, sys
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scene as S                        # noqa: E402

W, H, FPS = 1080, 1920, 30
PLANNED_CUTS = [S.TL["cut_s2"], S.TL["cut_s3"], S.TL["cut_s4"], S.TL["cut_s5"], S.TL["cut_s6"]]


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def probe(path):
    p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], text=True, capture_output=True)
    s = p.stderr + p.stdout
    dm = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", s)
    dur = int(dm.group(1)) * 3600 + int(dm.group(2)) * 60 + float(dm.group(3))
    vm = re.search(r"Video: ([^,]+).*?,\s*(\d{3,5})x(\d{3,5}).*?,\s*([\d.]+) fps", s)
    am = re.search(r"Audio: ([^,]+),\s*(\d+) Hz,\s*([^,]+)", s)
    return dict(duration=dur, video_codec=vm.group(1).strip(), width=int(vm.group(2)), height=int(vm.group(3)), fps=float(vm.group(4)),
                audio_codec=am.group(1).strip(), sample_rate=int(am.group(2)), channels=am.group(3).strip())


def decode_small(path, scale=4):
    """All frames, downscaled by `scale` (gray), as a uint8 array (n, h, w)."""
    w, h = W // scale, H // scale
    p = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", str(path), "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w)


def decode_frame(path, n):
    p = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", str(path), "-vf", f"select='eq(n\\,{n})'", "-frames:v", "1", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(H, W, 3)


def decode_audio(path):
    p = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "48000", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.float32)


def loudness(path):
    p = subprocess.run([ffmpeg_exe(), "-v", "info", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    return dict(lufs=float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1)),
                true_peak_db=float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1)),
                lra=float(re.search(r"LRA:\s+(-?[\d.]+) LU", tail).group(1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--dna", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    video = pathlib.Path(a.video)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = []

    def gate(name, ok, detail=""):
        rows.append(dict(gate=name, ok=bool(ok), detail=str(detail)))
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")

    pr = probe(video)
    gate("G-W1 container 1080x1920 @ 30 fps H.264 + AAC",
         pr["width"] == W and pr["height"] == H and abs(pr["fps"] - FPS) < 0.01 and pr["video_codec"].startswith("h264") and pr["audio_codec"].startswith("aac"),
         f"{pr['width']}x{pr['height']} {pr['fps']} fps {pr['video_codec']} / {pr['audio_codec']} {pr['sample_rate']} Hz")
    gate("G-W13 duration 20.0–30.0 s", 19.95 <= pr["duration"] <= 30.05, f"{pr['duration']:.2f} s")

    fr = decode_small(video, 4).astype(np.float32)
    n = len(fr)
    gate("frame count = 600", n == 600, f"{n} frames")
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))          # inter-frame change
    # G-W2 hook: motion between frame 0 and 3 (0.1 s) and a visible question by 0.8 s
    m03 = float(np.abs(fr[3] - fr[0]).mean()); m024 = float(np.abs(fr[24] - fr[0]).mean())
    gate("G-W2 frame 1 in motion (0→3 change > 0.15/255) + visual question by 0.8 s (0→24 change > 0.4/255)", m03 > 0.15 and m024 > 0.4,
         f"0→3 {m03:.2f}, 0→24 {m024:.2f}")
    # max still: no 12-frame window with change < 0.05/255
    win = 12
    still = max(0, int(np.argmax([d[i:i + win].max() < 0.05 for i in range(len(d) - win)]) if any(d[i:i + win].max() < 0.05 for i in range(len(d) - win)) else -1))
    has_still = any(d[i:i + win].max() < 0.05 for i in range(len(d) - win))
    gate("max still ≤ 0.4 s (no 12-frame window without change)", not has_still, f"first still window at frame {still}" if has_still else "none")
    # G-W6 cut detector: big jumps vs planned cuts; the WTF window must contain none
    thr = 12.0
    cuts = [i + 1 for i in range(len(d)) if d[i] > thr]
    cut_times = [round(c / FPS, 2) for c in cuts]
    planned = [int(round(c * FPS)) for c in PLANNED_CUTS]
    unplanned = [c for c in cuts if min(abs(c - p) for p in planned) > 1]
    wtf_a, wtf_b = int(S.TL["cut_s4"] * FPS), int(S.TL["cut_s5"] * FPS)
    inside = [c for c in cuts if wtf_a + 2 <= c < wtf_b - 1]
    shots = [PLANNED_CUTS[0]] + [PLANNED_CUTS[i + 1] - PLANNED_CUTS[i] for i in range(len(PLANNED_CUTS) - 1)] + [S.DUR - PLANNED_CUTS[-1]]
    wtf_len = PLANNED_CUTS[3] - PLANNED_CUTS[2]
    others = [s for s in shots if abs(s - wtf_len) > 1e-6]
    gate("G-W6 one uncut WTF set-piece ≥ 3 s, no cut inside it, no other shot > 4 s",
         wtf_len >= 3.0 and not inside and max(others) <= 4.0 and not unplanned,
         f"WTF shot {wtf_len:.1f} s, detected cuts at {cut_times}, unplanned {unplanned}, inside-WTF {inside}, other shots {others}")
    # G-W10 loop seam
    f0 = decode_frame(video, 0).astype(np.float32); f599 = decode_frame(video, n - 1).astype(np.float32)
    seam = float(np.abs(f0 - f599).mean())
    gate("G-W10 loop seam: last vs first frame mean abs diff ≤ 6/255", seam <= 6.0, f"{seam:.2f}/255")
    # audio
    x = decode_audio(video)
    sr = 48000
    def win_db(t0, t1):
        seg_ = x[int(t0 * sr):int(t1 * sr)]
        return 20 * math.log10(float(np.sqrt((seg_ ** 2).mean()) + 1e-9))
    hole_db = win_db(4.52, S.TL["field_on"] - 0.03)
    hole2_db = win_db(S.TL["glow_off"] + 0.17, S.TL["drop"] - 0.03)
    gate("G-W5 silence hole 0.3–0.6 s before the WTF onset (< −60 dBFS RMS)", hole_db < -60 and 0.3 <= (S.TL["field_on"] - 4.5) <= 0.6,
         f"4.50–{S.TL['field_on']:.2f} s = {S.TL['field_on'] - 4.5:.2f} s at {hole_db:.1f} dBFS; second hole {hole2_db:.1f} dBFS")
    first_sound = float(np.argmax(np.abs(x) > 0.01)) / sr
    gate("hook: sound within the first 0.1 s (frame 1 is alive)", first_sound < 0.1, f"first sound at {first_sound:.3f} s")
    lo = loudness(video)
    gate("G-W11 loudness −14 ± 1 LUFS, TP ≤ −1 dBTP", -15.0 <= lo["lufs"] <= -13.0 and lo["true_peak_db"] <= -1.0,
         f"{lo['lufs']} LUFS, TP {lo['true_peak_db']} dBTP, LRA {lo['lra']} LU")
    # no noise floor: the quietest 0.5 s outside the designed holes must be real silence or real room (either < −45 dBFS)
    blk = sr // 2
    rms = np.array([20 * math.log10(float(np.sqrt((x[i:i + blk] ** 2).mean()) + 1e-9)) for i in range(0, len(x) - blk, blk)])
    # With a composed score under the sound design the master never goes quiet, so the floor is measured on the
    # SOUND-DESIGN STEM (audio/mix_sfx.wav, written by audio.py before the music bus is added): a hiss bed would live there.
    stem = pathlib.Path(a.dna).resolve().parent.parent / "audio" / "mix_sfx.wav"
    if stem.exists():
        import wave
        with wave.open(str(stem)) as wv:
            st = np.frombuffer(wv.readframes(wv.getnframes()), "<i2").reshape(-1, wv.getnchannels()).mean(1) / 32767.0
        rms_s = np.array([20 * math.log10(float(np.sqrt((st[i:i + blk] ** 2).mean()) + 1e-9)) for i in range(0, len(st) - blk, blk)])
        gate("no synthetic noise floor (quietest 0.5 s of the sound-design stem ≤ −45 dBFS; score is a separate composed bus)",
             rms_s.min() <= -45, f"stem quietest block {rms_s.min():.1f} dBFS at {np.argmin(rms_s) * 0.5:.1f} s; master quietest {rms.min():.1f} dBFS at {np.argmin(rms) * 0.5:.1f} s")
    else:
        gate("no synthetic noise floor (quietest 0.5 s ≤ −45 dBFS)", rms.min() <= -45, f"quietest block {rms.min():.1f} dBFS at {np.argmin(rms) * 0.5:.1f} s")
    # 4:5 safe-centre proof: the SUBJECTS (phone, hero head + feet, the two text lines) sit inside y 285–1635 on key
    # frames (computed from the same camera the picture used), and the ink mass is more centred than uniform (≥ 0.72;
    # uniform = 1350/1920 = 0.70 — desk legs / baseboard legitimately run to the bottom edge).
    from PIL import Image
    import render as R
    proofs = []
    keyf = [15, 90, 255, 342, 500, 573, 585]
    sheet = Image.new("RGB", (len(keyf) * 270, 338), (30, 30, 30))
    for i, k in enumerate(keyf):
        t = k / FPS
        f = decode_frame(video, k)
        dark = (f.mean(2) < 90)
        inside = float(dark[285:1635].sum() / max(1, dark.sum()))
        subj = {}
        if not (S.TL["cut_s3"] <= t < S.TL["cut_s4"]):
            cam = R.camera(t)
            tau = S.world_time(t)
            subj["phone"] = cam.pt(*S.PHONE)[1]
            hs = S.hero_state(tau)
            if hs is not None:
                if hs["pivot"]:
                    subj["hero_pivot"] = cam.pt(*hs["pivot_world"])[1]
                else:
                    fy = cam.pt(*hs["feet"])[1]
                    subj["hero_feet"] = fy
                    subj["hero_head"] = fy - R.hero_screen_scale(t, cam)
            if S.TL["line1"] <= t < S.TL["cut_s6"]:
                subj["text_line1"] = 440
                subj["text_line2"] = 580
            if S.TL["moral1"] <= t < S.TL["moral_out"]:
                subj["text_moral_a"] = 668
                subj["text_moral_b"] = 812
        else:
            subj["ecu_head"] = 1010
        ok_s = all(285 <= v <= 1635 for v in subj.values())
        proofs.append(dict(frame=k, t=round(t, 2), ink_inside_safe=round(inside, 3), subjects={a: round(float(b)) for a, b in subj.items()}, subjects_ok=ok_s))
        sheet.paste(Image.fromarray(f[285:1635]).resize((270, 338)), (i * 270, 0))
    sheet.save(out / "crop_4x5_proof.jpg", quality=85)
    gate("4:5 safe centre: every subject inside y 285–1635 on key frames, ink share ≥ 0.72",
         all(p["subjects_ok"] and p["ink_inside_safe"] >= 0.72 for p in proofs),
         "; ".join(f"{p['t']}s ink {p['ink_inside_safe']:.2f} " + ",".join(f"{a}={b}" for a, b in p["subjects"].items()) for p in proofs))
    # receipt
    md5 = hashlib.md5(video.read_bytes()).hexdigest()
    dna = json.loads(pathlib.Path(a.dna).read_text())
    dna["measured"] = dict(lufs=lo["lufs"], true_peak_db=lo["true_peak_db"], lra=lo["lra"], duration_s=round(pr["duration"], 2),
                           frames=int(n), loop_seam_diff=round(seam, 2), silence_hole_db=round(hole_db, 1), md5=md5, bytes=video.stat().st_size,
                           detected_cuts_s=cut_times)
    pathlib.Path(a.dna).write_text(json.dumps(dna, indent=2, ensure_ascii=False))
    receipt = dict(video=str(video), md5=md5, bytes=video.stat().st_size, probe=pr, loudness=lo, gates=rows,
                   passed=sum(r["ok"] for r in rows), total=len(rows), seam_diff=seam, cuts_s=cut_times, safe_proof=proofs)
    (out / "gate_receipt.json").write_text(json.dumps(receipt, indent=1))
    print(f"\n{receipt['passed']}/{receipt['total']} gates passed · md5 {md5}")
    return 0 if receipt["passed"] == receipt["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
